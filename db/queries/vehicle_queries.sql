-- name: InsertVehicle :exec
INSERT INTO vehicle
    (id, system_pk, trip_pk, label, license_plate, current_status, location, bearing, odometer, speed, congestion_level, updated_at, current_stop_pk, current_stop_sequence, occupancy_status, feed_pk, occupancy_percentage)
VALUES
    (sqlc.arg(id), sqlc.arg(system_pk), sqlc.arg(trip_pk), sqlc.arg(label), sqlc.arg(license_plate), sqlc.arg(current_status), sqlc.arg(location), sqlc.arg(bearing), sqlc.arg(odometer), sqlc.arg(speed), sqlc.arg(congestion_level), sqlc.arg(updated_at), sqlc.arg(current_stop_pk), sqlc.arg(current_stop_sequence), sqlc.arg(occupancy_status), sqlc.arg(feed_pk), sqlc.arg(occupancy_percentage));

-- name: ListVehicles :many
SELECT vehicle.*,
       stop.id as stop_id,
       stop.name as stop_name,
       trip.id as trip_id,
       trip.direction_id as trip_direction_id,
       route.id as route_id,
       route.color as route_color
FROM vehicle
LEFT JOIN stop ON vehicle.current_stop_pk = stop.pk
LEFT JOIN trip ON vehicle.trip_pk = trip.pk
LEFT JOIN route ON trip.route_pk = route.pk
WHERE vehicle.system_pk = sqlc.arg(system_pk)
  AND vehicle.id >= sqlc.arg(first_vehicle_id)
  AND (
    NOT sqlc.arg(only_return_specified_ids)::bool OR
    vehicle.id = ANY(sqlc.arg(vehicle_ids)::text[])
  )
ORDER BY vehicle.id
LIMIT sqlc.arg(num_vehicles);

-- name: ListVehicles_Geographic :many
WITH distance AS (
    SELECT
        vehicle.pk vehicle_pk,
        vehicle.location <-> sqlc.arg(base)::geography distance
    FROM vehicle
    WHERE vehicle.location IS NOT NULL
    AND vehicle.system_pk = sqlc.arg(system_pk)
)
SELECT vehicle.*,
       stop.id as stop_id,
       stop.name as stop_name,
       trip.id as trip_id,
       trip.direction_id as trip_direction_id,
       route.id as route_id,
       route.color as route_color
FROM vehicle
INNER JOIN distance ON vehicle.pk = distance.vehicle_pk
AND distance.distance <= 1000 * sqlc.arg(max_distance)::float
LEFT JOIN stop ON vehicle.current_stop_pk = stop.pk
LEFT JOIN trip ON vehicle.trip_pk = trip.pk
LEFT JOIN route ON trip.route_pk = route.pk
ORDER BY distance.distance
LIMIT sqlc.arg(num_vehicles);

-- name: GetVehicle :one
SELECT vehicle.*,
       stop.id as stop_id,
       stop.name as stop_name,
       trip.id as trip_id,
       trip.direction_id as trip_direction_id,
       route.id as route_id,
       route.color as route_color
FROM vehicle
LEFT JOIN stop ON vehicle.current_stop_pk = stop.pk
LEFT JOIN trip ON vehicle.trip_pk = trip.pk
LEFT JOIN route ON trip.route_pk = route.pk
WHERE vehicle.system_pk = sqlc.arg(system_pk) AND vehicle.id = sqlc.arg(vehicle_id);

-- name: MapTripPkToVehicleID :many
SELECT id, trip_pk FROM vehicle
WHERE id = ANY(sqlc.arg(vehicle_ids)::text[])
AND system_pk = sqlc.arg(system_pk);

-- name: DeleteVehicles :exec
DELETE FROM vehicle
WHERE system_pk = sqlc.arg(system_pk)
  AND (feed_pk = sqlc.arg(feed_pk)
       OR vehicle.id = ANY(sqlc.arg(vehicle_ids)::text[])
       OR trip_pk = ANY(sqlc.arg(trip_pks)::bigint[]));
