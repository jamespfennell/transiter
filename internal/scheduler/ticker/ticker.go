// Package ticker implements tickers for the scheduler.
package ticker

import (
	"math/rand"
	"time"

	"github.com/benbjohnson/clock"
)

// Ticker describes the interface for tickers in this package.
type Ticker interface {
	// C returns the channel that ticks are sent on.
	C() <-chan time.Time
	// Stop stops the ticker.
	Stop()
}

type periodicTicker struct {
	c     chan time.Time
	stopC chan chan struct{}
}

// NewPeriodic creates a new ticker based on the provided clock and with the provided period.
//
// This ticker ticks at a given period like the standard library's ticker, but has an additional feature.
// Before sending the first tick it waits a random duration of time (but no more than the period).
// This means that ticks are smoothed out across different tickers started at the same time.
func NewPeriodic(clock clock.Clock, period time.Duration) Ticker {
	t := periodicTicker{
		c:     make(chan time.Time),
		stopC: make(chan chan struct{}),
	}
	initComplete := make(chan struct{})
	go t.run(clock, period, initComplete)
	<-initComplete
	return &t
}

func (t *periodicTicker) C() <-chan time.Time {
	return t.c
}

// Stop stops the ticker.
func (t *periodicTicker) Stop() {
	reply := make(chan struct{})
	t.stopC <- reply
	<-reply
}

func (t *periodicTicker) run(clock clock.Clock, period time.Duration, initComplete chan struct{}) {
	rand := rand.New(rand.NewSource(clock.Now().UnixNano()))
	tickerPeriod := time.Duration(float64(period) * rand.Float64())
	base := clock.Ticker(tickerPeriod)
	initComplete <- struct{}{}
	for {
		select {
		case tickTime := <-base.C:
			t.c <- tickTime
			if tickerPeriod != period {
				tickerPeriod = period
				base.Reset(tickerPeriod)
			}
		case reply := <-t.stopC:
			base.Stop()
			reply <- struct{}{}
			return
		}
	}
}

type dailyTicker struct {
	c     chan time.Time
	stopC chan chan struct{}
}

func NewDaily(clock clock.Clock, hour, minute int, tz *time.Location) Ticker {
	t := dailyTicker{
		c:     make(chan time.Time),
		stopC: make(chan chan struct{}),
	}
	initComplete := make(chan struct{})
	go t.run(clock, hour, minute, tz, initComplete)
	<-initComplete
	return &t
}

func (t *dailyTicker) C() <-chan time.Time {
	return t.c
}

// Stop stops the ticker.
func (t *dailyTicker) Stop() {
	reply := make(chan struct{})
	t.stopC <- reply
	<-reply
}

func (t *dailyTicker) run(clock clock.Clock, hour, minute int, tz *time.Location, initComplete chan struct{}) {
	now := clock.Now()
	lowerBound := now.Add(-7 * 24 * time.Hour)
	year := lowerBound.Year()
	month := lowerBound.Month()
	day := lowerBound.Day()
	var firstTickTime time.Time
	for {
		firstTickTime = time.Date(year, month, day, hour, minute, 0, 0, tz)
		if firstTickTime.After(now) {
			break
		}
		day++
	}
	period := firstTickTime.Sub(now)
	base := clock.Ticker(period)
	initComplete <- struct{}{}
	for {
		select {
		case tickTime := <-base.C:
			t.c <- tickTime
			day++
			period = clock.Until(time.Date(year, month, day, hour, minute, 0, 0, tz))
			base.Reset(period)
		case reply := <-t.stopC:
			base.Stop()
			reply <- struct{}{}
			return
		}
	}
}
