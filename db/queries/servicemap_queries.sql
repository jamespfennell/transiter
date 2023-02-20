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

-- name: ListServiceMapsConfigIDsForStops :many
SELECT stop.pk, service_map_config.id
FROM service_map_config
    INNER JOIN stop ON service_map_config.system_pk = stop.system_pk
WHERE stop.pk = ANY(sqlc.arg(stop_pks)::bigint[]);

-- name: ListServiceMapsForStops :many
SELECT stop.pk stop_pk, service_map_config.id config_id, service_map.route_pk route_pk
FROM stop
  INNER JOIN service_map_vertex vertex ON vertex.stop_pk = stop.pk
  INNER JOIN service_map ON service_map.pk = vertex.map_pk
  INNER JOIN service_map_config ON service_map_config.pk = service_map.config_pk
WHERE stop.pk = ANY(sqlc.arg(stop_pks)::bigint[]);

-- TODO: make this better?
-- name: ListServiceMapsForRoutes :many
SELECT DISTINCT route.pk route_pk, service_map_config.id config_id, service_map_vertex.position, stop.id stop_id, stop.name stop_name
FROM service_map_config
  INNER JOIN system ON service_map_config.system_pk = system.pk
  INNER JOIN route ON route.system_pk = system.pk
  LEFT JOIN service_map ON service_map.config_pk = service_map_config.pk AND service_map.route_pk = route.pk
  LEFT JOIN service_map_vertex ON service_map_vertex.map_pk = service_map.pk
  LEFT JOIN stop ON stop.pk = service_map_vertex.stop_pk
WHERE route.pk = ANY(sqlc.arg(route_pks)::bigint[])
ORDER BY service_map_config.id, service_map_vertex.position;
