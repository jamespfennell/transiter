-- TODO: move all queries from this file in the $x_queries.sql files.

-- name: GetSystem :one
SELECT * FROM system
WHERE id = $1 LIMIT 1;

-- name: ListSystems :many
SELECT * FROM system ORDER BY id, name;

-- name: CountAgenciesInSystem :one
SELECT COUNT(*) FROM agency WHERE system_pk = $1;

-- name: CountFeedsInSystem :one
SELECT COUNT(*) FROM feed WHERE system_pk = $1;

-- name: CountRoutesInSystem :one
SELECT COUNT(*) FROM route WHERE system_pk = $1;

-- name: CountStopsInSystem :one
SELECT COUNT(*) FROM stop WHERE system_pk = $1;

-- name: CountTransfersInSystem :one
SELECT COUNT(*) FROM transfer WHERE system_pk = $1;

-- name: ListRoutesInAgency :many
SELECT route.id, route.color FROM route
WHERE route.agency_pk = sqlc.arg(agency_pk);

-- name: ListStopsInSystem :many
SELECT * FROM stop
WHERE system_pk = sqlc.arg(system_pk)
  AND id >= sqlc.arg(first_stop_id)
  AND (
    NOT sqlc.arg(only_return_specified_ids)::bool OR
    id = ANY(sqlc.arg(stop_ids)::text[])
  )
ORDER BY id
LIMIT sqlc.arg(num_stops);

-- name: ListStopsInSystemGeoFilter :many
SELECT * FROM stop
WHERE system_pk = sqlc.arg(system_pk)
  AND (
    NOT sqlc.arg(only_return_specified_ids)::bool OR
    id = ANY(sqlc.arg(stop_ids)::text[])
  )
  AND (6371 * acos(cos(radians(latitude)) * cos(radians(sqlc.arg(latitude)::numeric)) * cos(radians(sqlc.arg(longitude)::numeric) - radians(longitude)) + sin(radians(latitude)) * sin(radians(sqlc.arg(latitude)::numeric)))) <= sqlc.arg(max_distance)::numeric
ORDER BY id;

-- name: GetStopInSystem :one
SELECT stop.* FROM stop
    INNER JOIN system ON stop.system_pk = system.pk
    WHERE system.id = sqlc.arg(system_id)
    AND stop.id = sqlc.arg(stop_id);

-- name: ListStopTimesAtStops :many
SELECT trip_stop_time.*, trip.*, vehicle.id vehicle_id FROM trip_stop_time
    INNER JOIN trip ON trip_stop_time.trip_pk = trip.pk
    LEFT JOIN vehicle ON vehicle.trip_pk = trip.pk
    WHERE trip_stop_time.stop_pk = ANY(sqlc.arg(stop_pks)::bigint[])
    AND NOT trip_stop_time.past
    ORDER BY trip_stop_time.departure_time, trip_stop_time.arrival_time;

-- name: ListStopsInStopTree :many
WITH RECURSIVE
ancestor AS (
    SELECT initial.pk, initial.parent_stop_pk
      FROM stop initial
      WHERE	initial.pk = $1
    UNION
    SELECT parent.pk, parent.parent_stop_pk
        FROM stop parent
        INNER JOIN ancestor ON ancestor.parent_stop_pk = parent.pk
),
descendent AS (
    SELECT * FROM ancestor
    UNION
    SELECT child.pk, child.parent_stop_pk
        FROM stop child
        INNER JOIN descendent ON descendent.pk = child.parent_stop_pk
)
SELECT stop.* FROM stop
  INNER JOIN descendent
  ON stop.pk = descendent.pk;


-- name: ListRoutesByPk :many
SELECT * FROM route WHERE route.pk = ANY(sqlc.arg(route_pks)::bigint[]);

-- name: GetDestinationsForTrips :many
WITH last_stop_sequence AS (
  SELECT trip_pk, MAX(stop_sequence) as stop_sequence
    FROM trip_stop_time
    WHERE trip_pk = ANY(sqlc.arg(trip_pks)::bigint[])
    GROUP BY trip_pk
)
SELECT lss.trip_pk, stop.pk destination_pk
  FROM last_stop_sequence lss
  INNER JOIN trip_stop_time
    ON lss.trip_pk = trip_stop_time.trip_pk
    AND lss.stop_sequence = trip_stop_time.stop_sequence
  INNER JOIN stop
    ON trip_stop_time.stop_pk = stop.pk;

-- name: ListTransfersFromStops :many
  SELECT transfer.*
  FROM transfer
  WHERE transfer.from_stop_pk = ANY(sqlc.arg(from_stop_pks)::bigint[]);


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

-- name: ListStopHeadsignRulesForStops :many
SELECT * FROM stop_headsign_rule
WHERE stop_pk = ANY(sqlc.arg(stop_pks)::bigint[])
ORDER BY priority ASC;

-- name: ListRoutesInSystem :many
SELECT * FROM route WHERE system_pk = $1 ORDER BY id;

-- name: GetRouteInSystem :one
SELECT route.* FROM route
    INNER JOIN system ON route.system_pk = system.pk
    WHERE system.pk = sqlc.arg(system_pk)
    AND route.id = sqlc.arg(route_id);

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


-- name: ListTransfersInSystem :many
SELECT
    transfer.*,
    from_stop.id from_stop_id, from_stop.name from_stop_name, from_system.id from_system_id,
    to_stop.id to_stop_id, to_stop.name to_stop_name, to_system.id to_system_id
FROM transfer
    INNER JOIN stop from_stop ON from_stop.pk = transfer.from_stop_pk
    INNER JOIN system from_system ON from_stop.system_pk = from_system.pk
    INNER JOIN stop to_stop ON to_stop.pk = transfer.to_stop_pk
    INNER JOIN system to_system ON to_stop.system_pk = to_system.pk
WHERE transfer.system_pk = $1
ORDER BY transfer.pk;

-- ListActiveAlertsForRoutes returns preview information about active alerts for the provided routes.
-- name: ListActiveAlertsForRoutes :many
SELECT route.pk route_pk, alert.id, alert.cause, alert.effect
FROM route
    INNER JOIN alert_route ON route.pk = alert_route.route_pk
    INNER JOIN alert ON alert_route.alert_pk = alert.pk
    INNER JOIN alert_active_period ON alert_active_period.alert_pk = alert.pk
WHERE route.pk = ANY(sqlc.arg(route_pks)::bigint[])
    AND (
        alert_active_period.starts_at < sqlc.arg(present_time)
        OR alert_active_period.starts_at IS NULL
    )
    AND (
        alert_active_period.ends_at > sqlc.arg(present_time)
        OR alert_active_period.ends_at IS NULL
    )
ORDER BY alert.id ASC;


-- name: ListActiveAlertsForStops :many
SELECT stop.pk stop_pk, alert.pk, alert.id, alert.cause, alert.effect, alert_active_period.starts_at, alert_active_period.ends_at
FROM stop
    INNER JOIN alert_stop ON stop.pk = alert_stop.stop_pk
    INNER JOIN alert ON alert_stop.alert_pk = alert.pk
    INNER JOIN alert_active_period ON alert_active_period.alert_pk = alert.pk
WHERE stop.pk = ANY(sqlc.arg(stop_pks)::bigint[])
    AND (
        alert_active_period.starts_at < sqlc.arg(present_time)
        OR alert_active_period.starts_at IS NULL
    )
    AND (
        alert_active_period.ends_at > sqlc.arg(present_time)
        OR alert_active_period.ends_at IS NULL
    )
ORDER BY alert.id ASC;



-- name: ListUpdatesInFeed :many
SELECT * FROM feed_update
WHERE feed_pk = sqlc.arg(feed_pk)
ORDER BY pk DESC
LIMIT 100;

-- name: ListTrips :many
SELECT * FROM trip
WHERE trip.route_pk = sqlc.arg(route_pk)
ORDER BY trip.id;

-- name: GetTrip :one
SELECT * FROM trip
WHERE trip.id = sqlc.arg(trip_id)
    AND trip.route_pk = sqlc.arg(route_pk);

-- name: GetTripByPk :one
SELECT * FROM trip WHERE pk = sqlc.arg(pk);

-- name: ListStopsTimesForTrip :many
SELECT trip_stop_time.*, stop.id stop_id, stop.name stop_name
FROM trip_stop_time
    INNER JOIN stop ON trip_stop_time.stop_pk = stop.pk
WHERE trip_stop_time.trip_pk = sqlc.arg(trip_pk)
ORDER BY trip_stop_time.stop_sequence ASC;
