package scheduler

import (
	"context"
	"reflect"
	"testing"
	"time"

	"github.com/benbjohnson/clock"
)

const systemId1 = "systemId1"
const feedId1 = "feedId1"
const feedId2 = "feedId2"
const systemId2 = "systemId2"
const feedId3 = "feedId3"

func TestScheduler(t *testing.T) {
	refreshSystem1 := func(s *Scheduler) error {
		return s.Refresh(context.Background(), systemId1)
	}
	refreshSystem2 := func(s *Scheduler) error {
		return s.Refresh(context.Background(), systemId2)
	}
	refreshAll := func(s *Scheduler) error {
		return s.RefreshAll(context.Background())
	}
	testCases := []struct {
		description     string
		update          []SystemConfig
		refreshF        func(*Scheduler) error
		runningPeriod   time.Duration
		expectedUpdates map[systemAndFeed]int
	}{
		{
			description: "just change periodicity of one feed",
			update: []SystemConfig{
				{
					Id: systemId1,
					FeedConfigs: []FeedConfig{
						{
							Id:     feedId1,
							Period: 1000 * time.Millisecond,
						},
					},
				},
			},
			refreshF:      refreshSystem1,
			runningPeriod: 2000 * time.Millisecond,
			expectedUpdates: map[systemAndFeed]int{
				{systemId: systemId1, feedId: feedId1}: 2,
			},
		},
		{
			description: "new feed in same system",
			update: []SystemConfig{
				{
					Id: systemId1,
					FeedConfigs: []FeedConfig{
						{
							Id:     feedId1,
							Period: 500 * time.Millisecond,
						},
						{
							Id:     feedId2,
							Period: 500 * time.Millisecond,
						},
					},
				},
			},
			refreshF:      refreshSystem1,
			runningPeriod: 2000 * time.Millisecond,
			expectedUpdates: map[systemAndFeed]int{
				{systemId: systemId1, feedId: feedId1}: 4,
				{systemId: systemId1, feedId: feedId2}: 4,
			},
		},
		{
			description: "remove feed in system",
			update: []SystemConfig{
				{
					Id:          systemId1,
					FeedConfigs: []FeedConfig{},
				},
			},
			refreshF:        refreshSystem1,
			runningPeriod:   2000 * time.Millisecond,
			expectedUpdates: map[systemAndFeed]int{},
		},
		{
			description:     "remove system",
			update:          []SystemConfig{},
			refreshF:        refreshSystem1,
			runningPeriod:   2000 * time.Millisecond,
			expectedUpdates: map[systemAndFeed]int{},
		},
		{
			description: "new system, only refresh the new one",
			update: []SystemConfig{
				{
					Id: systemId1,
					FeedConfigs: []FeedConfig{
						{
							Id:     feedId1,
							Period: 500 * time.Millisecond,
						},
					},
				},
				{
					Id: systemId2,
					FeedConfigs: []FeedConfig{
						{
							Id:     feedId3,
							Period: 500 * time.Millisecond,
						},
					},
				},
			},
			refreshF:      refreshSystem2,
			runningPeriod: 2000 * time.Millisecond,
			expectedUpdates: map[systemAndFeed]int{
				{systemId: systemId1, feedId: feedId1}: 4,
				{systemId: systemId2, feedId: feedId3}: 4,
			},
		},
		{
			description: "new system, refresh all",
			update: []SystemConfig{
				{
					Id: systemId1,
					FeedConfigs: []FeedConfig{
						{
							Id:     feedId1,
							Period: 500 * time.Millisecond,
						},
					},
				},
				{
					Id: systemId2,
					FeedConfigs: []FeedConfig{
						{
							Id:     feedId3,
							Period: 500 * time.Millisecond,
						},
					},
				},
			},
			refreshF:      refreshAll,
			runningPeriod: 2000 * time.Millisecond,
			expectedUpdates: map[systemAndFeed]int{
				{systemId: systemId1, feedId: feedId1}: 4,
				{systemId: systemId2, feedId: feedId3}: 4,
			},
		},
	}
	for _, tc := range testCases {
		t.Run(tc.description, func(t *testing.T) {
			ctx, cancelFunc := context.WithCancel(context.Background())
			defer cancelFunc()

			ops := testOps{
				currentConfig: []SystemConfig{
					{
						Id: systemId1,
						FeedConfigs: []FeedConfig{
							{
								Id:     feedId1,
								Period: 500 * time.Millisecond,
							},
						},
					},
				},
				updateChan: make(chan systemAndFeed, 20),
			}
			clock := clock.NewMock()

			scheduler, err := New(ctx, clock, &ops)
			if err != nil {
				t.Fatalf("failed to create scheduler: %s", err)
			}

			clock.Add(2000 * time.Millisecond)

			updates := ops.getUpdates(4)
			expected := map[systemAndFeed]int{
				{systemId: systemId1, feedId: feedId1}: 4,
			}
			if !reflect.DeepEqual(expected, updates) {
				t.Errorf("Updates got = %+v, want = %+v", updates, expected)
			}

			ops.currentConfig = tc.update

			if err := tc.refreshF(scheduler); err != nil {
				t.Errorf("Unexpected error when refreshing: %s", err)
			}

			clock.Add(tc.runningPeriod)

			var numExpectedUpdates int
			for _, val := range tc.expectedUpdates {
				numExpectedUpdates += val
			}
			updates = ops.getUpdates(numExpectedUpdates)
			if !reflect.DeepEqual(tc.expectedUpdates, updates) {
				t.Errorf("Updates got = %+v, want = %+v", updates, tc.expectedUpdates)
			}

			cancelFunc()
			scheduler.Wait()
			close(ops.updateChan)
			for update := range ops.updateChan {
				t.Errorf("Unexpected update after scheduler stopped: %s", update)
			}
		})
	}
}

type testOps struct {
	currentConfig []SystemConfig
	updateChan    chan systemAndFeed
}

func (ops *testOps) ListSystemConfigs(ctx context.Context) ([]SystemConfig, error) {
	return ops.currentConfig, nil
}

func (ops *testOps) GetSystemConfig(ctx context.Context, systemId string) (SystemConfig, error) {
	for _, config := range ops.currentConfig {
		if config.Id == systemId {
			return config, nil
		}
	}
	return SystemConfig{Id: systemId}, nil
}

func (ops *testOps) UpdateFeed(ctx context.Context, systemId, feedId string) error {
	ops.updateChan <- systemAndFeed{systemId: systemId, feedId: feedId}
	return nil
}

func (ops *testOps) getUpdates(num int) map[systemAndFeed]int {
	if num == 0 {
		return map[systemAndFeed]int{}
	}
	timeoutChan := time.After(time.Duration(num+1) * 500 * time.Millisecond)
	m := map[systemAndFeed]int{}
	seen := 0
	for {
		select {
		case key := <-ops.updateChan:
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
	systemId, feedId string
}
