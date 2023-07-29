-- name: ListFeeds :many
SELECT * FROM feed WHERE system_pk = $1 ORDER BY id;

-- name: GetFeed :one
SELECT feed.* FROM feed
    INNER JOIN system on system.pk = feed.system_pk
    WHERE system.id = sqlc.arg(system_id)
    AND feed.id = sqlc.arg(feed_id);

-- name: InsertFeed :exec
INSERT INTO feed
    (id, system_pk, config)
VALUES
    (sqlc.arg(id), sqlc.arg(system_pk), sqlc.arg(config));

-- name: UpdateFeed :exec
UPDATE feed
SET config = sqlc.arg(config)
WHERE pk = sqlc.arg(feed_pk);

-- name: MarkSuccessfulUpdate :exec
UPDATE feed
SET last_content_hash = sqlc.arg(content_hash),
    last_update = sqlc.arg(update_time),
    last_successful_update = sqlc.arg(update_time)
WHERE pk = sqlc.arg(feed_pk);

-- name: MarkSkippedUpdate :exec
UPDATE feed
SET last_update = sqlc.arg(update_time),
    last_skipped_update = sqlc.arg(update_time)
WHERE pk = sqlc.arg(feed_pk);

-- name: MarkFailedUpdate :exec
UPDATE feed
SET last_update = sqlc.arg(update_time),
    last_failed_update = sqlc.arg(update_time)
WHERE pk = sqlc.arg(feed_pk);

-- name: DeleteFeed :exec
DELETE FROM feed WHERE pk = sqlc.arg(pk);
