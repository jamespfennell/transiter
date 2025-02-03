package endtoend

import (
	"fmt"
	"testing"

	gtfsrt "github.com/jamespfennell/gtfs/proto"
	"github.com/jamespfennell/transiter/tests/endtoend/fixtures"
	"github.com/jamespfennell/transiter/tests/endtoend/testutils"
	"github.com/jamespfennell/transiter/tests/endtoend/transiterclient"
)

var Vehicle1 = transiterclient.Vehicle{
	ID: "vehicle_1_id",
	Trip: &transiterclient.TripReference{
		ID:          "trip_1_id",
		DirectionID: true,
		Route:       transiterclient.RouteReference{ID: RouteID},
	},
	Latitude:  40.75,
	Longitude: -73.875,
}

var Vehicle2 = transiterclient.Vehicle{
	ID: "vehicle_2_id",
	Trip: &transiterclient.TripReference{
		ID:          "trip_2_id",
		DirectionID: true,
		Route:       transiterclient.RouteReference{ID: RouteID},
	},
	Latitude:  30,
	Longitude: -150,
}

var Vehicle3 = transiterclient.Vehicle{
	ID: "vehicle_3_id",
	Trip: &transiterclient.TripReference{
		ID:          "trip_3_id",
		DirectionID: true,
		Route:       transiterclient.RouteReference{ID: RouteID},
	},
	Latitude:  50,
	Longitude: -50,
}

var VehiclesGTFSStaticZip = fixtures.GTFSStaticDefaultZipBuilder().AddOrReplaceFile(
	"routes.txt",
	"route_id,route_type",
	fmt.Sprintf("%s,2", RouteID),
).AddOrReplaceFile(
	"stops.txt",
	"stop_id",
	Stop1ID,
	Stop2ID,
	Stop3ID,
).MustBuild()

const (
	VehicleSearchLatitude  = 40.755
	VehicleSearchLongitude = -73.8755
)

func TestVehicles(t *testing.T) {
	for _, tc := range []struct {
		name string
		test func(t *testing.T, client *transiterclient.TransiterClient, systemID string)
	}{
		{
			name: "list vehicles",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string) {
				gotListVehicles, err := client.ListVehicles(systemID)
				if err != nil {
					t.Fatalf("failed to list vehicles: %v", err)
				}
				testutils.AssertEqual(t, gotListVehicles.Vehicles, []transiterclient.Vehicle{
					Vehicle1, Vehicle2, Vehicle3,
				})
			},
		},
		{
			name: "list vehicles with pagination",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string) {
				gotListVehicles, err := client.ListVehicles(systemID, transiterclient.QueryParam{
					Key: "limit", Value: "2",
				})
				if err != nil {
					t.Fatalf("failed to list vehicles (first page): %v", err)
				}
				testutils.AssertEqual(t, gotListVehicles, &transiterclient.ListVehiclesResponse{
					Vehicles: []transiterclient.Vehicle{Vehicle1, Vehicle2},
					NextID:   testutils.Ptr(Vehicle3.ID),
				})

				gotListVehicles, err = client.ListVehicles(systemID, transiterclient.QueryParam{
					Key: "limit", Value: "2",
				}, transiterclient.QueryParam{
					Key: "first_id", Value: *gotListVehicles.NextID,
				})
				if err != nil {
					t.Fatalf("failed to list vehicles (second page): %v", err)
				}
				testutils.AssertEqual(t, gotListVehicles, &transiterclient.ListVehiclesResponse{
					Vehicles: []transiterclient.Vehicle{Vehicle3},
					NextID:   nil,
				})
			},
		},
		{
			name: "list vehicles with filtering",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string) {
				gotListVehicles, err := client.ListVehicles(systemID, transiterclient.QueryParam{
					Key: "only_return_specified_ids", Value: "true",
				}, transiterclient.QueryParam{
					Key: "id[]", Value: Vehicle2.ID,
				}, transiterclient.QueryParam{
					Key: "id[]", Value: Vehicle3.ID,
				})
				if err != nil {
					t.Fatalf("failed to list vehicles with filtering: %v", err)
				}
				testutils.AssertEqual(t, gotListVehicles.Vehicles, []transiterclient.Vehicle{
					Vehicle2, Vehicle3,
				})
			},
		},
		{
			name: "get vehicle",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string) {
				for _, wantVehicle := range []transiterclient.Vehicle{Vehicle1, Vehicle2, Vehicle3} {
					gotVehicle, err := client.GetVehicle(systemID, wantVehicle.ID)
					if err != nil {
						t.Fatalf("failed to get vehicle %s: %v", wantVehicle.ID, err)
					}
					testutils.AssertEqual(t, gotVehicle, &wantVehicle)
				}
			},
		},
		{
			name: "geographic search",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string) {
				type testCase struct {
					searchDistance float64
					wantVehicles   []transiterclient.Vehicle
				}

				for _, tc := range []testCase{
					{
						// No vehicles within 0.5km of relative location
						searchDistance: 0,
						wantVehicles:   []transiterclient.Vehicle{},
					},
					{
						// Only vehicle 1 is within 1km of the relative location
						searchDistance: 1,
						wantVehicles:   []transiterclient.Vehicle{Vehicle1},
					},
					{
						// All vehicles returned in order of distance
						searchDistance: 40075,
						wantVehicles:   []transiterclient.Vehicle{Vehicle1, Vehicle3, Vehicle2},
					},
				} {
					params := []transiterclient.QueryParam{
						{Key: "search_mode", Value: "DISTANCE"},
						{Key: "latitude", Value: fmt.Sprintf("%f", VehicleSearchLatitude)},
						{Key: "longitude", Value: fmt.Sprintf("%f", VehicleSearchLongitude)},
						{Key: "max_distance", Value: fmt.Sprintf("%f", tc.searchDistance)},
					}

					gotListVehicles, err := client.ListVehicles(systemID, params...)
					if err != nil {
						t.Fatalf("failed to list vehicles with geographic search: %v", err)
					}
					testutils.AssertEqual(t, gotListVehicles.Vehicles, tc.wantVehicles)
				}
			},
		},
		{
			name: "trip view",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string) {
				gotTrip, err := client.GetTrip(systemID, RouteID, Vehicle1.Trip.ID)
				if err != nil {
					t.Fatalf("failed to get trip: %v", err)
				}
				testutils.AssertEqual(t, gotTrip.Vehicle, &transiterclient.VehicleReference{
					ID: Vehicle1.ID,
				})
			},
		},
	} {
		testName := fmt.Sprintf("%s/%s", "vehicles", tc.name)
		t.Run(testName, func(t *testing.T) {
			systemID, _, realtimeFeedURL := fixtures.InstallSystem(t, VehiclesGTFSStaticZip)
			fixtures.PublishGTFSRTMessageAndUpdate(t, systemID, realtimeFeedURL, buildGTFSRTMessage())
			transiterClient := fixtures.GetTransiterClient(t)
			tc.test(t, transiterClient, systemID)
		})
	}
}

func buildGTFSRTMessage() *gtfsrt.FeedMessage {
	buildVehicleEntity := func(vehicle transiterclient.Vehicle) *gtfsrt.FeedEntity {
		return &gtfsrt.FeedEntity{
			Id: testutils.Ptr(fmt.Sprintf("vehicle_%s", vehicle.ID)),
			Vehicle: &gtfsrt.VehiclePosition{
				Vehicle: &gtfsrt.VehicleDescriptor{
					Id: testutils.Ptr(vehicle.ID),
				},
				Trip: &gtfsrt.TripDescriptor{
					TripId: testutils.Ptr(vehicle.Trip.ID),
				},
				Position: &gtfsrt.Position{
					Latitude:  testutils.Ptr(float32(vehicle.Latitude)),
					Longitude: testutils.Ptr(float32(vehicle.Longitude)),
				},
			},
		}
	}

	buildTripEntity := func(vehicle transiterclient.Vehicle, stopTimeUpdates []*gtfsrt.TripUpdate_StopTimeUpdate) *gtfsrt.FeedEntity {
		return &gtfsrt.FeedEntity{
			Id: testutils.Ptr(fmt.Sprintf("trip_%s", vehicle.Trip.ID)),
			TripUpdate: &gtfsrt.TripUpdate{
				Vehicle: &gtfsrt.VehicleDescriptor{
					Id: testutils.Ptr(vehicle.ID),
				},
				Trip: &gtfsrt.TripDescriptor{
					TripId:      testutils.Ptr(vehicle.Trip.ID),
					RouteId:     testutils.Ptr(RouteID),
					DirectionId: testutils.Ptr(uint32(1)),
				},
				StopTimeUpdate: stopTimeUpdates,
			},
		}
	}

	stopTimeUpdate := func(stopID string, arrivalTime int64, stopSequence int32) *gtfsrt.TripUpdate_StopTimeUpdate {
		return &gtfsrt.TripUpdate_StopTimeUpdate{
			StopId: testutils.Ptr(stopID),
			Arrival: &gtfsrt.TripUpdate_StopTimeEvent{
				Time: testutils.Ptr(int64(arrivalTime)),
			},
			Departure: &gtfsrt.TripUpdate_StopTimeEvent{
				Time: testutils.Ptr(int64(arrivalTime + 15)),
			},
			StopSequence: testutils.Ptr(uint32(stopSequence)),
		}
	}

	return &gtfsrt.FeedMessage{
		Header: &gtfsrt.FeedHeader{
			GtfsRealtimeVersion: testutils.Ptr("2.0"),
			Timestamp:           testutils.Ptr(uint64(0)),
		},
		Entity: []*gtfsrt.FeedEntity{
			buildVehicleEntity(Vehicle1),
			buildVehicleEntity(Vehicle2),
			buildVehicleEntity(Vehicle3),
			buildTripEntity(Vehicle1, []*gtfsrt.TripUpdate_StopTimeUpdate{
				stopTimeUpdate(Stop1ID, 300, 1),
				stopTimeUpdate(Stop2ID, 800, 2),
				stopTimeUpdate(Stop3ID, 850, 3),
			}),
			buildTripEntity(Vehicle2, []*gtfsrt.TripUpdate_StopTimeUpdate{}),
			buildTripEntity(Vehicle3, []*gtfsrt.TripUpdate_StopTimeUpdate{}),
		},
	}
}
