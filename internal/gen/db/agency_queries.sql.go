// Code generated by sqlc. DO NOT EDIT.
// versions:
//   sqlc v1.13.0
// source: agency_queries.sql

package db

import (
	"context"
	"database/sql"
)

const deleteStaleAgencies = `-- name: DeleteStaleAgencies :many
DELETE FROM agency
USING feed_update
WHERE 
    feed_update.pk = agency.source_pk
    AND feed_update.feed_pk = $1
    AND feed_update.pk != $2
RETURNING agency.id
`

type DeleteStaleAgenciesParams struct {
	FeedPk   int64
	UpdatePk int64
}

func (q *Queries) DeleteStaleAgencies(ctx context.Context, arg DeleteStaleAgenciesParams) ([]string, error) {
	rows, err := q.db.Query(ctx, deleteStaleAgencies, arg.FeedPk, arg.UpdatePk)
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

const getAgencyInSystem = `-- name: GetAgencyInSystem :one
SELECT agency.pk, agency.id, agency.system_pk, agency.source_pk, agency.name, agency.url, agency.timezone, agency.language, agency.phone, agency.fare_url, agency.email FROM agency
WHERE agency.system_pk = $1
    AND agency.id = $2
`

type GetAgencyInSystemParams struct {
	SystemPk int64
	AgencyID string
}

func (q *Queries) GetAgencyInSystem(ctx context.Context, arg GetAgencyInSystemParams) (Agency, error) {
	row := q.db.QueryRow(ctx, getAgencyInSystem, arg.SystemPk, arg.AgencyID)
	var i Agency
	err := row.Scan(
		&i.Pk,
		&i.ID,
		&i.SystemPk,
		&i.SourcePk,
		&i.Name,
		&i.Url,
		&i.Timezone,
		&i.Language,
		&i.Phone,
		&i.FareUrl,
		&i.Email,
	)
	return i, err
}

const insertAgency = `-- name: InsertAgency :one
INSERT INTO agency
    (id, system_pk, source_pk, name, url, timezone, language, phone, fare_url, email)
VALUES
    ($1, $2, $3, $4, $5,
     $6, $7, $8, $9, $10)
RETURNING pk
`

type InsertAgencyParams struct {
	ID       string
	SystemPk int64
	SourcePk int64
	Name     string
	Url      string
	Timezone string
	Language sql.NullString
	Phone    sql.NullString
	FareUrl  sql.NullString
	Email    sql.NullString
}

func (q *Queries) InsertAgency(ctx context.Context, arg InsertAgencyParams) (int64, error) {
	row := q.db.QueryRow(ctx, insertAgency,
		arg.ID,
		arg.SystemPk,
		arg.SourcePk,
		arg.Name,
		arg.Url,
		arg.Timezone,
		arg.Language,
		arg.Phone,
		arg.FareUrl,
		arg.Email,
	)
	var pk int64
	err := row.Scan(&pk)
	return pk, err
}

const listAgenciesInSystem = `-- name: ListAgenciesInSystem :many
SELECT agency.pk, agency.id, agency.system_pk, agency.source_pk, agency.name, agency.url, agency.timezone, agency.language, agency.phone, agency.fare_url, agency.email FROM agency WHERE system_pk = $1 ORDER BY id
`

func (q *Queries) ListAgenciesInSystem(ctx context.Context, systemPk int64) ([]Agency, error) {
	rows, err := q.db.Query(ctx, listAgenciesInSystem, systemPk)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []Agency
	for rows.Next() {
		var i Agency
		if err := rows.Scan(
			&i.Pk,
			&i.ID,
			&i.SystemPk,
			&i.SourcePk,
			&i.Name,
			&i.Url,
			&i.Timezone,
			&i.Language,
			&i.Phone,
			&i.FareUrl,
			&i.Email,
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

const mapAgencyPkToIdInSystem = `-- name: MapAgencyPkToIdInSystem :many
SELECT pk, id FROM agency WHERE system_pk = $1
`

type MapAgencyPkToIdInSystemRow struct {
	Pk int64
	ID string
}

func (q *Queries) MapAgencyPkToIdInSystem(ctx context.Context, systemPk int64) ([]MapAgencyPkToIdInSystemRow, error) {
	rows, err := q.db.Query(ctx, mapAgencyPkToIdInSystem, systemPk)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []MapAgencyPkToIdInSystemRow
	for rows.Next() {
		var i MapAgencyPkToIdInSystemRow
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

const updateAgency = `-- name: UpdateAgency :exec
UPDATE agency SET
    source_pk = $1,
    name = $2,
    url = $3,
    timezone = $4, 
    language = $5, 
    phone = $6, 
    fare_url = $7, 
    email = $8
WHERE
    pk = $9
`

type UpdateAgencyParams struct {
	SourcePk int64
	Name     string
	Url      string
	Timezone string
	Language sql.NullString
	Phone    sql.NullString
	FareUrl  sql.NullString
	Email    sql.NullString
	Pk       int64
}

func (q *Queries) UpdateAgency(ctx context.Context, arg UpdateAgencyParams) error {
	_, err := q.db.Exec(ctx, updateAgency,
		arg.SourcePk,
		arg.Name,
		arg.Url,
		arg.Timezone,
		arg.Language,
		arg.Phone,
		arg.FareUrl,
		arg.Email,
		arg.Pk,
	)
	return err
}
