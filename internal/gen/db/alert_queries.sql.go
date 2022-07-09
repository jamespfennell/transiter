// Code generated by sqlc. DO NOT EDIT.
// versions:
//   sqlc v1.13.0
// source: alert_queries.sql

package db

import (
	"context"
	"database/sql"
)

const deleteAlerts = `-- name: DeleteAlerts :exec
DELETE FROM alert WHERE pk = ANY($1::bigint[])
`

func (q *Queries) DeleteAlerts(ctx context.Context, alertPks []int64) error {
	_, err := q.db.Exec(ctx, deleteAlerts, alertPks)
	return err
}

const deleteStaleAlerts = `-- name: DeleteStaleAlerts :exec
DELETE FROM alert
USING feed_update
WHERE 
    feed_update.pk = alert.source_pk
    AND feed_update.feed_pk = $1
    AND feed_update.pk != $2
`

type DeleteStaleAlertsParams struct {
	FeedPk   int64
	UpdatePk int64
}

// TODO: These DeleteStaleT queries can be simpler and just take the update_pk
func (q *Queries) DeleteStaleAlerts(ctx context.Context, arg DeleteStaleAlertsParams) error {
	_, err := q.db.Exec(ctx, deleteStaleAlerts, arg.FeedPk, arg.UpdatePk)
	return err
}

const getAlertInSystem = `-- name: GetAlertInSystem :one
SELECT alert.pk, alert.id, alert.source_pk, alert.system_pk, alert.cause, alert.effect, alert.header, alert.description, alert.url, alert.hash FROM alert WHERE alert.system_pk = $1 AND alert.id = $2
`

type GetAlertInSystemParams struct {
	SystemPk int64
	AlertID  string
}

func (q *Queries) GetAlertInSystem(ctx context.Context, arg GetAlertInSystemParams) (Alert, error) {
	row := q.db.QueryRow(ctx, getAlertInSystem, arg.SystemPk, arg.AlertID)
	var i Alert
	err := row.Scan(
		&i.Pk,
		&i.ID,
		&i.SourcePk,
		&i.SystemPk,
		&i.Cause,
		&i.Effect,
		&i.Header,
		&i.Description,
		&i.Url,
		&i.Hash,
	)
	return i, err
}

const insertAlert = `-- name: InsertAlert :one
INSERT INTO alert
    (id, system_pk, source_pk, cause, effect, header, description, url, hash)
VALUES
    ($1, $2, $3, $4,$5, 
     $6, $7, $8, $9)
RETURNING pk
`

type InsertAlertParams struct {
	ID          string
	SystemPk    int64
	SourcePk    int64
	Cause       string
	Effect      string
	Header      string
	Description string
	Url         string
	Hash        string
}

func (q *Queries) InsertAlert(ctx context.Context, arg InsertAlertParams) (int64, error) {
	row := q.db.QueryRow(ctx, insertAlert,
		arg.ID,
		arg.SystemPk,
		arg.SourcePk,
		arg.Cause,
		arg.Effect,
		arg.Header,
		arg.Description,
		arg.Url,
		arg.Hash,
	)
	var pk int64
	err := row.Scan(&pk)
	return pk, err
}

const insertAlertActivePeriod = `-- name: InsertAlertActivePeriod :exec
INSERT INTO alert_active_period
    (alert_pk, starts_at, ends_at)
VALUES
    ($1, $2, $3)
`

type InsertAlertActivePeriodParams struct {
	AlertPk  int64
	StartsAt sql.NullTime
	EndsAt   sql.NullTime
}

func (q *Queries) InsertAlertActivePeriod(ctx context.Context, arg InsertAlertActivePeriodParams) error {
	_, err := q.db.Exec(ctx, insertAlertActivePeriod, arg.AlertPk, arg.StartsAt, arg.EndsAt)
	return err
}

const insertAlertAgency = `-- name: InsertAlertAgency :exec
INSERT INTO alert_agency (alert_pk, agency_pk) VALUES ($1, $2)
`

type InsertAlertAgencyParams struct {
	AlertPk  int64
	AgencyPk int64
}

func (q *Queries) InsertAlertAgency(ctx context.Context, arg InsertAlertAgencyParams) error {
	_, err := q.db.Exec(ctx, insertAlertAgency, arg.AlertPk, arg.AgencyPk)
	return err
}

const insertAlertRoute = `-- name: InsertAlertRoute :exec
INSERT INTO alert_route (alert_pk, route_pk) VALUES ($1, $2)
`

type InsertAlertRouteParams struct {
	AlertPk int64
	RoutePk int64
}

func (q *Queries) InsertAlertRoute(ctx context.Context, arg InsertAlertRouteParams) error {
	_, err := q.db.Exec(ctx, insertAlertRoute, arg.AlertPk, arg.RoutePk)
	return err
}

const insertAlertStop = `-- name: InsertAlertStop :exec
INSERT INTO alert_stop (alert_pk, stop_pk) VALUES ($1, $2)
`

type InsertAlertStopParams struct {
	AlertPk int64
	StopPk  int64
}

func (q *Queries) InsertAlertStop(ctx context.Context, arg InsertAlertStopParams) error {
	_, err := q.db.Exec(ctx, insertAlertStop, arg.AlertPk, arg.StopPk)
	return err
}

const listActiveAlertsForAgencies = `-- name: ListActiveAlertsForAgencies :many
SELECT alert.id, alert.cause, alert.effect
FROM alert_agency
    INNER JOIN alert ON alert_agency.alert_pk = alert.pk
WHERE alert_agency.agency_pk = ANY($1::bigint[])
    AND EXISTS (
        SELECT 1 FROM alert_active_period
        WHERE alert_active_period.alert_pk = alert.pk
        AND (
            alert_active_period.starts_at < $2
            OR alert_active_period.starts_at IS NULL
        )
        AND (
            alert_active_period.ends_at > $2
            OR alert_active_period.ends_at IS NULL
        )
    )
`

type ListActiveAlertsForAgenciesParams struct {
	AgencyPks   []int64
	PresentTime sql.NullTime
}

type ListActiveAlertsForAgenciesRow struct {
	ID     string
	Cause  string
	Effect string
}

func (q *Queries) ListActiveAlertsForAgencies(ctx context.Context, arg ListActiveAlertsForAgenciesParams) ([]ListActiveAlertsForAgenciesRow, error) {
	rows, err := q.db.Query(ctx, listActiveAlertsForAgencies, arg.AgencyPks, arg.PresentTime)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []ListActiveAlertsForAgenciesRow
	for rows.Next() {
		var i ListActiveAlertsForAgenciesRow
		if err := rows.Scan(&i.ID, &i.Cause, &i.Effect); err != nil {
			return nil, err
		}
		items = append(items, i)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return items, nil
}

const listActivePeriodsForAlerts = `-- name: ListActivePeriodsForAlerts :many
SELECT alert.pk, alert_active_period.starts_at, alert_active_period.ends_at
FROM alert
    INNER JOIN alert_active_period ON alert_active_period.alert_pk = alert.pk
WHERE alert.pk = ANY($1::bigint[])
`

type ListActivePeriodsForAlertsRow struct {
	Pk       int64
	StartsAt sql.NullTime
	EndsAt   sql.NullTime
}

func (q *Queries) ListActivePeriodsForAlerts(ctx context.Context, pks []int64) ([]ListActivePeriodsForAlertsRow, error) {
	rows, err := q.db.Query(ctx, listActivePeriodsForAlerts, pks)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []ListActivePeriodsForAlertsRow
	for rows.Next() {
		var i ListActivePeriodsForAlertsRow
		if err := rows.Scan(&i.Pk, &i.StartsAt, &i.EndsAt); err != nil {
			return nil, err
		}
		items = append(items, i)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return items, nil
}

const listAlertPksAndHashes = `-- name: ListAlertPksAndHashes :many
SELECT id, pk, hash FROM alert 
WHERE id = ANY($1::text[]) 
AND system_pk = $2
`

type ListAlertPksAndHashesParams struct {
	AlertIds []string
	SystemPk int64
}

type ListAlertPksAndHashesRow struct {
	ID   string
	Pk   int64
	Hash string
}

func (q *Queries) ListAlertPksAndHashes(ctx context.Context, arg ListAlertPksAndHashesParams) ([]ListAlertPksAndHashesRow, error) {
	rows, err := q.db.Query(ctx, listAlertPksAndHashes, arg.AlertIds, arg.SystemPk)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []ListAlertPksAndHashesRow
	for rows.Next() {
		var i ListAlertPksAndHashesRow
		if err := rows.Scan(&i.ID, &i.Pk, &i.Hash); err != nil {
			return nil, err
		}
		items = append(items, i)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return items, nil
}

const listAlertsInSystem = `-- name: ListAlertsInSystem :many
SELECT alert.pk, alert.id, alert.source_pk, alert.system_pk, alert.cause, alert.effect, alert.header, alert.description, alert.url, alert.hash FROM alert WHERE alert.system_pk = $1 ORDER BY alert.id ASC
`

func (q *Queries) ListAlertsInSystem(ctx context.Context, systemPk int64) ([]Alert, error) {
	rows, err := q.db.Query(ctx, listAlertsInSystem, systemPk)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []Alert
	for rows.Next() {
		var i Alert
		if err := rows.Scan(
			&i.Pk,
			&i.ID,
			&i.SourcePk,
			&i.SystemPk,
			&i.Cause,
			&i.Effect,
			&i.Header,
			&i.Description,
			&i.Url,
			&i.Hash,
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

const markAlertsFresh = `-- name: MarkAlertsFresh :exec
UPDATE alert
SET source_pk = $1
WHERE pk = ANY($2::bigint[])
`

type MarkAlertsFreshParams struct {
	UpdatePk int64
	AlertPks []int64
}

func (q *Queries) MarkAlertsFresh(ctx context.Context, arg MarkAlertsFreshParams) error {
	_, err := q.db.Exec(ctx, markAlertsFresh, arg.UpdatePk, arg.AlertPks)
	return err
}