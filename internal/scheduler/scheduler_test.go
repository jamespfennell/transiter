package scheduler

import (
	"context"
	"reflect"
	"sync"
	"testing"
	"time"

	"github.com/benbjohnson/clock"
	"github.com/jamespfennell/transiter/internal/gen/api"
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
	testCases := []struct {
		description     string
		update          []SystemConfig
		resetF          func(*DefaultScheduler) error
		runningPeriod   time.Duration
		expectedUpdates map[systemAndFeed]int
	}{
		{
			description: "just change period of one feed",
			update: []SystemConfig{
				{
					ID: systemID1,
					FeedConfigs: []FeedConfig{
						{
							ID:     feedID1,
							Period: 1000 * time.Millisecond,
						},
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
			description: "new feed in same system",
			update: []SystemConfig{
				{
					ID: systemID1,
					FeedConfigs: []FeedConfig{
						{
							ID:     feedID1,
							Period: 500 * time.Millisecond,
						},
						{
							ID:     feedID2,
							Period: 500 * time.Millisecond,
						},
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
			update:          []SystemConfig{},
			resetF:          resetSystem1,
			runningPeriod:   2000 * time.Millisecond,
			expectedUpdates: map[systemAndFeed]int{},
		},
		{
			description: "new system, only reset the new one",
			update: []SystemConfig{
				{
					ID: systemID1,
					FeedConfigs: []FeedConfig{
						{
							ID:     feedID1,
							Period: 500 * time.Millisecond,
						},
					},
				},
				{
					ID: systemID2,
					FeedConfigs: []FeedConfig{
						{
							ID:     feedID3,
							Period: 500 * time.Millisecond,
						},
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
			update: []SystemConfig{
				{
					ID: systemID1,
					FeedConfigs: []FeedConfig{
						{
							ID:     feedID1,
							Period: 500 * time.Millisecond,
						},
					},
				},
				{
					ID: systemID2,
					FeedConfigs: []FeedConfig{
						{
							ID:     feedID3,
							Period: 500 * time.Millisecond,
						},
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
	}
	for _, tc := range testCases {
		t.Run(tc.description, func(t *testing.T) {
			ctx, cancelFunc := context.WithCancel(context.Background())
			defer cancelFunc()
			updateChan := make(chan systemAndFeed, 20)
			server := testServer{
				currentConfig: []SystemConfig{
					{
						ID: systemID1,
						FeedConfigs: []FeedConfig{
							{
								ID:     feedID1,
								Period: 500 * time.Millisecond,
							},
						},
					},
				},
				updateChan: updateChan,
			}
			clock := clock.NewMock()

			scheduler := NewDefaultScheduler()
			var wg sync.WaitGroup
			wg.Add(1)
			go func() {
				scheduler.runWithClock(ctx, &server, &server, clock)
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
				t.Errorf("Unexpected error when reseting: %s", err)
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
			ms := a.Period.Seconds()
			resp.Feeds = append(resp.Feeds, &api.FeedConfig{
				Id:             a.ID,
				UpdateStrategy: api.FeedConfig_PERIODIC,
				UpdatePeriodS:  &ms,
			})
		}
	}
	return resp, nil
}

func (t testServer) UpdateFeed(ctx context.Context, req *api.UpdateFeedRequest) (*api.UpdateFeedReply, error) {
	t.updateChan <- systemAndFeed{systemID: req.SystemId, feedID: req.FeedId}
	return &api.UpdateFeedReply{}, nil
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
}
