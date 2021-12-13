// Package scheduler contains the periodic feed update scheduler.
package scheduler

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/benbjohnson/clock"
	"github.com/jamespfennell/transiter/internal/gen/db"
)

type UpdateFunc func(ctx context.Context, systemId, feedId string)

type Scheduler struct {
	ctx              context.Context
	clock            clock.Clock
	querier          db.Querier
	updateFunc       UpdateFunc
	systemSchedulers map[string]*systemScheduler
	refreshChan      chan *systemScheduler
}

func New(ctx context.Context, clock clock.Clock, querier db.Querier, updateFunc UpdateFunc) (*Scheduler, error) {
	systems, err := querier.ListSystems(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to get systems data during scheduler initialization: %w", err)
	}
	s := &Scheduler{
		ctx:              ctx,
		clock:            clock,
		querier:          querier,
		updateFunc:       updateFunc,
		systemSchedulers: make(map[string]*systemScheduler),
		refreshChan:      make(chan *systemScheduler),
	}
	for _, system := range systems {
		s.systemSchedulers[system.ID], err = s.newSystemScheduler(s.ctx, system.ID)
		if err != nil {
			return nil, fmt.Errorf("failed to get data for system %q during scheduler initialization: %w", system.ID, err)
		}
	}
	return s, nil
}

func (s *Scheduler) Run(readyChan chan struct{}) {
	log.Printf("Running the scheduler\n")
	for _, systemScheduler := range s.systemSchedulers {
		systemScheduler.start(s.ctx)
	}
	if readyChan != nil {
		close(readyChan)
	}
	for {
		select {
		case <-s.ctx.Done():
			for _, systemScheduler := range s.systemSchedulers {
				systemScheduler.stop()
			}
			return
		case newSS := <-s.refreshChan:
			log.Printf("Refreshing scheduler for system %q\n", newSS.systemId)
			if oldSS := s.systemSchedulers[newSS.systemId]; oldSS != nil {
				oldSS.stop()
				delete(s.systemSchedulers, newSS.systemId)
			}
			if !newSS.empty() {
				s.systemSchedulers[newSS.systemId] = newSS
				newSS.start(s.ctx)
			}
			close(newSS.pendingChan)
		}
	}
}

func (s *Scheduler) Refresh(ctx context.Context, systemId string) error {
	log.Printf("Preparing to refresh scheduler for system %q\n", systemId)
	ss, err := s.newSystemScheduler(ctx, systemId)
	if err != nil {
		return err
	}
	s.refreshChan <- ss
	select {
	case <-ss.pendingChan:
		return nil
	case <-ctx.Done():
		return fmt.Errorf("context cancelled before refresh completed")
	}
}

type systemScheduler struct {
	scheduler     *Scheduler
	systemId      string
	feedSchedules []feedSchedule
	pendingChan   chan struct{}
	cancelFunc    context.CancelFunc
	cancelWg      sync.WaitGroup
}

func (s *Scheduler) newSystemScheduler(ctx context.Context, systemId string) (*systemScheduler, error) {
	ss := &systemScheduler{
		scheduler:   s,
		systemId:    systemId,
		pendingChan: make(chan struct{}),
	}
	feeds, err := s.querier.ListAutoUpdateFeedsForSystem(ctx, systemId)
	if err != nil {
		return nil, err
	}
	for _, feed := range feeds {
		period := 500 * time.Millisecond
		if feed.AutoUpdatePeriod.Valid {
			period = time.Millisecond * time.Duration(feed.AutoUpdatePeriod.Int32)
		}
		ss.feedSchedules = append(ss.feedSchedules, feedSchedule{
			feedId: feed.ID,
			period: period,
		})
	}
	return ss, nil
}

func (s *systemScheduler) start(ctx context.Context) {
	ctx, s.cancelFunc = context.WithCancel(ctx)
	for _, feed := range s.feedSchedules {
		feed := feed
		s.cancelWg.Add(1)
		// Creating the ticker outside the goroutine makes its start time more deterministic.
		ticker := s.scheduler.clock.Ticker(feed.period)
		go func() {
			defer func() {
				ticker.Stop()
				log.Printf("Stopped schedule for %s/%s (period was %s)\n", s.systemId, feed.feedId, feed.period)
				s.cancelWg.Done()
			}()
			log.Printf("Started schedule for %s/%s with period %s\n", s.systemId, feed.feedId, feed.period)
			for {
				select {
				case <-ctx.Done():
					return
				case <-ticker.C:
					s.scheduler.updateFunc(ctx, s.systemId, feed.feedId)
				}
			}
		}()
	}
}

func (s *systemScheduler) stop() {
	s.cancelFunc()
	s.cancelWg.Wait()
}

func (s *systemScheduler) empty() bool {
	return len(s.feedSchedules) == 0
}

type feedSchedule struct {
	feedId string
	period time.Duration
}
