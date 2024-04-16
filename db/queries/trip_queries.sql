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

-- name: ListTrips :many
WITH shapes_for_scheduled_trips_in_system AS (
  SELECT scheduled_trip.id as trip_id, shape.id as shape_id
  FROM shape
  INNER JOIN scheduled_trip ON shape.pk = scheduled_trip.shape_pk
  WHERE shape.system_pk = sqlc.arg(system_pk)
)
SELECT trip.*,
       vehicle.id as vehicle_id,
       vehicle.location::geography as vehicle_location,
       vehicle.bearing as vehicle_bearing,
       vehicle.updated_at as vehicle_updated_at,
       shapes_for_scheduled_trips_in_system.shape_id as shape_id
FROM trip
LEFT JOIN vehicle ON trip.pk = vehicle.trip_pk
LEFT JOIN shapes_for_scheduled_trips_in_system
     ON trip.id = shapes_for_scheduled_trips_in_system.trip_id
WHERE trip.route_pk = ANY(sqlc.arg(route_pks)::bigint[])
ORDER BY trip.route_pk, trip.id;

-- name: ListTripPksInSystem :many
SELECT trip.id, trip.pk
FROM trip
    INNER JOIN feed ON trip.feed_pk = feed.pk
WHERE trip.id = ANY(sqlc.arg(trip_ids)::text[])
    AND feed.system_pk = sqlc.arg(system_pk);

-- name: GetTrip :one
WITH shapes_for_scheduled_trips_in_system AS (
  SELECT scheduled_trip.id as trip_id, shape.id as shape_id
  FROM shape
  INNER JOIN scheduled_trip ON shape.pk = scheduled_trip.shape_pk
  WHERE shape.system_pk = sqlc.arg(system_pk)
)
SELECT trip.*,
       vehicle.id as vehicle_id,
       vehicle.location::geography as vehicle_location,
       vehicle.bearing as vehicle_bearing,
       vehicle.updated_at as vehicle_updated_at,
       shapes_for_scheduled_trips_in_system.shape_id as shape_id
FROM trip
LEFT JOIN vehicle ON trip.pk = vehicle.trip_pk
LEFT JOIN shapes_for_scheduled_trips_in_system
     ON trip.id = shapes_for_scheduled_trips_in_system.trip_id
WHERE trip.id = sqlc.arg(trip_id)
    AND trip.route_pk = sqlc.arg(route_pk);

-- name: ListStopsTimesForTrip :many
SELECT trip_stop_time.*, stop.id stop_id, stop.name stop_name
FROM trip_stop_time
    INNER JOIN stop ON trip_stop_time.stop_pk = stop.pk
WHERE trip_stop_time.trip_pk = sqlc.arg(trip_pk)
ORDER BY trip_stop_time.stop_sequence ASC;

-- name: InsertTrip :one
INSERT INTO trip
    (id, route_pk, feed_pk, direction_id, started_at, gtfs_hash)
VALUES
    (sqlc.arg(id), sqlc.arg(route_pk), sqlc.arg(feed_pk), sqlc.arg(direction_id), sqlc.arg(started_at), sqlc.arg(gtfs_hash))
RETURNING pk;

-- name: UpdateTrip :batchexec
UPDATE trip SET
    feed_pk = sqlc.arg(feed_pk),
    direction_id = sqlc.arg(direction_id),
    started_at = sqlc.arg(started_at),
    gtfs_hash = sqlc.arg(gtfs_hash)
WHERE pk = sqlc.arg(pk);

-- name: ListTripStopTimesForUpdate :many
SELECT pk, trip_pk, stop_pk, stop_sequence, past FROM trip_stop_time
WHERE trip_pk = ANY(sqlc.arg(trip_pks)::bigint[])
ORDER BY trip_pk, stop_sequence;

-- name: InsertTripStopTime :copyfrom
INSERT INTO trip_stop_time
    (stop_pk, trip_pk, arrival_time, arrival_delay, arrival_uncertainty,
     departure_time, departure_delay, departure_uncertainty, stop_sequence, track, headsign, past)
VALUES
    (sqlc.arg(stop_pk), sqlc.arg(trip_pk), sqlc.arg(arrival_time), sqlc.arg(arrival_delay),
     sqlc.arg(arrival_uncertainty), sqlc.arg(departure_time), sqlc.arg(departure_delay),
     sqlc.arg(departure_uncertainty), sqlc.arg(stop_sequence), sqlc.arg(track), sqlc.arg(headsign), sqlc.arg(past));

-- name: UpdateTripStopTime :exec
UPDATE trip_stop_time
SET
    stop_pk = sqlc.arg(stop_pk),
    arrival_time = sqlc.arg(arrival_time),
    arrival_delay = sqlc.arg(arrival_delay),
    arrival_uncertainty = sqlc.arg(arrival_uncertainty),
    departure_time = sqlc.arg(departure_time),
    departure_delay = sqlc.arg(departure_delay),
    departure_uncertainty = sqlc.arg(departure_uncertainty),
    stop_sequence = sqlc.arg(stop_sequence),
    track = sqlc.arg(track),
    headsign = sqlc.arg(headsign),
    past = FALSE
WHERE
    pk = sqlc.arg(pk);

-- name: MarkTripStopTimesPast :batchexec
UPDATE trip_stop_time
SET
    past = TRUE
WHERE
    trip_pk = sqlc.arg(trip_pk)
    AND stop_sequence < sqlc.arg(current_stop_sequence);

-- name: DeleteTripStopTimes :exec
DELETE FROM trip_stop_time
WHERE pk = ANY(sqlc.arg(pks)::bigint[]);

-- name: DeleteStaleTrips :many
DELETE FROM trip
WHERE
    trip.feed_pk = sqlc.arg(feed_pk)
    AND NOT trip.pk = ANY(sqlc.arg(updated_trip_pks)::bigint[])
RETURNING trip.route_pk;

-- name: MapTripIDToPkInSystem :many
SELECT trip.id, trip.pk
FROM trip
    INNER JOIN feed ON trip.feed_pk = feed.pk
WHERE trip.id = ANY(sqlc.arg(trip_ids)::text[])
    AND feed.system_pk = sqlc.arg(system_pk)
FOR UPDATE;
