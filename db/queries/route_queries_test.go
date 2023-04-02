package queries

import (
	"context"
	"fmt"
	"reflect"
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jamespfennell/transiter/internal/db/dbtesting"
	"github.com/jamespfennell/transiter/internal/gen/db"
)

func TestEstimateHeadwaysForRoutes(t *testing.T) {
	querier := dbtesting.NewQuerier(t)
	system := querier.NewSystem("system1")
	stop1 := system.NewStop("stop1")
	stop2 := system.NewStop("stop2")
	stop3 := system.NewStop("stop3")
	route1 := system.NewRoute("route1")
	route2 := system.NewRoute("route2")

	startTime := time.Date(2022, 3, 3, 4, 10, 0, 0, time.UTC)
	for _, data := range []struct {
		Route    dbtesting.Route
		Headways []time.Duration
	}{
		{
			Route:    route1,
			Headways: []time.Duration{0, 7 * time.Minute, 5 * time.Minute},
		},
		{
			Route:    route2,
			Headways: []time.Duration{0, 10 * time.Minute, 12 * time.Minute},
		},
	} {
		baseTime := startTime
		for i, headway := range data.Headways {
			baseTime = baseTime.Add(headway)
			data.Route.NewTrip(fmt.Sprintf("trip-%d", i), []dbtesting.StopTime{
				{
					Stop:    stop1,
					Arrival: baseTime,
				},
				{
					Stop:    stop2,
					Arrival: baseTime.Add(5 * time.Minute),
				},
				{
					Stop:    stop3,
					Arrival: baseTime.Add(15 * time.Minute),
				},
			})
		}
	}

	gotRows, err := querier.EstimateHeadwaysForRoutes(context.Background(), db.EstimateHeadwaysForRoutesParams{
		RoutePks:    []int64{route1.Data.Pk, route2.Data.Pk},
		PresentTime: pgtype.Timestamptz{Valid: true, Time: startTime},
	})
	querier.AssertNilErr(err, "EstimateHeadwaysForRoutes()")
	wantRows := []db.EstimateHeadwaysForRoutesRow{
		{
			RoutePk:          route1.Data.Pk,
			EstimatedHeadway: 6 * 60,
		},
		{
			RoutePk:          route2.Data.Pk,
			EstimatedHeadway: 11 * 60,
		},
	}
	if !reflect.DeepEqual(gotRows, wantRows) {
		t.Errorf("EstimateHeadwaysForRoutes() = %v, want = %v", gotRows, wantRows)
	}
}
