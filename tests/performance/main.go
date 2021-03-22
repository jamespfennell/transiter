package main

import (
	"context"
	"flag"
	"fmt"
	"github.com/jamespfennell/transiter/tests/performance/client"
	"github.com/jamespfennell/transiter/tests/performance/stats"
	"math/rand"
	"sync"
	"time"
)

var maxWorkers = flag.Int("max-clients", 5, "Maximum number of concurrent clients")
var minSpawnDelay = flag.Duration("spawn-delay-min", 50*time.Millisecond, "Minimum time to wait between spawning clients")
var maxSpawnDelay = flag.Duration("spawn-delay-max", 50*time.Millisecond, "Maximum time to wait between spawning clients")
var minActionPause = flag.Duration("action-pause-min", 500*time.Millisecond, "Minimum time to wait between client actions")
var maxActionPause = flag.Duration("action-pause-max", 1000*time.Millisecond, "Maximum time to wait between client actions")
var timeout = flag.Duration("timeout", 10*time.Second, "Length of time to run the benchmark for")
var baseUrl = flag.String("base-url", "https://demo.transiter.dev", "The base URL of the Transiter server to test")

func main() {
	flag.Parse()
	runWorkers()
	fmt.Println("-----STOPS-----")
	stats.StopStats.Print()
	fmt.Println("-----ROUTES-----")
	stats.RouteStats.Print()
	fmt.Println("-----TRIPS-----")
	stats.TripStats.Print()
}

func randDuration(lower, upper time.Duration) time.Duration {
	return lower + time.Duration(float64(upper-lower)*rand.Float64())
}

func runWorkers() {
	semaphore := NewSemaphore(*maxWorkers)
	ctx, cancelFunc := context.WithDeadline(context.Background(), time.Now().Add(*timeout))
	defer cancelFunc()
	t := time.NewTicker(time.Second)
	defer t.Stop()
	rand.Seed(303)
	for {
		select {
		case <-semaphore.Acquire():
			time.Sleep(randDuration(*minSpawnDelay, *maxSpawnDelay))
			go func() {
				var state client.State
				var err error
				state = client.NewStartState(*baseUrl)
				for {
					state, err = state.Transition()
					if err != nil {
						fmt.Println("Error:", err)
					}
					if _, ok := state.(client.EndState); ok {
						break
					}
					time.Sleep(randDuration(*minActionPause, *maxActionPause))
				}
				semaphore.Release()
			}()
		case <-t.C:
			fmt.Printf("Num clients: %d\n", semaphore.NumInUse())
		case <-ctx.Done():
			return
		}
	}
}

func NewSemaphore(size int) *Semaphore {
	s := Semaphore{
		c1:    make(chan struct{}),
		c2:    make(chan struct{}, size-1),
		nUsed: 0,
	}
	for i := 0; i < size-1; i++ {
		s.c2 <- struct{}{}
	}
	go func() {
		for {
			s.c1 <- struct{}{}
			s.m.Lock()
			s.nUsed++
			s.m.Unlock()
			<-s.c2
		}
	}()
	return &s
}

type Semaphore struct {
	c1    chan struct{}
	c2    chan struct{}
	m     sync.Mutex
	nUsed int
}

func (s *Semaphore) Acquire() <-chan struct{} {
	return s.c1
}

func (s *Semaphore) Release() {
	s.m.Lock()
	s.nUsed--
	s.m.Unlock()
	s.c2 <- struct{}{}
}

func (s *Semaphore) NumInUse() int {
	s.m.Lock()
	defer s.m.Unlock()
	return s.nUsed
}
