-- name: InsertScheduledTrip :one
INSERT INTO scheduled_trip
    (id, route_pk, service_pk, shape_pk, direction_id, bikes_allowed, block_id, headsign, short_name, wheelchair_accessible)
VALUES
    (sqlc.arg(id), sqlc.arg(route_pk), sqlc.arg(service_pk), sqlc.arg(shape_pk), sqlc.arg(direction_id), sqlc.arg(bikes_allowed), sqlc.arg(block_id), sqlc.arg(headsign), sqlc.arg(short_name), sqlc.arg(wheelchair_accessible))
RETURNING pk;

-- name: UpdateScheduledTrip :exec
UPDATE scheduled_trip SET
    route_pk = sqlc.arg(route_pk),
    service_pk = sqlc.arg(service_pk),
    shape_pk = sqlc.arg(shape_pk),
    direction_id = sqlc.arg(direction_id),
    bikes_allowed = sqlc.arg(bikes_allowed),
    block_id = sqlc.arg(block_id),
    headsign = sqlc.arg(headsign),
    short_name = sqlc.arg(short_name),
    wheelchair_accessible = sqlc.arg(wheelchair_accessible)
WHERE pk = sqlc.arg(pk);

-- name: InsertScheduledTripStopTime :copyfrom
INSERT INTO scheduled_trip_stop_time
    (trip_pk, stop_pk, arrival_time, departure_time, stop_sequence, continuous_drop_off, continuous_pickup,
    drop_off_type, exact_times, headsign, pickup_type, shape_distance_traveled)
VALUES
    (sqlc.arg(trip_pk), sqlc.arg(stop_pk), sqlc.arg(arrival_time), sqlc.arg(departure_time), sqlc.arg(stop_sequence), sqlc.arg(continuous_drop_off), sqlc.arg(continuous_pickup),
    sqlc.arg(drop_off_type), sqlc.arg(exact_times), sqlc.arg(headsign), sqlc.arg(pickup_type), sqlc.arg(shape_distance_traveled));

-- name: InsertScheduledTripFrequency :exec
INSERT INTO scheduled_trip_frequency
    (trip_pk, start_time, end_time, headway, frequency_based)
VALUES
    (sqlc.arg(trip_pk), sqlc.arg(start_time), sqlc.arg(end_time), sqlc.arg(headway), sqlc.arg(frequency_based));

-- name: InsertScheduledTripShape :one
INSERT INTO scheduled_trip_shape
    (id, system_pk, shape)
VALUES
    (sqlc.arg(id), sqlc.arg(system_pk), sqlc.arg(shape))
RETURNING pk;

-- name: UpdateScheduledTripShape :exec
UPDATE scheduled_trip_shape SET
    id = sqlc.arg(id),
    shape = sqlc.arg(shape)
WHERE pk = sqlc.arg(pk);

-- name: ListScheduledTrips :many
SELECT
    scheduled_trip.*,
    route.id route_id,
    scheduled_service.id service_id
FROM scheduled_trip
INNER JOIN route ON scheduled_trip.route_pk = route.pk
INNER JOIN scheduled_service ON scheduled_trip.service_pk = scheduled_service.pk
WHERE scheduled_service.system_pk = sqlc.arg(system_pk);

-- name: ListScheduledTripStopTimes :many
SELECT
    scheduled_trip_stop_time.*,
    scheduled_trip.id trip_id,
    stop.id stop_id
FROM scheduled_trip_stop_time
INNER JOIN scheduled_trip ON scheduled_trip_stop_time.trip_pk = scheduled_trip.pk
INNER JOIN stop ON scheduled_trip_stop_time.stop_pk = stop.pk
INNER JOIN scheduled_service ON scheduled_trip.service_pk = scheduled_service.pk
WHERE scheduled_service.system_pk = sqlc.arg(system_pk);

-- name: ListScheduledTripFrequencies :many
SELECT
    scheduled_trip_frequency.*,
    scheduled_trip.id trip_id
FROM scheduled_trip_frequency
INNER JOIN scheduled_trip ON scheduled_trip_frequency.trip_pk = scheduled_trip.pk
INNER JOIN scheduled_service ON scheduled_trip.service_pk = scheduled_service.pk
WHERE scheduled_service.system_pk = sqlc.arg(system_pk);

-- name: ListScheduledTripShapes :many
SELECT scheduled_trip_shape.*, scheduled_trip.id trip_id
FROM scheduled_trip_shape
INNER JOIN scheduled_trip ON scheduled_trip.shape_pk = scheduled_trip_shape.pk
WHERE system_pk = sqlc.arg(system_pk);

-- name: MapScheduledTripIDToPkInSystem :many
SELECT scheduled_trip.id, scheduled_trip.pk FROM scheduled_trip
INNER JOIN scheduled_service ON scheduled_trip.service_pk = scheduled_service.pk
WHERE
    system_pk = sqlc.arg(system_pk)
    AND (
        NOT sqlc.arg(filter_by_trip_id)::bool
        OR scheduled_trip.id = ANY(sqlc.arg(trip_ids)::text[])
    );

-- name: MapShapeIDToPkInSystem :many
SELECT id, pk
FROM scheduled_trip_shape
WHERE
    system_pk = sqlc.arg(system_pk)
    AND (
        NOT sqlc.arg(filter_by_shape_id)::bool
        OR id = ANY(sqlc.arg(shape_ids)::text[])
    );

-- name: DeleteStaleScheduledTrips :exec
DELETE FROM scheduled_trip
WHERE NOT scheduled_trip.pk = ANY(sqlc.arg(updated_trip_pks)::bigint[]);

-- name: DeleteScheduledTripStopTimes :exec
DELETE FROM scheduled_trip_stop_time
WHERE trip_pk = ANY(sqlc.arg(trip_pks)::bigint[]);

-- name: DeleteScheduledTripFrequencies :exec
DELETE FROM scheduled_trip_frequency
WHERE trip_pk = ANY(sqlc.arg(trip_pks)::bigint[]);

-- name: DeleteStaleScheduledTripShapes :exec
DELETE FROM scheduled_trip_shape
WHERE NOT scheduled_trip_shape.pk = ANY(sqlc.arg(updated_shape_pks)::bigint[]);
