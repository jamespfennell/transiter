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
	"sort"
	"time"

	"github.com/benbjohnson/clock"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/scheduler/ticker"
	"golang.org/x/exp/slog"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

// Scheduler defines the API of a Transiter scheduler.
// The methods of this interface are invoked in the Transiter admin service.
type Scheduler interface {
	// Reset resets the scheduler with the current periodic update configuration for all systems.
	Reset(ctx context.Context) error
	// ResetSystem resets the scheduler for the provided system.
	ResetSystem(ctx context.Context, systemID string) error
	// Status returns a list of feed statuses for all feeds being periodically updated by the scheduler.
	Status() []FeedStatus
}

// FeedStatus describes the status of one feed within a scheduler.
type FeedStatus struct {
	// ID of the system.
	SystemID string
	// ID of the feed.
	FeedID string
	// Update period.
	Period time.Duration
	// Time of the last update that finished.
	LastFinishedUpdate time.Time
	// Time of the last update that finished successfully.
	LastSuccessfulUpdate time.Time
	// Whether an update for this feed is currently reunning.
	CurrentlyRunning bool
}

// DefaultScheduler is Transiter's default scheduler.
type DefaultScheduler struct {
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

// NewDefaultScheduler creates a new instance of the default scheduler.
//
// This scheduler must be run using the `Run` method.
func NewDefaultScheduler() *DefaultScheduler {
	return &DefaultScheduler{
		resetAllRequest: make(chan struct{}),
		resetAllReply:   make(chan error),
		resetRequest:    make(chan string),
		resetReply:      make(chan error),
		statusRequest:   make(chan struct{}),
		statusReply:     make(chan []FeedStatus),
	}
}

// Run runs the scheduler until the provided context is cancelled.
func (s *DefaultScheduler) Run(ctx context.Context, public api.PublicServer, admin api.AdminServer, logger *slog.Logger) {
	s.runWithClock(ctx, public, admin, clock.New(), logger)
}

func (s *DefaultScheduler) runWithClock(ctx context.Context, public api.PublicServer, admin api.AdminServer, clock clock.Clock, logger *slog.Logger) {
	systemSchedulers := map[string]struct {
		scheduler  *systemScheduler
		cancelFunc context.CancelFunc
	}{}
	resetScheduler := func(systemID string, feeds []*api.FeedConfig) {
		if ss, ok := systemSchedulers[systemID]; ok {
			ss.scheduler.reset(feeds)
			return
		}
		systemCtx, cancelFunc := context.WithCancel(ctx)
		systemSchedulers[systemID] = struct {
			scheduler  *systemScheduler
			cancelFunc context.CancelFunc
		}{
			scheduler:  newSystemScheduler(systemCtx, admin, clock, systemID),
			cancelFunc: cancelFunc,
		}
		systemSchedulers[systemID].scheduler.reset(feeds)
	}
	stopScheduler := func(systemID string) {
		ss, ok := systemSchedulers[systemID]
		if !ok {
			return
		}
		ss.cancelFunc()
		ss.scheduler.wait()
		delete(systemSchedulers, systemID)
	}
	getFeeds := func(systemID string) ([]*api.FeedConfig, error) {
		resp, err := admin.GetSystemConfig(ctx, &api.GetSystemConfigRequest{SystemId: systemID})
		if err != nil {
			if s, ok := status.FromError(err); ok && s.Code() == codes.NotFound {
				return nil, nil
			}
			return nil, fmt.Errorf("failed to get data for system %s during scheduler reset: %w", systemID, err)
		}
		var feeds []*api.FeedConfig
		for _, feed := range resp.Feeds {
			if feed.UpdateStrategy != api.FeedConfig_PERIODIC {
				continue
			}
			feeds = append(feeds, feed)
		}
		return feeds, nil
	}
	for {
		select {
		case <-ctx.Done():
			for systemID := range systemSchedulers {
				stopScheduler(systemID)
			}
			return
		case <-s.resetAllRequest:
			logger.InfoCtx(ctx, "reseting scheduler")
			resp, err := public.ListSystems(ctx, &api.ListSystemsRequest{})
			if err != nil {
				s.resetAllReply <- fmt.Errorf("failed to get systems data during scheduler reset: %w", err)
				break
			}
			systemIDToFeeds := map[string][]*api.FeedConfig{}
			for _, system := range resp.Systems {
				var feeds []*api.FeedConfig
				feeds, err = getFeeds(system.Id)
				if err != nil {
					break
				}
				if len(feeds) == 0 {
					continue
				}
				systemIDToFeeds[system.Id] = feeds
			}
			if err != nil {
				s.resetAllReply <- err
				break
			}
			for systemID, feeds := range systemIDToFeeds {
				resetScheduler(systemID, feeds)
			}
			for systemID := range systemSchedulers {
				if _, ok := systemIDToFeeds[systemID]; ok {
					continue
				}
				stopScheduler(systemID)
			}
			s.resetAllReply <- nil
		case systemID := <-s.resetRequest:
			feeds, err := getFeeds(systemID)
			if err != nil {
				s.resetReply <- err
			}
			if len(feeds) == 0 {
				logger.InfoCtx(ctx, "stopping scheduler for system", slog.String("system_id", systemID))
				stopScheduler(systemID)
			} else {
				logger.InfoCtx(ctx, "reseting scheduler for system", slog.String("system_id", systemID))
				resetScheduler(systemID, feeds)
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

func (s *DefaultScheduler) Reset(ctx context.Context) error {
	s.resetAllRequest <- struct{}{}
	select {
	case err := <-s.resetAllReply:
		return err
	case <-ctx.Done():
		return ctx.Err()
	}
}

func (s *DefaultScheduler) ResetSystem(ctx context.Context, systemID string) error {
	s.resetRequest <- systemID
	select {
	case err := <-s.resetReply:
		return err
	case <-ctx.Done():
		return ctx.Err()
	}
}

func (s *DefaultScheduler) Status() []FeedStatus {
	s.statusRequest <- struct{}{}
	// TODO: use a context here
	feeds := <-s.statusReply
	sort.Slice(feeds, func(i, j int) bool {
		if feeds[i].SystemID == feeds[j].SystemID {
			return feeds[i].FeedID < feeds[j].FeedID
		}
		return feeds[i].SystemID < feeds[j].SystemID
	})
	return feeds
}

type systemScheduler struct {
	resetRequest chan []*api.FeedConfig

	// The status channels are used to get status from the scheduler loop
	statusRequest chan struct{}
	statusReply   chan []FeedStatus

	opDone chan struct{}
}

func newSystemScheduler(ctx context.Context, admin api.AdminServer, clock clock.Clock, systemID string) *systemScheduler {
	ss := &systemScheduler{
		resetRequest:  make(chan []*api.FeedConfig),
		statusRequest: make(chan struct{}),
		statusReply:   make(chan []FeedStatus),
		opDone:        make(chan struct{}),
	}
	go ss.run(ctx, admin, clock, systemID)
	return ss
}

func (s *systemScheduler) run(ctx context.Context, admin api.AdminServer, clock clock.Clock, systemID string) {
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
			close(s.opDone)
			return
		case msg := <-s.resetRequest:
			updatedFeedIds := map[string]bool{}
			for _, feed := range msg {
				updatedFeedIds[feed.Id] = true
				period := 500 * time.Millisecond
				if feed.UpdatePeriodS != nil {
					period = time.Duration(*feed.UpdatePeriodS * float64(time.Second))
				}
				if _, ok := feedSchedulers[feed.Id]; !ok {
					feedCtx, cancelFunc := context.WithCancel(ctx)
					feedSchedulers[feed.Id] = struct {
						scheduler  *feedScheduler
						cancelFunc context.CancelFunc
					}{
						scheduler:  newFeedScheduler(feedCtx, admin, clock, systemID, feed.Id, period),
						cancelFunc: cancelFunc,
					}
				} else {
					feedSchedulers[feed.Id].scheduler.reset(period)
				}
			}
			for feedID, fs := range feedSchedulers {
				if updatedFeedIds[feedID] {
					continue
				}
				fs.cancelFunc()
				fs.scheduler.wait()
				delete(feedSchedulers, feedID)
			}
			s.opDone <- struct{}{}
		case <-s.statusRequest:
			var response []FeedStatus
			for _, fs := range feedSchedulers {
				response = append(response, fs.scheduler.status())
			}
			s.statusReply <- response
		}
	}
}

func (s *systemScheduler) reset(msg []*api.FeedConfig) {
	s.resetRequest <- msg
	<-s.opDone
}

func (s *systemScheduler) status() []FeedStatus {
	s.statusRequest <- struct{}{}
	return <-s.statusReply
}

func (s *systemScheduler) wait() {
	<-s.opDone
}

type feedScheduler struct {
	resetRequest chan time.Duration

	statusRequest chan struct{}
	statusReply   chan FeedStatus

	updateFinished chan error

	opDone chan struct{}
}

func newFeedScheduler(ctx context.Context, admin api.AdminServer, clock clock.Clock, systemID, feedID string, period time.Duration) *feedScheduler {
	fs := &feedScheduler{
		resetRequest: make(chan time.Duration),

		statusRequest: make(chan struct{}),
		statusReply:   make(chan FeedStatus),

		updateFinished: make(chan error),
		opDone:         make(chan struct{}),
	}
	go fs.run(ctx, admin, clock, systemID, feedID, period)
	<-fs.opDone
	return fs
}

func (fs *feedScheduler) run(ctx context.Context, admin api.AdminServer, clock clock.Clock, systemID, feedID string, period time.Duration) {
	ticker := ticker.New(clock, period)
	fs.opDone <- struct{}{}
	var lastSuccessfulUpdate time.Time
	var lastFinishedUpdate time.Time
	updateRunning := false
	for {
		select {
		case <-ctx.Done():
			ticker.Stop()
			if updateRunning {
				<-fs.updateFinished
			}
			close(fs.opDone)
			return
		case period = <-fs.resetRequest:
			ticker.Reset(period)
			fs.opDone <- struct{}{}
		case <-ticker.C:
			if updateRunning {
				continue
			}
			updateRunning = true
			go func() {
				_, err := admin.UpdateFeed(ctx, &api.UpdateFeedRequest{SystemId: systemID, FeedId: feedID})
				fs.updateFinished <- err
			}()
		case err := <-fs.updateFinished:
			now := time.Now()
			if err == nil {
				lastSuccessfulUpdate = now
			}
			lastFinishedUpdate = now
			updateRunning = false
		case <-fs.statusRequest:
			fs.statusReply <- FeedStatus{
				SystemID:             systemID,
				FeedID:               feedID,
				CurrentlyRunning:     updateRunning,
				LastFinishedUpdate:   lastFinishedUpdate,
				LastSuccessfulUpdate: lastSuccessfulUpdate,
				Period:               period,
			}
		}
	}
}

func (fs *feedScheduler) reset(period time.Duration) {
	fs.resetRequest <- period
	<-fs.opDone
}

func (fs *feedScheduler) status() FeedStatus {
	fs.statusRequest <- struct{}{}
	return <-fs.statusReply
}

func (fs *feedScheduler) wait() {
	<-fs.opDone
}

type noOpScheduler struct{}

// NoOpScheduler returns a scheduler that does nothing.
//
// It is used when Transiter is running without a scheulder.
func NoOpScheduler() Scheduler {
	return noOpScheduler{}
}

func (noOpScheduler) Reset(ctx context.Context) error {
	// TODO: log an error
	return nil
}

func (noOpScheduler) ResetSystem(ctx context.Context, systemID string) error {
	// TODO: log an error
	return nil
}

func (noOpScheduler) Status() []FeedStatus {
	// TODO: log an error
	return []FeedStatus{}
}
