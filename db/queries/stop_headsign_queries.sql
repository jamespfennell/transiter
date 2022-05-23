-- name: InsertStopHeadSignRule :exec
INSERT INTO stop_headsign_rule
    (source_pk, priority, stop_pk, track, headsign)
VALUES
    (sqlc.arg(source_pk), sqlc.arg(priority), sqlc.arg(stop_pk),
     sqlc.arg(track), sqlc.arg(headsign));

-- name: DeleteStopHeadsignRules :exec
DELETE FROM stop_headsign_rule
USING feed_update
WHERE feed_update.pk = stop_headsign_rule.source_pk
AND feed_update.feed_pk = sqlc.arg(source_pk);
