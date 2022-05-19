// Package scheduler contains the periodic feed update scheduler.
//
// The scheduler reads the database configuration for all of the feeds to determines how often
// to auto-update each one. Auto-updates are scheduled on different goroutines. The scheduler
// guarantees that for each feed there is only on update happeneing at a time.
//
// The scheduler is a highly concurrent component. Not only is it scheduling
// multiple updates at the same time, but can also recieve concurrent "refresh" requests to
// update the auto-update configuration it is using. For example, after a system is installed
// the scheduler is instructed to refresh the auto-update configuration for the feeds in that
// system.
//
// To satisfy my own intellectual itch, the scheduler is implemented solely using the
// "concurrent sequential processes" model. The only concurrency primitive used is the
// Go channel. In the package there are actually three types of schedulers: a single
// root scheduler (type `Scheduler`) which contains 0 or more system schedulers (one per system), each of
// which in turns contains 1 or more "feed schedulers" (one per feed in the system).
// Each scheduler has its own `run` function which loops indefinitely reading messages on
// different channels. The scheduler will do different things depending on the message it recieves:
// "things" include triggering a new feed update, shutting down, or refreshing the
// auto-update configuration.
//
// As an example consider the process of refreshing the configuration for a particular system after,
// say, the system is updated. This process is triggered using the `Refresh` function. That function
// sends a message on the right channel to the main run loop of the root scheduler. The root scheduler
// reads the message and creates the system scheduler if needed. It thens send a message to the
// system scheduler run loop with the new configuration. That run loop reads the message and essentially
// propogates it to the feed schedulers contained inside.
package scheduler

import (
	"context"
	"fmt"
	"log"
	"sort"
	"time"

	"github.com/benbjohnson/clock"
	"github.com/jackc/pgx/v4"
	"github.com/jackc/pgx/v4/pgxpool"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/update"
)

type SystemConfig struct {
	Id          string
	FeedConfigs []FeedConfig
}

type FeedConfig struct {
	Id     string
	Period time.Duration
}

// Ops describes the operations the scheduler performs that involve the wider Transiter system.
//
// These operations are abstracted away to make unit testing easier.
type Ops interface {
	// List all system configs.
	ListSystemConfigs(ctx context.Context) ([]SystemConfig, error)

	// Get the system config for a system.
	GetSystemConfig(ctx context.Context, systemId string) (SystemConfig, error)

	// UpdateFeed updates the specified feed.
	UpdateFeed(ctx context.Context, systemId, feedId string) error
}

func DefaultOps(pool *pgxpool.Pool) Ops {
	return &defaultSchedulerOps{pool: pool}
}

type defaultSchedulerOps struct {
	pool *pgxpool.Pool
}

func (ops *defaultSchedulerOps) ListSystemConfigs(ctx context.Context) ([]SystemConfig, error) {
	var configs []SystemConfig
	if err := ops.pool.BeginTxFunc(ctx, pgx.TxOptions{}, func(tx pgx.Tx) error {
		querier := db.New(tx)
		systems, err := querier.ListSystems(ctx)
		if err != nil {
			return fmt.Errorf("failed to get systems data during scheduler refresh: %w", err)
		}
		for _, system := range systems {
			config, err := buildSystemConfig(ctx, querier, system.ID)
			if err != nil {
				return err
			}
			configs = append(configs, config)
		}
		return nil
	}); err != nil {
		return nil, err
	}
	return configs, nil
}

func (ops *defaultSchedulerOps) GetSystemConfig(ctx context.Context, systemId string) (SystemConfig, error) {
	var config SystemConfig
	if err := ops.pool.BeginTxFunc(ctx, pgx.TxOptions{}, func(tx pgx.Tx) error {
		querier := db.New(tx)
		var err error
		config, err = buildSystemConfig(ctx, querier, systemId)
		return err
	}); err != nil {
		return SystemConfig{}, err
	}
	return config, nil
}

func (ops *defaultSchedulerOps) UpdateFeed(ctx context.Context, systemId, feedId string) error {
	return update.CreateAndRun(ctx, ops.pool, systemId, feedId)
}

func buildSystemConfig(ctx context.Context, querier db.Querier, systemId string) (SystemConfig, error) {
	systemConfig := SystemConfig{Id: systemId}
	feeds, err := querier.ListAutoUpdateFeedsForSystem(ctx, systemId)
	if err != nil {
		return SystemConfig{}, err
	}
	for _, feed := range feeds {
		period := 500 * time.Millisecond
		if feed.AutoUpdatePeriod.Valid {
			period = time.Millisecond * time.Duration(feed.AutoUpdatePeriod.Int32)
		}
		systemConfig.FeedConfigs = append(systemConfig.FeedConfigs, FeedConfig{
			Id:     feed.ID,
			Period: period,
		})
	}
	return systemConfig, nil
}

type Scheduler struct {
	// The refreshAll channels are used to signal to the root scheduler that it should refresh all systems
	refreshAllRequest chan struct{}
	refreshAllReply   chan error

	// The refresh channels are used to signal to the root scheduler that it should refresh a specified system
	refreshRequest chan string
	refreshReply   chan error

	// The status channels are used to get status from the scheduler
	statusRequest chan struct{}
	statusReply   chan []FeedStatus
}

func New() *Scheduler {
	return &Scheduler{
		refreshAllRequest: make(chan struct{}),
		refreshAllReply:   make(chan error),
		refreshRequest:    make(chan string),
		refreshReply:      make(chan error),
		statusRequest:     make(chan struct{}),
		statusReply:       make(chan []FeedStatus),
	}
}

func (s *Scheduler) Run(ctx context.Context, clock clock.Clock, pool *pgxpool.Pool) {
	s.RunWithOps(ctx, clock, DefaultOps(pool))
}

func (s *Scheduler) RunWithOps(ctx context.Context, clock clock.Clock, ops Ops) {
	systemSchedulers := map[string]struct {
		scheduler  *systemScheduler
		cancelFunc context.CancelFunc
	}{}
	refreshScheduler := func(systemId string, feedsMsg []FeedConfig) {
		if ss, ok := systemSchedulers[systemId]; ok {
			ss.scheduler.refresh(feedsMsg)
			return
		}
		systemCtx, cancelFunc := context.WithCancel(ctx)
		systemSchedulers[systemId] = struct {
			scheduler  *systemScheduler
			cancelFunc context.CancelFunc
		}{
			scheduler:  newSystemScheduler(systemCtx, clock, ops, systemId),
			cancelFunc: cancelFunc,
		}
		systemSchedulers[systemId].scheduler.refresh(feedsMsg)
	}
	stopScheduler := func(systemId string) {
		ss, ok := systemSchedulers[systemId]
		if !ok {
			return
		}
		ss.cancelFunc()
		ss.scheduler.wait()
		delete(systemSchedulers, systemId)
	}
	for {
		select {
		case <-ctx.Done():
			for systemId := range systemSchedulers {
				stopScheduler(systemId)
			}
			return
		case <-s.refreshAllRequest:
			msg, err := ops.ListSystemConfigs(ctx)
			if err != nil {
				s.refreshAllReply <- fmt.Errorf("failed to get systems data during scheduler refresh: %w", err)
				break
			}
			log.Printf("Refreshing scheduler")
			updatedSystemIds := map[string]bool{}
			for _, systemMsg := range msg {
				updatedSystemIds[systemMsg.Id] = true
				refreshScheduler(systemMsg.Id, systemMsg.FeedConfigs)
			}
			for systemId := range systemSchedulers {
				if updatedSystemIds[systemId] {
					continue
				}
				stopScheduler(systemId)
			}
			s.refreshAllReply <- nil
		case systemId := <-s.refreshRequest:
			msg, err := ops.GetSystemConfig(ctx, systemId)
			if err != nil {
				s.refreshReply <- fmt.Errorf("failed to get data for system %s during scheduler refresh: %w", systemId, err)
				break
			}
			if len(msg.FeedConfigs) == 0 {
				stopScheduler(msg.Id)
			} else {
				refreshScheduler(msg.Id, msg.FeedConfigs)
			}
			s.refreshReply <- nil
		case <-s.statusRequest:
			var response []FeedStatus
			for systemId, ss := range systemSchedulers {
				statusesForSystem := ss.scheduler.status()
				for _, status := range statusesForSystem {
					status.SystemId = systemId
					response = append(response, status)
				}
			}
			s.statusReply <- response
		}
	}
}

func (s *Scheduler) RefreshAll(ctx context.Context) error {
	log.Printf("Preparing to refresh scheduler")
	s.refreshAllRequest <- struct{}{}
	select {
	case err := <-s.refreshAllReply:
		return err
	case <-ctx.Done():
		return fmt.Errorf("context cancelled before refresh all completed")
	}
}

func (s *Scheduler) Refresh(ctx context.Context, systemId string) error {
	log.Printf("Preparing to refresh scheduler for system %q\n", systemId)
	s.refreshRequest <- systemId
	select {
	case err := <-s.refreshReply:
		return err
	case <-ctx.Done():
		return fmt.Errorf("context cancelled before refresh completed")
	}
}

type FeedStatus struct {
	SystemId             string
	FeedId               string
	Period               time.Duration
	LastFinishedUpdate   time.Time
	LastSuccessfulUpdate time.Time
	CurrentlyRunning     bool
}

func (s *Scheduler) Status() []FeedStatus {
	s.statusRequest <- struct{}{}
	feeds := <-s.statusReply
	sort.Slice(feeds, func(i, j int) bool {
		if feeds[i].SystemId == feeds[j].SystemId {
			return feeds[i].FeedId < feeds[j].FeedId
		}
		return feeds[i].SystemId < feeds[j].SystemId
	})
	return feeds
}

type systemScheduler struct {
	refreshRequest chan []FeedConfig
	refreshReply   chan struct{}

	// The status channels are used to get status from the scheduler loop
	statusRequest chan struct{}
	statusReply   chan []FeedStatus

	doneChan chan struct{}
}

func newSystemScheduler(ctx context.Context, clock clock.Clock, ops Ops, systemId string) *systemScheduler {
	ss := &systemScheduler{
		refreshRequest: make(chan []FeedConfig),
		refreshReply:   make(chan struct{}),
		statusRequest:  make(chan struct{}),
		statusReply:    make(chan []FeedStatus),
		doneChan:       make(chan struct{}),
	}
	go ss.run(ctx, clock, ops, systemId)
	return ss
}

func (s *systemScheduler) run(ctx context.Context, clock clock.Clock, ops Ops, systemId string) {
	feedSchedulers := map[string]struct {
		scheduler  *feedScheduler
		cancelFunc context.CancelFunc
	}{}
	for {
		select {
		case <-ctx.Done():
			for _, fs := range feedSchedulers {
				fs.cancelFunc()
				fs.scheduler.wait()
			}
			close(s.doneChan)
			return
		case msg := <-s.refreshRequest:
			updatedFeedIds := map[string]bool{}
			for _, feed := range msg {
				updatedFeedIds[feed.Id] = true
				if _, ok := feedSchedulers[feed.Id]; !ok {
					feedCtx, cancelFunc := context.WithCancel(ctx)
					feedSchedulers[feed.Id] = struct {
						scheduler  *feedScheduler
						cancelFunc context.CancelFunc
					}{
						scheduler:  newFeedScheduler(feedCtx, clock, ops, systemId, feed.Id),
						cancelFunc: cancelFunc,
					}
				}
				feedSchedulers[feed.Id].scheduler.refresh(feed.Period)
			}
			for feedId, fs := range feedSchedulers {
				if updatedFeedIds[feedId] {
					continue
				}
				fs.cancelFunc()
				fs.scheduler.wait()
				delete(feedSchedulers, feedId)
			}
			s.refreshReply <- struct{}{}
		case <-s.statusRequest:
			var response []FeedStatus
			for feedId, fs := range feedSchedulers {
				s := fs.scheduler.status()
				s.FeedId = feedId
				response = append(response, s)
			}
			s.statusReply <- response
		}
	}
}

func (s *systemScheduler) refresh(msg []FeedConfig) {
	s.refreshRequest <- msg
	<-s.refreshReply
}

func (s *systemScheduler) status() []FeedStatus {
	s.statusRequest <- struct{}{}
	return <-s.statusReply
}

func (s *systemScheduler) wait() {
	<-s.doneChan
}

type feedScheduler struct {
	refreshRequest chan time.Duration
	refreshReply   chan struct{}

	statusRequest chan struct{}
	statusReply   chan FeedStatus

	updateFinished chan error

	doneChan chan struct{}
}

func newFeedScheduler(ctx context.Context, clock clock.Clock, ops Ops, systemId, feedId string) *feedScheduler {
	fs := &feedScheduler{
		refreshRequest: make(chan time.Duration),
		refreshReply:   make(chan struct{}),

		statusRequest: make(chan struct{}),
		statusReply:   make(chan FeedStatus),

		updateFinished: make(chan error),
		doneChan:       make(chan struct{}),
	}
	go fs.run(ctx, clock, ops, systemId, feedId)
	return fs
}

func (fs *feedScheduler) run(ctx context.Context, clock clock.Clock, ops Ops, systemId, feedId string) {
	period := time.Duration(0)
	// TODO: what is this about?
	ticker := clock.Ticker(time.Hour * 50000)
	var lastSuccesfulUpdate time.Time
	var lastFinishedUpdate time.Time
	updateRunning := false
	for {
		select {
		case <-ctx.Done():
			ticker.Stop()
			if updateRunning {
				<-fs.updateFinished
			}
			close(fs.doneChan)
			return
		case newPeriod := <-fs.refreshRequest:
			if period != newPeriod {
				period = newPeriod
				ticker.Reset(period)
			}
			fs.refreshReply <- struct{}{}
		case <-ticker.C:
			if updateRunning {
				continue
			}
			updateRunning = true
			go func() {
				fs.updateFinished <- ops.UpdateFeed(ctx, systemId, feedId)
			}()
		case err := <-fs.updateFinished:
			now := time.Now()
			if err == nil {
				lastSuccesfulUpdate = now
			}
			lastFinishedUpdate = now
			updateRunning = false
		case <-fs.statusRequest:
			fs.statusReply <- FeedStatus{
				CurrentlyRunning:     updateRunning,
				LastFinishedUpdate:   lastFinishedUpdate,
				LastSuccessfulUpdate: lastSuccesfulUpdate,
				Period:               period,
			}
		}
	}
}

func (fs *feedScheduler) refresh(period time.Duration) {
	fs.refreshRequest <- period
	<-fs.refreshReply
}

func (fs *feedScheduler) status() FeedStatus {
	fs.statusRequest <- struct{}{}
	return <-fs.statusReply
}

func (fs *feedScheduler) wait() {
	<-fs.doneChan
}
