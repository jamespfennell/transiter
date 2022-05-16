package dbwrappers

import (
	"context"
	"log"
	"time"

	"github.com/jackc/pgx/v4/pgxpool"
	"github.com/jamespfennell/transiter/internal/gen/db"
)

func MapStopIdToStationPk(ctx context.Context, querier db.Querier, systemPk int64) (map[string]int64, error) {
	rows, err := querier.MapStopIdToStationPk(ctx, systemPk)
	if err != nil {
		return nil, err
	}
	result := map[string]int64{}
	for _, row := range rows {
		result[row.StopID] = row.StationPk
	}
	return result, nil
}

func MapStopIdToPkInSystem(ctx context.Context, querier db.Querier, systemPk int64, stopIds []string) (map[string]int64, error) {
	rows, err := querier.MapStopsInSystem(ctx, db.MapStopsInSystemParams{
		SystemPk: systemPk,
		StopIds:  stopIds,
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

func MapRouteIdToPkInSystem(ctx context.Context, querier db.Querier, systemPk int64, routeIds []string) (map[string]int64, error) {
	rows, err := querier.MapRoutesInSystem(ctx, db.MapRoutesInSystemParams{
		SystemPk: systemPk,
		RouteIds: routeIds,
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
	Id      string
	RoutePk int64
}

type TripForUpdate struct {
	Pk        int64
	Id        string
	RoutePk   int64
	StopTimes []StopTimeForUpdate
}

type StopTimeForUpdate struct {
	Pk           int64
	StopPk       int64
	StopSequence int32
	Past         bool
}

func ListTripsForUpdate(ctx context.Context, querier db.Querier, feedPk int64, routePks []int64) (map[TripUID]*TripForUpdate, error) {
	tripRows, err := querier.ListTripsForUpdate(ctx, db.ListTripsForUpdateParams{
		FeedPk:   feedPk,
		RoutePks: routePks,
	})
	if err != nil {
		return nil, err
	}
	result := map[TripUID]*TripForUpdate{}
	tripPkToUid := map[int64]TripUID{}
	var tripPks []int64
	for _, tripRow := range tripRows {
		uid := TripUID{RoutePk: tripRow.RoutePk, Id: tripRow.ID}
		tripPks = append(tripPks, tripRow.Pk)
		tripPkToUid[tripRow.Pk] = uid
		result[uid] = &TripForUpdate{
			Pk:      tripRow.Pk,
			Id:      tripRow.ID,
			RoutePk: tripRow.RoutePk,
		}
	}
	stopTimeRows, err := querier.ListTripStopTimesForUpdate(ctx, tripPks)
	if err != nil {
		return nil, err
	}
	for _, stopTimeRow := range stopTimeRows {
		uid := tripPkToUid[stopTimeRow.TripPk]
		tripForUpdate := result[uid]
		tripForUpdate.StopTimes = append(tripForUpdate.StopTimes, StopTimeForUpdate{
			Pk:           stopTimeRow.Pk,
			StopPk:       stopTimeRow.StopPk,
			StopSequence: stopTimeRow.StopSequence,
			Past:         stopTimeRow.Past,
		})
		result[uid] = tripForUpdate
	}
	return result, nil
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
