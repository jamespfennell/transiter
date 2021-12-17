-- name: MapAgencyPkToIdInSystem :many
SELECT pk, id FROM agency WHERE system_pk = sqlc.arg(system_pk);

-- name: InsertAgency :exec
INSERT INTO agency
    (id, system_pk, source_pk, name, url, timezone, language, phone, fare_url, email)
VALUES
    (sqlc.arg(id), sqlc.arg(system_pk), sqlc.arg(source_pk), sqlc.arg(name), sqlc.arg(url),
     sqlc.arg(timezone), sqlc.arg(language), sqlc.arg(phone), sqlc.arg(fare_url), sqlc.arg(email));

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

-- name: DeleteAgency :exec
DELETE FROM agency WHERE pk = sqlc.arg(pk);
