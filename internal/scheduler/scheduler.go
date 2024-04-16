// Package scheduler contains the periodic feed update scheduler.
//
// The scheduler reads the database configuration for all of the feeds to determines how often
// to update each one. Periodic updates are scheduled on different goroutines. The scheduler
// guarantees that for each feed there is only one update happening at a time.
//
// The scheduler is a highly concurrent component. Not only is it scheduling
// multiple feed updates at the same time, but can also receive concurrent reset requests to
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
// different channels. The scheduler will do different things depending on the message it receives:
// "things" include triggering a new feed update, shutting down, or resetting the
// periodic update configuration.
//
// As an example consider the process of resetting the configuration for a particular system after
// the system is updated. This process is triggered using the `Reset` function. That function
// sends a message on the right channel to the main run loop of the root scheduler. The root scheduler
// reads the message and creates the system scheduler if needed. It thens send a message to the
// system scheduler run loop with the new configuration. That run loop reads the message and
// propagates it to the feed schedulers contained inside.
package scheduler

import (
	"context"
	"fmt"
	"sort"
	"strconv"
	"strings"
	"time"

	"github.com/benbjohnson/clock"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/scheduler/ticker"
	"github.com/jamespfennell/transiter/internal/update"
	"golang.org/x/exp/slog"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

// Scheduler defines the API of a Transiter scheduler.
//
// The methods of this interface are invoked in the Transiter admin service.
type Scheduler interface {
	// Reset resets the scheduler with the current periodic update configuration for all systems.
	Reset(ctx context.Context) error
	// ResetSystem resets the scheduler for the provided system.
	ResetSystem(ctx context.Context, systemID string) error
	// Status returns a list of feed statuses for all feeds being periodically updated by the scheduler.
	Status(ctx context.Context) ([]FeedStatus, error)
}

// FeedStatus describes the status of one feed within a scheduler.
type FeedStatus struct {
	// ID of the system.
	SystemID string
	// The feed configuration being used.
	FeedConfig *api.FeedConfig
	// Update period.
	Period time.Duration
	// Time of the last update that finished.
	LastFinishedUpdate time.Time
	// Time of the last update that finished successfully.
	LastSuccessfulUpdate time.Time
	// Whether an update for this feed is currently running.
	CurrentlyRunning bool
}

// DefaultScheduler is Transiter's default scheduler.
type DefaultScheduler struct {
	resetAllRequest chan msg[struct{}, error]
	resetRequest    chan msg[string, error]
	statusRequest   chan msg[struct{}, []FeedStatus]
}

// NewDefaultScheduler creates a new instance of the default scheduler.
//
// This scheduler must be run using the `Run` method.
func NewDefaultScheduler() *DefaultScheduler {
	return &DefaultScheduler{
		resetAllRequest: make(chan msg[struct{}, error]),
		resetRequest:    make(chan msg[string, error]),
		statusRequest:   make(chan msg[struct{}, []FeedStatus]),
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
			logger.InfoCtx(ctx, "resetting system scheduler", slog.String("system_id", systemID))
			ss.scheduler.reset(feeds)
			return
		}
		logger.InfoCtx(ctx, "starting system scheduler", slog.String("system_id", systemID))
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
		logger.InfoCtx(ctx, "stopping system scheduler", slog.String("system_id", systemID))
		ss.cancelFunc()
		ss.scheduler.wait()
		delete(systemSchedulers, systemID)
	}
	resetSystem := func(systemID string) error {
		logger := logger.With(slog.String("system_id", systemID))
		systemResp, err := admin.GetSystemConfig(ctx, &api.GetSystemConfigRequest{SystemId: systemID})
		if err != nil {
			s, ok := status.FromError(err)
			if ok && s.Code() == codes.NotFound {
				stopScheduler(systemID)
				return nil
			}
			return fmt.Errorf("failed to get system config for system %s during scheduler reset: %w", systemID, err)
		}
		agenciesResp, err := public.ListAgencies(ctx, &api.ListAgenciesRequest{SystemId: systemID})
		if err != nil {
			return fmt.Errorf("failed to list get agencies for system %s during scheduler reset: %w", systemID, err)
		}
		var feeds []*api.FeedConfig
		for i, feed := range systemResp.Feeds {
			logger := logger.With(slog.String("feed_id", feed.GetId()))
			NormalizeSchedulingPolicy(logger, feed, i, agenciesResp.Agencies)
			logger.DebugCtx(ctx, fmt.Sprintf("normalized feed config: %+v", feed))
			if feed.GetSchedulingPolicy() == api.FeedConfig_NONE {
				continue
			}
			feeds = append(feeds, feed)
		}
		if len(feeds) == 0 {
			stopScheduler(systemID)
		} else {
			resetScheduler(systemID, feeds)
		}
		return nil
	}
	for {
		select {
		case <-ctx.Done():
			for systemID := range systemSchedulers {
				stopScheduler(systemID)
			}
			return
		case msg := <-s.resetAllRequest:
			logger.InfoCtx(ctx, "resetting scheduler")
			resp, err := public.ListSystems(ctx, &api.ListSystemsRequest{})
			if err != nil {
				msg.resp <- fmt.Errorf("failed to get systems data during scheduler reset: %w", err)
				break
			}
			updatedSystems := map[string]bool{}
			for _, system := range resp.Systems {
				err = resetSystem(system.GetId())
				if err != nil {
					break
				}
				updatedSystems[system.GetId()] = true
			}
			for systemID := range systemSchedulers {
				if updatedSystems[systemID] {
					continue
				}
				stopScheduler(systemID)
			}
			msg.resp <- err
		case msg := <-s.resetRequest:
			msg.resp <- resetSystem(msg.req)
		case msg := <-s.statusRequest:
			var response []FeedStatus
			for _, ss := range systemSchedulers {
				response = append(response, ss.scheduler.status()...)
			}
			msg.resp <- response
		}
	}
}

func (s *DefaultScheduler) Reset(ctx context.Context) error {
	msg := newMsg[struct{}, error](struct{}{})
	s.resetAllRequest <- msg
	select {
	case err := <-msg.resp:
		return err
	case <-ctx.Done():
		return ctx.Err()
	}
}

func (s *DefaultScheduler) ResetSystem(ctx context.Context, systemID string) error {
	msg := newMsg[string, error](systemID)
	s.resetRequest <- msg
	select {
	case err := <-msg.resp:
		return err
	case <-ctx.Done():
		return ctx.Err()
	}
}

func (s *DefaultScheduler) Status(ctx context.Context) ([]FeedStatus, error) {
	msg := newMsg[struct{}, []FeedStatus](struct{}{})
	s.statusRequest <- msg
	select {
	case feeds := <-msg.resp:
		sort.Slice(feeds, func(i, j int) bool {
			if feeds[i].SystemID == feeds[j].SystemID {
				return feeds[i].FeedConfig.GetId() < feeds[j].FeedConfig.GetId()
			}
			return feeds[i].SystemID < feeds[j].SystemID
		})
		return feeds, nil
	case <-ctx.Done():
		return nil, ctx.Err()
	}
}

type systemScheduler struct {
	resetRequest  chan msg[[]*api.FeedConfig, struct{}]
	statusRequest chan msg[struct{}, []FeedStatus]
	done          chan struct{}
}

func newSystemScheduler(ctx context.Context, admin api.AdminServer, clock clock.Clock, systemID string) *systemScheduler {
	ss := &systemScheduler{
		resetRequest:  make(chan msg[[]*api.FeedConfig, struct{}]),
		statusRequest: make(chan msg[struct{}, []FeedStatus]),
		done:          make(chan struct{}),
	}
	go ss.run(ctx, admin, clock, systemID)
	return ss
}

func (s *systemScheduler) run(ctx context.Context, admin api.AdminServer, clock clock.Clock, systemID string) {
	feedSchedulers := map[string]struct {
		scheduler  *feedScheduler
		cancelFunc context.CancelFunc
	}{}
	stopFeedSchedulers := func() {
		for _, fs := range feedSchedulers {
			fs.cancelFunc()
		}
		for feedID, fs := range feedSchedulers {
			fs.scheduler.wait()
			delete(feedSchedulers, feedID)
		}
	}
	for {
		select {
		case <-ctx.Done():
			stopFeedSchedulers()
			close(s.done)
			return
		case msg := <-s.resetRequest:
			stopFeedSchedulers()
			for _, feed := range msg.req {
				feedCtx, cancelFunc := context.WithCancel(ctx)
				feedSchedulers[feed.Id] = struct {
					scheduler  *feedScheduler
					cancelFunc context.CancelFunc
				}{
					scheduler:  newFeedScheduler(feedCtx, admin, clock, systemID, feed),
					cancelFunc: cancelFunc,
				}
			}
			msg.resp <- struct{}{}
		case msg := <-s.statusRequest:
			var response []FeedStatus
			for _, fs := range feedSchedulers {
				response = append(response, fs.scheduler.status())
			}
			msg.resp <- response
		}
	}
}

func (s *systemScheduler) reset(feedConfigs []*api.FeedConfig) {
	msg := newMsg[[]*api.FeedConfig, struct{}](feedConfigs)
	s.resetRequest <- msg
	<-msg.resp
}

func (s *systemScheduler) status() []FeedStatus {
	msg := newMsg[struct{}, []FeedStatus](struct{}{})
	s.statusRequest <- msg
	return <-msg.resp
}

func (s *systemScheduler) wait() {
	<-s.done
}

type feedScheduler struct {
	statusRequest chan msg[struct{}, FeedStatus]
	done          chan struct{}
}

func newFeedScheduler(ctx context.Context, admin api.AdminServer, clock clock.Clock, systemID string, feedConfig *api.FeedConfig) *feedScheduler {
	fs := &feedScheduler{
		statusRequest: make(chan msg[struct{}, FeedStatus]),
		done:          make(chan struct{}),
	}
	initComplete := make(chan struct{})
	go fs.run(ctx, admin, clock, systemID, feedConfig, initComplete)
	<-initComplete
	return fs
}

func (fs *feedScheduler) run(ctx context.Context, admin api.AdminServer, clock clock.Clock, systemID string, feedConfig *api.FeedConfig, initComplete chan struct{}) {
	var t ticker.Ticker
	switch feedConfig.GetSchedulingPolicy() {
	case api.FeedConfig_DAILY:
		hour, minute, _ := parseDailyUpdateTime(feedConfig.GetDailyUpdateTime())
		tz, _ := time.LoadLocation(feedConfig.GetDailyUpdateTimezone())
		t = ticker.NewDaily(clock, hour, minute, tz)
	case api.FeedConfig_PERIODIC:
		t = ticker.NewPeriodic(clock, time.Duration(feedConfig.GetPeriodicUpdatePeriodMs())*time.Millisecond)
	default:
		panic(fmt.Sprintf("feed scheduler can't be started with scheduling policy %s", feedConfig.GetSchedulingPolicy()))
	}
	defer t.Stop()
	var lastSuccessfulUpdate time.Time
	var lastFinishedUpdate time.Time
	updateRunning := false
	updateFinished := make(chan error)
	initComplete <- struct{}{}
	for {
		select {
		case <-ctx.Done():
			if updateRunning {
				// wait for the update to finish
				<-updateFinished
			}
			close(fs.done)
			return
		case <-t.C():
			if updateRunning {
				continue
			}
			updateRunning = true
			go func() {
				_, err := admin.UpdateFeed(ctx, &api.UpdateFeedRequest{SystemId: systemID, FeedId: feedConfig.GetId()})
				updateFinished <- err
			}()
		case err := <-updateFinished:
			now := time.Now()
			if err == nil {
				lastSuccessfulUpdate = now
			}
			lastFinishedUpdate = now
			updateRunning = false
		case msg := <-fs.statusRequest:
			msg.resp <- FeedStatus{
				SystemID:             systemID,
				FeedConfig:           feedConfig,
				CurrentlyRunning:     updateRunning,
				LastFinishedUpdate:   lastFinishedUpdate,
				LastSuccessfulUpdate: lastSuccessfulUpdate,
			}
		}
	}
}

func (fs *feedScheduler) status() FeedStatus {
	msg := newMsg[struct{}, FeedStatus](struct{}{})
	fs.statusRequest <- msg
	return <-msg.resp
}

func (fs *feedScheduler) wait() {
	<-fs.done
}

type noOpScheduler struct {
	logger *slog.Logger
}

// NoOpScheduler returns a scheduler that does nothing.
//
// It is used when Transiter is running without a scheduler.
func NoOpScheduler(logger *slog.Logger) Scheduler {
	return noOpScheduler{logger: logger}
}

func (s noOpScheduler) Reset(ctx context.Context) error {
	s.logger.WarnCtx(ctx, "the no-op scheduler is running so the reset request does nothing")
	return nil
}

func (s noOpScheduler) ResetSystem(ctx context.Context, systemID string) error {
	s.logger.WarnCtx(ctx, "the no-op scheduler is running so the reset system request does nothing", slog.String("system_id", systemID))
	return nil
}

func (s noOpScheduler) Status(ctx context.Context) ([]FeedStatus, error) {
	s.logger.WarnCtx(ctx, "the no-op scheduler is running so the status request does nothing")
	return []FeedStatus{}, nil
}

type msg[Req any, Resp any] struct {
	req  Req
	resp chan Resp
}

func newMsg[Req any, Resp any](req Req) msg[Req, Resp] {
	return msg[Req, Resp]{
		req:  req,
		resp: make(chan Resp),
	}
}

// NormalizeSchedulingPolicy normalizes the scheduling policy fields in the feed config.
//
// After this function runs the following guarantees are in place:
//
//   - The scheduling policy is NONE, PERIODIC or DAILY.
//     In particular, the DEFAULT strategy does not appear.
//
//   - If the scheduling policy is PERIODIC,
//     the `periodic_update_period_ms` field has a valid value.
//
//   - If the scheduling policy is DAILY,
//     the `daily_update_time` and `daily_update_timezone` fields have valid values.
//     For the timezone field, this means the field contains a timezone that the current OS recognizes.
func NormalizeSchedulingPolicy(logger *slog.Logger, feedConfig *api.FeedConfig, position int, agencies []*api.Agency) {
	update.NormalizeFeedConfig(feedConfig)
	if feedConfig.SchedulingPolicy == api.FeedConfig_DEFAULT {
		if feedConfig.Type == update.GtfsRealtime {
			feedConfig.SchedulingPolicy = api.FeedConfig_PERIODIC
		} else {
			feedConfig.SchedulingPolicy = api.FeedConfig_DAILY
		}
	}
	switch feedConfig.SchedulingPolicy {
	case api.FeedConfig_PERIODIC:
		if feedConfig.PeriodicUpdatePeriodMs == nil {
			p := int64(5000)
			//lint:ignore SA1019 this is where we apply the deprecation logic!
			if updatePeriodS := feedConfig.GetUpdatePeriodS(); updatePeriodS != 0 {
				p = int64(updatePeriodS * 1000)
			}
			feedConfig.PeriodicUpdatePeriodMs = &p
		}
	case api.FeedConfig_DAILY:
		// We check if the provided time is valid
		if feedConfig.GetDailyUpdateTime() != "" {
			if _, _, ok := parseDailyUpdateTime(feedConfig.GetDailyUpdateTime()); !ok {
				logger.Error(fmt.Sprintf("could not parse provided time %q; will fall back to default", feedConfig.GetDailyUpdateTime()))
				feedConfig.DailyUpdateTime = ""
			}
		}
		// Then, if there is no time provided we populate a default
		if feedConfig.GetDailyUpdateTime() == "" {
			mins := 3*60 + 10*position
			feedConfig.DailyUpdateTime = fmt.Sprintf("%02d:%02d", mins/60, mins%60)
		}

		// We check if the provided timezone is valid
		if tz := feedConfig.GetDailyUpdateTimezone(); tz != "" {
			if _, err := time.LoadLocation(tz); err != nil {
				logger.Error(fmt.Sprintf("could not parse provided timezone %q; will fall back to default", tz))
				feedConfig.DailyUpdateTimezone = ""
			}
		}
		// Then, if there is no timezone set we populate a default
		if feedConfig.GetDailyUpdateTimezone() == "" {
			var tz string
			for _, agency := range agencies {
				candidateTz := agency.GetTimezone()
				if candidateTz == "" {
					continue
				}
				if _, err := time.LoadLocation(candidateTz); err == nil {
					tz = candidateTz
					break
				}
			}
			if tz == "" {
				tz = time.UTC.String()
			}
			feedConfig.DailyUpdateTimezone = tz
		}
	}
}

func parseDailyUpdateTime(s string) (int, int, bool) {
	pieces := strings.Split(s, ":")
	if len(pieces) != 2 {
		return 0, 0, false
	}
	h, err := strconv.Atoi(strings.TrimSpace(pieces[0]))
	if err != nil {
		return 0, 0, false
	}
	m, err := strconv.Atoi(strings.TrimSpace(pieces[1]))
	if err != nil {
		return 0, 0, false
	}
	return h, m, true
}
