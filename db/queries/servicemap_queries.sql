-- name: ListServiceMapConfigsInSystem :many
SELECT * FROM service_map_config WHERE system_pk = $1 ORDER BY id;

-- name: InsertServiceMapConfig :exec
INSERT INTO service_map_config
    (id, system_pk, config)
VALUES
    (sqlc.arg(id), sqlc.arg(system_pk), sqlc.arg(config));

-- name: UpdateServiceMapConfig :exec
UPDATE service_map_config
SET config = sqlc.arg(config)
WHERE pk = sqlc.arg(pk);

-- name: DeleteServiceMapConfig :exec
DELETE FROM service_map_config WHERE pk = sqlc.arg(pk);

-- name: InsertServiceMap :one
INSERT INTO service_map
    (config_pk, route_pk)
VALUES
    (sqlc.arg(config_pk), sqlc.arg(route_pk))
RETURNING pk;

-- name: InsertServiceMapStop :exec
INSERT INTO service_map_vertex
    (map_pk, stop_pk, position)
VALUES
    (sqlc.arg(map_pk), sqlc.arg(stop_pk), sqlc.arg(position));

-- name: DeleteServiceMap :exec
DELETE FROM service_map WHERE config_pk = sqlc.arg(config_pk) AND route_pk = sqlc.arg(route_pk);

-- name: ListStopPksForRealtimeMap :many
SELECT trip.pk trip_pk, trip.direction_id, trip_stop_time.stop_pk
FROM trip
INNER JOIN trip_stop_time on trip_stop_time.trip_pk = trip.pk
WHERE trip.route_pk = sqlc.arg(route_pk)
AND trip.direction_id IS NOT NULL
ORDER BY trip.pk, trip_stop_time.stop_sequence;
