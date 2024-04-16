package static

import (
	"context"
	"math"
	"math/big"
	"testing"
	"time"

	"github.com/google/go-cmp/cmp"
	"github.com/google/go-cmp/cmp/cmpopts"
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
	routeID1 = "routeID1"
	stopID1  = "stopID1"
	stopID2  = "stopID2"
)

var (
	may4 = time.Date(2022, 5, 4, 0, 0, 0, 0, time.UTC)
	may7 = time.Date(2022, 5, 7, 0, 0, 0, 0, time.UTC)
)

func TestUpdate(t *testing.T) {
	defaultAgency := gtfs.Agency{
		Id:       "a",
		Name:     "b",
		Url:      "c",
		Timezone: "d",
	}
	defaultRoute := gtfs.Route{
		Id:        "route_id",
		Agency:    &defaultAgency,
		Color:     "FFFFFF",
		TextColor: "000000",
		Type:      gtfs.RouteType_Bus,
	}
	defaultStop := gtfs.Stop{
		Id: "stop_id",
	}
	defaultService := gtfs.Service{
		Id:        "service_id",
		StartDate: may4,
		EndDate:   may7,
	}
	defaultTrip := gtfs.ScheduledTrip{
		ID:      "trip_id",
		Route:   &defaultRoute,
		Service: &defaultService,
	}
	defaultShape := gtfs.Shape{
		ID: "shape_id",
		Points: []gtfs.ShapePoint{
			{
				Latitude:  1.1,
				Longitude: 2.2,
			},
			{
				Latitude:  3.3,
				Longitude: 4.4,
				Distance:  ptr(1.1),
			},
		},
	}
	for _, tc := range []struct {
		name                 string
		updates              []*gtfs.Static
		wantStops            []db.Stop
		wantStopIDToParentID map[string]string
		wantServices         []db.ListScheduledServicesRow
		wantTrips            []db.ListScheduledTripsRow
		wantTripStopTimes    []db.ListScheduledTripStopTimesRow
		wantTripFrequencies  []db.ListScheduledTripFrequenciesRow
		wantTripShapes       []shapeAndTripID
		onlyCheckTrips       bool
	}{
		{
			name: "stop added",
			updates: []*gtfs.Static{
				{
					Stops: []gtfs.Stop{
						{
							Id:                 stopID1,
							Code:               "1",
							Name:               "2",
							Description:        "3",
							ZoneId:             "4",
							Longitude:          ptr(float64(5.5)),
							Latitude:           ptr(float64(6.6)),
							Url:                "7",
							Type:               gtfs.StopType_Station,
							Timezone:           "8",
							WheelchairBoarding: gtfs.WheelchairBoarding_NotPossible,
							PlatformCode:       "9",
						},
					},
				},
			},
			wantStops: []db.Stop{
				{
					ID:                 stopID1,
					Code:               dbString("1"),
					Name:               dbString("2"),
					Description:        dbString("3"),
					ZoneID:             dbString("4"),
					Longitude:          convert.Gps(ptr(float64(5.5))),
					Latitude:           convert.Gps(ptr(float64(6.6))),
					Url:                dbString("7"),
					Type:               gtfs.StopType_Station.String(),
					Timezone:           dbString("8"),
					WheelchairBoarding: pgtype.Bool{Valid: true, Bool: false},
					PlatformCode:       dbString("9"),
				},
			},
		},
		{
			name: "stop deleted",
			updates: []*gtfs.Static{
				{
					Stops: []gtfs.Stop{
						{
							Id:   stopID1,
							Type: gtfs.StopType_Station,
						},
					},
				},
				{},
			},
			wantStops: nil,
		},
		{
			name: "stop parent and child",
			updates: []*gtfs.Static{
				{
					Stops: []gtfs.Stop{
						{
							Id:   stopID1,
							Type: gtfs.StopType_Station,
						},
						{
							Id:     stopID2,
							Type:   gtfs.StopType_Platform,
							Parent: &gtfs.Stop{Id: stopID1},
						},
					},
				},
			},
			wantStops: []db.Stop{
				{
					ID:   stopID1,
					Type: gtfs.StopType_Station.String(),
				},
				{
					ID:   stopID2,
					Type: gtfs.StopType_Platform.String(),
				},
			},
			wantStopIDToParentID: map[string]string{
				stopID2: stopID1,
			},
		},
		{
			name: "stop parent deleted",
			updates: []*gtfs.Static{
				{
					Stops: []gtfs.Stop{
						{
							Id:   stopID1,
							Type: gtfs.StopType_Station,
						},
						{
							Id:     stopID2,
							Type:   gtfs.StopType_Platform,
							Parent: &gtfs.Stop{Id: stopID1},
						},
					},
				},
				{
					Stops: []gtfs.Stop{
						{
							Id:   stopID2,
							Type: gtfs.StopType_Platform,
						},
					},
				},
			},
			wantStops: []db.Stop{
				{
					ID:   stopID2,
					Type: gtfs.StopType_Platform.String(),
				},
			},
		},
		{
			name: "service with default values",
			updates: []*gtfs.Static{
				{
					Services: []gtfs.Service{
						{
							Id: "serviceID1",
						},
					},
				},
			},
			wantServices: []db.ListScheduledServicesRow{
				{
					ID:        "serviceID1",
					Monday:    convert.Bool(false),
					Tuesday:   convert.Bool(false),
					Wednesday: convert.Bool(false),
					Thursday:  convert.Bool(false),
					Friday:    convert.Bool(false),
					Saturday:  convert.Bool(false),
					Sunday:    convert.Bool(false),
					StartDate: convert.Date(time.Date(0001, 1, 1, 0, 0, 0, 0, time.UTC)),
					EndDate:   convert.Date(time.Date(0001, 1, 1, 0, 0, 0, 0, time.UTC)),
				},
			},
		},
		{
			name: "service all days",
			updates: []*gtfs.Static{
				{
					Services: []gtfs.Service{
						{
							Id:        "serviceID1",
							Monday:    true,
							Tuesday:   true,
							Wednesday: true,
							Thursday:  true,
							Friday:    true,
							Saturday:  true,
							Sunday:    true,
							StartDate: time.Date(2020, 1, 1, 0, 0, 0, 0, time.UTC),
							EndDate:   time.Date(2020, 1, 2, 0, 0, 0, 0, time.UTC),
						},
					},
				},
			},
			wantServices: []db.ListScheduledServicesRow{
				{
					ID:        "serviceID1",
					Monday:    convert.Bool(true),
					Tuesday:   convert.Bool(true),
					Wednesday: convert.Bool(true),
					Thursday:  convert.Bool(true),
					Friday:    convert.Bool(true),
					Saturday:  convert.Bool(true),
					Sunday:    convert.Bool(true),
					StartDate: convert.Date(time.Date(2020, 1, 1, 0, 0, 0, 0, time.UTC)),
					EndDate:   convert.Date(time.Date(2020, 1, 2, 0, 0, 0, 0, time.UTC)),
				},
			},
		},
		{
			name: "stale service deleted",
			updates: []*gtfs.Static{
				{
					Services: []gtfs.Service{
						{
							Id:        "serviceID1",
							Monday:    true,
							Tuesday:   false,
							Wednesday: true,
							Thursday:  false,
							Friday:    true,
							Saturday:  false,
							Sunday:    true,
							StartDate: time.Date(2020, 1, 1, 0, 0, 0, 0, time.UTC),
							EndDate:   time.Date(2020, 1, 2, 0, 0, 0, 0, time.UTC),
						},
					},
				},
				{
					Services: []gtfs.Service{
						{
							Id:        "serviceID2",
							Monday:    false,
							Tuesday:   true,
							Wednesday: false,
							Thursday:  true,
							Friday:    false,
							Saturday:  true,
							Sunday:    false,
							StartDate: time.Date(2020, 2, 1, 0, 0, 0, 0, time.UTC),
							EndDate:   time.Date(2020, 3, 2, 0, 0, 0, 0, time.UTC),
						},
					},
				},
			},
			wantServices: []db.ListScheduledServicesRow{
				{
					ID:        "serviceID2",
					Monday:    convert.Bool(false),
					Tuesday:   convert.Bool(true),
					Wednesday: convert.Bool(false),
					Thursday:  convert.Bool(true),
					Friday:    convert.Bool(false),
					Saturday:  convert.Bool(true),
					Sunday:    convert.Bool(false),
					StartDate: convert.Date(time.Date(2020, 2, 1, 0, 0, 0, 0, time.UTC)),
					EndDate:   convert.Date(time.Date(2020, 3, 2, 0, 0, 0, 0, time.UTC)),
				},
			},
		},
		{
			name: "service update",
			updates: []*gtfs.Static{
				{
					Services: []gtfs.Service{
						{
							Id:        "serviceID1",
							Monday:    true,
							Tuesday:   false,
							Wednesday: true,
							Thursday:  false,
							Friday:    true,
							Saturday:  false,
							Sunday:    true,
							StartDate: time.Date(2020, 1, 1, 0, 0, 0, 0, time.UTC),
							EndDate:   time.Date(2020, 1, 2, 0, 0, 0, 0, time.UTC),
						},
					},
				},
				{
					Services: []gtfs.Service{
						{
							Id:        "serviceID1",
							Monday:    false,
							Tuesday:   true,
							Wednesday: false,
							Thursday:  true,
							Friday:    false,
							Saturday:  true,
							Sunday:    false,
							StartDate: time.Date(2020, 2, 1, 0, 0, 0, 0, time.UTC),
							EndDate:   time.Date(2020, 3, 2, 0, 0, 0, 0, time.UTC),
						},
					},
				},
			},
			wantServices: []db.ListScheduledServicesRow{
				{
					ID:        "serviceID1",
					Monday:    convert.Bool(false),
					Tuesday:   convert.Bool(true),
					Wednesday: convert.Bool(false),
					Thursday:  convert.Bool(true),
					Friday:    convert.Bool(false),
					Saturday:  convert.Bool(true),
					Sunday:    convert.Bool(false),
					StartDate: convert.Date(time.Date(2020, 2, 1, 0, 0, 0, 0, time.UTC)),
					EndDate:   convert.Date(time.Date(2020, 3, 2, 0, 0, 0, 0, time.UTC)),
				},
			},
		},
		{
			name: "service additions and removals",
			updates: []*gtfs.Static{
				{
					Services: []gtfs.Service{
						{
							Id:        "serviceID1",
							Monday:    true,
							StartDate: time.Date(2020, 1, 1, 0, 0, 0, 0, time.UTC),
							EndDate:   time.Date(2020, 12, 31, 0, 0, 0, 0, time.UTC),
							AddedDates: []time.Time{
								time.Date(2021, 1, 3, 0, 0, 0, 0, time.UTC),
								time.Date(2021, 1, 4, 0, 0, 0, 0, time.UTC),
							},
							RemovedDates: []time.Time{
								time.Date(2020, 4, 1, 0, 0, 0, 0, time.UTC),
								time.Date(2020, 5, 1, 0, 0, 0, 0, time.UTC),
							},
						},
					},
				},
			},
			wantServices: []db.ListScheduledServicesRow{
				{
					ID:        "serviceID1",
					Monday:    convert.Bool(true),
					Tuesday:   convert.Bool(false),
					Wednesday: convert.Bool(false),
					Thursday:  convert.Bool(false),
					Friday:    convert.Bool(false),
					Saturday:  convert.Bool(false),
					Sunday:    convert.Bool(false),
					StartDate: convert.Date(time.Date(2020, 1, 1, 0, 0, 0, 0, time.UTC)),
					EndDate:   convert.Date(time.Date(2020, 12, 31, 0, 0, 0, 0, time.UTC)),
					Additions: []pgtype.Date{
						convert.Date(time.Date(2021, 1, 3, 0, 0, 0, 0, time.UTC)),
						convert.Date(time.Date(2021, 1, 4, 0, 0, 0, 0, time.UTC)),
					},
					Removals: []pgtype.Date{
						convert.Date(time.Date(2020, 4, 1, 0, 0, 0, 0, time.UTC)),
						convert.Date(time.Date(2020, 5, 1, 0, 0, 0, 0, time.UTC)),
					},
				},
			},
		},
		{
			name: "service additions and removals updates",
			updates: []*gtfs.Static{
				{
					Services: []gtfs.Service{
						{
							Id:        "serviceID1",
							Monday:    true,
							StartDate: time.Date(2020, 1, 1, 0, 0, 0, 0, time.UTC),
							EndDate:   time.Date(2020, 12, 31, 0, 0, 0, 0, time.UTC),
							AddedDates: []time.Time{
								time.Date(2021, 1, 3, 0, 0, 0, 0, time.UTC),
								time.Date(2021, 1, 4, 0, 0, 0, 0, time.UTC),
							},
							RemovedDates: []time.Time{
								time.Date(2020, 4, 1, 0, 0, 0, 0, time.UTC),
								time.Date(2020, 5, 1, 0, 0, 0, 0, time.UTC),
							},
						},
					},
				},
				{
					Services: []gtfs.Service{
						{
							Id:        "serviceID1",
							Monday:    true,
							StartDate: time.Date(2020, 1, 1, 0, 0, 0, 0, time.UTC),
							EndDate:   time.Date(2020, 12, 31, 0, 0, 0, 0, time.UTC),
							AddedDates: []time.Time{
								time.Date(2021, 2, 3, 0, 0, 0, 0, time.UTC),
								time.Date(2021, 3, 4, 0, 0, 0, 0, time.UTC),
							},
							RemovedDates: []time.Time{
								time.Date(2020, 5, 1, 0, 0, 0, 0, time.UTC),
								time.Date(2020, 6, 1, 0, 0, 0, 0, time.UTC),
							},
						},
					},
				},
			},
			wantServices: []db.ListScheduledServicesRow{
				{
					ID:        "serviceID1",
					Monday:    convert.Bool(true),
					Tuesday:   convert.Bool(false),
					Wednesday: convert.Bool(false),
					Thursday:  convert.Bool(false),
					Friday:    convert.Bool(false),
					Saturday:  convert.Bool(false),
					Sunday:    convert.Bool(false),
					StartDate: convert.Date(time.Date(2020, 1, 1, 0, 0, 0, 0, time.UTC)),
					EndDate:   convert.Date(time.Date(2020, 12, 31, 0, 0, 0, 0, time.UTC)),
					Additions: []pgtype.Date{
						convert.Date(time.Date(2021, 2, 3, 0, 0, 0, 0, time.UTC)),
						convert.Date(time.Date(2021, 3, 4, 0, 0, 0, 0, time.UTC)),
					},
					Removals: []pgtype.Date{
						convert.Date(time.Date(2020, 5, 1, 0, 0, 0, 0, time.UTC)),
						convert.Date(time.Date(2020, 6, 1, 0, 0, 0, 0, time.UTC)),
					},
				},
			},
		},
		{
			name: "delete stale service additions and removals",
			updates: []*gtfs.Static{
				{
					Services: []gtfs.Service{
						{
							Id:        "serviceID1",
							Monday:    true,
							StartDate: time.Date(2020, 1, 1, 0, 0, 0, 0, time.UTC),
							EndDate:   time.Date(2020, 12, 31, 0, 0, 0, 0, time.UTC),
							AddedDates: []time.Time{
								time.Date(2021, 1, 3, 0, 0, 0, 0, time.UTC),
								time.Date(2021, 1, 4, 0, 0, 0, 0, time.UTC),
							},
							RemovedDates: []time.Time{
								time.Date(2020, 4, 1, 0, 0, 0, 0, time.UTC),
								time.Date(2020, 5, 1, 0, 0, 0, 0, time.UTC),
							},
						},
					},
				},
				{
					Services: []gtfs.Service{
						{
							Id:        "serviceID1",
							Monday:    true,
							StartDate: time.Date(2020, 1, 1, 0, 0, 0, 0, time.UTC),
							EndDate:   time.Date(2020, 12, 31, 0, 0, 0, 0, time.UTC),
							AddedDates: []time.Time{
								time.Date(2021, 1, 3, 0, 0, 0, 0, time.UTC),
							},
							RemovedDates: []time.Time{
								time.Date(2020, 4, 1, 0, 0, 0, 0, time.UTC),
							},
						},
					},
				},
			},
			wantServices: []db.ListScheduledServicesRow{
				{
					ID:        "serviceID1",
					Monday:    convert.Bool(true),
					Tuesday:   convert.Bool(false),
					Wednesday: convert.Bool(false),
					Thursday:  convert.Bool(false),
					Friday:    convert.Bool(false),
					Saturday:  convert.Bool(false),
					Sunday:    convert.Bool(false),
					StartDate: convert.Date(time.Date(2020, 1, 1, 0, 0, 0, 0, time.UTC)),
					EndDate:   convert.Date(time.Date(2020, 12, 31, 0, 0, 0, 0, time.UTC)),
					Additions: []pgtype.Date{
						convert.Date(time.Date(2021, 1, 3, 0, 0, 0, 0, time.UTC)),
					},
					Removals: []pgtype.Date{
						convert.Date(time.Date(2020, 4, 1, 0, 0, 0, 0, time.UTC)),
					},
				},
			},
		},
		{
			name: "empty trips",
			updates: []*gtfs.Static{
				{
					Agencies: []gtfs.Agency{defaultAgency},
					Routes:   []gtfs.Route{defaultRoute},
					Services: []gtfs.Service{defaultService},
					Trips:    []gtfs.ScheduledTrip{},
				},
			},
			wantTrips:      nil,
			onlyCheckTrips: true,
		},
		{
			name: "simple trip",
			updates: []*gtfs.Static{
				{
					Agencies: []gtfs.Agency{defaultAgency},
					Routes:   []gtfs.Route{defaultRoute},
					Services: []gtfs.Service{defaultService},
					Trips:    []gtfs.ScheduledTrip{defaultTrip},
				},
			},
			wantTrips: []db.ListScheduledTripsRow{
				{
					ID:        "trip_id",
					ServiceID: "service_id",
					RouteID:   "route_id",
				},
			},
			onlyCheckTrips: true,
		},
		{
			name: "all fields",
			updates: []*gtfs.Static{
				{
					Agencies: []gtfs.Agency{defaultAgency},
					Routes:   []gtfs.Route{defaultRoute},
					Services: []gtfs.Service{defaultService},
					Trips: []gtfs.ScheduledTrip{
						{
							ID:                   "trip_id",
							Service:              &defaultService,
							Route:                &defaultRoute,
							Headsign:             "Times Square",
							ShortName:            "short name",
							DirectionId:          gtfs.DirectionID_True,
							WheelchairAccessible: gtfs.WheelchairBoarding_Possible,
							BikesAllowed:         gtfs.BikesAllowed_Allowed,
						},
					},
				},
			},
			wantTrips: []db.ListScheduledTripsRow{
				{
					ID:                   "trip_id",
					ServiceID:            "service_id",
					RouteID:              "route_id",
					Headsign:             convert.NullIfEmptyString("Times Square"),
					ShortName:            convert.NullIfEmptyString("short name"),
					DirectionID:          convert.Bool(true),
					WheelchairAccessible: convert.Bool(true),
					BikesAllowed:         convert.Bool(true),
				},
			},
			onlyCheckTrips: true,
		},
		{
			name: "trip stop times",
			updates: []*gtfs.Static{
				{
					Agencies: []gtfs.Agency{defaultAgency},
					Routes:   []gtfs.Route{defaultRoute},
					Services: []gtfs.Service{defaultService},
					Stops:    []gtfs.Stop{defaultStop, {Id: "stop_id_2"}},
					Trips: []gtfs.ScheduledTrip{
						{
							ID:      "trip_id",
							Route:   &defaultRoute,
							Service: &defaultService,
							StopTimes: []gtfs.ScheduledStopTime{
								{
									Trip:              &defaultTrip,
									Stop:              &defaultStop,
									ArrivalTime:       1 * time.Hour,
									DepartureTime:     2 * time.Hour,
									StopSequence:      42,
									Headsign:          "Times Square",
									ContinuousPickup:  gtfs.PickupDropOffPolicy_No,
									ContinuousDropOff: gtfs.PickupDropOffPolicy_PhoneAgency,
								},
								{
									Trip:                  &defaultTrip,
									Stop:                  &gtfs.Stop{Id: "stop_id_2"},
									ArrivalTime:           2 * time.Hour,
									DepartureTime:         3 * time.Hour,
									StopSequence:          43,
									Headsign:              "Times Square",
									ShapeDistanceTraveled: ptr(42.0),
								},
							},
						},
					},
				},
			},
			wantTrips: []db.ListScheduledTripsRow{
				{
					ID:        "trip_id",
					ServiceID: "service_id",
					RouteID:   "route_id",
				},
			},
			wantTripStopTimes: []db.ListScheduledTripStopTimesRow{
				{
					TripID:            "trip_id",
					StopID:            "stop_id",
					ArrivalTime:       convert.Duration(1 * time.Hour),
					DepartureTime:     convert.Duration(2 * time.Hour),
					StopSequence:      42,
					Headsign:          convert.NullIfEmptyString("Times Square"),
					ContinuousPickup:  "NOT_ALLOWED",
					ContinuousDropOff: "PHONE_AGENCY",
					PickupType:        "ALLOWED",
					DropOffType:       "ALLOWED",
				},
				{
					TripID:                "trip_id",
					StopID:                "stop_id_2",
					ArrivalTime:           convert.Duration(2 * time.Hour),
					DepartureTime:         convert.Duration(3 * time.Hour),
					StopSequence:          43,
					Headsign:              convert.NullIfEmptyString("Times Square"),
					ContinuousPickup:      "ALLOWED",
					ContinuousDropOff:     "ALLOWED",
					PickupType:            "ALLOWED",
					DropOffType:           "ALLOWED",
					ShapeDistanceTraveled: convert.NullFloat64(ptr(42.0)),
				},
			},
			onlyCheckTrips: true,
		},
		{
			name: "stale trip stop time deletion",
			updates: []*gtfs.Static{
				{
					Agencies: []gtfs.Agency{defaultAgency},
					Routes:   []gtfs.Route{defaultRoute},
					Services: []gtfs.Service{defaultService},
					Stops:    []gtfs.Stop{defaultStop},
					Trips: []gtfs.ScheduledTrip{
						{
							ID:      "trip_id",
							Route:   &defaultRoute,
							Service: &defaultService,
							StopTimes: []gtfs.ScheduledStopTime{
								{
									Trip:          &defaultTrip,
									Stop:          &defaultStop,
									ArrivalTime:   1 * time.Hour,
									DepartureTime: 2 * time.Hour,
									StopSequence:  42,
									Headsign:      "Times Square",
								},
							},
						},
					},
				},
				{
					Agencies: []gtfs.Agency{defaultAgency},
					Routes:   []gtfs.Route{defaultRoute},
					Services: []gtfs.Service{defaultService},
					Stops:    []gtfs.Stop{defaultStop},
					Trips: []gtfs.ScheduledTrip{
						{
							ID:        "trip_id",
							Route:     &defaultRoute,
							Service:   &defaultService,
							StopTimes: []gtfs.ScheduledStopTime{},
						},
					},
				},
			},
			wantTrips: []db.ListScheduledTripsRow{
				{
					ID:        "trip_id",
					ServiceID: "service_id",
					RouteID:   "route_id",
				},
			},
			wantTripStopTimes: nil,
			onlyCheckTrips:    true,
		},
		{
			name: "trip stop times update",
			updates: []*gtfs.Static{
				{
					Agencies: []gtfs.Agency{defaultAgency},
					Routes:   []gtfs.Route{defaultRoute},
					Services: []gtfs.Service{defaultService},
					Stops:    []gtfs.Stop{defaultStop},
					Trips: []gtfs.ScheduledTrip{
						{
							ID:      "trip_id",
							Route:   &defaultRoute,
							Service: &defaultService,
							StopTimes: []gtfs.ScheduledStopTime{
								{
									Trip:          &defaultTrip,
									Stop:          &defaultStop,
									ArrivalTime:   1 * time.Hour,
									DepartureTime: 2 * time.Hour,
									StopSequence:  42,
									Headsign:      "Times Square",
								},
							},
						},
					},
				},
				{
					Agencies: []gtfs.Agency{defaultAgency},
					Routes:   []gtfs.Route{defaultRoute},
					Services: []gtfs.Service{defaultService},
					Stops:    []gtfs.Stop{defaultStop, {Id: "stop_id_2"}},
					Trips: []gtfs.ScheduledTrip{
						{
							ID:      "trip_id",
							Route:   &defaultRoute,
							Service: &defaultService,
							StopTimes: []gtfs.ScheduledStopTime{
								{
									Trip:          &defaultTrip,
									Stop:          &gtfs.Stop{Id: "stop_id_2"},
									ArrivalTime:   3 * time.Hour,
									DepartureTime: 4 * time.Hour,
									StopSequence:  100,
									Headsign:      "Union Square",
								},
							},
						},
					},
				},
			},
			wantTrips: []db.ListScheduledTripsRow{
				{
					ID:        "trip_id",
					ServiceID: "service_id",
					RouteID:   "route_id",
				},
			},
			wantTripStopTimes: []db.ListScheduledTripStopTimesRow{
				{
					TripID:            "trip_id",
					StopID:            "stop_id_2",
					ArrivalTime:       convert.Duration(3 * time.Hour),
					DepartureTime:     convert.Duration(4 * time.Hour),
					StopSequence:      100,
					Headsign:          convert.NullIfEmptyString("Union Square"),
					ContinuousPickup:  "ALLOWED",
					ContinuousDropOff: "ALLOWED",
					PickupType:        "ALLOWED",
					DropOffType:       "ALLOWED",
				},
			},
			onlyCheckTrips: true,
		},
		{
			name: "multiple trips",
			updates: []*gtfs.Static{
				{
					Agencies: []gtfs.Agency{defaultAgency},
					Routes:   []gtfs.Route{defaultRoute},
					Services: []gtfs.Service{defaultService},
					Trips: []gtfs.ScheduledTrip{
						defaultTrip,
						{
							ID:      "other_trip",
							Service: &defaultService,
							Route:   &defaultRoute,
						},
					},
				},
			},
			wantTrips: []db.ListScheduledTripsRow{
				{
					ID:        "trip_id",
					ServiceID: "service_id",
					RouteID:   "route_id",
				},
				{
					ID:        "other_trip",
					ServiceID: "service_id",
					RouteID:   "route_id",
				},
			},
			onlyCheckTrips: true,
		},
		{
			name: "update trip",
			updates: []*gtfs.Static{
				{
					Agencies: []gtfs.Agency{defaultAgency},
					Routes:   []gtfs.Route{defaultRoute},
					Services: []gtfs.Service{defaultService},
					Trips: []gtfs.ScheduledTrip{
						defaultTrip,
						{
							ID:      "other_trip",
							Service: &defaultService,
							Route:   &defaultRoute,
						},
					},
				},
				{
					Agencies: []gtfs.Agency{defaultAgency},
					Routes:   []gtfs.Route{defaultRoute},
					Services: []gtfs.Service{defaultService},
					Trips: []gtfs.ScheduledTrip{
						defaultTrip,
						{
							ID:       "other_trip",
							Service:  &defaultService,
							Route:    &defaultRoute,
							Headsign: "Union Square",
						},
					},
				},
			},
			wantTrips: []db.ListScheduledTripsRow{
				{
					ID:        "trip_id",
					ServiceID: "service_id",
					RouteID:   "route_id",
				},
				{
					ID:        "other_trip",
					ServiceID: "service_id",
					RouteID:   "route_id",
					Headsign:  convert.NullIfEmptyString("Union Square"),
				},
			},
			onlyCheckTrips: true,
		},
		{
			name: "trip frequencies",
			updates: []*gtfs.Static{
				{
					Agencies: []gtfs.Agency{defaultAgency},
					Routes:   []gtfs.Route{defaultRoute},
					Services: []gtfs.Service{defaultService},
					Stops:    []gtfs.Stop{defaultStop},
					Trips: []gtfs.ScheduledTrip{
						{
							ID:      "trip_id",
							Route:   &defaultRoute,
							Service: &defaultService,
							Frequencies: []gtfs.Frequency{
								{
									StartTime:  1 * time.Hour,
									EndTime:    2 * time.Hour,
									Headway:    10 * time.Minute,
									ExactTimes: gtfs.FrequencyBased,
								},
								{
									StartTime:  3 * time.Hour,
									EndTime:    4 * time.Hour,
									Headway:    15 * time.Minute,
									ExactTimes: gtfs.ScheduleBased,
								},
							},
						},
					},
				},
			},
			wantTrips: []db.ListScheduledTripsRow{
				{
					ID:        "trip_id",
					ServiceID: "service_id",
					RouteID:   "route_id",
				},
			},
			wantTripFrequencies: []db.ListScheduledTripFrequenciesRow{
				{
					TripID:         "trip_id",
					StartTime:      int32((1 * time.Hour).Seconds()),
					EndTime:        int32((2 * time.Hour).Seconds()),
					Headway:        int32((10 * time.Minute).Seconds()),
					FrequencyBased: true,
				},
				{
					TripID:         "trip_id",
					StartTime:      int32((3 * time.Hour).Seconds()),
					EndTime:        int32((4 * time.Hour).Seconds()),
					Headway:        int32((15 * time.Minute).Seconds()),
					FrequencyBased: false,
				},
			},
			onlyCheckTrips: true,
		},
		{
			name: "trip frequencies update",
			updates: []*gtfs.Static{
				{
					Agencies: []gtfs.Agency{defaultAgency},
					Routes:   []gtfs.Route{defaultRoute},
					Services: []gtfs.Service{defaultService},
					Stops:    []gtfs.Stop{defaultStop},
					Trips: []gtfs.ScheduledTrip{
						{
							ID:      "trip_id",
							Route:   &defaultRoute,
							Service: &defaultService,
							Frequencies: []gtfs.Frequency{
								{
									StartTime:  1 * time.Hour,
									EndTime:    2 * time.Hour,
									Headway:    10 * time.Minute,
									ExactTimes: gtfs.FrequencyBased,
								},
								{
									StartTime:  3 * time.Hour,
									EndTime:    4 * time.Hour,
									Headway:    15 * time.Minute,
									ExactTimes: gtfs.ScheduleBased,
								},
							},
						},
					},
				},
				{
					Agencies: []gtfs.Agency{defaultAgency},
					Routes:   []gtfs.Route{defaultRoute},
					Services: []gtfs.Service{defaultService},
					Stops:    []gtfs.Stop{defaultStop},
					Trips: []gtfs.ScheduledTrip{
						{
							ID:      "trip_id",
							Route:   &defaultRoute,
							Service: &defaultService,
							Frequencies: []gtfs.Frequency{
								{
									StartTime:  2 * time.Hour,
									EndTime:    3 * time.Hour,
									Headway:    15 * time.Minute,
									ExactTimes: gtfs.ScheduleBased,
								},
								{
									StartTime:  4 * time.Hour,
									EndTime:    5 * time.Hour,
									Headway:    20 * time.Minute,
									ExactTimes: gtfs.FrequencyBased,
								},
							},
						},
					},
				},
			},
			wantTrips: []db.ListScheduledTripsRow{
				{
					ID:        "trip_id",
					ServiceID: "service_id",
					RouteID:   "route_id",
				},
			},
			wantTripFrequencies: []db.ListScheduledTripFrequenciesRow{
				{
					TripID:         "trip_id",
					StartTime:      int32((2 * time.Hour).Seconds()),
					EndTime:        int32((3 * time.Hour).Seconds()),
					Headway:        int32((15 * time.Minute).Seconds()),
					FrequencyBased: false,
				},
				{
					TripID:         "trip_id",
					StartTime:      int32((4 * time.Hour).Seconds()),
					EndTime:        int32((5 * time.Hour).Seconds()),
					Headway:        int32((20 * time.Minute).Seconds()),
					FrequencyBased: true,
				},
			},
			onlyCheckTrips: true,
		},
		{
			name: "trip shape",
			updates: []*gtfs.Static{
				{
					Agencies: []gtfs.Agency{defaultAgency},
					Routes:   []gtfs.Route{defaultRoute},
					Services: []gtfs.Service{defaultService},
					Stops:    []gtfs.Stop{defaultStop},
					Trips: []gtfs.ScheduledTrip{
						{
							ID:      "trip_id",
							Route:   &defaultRoute,
							Service: &defaultService,
							Shape:   &defaultShape,
						},
					},
					Shapes: []gtfs.Shape{defaultShape},
				},
			},
			wantTrips: []db.ListScheduledTripsRow{
				{
					ID:        "trip_id",
					ServiceID: "service_id",
					RouteID:   "route_id",
				},
			},
			wantTripShapes: []shapeAndTripID{
				{
					TripID: "trip_id",
					Shape:  convert.ApiShape(&defaultShape),
				},
			},
			onlyCheckTrips: true,
		},
		{
			name: "shape with multiple associated trips",
			updates: []*gtfs.Static{
				{
					Agencies: []gtfs.Agency{defaultAgency},
					Routes:   []gtfs.Route{defaultRoute},
					Services: []gtfs.Service{defaultService},
					Stops:    []gtfs.Stop{defaultStop},
					Trips: []gtfs.ScheduledTrip{
						{
							ID:      "trip_id",
							Route:   &defaultRoute,
							Service: &defaultService,
							Shape:   &defaultShape,
						},
						{
							ID:      "another_trip",
							Route:   &defaultRoute,
							Service: &defaultService,
							Shape:   &defaultShape,
						},
					},
					Shapes: []gtfs.Shape{defaultShape},
				},
			},
			wantTrips: []db.ListScheduledTripsRow{
				{
					ID:        "trip_id",
					ServiceID: "service_id",
					RouteID:   "route_id",
				},
				{
					ID:        "another_trip",
					ServiceID: "service_id",
					RouteID:   "route_id",
				},
			},
			wantTripShapes: []shapeAndTripID{
				{
					TripID: "trip_id",
					Shape:  convert.ApiShape(&defaultShape),
				},
				{
					TripID: "another_trip",
					Shape:  convert.ApiShape(&defaultShape),
				},
			},
			onlyCheckTrips: true,
		},
		{
			name: "shape update",
			updates: []*gtfs.Static{
				{
					Agencies: []gtfs.Agency{defaultAgency},
					Routes:   []gtfs.Route{defaultRoute},
					Services: []gtfs.Service{defaultService},
					Stops:    []gtfs.Stop{defaultStop},
					Trips: []gtfs.ScheduledTrip{
						{
							ID:      "trip_id",
							Route:   &defaultRoute,
							Service: &defaultService,
							Shape:   &defaultShape,
						},
					},
					Shapes: []gtfs.Shape{defaultShape},
				},
				{
					Agencies: []gtfs.Agency{defaultAgency},
					Routes:   []gtfs.Route{defaultRoute},
					Services: []gtfs.Service{defaultService},
					Stops:    []gtfs.Stop{defaultStop},
					Trips: []gtfs.ScheduledTrip{
						{
							ID:      "trip_id",
							Route:   &defaultRoute,
							Service: &defaultService,
							Shape:   &gtfs.Shape{ID: "shape_id"},
						},
					},
					Shapes: []gtfs.Shape{
						{
							ID: "shape_id",
							Points: []gtfs.ShapePoint{
								{
									Latitude:  100,
									Longitude: 200,
								},
								{
									Latitude:  -100,
									Longitude: -200,
								},
							},
						},
					},
				},
			},
			wantTrips: []db.ListScheduledTripsRow{
				{
					ID:        "trip_id",
					ServiceID: "service_id",
					RouteID:   "route_id",
				},
			},
			wantTripShapes: []shapeAndTripID{
				{
					TripID: "trip_id",
					Shape: &api.Shape{
						Id: "shape_id",
						Points: []*api.Shape_ShapePoint{
							{
								Latitude:  100,
								Longitude: 200,
							},
							{
								Latitude:  -100,
								Longitude: -200,
							},
						},
					},
				},
			},
			onlyCheckTrips: true,
		},
		{
			name: "trip shape update",
			updates: []*gtfs.Static{
				{
					Agencies: []gtfs.Agency{defaultAgency},
					Routes:   []gtfs.Route{defaultRoute},
					Services: []gtfs.Service{defaultService},
					Stops:    []gtfs.Stop{defaultStop},
					Trips: []gtfs.ScheduledTrip{
						{
							ID:      "trip_id",
							Route:   &defaultRoute,
							Service: &defaultService,
							Shape:   &defaultShape,
						},
					},
					Shapes: []gtfs.Shape{defaultShape},
				},
				{
					Agencies: []gtfs.Agency{defaultAgency},
					Routes:   []gtfs.Route{defaultRoute},
					Services: []gtfs.Service{defaultService},
					Stops:    []gtfs.Stop{defaultStop},
					Trips: []gtfs.ScheduledTrip{
						{
							ID:      "trip_id",
							Route:   &defaultRoute,
							Service: &defaultService,
							Shape: &gtfs.Shape{
								ID: "new_shape_id",
							},
						},
					},
					Shapes: []gtfs.Shape{
						{
							ID: "new_shape_id",
							Points: []gtfs.ShapePoint{
								{
									Latitude:  100,
									Longitude: 200,
								},
								{
									Latitude:  -100,
									Longitude: -200,
								},
							},
						},
					},
				},
			},
			wantTrips: []db.ListScheduledTripsRow{
				{
					ID:        "trip_id",
					ServiceID: "service_id",
					RouteID:   "route_id",
				},
			},
			wantTripShapes: []shapeAndTripID{
				{
					TripID: "trip_id",
					Shape: &api.Shape{
						Id: "new_shape_id",
						Points: []*api.Shape_ShapePoint{
							{
								Latitude:  100,
								Longitude: 200,
							},
							{
								Latitude:  -100,
								Longitude: -200,
							},
						},
					},
				},
			},
			onlyCheckTrips: true,
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			querier := dbtesting.NewQuerier(t)
			system := querier.NewSystem("system")
			feed := system.NewFeed("feedID")

			ctx := context.Background()
			updateCtx := common.UpdateContext{
				Querier:  querier,
				SystemPk: system.Data.Pk,
				FeedPk:   feed.Data.Pk,
				FeedConfig: &api.FeedConfig{
					Parser: "GTFS_STATIC",
				},
				Logger: slog.Default(),
			}

			for i, update := range tc.updates {
				err := Update(ctx, updateCtx, update)
				if err != nil {
					t.Fatalf("Update(update %d) got = %v, want = <nil>", err, i)
				}
			}

			gotStops, stopIDToParentID := listStops(ctx, t, querier, updateCtx.SystemPk)
			if diff := cmp.Diff(gotStops, tc.wantStops, cmp.Comparer(compareBigInt)); diff != "" && !tc.onlyCheckTrips {
				t.Errorf("ListStops() got = %v, want = %v, diff = %s", gotStops, tc.wantStops, diff)
			}
			if tc.wantStopIDToParentID == nil {
				tc.wantStopIDToParentID = map[string]string{}
			}
			if diff := cmp.Diff(stopIDToParentID, tc.wantStopIDToParentID); diff != "" && !tc.onlyCheckTrips {
				t.Errorf("ListStops() stopIDToParentID = %v, want = %v, diff = %s", stopIDToParentID, tc.wantStopIDToParentID, diff)
			}

			gotServices := listServices(ctx, t, querier, updateCtx.SystemPk)
			if diff := cmp.Diff(gotServices, tc.wantServices, cmp.Comparer(compareBigInt)); diff != "" && !tc.onlyCheckTrips {
				t.Errorf("ListServices() got = %v, want = %v, diff = %s", gotServices, tc.wantServices, diff)
			}

			gotTrips := listScheduledTrips(ctx, t, querier, updateCtx.SystemPk)
			if diff := cmp.Diff(gotTrips, tc.wantTrips, cmp.Comparer(compareBigInt)); diff != "" {
				t.Errorf("ListScheduledTrips() got = %v, want = %v, diff = %s", gotTrips, tc.wantTrips, diff)
			}

			gotTripStopTimes := listScheduledTripStopTimes(ctx, t, querier, updateCtx.SystemPk)
			if diff := cmp.Diff(gotTripStopTimes, tc.wantTripStopTimes, cmp.Comparer(compareBigInt)); diff != "" {
				t.Errorf("ListScheduledTripStopTimes() got = %v, want = %v, diff = %s", gotTripStopTimes, tc.wantTripStopTimes, diff)
			}

			gotTripFrequencies := listScheduledTripFrequencies(ctx, t, querier, updateCtx.SystemPk)
			if diff := cmp.Diff(gotTripFrequencies, tc.wantTripFrequencies, cmp.Comparer(compareBigInt)); diff != "" {
				t.Errorf("ListScheduledTripFrequencies() got = %v, want = %v, diff = %s", gotTripFrequencies, tc.wantTripFrequencies, diff)
			}

			gotTripShapes := listScheduledTripShapes(ctx, t, querier, updateCtx.SystemPk)
			if diff := cmp.Diff(gotTripShapes, tc.wantTripShapes, cmp.Comparer(compareBigInt), cmpopts.IgnoreUnexported(api.Shape{}, api.Shape_ShapePoint{})); diff != "" {
				t.Errorf("ListScheduledTripShapes() got = %v, want = %v, diff = %s", gotTripShapes, tc.wantTripShapes, diff)
			}
		})
	}
}

func listStops(ctx context.Context, t *testing.T, querier db.Querier, systemPk int64) ([]db.Stop, map[string]string) {
	stops, err := querier.ListStops(ctx, db.ListStopsParams{SystemPk: systemPk, NumStops: math.MaxInt32})
	if err != nil {
		t.Errorf("ListStops() err = %v, want = nil", err)
	}
	stopPkToParentPk := map[int64]int64{}
	pkToID := map[int64]string{}
	for i := range stops {
		stop := &stops[i]
		if stop.ParentStopPk.Valid {
			stopPkToParentPk[stop.Pk] = stop.ParentStopPk.Int64
		}
		pkToID[stop.Pk] = stop.ID
		stop.Pk = 0
		stop.ParentStopPk = pgtype.Int8{}
		stop.FeedPk = 0
		stop.SystemPk = 0
	}
	stopIDToParentID := map[string]string{}
	for stopPk, parentPk := range stopPkToParentPk {
		stopIDToParentID[pkToID[stopPk]] = pkToID[parentPk]
	}
	return stops, stopIDToParentID
}

func listServices(ctx context.Context, t *testing.T, querier db.Querier, systemPk int64) []db.ListScheduledServicesRow {
	services, err := querier.ListScheduledServices(ctx, systemPk)
	if err != nil {
		t.Errorf("ListServices() err = %v, want = nil", err)
	}
	for i := range services {
		service := &services[i]
		service.Pk = 0
		service.FeedPk = 0
		service.SystemPk = 0
	}
	return services
}

func listScheduledTrips(ctx context.Context, t *testing.T, querier db.Querier, systemPk int64) []db.ListScheduledTripsRow {
	trips, err := querier.ListScheduledTrips(ctx, systemPk)
	if err != nil {
		t.Errorf("ListScheduledTrips() err = %v, want = nil", err)
	}
	for i := range trips {
		trip := &trips[i]
		trip.Pk = 0
		trip.ServicePk = 0
		trip.RoutePk = 0
		trip.ShapePk = pgtype.Int8{}
	}
	return trips
}

func listScheduledTripStopTimes(ctx context.Context, t *testing.T, querier db.Querier, systemPk int64) []db.ListScheduledTripStopTimesRow {
	stopTimes, err := querier.ListScheduledTripStopTimes(ctx, systemPk)
	if err != nil {
		t.Errorf("ListScheduledTripStopTimes() err = %v, want = nil", err)
	}
	for i := range stopTimes {
		stopTime := &stopTimes[i]
		stopTime.Pk = 0
		stopTime.TripPk = 0
		stopTime.StopPk = 0
	}
	return stopTimes
}

func listScheduledTripFrequencies(ctx context.Context, t *testing.T, querier db.Querier, systemPk int64) []db.ListScheduledTripFrequenciesRow {
	frequencies, err := querier.ListScheduledTripFrequencies(ctx, systemPk)
	if err != nil {
		t.Errorf("ListScheduledTripFrequencies() err = %v, want = nil", err)
	}
	for i := range frequencies {
		frequency := &frequencies[i]
		frequency.Pk = 0
		frequency.TripPk = 0
	}
	return frequencies
}

type shapeAndTripID struct {
	Shape  *api.Shape
	TripID string
}

func listScheduledTripShapes(ctx context.Context, t *testing.T, querier db.Querier, systemPk int64) []shapeAndTripID {
	shapes, err := querier.ListShapesAndTrips(ctx, systemPk)
	if err != nil {
		t.Errorf("ListScheduledTripShapes() err = %v, want = nil", err)
	}
	shapeAndTripIDs := []shapeAndTripID{}
	for _, dbShape := range shapes {
		apiShape, err := convert.JSONShapeToApiShape(dbShape.Shape)
		if err != nil {
			t.Errorf("Failed to parse JSON shape, err = %v, want = nil", err)
		}
		shapeAndTripIDs = append(shapeAndTripIDs, shapeAndTripID{
			TripID: dbShape.TripID,
			Shape:  apiShape,
		})
	}

	if len(shapeAndTripIDs) == 0 {
		return nil
	}

	return shapeAndTripIDs
}

func ptr[T any](t T) *T {
	return &t
}

func dbString(s string) pgtype.Text {
	return pgtype.Text{Valid: true, String: s}
}

func compareBigInt(a, b *big.Int) bool {
	return a.Cmp(b) == 0
}
