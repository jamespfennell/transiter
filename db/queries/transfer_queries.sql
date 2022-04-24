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
