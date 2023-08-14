-- name: InsertShape :one
INSERT INTO shape
    (id, system_pk, feed_pk, shape)
VALUES
    (sqlc.arg(id), sqlc.arg(system_pk), sqlc.arg(feed_pk), sqlc.arg(shape))
RETURNING pk;

-- name: ListShapes :many
SELECT shape.*, scheduled_trip.id trip_id
FROM shape
INNER JOIN scheduled_trip ON scheduled_trip.shape_pk = shape.pk
WHERE system_pk = sqlc.arg(system_pk);

-- name: DeleteShapes :exec
DELETE FROM shape
WHERE feed_pk = sqlc.arg(feed_pk)
OR (system_pk = sqlc.arg(system_pk) AND
   id = ANY(sqlc.arg(updated_shape_ids)::text[]));
