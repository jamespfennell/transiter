-- name: InsertShape :one
INSERT INTO shape
    (id, system_pk, feed_pk, shape)
VALUES
    (sqlc.arg(id), sqlc.arg(system_pk), sqlc.arg(feed_pk), sqlc.arg(shape))
RETURNING pk;

-- name: ListShapes :many
SELECT *
FROM shape
WHERE system_pk = sqlc.arg(system_pk)
   AND id >= sqlc.arg(first_shape_id)
   AND (
      NOT sqlc.arg(only_return_specified_ids)::bool OR
      id = ANY(sqlc.arg(shape_ids)::text[])
    )
ORDER BY id
LIMIT sqlc.arg(num_shapes);

-- name: ListShapesAndTrips :many
SELECT shape.*, scheduled_trip.id trip_id
FROM shape
INNER JOIN scheduled_trip ON scheduled_trip.shape_pk = shape.pk
WHERE system_pk = sqlc.arg(system_pk);

-- name: GetShape :one
SELECT *
FROM shape
WHERE system_pk = sqlc.arg(system_pk) AND id = sqlc.arg(shape_id);

-- name: DeleteShapes :exec
DELETE FROM shape
WHERE feed_pk = sqlc.arg(feed_pk)
OR (system_pk = sqlc.arg(system_pk) AND
   id = ANY(sqlc.arg(updated_shape_ids)::text[]));
