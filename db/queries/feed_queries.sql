-- name: ListFeedsInSystem :many
SELECT * FROM feed WHERE system_pk = $1 ORDER BY id;

-- name: GetFeedInSystem :one
SELECT feed.* FROM feed
    INNER JOIN system ON feed.system_pk = system.pk
    WHERE system.id = sqlc.arg(system_id)
    AND feed.id = sqlc.arg(feed_id);

-- name: GetFeedForUpdate :one
SELECT feed.* FROM feed
    INNER JOIN feed_update ON feed_update.feed_pk = feed.pk
    WHERE feed_update.pk = sqlc.arg(update_pk);

-- name: InsertFeed :exec
INSERT INTO feed
    (id, system_pk, periodic_update_enabled, periodic_update_period, config)
VALUES
    (sqlc.arg(id), sqlc.arg(system_pk), sqlc.arg(periodic_update_enabled), 
     sqlc.arg(periodic_update_period), sqlc.arg(config));

-- name: UpdateFeed :exec
UPDATE feed
SET periodic_update_enabled = sqlc.arg(periodic_update_enabled), 
    periodic_update_period = sqlc.arg(periodic_update_period), 
    config = sqlc.arg(config)
WHERE pk = sqlc.arg(feed_pk);

-- name: DeleteFeed :exec
DELETE FROM feed WHERE pk = sqlc.arg(pk);

-- name: ListAutoUpdateFeedsForSystem :many
SELECT feed.id, feed.periodic_update_period
FROM feed
    INNER JOIN system ON system.pk = feed.system_pk
WHERE feed.periodic_update_enabled
    AND system.id = sqlc.arg(system_id);

-- name: InsertFeedUpdate :one
INSERT INTO feed_update
    (feed_pk, status, started_at)
VALUES
    (sqlc.arg(feed_pk), sqlc.arg(status), sqlc.arg(started_at))
RETURNING pk;

-- name: GetLastFeedUpdateContentHash :one
SELECT content_hash
FROM feed_update
WHERE feed_pk = sqlc.arg(feed_pk) AND status = 'SUCCESS'
ORDER BY ended_at DESC
LIMIT 1;

-- name: FinishFeedUpdate :exec
UPDATE feed_update
SET status = sqlc.arg(status),
    result = sqlc.arg(result),
    ended_at = sqlc.arg(ended_at),
    content_length = sqlc.arg(content_length),
    content_hash = sqlc.arg(content_hash),
    error_message = sqlc.arg(error_message)
WHERE pk = sqlc.arg(update_pk);
