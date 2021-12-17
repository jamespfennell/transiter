package scheduler

import (
	"context"
	"database/sql"
	"testing"
	"time"

	"github.com/benbjohnson/clock"
	"github.com/jamespfennell/transiter/internal/gen/db"
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
		description       string
		newSystemIds      []string
		newAutoUpdateRows map[string][]db.ListAutoUpdateFeedsForSystemRow
		refreshF          func(*Scheduler) error
		runningPeriod     time.Duration
		expectedUpdates   map[systemAndFeed]int
	}{
		{
			description:  "just change periodicity of one feed",
			newSystemIds: []string{systemId1},
			newAutoUpdateRows: map[string][]db.ListAutoUpdateFeedsForSystemRow{
				systemId1: {
					{ID: feedId1, AutoUpdatePeriod: sql.NullInt32{Valid: true, Int32: 1000}},
				},
			},
			refreshF:      refreshSystem1,
			runningPeriod: 2000 * time.Millisecond,
			expectedUpdates: map[systemAndFeed]int{
				{systemId: systemId1, feedId: feedId1}: 2,
			},
		},
		{
			description:  "new feed in same system",
			newSystemIds: []string{systemId1},
			newAutoUpdateRows: map[string][]db.ListAutoUpdateFeedsForSystemRow{
				systemId1: {
					{ID: feedId1, AutoUpdatePeriod: sql.NullInt32{Valid: true, Int32: 500}},
					{ID: feedId2, AutoUpdatePeriod: sql.NullInt32{Valid: true, Int32: 500}},
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
			description:       "remove feed in system",
			newSystemIds:      []string{systemId1},
			newAutoUpdateRows: map[string][]db.ListAutoUpdateFeedsForSystemRow{},
			refreshF:          refreshSystem1,
			runningPeriod:     2000 * time.Millisecond,
			expectedUpdates:   map[systemAndFeed]int{},
		},
		{
			description:       "remove system",
			newSystemIds:      nil,
			newAutoUpdateRows: map[string][]db.ListAutoUpdateFeedsForSystemRow{},
			refreshF:          refreshSystem1,
			runningPeriod:     2000 * time.Millisecond,
			expectedUpdates:   map[systemAndFeed]int{},
		},
		{
			description:  "new system, only refresh the new one",
			newSystemIds: []string{systemId1, systemId2},
			newAutoUpdateRows: map[string][]db.ListAutoUpdateFeedsForSystemRow{
				systemId2: {
					{ID: feedId3, AutoUpdatePeriod: sql.NullInt32{Valid: true, Int32: 500}},
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
			description:  "new system, refresh all",
			newSystemIds: []string{systemId1, systemId2},
			newAutoUpdateRows: map[string][]db.ListAutoUpdateFeedsForSystemRow{
				systemId2: {
					{ID: feedId3, AutoUpdatePeriod: sql.NullInt32{Valid: true, Int32: 500}},
				},
			},
			refreshF:      refreshAll,
			runningPeriod: 2000 * time.Millisecond,
			expectedUpdates: map[systemAndFeed]int{
				{systemId: systemId2, feedId: feedId3}: 4,
			},
		},
	}
	for _, tc := range testCases {
		t.Run(tc.description, func(t *testing.T) {
			ctx, cancelFunc := context.WithCancel(context.Background())

			querier := &mockQuerier{
				systemIdToRows: make(map[string][]db.ListAutoUpdateFeedsForSystemRow),
			}
			updater := &mockUpdater{
				updateChan: make(chan systemAndFeed, 100),
			}
			clock := clock.NewMock()

			querier.systems = []db.System{
				{ID: systemId1},
			}
			querier.systemIdToRows[systemId1] = []db.ListAutoUpdateFeedsForSystemRow{
				{ID: feedId1, AutoUpdatePeriod: sql.NullInt32{Valid: true, Int32: 500}},
			}

			scheduler, err := New(ctx, clock, nil, func(database *sql.DB) db.Querier { return querier }, updater.UpdateFunc)
			if err != nil {
				t.Fatalf("failed to create scheduler: %s", err)
			}

			clock.Add(2000 * time.Millisecond)
			updates := updater.getUpdates(4)
			if len(updates) < 4 {
				t.Errorf("Didn't recieve enough updates: %d!=%d", len(updates), 4)
			} else {
				expected := systemAndFeed{systemId: systemId1, feedId: feedId1}
				for i, update := range updates {
					if update != expected {
						t.Errorf("Unexpected update[%d]: %s", i, updates[0])
					}
				}
			}

			var systems []db.System
			for _, systemId := range tc.newSystemIds {
				systems = append(systems, db.System{ID: systemId})
			}
			querier.systems = systems
			querier.systemIdToRows = tc.newAutoUpdateRows

			if err := tc.refreshF(scheduler); err != nil {
				t.Errorf("Unexpected error when refreshing: %s", err)
			}

			clock.Add(tc.runningPeriod)

			var numExpectedUpdates int
			for _, val := range tc.expectedUpdates {
				numExpectedUpdates += val
			}
			updates = updater.getUpdates(numExpectedUpdates)
			if len(updates) < numExpectedUpdates {
				t.Errorf("Didn't recieve enough updates: %d!=%d", len(updates), numExpectedUpdates)
			} else {
				expectedUpdates := map[systemAndFeed]int{}
				for k, v := range tc.expectedUpdates {
					expectedUpdates[k] = v
				}
				for _, update := range updates {
					if expectedUpdates[update] == 1 {
						delete(expectedUpdates, update)
					} else {
						expectedUpdates[update] = expectedUpdates[update] - 1
					}
				}
				if len(expectedUpdates) != 0 {
					t.Errorf("Unexpected updates:\n%+v\nExpected:\n%+v\n", updates, tc.expectedUpdates)
				}
			}

			cancelFunc()
			scheduler.Wait()

			close(updater.updateChan)
			for update := range updater.updateChan {
				t.Errorf("Unexpected update after scheduler stopped: %s", update)
			}
		})
	}
}

type mockQuerier struct {
	systemIdToRows map[string][]db.ListAutoUpdateFeedsForSystemRow
	systems        []db.System
	db.Querier
}

func (q *mockQuerier) ListSystems(ctx context.Context) ([]db.System, error) {
	return q.systems, nil
}

func (q *mockQuerier) ListAutoUpdateFeedsForSystem(ctx context.Context, systemID string) ([]db.ListAutoUpdateFeedsForSystemRow, error) {
	return q.systemIdToRows[systemID], nil
}

type mockUpdater struct {
	updateChan chan systemAndFeed
}

func (m *mockUpdater) UpdateFunc(ctx context.Context, _ *sql.DB, systemId, feedId string) error {
	m.updateChan <- systemAndFeed{systemId: systemId, feedId: feedId}
	return nil
}

func (m *mockUpdater) getUpdates(maxUpdates int) []systemAndFeed {
	if maxUpdates == 0 {
		return nil
	}
	timeoutChan := time.After(time.Duration(maxUpdates+1) * 500 * time.Millisecond)
	var result []systemAndFeed
	for {
		select {
		case s := <-m.updateChan:
			result = append(result, s)
			if len(result) == maxUpdates {
				return result
			}
		case <-timeoutChan:
			return result
		}
	}
}

type systemAndFeed struct {
	systemId, feedId string
}
