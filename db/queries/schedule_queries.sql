-- name: InsertScheduledService :one
INSERT INTO scheduled_service
    (id, system_pk, monday, tuesday, wednesday, thursday, friday, saturday, sunday, start_date, end_date, feed_pk)
VALUES
    (sqlc.arg(id), sqlc.arg(system_pk), sqlc.arg(monday), sqlc.arg(tuesday), sqlc.arg(wednesday), sqlc.arg(thursday), sqlc.arg(friday), sqlc.arg(saturday), sqlc.arg(sunday), sqlc.arg(start_date), sqlc.arg(end_date), sqlc.arg(feed_pk))
RETURNING pk;

-- name: InsertScheduledServiceAddition :exec
INSERT INTO scheduled_service_addition
    (service_pk, date)
VALUES
    (sqlc.arg(service_pk), sqlc.arg(date));

-- name: InsertScheduledServiceRemoval :exec
INSERT INTO scheduled_service_removal
    (service_pk, date)
VALUES
    (sqlc.arg(service_pk), sqlc.arg(date));

-- name: InsertScheduledTrip :copyfrom
INSERT INTO scheduled_trip
    (id, route_pk, service_pk, shape_pk, direction_id, bikes_allowed, block_id, headsign, short_name, wheelchair_accessible)
VALUES
    (sqlc.arg(id), sqlc.arg(route_pk), sqlc.arg(service_pk), sqlc.arg(shape_pk), sqlc.arg(direction_id), sqlc.arg(bikes_allowed), sqlc.arg(block_id), sqlc.arg(headsign), sqlc.arg(short_name), sqlc.arg(wheelchair_accessible));

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

-- name: ListScheduledServices :many
SELECT scheduled_service.*,
       scheduled_service_addition.additions AS additions,
       scheduled_service_removal.removals AS removals
FROM scheduled_service
LEFT JOIN (SELECT service_pk,
                  CASE WHEN COUNT(scheduled_service_addition.date) > 0
                  THEN array_agg(scheduled_service_addition.date ORDER BY scheduled_service_addition.date)::date[]
                  ELSE NULL::date[] END AS additions
           FROM scheduled_service_addition
           GROUP BY scheduled_service_addition.service_pk) AS scheduled_service_addition
    ON scheduled_service.pk = scheduled_service_addition.service_pk
LEFT JOIN (SELECT service_pk,
                  CASE WHEN COUNT(scheduled_service_removal.date) > 0
                  THEN array_agg(scheduled_service_removal.date ORDER BY scheduled_service_removal.date)::date[]
                  ELSE NULL::date[] END AS removals
           FROM scheduled_service_removal
           GROUP BY scheduled_service_removal.service_pk) AS scheduled_service_removal
    ON scheduled_service.pk = scheduled_service_removal.service_pk
WHERE system_pk = sqlc.arg(system_pk);

-- name: GetScheduledService :one
SELECT * from scheduled_service
WHERE system_pk = sqlc.arg(system_pk)
AND id = sqlc.arg(id);

-- name: ListScheduledTrips :many
SELECT
    scheduled_trip.*,
    route.id route_id,
    scheduled_service.id service_id
FROM scheduled_trip
INNER JOIN route ON scheduled_trip.route_pk = route.pk
INNER JOIN scheduled_service ON scheduled_trip.service_pk = scheduled_service.pk
WHERE scheduled_service.system_pk = sqlc.arg(system_pk);

-- name: GetScheduledTrip :one
SELECT scheduled_trip.*
FROM scheduled_trip
INNER JOIN route ON scheduled_trip.route_pk = route.pk
INNER JOIN scheduled_service ON scheduled_trip.service_pk = scheduled_service.pk
WHERE scheduled_service.system_pk = sqlc.arg(system_pk)
AND scheduled_trip.id = sqlc.arg(trip_id);

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

-- name: MapScheduledTripIDToPkInSystem :many
SELECT scheduled_trip.id, scheduled_trip.pk FROM scheduled_trip
INNER JOIN scheduled_service ON scheduled_trip.service_pk = scheduled_service.pk
WHERE
    system_pk = sqlc.arg(system_pk)
    AND (
        NOT sqlc.arg(filter_by_trip_id)::bool
        OR scheduled_trip.id = ANY(sqlc.arg(trip_ids)::text[])
    );

-- name: MapScheduledTripIDToRoutePkInSystem :many
SELECT scheduled_trip.id, scheduled_trip.route_pk FROM scheduled_trip
INNER JOIN scheduled_service ON scheduled_trip.service_pk = scheduled_service.pk
WHERE
    system_pk = sqlc.arg(system_pk)
    AND (
        NOT sqlc.arg(filter_by_trip_id)::bool
        OR scheduled_trip.id = ANY(sqlc.arg(trip_ids)::text[])
    );

-- name: DeleteScheduledServices :exec
DELETE FROM scheduled_service
WHERE feed_pk = sqlc.arg(feed_pk)
OR (system_pk = sqlc.arg(system_pk) AND
   id = ANY(sqlc.arg(updated_service_ids)::text[]));
