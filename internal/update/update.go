// Package update implements the feed update mechanism.
package update

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/jamespfennell/gtfs"
	"github.com/jamespfennell/transiter/internal/db/constants"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/monitoring"
	"github.com/jamespfennell/transiter/internal/public/errors"
	"github.com/jamespfennell/transiter/internal/update/common"
	"github.com/jamespfennell/transiter/internal/update/nyctsubwaycsv"
	"github.com/jamespfennell/transiter/internal/update/realtime"
	"github.com/jamespfennell/transiter/internal/update/static"
	"golang.org/x/exp/slog"
	"google.golang.org/protobuf/encoding/protojson"
)

func Update(ctx context.Context, logger *slog.Logger, pool *pgxpool.Pool, systemID, feedID string) error {
	startTime := time.Now()
	logger = logger.With(slog.String("system_id", systemID), slog.String("feed_id", feedID))
	logger.DebugCtx(ctx, "starting feed update")

	// DB transaction 1: insert the update. If this fails no database artifacts will be left.
	var feed db.Feed
	var feedUpdate db.FeedUpdate
	var lastContentHash string
	if err := pgx.BeginTxFunc(ctx, pool, pgx.TxOptions{}, func(tx pgx.Tx) error {
		var err error
		feed, feedUpdate, lastContentHash, err = createUpdate(ctx, db.New(tx), systemID, feedID)
		return err
	}); err != nil {
		logger.ErrorCtx(ctx, fmt.Sprintf("failed to insert new feed update: %s", err))
		return err
	}
	logger = logger.With(slog.Int64("update_id", feedUpdate.Pk))

	// DB transaction 2: perform the update. If this fails any database changes are rolled back.
	//
	// This is in a separate transaction to (1) because the first steps of performing an update
	// don't require a database connection and may take a long time.
	// These steps include downloading the feed data (theoretically unbounded, though we enforce a timeout)
	// and parsing the feed (for the Brooklyn MTA buses this is over a second).
	// By not holding a transaction open we reduce the risk that this transaction, or another incompatible
	// concurrent transaction, will fail.
	//
	// Moreover this enables us to have asynchronous updates in the future, if we want.
	err := run(ctx, pool, logger, systemID, feed, &feedUpdate, lastContentHash)

	// DB transaction 3: commit the result of the update.
	//
	// This is a separate transaction to (2) because in the case when the update fails we want to
	// rollback the update itself but commit the failure result.
	if commitErr := pgx.BeginTxFunc(ctx, pool, pgx.TxOptions{}, func(tx pgx.Tx) error {
		querier := db.New(tx)
		return querier.FinishFeedUpdate(ctx, db.FinishFeedUpdateParams{
			UpdatePk:      feedUpdate.Pk,
			Result:        feedUpdate.Result,
			FinishedAt:    pgtype.Timestamptz{Valid: true, Time: time.Now()},
			ContentLength: feedUpdate.ContentLength,
			ContentHash:   feedUpdate.ContentHash,
			ErrorMessage:  feedUpdate.ErrorMessage,
		})
	}); commitErr != nil {
		logger.ErrorCtx(ctx, fmt.Sprintf("failed to commit finish feed update transaction (this is really bad!): %s", commitErr))
		if err == nil {
			err = commitErr
		}
	}

	status := "SUCCESS"
	if err != nil {
		logger.ErrorCtx(ctx, fmt.Sprintf("update failed with reason %s and error %s", feedUpdate.Result.String, err))
		status = "FAILURE"
	}
	monitoring.RecordFeedUpdate(systemID, feedID, status, feedUpdate.Result.String, time.Since(startTime))
	logger.DebugCtx(ctx, fmt.Sprintf("finished update with result %s in %s", feedUpdate.Result.String, time.Since(startTime)))
	return err
}

func createUpdate(ctx context.Context, querier db.Querier, systemID, feedID string) (db.Feed, db.FeedUpdate, string, error) {
	feed, err := querier.GetFeed(ctx, db.GetFeedParams{
		SystemID: systemID,
		FeedID:   feedID,
	})
	if err != nil {
		return db.Feed{}, db.FeedUpdate{}, "", errors.NewNotFoundError(fmt.Sprintf("unknown feed %s/%s", systemID, feedID))
	}
	lastContentHash, err := getLastContentHash(ctx, querier, feed.Pk)
	if err != nil {
		return db.Feed{}, db.FeedUpdate{}, "", err
	}
	feedUpdate, err := querier.InsertFeedUpdate(ctx, db.InsertFeedUpdateParams{
		FeedPk:    feed.Pk,
		StartedAt: pgtype.Timestamptz{Valid: true, Time: time.Now()},
	})
	if err != nil {
		return db.Feed{}, db.FeedUpdate{}, "", err
	}
	return feed, feedUpdate, lastContentHash, nil
}

func markFailure(feedUpdate *db.FeedUpdate, result string, err error) error {
	feedUpdate.Result = pgtype.Text{Valid: true, String: result}
	feedUpdate.ErrorMessage = pgtype.Text{Valid: true, String: err.Error()}
	return err
}

func markSuccess(feedUpdate *db.FeedUpdate, result string) error {
	feedUpdate.Result = pgtype.Text{Valid: true, String: result}
	return nil
}

func run(ctx context.Context, pool *pgxpool.Pool, logger *slog.Logger, systemID string, feed db.Feed, feedUpdate *db.FeedUpdate, lastContentHash string) error {
	var feedConfig api.FeedConfig
	if err := protojson.Unmarshal([]byte(feed.Config), &feedConfig); err != nil {
		return markFailure(feedUpdate, constants.ResultInvalidFeedConfig, fmt.Errorf("failed to parse feed config: %w", err))
	}
	content, err := getFeedContent(ctx, systemID, &feedConfig)
	if err != nil {
		return markFailure(feedUpdate, constants.ResultDownloadError, err)
	}
	feedUpdate.ContentLength = pgtype.Int4{Valid: true, Int32: int32(len(content))}
	if len(content) == 0 {
		return markFailure(feedUpdate, constants.ResultEmptyFeed, fmt.Errorf("empty feed content"))
	}
	contentHash := common.HashBytes(content)
	feedUpdate.ContentHash = pgtype.Text{Valid: true, String: contentHash}
	if contentHash == lastContentHash {
		return markSuccess(feedUpdate, constants.ResultNotNeeded)
	}

	var p interface {
		parse(b []byte) error
		update(ctx context.Context, updateCtx common.UpdateContext) error
	}
	switch feedConfig.Parser {
	case "GTFS_STATIC":
		p = &parserAndUpdater[*gtfs.Static]{
			parseFn:  static.Parse,
			updateFn: static.Update,
		}
	case "GTFS_REALTIME":
		p = &parserAndUpdater[*gtfs.Realtime]{
			parseFn: func(b []byte) (*gtfs.Realtime, error) {
				return realtime.Parse(b, feedConfig.GtfsRealtimeOptions)
			},
			updateFn: realtime.Update,
		}
	case "NYCT_SUBWAY_CSV":
		p = &parserAndUpdater[[]nyctsubwaycsv.StopHeadsignRule]{
			parseFn:  nyctsubwaycsv.Parse,
			updateFn: nyctsubwaycsv.Update,
		}
	default:
		return markFailure(feedUpdate, constants.ResultInvalidParser, fmt.Errorf("invalid feed parser %q", feedConfig.Parser))
	}
	if err := p.parse(content); err != nil {
		return markFailure(feedUpdate, constants.ResultParseError, err)
	}

	if err := pgx.BeginTxFunc(ctx, pool, pgx.TxOptions{}, func(tx pgx.Tx) error {
		updateCtx := common.UpdateContext{
			Querier:    db.New(tx),
			Logger:     logger,
			SystemPk:   feed.SystemPk,
			FeedPk:     feed.Pk,
			UpdatePk:   feedUpdate.Pk,
			FeedConfig: &feedConfig,
		}
		return p.update(ctx, updateCtx)
	}); err != nil {
		return markFailure(feedUpdate, constants.ResultUpdateError, err)
	}
	return markSuccess(feedUpdate, constants.ResultUpdated)
}

// parserAndUpdater is a helper type for linking the parse and update steps together in
// a type safe way.
type parserAndUpdater[T any] struct {
	parseFn   func(b []byte) (T, error)
	updateFn  func(context.Context, common.UpdateContext, T) error
	parsedVal T
}

func (p *parserAndUpdater[T]) parse(b []byte) error {
	var err error
	p.parsedVal, err = p.parseFn(b)
	return err
}

func (p *parserAndUpdater[T]) update(ctx context.Context, updateCtx common.UpdateContext) error {
	return p.updateFn(ctx, updateCtx, p.parsedVal)
}

func getFeedContent(ctx context.Context, systemID string, feedConfig *api.FeedConfig) ([]byte, error) {
	client := http.Client{
		Timeout: 5 * time.Second,
	}
	if feedConfig.RequestTimeoutMs != nil {
		client.Timeout = time.Duration(*feedConfig.RequestTimeoutMs) * time.Millisecond
	}
	req, err := http.NewRequestWithContext(ctx, "GET", feedConfig.Url, nil)
	if err != nil {
		return nil, err
	}
	for key, value := range feedConfig.HttpHeaders {
		req.Header.Add(key, value)
	}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("HTTP request for %s/%s returned non-ok status %s", systemID, feedConfig.Id, resp.Status)
	}
	return io.ReadAll(resp.Body)
}

func getLastContentHash(ctx context.Context, querier db.Querier, feedPk int64) (string, error) {
	hash, err := querier.GetLastFeedUpdateContentHash(ctx, feedPk)
	if err != nil {
		if err == pgx.ErrNoRows {
			return "", nil
		}
		return "", err
	}
	return hash.String, nil
}
