-- name: InsertStopHeadSignRule :exec
INSERT INTO stop_headsign_rule
    (feed_pk, priority, stop_pk, track, headsign)
VALUES
    (sqlc.arg(feed_pk), sqlc.arg(priority), sqlc.arg(stop_pk),
     sqlc.arg(track), sqlc.arg(headsign));

-- name: DeleteStopHeadsignRules :exec
DELETE FROM stop_headsign_rule
WHERE stop_headsign_rule.feed_pk = sqlc.arg(feed_pk);

-- name: ListStopHeadsignRulesForStops :many
SELECT * FROM stop_headsign_rule
WHERE stop_pk = ANY(sqlc.arg(stop_pks)::bigint[])
ORDER BY priority ASC;
