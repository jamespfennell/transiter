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
	systemID             = "systemID1"
	feedID1              = "feedID1"
	feedID2              = "feedID2"
	routeID1             = "routeID1"
	stopID1              = "stopID1"
	stopID2              = "stopID2"
	stopID3              = "stopID3"
	stopID4              = "stopID4"
	tripID1              = "tripID1"
	vehicleID1           = "vehicleID1"
	vehicleID2           = "vehicleID2"
	defaultVehicleFeedID = "vehicles"
	scheduledService     = "weekdays"
	scheduledTripID1     = "scheduledTripID1"
	alertID1             = "alertID1"
)

// update represents a single update operations
type update struct {
	// feedID can be left blank, and it will default to feedID1.
	feedID string
	// the data to use in the update
	data *gtfs.Realtime
}

func TestUpdate(t *testing.T) {
	// Each test case performs one or more updates, and then the entities are verified.
	for _, tc := range []struct {
		name                string
		updates             []update
		wantTrips           []*Trip
		wantVehicles        []*Vehicle
		wantAlerts          []*Alert
		gtfsRealtimeOptions *api.GtfsRealtimeOptions
	}{
		{
			name: "basic trip case",
			updates: []update{
				{
					data: &gtfs.Realtime{
						Trips: []gtfs.Trip{
							*gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{
								gtfsStu(gStopID(stopID1), gDepTime(5)),
								gtfsStu(gStopID(stopID2), gArrTime(10), gDepTime(15)),
								gtfsStu(gStopID(stopID3), gArrTime(20), gDepTime(25)),
								gtfsStu(gStopID(stopID4), gArrTime(30)),
							}),
						},
					},
				},
			},
			wantTrips: []*Trip{
				wantTrip(tripID1, routeID1, true, []StopTime{
					wantSt(0, stopID1, wDepTime(5)),
					wantSt(1, stopID2, wArrTime(10), wDepTime(15)),
					wantSt(2, stopID3, wArrTime(20), wDepTime(25)),
					wantSt(3, stopID4, wArrTime(30)),
				}),
			},
		},
		{
			name: "trip deleted",
			updates: []update{
				{
					data: &gtfs.Realtime{
						Trips: []gtfs.Trip{
							*gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{
								gtfsStu(gStopID(stopID1), gDepTime(5)),
								gtfsStu(gStopID(stopID2), gArrTime(10), gDepTime(15)),
								gtfsStu(gStopID(stopID3), gArrTime(20), gDepTime(25)),
								gtfsStu(gStopID(stopID4), gArrTime(30)),
							}),
						},
					},
				},
				{
					data: &gtfs.Realtime{},
				},
			},
			wantTrips: []*Trip{},
		},
		{
			name: "same trip updated twice identically",
			updates: []update{
				{
					data: &gtfs.Realtime{
						Trips: []gtfs.Trip{
							*gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{
								gtfsStu(gStopID(stopID1), gDepTime(5)),
								gtfsStu(gStopID(stopID2), gArrTime(10), gDepTime(15)),
								gtfsStu(gStopID(stopID3), gArrTime(20), gDepTime(25)),
								gtfsStu(gStopID(stopID4), gArrTime(30)),
							}),
						},
					},
				},
				{
					data: &gtfs.Realtime{
						Trips: []gtfs.Trip{
							*gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{
								gtfsStu(gStopID(stopID1), gDepTime(5)),
								gtfsStu(gStopID(stopID2), gArrTime(10), gDepTime(15)),
								gtfsStu(gStopID(stopID3), gArrTime(20), gDepTime(25)),
								gtfsStu(gStopID(stopID4), gArrTime(30)),
							}),
						},
					},
				},
			},
			wantTrips: []*Trip{
				wantTrip(tripID1, routeID1, true, []StopTime{
					wantSt(0, stopID1, wDepTime(5)),
					wantSt(1, stopID2, wArrTime(10), wDepTime(15)),
					wantSt(2, stopID3, wArrTime(20), wDepTime(25)),
					wantSt(3, stopID4, wArrTime(30)),
				}),
			},
		},
		{
			name: "basic trip update case",
			updates: []update{
				{
					data: &gtfs.Realtime{
						Trips: []gtfs.Trip{
							*gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{
								gtfsStu(gStopID(stopID1), gDepTime(5)),
								gtfsStu(gStopID(stopID2), gArrTime(10), gDepTime(15)),
								gtfsStu(gStopID(stopID3), gArrTime(20), gDepTime(25)),
								gtfsStu(gStopID(stopID4), gArrTime(30)),
							}),
						},
					},
				},
				{
					data: &gtfs.Realtime{
						Trips: []gtfs.Trip{
							*gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{
								gtfsStu(gStopID(stopID1), gDepTime(5)),
								gtfsStu(gStopID(stopID2), gArrTime(11), gDepTime(16)),
								gtfsStu(gStopID(stopID3), gArrTime(20), gDepTime(25)),
								gtfsStu(gStopID(stopID4), gArrTime(31)),
							}),
						},
					},
				},
			},
			wantTrips: []*Trip{
				wantTrip(tripID1, routeID1, true, []StopTime{
					wantSt(0, stopID1, wDepTime(5)),
					wantSt(1, stopID2, wArrTime(11), wDepTime(16)),
					wantSt(2, stopID3, wArrTime(20), wDepTime(25)),
					wantSt(3, stopID4, wArrTime(31)),
				}),
			},
		},
		{
			name: "update with stops in the past",
			updates: []update{
				{
					data: &gtfs.Realtime{
						Trips: []gtfs.Trip{
							*gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{
								gtfsStu(gStopID(stopID1), gDepTime(5)),
								gtfsStu(gStopID(stopID2), gArrTime(10), gDepTime(15)),
								gtfsStu(gStopID(stopID3), gArrTime(20), gDepTime(25)),
								gtfsStu(gStopID(stopID4), gArrTime(30)),
							}),
						},
					},
				},
				{
					data: &gtfs.Realtime{
						Trips: []gtfs.Trip{
							*gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{
								gtfsStu(gStopID(stopID3), gArrTime(20), gDepTime(25)),
								gtfsStu(gStopID(stopID4), gArrTime(31)),
							}),
						},
					},
				},
			},
			wantTrips: []*Trip{
				wantTrip(tripID1, routeID1, true, []StopTime{
					wantSt(0, stopID1, wDepTime(5), wPast),
					wantSt(1, stopID2, wArrTime(10), wDepTime(15), wPast),
					wantSt(2, stopID3, wArrTime(20), wDepTime(25)),
					wantSt(3, stopID4, wArrTime(31)),
				}),
			},
		},
		{
			name: "reassign stop sequences",
			gtfsRealtimeOptions: &api.GtfsRealtimeOptions{
				ReassignStopSequences: true,
			},
			updates: []update{
				{
					data: &gtfs.Realtime{
						Trips: []gtfs.Trip{
							*gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{
								gtfsStu(gStopID(stopID1), gArrTime(5), gStopSeq(1)),
								gtfsStu(gStopID(stopID2), gArrTime(10), gStopSeq(2)),
								gtfsStu(gStopID(stopID3), gArrTime(20), gStopSeq(3)),
								gtfsStu(gStopID(stopID4), gArrTime(30), gStopSeq(4)),
							}),
						},
					},
				},
				{
					data: &gtfs.Realtime{
						Trips: []gtfs.Trip{
							*gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{
								gtfsStu(gStopID(stopID1), gArrTime(5), gStopSeq(2)),
								gtfsStu(gStopID(stopID2), gArrTime(10), gStopSeq(3)),
								gtfsStu(gStopID(stopID3), gArrTime(20), gStopSeq(4)),
								gtfsStu(gStopID(stopID4), gArrTime(30), gStopSeq(5)),
							}),
						},
					},
				},
			},
			wantTrips: []*Trip{
				wantTrip(tripID1, routeID1, true, []StopTime{
					wantSt(0, stopID1, wArrTime(5)),
					wantSt(1, stopID2, wArrTime(10)),
					wantSt(2, stopID3, wArrTime(20)),
					wantSt(3, stopID4, wArrTime(30)),
				}),
			},
		},
		{
			name: "no route in trip update",
			updates: []update{
				{
					data: &gtfs.Realtime{
						Trips: []gtfs.Trip{
							*gtfsTrip(tripID1, "", gtfs.DirectionID_True, []gtfs.StopTimeUpdate{}),
						},
					},
				},
			},
			wantTrips: []*Trip{},
		},
		{
			name: "no route in trip update, infer from static data",
			updates: []update{
				{
					data: &gtfs.Realtime{
						Trips: []gtfs.Trip{
							*gtfsTrip(scheduledTripID1, "", gtfs.DirectionID_True, []gtfs.StopTimeUpdate{}),
						},
					},
				},
			},
			wantTrips: []*Trip{
				wantTrip(scheduledTripID1, routeID1, true, nil),
			},
		},
		{
			name: "some trips with route id, some without",
			updates: []update{
				{
					data: &gtfs.Realtime{
						Trips: []gtfs.Trip{
							*gtfsTrip(scheduledTripID1, "", gtfs.DirectionID_True, []gtfs.StopTimeUpdate{}),
							*gtfsTrip(tripID1, routeID1, gtfs.DirectionID_False, []gtfs.StopTimeUpdate{}),
						},
					},
				},
			},
			wantTrips: []*Trip{
				wantTrip(scheduledTripID1, routeID1, true, nil),
				wantTrip(tripID1, routeID1, false, nil),
			},
		},
		{
			name: "simple vehicle case",
			updates: []update{
				{
					data: &gtfs.Realtime{
						Vehicles: []gtfs.Vehicle{
							*gtfsVehicle(vehicleID1, nil, nil, nil),
						},
					},
				},
			},
			wantVehicles: []*Vehicle{
				wantVehicle(vehicleID1, systemID, nil, nil, nil, nil, nil,
					nil, nil, nil, nil, nil, nil, nil, nil, nil, nil),
			},
		},
		{
			name: "vehicle with no id",
			updates: []update{
				{
					data: &gtfs.Realtime{
						Vehicles: []gtfs.Vehicle{
							{
								ID:                &gtfs.VehicleID{},
								IsEntityInMessage: true,
							},
						},
					},
				},
			},
			wantVehicles: []*Vehicle{},
		},
		{
			name: "vehicle lots of fields",
			updates: []update{
				{
					data: &gtfs.Realtime{
						Vehicles: []gtfs.Vehicle{
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
				},
			},
			wantVehicles: []*Vehicle{
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
		{
			name: "vehicle with associated trip",
			updates: []update{
				{
					data: &gtfs.Realtime{
						Trips: []gtfs.Trip{
							*gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{}),
						},
						Vehicles: []gtfs.Vehicle{
							*gtfsVehicle(vehicleID1, ptr(tripID1), nil, nil),
						},
					},
				},
			},
			wantTrips: []*Trip{
				wantTrip(tripID1, routeID1, true, nil, withVehicleID(vehicleID1)),
			},
			wantVehicles: []*Vehicle{
				wantVehicle(vehicleID1, systemID, ptr(tripID1),
					nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil),
			},
		},
		{
			name: "vehicles with duplicate trips in same update",
			updates: []update{
				{
					data: &gtfs.Realtime{
						Trips: []gtfs.Trip{
							*gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{}),
						},
						Vehicles: []gtfs.Vehicle{
							*gtfsVehicle(vehicleID1, ptr(tripID1), nil, nil),
							*gtfsVehicle(vehicleID2, ptr(tripID1), nil, nil),
						},
					},
				},
			},
			wantTrips: []*Trip{
				wantTrip(tripID1, routeID1, true, nil, withVehicleID(vehicleID1)),
			},
			wantVehicles: []*Vehicle{
				wantVehicle(vehicleID1, systemID, ptr(tripID1),
					nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil),
			},
		},
		{
			name: "vehicle trip changes vehicles across updates",
			updates: []update{
				{
					data: &gtfs.Realtime{
						Trips: []gtfs.Trip{
							*gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{}),
						},
						Vehicles: []gtfs.Vehicle{
							*gtfsVehicle(vehicleID1, ptr(tripID1), nil, nil),
						},
					},
				},
				{
					data: &gtfs.Realtime{
						Trips: []gtfs.Trip{
							*gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{}),
						},
						Vehicles: []gtfs.Vehicle{
							*gtfsVehicle(vehicleID2, ptr(tripID1), nil, nil),
						},
					},
				},
			},
			wantTrips: []*Trip{
				wantTrip(tripID1, routeID1, true, nil, withVehicleID(vehicleID2)),
			},
			wantVehicles: []*Vehicle{
				wantVehicle(vehicleID2, systemID, ptr(tripID1),
					nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil),
			},
		},
		{
			name: "vehicles with duplicate trips across different updates",
			updates: []update{
				{
					data: &gtfs.Realtime{
						Trips: []gtfs.Trip{
							*gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{}),
						},
						Vehicles: []gtfs.Vehicle{
							*gtfsVehicle(vehicleID1, ptr(tripID1), nil, nil),
						},
					},
				},
				{
					data: &gtfs.Realtime{
						Trips: []gtfs.Trip{
							*gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{}),
						},
						Vehicles: []gtfs.Vehicle{
							*gtfsVehicle(vehicleID1, ptr(tripID1), nil, nil),
							*gtfsVehicle(vehicleID2, ptr(tripID1), nil, nil),
						},
					},
				},
			},
			wantTrips: []*Trip{
				wantTrip(tripID1, routeID1, true, nil, withVehicleID(vehicleID1)),
			},
			wantVehicles: []*Vehicle{
				// If an existing vehicle and incoming vehicle both have same trip ID, we
				// keep the existing vehicle and ignore the incoming vehicle.
				wantVehicle(vehicleID1, systemID, ptr(tripID1),
					nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil),
			},
		},
		{
			name: "duplicate vehicle ids in same update",
			updates: []update{
				{
					data: &gtfs.Realtime{
						Vehicles: []gtfs.Vehicle{
							*gtfsVehicle(vehicleID1, nil, nil, nil),
							*gtfsVehicle(vehicleID1, nil, nil, nil),
						},
					},
				},
			},
			wantVehicles: []*Vehicle{
				wantVehicle(vehicleID1, systemID, nil,
					nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil),
			},
		},
		{
			name: "vehicle with associated trip and stop",
			updates: []update{
				{
					data: &gtfs.Realtime{
						Trips: []gtfs.Trip{
							*gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{
								gtfsStu(gStopID(stopID1), gDepTime(5)),
								gtfsStu(gStopID(stopID2), gArrTime(10), gDepTime(15)),
							}),
						},
						Vehicles: []gtfs.Vehicle{
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
				},
			},
			wantTrips: []*Trip{
				wantTrip(tripID1, routeID1, true, []StopTime{
					wantSt(0, stopID1, wDepTime(5)),
					wantSt(1, stopID2, wArrTime(10), wDepTime(15)),
				}, withVehicleID(vehicleID1)),
			},
			wantVehicles: []*Vehicle{
				wantVehicle(vehicleID1, systemID, ptr(tripID1),
					nil, nil, nil, nil, nil, nil, nil, nil, nil, ptr(int32(0)), nil, nil, ptr(stopID1), nil),
			},
		},
		{
			name: "vehicle update",
			updates: []update{
				{
					data: &gtfs.Realtime{
						Vehicles: []gtfs.Vehicle{
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
					},
				},
				{
					data: &gtfs.Realtime{
						Vehicles: []gtfs.Vehicle{
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
				},
			},
			wantVehicles: []*Vehicle{
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
		{
			name: "stale vehicle deleted",
			updates: []update{
				{
					data: &gtfs.Realtime{
						Vehicles: []gtfs.Vehicle{
							*gtfsVehicle(vehicleID1, nil, nil, nil),
							*gtfsVehicle(vehicleID2, nil, nil, nil),
						},
					},
				},
				{
					data: &gtfs.Realtime{
						Vehicles: []gtfs.Vehicle{
							*gtfsVehicle(vehicleID2, nil, nil, nil),
						},
					},
				},
			},
			wantVehicles: []*Vehicle{
				wantVehicle(vehicleID2, systemID, nil, nil, nil, nil, nil,
					nil, nil, nil, nil, nil, nil, nil, nil, nil, nil),
			},
		},
		{
			name: "vehicles from multiple feeds",
			updates: []update{
				{
					feedID: feedID1,
					data: &gtfs.Realtime{
						Vehicles: []gtfs.Vehicle{
							{
								ID: &gtfs.VehicleID{
									ID: vehicleID1,
								},
								IsEntityInMessage: true,
							},
						},
					},
				},
				{
					feedID: feedID2,
					data: &gtfs.Realtime{
						Vehicles: []gtfs.Vehicle{
							{
								ID: &gtfs.VehicleID{
									ID: vehicleID2,
								},
								IsEntityInMessage: true,
							},
						},
					},
				},
			},
			wantVehicles: []*Vehicle{
				wantVehicle(vehicleID1, systemID, nil, nil, nil, nil, nil,
					nil, nil, nil, nil, nil, nil, nil, nil, nil, nil),
				wantVehicle(vehicleID2, systemID, nil, nil, nil, nil, nil,
					nil, nil, nil, nil, nil, nil, nil, nil, nil, nil),
			},
		},
		{
			name: "same vehicle from different feeds",
			updates: []update{
				{
					feedID: feedID1,
					data: &gtfs.Realtime{
						Vehicles: []gtfs.Vehicle{
							{
								ID: &gtfs.VehicleID{
									ID: vehicleID1,
								},
								IsEntityInMessage: true,
							},
						},
					},
				},
				{
					feedID: feedID2,
					data: &gtfs.Realtime{
						Vehicles: []gtfs.Vehicle{
							{
								ID: &gtfs.VehicleID{
									ID: vehicleID1,
								},
								IsEntityInMessage: true,
							},
						},
					},
				},
			},
			wantVehicles: []*Vehicle{
				wantVehicle(vehicleID1, systemID, nil, nil, nil, nil, nil,
					nil, nil, nil, nil, nil, nil, nil, nil, nil, nil),
			},
		},
		{
			name: "same trip associated with different vehicles from different feeds",
			updates: []update{
				{
					feedID: feedID1,
					data: &gtfs.Realtime{
						Trips: []gtfs.Trip{
							*gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{}),
						},
						Vehicles: []gtfs.Vehicle{
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
				},
				{
					feedID: feedID2,
					data: &gtfs.Realtime{
						Vehicles: []gtfs.Vehicle{
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
				},
			},
			wantTrips: []*Trip{
				wantTrip(tripID1, routeID1, true, nil, withVehicleID(vehicleID2)),
			},
			wantVehicles: []*Vehicle{
				wantVehicle(vehicleID2, systemID, ptr(tripID1), nil, nil, nil, nil,
					nil, nil, nil, nil, nil, nil, nil, nil, nil, nil),
			},
		},
		{
			name: "simple alert",
			updates: []update{
				{
					data: &gtfs.Realtime{
						Alerts: []gtfs.Alert{
							*gtfsAlert(alertID1),
						},
					},
				},
			},
			wantAlerts: []*Alert{
				wantAlert(systemID, alertID1),
			},
		},
		{
			name: "alert with many fields",
			updates: []update{
				{
					data: &gtfs.Realtime{
						Alerts: []gtfs.Alert{
							{
								ID:     alertID1,
								Cause:  gtfs.Maintenance,
								Effect: gtfs.ModifiedService,
								ActivePeriods: []gtfs.AlertActivePeriod{
									{
										StartsAt: ptr(mkTime(1)),
										EndsAt:   ptr(mkTime(2)),
									},
									{
										StartsAt: ptr(mkTime(3)),
										EndsAt:   ptr(mkTime(4)),
									},
								},
								Header: []gtfs.AlertText{
									makeAlertText("Header 1", "en"),
									makeAlertText("Header 2", "jp"),
								},
								Description: []gtfs.AlertText{
									makeAlertText("Description 1", "en"),
									makeAlertText("Description 2", "jp"),
								},
								URL: []gtfs.AlertText{
									makeAlertText("Url 1", "en"),
									makeAlertText("Url 2", "jp"),
								},
							},
						},
					},
				},
			},
			wantAlerts: []*Alert{
				wantAlert(systemID, alertID1, wCause(gtfs.Maintenance), wEffect(gtfs.ModifiedService),
					wActivePeriods(t, mkTime(1), mkTime(2), mkTime(3), mkTime(4)),
					wHeaders(t, "Header 1", "en", "Header 2", "jp"),
					wDescriptions(t, "Description 1", "en", "Description 2", "jp"),
					wUrls(t, "Url 1", "en", "Url 2", "jp")),
			},
		},
		{
			name: "alert with informed agency",
			updates: []update{
				{
					data: &gtfs.Realtime{
						Alerts: []gtfs.Alert{
							{
								ID:     alertID1,
								Cause:  gtfs.UnknownCause,
								Effect: gtfs.UnknownEffect,
								InformedEntities: []gtfs.AlertInformedEntity{
									{
										AgencyID:  ptr("defaultAgency"),
										RouteType: gtfs.RouteType_Unknown,
									},
								},
							},
						},
					},
				},
			},
			wantAlerts: []*Alert{
				wantAlert(systemID, alertID1, wInformedAgencies("defaultAgency")),
			},
		},
		{
			name: "alert with informed route",
			updates: []update{
				{
					data: &gtfs.Realtime{
						Alerts: []gtfs.Alert{
							{
								ID:     alertID1,
								Cause:  gtfs.UnknownCause,
								Effect: gtfs.UnknownEffect,
								InformedEntities: []gtfs.AlertInformedEntity{
									{
										RouteID:   ptr(routeID1),
										RouteType: gtfs.RouteType_Unknown,
									},
								},
							},
						},
					},
				},
			},
			wantAlerts: []*Alert{
				wantAlert(systemID, alertID1, wInformedRoutes(routeID1)),
			},
		},
		{
			name: "alert with informed route type",
			updates: []update{
				{
					data: &gtfs.Realtime{
						Alerts: []gtfs.Alert{
							{
								ID:     alertID1,
								Cause:  gtfs.UnknownCause,
								Effect: gtfs.UnknownEffect,
								InformedEntities: []gtfs.AlertInformedEntity{
									{
										RouteType: gtfs.RouteType_Subway,
									},
									{
										RouteType: gtfs.RouteType_Bus,
									},
								},
							},
						},
					},
				},
			},
			wantAlerts: []*Alert{
				wantAlert(systemID, alertID1, wInformedRouteTypes("BUS", "SUBWAY")),
			},
		},
		{
			name: "alert with informed stops",
			updates: []update{
				{
					data: &gtfs.Realtime{
						Alerts: []gtfs.Alert{
							{
								ID:     alertID1,
								Cause:  gtfs.UnknownCause,
								Effect: gtfs.UnknownEffect,
								InformedEntities: []gtfs.AlertInformedEntity{
									{
										StopID:    ptr(stopID1),
										RouteType: gtfs.RouteType_Unknown,
									},
									{
										StopID:    ptr(stopID2),
										RouteType: gtfs.RouteType_Unknown,
									},
								},
							},
						},
					},
				},
			},
			wantAlerts: []*Alert{
				wantAlert(systemID, alertID1, wInformedStops(stopID1, stopID2)),
			},
		},
		{
			name: "alert with informed trip",
			updates: []update{
				{
					data: &gtfs.Realtime{
						Trips: []gtfs.Trip{
							*gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{}),
						},
						Alerts: []gtfs.Alert{
							{
								ID:     alertID1,
								Cause:  gtfs.UnknownCause,
								Effect: gtfs.UnknownEffect,
								InformedEntities: []gtfs.AlertInformedEntity{
									{
										TripID: &gtfs.TripID{
											ID: tripID1,
										},
										RouteType: gtfs.RouteType_Unknown,
									},
								},
							},
						},
					},
				},
			},
			wantTrips: []*Trip{
				wantTrip(tripID1, routeID1, true, nil),
			},
			wantAlerts: []*Alert{
				wantAlert(systemID, alertID1, wInformedTrips(tripID1)),
			},
		},
		{
			name: "alert with informed scheduled trip",
			updates: []update{
				{
					data: &gtfs.Realtime{
						Alerts: []gtfs.Alert{
							{
								ID:     alertID1,
								Cause:  gtfs.UnknownCause,
								Effect: gtfs.UnknownEffect,
								InformedEntities: []gtfs.AlertInformedEntity{
									{
										TripID: &gtfs.TripID{
											ID: scheduledTripID1,
										},
										RouteType: gtfs.RouteType_Unknown,
									},
								},
							},
						},
					},
				},
			},
			wantAlerts: []*Alert{
				wantAlert(systemID, alertID1, wInformedScheduledTrips(scheduledTripID1)),
			},
		},
		{
			name: "alert with informed trip and informed scheduled trip",
			updates: []update{
				{
					data: &gtfs.Realtime{
						Trips: []gtfs.Trip{
							*gtfsTrip(tripID1, routeID1, gtfs.DirectionID_True, []gtfs.StopTimeUpdate{}),
						},
						Alerts: []gtfs.Alert{
							{
								ID:     alertID1,
								Cause:  gtfs.UnknownCause,
								Effect: gtfs.UnknownEffect,
								InformedEntities: []gtfs.AlertInformedEntity{
									{
										TripID: &gtfs.TripID{
											ID: tripID1,
										},
										RouteType: gtfs.RouteType_Unknown,
									},
									{
										TripID: &gtfs.TripID{
											ID: scheduledTripID1,
										},
										RouteType: gtfs.RouteType_Unknown,
									},
								},
							},
						},
					},
				},
			},
			wantTrips: []*Trip{
				wantTrip(tripID1, routeID1, true, nil),
			},
			wantAlerts: []*Alert{
				wantAlert(systemID, alertID1, wInformedTrips(tripID1), wInformedScheduledTrips(scheduledTripID1)),
			},
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			querier := dbtesting.NewQuerier(t)
			system := querier.NewSystem(systemID)
			systemPkToID := map[int64]string{}
			systemPkToID[system.Data.Pk] = systemID

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
			feed1 := system.NewFeed(feedID1)
			feed2 := system.NewFeed(feedID2)
			staticFeed := system.NewFeed("static")

			// Static data
			system.NewScheduledService(scheduledService, db.InsertScheduledServiceParams{
				FeedPk:    staticFeed.Data.Pk,
				Monday:    convert.Bool(true),
				Tuesday:   convert.Bool(true),
				Wednesday: convert.Bool(true),
				Thursday:  convert.Bool(true),
				Friday:    convert.Bool(true),
			})
			system.NewScheduledTrip(scheduledTripID1, scheduledService, routeID1)

			ctx := context.Background()

			for i, update := range tc.updates {
				var feedPk int64
				switch update.feedID {
				case "":
					fallthrough
				case feedID1:
					feedPk = feed1.Data.Pk
				case feedID2:
					feedPk = feed2.Data.Pk
				default:
					t.Fatalf("unknown feed ID %q", update.feedID)
				}
				updateCtx := common.UpdateContext{
					Querier:  querier,
					SystemPk: system.Data.Pk,
					FeedPk:   feedPk,
					FeedConfig: &api.FeedConfig{
						GtfsRealtimeOptions: tc.gtfsRealtimeOptions,
					},
					Logger: slog.Default(),
				}
				err := Update(ctx, updateCtx, update.data)
				if err != nil {
					t.Fatalf("Update(trip update version %d) got = %v, want = <nil>", err, i)
				}
			}

			if tc.wantTrips == nil {
				tc.wantTrips = []*Trip{}
			}
			gotTrips := readTripsFromDB(ctx, t, querier, system.Data.Pk, routePkToID, stopPkToID)
			if diff := cmp.Diff(gotTrips, tc.wantTrips); diff != "" {
				t.Errorf("got = %v, want = %v, diff = %s", gotTrips, tc.wantTrips, diff)
			}

			if tc.wantVehicles == nil {
				tc.wantVehicles = []*Vehicle{}
			}
			gotVehicles := readVehiclesFromDB(ctx, t, querier, system.Data.Pk, systemPkToID)
			opt := cmp.Options{
				cmpopts.IgnoreUnexported(pgtype.Numeric{}),
				cmp.Comparer(compareNumerics),
			}
			if diff := cmp.Diff(gotVehicles, tc.wantVehicles, opt); diff != "" {
				t.Errorf("got = %v, want = %v, diff = %s", gotVehicles, tc.wantVehicles, diff)
			}

			if tc.wantAlerts == nil {
				tc.wantAlerts = []*Alert{}
			}
			gotAlerts := readAlertsFromDB(ctx, t, querier, system.Data.Pk, systemPkToID)
			if diff := cmp.Diff(gotAlerts, tc.wantAlerts); diff != "" {
				t.Errorf("got = %v, want = %v, diff = %s", gotAlerts, tc.wantAlerts, diff)
			}
		})
	}
}

type Trip struct {
	RouteID   string
	DBFields  db.ListTripsRow
	StopTimes []StopTime
}

type Vehicle struct {
	SystemID      string
	TripID        *string
	CurrentStopID *string
	DBFields      db.GetVehicleRow
}

type Alert struct {
	SystemID string
	DBFields db.ListAlertsWithActivePeriodsAndAllInformedEntitiesRow
}

func readTripsFromDB(ctx context.Context, t *testing.T, querier db.Querier, systemPk int64, routePkToID map[int64]string, stopPkToID map[int64]string) []*Trip {
	routePks := common.MapKeys(routePkToID)
	dbTrips, err := querier.ListTrips(ctx, db.ListTripsParams{
		SystemPk: systemPk,
		RoutePks: routePks,
	})
	if err != nil {
		t.Fatalf("ListTrips(systemPk=%d, routePks=%v) err got = %v, want = <nil>", systemPk, routePks, err)
	}

	trips := []*Trip{}
	for _, dbTrip := range dbTrips {
		dbStopTimes, err := querier.ListStopsTimesForTrip(ctx, dbTrip.Pk)
		routeID := routePkToID[dbTrip.RoutePk]
		if err != nil {
			t.Fatalf("ListStopTimesForTrip(routeID=%s, tripID=%s) err got = %v, want = <nil>", routeID, dbTrip.ID, err)
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

		trips = append(trips, &Trip{
			RouteID:   routeID,
			DBFields:  dbTrip,
			StopTimes: outStopTimes,
		})
	}

	return trips
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

func readAlertsFromDB(
	ctx context.Context,
	t *testing.T, querier db.Querier,
	systemPk int64,
	systemPkToID map[int64]string) []*Alert {

	dbAlerts, err := querier.ListAlertsWithActivePeriodsAndAllInformedEntities(ctx, systemPk)
	if err != nil {
		t.Fatalf("ListAlertsWithActivePeriodsAndInformedEntitiesInSystem(systemPk=%d) err got = %v, want = <nil>", systemPk, err)
	}

	alerts := make([]*Alert, 0, len(dbAlerts))
	systemID, ok := systemPkToID[systemPk]
	if !ok {
		t.Fatalf("systemPkToID[%d] not found", systemPk)
	}

	for _, dbAlert := range dbAlerts {
		alerts = append(alerts, &Alert{
			SystemID: systemID,
			DBFields: dbAlert,
		})
	}

	return alerts
}

type wantTripOpt func(*Trip)

func wantTrip(tripID, routeID string, directionID bool, sts []StopTime, opts ...wantTripOpt) *Trip {
	t := &Trip{
		RouteID: routeID,
		DBFields: db.ListTripsRow{
			ID:          tripID,
			DirectionID: convert.NullBool(&directionID),
		},
		StopTimes: sts,
	}
	for _, opt := range opts {
		opt(t)
	}
	return t
}

func withVehicleID(vehicleID string) wantTripOpt {
	return func(t *Trip) {
		t.DBFields.VehicleID = convert.NullString(&vehicleID)
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

type wantAlertOpt func(*Alert)

func wCause(cause gtfs.AlertCause) wantAlertOpt {
	return func(a *Alert) {
		a.DBFields.Cause = cause.String()
	}
}

func wEffect(effect gtfs.AlertEffect) wantAlertOpt {
	return func(a *Alert) {
		a.DBFields.Effect = effect.String()
	}
}

func wActivePeriods(tc *testing.T, times ...time.Time) wantAlertOpt {
	if len(times)%2 != 0 {
		tc.Fatalf("wActivePeriods: len(times) = %d, want even", len(times))
	}
	var activePeriods []pgtype.Range[pgtype.Timestamptz]
	for i := 0; i < len(times); i += 2 {
		activePeriods = append(activePeriods, pgtype.Range[pgtype.Timestamptz]{
			Lower:     convert.NullTime(&times[i]),
			Upper:     convert.NullTime(&times[i+1]),
			LowerType: pgtype.Inclusive,
			UpperType: pgtype.Exclusive,
			Valid:     true,
		})
	}
	return func(a *Alert) {
		a.DBFields.ActivePeriods = activePeriods
	}
}

func wHeaders(t *testing.T, textAndLangs ...string) wantAlertOpt {
	return func(a *Alert) {
		a.DBFields.Header = convertAlertText(convertTextLangPairsToAlertText(t, textAndLangs...))
	}
}

func wDescriptions(t *testing.T, textAndLangs ...string) wantAlertOpt {
	return func(a *Alert) {
		a.DBFields.Description = convertAlertText(convertTextLangPairsToAlertText(t, textAndLangs...))
	}
}

func wUrls(t *testing.T, textAndLangs ...string) wantAlertOpt {
	return func(a *Alert) {
		a.DBFields.Url = convertAlertText(convertTextLangPairsToAlertText(t, textAndLangs...))
	}
}

func convertTextLangPairsToAlertText(t *testing.T, textAndLangs ...string) []gtfs.AlertText {
	if len(textAndLangs)%2 != 0 {
		t.Fatalf("convertTextLangPairsToAlertText: len(textAndLangs) = %d, want even", len(textAndLangs))
	}
	var headers []gtfs.AlertText
	for i := 0; i < len(textAndLangs); i += 2 {
		headers = append(headers, makeAlertText(textAndLangs[i], textAndLangs[i+1]))
	}
	return headers
}

func wInformedAgencies(agencyIDs ...string) wantAlertOpt {
	return func(a *Alert) {
		a.DBFields.Agencies = agencyIDs
	}
}

func wInformedRoutes(routeIDs ...string) wantAlertOpt {
	return func(a *Alert) {
		a.DBFields.Routes = routeIDs
	}
}

func wInformedRouteTypes(routeTypes ...string) wantAlertOpt {
	return func(a *Alert) {
		a.DBFields.RouteTypes = routeTypes
	}
}

func wInformedStops(stopIDs ...string) wantAlertOpt {
	return func(a *Alert) {
		a.DBFields.Stops = stopIDs
	}
}

func wInformedTrips(tripIDs ...string) wantAlertOpt {
	return func(a *Alert) {
		a.DBFields.Trips = tripIDs
	}
}

func wInformedScheduledTrips(tripIDs ...string) wantAlertOpt {
	return func(a *Alert) {
		a.DBFields.ScheduledTrips = tripIDs
	}
}

func wantAlert(systemID string, alertID string, opts ...wantAlertOpt) *Alert {
	a := &Alert{
		SystemID: systemID,
		DBFields: db.ListAlertsWithActivePeriodsAndAllInformedEntitiesRow{
			ID:             alertID,
			Cause:          "UNKNOWN_CAUSE",
			Effect:         "UNKNOWN_EFFECT",
			Header:         "null",
			Description:    "null",
			Url:            "null",
			ActivePeriods:  []pgtype.Range[pgtype.Timestamptz]{},
			Agencies:       []string{},
			Routes:         []string{},
			RouteTypes:     []string{},
			Stops:          []string{},
			Trips:          []string{},
			ScheduledTrips: []string{},
		},
	}
	for _, opt := range opts {
		opt(a)
	}
	return a
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
			ID:          tripID,
			RouteID:     routeID,
			DirectionID: directionID,
		},
		StopTimeUpdates:   stus,
		IsEntityInMessage: true,
	}
}

func gtfsVehicle(vehicleID string, tripID *string, latitude, longitude *float32) *gtfs.Vehicle {
	vehicle := &gtfs.Vehicle{
		ID: &gtfs.VehicleID{
			ID: vehicleID,
		},
		IsEntityInMessage: true,
	}
	if tripID != nil {
		vehicle.Trip = &gtfs.Trip{
			ID: gtfs.TripID{
				ID: *tripID,
			},
		}
	}
	if latitude != nil && longitude != nil {
		vehicle.Position = &gtfs.Position{
			Latitude:  latitude,
			Longitude: longitude,
		}
	}
	return vehicle
}

func gtfsAlert(alertID string) *gtfs.Alert {
	return &gtfs.Alert{
		ID:     alertID,
		Cause:  gtfs.UnknownCause,
		Effect: gtfs.UnknownEffect,
	}
}

func makeAlertText(text string, language string) gtfs.AlertText {
	return gtfs.AlertText{
		Language: language,
		Text:     text,
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
