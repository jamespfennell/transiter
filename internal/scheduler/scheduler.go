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
	"database/sql"
	"fmt"
	"log"
	"sort"
	"time"

	"github.com/benbjohnson/clock"
	"github.com/jamespfennell/transiter/internal/gen/db"
)

type UpdateFunc func(ctx context.Context, database *sql.DB, systemId, feedId string) error

type QuerierFunc func(database *sql.DB) db.Querier

type Scheduler struct {
	database    *sql.DB
	querierFunc QuerierFunc

	// The refreshAll channels are used to signal to the root scheduler that it should refresh all systems
	refreshAllRequest chan []refreshMsg
	refreshAllReply   chan struct{}

	// The refresh channels are used to signal to the root scheduler that it should refresh a specified system
	refreshRequest chan refreshMsg
	refreshReply   chan struct{}

	// The status channels are used to get status from the scheduler
	statusRequest chan struct{}
	statusReply   chan []ScheduledFeed

	// doneChan is closed when the scheduler shuts down
	doneChan chan struct{}
}

func New(ctx context.Context, clock clock.Clock, database *sql.DB, querierFunc QuerierFunc, updateFunc UpdateFunc) (*Scheduler, error) {
	s := &Scheduler{
		database:          database,
		querierFunc:       querierFunc,
		refreshAllRequest: make(chan []refreshMsg),
		refreshAllReply:   make(chan struct{}),
		refreshRequest:    make(chan refreshMsg),
		refreshReply:      make(chan struct{}),
		statusRequest:     make(chan struct{}),
		statusReply:       make(chan []ScheduledFeed),
		doneChan:          make(chan struct{}),
	}
	go s.run(ctx, clock, database, updateFunc)
	return s, s.RefreshAll(ctx)
}

func (s *Scheduler) run(ctx context.Context, clock clock.Clock, database *sql.DB, updateFunc UpdateFunc) {
	systemSchedulers := map[string]struct {
		scheduler  *systemScheduler
		cancelFunc context.CancelFunc
	}{}
	refreshScheduler := func(systemId string, feedsMsg []refreshFeedsMsg) {
		if ss, ok := systemSchedulers[systemId]; ok {
			ss.scheduler.refresh(feedsMsg)
			return
		}
		systemCtx, cancelFunc := context.WithCancel(ctx)
		systemSchedulers[systemId] = struct {
			scheduler  *systemScheduler
			cancelFunc context.CancelFunc
		}{
			scheduler: newSystemScheduler(systemCtx, clock, func(ctx context.Context, feedId string) error {
				return updateFunc(ctx, database, systemId, feedId)
			}),
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
			close(s.doneChan)
			return
		case msg := <-s.refreshAllRequest:
			log.Printf("Refreshing scheduler")
			updatedSystemIds := map[string]bool{}
			for _, systemMsg := range msg {
				updatedSystemIds[systemMsg.systemId] = true
				refreshScheduler(systemMsg.systemId, systemMsg.feeds)
			}
			for systemId := range systemSchedulers {
				if updatedSystemIds[systemId] {
					continue
				}
				stopScheduler(systemId)
			}
			s.refreshAllReply <- struct{}{}
		case msg := <-s.refreshRequest:
			if len(msg.feeds) == 0 {
				stopScheduler(msg.systemId)
			} else {
				refreshScheduler(msg.systemId, msg.feeds)
			}
			s.refreshReply <- struct{}{}
		case <-s.statusRequest:
			var response []ScheduledFeed
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

func (s *Scheduler) Wait() {
	<-s.doneChan
}

func (s *Scheduler) RefreshAll(ctx context.Context) error {
	log.Printf("Preparing to refresh scheduler")
	querier := s.querierFunc(s.database)
	systems, err := querier.ListSystems(ctx)
	if err != nil {
		return fmt.Errorf("failed to get systems data during scheduler refresh: %w", err)
	}
	var msg []refreshMsg
	for _, system := range systems {
		systemMsg := refreshMsg{systemId: system.ID}
		feeds, err := querier.ListAutoUpdateFeedsForSystem(ctx, system.ID)
		if err != nil {
			return err
		}
		for _, feed := range feeds {
			period := 500 * time.Millisecond
			if feed.AutoUpdatePeriod.Valid {
				period = time.Millisecond * time.Duration(feed.AutoUpdatePeriod.Int32)
			}
			systemMsg.feeds = append(systemMsg.feeds, refreshFeedsMsg{
				feedId: feed.ID,
				period: period,
			})
		}
		msg = append(msg, systemMsg)
	}
	s.refreshAllRequest <- msg
	select {
	case <-s.refreshAllReply:
		return nil
	case <-ctx.Done():
		return fmt.Errorf("context cancelled before refresh all completed")
	}
}

type refreshFeedsMsg struct {
	feedId string
	period time.Duration
}

type refreshMsg struct {
	systemId string
	feeds    []refreshFeedsMsg
}

func (s *Scheduler) Refresh(ctx context.Context, systemId string) error {
	log.Printf("Preparing to refresh scheduler for system %q\n", systemId)
	querier := s.querierFunc(s.database)
	feeds, err := querier.ListAutoUpdateFeedsForSystem(ctx, systemId)
	if err != nil {
		return err
	}
	msg := refreshMsg{systemId: systemId}
	for _, feed := range feeds {
		period := 500 * time.Millisecond
		if feed.AutoUpdatePeriod.Valid {
			period = time.Millisecond * time.Duration(feed.AutoUpdatePeriod.Int32)
		}
		msg.feeds = append(msg.feeds, refreshFeedsMsg{
			feedId: feed.ID,
			period: period,
		})
	}
	s.refreshRequest <- msg
	select {
	case <-s.refreshReply:
		return nil
	case <-ctx.Done():
		return fmt.Errorf("context cancelled before refresh completed")
	}
}

type ScheduledFeed struct {
	SystemId             string
	FeedId               string
	Period               time.Duration
	LastFinishedUpdate   time.Time
	LastSuccessfulUpdate time.Time
	CurrentlyRunning     bool
}

type scheduledFeeds []ScheduledFeed

func (s scheduledFeeds) Len() int {
	return len(s)
}
func (s scheduledFeeds) Swap(i, j int) {
	s[i], s[j] = s[j], s[i]
}
func (s scheduledFeeds) Less(i, j int) bool {
	if s[i].SystemId == s[j].SystemId {
		return s[i].FeedId < s[j].FeedId
	}
	return s[i].SystemId < s[j].SystemId
}

func (s *Scheduler) Status() []ScheduledFeed {
	s.statusRequest <- struct{}{}
	feeds := <-s.statusReply
	sort.Sort(scheduledFeeds(feeds))
	return feeds
}

type systemScheduler struct {
	refreshRequest chan []refreshFeedsMsg
	refreshReply   chan struct{}

	// The status channels are used to get status from the scheduler loop
	statusRequest chan struct{}
	statusReply   chan []ScheduledFeed

	doneChan chan struct{}
}

func newSystemScheduler(ctx context.Context, clock clock.Clock, f func(ctx context.Context, feedId string) error) *systemScheduler {
	ss := &systemScheduler{
		refreshRequest: make(chan []refreshFeedsMsg),
		refreshReply:   make(chan struct{}),
		statusRequest:  make(chan struct{}),
		statusReply:    make(chan []ScheduledFeed),
		doneChan:       make(chan struct{}),
	}
	go ss.run(ctx, clock, f)
	return ss
}

func (s *systemScheduler) run(ctx context.Context, clock clock.Clock, f func(ctx context.Context, feedId string) error) {
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
				updatedFeedIds[feed.feedId] = true
				if _, ok := feedSchedulers[feed.feedId]; !ok {
					feedCtx, cancelFunc := context.WithCancel(ctx)
					feedSchedulers[feed.feedId] = struct {
						scheduler  *feedScheduler
						cancelFunc context.CancelFunc
					}{
						scheduler: newFeedScheduler(feedCtx, clock, func(ctx context.Context) error {
							return f(ctx, feed.feedId)
						}),
						cancelFunc: cancelFunc,
					}
				}
				feedSchedulers[feed.feedId].scheduler.refresh(feed.period)
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
			var response []ScheduledFeed
			for feedId, fs := range feedSchedulers {
				s := fs.scheduler.status()
				s.FeedId = feedId
				response = append(response, s)
			}
			s.statusReply <- response
		}
	}
}

func (s *systemScheduler) refresh(msg []refreshFeedsMsg) {
	s.refreshRequest <- msg
	<-s.refreshReply
}

func (s *systemScheduler) status() []ScheduledFeed {
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
	statusReply   chan ScheduledFeed

	updateFinished chan error

	doneChan chan struct{}
}

func newFeedScheduler(ctx context.Context, clock clock.Clock, f func(ctx context.Context) error) *feedScheduler {
	fs := &feedScheduler{
		refreshRequest: make(chan time.Duration),
		refreshReply:   make(chan struct{}),

		statusRequest: make(chan struct{}),
		statusReply:   make(chan ScheduledFeed),

		updateFinished: make(chan error),
		doneChan:       make(chan struct{}),
	}
	go fs.run(ctx, clock, f)
	return fs
}

func (fs *feedScheduler) run(ctx context.Context, clock clock.Clock, f func(ctx context.Context) error) {
	period := time.Duration(0)
	ticker := clock.Ticker(time.Hour * 50000)
	var lastSuccesfulUpdate time.Time
	var lastFinishedUpdate time.Time
	updateRunning := false
	for {
		select {
		case <-ctx.Done():
			ticker.Stop()
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
				fs.updateFinished <- f(ctx)
			}()
		case err := <-fs.updateFinished:
			now := time.Now()
			if err == nil {
				lastSuccesfulUpdate = now
			}
			lastFinishedUpdate = now
			updateRunning = false
		case <-fs.statusRequest:
			fs.statusReply <- ScheduledFeed{
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

func (fs *feedScheduler) status() ScheduledFeed {
	fs.statusRequest <- struct{}{}
	return <-fs.statusReply
}

func (fs *feedScheduler) wait() {
	<-fs.doneChan
}
