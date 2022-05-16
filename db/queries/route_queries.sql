-- name: MapRoutePkToIdInSystem :many
SELECT pk, id FROM route WHERE system_pk = sqlc.arg(system_pk);

-- name: InsertRoute :one
INSERT INTO route
    (id, system_pk, source_pk, color, text_color,
     short_name, long_name, description, url, sort_order,
     type, continuous_pickup, continuous_drop_off, agency_pk)
VALUES
    (sqlc.arg(id), sqlc.arg(system_pk), sqlc.arg(source_pk), sqlc.arg(color), sqlc.arg(text_color),
     sqlc.arg(short_name), sqlc.arg(long_name), sqlc.arg(description), sqlc.arg(url), sqlc.arg(sort_order),
     sqlc.arg(type), sqlc.arg(continuous_pickup),sqlc.arg(continuous_drop_off), sqlc.arg(agency_pk))
RETURNING pk;

-- name: UpdateRoute :exec
UPDATE route SET
    source_pk = sqlc.arg(source_pk),
    color = sqlc.arg(color),
    text_color = sqlc.arg(text_color),
    short_name = sqlc.arg(short_name), 
    long_name = sqlc.arg(long_name), 
    description = sqlc.arg(description), 
    url = sqlc.arg(url), 
    sort_order = sqlc.arg(sort_order), 
    type = sqlc.arg(type), 
    continuous_pickup = sqlc.arg(continuous_pickup), 
    continuous_drop_off = sqlc.arg(continuous_drop_off), 
    agency_pk = sqlc.arg(agency_pk)
WHERE
    pk = sqlc.arg(pk);

-- name: DeleteStaleRoutes :many
DELETE FROM route
USING feed_update
WHERE 
    feed_update.pk = route.source_pk
    AND feed_update.feed_pk = sqlc.arg(feed_pk)
    AND feed_update.pk != sqlc.arg(update_pk)
RETURNING route.id;


-- name: MapRoutesInSystem :many
SELECT pk, id from route
WHERE
    system_pk = sqlc.arg(system_pk)
    AND id = ANY(sqlc.arg(route_ids)::text[]);
