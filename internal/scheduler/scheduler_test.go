package scheduler

import (
	"context"
	"database/sql"
	"sync"
	"testing"
	"time"

	"github.com/benbjohnson/clock"
	"github.com/jamespfennell/transiter/internal/gen/db"
)

const systemId = "systemId"
const feedId = "feedId"

func TestScheduler(t *testing.T) {
	ctx, cancelFunc := context.WithCancel(context.Background())

	querier := &mockQuerier{
		systemIdToRows: make(map[string][]db.ListAutoUpdateFeedsForSystemRow),
	}
	updater := &mockUpdater{
		updateChan: make(chan systemAndFeed, 100),
	}
	clock := clock.NewMock()

	querier.systems = []db.System{
		{ID: systemId},
	}
	querier.systemIdToRows[systemId] = []db.ListAutoUpdateFeedsForSystemRow{
		{ID: feedId, AutoUpdatePeriod: sql.NullInt32{Valid: true, Int32: 500}},
	}

	scheduler, err := New(ctx, clock, querier, updater.UpdateFunc)
	if err != nil {
		t.Fatalf("failed to create scheduler: %s", err)
	}

	readyChan := make(chan struct{})
	var wg sync.WaitGroup
	wg.Add(1)
	go func() {
		scheduler.Run(readyChan)
		wg.Done()
	}()

	<-readyChan

	clock.Add(4 * 500 * time.Millisecond)
	updates := updater.getUpdates(4)
	if len(updates) < 4 {
		t.Errorf("Didn't recieve enough updates: %d!=%d", len(updates), 4)
	} else {
		expected := systemAndFeed{systemId: systemId, feedId: feedId}
		if updates[0] != expected {
			t.Errorf("Unexpected update: %s", updates[0])
		}
	}

	if err := scheduler.Refresh(ctx, systemId); err != nil {
		t.Errorf("Unexpected error when refreshing: %s", err)
	}

	querier.systemIdToRows[systemId] = []db.ListAutoUpdateFeedsForSystemRow{
		{ID: feedId, AutoUpdatePeriod: sql.NullInt32{Valid: true, Int32: 500}},
	}
	if err := scheduler.Refresh(ctx, systemId); err != nil {
		t.Errorf("Unexpected error when refreshing: %s", err)
	}

	clock.Add(4 * 500 * time.Millisecond)
	updates = updater.getUpdates(4)
	if len(updates) < 4 {
		t.Errorf("Didn't recieve enough updates: %d!=%d", len(updates), 4)
	} else {
		expected := systemAndFeed{systemId: systemId, feedId: feedId}
		if updates[0] != expected {
			t.Errorf("Unexpected update: %s", updates[0])
		}
	}

	querier.systemIdToRows[systemId] = []db.ListAutoUpdateFeedsForSystemRow{
		{ID: feedId, AutoUpdatePeriod: sql.NullInt32{Valid: true, Int32: 1000}},
	}
	if err := scheduler.Refresh(ctx, systemId); err != nil {
		t.Errorf("Unexpected error when refreshing: %s", err)
	}

	clock.Add(4 * 500 * time.Millisecond)
	updates = updater.getUpdates(2)
	if len(updates) < 2 {
		t.Errorf("Didn't recieve enough updates: %d!=%d", len(updates), 2)
	} else {
		expected := systemAndFeed{systemId: systemId, feedId: feedId}
		if updates[0] != expected {
			t.Errorf("Unexpected update: %s", updates[0])
		}
	}

	cancelFunc()
	wg.Wait()

	close(updater.updateChan)
	for update := range updater.updateChan {
		t.Errorf("Unexpected update after scheduler stopped: %s", update)
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

func (m *mockUpdater) UpdateFunc(ctx context.Context, systemId, feedId string) {
	m.updateChan <- systemAndFeed{systemId: systemId, feedId: feedId}
}

func (m *mockUpdater) getUpdates(maxUpdates int) []systemAndFeed {
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
