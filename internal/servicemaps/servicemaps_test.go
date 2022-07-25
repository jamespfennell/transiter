package servicemaps

import (
	"reflect"
	"testing"
	"time"

	"github.com/jamespfennell/gtfs"
	"github.com/jamespfennell/transiter/config"
)

const (
	serviceID1 = "serviceID1"
	serviceID2 = "serviceID2"
	serviceID3 = "serviceID3"
)

func TestBuildStaticMaps(t *testing.T) {
	directionIDTrue := true
	directionIDFalse := false
	service1 := &gtfs.Service{
		Id: serviceID1,
	}
	stopTimes := func(stopIDs ...string) []gtfs.ScheduledStopTime {
		var stopTimes []gtfs.ScheduledStopTime
		for _, t := range stopIDs {
			stopTimes = append(stopTimes, gtfs.ScheduledStopTime{
				Stop: &gtfs.Stop{Id: t},
			})
		}
		return stopTimes
	}
	for _, tc := range []struct {
		name      string
		threshold float64
		trips     []gtfs.ScheduledTrip
		want      []int64
	}{
		{
			name:  "empty",
			trips: []gtfs.ScheduledTrip{},
			want:  []int64{},
		},
		{
			name: "base case",
			trips: []gtfs.ScheduledTrip{
				{
					StopTimes:   stopTimes("1", "2", "3"),
					DirectionId: &directionIDTrue,
				},
			},
			want: []int64{1, 2, 3},
		},
		{
			name: "reversed",
			trips: []gtfs.ScheduledTrip{
				{
					StopTimes:   stopTimes("3", "2", "1"),
					DirectionId: &directionIDFalse,
				},
			},
			want: []int64{1, 2, 3},
		},
		{
			name: "regular and reversed",
			trips: []gtfs.ScheduledTrip{
				{
					StopTimes:   stopTimes("1", "2", "3"),
					DirectionId: &directionIDTrue,
				},
				{
					StopTimes:   stopTimes("3", "2", "1"),
					DirectionId: &directionIDFalse,
				},
			},
			want: []int64{1, 2, 3},
		},
		{
			name: "no threshold",
			trips: []gtfs.ScheduledTrip{
				{
					StopTimes:   stopTimes("1", "2", "3"),
					DirectionId: &directionIDTrue,
				},
				{
					StopTimes:   stopTimes("3", "2", "1"),
					DirectionId: &directionIDFalse,
				},
				{
					StopTimes:   stopTimes("1", "2", "3", "4"),
					DirectionId: &directionIDTrue,
				},
			},
			want: []int64{1, 2, 3, 4},
		},
		{
			name:      "has threshold",
			threshold: 0.4,
			trips: []gtfs.ScheduledTrip{
				{
					StopTimes:   stopTimes("1", "2", "3"),
					DirectionId: &directionIDTrue,
				},
				{
					StopTimes:   stopTimes("3", "2", "1"),
					DirectionId: &directionIDFalse,
				},
				{
					StopTimes:   stopTimes("1", "2", "3", "4"),
					DirectionId: &directionIDTrue,
				},
			},
			want: []int64{1, 2, 3},
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			for i := range tc.trips {
				tc.trips[i].Service = service1
				tc.trips[i].Route = &gtfs.Route{Id: "1"}
			}
			config := &config.ServiceMapConfig{
				Threshold: tc.threshold,
			}
			routeIDToPk := map[string]int64{"1": 1}
			stopIDToPk := map[string]int64{"1": 1, "2": 2, "3": 3, "4": 4}
			gotAll := buildStaticMaps(config, routeIDToPk, stopIDToPk, tc.trips)

			got, ok := gotAll[1]
			if !ok {
				t.Fatalf("buildStaticMaps() = empty map, wanted non-empty map")
			}

			if !reflect.DeepEqual(got, tc.want) {
				t.Errorf("buildStaticMaps()[routePk=1] = %+v, want %+v", got, tc.want)
			}
		})
	}
}

func TestIsIncludedTrip(t *testing.T) {
	directionIDTrue := true
	service1 := &gtfs.Service{
		Id: serviceID1,
	}
	ptr := func(i int) *time.Duration {
		d := time.Duration(i) * time.Hour
		return &d
	}
	stopTimes := func(times ...int) []gtfs.ScheduledStopTime {
		var stopTimes []gtfs.ScheduledStopTime
		for _, t := range times {
			stopTimes = append(stopTimes, gtfs.ScheduledStopTime{
				ArrivalTime: time.Duration(t) * time.Hour,
			})
		}
		return stopTimes
	}
	for _, tc := range []struct {
		name   string
		config *config.ServiceMapConfig
		trip   *gtfs.ScheduledTrip
		want   bool
	}{
		{
			name:   "no config conditions",
			config: &config.ServiceMapConfig{},
			trip: &gtfs.ScheduledTrip{
				Service:     service1,
				DirectionId: &directionIDTrue,
				StopTimes:   stopTimes(10, 12),
			},
			want: true,
		},
		{
			name:   "missing direction ID",
			config: &config.ServiceMapConfig{},
			trip: &gtfs.ScheduledTrip{
				Service:     service1,
				DirectionId: nil,
				StopTimes:   stopTimes(10, 12),
			},
			want: false,
		},
		{
			name:   "no stop times",
			config: &config.ServiceMapConfig{},
			trip: &gtfs.ScheduledTrip{
				Service:     service1,
				DirectionId: &directionIDTrue,
				StopTimes:   nil,
			},
			want: false,
		},
		{
			name:   "service not included",
			config: &config.ServiceMapConfig{},
			trip: &gtfs.ScheduledTrip{
				Service: &gtfs.Service{Id: serviceID2},

				DirectionId: &directionIDTrue,
				StopTimes:   stopTimes(10, 12),
			},
			want: false,
		},
		{
			name: "trip start not early enough",
			config: &config.ServiceMapConfig{
				StartsEarlierThan: ptr(9),
			},
			trip: &gtfs.ScheduledTrip{
				Service:     service1,
				DirectionId: &directionIDTrue,
				StopTimes:   stopTimes(10, 12),
			},
			want: false,
		},
		{
			name: "trip start not late enough",
			config: &config.ServiceMapConfig{
				StartsLaterThan: ptr(11),
			},
			trip: &gtfs.ScheduledTrip{
				Service:     service1,
				DirectionId: &directionIDTrue,
				StopTimes:   stopTimes(10, 12),
			},
			want: false,
		},
		{
			name: "trip end not early enough",
			config: &config.ServiceMapConfig{
				EndsEarlierThan: ptr(11),
			},
			trip: &gtfs.ScheduledTrip{
				Service:     service1,
				DirectionId: &directionIDTrue,
				StopTimes:   stopTimes(10, 12),
			},
			want: false,
		},
		{
			name: "trip end not late enough",
			config: &config.ServiceMapConfig{
				EndsLaterThan: ptr(13),
			},
			trip: &gtfs.ScheduledTrip{
				Service:     service1,
				DirectionId: &directionIDTrue,
				StopTimes:   stopTimes(10, 12),
			},
			want: false,
		},
		{
			name: "trip passes all conditions",
			config: &config.ServiceMapConfig{
				StartsEarlierThan: ptr(11),
				StartsLaterThan:   ptr(9),
				EndsEarlierThan:   ptr(13),
				EndsLaterThan:     ptr(11),
			},
			trip: &gtfs.ScheduledTrip{
				Service:     service1,
				DirectionId: &directionIDTrue,
				StopTimes:   stopTimes(10, 12),
			},
			want: true,
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			includedServiceIDs := map[string]bool{serviceID1: true}
			got := isIncludedTrip(tc.config, tc.trip, includedServiceIDs)

			if got != tc.want {
				t.Errorf("isIncludedTrip() got = %v, want = %v", got, tc.want)
			}
		})
	}
}

func TestBuildIncludedServiceMapsIDs(t *testing.T) {
	service1 := &gtfs.Service{
		Id:      serviceID1,
		Monday:  true,
		Tuesday: true,
	}
	service2 := &gtfs.Service{
		Id:     serviceID2,
		Monday: true,
		Sunday: true,
	}
	service3 := &gtfs.Service{
		Id:        serviceID3,
		Tuesday:   true,
		Wednesday: true,
	}
	trips := []gtfs.ScheduledTrip{
		{Service: service1},
		{Service: service1},
		{Service: service2},
		{Service: service3},
	}

	for _, tc := range []struct {
		name string
		days []string
		want map[string]bool
	}{
		{
			name: "two days specified",
			days: []string{"tuesday", "wedesday"},
			want: map[string]bool{
				serviceID1: true,
				serviceID3: true,
			},
		},
		{
			name: "no days specified",
			days: []string{},
			want: map[string]bool{
				serviceID1: true,
				serviceID2: true,
				serviceID3: true,
			},
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			config := &config.ServiceMapConfig{
				Days: tc.days,
			}
			got := buildIncludedServiceIDs(config, trips)

			if !reflect.DeepEqual(got, tc.want) {
				t.Errorf("buildIncludedServiceIDs() got = %+v, want = %+v", got, tc.want)
			}
		})
	}

}
