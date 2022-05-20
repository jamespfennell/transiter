// Package scheduler contains the periodic feed update scheduler.
//
// The scheduler reads the database configuration for all of the feeds to determines how often
// to update each one. Periodic updates are scheduled on different goroutines. The scheduler
// guarantees that for each feed there is only one update happeneing at a time.
//
// The scheduler is a highly concurrent component. Not only is it scheduling
// multiple feed updates at the same time, but can also recieve concurrent reset requests to
// update the periodic update configuration it is using. For example, after a system is installed
// the scheduler is instructed to reset the periodic update configuration for the feeds in that
// system.
//
// To satisfy my own intellectual itch, the scheduler is implemented solely using the
// "concurrent sequential processes" model. The only concurrency primitive used is the
// Go channel. In the package there are actually three types of schedulers: a single
// root scheduler (type `Scheduler`) which contains 0 or more system schedulers (one per system), each of
// which in turns contains 1 or more "feed schedulers" (one per feed in the system).
// Each scheduler has its own `run` function which loops indefinitely reading messages on
// different channels. The scheduler will do different things depending on the message it recieves:
// "things" include triggering a new feed update, shutting down, or reseting the
// periodic update configuration.
//
// As an example consider the process of reseting the configuration for a particular system after
// the system is updated. This process is triggered using the `Reset` function. That function
// sends a message on the right channel to the main run loop of the root scheduler. The root scheduler
// reads the message and creates the system scheduler if needed. It thens send a message to the
// system scheduler run loop with the new configuration. That run loop reads the message and
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
			return fmt.Errorf("failed to get systems data during scheduler reset: %w", err)
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
		if feed.PeriodicUpdatePeriod.Valid {
			period = time.Millisecond * time.Duration(feed.PeriodicUpdatePeriod.Int32)
		}
		systemConfig.FeedConfigs = append(systemConfig.FeedConfigs, FeedConfig{
			Id:     feed.ID,
			Period: period,
		})
	}
	return systemConfig, nil
}

type Scheduler struct {
	// The resetAll channels are used to signal to the root scheduler that it should reset all systems
	resetAllRequest chan struct{}
	resetAllReply   chan error

	// The reset channels are used to signal to the root scheduler that it should reset a specified system
	resetRequest chan string
	resetReply   chan error

	// The status channels are used to get status from the scheduler
	statusRequest chan struct{}
	statusReply   chan []FeedStatus
}

func New() *Scheduler {
	return &Scheduler{
		resetAllRequest: make(chan struct{}),
		resetAllReply:   make(chan error),
		resetRequest:    make(chan string),
		resetReply:      make(chan error),
		statusRequest:   make(chan struct{}),
		statusReply:     make(chan []FeedStatus),
	}
}

func (s *Scheduler) Run(ctx context.Context, pool *pgxpool.Pool) {
	s.RunWithClockAndOps(ctx, clock.New(), DefaultOps(pool))
}

func (s *Scheduler) RunWithClockAndOps(ctx context.Context, clock clock.Clock, ops Ops) {
	systemSchedulers := map[string]struct {
		scheduler  *systemScheduler
		cancelFunc context.CancelFunc
	}{}
	resetScheduler := func(systemId string, feedsMsg []FeedConfig) {
		if ss, ok := systemSchedulers[systemId]; ok {
			ss.scheduler.reset(feedsMsg)
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
		systemSchedulers[systemId].scheduler.reset(feedsMsg)
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
		case <-s.resetAllRequest:
			msg, err := ops.ListSystemConfigs(ctx)
			if err != nil {
				s.resetAllReply <- fmt.Errorf("failed to get systems data during scheduler reset: %w", err)
				break
			}
			log.Printf("Reseting scheduler")
			updatedSystemIds := map[string]bool{}
			for _, systemMsg := range msg {
				updatedSystemIds[systemMsg.Id] = true
				resetScheduler(systemMsg.Id, systemMsg.FeedConfigs)
			}
			for systemId := range systemSchedulers {
				if updatedSystemIds[systemId] {
					continue
				}
				stopScheduler(systemId)
			}
			s.resetAllReply <- nil
		case systemId := <-s.resetRequest:
			msg, err := ops.GetSystemConfig(ctx, systemId)
			if err != nil {
				s.resetReply <- fmt.Errorf("failed to get data for system %s during scheduler reset: %w", systemId, err)
				break
			}
			if len(msg.FeedConfigs) == 0 {
				stopScheduler(msg.Id)
			} else {
				resetScheduler(msg.Id, msg.FeedConfigs)
			}
			s.resetReply <- nil
		case <-s.statusRequest:
			var response []FeedStatus
			for _, ss := range systemSchedulers {
				response = append(response, ss.scheduler.status()...)
			}
			s.statusReply <- response
		}
	}
}

func (s *Scheduler) ResetAll(ctx context.Context) error {
	log.Printf("Preparing to reset scheduler")
	s.resetAllRequest <- struct{}{}
	select {
	case err := <-s.resetAllReply:
		return err
	case <-ctx.Done():
		return fmt.Errorf("context cancelled before reset all completed")
	}
}

func (s *Scheduler) Reset(ctx context.Context, systemId string) error {
	log.Printf("Preparing to reset scheduler for system %q\n", systemId)
	s.resetRequest <- systemId
	select {
	case err := <-s.resetReply:
		return err
	case <-ctx.Done():
		return fmt.Errorf("context cancelled before reset completed")
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
	resetRequest chan []FeedConfig
	resetReply   chan struct{}

	// The status channels are used to get status from the scheduler loop
	statusRequest chan struct{}
	statusReply   chan []FeedStatus

	doneChan chan struct{}
}

func newSystemScheduler(ctx context.Context, clock clock.Clock, ops Ops, systemId string) *systemScheduler {
	ss := &systemScheduler{
		resetRequest:  make(chan []FeedConfig),
		resetReply:    make(chan struct{}),
		statusRequest: make(chan struct{}),
		statusReply:   make(chan []FeedStatus),
		doneChan:      make(chan struct{}),
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
		case msg := <-s.resetRequest:
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
				feedSchedulers[feed.Id].scheduler.reset(feed.Period)
			}
			for feedId, fs := range feedSchedulers {
				if updatedFeedIds[feedId] {
					continue
				}
				fs.cancelFunc()
				fs.scheduler.wait()
				delete(feedSchedulers, feedId)
			}
			s.resetReply <- struct{}{}
		case <-s.statusRequest:
			var response []FeedStatus
			for _, fs := range feedSchedulers {
				response = append(response, fs.scheduler.status())
			}
			s.statusReply <- response
		}
	}
}

func (s *systemScheduler) reset(msg []FeedConfig) {
	s.resetRequest <- msg
	<-s.resetReply
}

func (s *systemScheduler) status() []FeedStatus {
	s.statusRequest <- struct{}{}
	return <-s.statusReply
}

func (s *systemScheduler) wait() {
	<-s.doneChan
}

type feedScheduler struct {
	resetRequest chan time.Duration
	resetReply   chan struct{}

	statusRequest chan struct{}
	statusReply   chan FeedStatus

	updateFinished chan error

	doneChan chan struct{}
}

func newFeedScheduler(ctx context.Context, clock clock.Clock, ops Ops, systemId, feedId string) *feedScheduler {
	fs := &feedScheduler{
		resetRequest: make(chan time.Duration),
		resetReply:   make(chan struct{}),

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
		case newPeriod := <-fs.resetRequest:
			if period != newPeriod {
				period = newPeriod
				ticker.Reset(period)
			}
			fs.resetReply <- struct{}{}
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
				SystemId:             systemId,
				FeedId:               feedId,
				CurrentlyRunning:     updateRunning,
				LastFinishedUpdate:   lastFinishedUpdate,
				LastSuccessfulUpdate: lastSuccesfulUpdate,
				Period:               period,
			}
		}
	}
}

func (fs *feedScheduler) reset(period time.Duration) {
	fs.resetRequest <- period
	<-fs.resetReply
}

func (fs *feedScheduler) status() FeedStatus {
	fs.statusRequest <- struct{}{}
	return <-fs.statusReply
}

func (fs *feedScheduler) wait() {
	<-fs.doneChan
}
