package scheduler

import (
	"context"
	"reflect"
	"sync"
	"testing"
	"time"

	"github.com/benbjohnson/clock"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"golang.org/x/exp/slog"
)

const systemID1 = "systemID1"
const feedID1 = "feedID1"
const feedID2 = "feedID2"
const systemID2 = "systemID2"
const feedID3 = "feedID3"

func TestScheduler(t *testing.T) {
	resetSystem1 := func(s *DefaultScheduler) error {
		return s.ResetSystem(context.Background(), systemID1)
	}
	resetSystem2 := func(s *DefaultScheduler) error {
		return s.ResetSystem(context.Background(), systemID2)
	}
	resetAll := func(s *DefaultScheduler) error {
		return s.Reset(context.Background())
	}
	initialForPeriodicTest := []SystemConfig{
		{
			ID: systemID1,
			FeedConfigs: []FeedConfig{
				periodicFeedConfig(feedID1, 500*time.Millisecond),
			},
		},
	}
	testCases := []struct {
		description     string
		initial         []SystemConfig
		update          []SystemConfig
		resetF          func(*DefaultScheduler) error
		runningPeriod   time.Duration
		expectedUpdates map[systemAndFeed]int
	}{
		{
			description: "increase period of one feed",
			initial:     initialForPeriodicTest,
			update: []SystemConfig{
				{
					ID: systemID1,
					FeedConfigs: []FeedConfig{
						periodicFeedConfig(feedID1, 1000*time.Millisecond),
					},
				},
			},
			resetF:        resetSystem1,
			runningPeriod: 2000 * time.Millisecond,
			expectedUpdates: map[systemAndFeed]int{
				{systemID: systemID1, feedID: feedID1}: 2,
			},
		},
		{
			description: "reduce period of one feed",
			initial:     initialForPeriodicTest,
			update: []SystemConfig{
				{
					ID: systemID1,
					FeedConfigs: []FeedConfig{
						periodicFeedConfig(feedID1, 100*time.Millisecond),
					},
				},
			},
			resetF:        resetSystem1,
			runningPeriod: 200 * time.Millisecond,
			expectedUpdates: map[systemAndFeed]int{
				{systemID: systemID1, feedID: feedID1}: 2,
			},
		},
		{
			description: "new feed in same system",
			initial:     initialForPeriodicTest,
			update: []SystemConfig{
				{
					ID: systemID1,
					FeedConfigs: []FeedConfig{
						periodicFeedConfig(feedID1, 500*time.Millisecond),
						periodicFeedConfig(feedID2, 500*time.Millisecond),
					},
				},
			},
			resetF:        resetSystem1,
			runningPeriod: 2000 * time.Millisecond,
			expectedUpdates: map[systemAndFeed]int{
				{systemID: systemID1, feedID: feedID1}: 4,
				{systemID: systemID1, feedID: feedID2}: 4,
			},
		},
		{
			description: "remove feed in system",
			initial:     initialForPeriodicTest,
			update: []SystemConfig{
				{
					ID:          systemID1,
					FeedConfigs: []FeedConfig{},
				},
			},
			resetF:          resetSystem1,
			runningPeriod:   2000 * time.Millisecond,
			expectedUpdates: map[systemAndFeed]int{},
		},
		{
			description:     "remove system",
			initial:         initialForPeriodicTest,
			update:          []SystemConfig{},
			resetF:          resetSystem1,
			runningPeriod:   2000 * time.Millisecond,
			expectedUpdates: map[systemAndFeed]int{},
		},
		{
			description:     "remove system, reset all",
			initial:         initialForPeriodicTest,
			update:          []SystemConfig{},
			resetF:          resetAll,
			runningPeriod:   2000 * time.Millisecond,
			expectedUpdates: map[systemAndFeed]int{},
		},
		{
			description: "new system, only reset the new one",
			initial:     initialForPeriodicTest,
			update: []SystemConfig{
				{
					ID: systemID1,
					FeedConfigs: []FeedConfig{
						periodicFeedConfig(feedID1, 500*time.Millisecond),
					},
				},
				{
					ID: systemID2,
					FeedConfigs: []FeedConfig{
						periodicFeedConfig(feedID3, 500*time.Millisecond),
					},
				},
			},
			resetF:        resetSystem2,
			runningPeriod: 2000 * time.Millisecond,
			expectedUpdates: map[systemAndFeed]int{
				{systemID: systemID1, feedID: feedID1}: 4,
				{systemID: systemID2, feedID: feedID3}: 4,
			},
		},
		{
			description: "new system, reset all",
			initial:     initialForPeriodicTest,
			update: []SystemConfig{
				{
					ID: systemID1,
					FeedConfigs: []FeedConfig{
						periodicFeedConfig(feedID1, 500*time.Millisecond),
					},
				},
				{
					ID: systemID2,
					FeedConfigs: []FeedConfig{
						periodicFeedConfig(feedID3, 500*time.Millisecond),
					},
				},
			},
			resetF:        resetAll,
			runningPeriod: 2000 * time.Millisecond,
			expectedUpdates: map[systemAndFeed]int{
				{systemID: systemID1, feedID: feedID1}: 4,
				{systemID: systemID2, feedID: feedID3}: 4,
			},
		},
		{
			description: "daily",
			initial:     initialForPeriodicTest,
			update: []SystemConfig{
				{
					ID: systemID2,
					FeedConfigs: []FeedConfig{
						dailyFeedConfig(feedID3, "05:00"),
					},
				},
			},
			resetF:        resetAll,
			runningPeriod: 3 * 24 * time.Hour,
			expectedUpdates: map[systemAndFeed]int{
				{systemID: systemID2, feedID: feedID3}: 3,
			},
		},
	}
	for _, tc := range testCases {
		t.Run(tc.description, func(t *testing.T) {
			ctx, cancelFunc := context.WithCancel(context.Background())
			defer cancelFunc()
			updateChan := make(chan systemAndFeed, 20)
			server := testServer{
				currentConfig: tc.initial,
				updateChan:    updateChan,
			}
			clock := clock.NewMock()

			scheduler := NewDefaultScheduler()
			var wg sync.WaitGroup
			wg.Add(1)
			go func() {
				scheduler.runWithClock(ctx, &server, &server, clock, slog.Default())
				wg.Done()
			}()
			if err := scheduler.Reset(ctx); err != nil {
				t.Fatalf("failed to create scheduler: %s", err)
			}

			clock.Add(2000 * time.Millisecond)

			updates := getUpdates(updateChan, 4)
			expected := map[systemAndFeed]int{
				{systemID: systemID1, feedID: feedID1}: 4,
			}
			if !reflect.DeepEqual(expected, updates) {
				t.Errorf("Updates got = %+v, want = %+v", updates, expected)
			}
			server.currentConfig = tc.update

			if err := tc.resetF(scheduler); err != nil {
				t.Errorf("Unexpected error when resetting: %s", err)
			}

			clock.Add(tc.runningPeriod)

			var numExpectedUpdates int
			for _, val := range tc.expectedUpdates {
				numExpectedUpdates += val
			}
			updates = getUpdates(updateChan, numExpectedUpdates)
			if !reflect.DeepEqual(tc.expectedUpdates, updates) {
				t.Errorf("Updates got = %+v, want = %+v", updates, tc.expectedUpdates)
			}

			cancelFunc()
			wg.Wait()
			close(updateChan)
			for update := range updateChan {
				t.Errorf("Unexpected update after scheduler stopped: %s", update)
			}
		})
	}
}

type testServer struct {
	api.UnimplementedPublicServer
	api.UnimplementedAdminServer
	currentConfig []SystemConfig
	updateChan    chan systemAndFeed
}

func (t testServer) ListSystems(context.Context, *api.ListSystemsRequest) (*api.ListSystemsReply, error) {
	systems := map[string]bool{}
	for _, c := range t.currentConfig {
		systems[c.ID] = true
	}
	resp := &api.ListSystemsReply{}
	for systemID := range systems {
		resp.Systems = append(resp.Systems, &api.System{
			Id: systemID,
		})
	}
	return resp, nil
}

func (t testServer) GetSystemConfig(ctx context.Context, req *api.GetSystemConfigRequest) (*api.SystemConfig, error) {
	resp := &api.SystemConfig{}
	for _, c := range t.currentConfig {
		if c.ID != req.SystemId {
			continue
		}
		for _, a := range c.FeedConfigs {
			feedConfig := &api.FeedConfig{
				Id: a.ID,
			}
			if a.Daily == "" {
				ms := a.Period.Milliseconds()
				feedConfig.SchedulingPolicy = api.FeedConfig_PERIODIC
				feedConfig.PeriodicUpdatePeriodMs = &ms
			} else {
				feedConfig.SchedulingPolicy = api.FeedConfig_DAILY
				feedConfig.DailyUpdateTime = a.Daily
				feedConfig.DailyUpdateTimezone = time.UTC.String()
			}
			resp.Feeds = append(resp.Feeds, feedConfig)
		}
	}
	return resp, nil
}

func (t testServer) UpdateFeed(ctx context.Context, req *api.UpdateFeedRequest) (*api.UpdateFeedReply, error) {
	t.updateChan <- systemAndFeed{systemID: req.SystemId, feedID: req.FeedId}
	return &api.UpdateFeedReply{}, nil
}

func (t testServer) ListAgencies(ctx context.Context, req *api.ListAgenciesRequest) (*api.ListAgenciesReply, error) {
	return &api.ListAgenciesReply{}, nil
}

func getUpdates(updateChan chan systemAndFeed, num int) map[systemAndFeed]int {
	if num == 0 {
		return map[systemAndFeed]int{}
	}
	timeoutChan := time.After(time.Duration(num+1) * 500 * time.Millisecond)
	m := map[systemAndFeed]int{}
	seen := 0
	for {
		select {
		case key := <-updateChan:
			m[key] = m[key] + 1
			seen += 1
			if seen == num {
				return m
			}
		case <-timeoutChan:
			return m
		}
	}
}

type systemAndFeed struct {
	systemID, feedID string
}

type SystemConfig struct {
	ID          string
	FeedConfigs []FeedConfig
}

type FeedConfig struct {
	ID     string
	Period time.Duration
	Daily  string
}

func periodicFeedConfig(id string, period time.Duration) FeedConfig {
	return FeedConfig{
		ID:     id,
		Period: period,
	}
}
func dailyFeedConfig(id string, time string) FeedConfig {
	return FeedConfig{
		ID:    id,
		Daily: time,
	}
}
