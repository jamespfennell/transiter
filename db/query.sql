-- name: GetSystem :one
SELECT * FROM system
WHERE id = $1 LIMIT 1;

-- name: ListSystems :many
SELECT * FROM system;

-- name: CountSystems :one
SELECT COUNT(*) FROM system;

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
