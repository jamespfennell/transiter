// Code generated by sqlc. DO NOT EDIT.
// versions:
//   sqlc v1.16.0
// source: system_queries.sql

package db

import (
	"context"
	"database/sql"
)

const countAgenciesInSystem = `-- name: CountAgenciesInSystem :one
SELECT COUNT(*) FROM agency WHERE system_pk = $1
`

func (q *Queries) CountAgenciesInSystem(ctx context.Context, systemPk int64) (int64, error) {
	row := q.db.QueryRow(ctx, countAgenciesInSystem, systemPk)
	var count int64
	err := row.Scan(&count)
	return count, err
}

const countFeedsInSystem = `-- name: CountFeedsInSystem :one
SELECT COUNT(*) FROM feed WHERE system_pk = $1
`

func (q *Queries) CountFeedsInSystem(ctx context.Context, systemPk int64) (int64, error) {
	row := q.db.QueryRow(ctx, countFeedsInSystem, systemPk)
	var count int64
	err := row.Scan(&count)
	return count, err
}

const countRoutesInSystem = `-- name: CountRoutesInSystem :one
SELECT COUNT(*) FROM route WHERE system_pk = $1
`

func (q *Queries) CountRoutesInSystem(ctx context.Context, systemPk int64) (int64, error) {
	row := q.db.QueryRow(ctx, countRoutesInSystem, systemPk)
	var count int64
	err := row.Scan(&count)
	return count, err
}

const countStopsInSystem = `-- name: CountStopsInSystem :one
SELECT COUNT(*) FROM stop WHERE system_pk = $1
`

func (q *Queries) CountStopsInSystem(ctx context.Context, systemPk int64) (int64, error) {
	row := q.db.QueryRow(ctx, countStopsInSystem, systemPk)
	var count int64
	err := row.Scan(&count)
	return count, err
}

const countTransfersInSystem = `-- name: CountTransfersInSystem :one
SELECT COUNT(*) FROM transfer WHERE system_pk = $1
`

func (q *Queries) CountTransfersInSystem(ctx context.Context, systemPk sql.NullInt64) (int64, error) {
	row := q.db.QueryRow(ctx, countTransfersInSystem, systemPk)
	var count int64
	err := row.Scan(&count)
	return count, err
}

const deleteSystem = `-- name: DeleteSystem :exec
DELETE FROM system WHERE pk = $1
`

func (q *Queries) DeleteSystem(ctx context.Context, pk int64) error {
	_, err := q.db.Exec(ctx, deleteSystem, pk)
	return err
}

const getSystem = `-- name: GetSystem :one
SELECT pk, id, name, timezone, status FROM system
WHERE id = $1 LIMIT 1
`

func (q *Queries) GetSystem(ctx context.Context, id string) (System, error) {
	row := q.db.QueryRow(ctx, getSystem, id)
	var i System
	err := row.Scan(
		&i.Pk,
		&i.ID,
		&i.Name,
		&i.Timezone,
		&i.Status,
	)
	return i, err
}

const insertSystem = `-- name: InsertSystem :one
INSERT INTO system (id, name, status) 
VALUES ($1, $2, $3)
RETURNING pk
`

type InsertSystemParams struct {
	ID     string
	Name   string
	Status string
}

func (q *Queries) InsertSystem(ctx context.Context, arg InsertSystemParams) (int64, error) {
	row := q.db.QueryRow(ctx, insertSystem, arg.ID, arg.Name, arg.Status)
	var pk int64
	err := row.Scan(&pk)
	return pk, err
}

const listSystems = `-- name: ListSystems :many
SELECT pk, id, name, timezone, status FROM system ORDER BY id
`

func (q *Queries) ListSystems(ctx context.Context) ([]System, error) {
	rows, err := q.db.Query(ctx, listSystems)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []System
	for rows.Next() {
		var i System
		if err := rows.Scan(
			&i.Pk,
			&i.ID,
			&i.Name,
			&i.Timezone,
			&i.Status,
		); err != nil {
			return nil, err
		}
		items = append(items, i)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return items, nil
}

const updateSystem = `-- name: UpdateSystem :exec
UPDATE system 
SET
    name = $1
WHERE pk = $2
`

type UpdateSystemParams struct {
	Name string
	Pk   int64
}

func (q *Queries) UpdateSystem(ctx context.Context, arg UpdateSystemParams) error {
	_, err := q.db.Exec(ctx, updateSystem, arg.Name, arg.Pk)
	return err
}

const updateSystemStatus = `-- name: UpdateSystemStatus :exec
UPDATE system 
SET
    status = $1
WHERE pk = $2
`

type UpdateSystemStatusParams struct {
	Status string
	Pk     int64
}

func (q *Queries) UpdateSystemStatus(ctx context.Context, arg UpdateSystemStatusParams) error {
	_, err := q.db.Exec(ctx, updateSystemStatus, arg.Status, arg.Pk)
	return err
}
