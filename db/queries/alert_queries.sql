-- name: ListAlertPksAndHashes :many
SELECT id, pk, hash FROM alert
WHERE id = ANY(sqlc.arg(alert_ids)::text[])
AND system_pk = sqlc.arg(system_pk);

-- name: InsertAlert :one
INSERT INTO alert
    (id, system_pk, feed_pk, cause, effect, header, description, url, hash)
VALUES
    (sqlc.arg(id), sqlc.arg(system_pk), sqlc.arg(feed_pk), sqlc.arg(cause),sqlc.arg(effect),
     sqlc.arg(header), sqlc.arg(description), sqlc.arg(url), sqlc.arg(hash))
RETURNING pk;

-- name: InsertAlertActivePeriod :exec
INSERT INTO alert_active_period
    (alert_pk, starts_at, ends_at)
VALUES
    (sqlc.arg(alert_pk), sqlc.arg(starts_at), sqlc.arg(ends_at));

-- name: InsertAlertAgency :exec
INSERT INTO alert_agency (alert_pk, agency_pk) VALUES (sqlc.arg(alert_pk), sqlc.arg(agency_pk));

-- name: InsertAlertStop :exec
INSERT INTO alert_stop (alert_pk, stop_pk) VALUES (sqlc.arg(alert_pk), sqlc.arg(stop_pk));

-- name: InsertAlertRoute :exec
INSERT INTO alert_route (alert_pk, route_pk) VALUES (sqlc.arg(alert_pk), sqlc.arg(route_pk));

-- name: InsertAlertTrip :exec
INSERT INTO alert_trip (alert_pk, trip_pk, scheduled_trip_pk) VALUES (sqlc.arg(alert_pk), sqlc.narg(trip_pk), sqlc.narg(scheduled_trip_pk));

-- name: InsertAlertRouteType :exec
INSERT INTO alert_route_type (alert_pk, route_type) VALUES (sqlc.arg(alert_pk), sqlc.arg(route_type));

-- name: DeleteAlerts :exec
DELETE FROM alert WHERE pk = ANY(sqlc.arg(alert_pks)::bigint[]);

-- name: DeleteStaleAlerts :exec
DELETE FROM alert
WHERE
    alert.feed_pk = sqlc.arg(feed_pk)
    AND NOT alert.pk = ANY(sqlc.arg(updated_alert_pks)::bigint[]);

-- name: ListActiveAlertsForAgencies :many
SELECT alert.id, alert.cause, alert.effect
FROM alert_agency
    INNER JOIN alert ON alert_agency.alert_pk = alert.pk
WHERE alert_agency.agency_pk = ANY(sqlc.arg(agency_pks)::bigint[])
    AND EXISTS (
        SELECT 1 FROM alert_active_period
        WHERE alert_active_period.alert_pk = alert.pk
        AND (
            alert_active_period.starts_at < sqlc.arg(present_time)
            OR alert_active_period.starts_at IS NULL
        )
        AND (
            alert_active_period.ends_at > sqlc.arg(present_time)
            OR alert_active_period.ends_at IS NULL
        )
    );

-- name: ListAlertsInSystem :many
SELECT * FROM alert WHERE system_pk = sqlc.arg(system_pk) ORDER BY id ASC;

-- name: ListAlertsInSystemAndByIDs :many
SELECT * FROM alert
    WHERE system_pk = sqlc.arg(system_pk)
    AND id = ANY(sqlc.arg(ids)::text[])
ORDER BY id ASC;

-- name: GetAlertInSystem :one
SELECT alert.* FROM alert WHERE alert.system_pk = sqlc.arg(system_pk) AND alert.id = sqlc.arg(alert_id);

-- name: ListActivePeriodsForAlerts :many
SELECT alert.pk, alert_active_period.starts_at, alert_active_period.ends_at
FROM alert
    INNER JOIN alert_active_period ON alert_active_period.alert_pk = alert.pk
WHERE alert.pk = ANY(sqlc.arg(pks)::bigint[]);


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

-- name: ListAlertsWithActivePeriodsAndAllInformedEntities :many
SELECT alert.id,
       alert.cause,
       alert.effect,
       alert.header,
       alert.description,
       alert.url,
       COALESCE(
               (ARRAY_AGG(
                DISTINCT tstzrange(alert_active_period.starts_at::timestamptz, alert_active_period.ends_at::timestamptz, '[)')
                ORDER BY tstzrange(alert_active_period.starts_at::timestamptz, alert_active_period.ends_at::timestamptz, '[)'))
                FILTER ( WHERE alert_active_period.starts_at IS NOT NULL OR alert_active_period.ends_at IS NOT NULL )),
               ARRAY []::tstzrange[])::tstzrange[] AS active_periods,
       COALESCE(
               (ARRAY_AGG(DISTINCT agency.id ORDER BY agency.id) FILTER (where agency.id is not null)),
               ARRAY []::text[])::text[]           AS agencies,
       COALESCE(
               (ARRAY_AGG(DISTINCT route.id ORDER BY route.id) FILTER (where route.id is not null)),
               ARRAY []::text[])::text[]           AS routes,
       COALESCE(
               (ARRAY_AGG(DISTINCT stop.id ORDER BY stop.id) FILTER (where stop.id is not null)),
               ARRAY []::text[])::text[]           AS stops,
       COALESCE(
               (ARRAY_AGG(DISTINCT trip.id ORDER BY trip.id) FILTER (where trip.id is not null)),
               ARRAY []::text[])::text[]           AS trips,
       COALESCE(
               (ARRAY_AGG(DISTINCT scheduled_trip.id ORDER BY scheduled_trip.id) FILTER (where scheduled_trip.id is not null)),
               ARRAY []::text[])::text[]           AS scheduled_trips,
       COALESCE(
               (ARRAY_AGG(DISTINCT route_type ORDER BY route_type) FILTER (where route_type is not null)),
               ARRAY []::text[])::text[]           AS route_types
FROM alert
         LEFT JOIN alert_active_period ON alert.pk = alert_active_period.alert_pk
         LEFT JOIN alert_agency ON alert.pk = alert_agency.alert_pk
         LEFT JOIN agency ON alert_agency.agency_pk = agency.pk
         LEFT JOIN alert_route ON alert.pk = alert_route.alert_pk
         LEFT JOIN route ON alert_route.route_pk = route.pk
         LEFT JOIN alert_stop ON alert.pk = alert_stop.alert_pk
         LEFT JOIN stop ON alert_stop.stop_pk = stop.pk
         LEFT JOIN alert_trip ON alert.pk = alert_trip.alert_pk
         LEFT JOIN trip ON alert_trip.trip_pk = trip.pk
         LEFT JOIN scheduled_trip ON alert_trip.scheduled_trip_pk = scheduled_trip.pk
         LEFT JOIN alert_route_type ON alert.pk = alert_route_type.alert_pk
WHERE alert.system_pk = sqlc.arg(system_pk)
GROUP BY alert.id, alert.cause, alert.effect, alert.header, alert.description, alert.url;
