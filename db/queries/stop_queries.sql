-- name: InsertStop :one
INSERT INTO stop
    (id, system_pk, feed_pk, name, location,
     url, code, description, platform_code, timezone, type,
     wheelchair_boarding, zone_id)
VALUES
    (sqlc.arg(id), sqlc.arg(system_pk), sqlc.arg(feed_pk), sqlc.arg(name),
     sqlc.arg(location)::geography,
     sqlc.arg(url), sqlc.arg(code), sqlc.arg(description), sqlc.arg(platform_code),
     sqlc.arg(timezone), sqlc.arg(type), sqlc.arg(wheelchair_boarding), sqlc.arg(zone_id))
RETURNING pk;

-- name: UpdateStop :exec
UPDATE stop SET
    feed_pk = sqlc.arg(feed_pk),
    name = sqlc.arg(name),
    location = sqlc.arg(location)::geography,
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

-- name: UpdateStop_Parent :exec
UPDATE stop SET
    parent_stop_pk = sqlc.arg(parent_stop_pk)
WHERE
    pk = sqlc.arg(pk);

-- name: DeleteStaleStops :exec
DELETE FROM stop
WHERE
    stop.feed_pk = sqlc.arg(feed_pk)
    AND NOT stop.pk = ANY(sqlc.arg(updated_stop_pks)::bigint[]);

-- name: ListStops :many
SELECT * FROM stop
WHERE system_pk = sqlc.arg(system_pk)
  AND id >= sqlc.arg(first_stop_id)
  AND (
    NOT sqlc.arg(filter_by_id)::bool OR
    id = ANY(sqlc.arg(stop_ids)::text[])
  )
  AND (
    NOT sqlc.arg(filter_by_type)::bool OR
    type = ANY(sqlc.arg(types)::text[])
  )
ORDER BY id
LIMIT sqlc.arg(num_stops);

-- name: ListStops_Geographic :many
WITH distance AS (
    SELECT
        stop.pk stop_pk,
        stop.location <-> sqlc.arg(base)::geography distance
    FROM stop
    WHERE stop.location IS NOT NULL
    AND (
        NOT sqlc.arg(filter_by_type)::bool OR
        type = ANY(sqlc.arg(types)::text[])
    )
)
SELECT stop.* FROM stop
INNER JOIN distance ON stop.pk = distance.stop_pk
WHERE stop.system_pk = sqlc.arg(system_pk)
    AND distance.distance <= 1000 * sqlc.arg(max_distance)::float
ORDER by distance.distance
LIMIT sqlc.arg(max_results);

-- name: GetStop :one
SELECT stop.* FROM stop
    INNER JOIN system ON stop.system_pk = system.pk
    WHERE system.id = sqlc.arg(system_id)
    AND stop.id = sqlc.arg(stop_id);

-- name: ListTripStopTimesByStops :many
SELECT trip_stop_time.*,
       trip.*, vehicle.id vehicle_id,
       vehicle.location::geography vehicle_location,
       vehicle.bearing vehicle_bearing,
       vehicle.updated_at vehicle_updated_at,
       COALESCE(scheduled_trip_stop_time.headsign, scheduled_trip.headsign) scheduled_trip_headsign
    FROM trip_stop_time
    INNER JOIN trip ON trip_stop_time.trip_pk = trip.pk
    LEFT JOIN vehicle ON vehicle.trip_pk = trip.pk
    LEFT JOIN scheduled_trip ON scheduled_trip.id = trip.id AND scheduled_trip.route_pk = trip.route_pk
    LEFT JOIN scheduled_trip_stop_time ON scheduled_trip_stop_time.trip_pk = scheduled_trip.pk AND
                                          scheduled_trip_stop_time.stop_pk = trip_stop_time.stop_pk AND
                                          scheduled_trip_stop_time.stop_sequence = trip_stop_time.stop_sequence
    WHERE trip_stop_time.stop_pk = ANY(sqlc.arg(stop_pks)::bigint[])
    AND NOT trip_stop_time.past
    ORDER BY COALESCE(trip_stop_time.arrival_time, trip_stop_time.departure_time);

-- name: ListStopsByPk :many
SELECT stop.pk, stop.id stop_id, stop.name, system.id system_id
FROM stop
    INNER JOIN system on stop.system_pk = system.pk
WHERE stop.pk = ANY(sqlc.arg(stop_pks)::bigint[]);

-- name: MapStopPkToChildPks :many
SELECT parent_stop_pk parent_pk, pk child_pk
FROM stop
WHERE stop.parent_stop_pk = ANY(sqlc.arg(stop_pks)::bigint[]);

-- name: MapStopIDAndPkToStationPk :many
WITH RECURSIVE
ancestor AS (
    SELECT
    id stop_id,
    pk stop_pk,
    pk station_pk,
    parent_stop_pk,
    (type = 'STATION') is_station
    FROM stop
        WHERE stop.system_pk = sqlc.arg(system_pk)
        AND (
            NOT sqlc.arg(filter_by_stop_pk)::bool
            OR stop.pk = ANY(sqlc.arg(stop_pks)::bigint[])
        )
    UNION
    SELECT
    child.stop_id stop_id,
    child.stop_pk stop_pk,
    parent.pk station_pk,
    parent.parent_stop_pk,
    (parent.type = 'STATION') is_station
        FROM stop parent
        INNER JOIN ancestor child
    ON child.parent_stop_pk = parent.pk
    AND NOT child.is_station
)
SELECT stop_id, stop_pk, station_pk
  FROM ancestor
  WHERE parent_stop_pk IS NULL
  OR is_station;

-- name: MapStopPkToDescendentPks :many
WITH RECURSIVE descendent AS (
    SELECT
    stop.pk root_stop_pk,
    stop.pk descendent_stop_pk
    FROM stop
        WHERE stop.pk = ANY(sqlc.arg(stop_pks)::bigint[])
    UNION
    SELECT
    descendent.root_stop_pk root_stop_pk,
    child.pk descendent_stop_pk
        FROM stop child
        INNER JOIN descendent
    ON child.parent_stop_pk = descendent.descendent_stop_pk
)
SELECT root_stop_pk, descendent_stop_pk FROM descendent;

-- name: MapStopIDToPk :many
SELECT pk, id from stop
WHERE
    system_pk = sqlc.arg(system_pk)
    AND (
        NOT sqlc.arg(filter_by_stop_id)::bool
        OR id = ANY(sqlc.arg(stop_ids)::text[])
    );
