// Package dbtesting is a testing util package for running unit tests against a running database.
package dbtesting

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"os"
	"sync"
	"testing"
	"time"

	"github.com/jackc/pgtype"
	"github.com/jackc/pgx/v4"
	"github.com/jackc/pgx/v4/pgxpool"
	"github.com/jamespfennell/gtfs"
	"github.com/jamespfennell/transiter/db/schema"
	"github.com/jamespfennell/transiter/internal/db/constants"
	"github.com/jamespfennell/transiter/internal/db/dbwrappers"
	"github.com/jamespfennell/transiter/internal/gen/db"
)

type Querier struct {
	db.Querier
	t *testing.T
}

var skipDatabaseTests bool

func init() {
	_, skipDatabaseTests = os.LookupEnv("SKIP_DATABASE_TESTS")
}

func NewQuerier(t *testing.T) *Querier {
	if skipDatabaseTests {
		t.Skip("database tests are disabled")
	}
	tx, err := getDB(t).BeginTx(context.Background(), pgx.TxOptions{})
	if err != nil {
		t.Fatalf("failed to start testing transaction: %+v", err)
	}
	t.Cleanup(func() {
		if err := tx.Rollback(context.Background()); err != nil {
			t.Errorf("failed to rollback testing transaction: %+v", err)
		}
	})
	return &Querier{
		Querier: db.New(tx),
		t:       t,
	}
}

var d *pgxpool.Pool
var dm sync.Mutex

func getDB(t *testing.T) *pgxpool.Pool {
	dm.Lock()
	defer dm.Unlock()
	if d != nil {
		return d
	}
	var err error
	d, err = pgxpool.Connect(context.Background(), fmt.Sprintf("postgres://%s:%s@%s?sslmode=disable",
		"transiter", // TODO customize?
		"transiter",
		"localhost:5432",
	))
	if err != nil {
		t.Fatalf("failed to connect to Postgres: %+v", err)
	}
	if err := dbwrappers.Ping(context.Background(), d, 100, 50*time.Millisecond); err != nil {
		log.Fatalf("Failed to connect to the database; exiting: %s\n", err)
	}

	dbName := "transitertestdatabase"
	_, err = d.Exec(context.Background(), "DROP DATABASE IF EXISTS "+dbName)
	if err != nil {
		t.Fatalf("failed to drop Postgres database %s: %+v", dbName, err)
	}
	_, err = d.Exec(context.Background(), "CREATE DATABASE "+dbName)
	if err != nil {
		t.Fatalf("failed to create Postgres database %s: %+v", dbName, err)
	}

	d, err = pgxpool.Connect(context.Background(), fmt.Sprintf("postgres://%s:%s@%s/%s?sslmode=disable",
		"transiter", // TODO customize?
		"transiter",
		"localhost:5432",
		dbName,
	))
	if err != nil {
		t.Fatalf("failed to connect to Postgres: %+v", err)
	}

	fmt.Println("Running schema migrations")
	if err := schema.Migrate(context.Background(), d); err != nil {
		t.Fatalf("failed to run schema migrations: %+v", err)
	}
	return d
}

type System struct {
	Data          *db.System
	DefaultFeed   *Feed
	DefaulUpdate  *db.FeedUpdate
	DefaultAgency *db.Agency
	q             *Querier
}

func (q *Querier) NewSystem(id string) System {
	// TODO: generate a unique prefix in the querier and add it to the system ID
	// This will mean the same test can be run concurrently
	fullID := fmt.Sprintf("%s-%s", q.t.Name(), id)
	data := insertAndGet(
		q, fmt.Sprintf("system with ID %s (full ID %s)", id, fullID),
		func() error {
			_, err := q.InsertSystem(context.Background(), db.InsertSystemParams{
				ID:     fullID,
				Name:   fullID,
				Status: constants.Active,
			})
			return err
		},
		func() (db.System, error) {
			return q.GetSystem(context.Background(), fullID)
		},
	)
	s := System{
		Data: &data,
		q:    q,
	}
	feed := s.NewFeed("defaultFeed")
	s.DefaultFeed = &feed
	update := feed.NewUpdate()
	s.DefaulUpdate = &update
	agency := s.NewAgency("defaultAgency")
	s.DefaultAgency = &agency
	return s
}

type Feed struct {
	Data *db.Feed
	s    *System
}

func (s *System) NewFeed(id string) Feed {
	data := insertAndGet(
		s.q, fmt.Sprintf("feed %s/%s", s.Data.ID, id),
		func() error {
			return s.q.InsertFeed(context.Background(), db.InsertFeedParams{
				ID:       id,
				SystemPk: s.Data.Pk,
			})
		},
		func() (db.Feed, error) {
			return s.q.GetFeedInSystem(context.Background(), db.GetFeedInSystemParams{
				SystemID: s.Data.ID,
				FeedID:   id,
			})
		},
	)
	return Feed{
		Data: &data,
		s:    s,
	}
}

func (f *Feed) NewUpdate() db.FeedUpdate {
	var pk int64
	return insertAndGet(
		f.s.q, fmt.Sprintf("feed update %s/%s/<update_pk>", f.Data.ID, f.s.Data.ID),
		func() error {
			var err error
			pk, err = f.s.q.InsertFeedUpdate(context.Background(), db.InsertFeedUpdateParams{
				FeedPk: f.Data.Pk,
				Status: "SUCCESS",
			})
			return err
		},
		func() (db.FeedUpdate, error) {
			return f.s.q.GetFeedUpdate(context.Background(), pk)
		},
	)
}

func (s *System) NewAgency(id string) db.Agency {
	return insertAndGet(
		s.q, id,
		func() error {
			var err error
			_, err = s.q.InsertAgency(context.Background(), db.InsertAgencyParams{
				ID:       id,
				SystemPk: s.Data.Pk,
				SourcePk: s.DefaulUpdate.Pk,
			})
			return err
		},
		func() (db.Agency, error) {
			return s.q.GetAgencyInSystem(context.Background(), db.GetAgencyInSystemParams{
				SystemPk: s.Data.Pk,
				AgencyID: id,
			})
		},
	)
}

type Route struct {
	Data *db.Route
	s    *System
}

func (s *System) NewRoute(id string) Route {
	var pk int64
	route := insertAndGet(
		s.q, id,
		func() error {
			var err error
			pk, err = s.q.InsertRoute(context.Background(), db.InsertRouteParams{
				ID:       id,
				SystemPk: s.Data.Pk,
				SourcePk: s.DefaulUpdate.Pk,
				AgencyPk: s.DefaultAgency.Pk,
			})
			return err
		},
		func() (db.Route, error) {
			return s.q.GetRoute(context.Background(), pk)
		},
	)
	return Route{
		Data: &route,
		s:    s,
	}
}

type StopTime struct {
	Stop      db.Stop
	Departure time.Time
	Arrival   time.Time
}

func (r *Route) NewTrip(id string, stopTimes []StopTime) db.Trip {
	var pk int64
	trip := insertAndGet(
		r.s.q, id,
		func() error {
			var err error
			pk, err = r.s.q.InsertTrip(context.Background(), db.InsertTripParams{
				ID:       id,
				SourcePk: r.s.DefaulUpdate.Pk,
				RoutePk:  r.Data.Pk,
			})
			return err
		},
		func() (db.Trip, error) {
			return r.s.q.GetTripByPk(context.Background(), pk)
		},
	)
	for i, stopTime := range stopTimes {
		err := r.s.q.InsertTripStopTime(context.Background(), db.InsertTripStopTimeParams{
			StopPk:        stopTime.Stop.Pk,
			TripPk:        pk,
			StopSequence:  int32(i),
			DepartureTime: sql.NullTime{Valid: true, Time: stopTime.Departure},
			ArrivalTime:   sql.NullTime{Valid: true, Time: stopTime.Arrival},
		})
		r.s.q.AssertNilErr(err, "insert trip stop time")
	}
	return trip
}

func (s *System) NewStop(id string, params ...db.InsertStopParams) db.Stop {
	var p db.InsertStopParams
	if len(params) > 0 {
		p = params[0]
	}
	p.ID = id
	p.SystemPk = s.Data.Pk
	p.SourcePk = s.DefaulUpdate.Pk
	var zeroNumeric pgtype.Numeric
	if p.Longitude == zeroNumeric {
		p.Longitude = pgtype.Numeric{Status: pgtype.Null}
	}
	if p.Latitude == zeroNumeric {
		p.Latitude = pgtype.Numeric{Status: pgtype.Null}
	}
	if p.Type == "" {
		p.Type = gtfs.Station.String()
	}
	return insertAndGet(
		s.q, id,
		func() error {
			_, err := s.q.InsertStop(context.Background(), p)
			return err
		},
		func() (db.Stop, error) {
			return s.q.GetStopInSystem(context.Background(), db.GetStopInSystemParams{
				SystemID: s.Data.ID,
				StopID:   id,
			})
		},
	)
}

func (q *Querier) AssertNilErr(err error, action string) {
	if err != nil {
		q.t.Fatalf("failed to %s: %+v", action, err)
	}
}

func insertAndGet[T any](q *Querier, id string, insertFunc func() error, getFunc func() (T, error)) T {
	err := insertFunc()
	q.AssertNilErr(err, fmt.Sprintf("insert %s", id))
	t, err := getFunc()
	q.AssertNilErr(err, fmt.Sprintf("get %s", id))
	return t
}