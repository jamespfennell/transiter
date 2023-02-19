package realtime

import (
	"context"
	"database/sql"
	"testing"
	"time"

	"github.com/google/go-cmp/cmp"
	"github.com/jamespfennell/gtfs"
	"github.com/jamespfennell/transiter/internal/db/dbtesting"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/update/common"
)

const (
	routeID1 = "routeID1"
	stopID1  = "stopID1"
	stopID2  = "stopID2"
	stopID3  = "stopID3"
	stopID4  = "stopID4"
	tripID1  = "tripID1"
)

func TestUpdateTrips(t *testing.T) {
	for _, tc := range []struct {
		name string
		// The update process will run N times, 1 for each trip version. Providing <nil> for a version
		// will run an update with no trips.
		tripVersions []*gtfs.Trip
		wantTrip     *Trip
	}{
		{
			name: "simple case",
			tripVersions: []*gtfs.Trip{
				gtfsTrip(tripID1, routeID1, gtfs.DirectionIDTrue, []gtfs.StopTimeUpdate{
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
			name: "same update twice",
			tripVersions: func(t *gtfs.Trip) []*gtfs.Trip {
				return []*gtfs.Trip{t, t}
			}(
				gtfsTrip(tripID1, routeID1, gtfs.DirectionIDTrue, []gtfs.StopTimeUpdate{
					gtfsStu(gStopID(stopID1), gDepTime(5)),
					gtfsStu(gStopID(stopID2), gArrTime(10), gDepTime(15)),
					gtfsStu(gStopID(stopID3), gArrTime(20), gDepTime(25)),
					gtfsStu(gStopID(stopID4), gArrTime(30)),
				}),
			),
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
				gtfsTrip(tripID1, routeID1, gtfs.DirectionIDTrue, []gtfs.StopTimeUpdate{
					gtfsStu(gStopID(stopID1), gDepTime(5)),
					gtfsStu(gStopID(stopID2), gArrTime(10), gDepTime(15)),
					gtfsStu(gStopID(stopID3), gArrTime(20), gDepTime(25)),
					gtfsStu(gStopID(stopID4), gArrTime(30)),
				}),
				gtfsTrip(tripID1, routeID1, gtfs.DirectionIDTrue, []gtfs.StopTimeUpdate{
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
				gtfsTrip(tripID1, routeID1, gtfs.DirectionIDTrue, []gtfs.StopTimeUpdate{
					gtfsStu(gStopID(stopID1), gDepTime(5)),
					gtfsStu(gStopID(stopID2), gArrTime(10), gDepTime(15)),
					gtfsStu(gStopID(stopID3), gArrTime(20), gDepTime(25)),
					gtfsStu(gStopID(stopID4), gArrTime(30)),
				}),
				gtfsTrip(tripID1, routeID1, gtfs.DirectionIDTrue, []gtfs.StopTimeUpdate{
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
	} {
		t.Run(tc.name, func(t *testing.T) {
			querier := dbtesting.NewQuerier(t)
			system := querier.NewSystem("system")
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
			update := feed.NewUpdate()

			ctx := context.Background()
			updateCtx := common.UpdateContext{
				Querier:  querier,
				SystemPk: system.Data.Pk,
				FeedPk:   feed.Data.Pk,
				UpdatePk: update.Pk,
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

			dbTrip, err := querier.GetTrip(ctx, db.GetTripParams{
				RoutePk: routeIDToPk[tc.wantTrip.RouteID],
				TripID:  tc.wantTrip.DBFields.ID,
			})
			if err != nil {
				t.Fatalf("GetTrip(routeID=%s, tripID=%s) err got = %v, want = <nil>", tc.wantTrip.RouteID, tc.wantTrip.DBFields.ID, err)
			}
			dbStopTimes, err := querier.ListStopsTimesForTrip(ctx, dbTrip.Pk)
			if err != nil {
				t.Fatalf("ListStopTimesForTrip(routeID=%s, tripID=%s) err got = %v, want = <nil>", tc.wantTrip.RouteID, tc.wantTrip.DBFields.ID, err)
			}

			gotTrip := NewTripFromDB(dbTrip, dbStopTimes, routePkToID, stopPkToID)

			if diff := cmp.Diff(gotTrip, *tc.wantTrip); diff != "" {
				t.Errorf("got = %v, want = %v, diff = %s", gotTrip, tc.wantTrip, diff)
			}
		})
	}
}

type Trip struct {
	RouteID   string
	DBFields  db.Trip
	StopTimes []StopTime
}

func NewTripFromDB(in db.Trip, stopTimes []db.ListStopsTimesForTripRow, routePkToID, stopPkToID map[int64]string) Trip {
	var outStopTimes []StopTime
	for _, inStopTime := range stopTimes {
		outStopTimes = append(outStopTimes, NewStopTimeFromDB(inStopTime, stopPkToID))
	}
	routeID := routePkToID[in.RoutePk]
	// Clear all primary key columns
	in.Pk = 0
	in.RoutePk = 0
	in.SourcePk = 0
	in.GtfsHash = ""
	return Trip{
		RouteID:   routeID,
		DBFields:  in,
		StopTimes: outStopTimes,
	}
}

func wantTrip(tripID, routeID string, directionID bool, sts []StopTime) *Trip {
	return &Trip{
		RouteID: routeID,
		DBFields: db.Trip{
			ID:          tripID,
			DirectionID: sql.NullBool{Valid: true, Bool: directionID},
		},
		StopTimes: sts,
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
	in.StopName = sql.NullString{}
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
		st.DBFields.ArrivalTime = sql.NullTime{Valid: true, Time: t}
	}
}

func wDepTime(i int) wantStOpt {
	t := mkTime(i)
	return func(st *StopTime) {
		st.DBFields.DepartureTime = sql.NullTime{Valid: true, Time: t}
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
			DirectionID: gtfs.DirectionIDTrue,
		},
		StopTimeUpdates: stus,
	}
}
