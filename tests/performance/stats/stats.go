package stats

import (
	"fmt"
	"sort"
	"sync"
	"time"
)

var StopStats Stats
var RouteStats Stats
var TripStats Stats

func init() {
	StopStats = Stats{
		data: map[string][]time.Duration{},
	}
	RouteStats = Stats{
		data: map[string][]time.Duration{},
	}
	TripStats = Stats{
		data: map[string][]time.Duration{},
	}
}

type Stats struct {
	m     sync.Mutex
	data  map[string][]time.Duration
	nErrs int
}

func (stats *Stats) Add(id string, d time.Duration) {
	stats.m.Lock()
	defer stats.m.Unlock()
	stats.data[id] = append(stats.data[id], d)
}

func (stats *Stats) AddErr() {
	stats.m.Lock()
	defer stats.m.Unlock()
	stats.nErrs++
}

func (stats *Stats) Print() {
	var totalDuration time.Duration
	var nPoints int
	var results []result
	for id, ds := range stats.data {
		for _, d := range ds {
			totalDuration += d
		}
		nPoints += len(ds)
		results = append(results, result{
			id:          id,
			avgDuration: totalDuration / time.Duration(nPoints),
		})
	}
	sortResults(results)
	fmt.Println("Slowest IDs")
	for _, result := range results[len(results)-5:] {
		fmt.Println(result.id, result.avgDuration)
	}
	fmt.Println("Average duration:", totalDuration/time.Duration(nPoints))
}

type result struct {
	id          string
	avgDuration time.Duration
	// TODO: min and max
}

type resultsList struct {
	l []result
	f func(result) time.Duration
}

func (l resultsList) Len() int {
	return len(l.l)
}

func (l resultsList) Less(i, j int) bool {
	return l.f(l.l[i]) < l.f(l.l[j])
}

func (l resultsList) Swap(i, j int) {
	l.l[i], l.l[j] = l.l[j], l.l[i]
}

func sortResults(results []result) {
	sort.Sort(resultsList{
		l: results,
		f: func(r result) time.Duration { return r.avgDuration },
	})
}
