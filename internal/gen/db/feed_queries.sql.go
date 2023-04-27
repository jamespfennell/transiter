// Code generated by sqlc. DO NOT EDIT.
// versions:
//   sqlc v1.17.2
// source: feed_queries.sql

package db

import (
	"context"

	"github.com/jackc/pgx/v5/pgtype"
)

const deleteFeed = `-- name: DeleteFeed :exec
DELETE FROM feed WHERE pk = $1
`

func (q *Queries) DeleteFeed(ctx context.Context, pk int64) error {
	_, err := q.db.Exec(ctx, deleteFeed, pk)
	return err
}

const getFeed = `-- name: GetFeed :one
SELECT feed.pk, feed.id, feed.system_pk, feed.update_strategy, feed.update_period, feed.config, feed.last_content_hash, feed.last_update, feed.last_successful_update, feed.last_skipped_update, feed.last_failed_update FROM feed
    INNER JOIN system on system.pk = feed.system_pk
    WHERE system.id = $1
    AND feed.id = $2
`

type GetFeedParams struct {
	SystemID string
	FeedID   string
}

func (q *Queries) GetFeed(ctx context.Context, arg GetFeedParams) (Feed, error) {
	row := q.db.QueryRow(ctx, getFeed, arg.SystemID, arg.FeedID)
	var i Feed
	err := row.Scan(
		&i.Pk,
		&i.ID,
		&i.SystemPk,
		&i.UpdateStrategy,
		&i.UpdatePeriod,
		&i.Config,
		&i.LastContentHash,
		&i.LastUpdate,
		&i.LastSuccessfulUpdate,
		&i.LastSkippedUpdate,
		&i.LastFailedUpdate,
	)
	return i, err
}

const insertFeed = `-- name: InsertFeed :exec
INSERT INTO feed
    (id, system_pk, update_strategy, update_period, config)
VALUES
    ($1, $2, $3, 
     $4, $5)
`

type InsertFeedParams struct {
	ID             string
	SystemPk       int64
	UpdateStrategy string
	UpdatePeriod   pgtype.Float8
	Config         string
}

func (q *Queries) InsertFeed(ctx context.Context, arg InsertFeedParams) error {
	_, err := q.db.Exec(ctx, insertFeed,
		arg.ID,
		arg.SystemPk,
		arg.UpdateStrategy,
		arg.UpdatePeriod,
		arg.Config,
	)
	return err
}

const listFeeds = `-- name: ListFeeds :many
SELECT pk, id, system_pk, update_strategy, update_period, config, last_content_hash, last_update, last_successful_update, last_skipped_update, last_failed_update FROM feed WHERE system_pk = $1 ORDER BY id
`

func (q *Queries) ListFeeds(ctx context.Context, systemPk int64) ([]Feed, error) {
	rows, err := q.db.Query(ctx, listFeeds, systemPk)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []Feed
	for rows.Next() {
		var i Feed
		if err := rows.Scan(
			&i.Pk,
			&i.ID,
			&i.SystemPk,
			&i.UpdateStrategy,
			&i.UpdatePeriod,
			&i.Config,
			&i.LastContentHash,
			&i.LastUpdate,
			&i.LastSuccessfulUpdate,
			&i.LastSkippedUpdate,
			&i.LastFailedUpdate,
		); err != nil {
			return nil, err
		}
		items = append(items, i)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return items, nil
}

const markFailedUpdate = `-- name: MarkFailedUpdate :exec
UPDATE feed
SET last_update = $1,
    last_failed_update = $1
WHERE pk = $2
`

type MarkFailedUpdateParams struct {
	UpdateTime pgtype.Timestamptz
	FeedPk     int64
}

func (q *Queries) MarkFailedUpdate(ctx context.Context, arg MarkFailedUpdateParams) error {
	_, err := q.db.Exec(ctx, markFailedUpdate, arg.UpdateTime, arg.FeedPk)
	return err
}

const markSkippedUpdate = `-- name: MarkSkippedUpdate :exec
UPDATE feed
SET last_update = $1,
    last_skipped_update = $1
WHERE pk = $2
`

type MarkSkippedUpdateParams struct {
	UpdateTime pgtype.Timestamptz
	FeedPk     int64
}

func (q *Queries) MarkSkippedUpdate(ctx context.Context, arg MarkSkippedUpdateParams) error {
	_, err := q.db.Exec(ctx, markSkippedUpdate, arg.UpdateTime, arg.FeedPk)
	return err
}

const markSuccessfulUpdate = `-- name: MarkSuccessfulUpdate :exec
UPDATE feed
SET last_content_hash = $1,
    last_update = $2,
    last_successful_update = $2
WHERE pk = $3
`

type MarkSuccessfulUpdateParams struct {
	ContentHash pgtype.Text
	UpdateTime  pgtype.Timestamptz
	FeedPk      int64
}

func (q *Queries) MarkSuccessfulUpdate(ctx context.Context, arg MarkSuccessfulUpdateParams) error {
	_, err := q.db.Exec(ctx, markSuccessfulUpdate, arg.ContentHash, arg.UpdateTime, arg.FeedPk)
	return err
}

const updateFeed = `-- name: UpdateFeed :exec
UPDATE feed
SET update_strategy = $1,
    update_period = $2, 
    config = $3
WHERE pk = $4
`

type UpdateFeedParams struct {
	UpdateStrategy string
	UpdatePeriod   pgtype.Float8
	Config         string
	FeedPk         int64
}

func (q *Queries) UpdateFeed(ctx context.Context, arg UpdateFeedParams) error {
	_, err := q.db.Exec(ctx, updateFeed,
		arg.UpdateStrategy,
		arg.UpdatePeriod,
		arg.Config,
		arg.FeedPk,
	)
	return err
}
