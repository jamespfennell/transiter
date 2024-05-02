-- name: InsertTransfer :exec
INSERT INTO transfer
    (id, system_pk, feed_pk, from_stop_pk, to_stop_pk,
     type, min_transfer_time)
VALUES
    (sqlc.arg(id), sqlc.arg(system_pk), sqlc.arg(feed_pk),
     sqlc.arg(from_stop_pk), sqlc.arg(to_stop_pk), sqlc.arg(type),
     sqlc.arg(min_transfer_time));

-- name: DeleteTransfers :exec
DELETE FROM transfer
WHERE transfer.feed_pk = sqlc.arg(feed_pk);

-- name: ListTransfersInSystem :many
SELECT transfer.* FROM transfer
WHERE transfer.system_pk = sqlc.arg(system_pk)
ORDER BY transfer.id;

-- name: GetTransfer :one
SELECT transfer.* FROM transfer
    INNER JOIN system ON transfer.system_pk = system.pk
    WHERE system.id = sqlc.arg(system_id)
    AND transfer.id = sqlc.arg(transfer_id);

-- name: ListTransfersFromStops :many
  SELECT transfer.*
  FROM transfer
  WHERE transfer.from_stop_pk = ANY(sqlc.arg(from_stop_pks)::bigint[]);
