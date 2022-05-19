// Code generated by sqlc. DO NOT EDIT.
// versions:
//   sqlc v1.13.0
// source: stop_queries.sql

package db

import (
	"context"
	"database/sql"

	"github.com/jackc/pgtype"
)

const deleteStaleStops = `-- name: DeleteStaleStops :many
DELETE FROM stop
USING feed_update
WHERE 
    feed_update.pk = stop.source_pk
    AND feed_update.feed_pk = $1
    AND feed_update.pk != $2
RETURNING stop.id
`

type DeleteStaleStopsParams struct {
	FeedPk   int64
	UpdatePk int64
}

func (q *Queries) DeleteStaleStops(ctx context.Context, arg DeleteStaleStopsParams) ([]string, error) {
	rows, err := q.db.Query(ctx, deleteStaleStops, arg.FeedPk, arg.UpdatePk)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []string
	for rows.Next() {
		var id string
		if err := rows.Scan(&id); err != nil {
			return nil, err
		}
		items = append(items, id)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return items, nil
}

const insertStop = `-- name: InsertStop :one
INSERT INTO stop
    (id, system_pk, source_pk, name, longitude, latitude,
     url, code, description, platform_code, timezone, type,
     wheelchair_boarding, zone_id)
VALUES
    ($1, $2, $3, $4, $5,
     $6, $7, $8, $9, $10,
     $11, $12, $13, $14)
RETURNING pk
`

type InsertStopParams struct {
	ID                 string
	SystemPk           int64
	SourcePk           int64
	Name               sql.NullString
	Longitude          pgtype.Numeric
	Latitude           pgtype.Numeric
	Url                sql.NullString
	Code               sql.NullString
	Description        sql.NullString
	PlatformCode       sql.NullString
	Timezone           sql.NullString
	Type               string
	WheelchairBoarding string
	ZoneID             sql.NullString
}

func (q *Queries) InsertStop(ctx context.Context, arg InsertStopParams) (int64, error) {
	row := q.db.QueryRow(ctx, insertStop,
		arg.ID,
		arg.SystemPk,
		arg.SourcePk,
		arg.Name,
		arg.Longitude,
		arg.Latitude,
		arg.Url,
		arg.Code,
		arg.Description,
		arg.PlatformCode,
		arg.Timezone,
		arg.Type,
		arg.WheelchairBoarding,
		arg.ZoneID,
	)
	var pk int64
	err := row.Scan(&pk)
	return pk, err
}

const mapStopIdToStationPk = `-- name: MapStopIdToStationPk :many
WITH RECURSIVE 
ancestor AS (
	SELECT 
    id stop_id, 
    pk station_pk, 
    parent_stop_pk,
    (type = 'STATION' OR type = 'GROUPED_STATION') is_station 
    FROM stop
	  WHERE	stop.system_pk = $1
	UNION
	SELECT
    child.stop_id stop_id, 
    parent.pk station_pk, 
    parent.parent_stop_pk, 
    (parent.type = 'STATION' OR parent.type = 'GROUPED_STATION') is_station 
		FROM stop parent
		INNER JOIN ancestor child 
    ON child.parent_stop_pk = parent.pk
    AND NOT child.is_station
)
SELECT stop_id, station_pk
  FROM ancestor
  WHERE parent_stop_pk IS NULL
  OR is_station
`

type MapStopIdToStationPkRow struct {
	StopID    string
	StationPk int64
}

func (q *Queries) MapStopIdToStationPk(ctx context.Context, systemPk int64) ([]MapStopIdToStationPkRow, error) {
	rows, err := q.db.Query(ctx, mapStopIdToStationPk, systemPk)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []MapStopIdToStationPkRow
	for rows.Next() {
		var i MapStopIdToStationPkRow
		if err := rows.Scan(&i.StopID, &i.StationPk); err != nil {
			return nil, err
		}
		items = append(items, i)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return items, nil
}

const mapStopPkToIdInSystem = `-- name: MapStopPkToIdInSystem :many
SELECT pk, id FROM stop WHERE system_pk = $1
`

type MapStopPkToIdInSystemRow struct {
	Pk int64
	ID string
}

func (q *Queries) MapStopPkToIdInSystem(ctx context.Context, systemPk int64) ([]MapStopPkToIdInSystemRow, error) {
	rows, err := q.db.Query(ctx, mapStopPkToIdInSystem, systemPk)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []MapStopPkToIdInSystemRow
	for rows.Next() {
		var i MapStopPkToIdInSystemRow
		if err := rows.Scan(&i.Pk, &i.ID); err != nil {
			return nil, err
		}
		items = append(items, i)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return items, nil
}

const mapStopPkToStationPk = `-- name: MapStopPkToStationPk :many
WITH RECURSIVE 
ancestor AS (
	SELECT 
    pk stop_pk,
    pk station_pk, 
    parent_stop_pk,
    (type = 'STATION' OR type = 'GROUPED_STATION') is_station 
    FROM stop
        WHERE stop.pk = ANY($1::bigint[])
	UNION
	SELECT
    child.stop_pk stop_pk,
    parent.pk station_pk, 
    parent.parent_stop_pk, 
    (parent.type = 'STATION' OR parent.type = 'GROUPED_STATION') is_station 
		FROM stop parent
		INNER JOIN ancestor child 
    ON child.parent_stop_pk = parent.pk
    AND NOT child.is_station
)
SELECT stop_pk, station_pk
  FROM ancestor
  WHERE parent_stop_pk IS NULL
  OR is_station
`

type MapStopPkToStationPkRow struct {
	StopPk    int64
	StationPk int64
}

func (q *Queries) MapStopPkToStationPk(ctx context.Context, stopPks []int64) ([]MapStopPkToStationPkRow, error) {
	rows, err := q.db.Query(ctx, mapStopPkToStationPk, stopPks)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []MapStopPkToStationPkRow
	for rows.Next() {
		var i MapStopPkToStationPkRow
		if err := rows.Scan(&i.StopPk, &i.StationPk); err != nil {
			return nil, err
		}
		items = append(items, i)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return items, nil
}

const mapStopsInSystem = `-- name: MapStopsInSystem :many
SELECT pk, id from stop
WHERE
    system_pk = $1
    AND id = ANY($2::text[])
`

type MapStopsInSystemParams struct {
	SystemPk int64
	StopIds  []string
}

type MapStopsInSystemRow struct {
	Pk int64
	ID string
}

func (q *Queries) MapStopsInSystem(ctx context.Context, arg MapStopsInSystemParams) ([]MapStopsInSystemRow, error) {
	rows, err := q.db.Query(ctx, mapStopsInSystem, arg.SystemPk, arg.StopIds)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []MapStopsInSystemRow
	for rows.Next() {
		var i MapStopsInSystemRow
		if err := rows.Scan(&i.Pk, &i.ID); err != nil {
			return nil, err
		}
		items = append(items, i)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return items, nil
}

const updateStop = `-- name: UpdateStop :exec
UPDATE stop SET
    source_pk = $1,
    name = $2,
    longitude = $3,
    latitude = $4,
    url = $5,
    code = $6,
    description = $7,
    platform_code = $8,
    timezone = $9, 
    type = $10, 
    wheelchair_boarding = $11,
    zone_id = $12,
    parent_stop_pk = NULL
WHERE
    pk = $13
`

type UpdateStopParams struct {
	SourcePk           int64
	Name               sql.NullString
	Longitude          pgtype.Numeric
	Latitude           pgtype.Numeric
	Url                sql.NullString
	Code               sql.NullString
	Description        sql.NullString
	PlatformCode       sql.NullString
	Timezone           sql.NullString
	Type               string
	WheelchairBoarding string
	ZoneID             sql.NullString
	Pk                 int64
}

func (q *Queries) UpdateStop(ctx context.Context, arg UpdateStopParams) error {
	_, err := q.db.Exec(ctx, updateStop,
		arg.SourcePk,
		arg.Name,
		arg.Longitude,
		arg.Latitude,
		arg.Url,
		arg.Code,
		arg.Description,
		arg.PlatformCode,
		arg.Timezone,
		arg.Type,
		arg.WheelchairBoarding,
		arg.ZoneID,
		arg.Pk,
	)
	return err
}

const updateStopParent = `-- name: UpdateStopParent :exec
UPDATE stop SET
    parent_stop_pk = $1
WHERE
    pk = $2
`

type UpdateStopParentParams struct {
	ParentStopPk sql.NullInt64
	Pk           int64
}

func (q *Queries) UpdateStopParent(ctx context.Context, arg UpdateStopParentParams) error {
	_, err := q.db.Exec(ctx, updateStopParent, arg.ParentStopPk, arg.Pk)
	return err
}
