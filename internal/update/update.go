// Package update implements the feed update functionality.
package update

import (
	"context"
	"fmt"
	"io"
	"log"
	"net/http"
	"time"

	"github.com/jackc/pgx/v4"
	"github.com/jackc/pgx/v4/pgxpool"
	"github.com/jamespfennell/gtfs"
	"github.com/jamespfennell/transiter/config"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/public/errors"
	"github.com/jamespfennell/transiter/internal/update/common"
	"github.com/jamespfennell/transiter/internal/update/realtime"
	"github.com/jamespfennell/transiter/internal/update/static"
)

func CreateAndRun(ctx context.Context, pool *pgxpool.Pool, systemID, feedID string) error {
	var updatePk int64
	if err := pool.BeginTxFunc(ctx, pgx.TxOptions{}, func(tx pgx.Tx) error {
		var err error
		updatePk, err = CreateInExistingTx(ctx, db.New(tx), systemID, feedID)
		return err
	}); err != nil {
		return err
	}
	// TODO: mark update as IN_PROGRESS / FAILED / etc
	return pool.BeginTxFunc(ctx, pgx.TxOptions{}, func(tx pgx.Tx) error {
		return RunInExistingTx(ctx, db.New(tx), systemID, updatePk)
	})
}

func CreateAndRunInExistingTx(ctx context.Context, querier db.Querier, systemID, feedID string) error {
	updatePk, err := CreateInExistingTx(ctx, querier, systemID, feedID)
	if err != nil {
		return err
	}
	return RunInExistingTx(ctx, querier, systemID, updatePk)
}

func CreateInExistingTx(ctx context.Context, querier db.Querier, systemID, feedID string) (int64, error) {
	log.Printf("Creating update for %s/%s\n", systemID, feedID)
	feed, err := querier.GetFeedInSystem(ctx, db.GetFeedInSystemParams{
		SystemID: systemID,
		FeedID:   feedID,
	})
	if err != nil {
		return 0, errors.NewNotFoundError(fmt.Sprintf("unknown feed %s/%s", systemID, feedID))
	}
	return querier.InsertFeedUpdate(ctx, db.InsertFeedUpdateParams{
		FeedPk: feed.Pk,
		Status: "CREATED",
	})
}

func RunInExistingTx(ctx context.Context, querier db.Querier, systemID string, updatePk int64) error {
	feed, err := querier.GetFeedForUpdate(ctx, updatePk)
	if err != nil {
		log.Printf("Error update for pk=%d\n", updatePk)
		return err
	}
	feedConfig, err := config.UnmarshalFromJSON([]byte(feed.Config))
	if err != nil {
		return fmt.Errorf("failed to parse feed config in the DB: %w", err)
	}
	content, err := getFeedContent(ctx, systemID, feedConfig)
	if err != nil {
		return err
	}
	updateCtx := common.UpdateContext{
		Querier:  querier,
		SystemPk: feed.SystemPk,
		FeedPk:   feed.Pk,
		UpdatePk: updatePk,
	}
	switch feedConfig.Parser {
	case config.GtfsStatic:
		// TODO: support custom GTFS static options
		parsedEntities, err := gtfs.ParseStatic(content, gtfs.ParseStaticOptions{})
		if err != nil {
			return err
		}
		return static.Update(ctx, updateCtx, parsedEntities)
	case config.GtfsRealtime:
		// TODO: support custom GTFS realtime options
		parsedEntities, err := gtfs.ParseRealtime(content, &gtfs.ParseRealtimeOptions{
			UseNyctExtension: true,
		})
		if err != nil {
			return err
		}
		return realtime.Update(ctx, updateCtx, parsedEntities)
	default:
		return fmt.Errorf("unknown parser %q", feedConfig.Parser)
	}
}

func getFeedContent(ctx context.Context, systemID string, feedConfig *config.FeedConfig) ([]byte, error) {
	client := http.Client{
		Timeout: 5 * time.Second,
	}
	if feedConfig.HTTPTimeout != nil {
		client.Timeout = *feedConfig.HTTPTimeout
	}
	req, err := http.NewRequestWithContext(ctx, "GET", feedConfig.URL, nil)
	if err != nil {
		return nil, err
	}
	for key, value := range feedConfig.HTTPHeaders {
		req.Header.Add(key, value)
	}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("HTTP request for %s/%s returned non-ok status %s", systemID, feedConfig.ID, resp.Status)
	}
	return io.ReadAll(resp.Body)
}
