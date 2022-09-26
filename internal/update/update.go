// Package update implements the feed update functionality.
package update

import (
	"context"
	"crypto/md5"
	"database/sql"
	"fmt"
	"io"
	"log"
	"net/http"
	"time"

	"github.com/jackc/pgx/v4"
	"github.com/jackc/pgx/v4/pgxpool"
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
	"google.golang.org/protobuf/encoding/protojson"
)

func Do(ctx context.Context, pool *pgxpool.Pool, systemID, feedID string) error {
	var updatePk int64
	if err := pool.BeginTxFunc(ctx, pgx.TxOptions{}, func(tx pgx.Tx) error {
		var err error
		updatePk, err = createInExistingTx(ctx, db.New(tx), systemID, feedID)
		return err
	}); err != nil {
		return err
	}
	var updateErr error
	if err := pool.BeginTxFunc(ctx, pgx.TxOptions{}, func(tx pgx.Tx) error {
		// We don't return the error through the transaction function as we want to commit the feed update
		// result irrespective of whether it was success or failure.
		updateErr = runInExistingTx(ctx, db.New(tx), systemID, feedID, updatePk)
		return nil
	}); err != nil {
		log.Printf("Failed to commit feed update transaction: %s", err)
		// TODO: try to mark it as failed again
		return err
	}
	return updateErr
}

func DoInExistingTx(ctx context.Context, querier db.Querier, systemID, feedID string) error {
	updatePk, err := createInExistingTx(ctx, querier, systemID, feedID)
	if err != nil {
		return err
	}
	return runInExistingTx(ctx, querier, systemID, feedID, updatePk)
}

func createInExistingTx(ctx context.Context, querier db.Querier, systemID, feedID string) (int64, error) {
	log.Printf("Creating update for %s/%s\n", systemID, feedID)
	feed, err := querier.GetFeed(ctx, db.GetFeedParams{
		SystemID: systemID,
		FeedID:   feedID,
	})
	if err != nil {
		return 0, errors.NewNotFoundError(fmt.Sprintf("unknown feed %s/%s", systemID, feedID))
	}
	return querier.InsertFeedUpdate(ctx, db.InsertFeedUpdateParams{
		FeedPk:    feed.Pk,
		StartedAt: time.Now(),
	})
}

func runInExistingTx(ctx context.Context, querier db.Querier, systemID, feedID string, updatePk int64) error {
	r := run(ctx, querier, systemID, updatePk)

	contentLength := sql.NullInt32{}
	if r.ContentLength != -1 {
		contentLength = sql.NullInt32{Valid: true, Int32: r.ContentLength}
	}
	contentHash := sql.NullString{}
	if r.ContentHash != "" {
		contentHash = sql.NullString{Valid: true, String: r.ContentHash}
	}
	errorMessage := sql.NullString{}
	if r.Err != nil {
		log.Printf("Error during feed update: %s\n", r.Err)
		errorMessage = sql.NullString{Valid: true, String: r.Err.Error()}
	}
	if err := querier.FinishFeedUpdate(ctx, db.FinishFeedUpdateParams{
		UpdatePk:      updatePk,
		Result:        sql.NullString{Valid: true, String: r.Result},
		FinishedAt:    sql.NullTime{Valid: true, Time: time.Now()},
		ContentLength: contentLength,
		ContentHash:   contentHash,
		ErrorMessage:  errorMessage,
	}); err != nil {
		// TODO: we should rollback the transaction if this happens?
		log.Printf("Error while finishing feed update for pk=%d: %s\n", updatePk, r.Err)
		return err
	}

	monitoring.RecordFeedUpdate(systemID, feedID, r.Status, r.Result)
	if r.Err != nil {
		log.Printf("Error update for pk=%d: %s\n", updatePk, r.Err)
		return r.Err
	}
	return nil
}

type runResult struct {
	Status        string
	Result        string
	Err           error
	ContentLength int32
	ContentHash   string
}

func (r *runResult) markErr(result string, err error) {
	r.Status = constants.StatusFailure
	r.Result = result
	r.Err = err
}

func run(ctx context.Context, querier db.Querier, systemID string, updatePk int64) runResult {
	var r runResult
	r.ContentLength = -1
	feed, err := querier.GetFeedForUpdate(ctx, updatePk)
	if err != nil {
		r.markErr(constants.ResultInternalError, err)
		return r
	}
	var feedConfig api.FeedConfig
	if err := protojson.Unmarshal([]byte(feed.Config), &feedConfig); err != nil {
		r.markErr(constants.ResultInvalidFeedConfig, fmt.Errorf("failed to parse feed config: %w", err))
		return r
	}
	content, err := getFeedContent(ctx, systemID, &feedConfig)
	if err != nil {
		r.markErr(constants.ResultDownloadError, err)
		return r
	}
	r.ContentLength = int32(len(content))
	if len(content) == 0 {
		r.markErr(constants.ResultEmptyFeed, fmt.Errorf("empty feed content"))
		return r
	}
	r.ContentHash = calculateContentHash(content)
	lastContentHash, err := getLastContentHash(ctx, querier, feed.Pk)
	if err != nil {
		r.markErr(constants.ResultInternalError, err)
		return r
	}
	if r.ContentHash == lastContentHash {
		r.Status = constants.StatusSuccess
		r.Result = constants.ResultNotNeeded
		return r
	}
	updateCtx := common.UpdateContext{
		Querier:  querier,
		SystemPk: feed.SystemPk,
		FeedPk:   feed.Pk,
		UpdatePk: updatePk,
	}
	var parseErr error
	var updateErr error
	switch feedConfig.Parser {
	case "GTFS_STATIC":
		var data *gtfs.Static
		data, parseErr = static.Parse(content)
		if parseErr != nil {
			break
		}
		updateErr = static.Update(ctx, updateCtx, data)
	case "GTFS_REALTIME":
		var data *gtfs.Realtime
		data, parseErr = realtime.Parse(content, feedConfig.GtfsRealtimeOptions)
		if parseErr != nil {
			break
		}
		updateErr = realtime.Update(ctx, updateCtx, data)
	case "NYCT_SUBWAY_CSV":
		// TODO: parse error
		updateErr = nyctsubwaycsv.ParseAndUpdate(ctx, updateCtx, content)
	default:
		r.markErr(constants.ResultInvalidParser, fmt.Errorf("invalid feed parser %q", feedConfig.Parser))
		return r
	}
	if parseErr != nil {
		r.markErr(constants.ResultParseError, parseErr)
		return r
	}
	if updateErr != nil {
		r.markErr(constants.ResultUpdateError, updateErr)
		return r
	}
	r.Status = constants.StatusSuccess
	r.Result = constants.ResultUpdated
	return r
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

func calculateContentHash(content []byte) string {
	return fmt.Sprintf("%x", md5.Sum(content))
}

// TODO: move to wrappers and write DB tests
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
