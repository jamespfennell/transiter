-- name: ListFeeds :many
SELECT * FROM feed WHERE system_pk = $1 ORDER BY id;

-- name: GetFeed :one
SELECT feed.* FROM feed
    INNER JOIN system on system.pk = feed.system_pk
    WHERE system.id = sqlc.arg(system_id)
    AND feed.id = sqlc.arg(feed_id);

-- name: GetFeedForUpdate :one
SELECT feed.* FROM feed
    INNER JOIN feed_update ON feed_update.feed_pk = feed.pk
    WHERE feed_update.pk = sqlc.arg(update_pk);

-- name: InsertFeed :exec
INSERT INTO feed
    (id, system_pk, update_strategy, update_period, config)
VALUES
    (sqlc.arg(id), sqlc.arg(system_pk), sqlc.arg(update_strategy), 
     sqlc.arg(update_period), sqlc.arg(config));

-- name: UpdateFeed :exec
UPDATE feed
SET update_strategy = sqlc.arg(update_strategy),
    update_period = sqlc.arg(update_period), 
    config = sqlc.arg(config)
WHERE pk = sqlc.arg(feed_pk);

-- name: DeleteFeed :exec
DELETE FROM feed WHERE pk = sqlc.arg(pk);

-- name: ListAutoUpdateFeedsForSystem :many
SELECT feed.id, feed.update_period
FROM feed
    INNER JOIN system ON system.pk = feed.system_pk
WHERE feed.update_strategy = 'PERIODIC'
    AND system.id = sqlc.arg(system_id);

-- name: InsertFeedUpdate :one
INSERT INTO feed_update
    (feed_pk, started_at, finished)
VALUES
    (sqlc.arg(feed_pk), sqlc.arg(started_at), false)
RETURNING pk;

-- name: GetLastFeedUpdateContentHash :one
SELECT content_hash
FROM feed_update
WHERE feed_pk = sqlc.arg(feed_pk) AND result = 'UPDATED'
ORDER BY finished_at DESC
LIMIT 1;

-- name: FinishFeedUpdate :exec
UPDATE feed_update
SET finished = true, 
    result = sqlc.arg(result),
    finished_at = sqlc.arg(finished_at),
    content_length = sqlc.arg(content_length),
    content_hash = sqlc.arg(content_hash),
    error_message = sqlc.arg(error_message)
WHERE pk = sqlc.arg(update_pk);

-- name: GetFeedUpdate :one
SELECT * FROM feed_update WHERE pk = sqlc.arg(pk);

-- name: CountUpdatesInFeed :one
SELECT COUNT(*) FROM feed_update WHERE feed_pk = sqlc.arg(feed_pk);

-- name: ListActiveFeedUpdatePks :many
SELECT DISTINCT route.source_pk FROM route
UNION SELECT DISTINCT stop.source_pk FROM stop;

-- name: GarbageCollectFeedUpdates :exec
DELETE FROM feed_update
WHERE started_at <= NOW() - INTERVAL '7 days'
AND feed_update.pk NOT IN (sqlc.arg(active_feed_update_pks));
