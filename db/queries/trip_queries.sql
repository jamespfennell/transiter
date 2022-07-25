-- name: InsertTrip :one
INSERT INTO trip
    (id, route_pk, source_pk, direction_id, started_at)
VALUES
    (sqlc.arg(id), sqlc.arg(route_pk), sqlc.arg(source_pk), sqlc.arg(direction_id), sqlc.arg(started_at))
RETURNING pk;

-- name: UpdateTrip :exec
UPDATE trip SET 
    source_pk = sqlc.arg(source_pk),
    direction_id = sqlc.arg(direction_id),
    started_at = sqlc.arg(started_at)
WHERE pk = sqlc.arg(pk);

-- name: ListTripsForUpdate :many
SELECT trip.pk, trip.id, trip.route_pk, trip.direction_id
FROM trip
WHERE
    trip.route_pk = ANY(sqlc.arg(route_pks)::bigint[]);

-- name: ListTripStopTimesForUpdate :many
SELECT pk, trip_pk, stop_pk, stop_sequence, past FROM trip_stop_time
WHERE trip_pk = ANY(sqlc.arg(trip_pks)::bigint[])
ORDER BY trip_pk, stop_sequence;

-- name: InsertTripStopTime :exec
INSERT INTO trip_stop_time
    (stop_pk, trip_pk, arrival_time, arrival_delay, arrival_uncertainty,
     departure_time, departure_delay, departure_uncertainty, stop_sequence, track, headsign, past)
VALUES
    (sqlc.arg(stop_pk), sqlc.arg(trip_pk), sqlc.arg(arrival_time), sqlc.arg(arrival_delay),
     sqlc.arg(arrival_uncertainty), sqlc.arg(departure_time), sqlc.arg(departure_delay),
     sqlc.arg(departure_uncertainty), sqlc.arg(stop_sequence), sqlc.arg(track), sqlc.arg(headsign), FALSE);

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

-- name: MarkTripStopTimesPast :exec
UPDATE trip_stop_time
SET
    past = TRUE
WHERE
    trip_pk = sqlc.arg(trip_pk)
    AND stop_sequence < sqlc.arg(current_stop_sequence);

-- name: DeleteTripStopTimes :exec
DELETE FROM trip_stop_time
WHERE pk = ANY(sqlc.arg(pks)::bigint[]);

-- TODO: These DeleteStaleT queries can be simpler and just take the update_pk
-- name: DeleteStaleTrips :many
DELETE FROM trip
USING feed_update
WHERE 
    feed_update.pk = trip.source_pk
    AND feed_update.feed_pk = sqlc.arg(feed_pk)
    AND feed_update.pk != sqlc.arg(update_pk)
RETURNING trip.route_pk;
