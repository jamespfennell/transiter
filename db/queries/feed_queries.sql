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
    (feed_pk, status)
VALUES
    (sqlc.arg(feed_pk), sqlc.arg(status))
RETURNING pk;
