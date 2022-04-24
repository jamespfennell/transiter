-- name: MapStopPkToIdInSystem :many
SELECT pk, id FROM stop WHERE system_pk = sqlc.arg(system_pk);

-- name: InsertStop :one
INSERT INTO stop
    (id, system_pk, source_pk, name, longitude, latitude,
     url, code, description, platform_code, timezone, type,
     wheelchair_boarding, zone_id)
VALUES
    (sqlc.arg(id), sqlc.arg(system_pk), sqlc.arg(source_pk), sqlc.arg(name), sqlc.arg(longitude),
     sqlc.arg(latitude), sqlc.arg(url), sqlc.arg(code), sqlc.arg(description), sqlc.arg(platform_code),
     sqlc.arg(timezone), sqlc.arg(type), sqlc.arg(wheelchair_boarding), sqlc.arg(zone_id))
RETURNING pk;

-- name: UpdateStop :exec
UPDATE stop SET
    source_pk = sqlc.arg(source_pk),
    name = sqlc.arg(name),
    longitude = sqlc.arg(longitude),
    latitude = sqlc.arg(latitude),
    url = sqlc.arg(url),
    code = sqlc.arg(code),
    description = sqlc.arg(description),
    platform_code = sqlc.arg(platform_code),
    timezone = sqlc.arg(timezone), 
    type = sqlc.arg(type), 
    wheelchair_boarding = sqlc.arg(wheelchair_boarding),
    zone_id = sqlc.arg(zone_id),
    parent_stop_pk = NULL
WHERE
    pk = sqlc.arg(pk);

-- name: UpdateStopParent :exec
UPDATE stop SET
    parent_stop_pk = sqlc.arg(parent_stop_pk)
WHERE
    pk = sqlc.arg(pk);

-- name: DeleteStaleStops :many
DELETE FROM stop
USING feed_update
WHERE 
    feed_update.pk = stop.source_pk
    AND feed_update.feed_pk = sqlc.arg(feed_pk)
    AND feed_update.pk != sqlc.arg(update_pk)
RETURNING stop.id;
