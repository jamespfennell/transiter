-- name: InsertTransfer :exec
INSERT INTO transfer
    (system_pk, source_pk, config_source_pk, from_stop_pk, to_stop_pk,
     type, min_transfer_time, distance)
VALUES
    (sqlc.arg(system_pk), sqlc.arg(source_pk), NULL,
     sqlc.arg(from_stop_pk), sqlc.arg(to_stop_pk), sqlc.arg(type),
     sqlc.arg(min_transfer_time), NULL);

-- name: DeleteStaleTransfers :exec
DELETE FROM transfer
USING feed_update
WHERE 
    feed_update.pk = transfer.source_pk
    AND feed_update.feed_pk = sqlc.arg(feed_pk)
    AND feed_update.pk != sqlc.arg(update_pk);


-- name: ListTransfersInSystem :many
SELECT
    transfer.*,
    from_stop.id from_stop_id, from_stop.name from_stop_name, from_system.id from_system_id,
    to_stop.id to_stop_id, to_stop.name to_stop_name, to_system.id to_system_id
FROM transfer
    INNER JOIN stop from_stop ON from_stop.pk = transfer.from_stop_pk
    INNER JOIN system from_system ON from_stop.system_pk = from_system.pk
    INNER JOIN stop to_stop ON to_stop.pk = transfer.to_stop_pk
    INNER JOIN system to_system ON to_stop.system_pk = to_system.pk
WHERE transfer.system_pk = $1
ORDER BY transfer.pk;

-- name: ListTransfersFromStops :many
  SELECT transfer.*
  FROM transfer
  WHERE transfer.from_stop_pk = ANY(sqlc.arg(from_stop_pks)::bigint[]);
