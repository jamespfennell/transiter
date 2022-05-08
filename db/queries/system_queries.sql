-- name: InsertSystem :one
INSERT INTO system (id, name, status) 
VALUES (sqlc.arg(id), sqlc.arg(name), sqlc.arg(status))
RETURNING pk;

-- name: UpdateSystem :exec
UPDATE system SET name = sqlc.arg(name) WHERE pk = sqlc.arg(pk);

-- name: DeleteSystem :exec
DELETE FROM system WHERE pk = sqlc.arg(pk);
