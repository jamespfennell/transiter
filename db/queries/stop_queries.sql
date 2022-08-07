-- name: MapStopPkToIdInSystem :many
SELECT pk, id FROM stop WHERE system_pk = sqlc.arg(system_pk);

-- name: InsertStop :one
INSERT INTO stop
    (id, system_pk, source_pk, name, longitude, latitude,
     url, code, description, platform_code, timezone, type,
     wheelchair_boarding, zone_id)
VALUES
    (sqlc.arg(id), sqlc.arg(system_pk), sqlc.arg(source_pk), sqlc.arg(name), sqlc.arg(longitude),
     sqlc.arg(latitude), sqlc.arg(url), sqlc.arg(code), sqlc.arg(description), sqlc.arg(platform_code),
     sqlc.arg(timezone), sqlc.arg(type), sqlc.arg(wheelchair_boarding), sqlc.arg(zone_id))
RETURNING pk;

-- name: UpdateStop :exec
UPDATE stop SET
    source_pk = sqlc.arg(source_pk),
    name = sqlc.arg(name),
    longitude = sqlc.arg(longitude),
    latitude = sqlc.arg(latitude),
    url = sqlc.arg(url),
    code = sqlc.arg(code),
    description = sqlc.arg(description),
    platform_code = sqlc.arg(platform_code),
    timezone = sqlc.arg(timezone), 
    type = sqlc.arg(type), 
    wheelchair_boarding = sqlc.arg(wheelchair_boarding),
    zone_id = sqlc.arg(zone_id),
    parent_stop_pk = NULL
WHERE
    pk = sqlc.arg(pk);

-- name: UpdateStopParent :exec
UPDATE stop SET
    parent_stop_pk = sqlc.arg(parent_stop_pk)
WHERE
    pk = sqlc.arg(pk);

-- name: DeleteStaleStops :many
DELETE FROM stop
USING feed_update
WHERE 
    feed_update.pk = stop.source_pk
    AND feed_update.feed_pk = sqlc.arg(feed_pk)
    AND feed_update.pk != sqlc.arg(update_pk)
RETURNING stop.id;

-- name: MapStopIDToStationPk :many
WITH RECURSIVE 
ancestor AS (
	SELECT 
    id stop_id, 
    pk station_pk, 
    parent_stop_pk,
    (type = 'STATION') is_station 
    FROM stop
	  WHERE	stop.system_pk = sqlc.arg(system_pk)
	UNION
	SELECT
    child.stop_id stop_id, 
    parent.pk station_pk, 
    parent.parent_stop_pk, 
    (parent.type = 'STATION') is_station 
		FROM stop parent
		INNER JOIN ancestor child 
    ON child.parent_stop_pk = parent.pk
    AND NOT child.is_station
)
SELECT stop_id, station_pk
  FROM ancestor
  WHERE parent_stop_pk IS NULL
  OR is_station;


-- name: MapStopPkToStationPk :many
WITH RECURSIVE 
ancestor AS (
	SELECT 
    pk stop_pk,
    pk station_pk, 
    parent_stop_pk,
    (type = 'STATION') is_station 
    FROM stop
        WHERE stop.pk = ANY(sqlc.arg(stop_pks)::bigint[])
	UNION
	SELECT
    child.stop_pk stop_pk,
    parent.pk station_pk, 
    parent.parent_stop_pk, 
    (parent.type = 'STATION') is_station 
		FROM stop parent
		INNER JOIN ancestor child 
    ON child.parent_stop_pk = parent.pk
    AND NOT child.is_station
)
SELECT stop_pk, station_pk
  FROM ancestor
  WHERE parent_stop_pk IS NULL
  OR is_station;


-- name: MapStopPkToDescendentPks :many
WITH RECURSIVE descendent AS (
	SELECT
    stop.pk root_stop_pk,
    stop.pk descendent_stop_pk
    FROM stop
        WHERE stop.pk = ANY(sqlc.arg(stop_pks)::bigint[])
	UNION
	SELECT
    descendent.root_stop_pk root_stop_pk,
    child.pk descendent_stop_pk
		FROM stop child
		INNER JOIN descendent
    ON child.parent_stop_pk = descendent.descendent_stop_pk
)
SELECT root_stop_pk, descendent_stop_pk FROM descendent;


-- name: MapStopsInSystem :many
SELECT pk, id from stop
WHERE
    system_pk = sqlc.arg(system_pk)
    AND id = ANY(sqlc.arg(stop_ids)::text[]);


-- name: ListStopPreviews :many
SELECT stop.pk, stop.id stop_id, stop.name, system.id system_id
FROM stop
    INNER JOIN system on stop.system_pk = system.pk
WHERE stop.pk = ANY(sqlc.arg(stop_pks)::bigint[]);

-- name: ListChildrenForStops :many
SELECT parent_stop_pk parent_pk, pk child_pk
FROM stop
WHERE stop.parent_stop_pk = ANY(sqlc.arg(stop_pks)::bigint[]);
