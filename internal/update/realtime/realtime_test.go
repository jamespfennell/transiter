package realtime

import (
	"context"
	"testing"
	"time"

	"github.com/google/go-cmp/cmp"
	"github.com/google/go-cmp/cmp/cmpopts"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jamespfennell/gtfs"
	"github.com/jamespfennell/transiter/internal/convert"
	"github.com/jamespfennell/transiter/internal/db/dbtesting"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/update/common"
	"golang.org/x/exp/slog"
)

const (
	systemID   = "systemID1"
	routeID1   = "routeID1"
	stopID1    = "stopID1"
	stopID2    = "stopID2"
	stopID3    = "stopID3"
	stopID4    = "stopID4"
	tripID1    = "tripID1"
	vehicleID1 = "vehicleID1"
	vehicleID2 = "vehicleID2"
)

func TestUpdateTrips(t *testing.T) {
	for _, tc := range []struct {
		name string
		// The update process will run N times, 1 for each trip version. Providing <nil> for a version
		// will run an update with no trips.
		tripVersions        []*gtfs.Trip
		wantTrip            *Trip
		gtfsRealTimeOptions *api.GtfsRealtimeOptions
	}{
		{
			name: "simple case",
			tripVersions: []*gtfs.Trip{
				gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{
					gtfsStu(gStopID(stopID1), gDepTime(5)),
					gtfsStu(gStopID(stopID2), gArrTime(10), gDepTime(15)),
					gtfsStu(gStopID(stopID3), gArrTime(20), gDepTime(25)),
					gtfsStu(gStopID(stopID4), gArrTime(30)),
				}),
			},
			wantTrip: wantTrip(tripID1, routeID1, true, []StopTime{
				wantSt(0, stopID1, wDepTime(5)),
				wantSt(1, stopID2, wArrTime(10), wDepTime(15)),
				wantSt(2, stopID3, wArrTime(20), wDepTime(25)),
				wantSt(3, stopID4, wArrTime(30)),
			}),
		},
		{
			name: "trip deleted",
			tripVersions: []*gtfs.Trip{
				gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{
					gtfsStu(gStopID(stopID1), gDepTime(5)),
					gtfsStu(gStopID(stopID2), gArrTime(10), gDepTime(15)),
					gtfsStu(gStopID(stopID3), gArrTime(20), gDepTime(25)),
					gtfsStu(gStopID(stopID4), gArrTime(30)),
				}),
				nil,
			},
			wantTrip: nil,
		},
		{
			name: "same update twice",
			tripVersions: []*gtfs.Trip{
				gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{
					gtfsStu(gStopID(stopID1), gDepTime(5)),
					gtfsStu(gStopID(stopID2), gArrTime(10), gDepTime(15)),
					gtfsStu(gStopID(stopID3), gArrTime(20), gDepTime(25)),
					gtfsStu(gStopID(stopID4), gArrTime(30)),
				}),
				gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{
					gtfsStu(gStopID(stopID1), gDepTime(5)),
					gtfsStu(gStopID(stopID2), gArrTime(10), gDepTime(15)),
					gtfsStu(gStopID(stopID3), gArrTime(20), gDepTime(25)),
					gtfsStu(gStopID(stopID4), gArrTime(30)),
				}),
			},
			wantTrip: wantTrip(tripID1, routeID1, true, []StopTime{
				wantSt(0, stopID1, wDepTime(5)),
				wantSt(1, stopID2, wArrTime(10), wDepTime(15)),
				wantSt(2, stopID3, wArrTime(20), wDepTime(25)),
				wantSt(3, stopID4, wArrTime(30)),
			}),
		},
		{
			name: "basic update case",
			tripVersions: []*gtfs.Trip{
				gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{
					gtfsStu(gStopID(stopID1), gDepTime(5)),
					gtfsStu(gStopID(stopID2), gArrTime(10), gDepTime(15)),
					gtfsStu(gStopID(stopID3), gArrTime(20), gDepTime(25)),
					gtfsStu(gStopID(stopID4), gArrTime(30)),
				}),
				gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{
					gtfsStu(gStopID(stopID1), gDepTime(5)),
					gtfsStu(gStopID(stopID2), gArrTime(11), gDepTime(16)),
					gtfsStu(gStopID(stopID3), gArrTime(20), gDepTime(25)),
					gtfsStu(gStopID(stopID4), gArrTime(31)),
				}),
			},
			wantTrip: wantTrip(tripID1, routeID1, true, []StopTime{
				wantSt(0, stopID1, wDepTime(5)),
				wantSt(1, stopID2, wArrTime(11), wDepTime(16)),
				wantSt(2, stopID3, wArrTime(20), wDepTime(25)),
				wantSt(3, stopID4, wArrTime(31)),
			}),
		},
		{
			name: "update with stops in the past",
			tripVersions: []*gtfs.Trip{
				gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{
					gtfsStu(gStopID(stopID1), gDepTime(5)),
					gtfsStu(gStopID(stopID2), gArrTime(10), gDepTime(15)),
					gtfsStu(gStopID(stopID3), gArrTime(20), gDepTime(25)),
					gtfsStu(gStopID(stopID4), gArrTime(30)),
				}),
				gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{
					gtfsStu(gStopID(stopID3), gArrTime(20), gDepTime(25)),
					gtfsStu(gStopID(stopID4), gArrTime(31)),
				}),
			},
			wantTrip: wantTrip(tripID1, routeID1, true, []StopTime{
				wantSt(0, stopID1, wDepTime(5), wPast),
				wantSt(1, stopID2, wArrTime(10), wDepTime(15), wPast),
				wantSt(2, stopID3, wArrTime(20), wDepTime(25)),
				wantSt(3, stopID4, wArrTime(31)),
			}),
		},
		{
			name: "reassign stop sequences",
			gtfsRealTimeOptions: &api.GtfsRealtimeOptions{
				ReassignStopSequences: true,
			},
			tripVersions: []*gtfs.Trip{
				gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{
					gtfsStu(gStopID(stopID1), gArrTime(5), gStopSeq(1)),
					gtfsStu(gStopID(stopID2), gArrTime(10), gStopSeq(2)),
					gtfsStu(gStopID(stopID3), gArrTime(20), gStopSeq(3)),
					gtfsStu(gStopID(stopID4), gArrTime(30), gStopSeq(4)),
				}),
				gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{
					gtfsStu(gStopID(stopID1), gArrTime(5), gStopSeq(2)),
					gtfsStu(gStopID(stopID2), gArrTime(10), gStopSeq(3)),
					gtfsStu(gStopID(stopID3), gArrTime(20), gStopSeq(4)),
					gtfsStu(gStopID(stopID4), gArrTime(30), gStopSeq(5)),
				}),
			},
			wantTrip: wantTrip(tripID1, routeID1, true, []StopTime{
				wantSt(0, stopID1, wArrTime(5)),
				wantSt(1, stopID2, wArrTime(10)),
				wantSt(2, stopID3, wArrTime(20)),
				wantSt(3, stopID4, wArrTime(30)),
			}),
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			querier := dbtesting.NewQuerier(t)
			system := querier.NewSystem(systemID)
			stopPkToID := map[int64]string{}
			for _, stopID := range []string{stopID1, stopID2, stopID3, stopID4} {
				stopPkToID[system.NewStop(stopID).Pk] = stopID
			}
			routePkToID := map[int64]string{}
			routeIDToPk := map[string]int64{}
			for _, routeID := range []string{routeID1} {
				route := system.NewRoute(routeID)
				routePkToID[route.Data.Pk] = routeID
				routeIDToPk[routeID] = route.Data.Pk
			}
			feed := system.NewFeed("feedID")

			ctx := context.Background()
			updateCtx := common.UpdateContext{
				Querier:  querier,
				SystemPk: system.Data.Pk,
				FeedPk:   feed.Data.Pk,
				FeedConfig: &api.FeedConfig{
					GtfsRealtimeOptions: tc.gtfsRealTimeOptions,
				},
				Logger: slog.Default(),
			}

			for i, tripVersion := range tc.tripVersions {
				var r gtfs.Realtime
				if tripVersion != nil {
					r.Trips = append(r.Trips, *tripVersion)
				}
				err := Update(ctx, updateCtx, &r)
				if err != nil {
					t.Fatalf("Update(trip version %d) got = %v, want = <nil>", err, i)
				}
			}

			gotTrip := readTripFromDB(ctx, t, querier, routeIDToPk, stopPkToID)

			if diff := cmp.Diff(gotTrip, tc.wantTrip); diff != "" {
				t.Errorf("got = %v, want = %v, diff = %s", gotTrip, tc.wantTrip, diff)
			}
		})
	}
}

func TestUpdateVehicles(t *testing.T) {
	for _, tc := range []struct {
		name              string
		vehicleGroups     [][]*gtfs.Vehicle
		wantVehicleGroups [][]*Vehicle
		tripVersions      []*gtfs.Trip
	}{
		{
			name: "simple case",
			vehicleGroups: [][]*gtfs.Vehicle{
				{
					{
						ID: &gtfs.VehicleID{
							ID: vehicleID1,
						},
						IsEntityInMessage: true,
					},
				},
			},
			wantVehicleGroups: [][]*Vehicle{
				{
					wantVehicle(vehicleID1, systemID, nil, nil, nil, nil, nil,
						nil, nil, nil, nil, nil, nil, nil, nil, nil, nil),
				},
			},
		},
		{
			name: "trip with no id",
			vehicleGroups: [][]*gtfs.Vehicle{
				{
					{
						ID:                &gtfs.VehicleID{},
						IsEntityInMessage: true,
					},
				},
			},
			wantVehicleGroups: [][]*Vehicle{
				{},
			},
		},
		{
			name: "entity not in message",
			vehicleGroups: [][]*gtfs.Vehicle{
				{
					{
						ID: &gtfs.VehicleID{
							ID: vehicleID1,
						},
					},
				},
			},
			wantVehicleGroups: [][]*Vehicle{
				{},
			},
		},
		{
			name: "lots of fields",
			vehicleGroups: [][]*gtfs.Vehicle{
				{
					{
						ID: &gtfs.VehicleID{
							ID:           vehicleID1,
							Label:        "label",
							LicensePlate: "licensePlate",
						},
						Position: &gtfs.Position{
							Latitude:  ptr(float32(1.0)),
							Longitude: ptr(float32(2.0)),
							Bearing:   ptr(float32(3.0)),
							Odometer:  ptr(4.0),
							Speed:     ptr(float32(5.0)),
						},
						// STOPPED_AT
						CurrentStatus: ptr(gtfs.CurrentStatus(1)),
						Timestamp:     ptr(mkTime(6)),
						// RUNNING_SMOOTHLY
						CongestionLevel: gtfs.CongestionLevel(1),
						// MANY_SEATS_AVAILABLE
						OccupancyStatus:     ptr(gtfs.OccupancyStatus(1)),
						OccupancyPercentage: ptr(uint32(8)),
						IsEntityInMessage:   true,
					},
				},
			},
			wantVehicleGroups: [][]*Vehicle{
				{
					wantVehicle(
						vehicleID1, systemID, nil,
						ptr("label"), ptr("licensePlate"),
						ptr(float32(1.0)), ptr(float32(2.0)), ptr(float32(3.0)), ptr(4.0), ptr(float32(5.0)),
						ptr(gtfs.CongestionLevel(1)),
						ptr(mkTime(6)),
						nil,
						ptr(gtfs.OccupancyStatus(1)),
						ptr(gtfs.CurrentStatus(1)),
						nil,
						ptr(uint32(8))),
				},
			},
		},
		{
			name: "associated trip",
			vehicleGroups: [][]*gtfs.Vehicle{
				{
					{
						ID: &gtfs.VehicleID{
							ID: vehicleID1,
						},
						Trip: &gtfs.Trip{
							ID: gtfs.TripID{
								ID: tripID1,
							},
						},
						IsEntityInMessage: true,
					},
				},
			},
			wantVehicleGroups: [][]*Vehicle{
				{
					wantVehicle(vehicleID1, systemID, ptr(tripID1),
						nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil),
				},
			},
			tripVersions: []*gtfs.Trip{
				gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{}),
			},
		},
		{
			name: "duplicate trips, same update",
			vehicleGroups: [][]*gtfs.Vehicle{
				{
					{
						ID: &gtfs.VehicleID{
							ID: vehicleID1,
						},
						Trip: &gtfs.Trip{
							ID: gtfs.TripID{
								ID: tripID1,
							},
						},
						IsEntityInMessage: true,
					},
					{
						ID: &gtfs.VehicleID{
							ID: vehicleID2,
						},
						Trip: &gtfs.Trip{
							ID: gtfs.TripID{
								ID: tripID1,
							},
						},
						IsEntityInMessage: true,
					},
				},
			},
			wantVehicleGroups: [][]*Vehicle{
				{
					wantVehicle(vehicleID1, systemID, ptr(tripID1),
						nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil),
				},
			},
			tripVersions: []*gtfs.Trip{
				gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{}),
			},
		},
		{
			name: "trip changes vehicles across updates",
			vehicleGroups: [][]*gtfs.Vehicle{
				{
					{
						ID: &gtfs.VehicleID{
							ID: vehicleID1,
						},
						Trip: &gtfs.Trip{
							ID: gtfs.TripID{
								ID: tripID1,
							},
						},
						IsEntityInMessage: true,
					},
				},
				{
					{
						ID: &gtfs.VehicleID{
							ID: vehicleID2,
						},
						Trip: &gtfs.Trip{
							ID: gtfs.TripID{
								ID: tripID1,
							},
						},
						IsEntityInMessage: true,
					},
				},
			},
			wantVehicleGroups: [][]*Vehicle{
				{
					wantVehicle(vehicleID1, systemID, ptr(tripID1),
						nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil),
				},
				{
					wantVehicle(vehicleID2, systemID, ptr(tripID1),
						nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil),
				},
			},
			tripVersions: []*gtfs.Trip{
				gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{}),
			},
		},
		{
			name: "duplicate trips, different updates",
			vehicleGroups: [][]*gtfs.Vehicle{
				{
					{
						ID: &gtfs.VehicleID{
							ID: vehicleID1,
						},
						Trip: &gtfs.Trip{
							ID: gtfs.TripID{
								ID: tripID1,
							},
						},
						IsEntityInMessage: true,
					},
				},
				{
					{
						ID: &gtfs.VehicleID{
							ID: vehicleID1,
						},
						Trip: &gtfs.Trip{
							ID: gtfs.TripID{
								ID: tripID1,
							},
						},
						IsEntityInMessage: true,
					},
					{
						ID: &gtfs.VehicleID{
							ID: vehicleID2,
						},
						Trip: &gtfs.Trip{
							ID: gtfs.TripID{
								ID: tripID1,
							},
						},
						IsEntityInMessage: true,
					},
				},
			},
			wantVehicleGroups: [][]*Vehicle{
				{
					wantVehicle(vehicleID1, systemID, ptr(tripID1),
						nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil),
				},
				{
					// If an existing vehicle and incoming vehicle both have same trip ID, we
					// keep the existing vehicle and ignore the incoming vehicle.
					wantVehicle(vehicleID1, systemID, ptr(tripID1),
						nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil),
				},
			},
			tripVersions: []*gtfs.Trip{
				gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{}),
			},
		},
		{
			name: "duplicate vehicle ids",
			vehicleGroups: [][]*gtfs.Vehicle{
				{
					{
						ID: &gtfs.VehicleID{
							ID: vehicleID1,
						},
						IsEntityInMessage: true,
					},
					{
						ID: &gtfs.VehicleID{
							ID: vehicleID1,
						},
						IsEntityInMessage: true,
					},
				},
			},
			wantVehicleGroups: [][]*Vehicle{
				{
					wantVehicle(vehicleID1, systemID, nil,
						nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil),
				},
			},
			tripVersions: []*gtfs.Trip{
				gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{}),
			},
		},
		{
			name: "associated trip and stop",
			vehicleGroups: [][]*gtfs.Vehicle{
				{
					{
						ID: &gtfs.VehicleID{
							ID: vehicleID1,
						},
						Trip: &gtfs.Trip{
							ID: gtfs.TripID{
								ID: tripID1,
							},
						},
						CurrentStopSequence: ptr(uint32(0)),
						StopID:              ptr(stopID1),
						IsEntityInMessage:   true,
					},
				},
			},
			wantVehicleGroups: [][]*Vehicle{
				{
					wantVehicle(vehicleID1, systemID, ptr(tripID1),
						nil, nil, nil, nil, nil, nil, nil, nil, nil, ptr(int32(0)), nil, nil, ptr(stopID1), nil),
				},
			},
			tripVersions: []*gtfs.Trip{
				gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{
					gtfsStu(gStopID(stopID1), gDepTime(5)),
					gtfsStu(gStopID(stopID2), gArrTime(10), gDepTime(15)),
				}),
			},
		}, {
			name: "vehicle update",
			vehicleGroups: [][]*gtfs.Vehicle{
				{
					{
						ID: &gtfs.VehicleID{
							ID: vehicleID1,
						},
						Position: &gtfs.Position{
							Latitude:  ptr(float32(1.0)),
							Longitude: ptr(float32(2.0)),
							Bearing:   ptr(float32(3.0)),
							Odometer:  ptr(4.0),
							Speed:     ptr(float32(5.0)),
						},
						IsEntityInMessage: true,
					},
				},
				{
					{
						ID: &gtfs.VehicleID{
							ID: vehicleID1,
						},
						Position: &gtfs.Position{
							Latitude:  ptr(float32(2.0)),
							Longitude: ptr(float32(3.0)),
							Bearing:   ptr(float32(4.0)),
							Odometer:  ptr(5.0),
							Speed:     ptr(float32(6.0)),
						},
						IsEntityInMessage: true,
					},
				},
			},
			wantVehicleGroups: [][]*Vehicle{
				{
					wantVehicle(
						vehicleID1, systemID, nil,
						nil, nil,
						ptr(float32(1.0)), ptr(float32(2.0)), ptr(float32(3.0)), ptr(4.0), ptr(float32(5.0)),
						nil,
						nil,
						nil,
						nil,
						nil,
						nil,
						nil),
				},
				{
					wantVehicle(
						vehicleID1, systemID, nil,
						nil, nil,
						ptr(float32(2.0)), ptr(float32(3.0)), ptr(float32(4.0)), ptr(5.0), ptr(float32(6.0)),
						nil,
						nil,
						nil,
						nil,
						nil,
						nil,
						nil),
				},
			},
		},
		{
			name: "stale vehicle deleted",
			vehicleGroups: [][]*gtfs.Vehicle{
				{
					{
						ID: &gtfs.VehicleID{
							ID: vehicleID1,
						},
						IsEntityInMessage: true,
					},
					{
						ID: &gtfs.VehicleID{
							ID: vehicleID2,
						},
						IsEntityInMessage: true,
					},
				},
				{
					{
						ID: &gtfs.VehicleID{
							ID: vehicleID2,
						},
						IsEntityInMessage: true,
					},
				},
			},
			wantVehicleGroups: [][]*Vehicle{
				{
					wantVehicle(vehicleID1, systemID, nil, nil, nil, nil, nil,
						nil, nil, nil, nil, nil, nil, nil, nil, nil, nil),
					wantVehicle(vehicleID2, systemID, nil, nil, nil, nil, nil,
						nil, nil, nil, nil, nil, nil, nil, nil, nil, nil),
				},
				{
					wantVehicle(vehicleID2, systemID, nil, nil, nil, nil, nil,
						nil, nil, nil, nil, nil, nil, nil, nil, nil, nil),
				},
			},
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			querier := dbtesting.NewQuerier(t)
			system := querier.NewSystem(systemID)
			stopPkToID := map[int64]string{}
			for _, stopID := range []string{stopID1, stopID2, stopID3, stopID4} {
				stopPkToID[system.NewStop(stopID).Pk] = stopID
			}
			for _, routeID := range []string{routeID1} {
				system.NewRoute(routeID)
			}
			tripsFeed := system.NewFeed("trips")
			vehiclesFeed := system.NewFeed("vehicles")

			ctx := context.Background()
			updateCtx := common.UpdateContext{
				Querier:  querier,
				SystemPk: system.Data.Pk,
				Logger:   slog.Default(),
			}

			for i, tripVersion := range tc.tripVersions {
				updateCtx.FeedPk = tripsFeed.Data.Pk
				var r gtfs.Realtime
				if tripVersion != nil {
					r.Trips = append(r.Trips, *tripVersion)
				}
				err := Update(ctx, updateCtx, &r)
				if err != nil {
					t.Fatalf("Update(trip version %d) got = %v, want = <nil>", err, i)
				}
			}

			systemPkToID := map[int64]string{}
			systemPkToID[system.Data.Pk] = systemID

			if len(tc.vehicleGroups) != len(tc.wantVehicleGroups) {
				t.Fatalf("len(vehicleGroups) != len(wantVehicleGroups)")
			}

			updateCtx.FeedPk = vehiclesFeed.Data.Pk
			updateCtx.FeedConfig = &api.FeedConfig{
				GtfsRealtimeOptions: &api.GtfsRealtimeOptions{
					OnlyProcessFullEntities: true,
				},
			}
			for i := range tc.vehicleGroups {
				vehicles := tc.vehicleGroups[i]
				wantVehicles := tc.wantVehicleGroups[i]

				var r gtfs.Realtime
				for _, vehicle := range vehicles {
					r.Vehicles = append(r.Vehicles, *vehicle)
				}

				err := Update(ctx, updateCtx, &r)
				if err != nil {
					t.Fatalf("Update(vehicle %d) got = %v, want = <nil>", err, i)
				}

				dbVehicles := readVehiclesFromDB(ctx, t, querier, system.Data.Pk, systemPkToID)

				opt := cmp.Options{
					cmpopts.IgnoreUnexported(pgtype.Numeric{}),
					cmp.Comparer(compareNumerics),
				}
				if diff := cmp.Diff(dbVehicles, wantVehicles, opt); diff != "" {
					t.Errorf("got = %v, want = %v, diff = %s", vehicles, tc.vehicleGroups, diff)
				}
			}
		})
	}
}

type Trip struct {
	RouteID   string
	DBFields  db.GetTripRow
	StopTimes []StopTime
}

type Vehicle struct {
	SystemID      string
	TripID        *string
	CurrentStopID *string
	DBFields      db.GetVehicleRow
}

func readTripFromDB(ctx context.Context, t *testing.T, querier db.Querier, routeIDToPk map[string]int64, stopPkToID map[int64]string) *Trip {
	dbTrip, err := querier.GetTrip(ctx, db.GetTripParams{
		RoutePk: routeIDToPk[routeID1],
		TripID:  tripID1,
	})
	if err == pgx.ErrNoRows {
		return nil
	}
	if err != nil {
		t.Fatalf("GetTrip(routeID=%s, tripID=%s) err got = %v, want = <nil>", routeID1, tripID1, err)
	}
	dbStopTimes, err := querier.ListStopsTimesForTrip(ctx, dbTrip.Pk)
	if err != nil {
		t.Fatalf("ListStopTimesForTrip(routeID=%s, tripID=%s) err got = %v, want = <nil>", routeID1, tripID1, err)
	}

	var outStopTimes []StopTime
	for _, inStopTime := range dbStopTimes {
		outStopTimes = append(outStopTimes, NewStopTimeFromDB(inStopTime, stopPkToID))
	}
	// Clear all primary key columns
	dbTrip.Pk = 0
	dbTrip.RoutePk = 0
	dbTrip.FeedPk = 0
	dbTrip.GtfsHash = ""
	return &Trip{
		RouteID:   routeID1,
		DBFields:  dbTrip,
		StopTimes: outStopTimes,
	}
}

func readVehiclesFromDB(
	ctx context.Context,
	t *testing.T, querier db.Querier,
	systemPk int64,
	systemPkToID map[int64]string) []*Vehicle {
	dbVehicles, err := querier.ListVehicles(ctx, db.ListVehiclesParams{
		SystemPk:       systemPk,
		NumVehicles:    100,
		FirstVehicleID: convert.NullString(ptr("")),
	})
	if err == pgx.ErrNoRows {
		return nil
	}
	if err != nil {
		t.Fatalf("ListVehicles(systemPk=%d) err got = %v, want = <nil>", systemPk, err)
	}

	vehicles := make([]*Vehicle, 0, len(dbVehicles))

	for _, dbVehicle := range dbVehicles {
		systemID, ok := systemPkToID[dbVehicle.SystemPk]
		if !ok {
			t.Fatalf("systemPkToID[%d] not found", systemPk)
		}

		var tripID *string = nil
		if dbVehicle.TripID.Valid {
			tripID = &dbVehicle.TripID.String
		}

		var currentStopID *string = nil
		if dbVehicle.StopID.Valid {
			currentStopID = &dbVehicle.StopID.String
		}

		vehicles = append(vehicles, &Vehicle{
			SystemID:      systemID,
			TripID:        tripID,
			CurrentStopID: currentStopID,
			DBFields: db.GetVehicleRow{
				ID:                  dbVehicle.ID,
				Label:               dbVehicle.Label,
				LicensePlate:        dbVehicle.LicensePlate,
				Latitude:            dbVehicle.Latitude,
				Longitude:           dbVehicle.Longitude,
				Bearing:             dbVehicle.Bearing,
				Odometer:            dbVehicle.Odometer,
				Speed:               dbVehicle.Speed,
				CongestionLevel:     dbVehicle.CongestionLevel,
				UpdatedAt:           dbVehicle.UpdatedAt,
				OccupancyStatus:     dbVehicle.OccupancyStatus,
				CurrentStatus:       dbVehicle.CurrentStatus,
				CurrentStopSequence: dbVehicle.CurrentStopSequence,
				OccupancyPercentage: dbVehicle.OccupancyPercentage,
			},
		})
	}

	return vehicles
}

func wantTrip(tripID, routeID string, directionID bool, sts []StopTime) *Trip {
	return &Trip{
		RouteID: routeID,
		DBFields: db.GetTripRow{
			ID:          tripID,
			DirectionID: convert.NullBool(&directionID),
		},
		StopTimes: sts,
	}
}

func wantVehicle(
	vehicleID string,
	systemID string,
	tripID, label, licensePlate *string,
	latitude, longitude, bearing *float32,
	odometer *float64,
	speed *float32,
	congestionLevel *gtfs.CongestionLevel,
	updatedAt *time.Time,
	currentStopSequence *int32,
	occupancyStatus *gtfs.OccupancyStatus,
	currentStatus *gtfs.CurrentStatus,
	currentStopID *string,
	occupancyPercentage *uint32) *Vehicle {
	return &Vehicle{
		SystemID:      systemID,
		TripID:        tripID,
		CurrentStopID: currentStopID,
		DBFields: db.GetVehicleRow{
			ID:                  convert.NullIfEmptyString(vehicleID),
			Label:               convert.NullString(label),
			LicensePlate:        convert.NullString(licensePlate),
			CurrentStatus:       convert.NullVehicleCurrentStatus(currentStatus),
			Latitude:            convert.Gps(latitude),
			Longitude:           convert.Gps(longitude),
			Bearing:             convert.NullFloat32(bearing),
			Odometer:            convert.NullFloat64(odometer),
			Speed:               convert.NullFloat32(speed),
			CongestionLevel:     convert.NullCongestionLevel(congestionLevel),
			UpdatedAt:           convert.NullTime(updatedAt),
			CurrentStopSequence: convert.NullInt32(currentStopSequence),
			OccupancyStatus:     convert.NullOccupancyStatus(occupancyStatus),
			OccupancyPercentage: convert.NullUInt32ToSigned(occupancyPercentage),
		},
	}
}

type StopTime struct {
	StopID   string
	DBFields db.ListStopsTimesForTripRow
}

func NewStopTimeFromDB(in db.ListStopsTimesForTripRow, stopPkToID map[int64]string) StopTime {
	stopID := stopPkToID[in.StopPk]
	// Clear all primary key columns
	in.Pk = 0
	in.TripPk = 0
	in.StopPk = 0
	in.StopID = ""
	in.StopName = pgtype.Text{}
	return StopTime{
		StopID:   stopID,
		DBFields: in,
	}
}

func wantSt(stopSequence uint32, stopID string, opts ...wantStOpt) StopTime {
	st := StopTime{
		StopID: stopID,
		DBFields: db.ListStopsTimesForTripRow{
			StopSequence: int32(stopSequence),
		},
	}
	for _, opt := range opts {
		opt(&st)
	}
	return st
}

type wantStOpt func(st *StopTime)

func wArrTime(i int) wantStOpt {
	t := mkTime(i)
	return func(st *StopTime) {
		st.DBFields.ArrivalTime = convert.NullTime(&t)
	}
}

func wDepTime(i int) wantStOpt {
	t := mkTime(i)
	return func(st *StopTime) {
		st.DBFields.DepartureTime = convert.NullTime(&t)
	}
}

func wPast(st *StopTime) {
	st.DBFields.Past = true
}

func gtfsStu(opts ...gtfsStuOpt) gtfs.StopTimeUpdate {
	stu := gtfs.StopTimeUpdate{
		Arrival:   &gtfs.StopTimeEvent{},
		Departure: &gtfs.StopTimeEvent{},
	}
	for _, opt := range opts {
		opt(&stu)
	}
	return stu
}

type gtfsStuOpt func(stu *gtfs.StopTimeUpdate)

func gStopID(stopID string) gtfsStuOpt {
	return func(stu *gtfs.StopTimeUpdate) {
		stu.StopID = &stopID
	}
}

/*
func gSeq(stopSequence uint32) gtfsStuOpt {
	return func(stu *gtfs.StopTimeUpdate) {
		stu.StopSequence = &stopSequence
	}
}
*/

func gArrTime(i int) gtfsStuOpt {
	t := mkTime(i)
	return func(stu *gtfs.StopTimeUpdate) {
		stu.Arrival.Time = &t
	}
}

func gDepTime(i int) gtfsStuOpt {
	t := mkTime(i)
	return func(stu *gtfs.StopTimeUpdate) {
		stu.Departure.Time = &t
	}
}

func gStopSeq(i uint32) gtfsStuOpt {
	return func(stu *gtfs.StopTimeUpdate) {
		stu.StopSequence = &i
	}
}

func mkTime(i int) time.Time {
	if i < 0 {
		return time.Time{}
	}
	return time.Date(2023, time.April, 22, 10, i, 0, 0, time.UTC)
}

func gtfsTrip(tripID, routeID string, directionID gtfs.DirectionID, stus []gtfs.StopTimeUpdate) *gtfs.Trip {
	return &gtfs.Trip{
		ID: gtfs.TripID{
			ID:          tripID1,
			RouteID:     routeID1,
			DirectionID: gtfs.DirectionID_True,
		},
		StopTimeUpdates: stus,
	}
}

func compareNumerics(x, y pgtype.Numeric) bool {
	if !x.Valid && !y.Valid {
		return true
	}

	if x.NaN && y.NaN {
		return true
	}

	if x.NaN != y.NaN {
		return false
	}

	if x.Valid != y.Valid {
		return false
	}

	if x.Int == nil && y.Int == nil {
		return x.Exp == y.Exp
	}

	if x.Int == nil || y.Int == nil {
		return false
	}

	if x.Int.Cmp(y.Int) != 0 {
		return false
	}

	return x.Exp == y.Exp
}
