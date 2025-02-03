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
	ChildStopID         = "StopID"
	ParentStopID        = "ParentStopID"
	StopSearchLatitude  = 40.7559
	StopSearchLongitude = -73.9871
)

var ChildStop = transiterclient.Stop{
	ID:                 "StopID",
	Code:               "StopCode",
	Name:               "StopName",
	Description:        "StopDesc",
	ZoneID:             "ZoneId",
	Latitude:           40.7527,
	Longitude:          -73.9772,
	URL:                "StopUrl",
	Type:               "PLATFORM",
	Timezone:           "StopTimezone",
	WheelchairBoarding: true,
	PlatformCode:       "PlatformCode",
	ParentStop:         &transiterclient.StopReference{ID: ParentStopID},
	ChildStops:         []transiterclient.StopReference{},
	Transfers:          []transiterclient.Transfer{},
	ServiceMaps:        []transiterclient.ServiceMapAtStop{},
	Alerts:             []transiterclient.AlertReference{},
	StopTimes:          []transiterclient.StopTime{},
}

var ParentStop = transiterclient.Stop{
	ID:          ParentStopID,
	Latitude:    30,
	Longitude:   50,
	Type:        "STATION",
	ChildStops:  []transiterclient.StopReference{{ID: ChildStopID}},
	Transfers:   []transiterclient.Transfer{},
	ServiceMaps: []transiterclient.ServiceMapAtStop{},
	Alerts:      []transiterclient.AlertReference{},
	StopTimes:   []transiterclient.StopTime{},
}

var StopsGTFSStaticZip = fixtures.GTFSStaticDefaultZipBuilder().AddOrReplaceFile(
	"stops.txt",
	"stop_id,stop_name,stop_lat,stop_lon,location_type,parent_station,stop_code,stop_desc,zone_id,stop_url,stop_timezone,wheelchair_boarding,level_id,platform_code",
	fmt.Sprintf("%s,StopName,40.7527,-73.9772,0,%s,StopCode,StopDesc,ZoneId,StopUrl,StopTimezone,1,LevelId,PlatformCode", ChildStopID, ParentStopID),
	fmt.Sprintf("%s,,30,50,1,,,,,,,,,", ParentStopID),
).MustBuild()

func TestStops(t *testing.T) {
	for _, tc := range []struct {
		name                     string
		test                     func(t *testing.T, client *transiterclient.TransiterClient, systemID *string)
		skipDefaultSystemInstall bool
	}{
		{
			name: "list and get stops",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID *string) {
				gotSystem, err := client.GetSystem(*systemID)
				if err != nil {
					t.Fatalf("failed to get system: %v", err)
				}
				testutils.AssertEqual(t, gotSystem.Stops, &transiterclient.ChildResources{
					Count: 2,
					Path:  fmt.Sprintf("systems/%s/stops", *systemID),
				})

				params := []transiterclient.QueryParam{
					{Key: "skip_service_maps", Value: "true"},
				}

				gotAllStops, err := client.ListStops(*systemID, params...)
				if err != nil {
					t.Fatalf("failed to list stops: %v", err)
				}
				testutils.AssertEqual(t, gotAllStops.Stops, []transiterclient.Stop{ParentStop, ChildStop})

				for _, wantStop := range []transiterclient.Stop{ParentStop, ChildStop} {
					gotStop, err := client.GetStop(*systemID, wantStop.ID, params...)
					if err != nil {
						t.Fatalf("failed to get stop %s: %v", wantStop.ID, err)
					}
					testutils.AssertEqual(t, gotStop, &wantStop)
				}
			},
		},
		{
			name:                     "pagination",
			skipDefaultSystemInstall: true,
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID *string) {
				var stopIDs []string
				for i := 0; i < 150; i++ {
					stopIDs = append(stopIDs, fmt.Sprintf("stop_%03d", i))
				}
				stopHeaderAndIDs := []string{"stop_id"}
				stopHeaderAndIDs = append(stopHeaderAndIDs, stopIDs...)
				paginationTXTAR := fixtures.GTFSStaticDefaultZipBuilder().AddOrReplaceFile(
					"stops.txt",
					stopHeaderAndIDs...,
				).MustBuild()

				paginationSystemID, _, _ := fixtures.InstallSystem(t, paginationTXTAR)

				gotAllStops, err := client.ListStops(paginationSystemID)
				if err != nil {
					t.Fatalf("failed to list stops: %v", err)
				}

				var gotStopIDs []string
				for _, stop := range gotAllStops.Stops {
					gotStopIDs = append(gotStopIDs, stop.ID)
				}

				var wantStopIDs []string
				for i := 0; i < 100; i++ {
					wantStopIDs = append(wantStopIDs, fmt.Sprintf("stop_%03d", i))
				}
				testutils.AssertEqual(t, gotStopIDs, wantStopIDs)
				testutils.AssertEqual(t, gotAllStops.NextID, testutils.Ptr("stop_100"))

				gotAllStops, err = client.ListStops(paginationSystemID, transiterclient.QueryParam{
					Key:   "first_id",
					Value: *gotAllStops.NextID,
				})
				if err != nil {
					t.Fatalf("failed to list stops (second page): %v", err)
				}

				gotStopIDs = nil
				for _, stop := range gotAllStops.Stops {
					gotStopIDs = append(gotStopIDs, stop.ID)
				}

				wantStopIDs = nil
				for i := 100; i < 150; i++ {
					wantStopIDs = append(wantStopIDs, fmt.Sprintf("stop_%03d", i))
				}
				testutils.AssertEqual(t, gotStopIDs, wantStopIDs)
				testutils.AssertEqual(t, gotAllStops.NextID, (*string)(nil))
			},
		},
		{
			name: "geographic search",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID *string) {
				type testCase struct {
					searchDistance float64
					wantStops      []transiterclient.Stop
				}

				for _, tc := range []testCase{
					{
						searchDistance: 0,
						wantStops:      []transiterclient.Stop{},
					},
					{
						searchDistance: 1,
						wantStops:      []transiterclient.Stop{ChildStop},
					},
					{
						searchDistance: 40075,
						wantStops:      []transiterclient.Stop{ChildStop, ParentStop},
					},
				} {
					params := []transiterclient.QueryParam{
						{Key: "search_mode", Value: "DISTANCE"},
						{Key: "latitude", Value: fmt.Sprintf("%f", StopSearchLatitude)},
						{Key: "longitude", Value: fmt.Sprintf("%f", StopSearchLongitude)},
						{Key: "max_distance", Value: fmt.Sprintf("%f", tc.searchDistance)},
						{Key: "skip_service_maps", Value: "true"},
					}

					gotGeoStops, err := client.ListStops(*systemID, params...)
					if err != nil {
						t.Fatalf("failed to list stops with geographic search: %v", err)
					}
					testutils.AssertEqual(t, gotGeoStops.Stops, tc.wantStops)
				}
			},
		},
		{
			name:                     "trip headsigns",
			skipDefaultSystemInstall: true,
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID *string) {
				stop1ID := "stop_1_id"
				stop2ID := "stop_2_id"
				route1ID := "route_id_1"
				route2ID := "route_id_2"
				trip1ID := "trip_1_id"
				trip2ID := "trip_2_id"

				gtfsStatic := fixtures.GTFSStaticDefaultZipBuilder().
					AddOrReplaceFile(
						"stops.txt",
						"stop_id,stop_name,stop_lat,stop_lon,location_type,parent_station,stop_code,stop_desc,zone_id,stop_url,stop_timezone,wheelchair_boarding,level_id,platform_code",
						fmt.Sprintf("%s,,30,50,1,,,,,,,,,", stop1ID),
						fmt.Sprintf("%s,,80,90,1,,,,,,,,,", stop2ID),
					).
					AddOrReplaceFile(
						"calendar.txt",
						"service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date",
						"Weekday,1,1,1,1,1,0,0,20240101,20240101",
					).
					AddOrReplaceFile(
						"trips.txt",
						"route_id,service_id,trip_id,direction_id,trip_headsign",
						fmt.Sprintf("%s,Weekday,%s,1,headsign_1", route1ID, trip1ID),
						fmt.Sprintf("%s,Weekday,%s,1,headsign_2", route2ID, trip2ID),
					).
					AddOrReplaceFile(
						"stop_times.txt",
						"trip_id,arrival_time,departure_time,stop_id,direction_id,stop_sequence,stop_headsign",
						fmt.Sprintf("%s,11:00:00,11:00:10,%s,1,0,", trip1ID, stop1ID),
						fmt.Sprintf("%s,11:02:00,11:02:10,%s,1,1,", trip1ID, stop2ID),
						fmt.Sprintf("%s,11:00:00,11:00:10,%s,1,0,headsign_3", trip2ID, stop1ID),
						fmt.Sprintf("%s,11:02:00,11:02:10,%s,1,1,headsign_4", trip2ID, stop2ID),
					).
					AddOrReplaceFile(
						"routes.txt",
						"route_id,route_type",
						fmt.Sprintf("%s,2", route1ID),
						fmt.Sprintf("%s,2", route2ID),
					).MustBuild()

				installedSystemID, _, realtimeFeedURL := fixtures.InstallSystem(t, gtfsStatic)

				trip1Timetable := []stopTime{
					{stopID: stop1ID, time: 300},
					{stopID: stop2ID, time: 600},
				}
				trip2Timetable := []stopTime{
					{stopID: stop1ID, time: 700},
					{stopID: stop2ID, time: 800},
				}

				updateMsg := buildGtfsRtTripUpdateMessage(trip1ID, route1ID, trip1Timetable)
				trip2Entity := buildGtfsRtTripUpdateMessage(trip2ID, route2ID, trip2Timetable).Entity
				updateMsg.Entity = append(updateMsg.Entity, trip2Entity...)

				fixtures.PublishGTFSRTMessageAndUpdate(t, installedSystemID, realtimeFeedURL, updateMsg)

				// Validate headsigns at stop1
				stop1, err := client.GetStop(installedSystemID, stop1ID)
				if err != nil {
					t.Fatalf("failed to get stop1: %v", err)
				}

				var trip1Stop1Times, trip2Stop1Times []transiterclient.StopTime
				for _, st := range stop1.StopTimes {
					if st.Trip.ID == trip1ID {
						trip1Stop1Times = append(trip1Stop1Times, st)
					}
					if st.Trip.ID == trip2ID {
						trip2Stop1Times = append(trip2Stop1Times, st)
					}
				}

				verifyHeadsign := func(stopTimes []transiterclient.StopTime, idx int, wantHeadsign string) {
					if len(stopTimes) <= idx {
						t.Errorf("expected %d stop times, got %d", idx+1, len(stopTimes))
					} else if stopTimes[idx].Headsign == nil {
						t.Errorf("expected headsign for stop time %d, got nil", idx)
					} else if *stopTimes[idx].Headsign != wantHeadsign {
						t.Errorf("expected headsign %s for stop time %d, got %s", wantHeadsign, idx, *stopTimes[idx].Headsign)
					}
				}

				verifyHeadsign(trip1Stop1Times, 0, "headsign_1")
				verifyHeadsign(trip2Stop1Times, 0, "headsign_3")

				// Validate headsigns at stop2
				stop2, err := client.GetStop(installedSystemID, stop2ID)
				if err != nil {
					t.Fatalf("failed to get stop2: %v", err)
				}

				var trip1Stop2Times, trip2Stop2Times []transiterclient.StopTime
				for _, st := range stop2.StopTimes {
					if st.Trip.ID == trip1ID {
						trip1Stop2Times = append(trip1Stop2Times, st)
					}
					if st.Trip.ID == trip2ID {
						trip2Stop2Times = append(trip2Stop2Times, st)
					}
				}

				verifyHeadsign(trip1Stop2Times, 0, "headsign_1")
				verifyHeadsign(trip2Stop2Times, 0, "headsign_4")
			},
		},
	} {
		testName := fmt.Sprintf("%s/%s", "stops", tc.name)
		t.Run(testName, func(t *testing.T) {
			var systemID *string
			if !tc.skipDefaultSystemInstall {
				installedSystemID, _, _ := fixtures.InstallSystem(t, StopsGTFSStaticZip)
				systemID = &installedSystemID
			}
			transiterClient := fixtures.GetTransiterClient(t)
			tc.test(t, transiterClient, systemID)
		})
	}
}

func buildGtfsRtTripUpdateMessage(tripID, routeID string, timetable []stopTime) *gtfsrt.FeedMessage {
	msg := &gtfsrt.FeedMessage{
		Header: &gtfsrt.FeedHeader{
			GtfsRealtimeVersion: testutils.Ptr("2.0"),
		},
	}
	StopTimeUpdates := []*gtfsrt.TripUpdate_StopTimeUpdate{}
	for seq, stopTime := range timetable {
		stopTimeUpdate := &gtfsrt.TripUpdate_StopTimeUpdate{
			StopId:       testutils.Ptr(stopTime.stopID),
			StopSequence: testutils.Ptr(uint32(seq)),
			Arrival: &gtfsrt.TripUpdate_StopTimeEvent{
				Time: testutils.Ptr(int64(stopTime.time)),
			},
			Departure: &gtfsrt.TripUpdate_StopTimeEvent{
				Time: testutils.Ptr(int64(stopTime.time + 10)),
			},
		}
		StopTimeUpdates = append(StopTimeUpdates, stopTimeUpdate)
	}
	msg.Entity = append(msg.Entity, &gtfsrt.FeedEntity{
		Id: testutils.Ptr("message_id"),
		TripUpdate: &gtfsrt.TripUpdate{
			Trip: &gtfsrt.TripDescriptor{
				TripId:  testutils.Ptr(tripID),
				RouteId: testutils.Ptr(routeID),
			},
			StopTimeUpdate: StopTimeUpdates,
		},
	})
	return msg
}
