// Package dbwrappers contains methods that wrap the raw methods generated by sqlc and provide a nicer API.
package dbwrappers

import (
	"context"
	"log"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/jamespfennell/transiter/internal/gen/db"
)

func MapStopPkToDescendentPks(ctx context.Context, querier db.Querier, stopPks []int64) (map[int64]map[int64]bool, error) {
	rows, err := querier.MapStopPkToDescendentPks(ctx, stopPks)
	if err != nil {
		return nil, err
	}
	result := map[int64]map[int64]bool{}
	for _, row := range rows {
		if _, ok := result[row.RootStopPk]; !ok {
			result[row.RootStopPk] = map[int64]bool{}
		}
		result[row.RootStopPk][row.DescendentStopPk] = true
	}
	return result, nil
}

func MapStopIDToStationPk(ctx context.Context, querier db.Querier, systemPk int64) (map[string]int64, error) {
	rows, err := querier.MapStopIDAndPkToStationPk(ctx, db.MapStopIDAndPkToStationPkParams{SystemPk: systemPk})
	if err != nil {
		return nil, err
	}
	result := map[string]int64{}
	for _, row := range rows {
		result[row.StopID] = row.StationPk
	}
	return result, nil
}

func MapStopPkToStationPk(ctx context.Context, querier db.Querier, systemPk int64, stopPks []int64) (map[int64]int64, error) {
	rows, err := querier.MapStopIDAndPkToStationPk(ctx, db.MapStopIDAndPkToStationPkParams{
		SystemPk:       systemPk,
		FilterByStopPk: true,
		StopPks:        stopPks,
	})
	if err != nil {
		return nil, err
	}
	result := map[int64]int64{}
	for _, row := range rows {
		result[row.StopPk] = row.StationPk
	}
	return result, nil
}

func MapAgencyIDToPk(ctx context.Context, querier db.Querier, systemPk int64) (map[string]int64, error) {
	rows, err := querier.MapAgencyPkToId(ctx, systemPk)
	if err != nil {
		return nil, err
	}
	result := map[string]int64{}
	for _, row := range rows {
		result[row.ID] = row.Pk
	}
	return result, nil
}

func MapStopPkToChildPks(ctx context.Context, querier db.Querier, stopPks []int64) (map[int64][]int64, error) {
	rows, err := querier.MapStopPkToChildPks(ctx, stopPks)
	if err != nil {
		return nil, err
	}
	m := map[int64][]int64{}
	for _, row := range rows {
		m[row.ParentPk.Int64] = append(m[row.ParentPk.Int64], row.ChildPk)
	}
	return m, nil
}

func MapStopIDToPkInSystem(ctx context.Context, querier db.Querier, systemPk int64, stopIDs ...[]string) (map[string]int64, error) {
	var queryStopIDs []string
	if len(stopIDs) > 0 {
		queryStopIDs = stopIDs[0]
	}
	rows, err := querier.MapStopIDToPk(ctx, db.MapStopIDToPkParams{
		SystemPk:       systemPk,
		FilterByStopID: len(stopIDs) > 0,
		StopIds:        queryStopIDs,
	})
	if err != nil {
		return nil, err
	}
	result := map[string]int64{}
	for _, row := range rows {
		result[row.ID] = row.Pk
	}
	return result, nil
}

func MapRouteIDToPkInSystem(ctx context.Context, querier db.Querier, systemPk int64, routeIDs ...[]string) (map[string]int64, error) {
	var queryRouteIDs []string
	if len(routeIDs) > 0 {
		queryRouteIDs = routeIDs[0]
	}
	rows, err := querier.MapRouteIDToPkInSystem(ctx, db.MapRouteIDToPkInSystemParams{
		SystemPk:        systemPk,
		FilterByRouteID: len(routeIDs) > 0,
		RouteIds:        queryRouteIDs,
	})
	if err != nil {
		return nil, err
	}
	result := map[string]int64{}
	for _, row := range rows {
		result[row.ID] = row.Pk
	}
	return result, nil
}

type TripUID struct {
	ID      string
	RoutePk int64
}

func ListTripsForUpdate(ctx context.Context, querier db.Querier, routePks []int64) (map[TripUID]db.ListTripsForUpdateRow, error) {
	rows, err := querier.ListTripsForUpdate(ctx, routePks)
	if err != nil {
		return nil, err
	}
	m := map[TripUID]db.ListTripsForUpdateRow{}
	for _, row := range rows {
		uid := TripUID{RoutePk: row.RoutePk, ID: row.ID}
		m[uid] = row
	}
	return m, nil
}

func ListStopTimesForUpdate(ctx context.Context, querier db.Querier, tripUIDToPk map[TripUID]int64) (map[TripUID][]db.ListTripStopTimesForUpdateRow, error) {
	var tripPks []int64
	tripPkToUID := map[int64]TripUID{}
	for uid, pk := range tripUIDToPk {
		tripPks = append(tripPks, pk)
		tripPkToUID[pk] = uid
	}
	rows, err := querier.ListTripStopTimesForUpdate(ctx, tripPks)
	if err != nil {
		return nil, err
	}
	m := map[TripUID][]db.ListTripStopTimesForUpdateRow{}
	for _, row := range rows {
		uid := tripPkToUID[row.TripPk]
		m[uid] = append(m[uid], row)
	}
	return m, nil
}

func Ping(ctx context.Context, pool *pgxpool.Pool, numRetries int, waitBetweenPings time.Duration) error {
	var err error
	for i := 0; i < numRetries; i++ {
		err = pool.Ping(ctx)
		if err == nil {
			log.Printf("Database ping successful")
			break
		}
		log.Printf("Failed to ping the database: %s\n", err)
		if i != numRetries-1 {
			log.Printf("Will try to ping again in %s", waitBetweenPings)
			time.Sleep(waitBetweenPings)
		}
	}
	return err
}

type batchResult interface {
	Exec(f func(i int, err error))
}

func BatchUpdate[T any, S batchResult](ctx context.Context, f func(ctx context.Context, args []T) S, args []T) error {
	var err error
	f(ctx, args).Exec(func(i int, rowErr error) {
		if rowErr != nil {
			err = rowErr
		}
	})
	return err
}
