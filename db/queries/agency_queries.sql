-- name: InsertAgency :one
INSERT INTO agency
    (id, system_pk, source_pk, name, url, timezone, language, phone, fare_url, email)
VALUES
    (sqlc.arg(id), sqlc.arg(system_pk), sqlc.arg(source_pk), sqlc.arg(name), sqlc.arg(url),
     sqlc.arg(timezone), sqlc.arg(language), sqlc.arg(phone), sqlc.arg(fare_url), sqlc.arg(email))
RETURNING pk;

-- name: UpdateAgency :exec
UPDATE agency SET
    source_pk = sqlc.arg(source_pk),
    name = sqlc.arg(name),
    url = sqlc.arg(url),
    timezone = sqlc.arg(timezone), 
    language = sqlc.arg(language), 
    phone = sqlc.arg(phone), 
    fare_url = sqlc.arg(fare_url), 
    email = sqlc.arg(email)
WHERE
    pk = sqlc.arg(pk);

-- name: DeleteStaleAgencies :exec
DELETE FROM agency
USING feed_update
WHERE 
    feed_update.pk = agency.source_pk
    AND feed_update.feed_pk = sqlc.arg(feed_pk)
    AND NOT agency.pk = ANY(sqlc.arg(updated_agency_pks)::bigint[]);

-- name: ListAgencies :many
SELECT agency.* FROM agency WHERE system_pk = $1 ORDER BY id;

-- name: ListAgenciesByPk :many
SELECT agency.* FROM agency WHERE pk = ANY(sqlc.arg(pk)::bigint[]);

-- name: GetAgency :one
SELECT agency.* FROM agency
WHERE agency.system_pk = sqlc.arg(system_pk)
    AND agency.id = sqlc.arg(agency_id);

-- name: MapAgencyPkToId :many
SELECT pk, id FROM agency WHERE system_pk = sqlc.arg(system_pk);
