package endtoend

import (
	"fmt"
	"testing"

	gtfsrt "github.com/jamespfennell/gtfs/proto"
	"github.com/jamespfennell/transiter/tests/endtoend/fixtures"
	"github.com/jamespfennell/transiter/tests/endtoend/testutils"
	"github.com/jamespfennell/transiter/tests/endtoend/transiterclient"
)

const (
	Stop1  = "stop-1"
	Stop2  = "stop-2"
	Stop3  = "stop-3"
	Stop4  = "stop-4"
	Stop5  = "stop-5"
	Stop6  = "stop-6"
	Stop7  = "stop-7"
	RouteA = "A"
)

var ServiceMapsGTFSStaticTXTARZip = fixtures.GTFSStaticDefaultZipBuilder().AddOrReplaceFile(
	"stops.txt",
	"stop_id",
	Stop1,
	Stop2,
	Stop3,
	Stop4,
	Stop5,
	Stop6,
	Stop7,
).AddOrReplaceFile(
	"routes.txt",
	"route_id,route_type",
	fmt.Sprintf("%s,2", RouteA),
	"B,2",
).AddOrReplaceFile(
	"calendar.txt",
	"service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date",
	"Weekday,1,1,1,1,1,0,0,20180101,20181231",
	"Weekend,0,0,0,0,0,1,1,20180101,20181231",
).AddOrReplaceFile(
	"trips.txt",
	"route_id,service_id,trip_id,direction_id",
	fmt.Sprintf("%s,Weekday,A-S-A01-Weekday-1100,1", RouteA),
	fmt.Sprintf("%s,Weekday,A-N-A01-Weekend-1100,0", RouteA),
	fmt.Sprintf("%s,Weekday,A-S-A01-Weekday-1130,1", RouteA),
	fmt.Sprintf("%s,Weekday,A-N-A01-Weekend-1130,0", RouteA),
).AddOrReplaceFile(
	"stop_times.txt",
	"trip_id,arrival_time,departure_time,stop_id,stop_sequence",
	"A-S-A01-Weekday-1100,11:00:00,11:00:10,"+Stop1+",1",
	"A-S-A01-Weekday-1100,11:02:00,11:02:10,"+Stop4+",2",
	"A-S-A01-Weekday-1100,11:03:00,11:03:10,"+Stop5+",3",
	"A-S-A01-Weekday-1130,11:30:00,11:30:10,"+Stop1+",1",
	"A-S-A01-Weekday-1130,11:32:00,11:32:10,"+Stop4+",2",
	"A-S-A01-Weekday-1130,11:33:00,11:33:10,"+Stop5+",3",
	"A-S-A01-Weekday-1130,11:34:00,11:34:10,"+Stop7+",4",
).MustBuild()

func TestServiceMaps(t *testing.T) {
	for _, tc := range []struct {
		name string
		test func(t *testing.T, client *transiterclient.TransiterClient, systemID string, realtimeFeedURL string)
	}{
		{
			name: "static stop view",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string, realtimeFeedURL string) {
				stopToRoutes := map[string][]string{
					Stop1: {RouteA},
					Stop2: {},
					Stop3: {},
					Stop4: {RouteA},
					Stop5: {RouteA},
					Stop6: {},
					Stop7: {RouteA},
				}

				for stopID, wantRouteIDs := range stopToRoutes {
					stop, err := client.GetStop(systemID, stopID)
					if err != nil {
						t.Fatalf("failed to get stop %s: %v", stopID, err)
					}

					var gotRoutes []transiterclient.RouteReference
					for _, serviceMap := range stop.ServiceMaps {
						if serviceMap.ConfigID != "weekday" {
							continue
						}
						gotRoutes = serviceMap.Routes
						break
					}

					wantRoutes := make([]transiterclient.RouteReference, 0)
					for _, routeID := range wantRouteIDs {
						wantRoutes = append(wantRoutes, transiterclient.RouteReference{ID: routeID})
					}
					testutils.AssertEqual(t, gotRoutes, wantRoutes)
				}
			},
		},
		{
			name: "static route view",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string, realtimeFeedURL string) {
				routeToStops := map[string][]string{
					"A": {Stop1, Stop4, Stop5, Stop7},
					"B": {},
				}

				for routeID, wantStopIDs := range routeToStops {
					route, err := client.GetRoute(systemID, routeID)
					if err != nil {
						t.Fatalf("failed to get route %s: %v", routeID, err)
					}

					var gotStops []transiterclient.StopReference
					for _, serviceMap := range route.ServiceMaps {
						if serviceMap.ConfigID != "alltimes" {
							continue
						}
						gotStops = serviceMap.Stops
						break
					}

					wantStops := make([]transiterclient.StopReference, 0)
					for _, stopID := range wantStopIDs {
						wantStops = append(wantStops, transiterclient.StopReference{ID: stopID})
					}
					testutils.AssertEqual(t, gotStops, wantStops)
				}
			},
		},
		{
			name: "realtime",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string, realtimeFeedURL string) {

				// (1) Regular case
				trip1Stops := []stopTime{
					{stopID: Stop1, time: 300},
					{stopID: Stop5, time: 1800},
					{stopID: Stop6, time: 2500},
				}
				trip2Stops := []stopTime{
					{stopID: Stop1, time: 300},
					{stopID: Stop2, time: 600},
					{stopID: Stop3, time: 800},
					{stopID: Stop4, time: 900},
					{stopID: Stop5, time: 1800},
				}
				feedTrips := []feedTrip{
					{tripID: "trip_1", routeID: RouteA, stopTimes: trip1Stops},
					{tripID: "trip_2", routeID: RouteA, stopTimes: trip2Stops},
				}
				checkRealtimeServiceMaps(t, systemID, client, realtimeFeedURL, feedTrips,
					[]string{Stop1, Stop2, Stop3, Stop4, Stop5, Stop6})

				// (2) Old trips + new trips give an invalid map, but the update still happens
				// because old trips shouldn't count
				trip3Stops := []stopTime{
					{stopID: Stop6, time: 250},
					{stopID: Stop5, time: 1800},
					{stopID: Stop1, time: 3000},
				}
				trip4Stops := []stopTime{
					{stopID: Stop5, time: 100},
					{stopID: Stop4, time: 900},
					{stopID: Stop3, time: 8000},
					{stopID: Stop2, time: 60000},
					{stopID: Stop1, time: 300000},
				}
				feedTrips = []feedTrip{
					{tripID: "trip_3", routeID: RouteA, stopTimes: trip3Stops},
					{tripID: "trip_4", routeID: RouteA, stopTimes: trip4Stops},
				}
				wantStops := []string{Stop6, Stop5, Stop4, Stop3, Stop2, Stop1}
				checkRealtimeServiceMaps(t, systemID, client, realtimeFeedURL, feedTrips, wantStops)

				// (3) With this update the map is now invalid so should not be updated, but the
				// trips are still updated successfully
				trip5Stops := []stopTime{
					{stopID: Stop1, time: 250},
					{stopID: Stop5, time: 1800},
					{stopID: Stop6, time: 3000},
				}
				feedTrips = []feedTrip{
					{tripID: "trip_3", routeID: RouteA, stopTimes: trip3Stops},
					{tripID: "trip_4", routeID: RouteA, stopTimes: trip4Stops},
					{tripID: "trip_5", routeID: RouteA, stopTimes: trip5Stops},
				}
				checkRealtimeServiceMaps(t, systemID, client, realtimeFeedURL, feedTrips, wantStops)

				// (4) Valid map again
				trip1Stops = []stopTime{
					{stopID: Stop1, time: 300},
					{stopID: Stop5, time: 1800},
					{stopID: Stop6, time: 2500},
				}
				feedTrips = []feedTrip{
					{tripID: "trip_1", routeID: RouteA, stopTimes: trip1Stops},
				}
				checkRealtimeServiceMaps(t, systemID, client, realtimeFeedURL, feedTrips,
					[]string{Stop1, Stop5, Stop6})

				// (5) No more trips, service map is deleted
				feedTrips = []feedTrip{}
				checkRealtimeServiceMaps(t, systemID, client, realtimeFeedURL, feedTrips, []string{})
			},
		},
	} {
		testName := fmt.Sprintf("%s/%s", "servicemaps", tc.name)
		t.Run(testName, func(t *testing.T) {
			systemID, _, realtimeFeedURL := fixtures.InstallSystem(t, ServiceMapsGTFSStaticTXTARZip)
			transiterClient := fixtures.GetTransiterClient(t)
			tc.test(t, transiterClient, systemID, realtimeFeedURL)
		})
	}
}

type stopTime struct {
	stopID string
	time   int64
}

type feedTrip struct {
	tripID    string
	routeID   string
	stopTimes []stopTime
}

func checkRealtimeServiceMaps(
	t *testing.T,
	systemID string,
	client *transiterclient.TransiterClient,
	realtimeFeedURL string,
	feedTrips []feedTrip,
	wantStopIDs []string,
) {
	fixtures.PublishGTFSRTMessageAndUpdate(t, systemID, realtimeFeedURL, buildGTFSRealtimeFeed(feedTrips))

	// (1) validate the service map appears in the route endpoints
	route, err := client.GetRoute(systemID, RouteA)
	if err != nil {
		t.Fatalf("failed to get route: %v", err)
	}

	wantStops := make([]transiterclient.StopReference, 0)
	for _, stopID := range wantStopIDs {
		wantStops = append(wantStops, transiterclient.StopReference{ID: stopID})
	}

	var gotStops []transiterclient.StopReference
	for _, serviceMap := range route.ServiceMaps {
		if serviceMap.ConfigID != "realtime" {
			continue
		}
		gotStops = serviceMap.Stops
		break
	}
	testutils.AssertEqual(t, gotStops, wantStops)

	// (2) validate the service map appears in the stop endpoints
	wantStopIDsSet := make(map[string]bool)
	for _, stopID := range wantStopIDs {
		wantStopIDsSet[stopID] = true
	}

	stops, err := client.ListStops(systemID)
	if err != nil {
		t.Fatalf("failed to list stops: %v", err)
	}

	for _, stop := range stops.Stops {
		var wantRoutes []transiterclient.RouteReference
		if wantStopIDsSet[stop.ID] {
			wantRoutes = []transiterclient.RouteReference{{ID: RouteA}}
		} else {
			wantRoutes = []transiterclient.RouteReference{}
		}

		var gotRoutes []transiterclient.RouteReference
		for _, serviceMap := range stop.ServiceMaps {
			if serviceMap.ConfigID != "realtime" {
				continue
			}
			gotRoutes = serviceMap.Routes
			break
		}

		wantServiceMap := transiterclient.ServiceMapAtStop{
			ConfigID: "realtime",
			Routes:   wantRoutes,
		}
		gotServiceMap := transiterclient.ServiceMapAtStop{
			ConfigID: "realtime",
			Routes:   gotRoutes,
		}
		testutils.AssertEqual(t, gotServiceMap, wantServiceMap)
	}
}

func buildGTFSRealtimeFeed(trips []feedTrip) *gtfsrt.FeedMessage {
	entities := []*gtfsrt.FeedEntity{}
	for i, trip := range trips {
		stopTimeUpdates := []*gtfsrt.TripUpdate_StopTimeUpdate{}
		for _, stopTime := range trip.stopTimes {
			stopTimeUpdates = append(stopTimeUpdates, &gtfsrt.TripUpdate_StopTimeUpdate{
				StopId: testutils.Ptr(stopTime.stopID),
				Arrival: &gtfsrt.TripUpdate_StopTimeEvent{
					Time: testutils.Ptr(stopTime.time),
				},
				Departure: &gtfsrt.TripUpdate_StopTimeEvent{
					Time: testutils.Ptr(stopTime.time + 15),
				},
			})
		}

		entities = append(entities, &gtfsrt.FeedEntity{
			Id: testutils.Ptr(fmt.Sprintf("%d", i)),
			TripUpdate: &gtfsrt.TripUpdate{
				Trip: &gtfsrt.TripDescriptor{
					TripId:      testutils.Ptr(trip.tripID),
					RouteId:     testutils.Ptr(trip.routeID),
					DirectionId: testutils.Ptr(uint32(1)),
				},
				StopTimeUpdate: stopTimeUpdates,
			},
		})
	}

	message := gtfsrt.FeedMessage{
		Header: &gtfsrt.FeedHeader{
			GtfsRealtimeVersion: testutils.Ptr("2.0"),
			Timestamp:           testutils.Ptr(uint64(0)),
		},
		Entity: entities,
	}
	return &message
}
