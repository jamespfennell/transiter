// Package update implements the feed update mechanism.
package update

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/jamespfennell/gtfs"
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
	"google.golang.org/protobuf/proto"
)

const (
	NyctSubwayCsv = "NYCT_SUBWAY_CSV"
	GtfsRealtime  = "GTFS_REALTIME"
	GtfsStatic    = "GTFS_STATIC"
)

func NormalizeFeedConfig(feedConfig *api.FeedConfig) {
	if t := feedConfig.GetType(); t == "" {
		//lint:ignore SA1019 this is where we apply the deprecation logic!
		feedConfig.Type = feedConfig.GetParser()
	}
	if feedConfig.RequiredForInstall == nil {
		b := feedConfig.Type != GtfsRealtime
		feedConfig.RequiredForInstall = &b
	}
}

func Update(ctx context.Context, logger *slog.Logger, pool *pgxpool.Pool, m monitoring.Monitoring, systemID, feedID string, force bool) (*api.FeedUpdate, error) {
	startTime := time.Now()
	updateID := uuid.New().String()
	logger = logger.With(slog.String("system_id", systemID), slog.String("feed_id", feedID), slog.String("update_id", updateID))
	logger.DebugCtx(ctx, "starting feed update")

	var feed db.Feed
	if err := pgx.BeginTxFunc(ctx, pool, pgx.TxOptions{}, func(tx pgx.Tx) error {
		var err error
		feed, err = db.New(tx).GetFeed(ctx, db.GetFeedParams{
			SystemID: systemID,
			FeedID:   feedID,
		})
		if err == pgx.ErrNoRows {
			return errors.NewNotFoundError(fmt.Sprintf("unknown feed %s/%s", systemID, feedID))
		}
		return err
	}); err != nil {
		logger.ErrorCtx(ctx, fmt.Sprintf("failed to start new feed update: %s", err))
		return nil, err
	}

	feedUpdate, err := run(ctx, pool, logger, systemID, feed, force)
	feedUpdate.UpdateId = updateID
	feedUpdate.StartedAtMs = startTime.UnixMilli()

	finishTime := time.Now()
	finishTimeMs := finishTime.UnixMilli()
	feedUpdate.FinishedAtMs = &finishTimeMs

	switch feedUpdate.GetStatus() {
	case api.FeedUpdate_UPDATED:
		// Nothing to do: the feed update time is updated in the update transaction itself.
	case api.FeedUpdate_SKIPPED:
		if err := db.New(pool).MarkSkippedUpdate(ctx, db.MarkSkippedUpdateParams{
			FeedPk:     feed.Pk,
			UpdateTime: pgtype.Timestamptz{Valid: true, Time: finishTime},
		}); err != nil {
			logger.ErrorCtx(ctx, fmt.Sprintf("failed to mark skipped update: %s", err))
		}
	default:
		if err := db.New(pool).MarkFailedUpdate(ctx, db.MarkFailedUpdateParams{
			FeedPk:     feed.Pk,
			UpdateTime: pgtype.Timestamptz{Valid: true, Time: finishTime},
		}); err != nil {
			logger.ErrorCtx(ctx, fmt.Sprintf("failed to mark failed update: %s", err))
		}
	}

	totalLatency := finishTime.Sub(startTime)
	totalLatencyMs := totalLatency.Milliseconds()
	feedUpdate.TotalLatencyMs = &totalLatencyMs
	if err != nil {
		logger.ErrorCtx(ctx, fmt.Sprintf("failed update with reason %s and error %s in %s", feedUpdate.Status.String(), err, totalLatency))
	} else {
		logger.DebugCtx(ctx, fmt.Sprintf("successful update with reason %s in %s", feedUpdate.Status.String(), totalLatency))
	}
	m.RecordFeedUpdate(systemID, feedID, feedUpdate)
	return feedUpdate, err
}

func markFailure(feedUpdate *api.FeedUpdate, status api.FeedUpdate_Status, err error) (*api.FeedUpdate, error) {
	feedUpdate.Status = status
	errMsg := err.Error()
	feedUpdate.ErrorMessage = &errMsg
	return feedUpdate, err
}

func markSuccess(feedUpdate *api.FeedUpdate, status api.FeedUpdate_Status) (*api.FeedUpdate, error) {
	feedUpdate.Status = status
	return feedUpdate, nil
}

func run(ctx context.Context, pool *pgxpool.Pool, logger *slog.Logger, systemID string, feed db.Feed, force bool) (*api.FeedUpdate, error) {
	feedUpdate := &api.FeedUpdate{}
	var feedConfig api.FeedConfig
	if err := protojson.Unmarshal([]byte(feed.Config), &feedConfig); err != nil {
		return markFailure(feedUpdate, api.FeedUpdate_FAILED_INVALID_FEED_CONFIG, fmt.Errorf("failed to parse feed config: %w", err))
	}
	NormalizeFeedConfig(&feedConfig)
	feedUpdate.FeedConfig = &feedConfig
	content, err := getFeedContent(ctx, systemID, &feedConfig, feedUpdate)
	if err != nil {
		return markFailure(feedUpdate, api.FeedUpdate_FAILED_DOWNLOAD_ERROR, err)
	}
	contentLength := int32(len(content))
	feedUpdate.ContentLength = &contentLength
	if len(content) == 0 {
		return markFailure(feedUpdate, api.FeedUpdate_FAILED_EMPTY_FEED, fmt.Errorf("empty feed content"))
	}
	contentHash := common.HashBytes(content)
	feedUpdate.ContentHash = &contentHash
	if feed.LastContentHash.Valid && feed.LastContentHash.String == contentHash && !force {
		return markSuccess(feedUpdate, api.FeedUpdate_SKIPPED)
	}

	var p interface {
		parse(b []byte, feedUpdate *api.FeedUpdate) error
		update(ctx context.Context, updateCtx common.UpdateContext, feedUpdate *api.FeedUpdate) error
	}
	switch feedConfig.Type {
	case GtfsStatic:
		p = &parserAndUpdater[*gtfs.Static]{
			parseFn:  static.Parse,
			updateFn: static.Update,
		}
	case GtfsRealtime:
		p = &parserAndUpdater[*gtfs.Realtime]{
			parseFn: func(b []byte) (*gtfs.Realtime, error) {
				return realtime.Parse(b, feedConfig.GtfsRealtimeOptions)
			},
			updateFn: realtime.Update,
		}
	case NyctSubwayCsv:
		p = &parserAndUpdater[[]nyctsubwaycsv.StopHeadsignRule]{
			parseFn:  nyctsubwaycsv.Parse,
			updateFn: nyctsubwaycsv.Update,
		}
	default:
		return markFailure(feedUpdate, api.FeedUpdate_FAILED_UNKNOWN_FEED_TYPE, fmt.Errorf("unknown feed type %q", feedConfig.Type))
	}
	if err := p.parse(content, feedUpdate); err != nil {
		return markFailure(feedUpdate, api.FeedUpdate_FAILED_PARSE_ERROR, err)
	}

	if err := pgx.BeginTxFunc(ctx, pool, pgx.TxOptions{}, func(tx pgx.Tx) error {
		updateCtx := common.UpdateContext{
			Querier:    db.New(tx),
			Logger:     logger,
			SystemPk:   feed.SystemPk,
			FeedPk:     feed.Pk,
			FeedConfig: &feedConfig,
		}
		if err := p.update(ctx, updateCtx, feedUpdate); err != nil {
			return err
		}
		return updateCtx.Querier.MarkSuccessfulUpdate(ctx, db.MarkSuccessfulUpdateParams{
			FeedPk:      updateCtx.FeedPk,
			ContentHash: pgtype.Text{Valid: true, String: contentHash},
			UpdateTime:  pgtype.Timestamptz{Valid: true, Time: time.Now()},
		})
	}); err != nil {
		return markFailure(feedUpdate, api.FeedUpdate_FAILED_UPDATE_ERROR, err)
	}
	return markSuccess(feedUpdate, api.FeedUpdate_UPDATED)
}

// parserAndUpdater is a helper type for linking the parse and update steps together in
// a type safe way.
type parserAndUpdater[T any] struct {
	parseFn   func(b []byte) (T, error)
	updateFn  func(context.Context, common.UpdateContext, T) error
	parsedVal T
}

func (p *parserAndUpdater[T]) parse(b []byte, feedUpdate *api.FeedUpdate) error {
	start := time.Now()
	var err error
	p.parsedVal, err = p.parseFn(b)
	feedUpdate.ParseLatencyMs = proto.Int64(time.Since(start).Milliseconds())
	return err
}

func (p *parserAndUpdater[T]) update(ctx context.Context, updateCtx common.UpdateContext, feedUpdate *api.FeedUpdate) error {
	start := time.Now()
	err := p.updateFn(ctx, updateCtx, p.parsedVal)
	feedUpdate.DatabaseLatencyMs = proto.Int64(time.Since(start).Milliseconds())
	return err
}

func getFeedContent(ctx context.Context, systemID string, feedConfig *api.FeedConfig, feedUpdate *api.FeedUpdate) ([]byte, error) {
	start := time.Now()
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
	feedUpdate.DownloadHttpStatusCode = proto.Int32(int32(resp.StatusCode))
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("HTTP request for %s/%s returned non-ok status %s", systemID, feedConfig.Id, resp.Status)
	}
	b, err := io.ReadAll(resp.Body)
	feedUpdate.DownloadLatencyMs = proto.Int64(time.Since(start).Milliseconds())
	return b, err
}
