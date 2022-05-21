// Package dbtesting is a testing util package for running unit tests against a running database.
package dbtesting

import (
	"context"
	"fmt"
	"log"
	"os"
	"sync"
	"testing"
	"time"

	"github.com/jackc/pgx/v4"
	"github.com/jackc/pgx/v4/pgxpool"
	"github.com/jamespfennell/transiter/db/schema"
	"github.com/jamespfennell/transiter/internal/db/constants"
	"github.com/jamespfennell/transiter/internal/db/dbwrappers"
	"github.com/jamespfennell/transiter/internal/gen/db"
)

type Querier struct {
	db.Querier
	t *testing.T

	system1Created bool
	feed1Created   bool
	update1Pk      *int64
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

func (q *Querier) System1() db.System {
	if !q.system1Created {
		_, err := q.InsertSystem(context.Background(), db.InsertSystemParams{
			ID:     q.System1Id(),
			Name:   q.System1Id(),
			Status: constants.Active,
		})
		q.AssertNilErr(err, "insert system 1")
		q.system1Created = true
	}
	system, err := q.GetSystem(context.Background(), q.System1Id())
	q.AssertNilErr(err, "read system 1")
	return system
}

func (q *Querier) System1Id() string {
	return q.t.Name() + "-System1"
}

func (q *Querier) System1Feed1() db.Feed {
	if !q.feed1Created {
		system1 := q.System1()
		err := q.InsertFeed(context.Background(), db.InsertFeedParams{
			ID:       "feed1",
			SystemPk: system1.Pk,
		})
		q.AssertNilErr(err, "insert feed 1")
		q.feed1Created = true
	}
	feed, err := q.GetFeedInSystem(context.Background(), db.GetFeedInSystemParams{
		SystemID: q.System1Id(),
		FeedID:   "feed1",
	})
	q.AssertNilErr(err, "read feed 1")
	return feed
}

func (q *Querier) Update1Pk() int64 {
	if q.update1Pk == nil {
		feed1 := q.System1Feed1()
		pk, err := q.InsertFeedUpdate(context.Background(), db.InsertFeedUpdateParams{
			FeedPk: feed1.Pk,
			Status: "SUCCESS",
		})
		q.update1Pk = &pk
		q.AssertNilErr(err, "insert update 1")
	}
	return *q.update1Pk
}

func (q *Querier) AssertNilErr(err error, action string) {
	if err != nil {
		q.t.Fatalf("failed to %s: %+v", action, err)
	}
}
