package endtoend

import (
	"fmt"
	"testing"
	"time"

	gtfsrt "github.com/jamespfennell/gtfs/proto"
	"github.com/jamespfennell/transiter/tests/endtoend/fixtures"
	"github.com/jamespfennell/transiter/tests/endtoend/testutils"
	"github.com/jamespfennell/transiter/tests/endtoend/transiterclient"
)

const (
	Trip1ID = "trip_1_id"
	Trip2ID = "trip_2_id"
	Trip3ID = "trip_3_id"
)

var TripInitialTimetable = []stopTime{
	{Stop1, 300},
	{Stop2, 600},
	{Stop3, 800},
	{Stop4, 900},
	{Stop5, 1800},
	{Stop6, 2500},
}

var TripsGTFSStaticZip = fixtures.GTFSStaticDefaultZipBuilder().AddOrReplaceFile(
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
).MustBuild()

type testCase struct {
	useStopSequences bool
	currentTime      int64
	timetable        []stopTime
}

func TestTrips(t *testing.T) {
	timetables := [][]stopTime{
		// Basic case where the second update does nothing
		TripInitialTimetable,
		// Change the stop times - change time at Stop3 to before the update at t=700
		{
			{Stop1, 300},
			{Stop2, 800},
			{Stop3, 850},
			{Stop4, 900},
			{Stop5, 1800},
			{Stop6, 2500},
		},
		// Change the stop times - change time at Stop3 to after the update at t=700
		{
			{Stop1, 300},
			{Stop2, 600},
			{Stop3, 650},
			{Stop4, 900},
			{Stop5, 1800},
			{Stop6, 2500},
		},
		// Add a new stop at the end
		{
			{Stop1, 200},
			{Stop2, 600},
			{Stop3, 800},
			{Stop4, 900},
			{Stop5, 1800},
			{Stop6, 2500},
			{Stop7, 2600},
		},
		// Delete the last stop
		{
			{Stop1, 200},
			{Stop2, 600},
			{Stop3, 800},
			{Stop4, 900},
			{Stop5, 1800},
		},
		// Swap the ordering of the last two stops
		{
			{Stop1, 300},
			{Stop2, 600},
			{Stop3, 800},
			{Stop4, 900},
			{Stop5, 1800},
			{Stop7, 2500},
			{Stop6, 3000},
		},
	}

	for _, useStopSequences := range []bool{true, false} {
		for _, currentTime := range []int64{0, 10, 700, 4000} {
			for _, timetable := range timetables {
				name := fmt.Sprintf("sequences=%v/time=%d/case=%v", useStopSequences, currentTime, timetable)
				t.Run(name, func(t *testing.T) {
					testTripUpdates(t, testCase{
						useStopSequences: useStopSequences,
						currentTime:      currentTime,
						timetable:        timetable,
					})
				})
			}
		}
	}
}

func testTripUpdates(t *testing.T, tc testCase) {
	systemID, _, realtimeFeedURL := fixtures.InstallSystem(t, TripsGTFSStaticZip)
	client := fixtures.GetTransiterClient(t)

	// Publish feed updates
	stopIDToStopSequence := make(map[string]uint32)
	for _, update := range []struct {
		stopTimes    []stopTime
		timeAtUpdate int64
	}{
		{TripInitialTimetable, 0},
		{tc.timetable, tc.currentTime},
	} {
		stopTimeUpdates := make([]*gtfsrt.TripUpdate_StopTimeUpdate, 0)
		for stopSequence, stopTime := range update.stopTimes {
			if stopTime.time < update.timeAtUpdate {
				continue
			}
			stopIDToStopSequence[stopTime.stopID] = uint32(stopSequence + 25)
			stopTimeUpdate := &gtfsrt.TripUpdate_StopTimeUpdate{
				StopId: testutils.Ptr(stopTime.stopID),
				Arrival: &gtfsrt.TripUpdate_StopTimeEvent{
					Time: testutils.Ptr(stopTime.time),
				},
				Departure: &gtfsrt.TripUpdate_StopTimeEvent{
					Time: testutils.Ptr(stopTime.time + 15),
				},
			}
			if tc.useStopSequences {
				stopTimeUpdate.StopSequence = testutils.Ptr(stopIDToStopSequence[stopTime.stopID])
			}
			stopTimeUpdates = append(stopTimeUpdates, stopTimeUpdate)
		}
		message := gtfsrt.FeedMessage{
			Header: &gtfsrt.FeedHeader{
				GtfsRealtimeVersion: testutils.Ptr("2.0"),
				Timestamp:           testutils.Ptr(uint64(update.timeAtUpdate)),
			},
			Entity: []*gtfsrt.FeedEntity{
				{
					Id: testutils.Ptr("1"),
					TripUpdate: &gtfsrt.TripUpdate{
						Trip: &gtfsrt.TripDescriptor{
							TripId:      testutils.Ptr(Trip1ID),
							RouteId:     testutils.Ptr(RouteA),
							DirectionId: testutils.Ptr(uint32(1)),
						},
						StopTimeUpdate: stopTimeUpdates,
					},
				},
			},
		}
		fixtures.PublishGTFSRTMessageAndUpdate(t, systemID, realtimeFeedURL, &message)
	}

	// Test stop view
	allStopIDs := make(map[string]bool)
	stopIDToStopTime := make(map[string]int64)
	for _, stopTime := range TripInitialTimetable {
		allStopIDs[stopTime.stopID] = true
	}
	for _, stopTime := range tc.timetable {
		allStopIDs[stopTime.stopID] = true
		stopIDToStopTime[stopTime.stopID] = stopTime.time
	}

	for stopID := range allStopIDs {
		gotStop, err := client.GetStop(systemID, stopID)
		if err != nil {
			t.Fatalf("failed to get stop %s: %v", stopID, err)
		}

		time, hasStopTime := stopIDToStopTime[stopID]
		wantStopTimes := []transiterclient.StopTime{}
		if hasStopTime && time >= tc.currentTime {
			wantStopTimes = []transiterclient.StopTime{
				{
					Trip: &transiterclient.TripReference{
						ID:          Trip1ID,
						DirectionID: true,
						Route:       transiterclient.RouteReference{ID: RouteA},
					},
					Arrival: &transiterclient.EstimatedTime{
						Time: transiterclient.Int64String(time),
					},
					Departure: &transiterclient.EstimatedTime{
						Time: transiterclient.Int64String(time + 15),
					},
					Future: true,
				},
			}
			if tc.useStopSequences {
				wantStopTimes[0].StopSequence = testutils.Ptr(stopIDToStopSequence[stopID])
			}
		}

		if !tc.useStopSequences {
			for i := range gotStop.StopTimes {
				gotStop.StopTimes[i].StopSequence = nil
			}
		}
		testutils.AssertEqual(t, gotStop.StopTimes, wantStopTimes)
	}

	// Test trip view
	gotTrip, err := client.GetTrip(systemID, RouteA, Trip1ID)
	if err != nil {
		t.Fatalf("failed to get trip: %v", err)
	}

	wantStopTimes := []transiterclient.StopTime{}
	stopIDsInSecondUpdate := make(map[string]bool)
	for _, stopTime := range tc.timetable {
		if stopTime.time >= tc.currentTime {
			stopIDsInSecondUpdate[stopTime.stopID] = true
		}
	}

	for _, stopTime := range TripInitialTimetable {
		if _, ok := stopIDsInSecondUpdate[stopTime.stopID]; ok {
			break
		}
		wantStopTimes = append(wantStopTimes, transiterclient.StopTime{
			Arrival: &transiterclient.EstimatedTime{
				Time: transiterclient.Int64String(stopTime.time),
			},
			Departure: &transiterclient.EstimatedTime{
				Time: transiterclient.Int64String(stopTime.time + 15),
			},
			Future: false,
		})
	}

	for _, stopTime := range tc.timetable {
		if stopTime.time < tc.currentTime {
			continue
		}
		wantStopTimes = append(wantStopTimes, transiterclient.StopTime{
			Arrival: &transiterclient.EstimatedTime{
				Time: transiterclient.Int64String(stopTime.time),
			},
			Departure: &transiterclient.EstimatedTime{
				Time: transiterclient.Int64String(stopTime.time + 15),
			},
			Future: true,
		})
	}

	// We don't know the exact values of the Transiter generated stop sequences
	for i := range gotTrip.StopTimes {
		gotTrip.StopTimes[i].StopSequence = nil
	}

	wantTrip := transiterclient.Trip{
		ID:        Trip1ID,
		StopTimes: wantStopTimes,
		Alerts:    []transiterclient.AlertReference{},
	}
	testutils.AssertEqual(t, gotTrip, &wantTrip)
}

func TestArrivalDepartureOrdering(t *testing.T) {
	for _, tc := range []struct {
		name        string
		dataPresent string
	}{
		{"arrival", "arrival"},
		{"departure", "departure"},
	} {
		t.Run(tc.name, func(t *testing.T) {
			systemID, _, realtimeFeedURL := fixtures.InstallSystem(t, TripsGTFSStaticZip)
			client := fixtures.GetTransiterClient(t)

			message := gtfsrt.FeedMessage{
				Header: &gtfsrt.FeedHeader{
					GtfsRealtimeVersion: testutils.Ptr("2.0"),
					Timestamp:           testutils.Ptr(uint64(time.Now().Unix())),
				},
				Entity: []*gtfsrt.FeedEntity{
					buildTripEntity("1", Trip1ID, Stop1, 500, tc.dataPresent),
					buildTripEntity("2", Trip2ID, Stop1, 1100, "both"),
					buildTripEntity("4", Trip3ID, Stop1, 1500, tc.dataPresent),
				},
			}

			fixtures.PublishGTFSRTMessageAndUpdate(t, systemID, realtimeFeedURL, &message)

			gotStop, err := client.GetStop(systemID, Stop1)
			if err != nil {
				t.Fatalf("failed to get stop: %v", err)
			}

			wantStopTimes := []transiterclient.StopTime{
				{
					Trip: &transiterclient.TripReference{
						ID:          Trip1ID,
						Route:       transiterclient.RouteReference{ID: RouteA},
						DirectionID: true,
					},
					Arrival: &transiterclient.EstimatedTime{
						Time: transiterclient.Int64String(func() int64 {
							if tc.dataPresent == "arrival" {
								return 500
							}
							return 0
						}()),
					},
					Departure: &transiterclient.EstimatedTime{
						Time: transiterclient.Int64String(func() int64 {
							if tc.dataPresent == "departure" {
								return 500
							}
							return 0
						}()),
					},
					StopSequence: testutils.Ptr(uint32(1)),
					Future:       true,
				},
				{
					Trip: &transiterclient.TripReference{
						ID:          Trip2ID,
						Route:       transiterclient.RouteReference{ID: RouteA},
						DirectionID: true,
					},
					Arrival: &transiterclient.EstimatedTime{
						Time: transiterclient.Int64String(1100),
					},
					Departure: &transiterclient.EstimatedTime{
						Time: transiterclient.Int64String(1115),
					},
					StopSequence: testutils.Ptr(uint32(1)),
					Future:       true,
				},
				{
					Trip: &transiterclient.TripReference{
						ID:          Trip3ID,
						Route:       transiterclient.RouteReference{ID: RouteA},
						DirectionID: true,
					},
					Arrival: &transiterclient.EstimatedTime{
						Time: transiterclient.Int64String(func() int64 {
							if tc.dataPresent == "arrival" {
								return 1500
							}
							return 0
						}()),
					},
					Departure: &transiterclient.EstimatedTime{
						Time: transiterclient.Int64String(func() int64 {
							if tc.dataPresent == "departure" {
								return 1500
							}
							return 0
						}()),
					},
					StopSequence: testutils.Ptr(uint32(1)),
					Future:       true,
				},
			}

			testutils.AssertEqual(t, gotStop.StopTimes, wantStopTimes)
		})
	}
}

func buildTripEntity(id, tripID, stopID string, timestamp int64, dataPresent string) *gtfsrt.FeedEntity {
	entity := &gtfsrt.FeedEntity{
		Id: testutils.Ptr(id),
		TripUpdate: &gtfsrt.TripUpdate{
			Trip: &gtfsrt.TripDescriptor{
				TripId:      testutils.Ptr(tripID),
				RouteId:     testutils.Ptr(RouteA),
				DirectionId: testutils.Ptr(uint32(1)),
			},
			StopTimeUpdate: []*gtfsrt.TripUpdate_StopTimeUpdate{
				{
					StopId:       testutils.Ptr(stopID),
					StopSequence: testutils.Ptr(uint32(1)),
				},
			},
		},
	}

	update := entity.TripUpdate.StopTimeUpdate[0]
	switch dataPresent {
	case "arrival":
		update.Arrival = &gtfsrt.TripUpdate_StopTimeEvent{Time: testutils.Ptr(timestamp)}
	case "departure":
		update.Departure = &gtfsrt.TripUpdate_StopTimeEvent{Time: testutils.Ptr(timestamp)}
	case "both":
		update.Arrival = &gtfsrt.TripUpdate_StopTimeEvent{Time: testutils.Ptr(timestamp)}
		update.Departure = &gtfsrt.TripUpdate_StopTimeEvent{Time: testutils.Ptr(timestamp + 15)}
	}

	return entity
}
