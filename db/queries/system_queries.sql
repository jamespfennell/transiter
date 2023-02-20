-- name: GetSystem :one
SELECT * FROM system
WHERE id = $1 LIMIT 1;

-- name: ListSystems :many
SELECT * FROM system ORDER BY id;

-- name: CountAgenciesInSystem :one
SELECT COUNT(*) FROM agency WHERE system_pk = $1;

-- name: CountFeedsInSystem :one
SELECT COUNT(*) FROM feed WHERE system_pk = $1;

-- name: CountRoutesInSystem :one
SELECT COUNT(*) FROM route WHERE system_pk = $1;

-- name: CountStopsInSystem :one
SELECT COUNT(*) FROM stop WHERE system_pk = $1;

-- name: CountTransfersInSystem :one
SELECT COUNT(*) FROM transfer WHERE system_pk = $1;

-- name: InsertSystem :one
INSERT INTO system (id, name, status) 
VALUES (sqlc.arg(id), sqlc.arg(name), sqlc.arg(status))
RETURNING pk;

-- name: UpdateSystem :exec
UPDATE system 
SET
    name = sqlc.arg(name)
WHERE pk = sqlc.arg(pk);

-- name: UpdateSystemStatus :exec
UPDATE system 
SET
    status = sqlc.arg(status)
WHERE pk = sqlc.arg(pk);

-- name: DeleteSystem :exec
DELETE FROM system WHERE pk = sqlc.arg(pk);
