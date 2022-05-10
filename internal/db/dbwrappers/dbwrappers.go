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
