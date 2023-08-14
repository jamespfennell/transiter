// Code generated by sqlc. DO NOT EDIT.
// versions:
//   sqlc v1.17.2
// source: shape_queries.sql

package db

import (
	"context"
)

const deleteShapes = `-- name: DeleteShapes :exec
DELETE FROM shape
WHERE feed_pk = $1
OR (system_pk = $2 AND
   id = ANY($3::text[]))
`

type DeleteShapesParams struct {
	FeedPk          int64
	SystemPk        int64
	UpdatedShapeIds []string
}

func (q *Queries) DeleteShapes(ctx context.Context, arg DeleteShapesParams) error {
	_, err := q.db.Exec(ctx, deleteShapes, arg.FeedPk, arg.SystemPk, arg.UpdatedShapeIds)
	return err
}

const getShape = `-- name: GetShape :one
SELECT pk, id, system_pk, feed_pk, shape
FROM shape
WHERE system_pk = $1 AND id = $2
`

type GetShapeParams struct {
	SystemPk int64
	ShapeID  string
}

func (q *Queries) GetShape(ctx context.Context, arg GetShapeParams) (Shape, error) {
	row := q.db.QueryRow(ctx, getShape, arg.SystemPk, arg.ShapeID)
	var i Shape
	err := row.Scan(
		&i.Pk,
		&i.ID,
		&i.SystemPk,
		&i.FeedPk,
		&i.Shape,
	)
	return i, err
}

const insertShape = `-- name: InsertShape :one
INSERT INTO shape
    (id, system_pk, feed_pk, shape)
VALUES
    ($1, $2, $3, $4)
RETURNING pk
`

type InsertShapeParams struct {
	ID       string
	SystemPk int64
	FeedPk   int64
	Shape    []byte
}

func (q *Queries) InsertShape(ctx context.Context, arg InsertShapeParams) (int64, error) {
	row := q.db.QueryRow(ctx, insertShape,
		arg.ID,
		arg.SystemPk,
		arg.FeedPk,
		arg.Shape,
	)
	var pk int64
	err := row.Scan(&pk)
	return pk, err
}

const listShapes = `-- name: ListShapes :many
SELECT pk, id, system_pk, feed_pk, shape
FROM shape
WHERE system_pk = $1
   AND id >= $2
   AND (
      NOT $3::bool OR
      id = ANY($4::text[])
    )
ORDER BY id
LIMIT $5
`

type ListShapesParams struct {
	SystemPk               int64
	FirstShapeID           string
	OnlyReturnSpecifiedIds bool
	ShapeIds               []string
	NumShapes              int32
}

func (q *Queries) ListShapes(ctx context.Context, arg ListShapesParams) ([]Shape, error) {
	rows, err := q.db.Query(ctx, listShapes,
		arg.SystemPk,
		arg.FirstShapeID,
		arg.OnlyReturnSpecifiedIds,
		arg.ShapeIds,
		arg.NumShapes,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []Shape
	for rows.Next() {
		var i Shape
		if err := rows.Scan(
			&i.Pk,
			&i.ID,
			&i.SystemPk,
			&i.FeedPk,
			&i.Shape,
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

const listShapesAndTrips = `-- name: ListShapesAndTrips :many
SELECT shape.pk, shape.id, shape.system_pk, shape.feed_pk, shape.shape, scheduled_trip.id trip_id
FROM shape
INNER JOIN scheduled_trip ON scheduled_trip.shape_pk = shape.pk
WHERE system_pk = $1
`

type ListShapesAndTripsRow struct {
	Pk       int64
	ID       string
	SystemPk int64
	FeedPk   int64
	Shape    []byte
	TripID   string
}

func (q *Queries) ListShapesAndTrips(ctx context.Context, systemPk int64) ([]ListShapesAndTripsRow, error) {
	rows, err := q.db.Query(ctx, listShapesAndTrips, systemPk)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []ListShapesAndTripsRow
	for rows.Next() {
		var i ListShapesAndTripsRow
		if err := rows.Scan(
			&i.Pk,
			&i.ID,
			&i.SystemPk,
			&i.FeedPk,
			&i.Shape,
			&i.TripID,
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
