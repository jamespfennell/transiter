-- name: InsertScheduledService :one
INSERT INTO scheduled_service
    (id, system_pk, monday, tuesday, wednesday, thursday, friday, saturday, sunday, start_date, end_date, feed_pk)
VALUES
    (sqlc.arg(id), sqlc.arg(system_pk), sqlc.arg(monday), sqlc.arg(tuesday), sqlc.arg(wednesday), sqlc.arg(thursday), sqlc.arg(friday), sqlc.arg(saturday), sqlc.arg(sunday), sqlc.arg(start_date), sqlc.arg(end_date), sqlc.arg(feed_pk))
RETURNING pk;

-- name: UpdateScheduledService :exec
UPDATE scheduled_service SET
    system_pk = sqlc.arg(system_pk),
    monday = sqlc.arg(monday),
    tuesday = sqlc.arg(tuesday),
    wednesday = sqlc.arg(wednesday),
    thursday = sqlc.arg(thursday),
    friday = sqlc.arg(friday),
    saturday = sqlc.arg(saturday),
    sunday = sqlc.arg(sunday),
    start_date = sqlc.arg(start_date),
    end_date = sqlc.arg(end_date),
    feed_pk = sqlc.arg(feed_pk)
WHERE pk = sqlc.arg(pk);

-- name: InsertScheduledServiceAddition :exec
INSERT INTO scheduled_service_addition
    (service_pk, date)
VALUES
    (sqlc.arg(service_pk), sqlc.arg(date));

-- name: DeleteScheduledServiceAdditions :exec
DELETE FROM scheduled_service_addition
WHERE service_pk = ANY(sqlc.arg(service_pks)::bigint[]);

-- name: InsertScheduledServiceRemoval :exec
INSERT INTO scheduled_service_removal
    (service_pk, date)
VALUES
    (sqlc.arg(service_pk), sqlc.arg(date));

-- name: DeleteScheduledServiceRemovals :exec
DELETE FROM scheduled_service_removal
WHERE service_pk = ANY(sqlc.arg(service_pks)::bigint[]);

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

-- name: MapScheduledServiceIDToPkInSystem :many
SELECT id, pk FROM scheduled_service
WHERE
    system_pk = sqlc.arg(system_pk)
    AND (
        NOT sqlc.arg(filter_by_scheduled_service_id)::bool
        OR id = ANY(sqlc.arg(scheduled_service_ids)::text[])
    );

-- name: DeleteStaleScheduledServices :exec
DELETE FROM scheduled_service
WHERE
    feed_pk = sqlc.arg(feed_pk)
    AND NOT pk = ANY(sqlc.arg(updated_scheduled_service_pks)::bigint[]);
