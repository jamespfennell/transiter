// Package ticker implements a ticker for the scheduler.
//
// This ticker ticks at a given period like the standard library's ticker, has an additional features:
//
// (1) Before sending the first tick it waits a random duration (at most the period). This means that
//
//	ticks are smoothed out across different tickers started at the same time.
//
// (2) It has support for pausing the ticks.
package ticker

import (
	"math/rand"
	"time"

	"github.com/benbjohnson/clock"
)

type Ticker struct {
	C <-chan time.Time

	tickC  chan time.Time
	resetC chan time.Duration
	pauseC chan time.Duration
	stopC  chan struct{}

	// Channel for notifying that an operation is complete. Operation here can be
	// create ticker, reset, pause and stop. This is added to make unit tests deterministic.
	opDoneC chan struct{}
}

// New creates a new ticker based on the provided clock and with the provided initial period.
func New(clock clock.Clock, period time.Duration) *Ticker {
	tickC := make(chan time.Time)
	t := Ticker{
		C:       tickC,
		tickC:   tickC,
		resetC:  make(chan time.Duration),
		pauseC:  make(chan time.Duration),
		stopC:   make(chan struct{}),
		opDoneC: make(chan struct{}),
	}
	go t.run(clock, period)
	<-t.opDoneC
	return &t
}

// Reset changes the period of the ticker.
func (t *Ticker) Reset(period time.Duration) {
	t.resetC <- period
	<-t.opDoneC
}

// Pause pauses the ticker for the provided duration.
func (t *Ticker) Pause(duration time.Duration) {
	t.pauseC <- duration
	<-t.opDoneC
}

// Stop stops the ticker.
func (t *Ticker) Stop() {
	t.stopC <- struct{}{}
}

func (t *Ticker) run(clock clock.Clock, period time.Duration) {
	rand := rand.New(rand.NewSource(clock.Now().UnixNano()))
	tickerPeriod := time.Duration(float64(period) * rand.Float64())
	c := clock.Ticker(tickerPeriod)
	t.opDoneC <- struct{}{}
	reset := func() {
		c.Reset(tickerPeriod)
	}
	for {
		select {
		case tickTime := <-c.C:
			t.tickC <- tickTime
			if tickerPeriod != period {
				tickerPeriod = period
				reset()
			}
		case period = <-t.resetC:
			tickerPeriod = time.Duration(float64(period) * rand.Float64())
			reset()
			t.opDoneC <- struct{}{}
		case tickerPeriod = <-t.pauseC:
			reset()
			t.opDoneC <- struct{}{}
		case <-t.stopC:
			c.Stop()
			return
		}
	}
}
