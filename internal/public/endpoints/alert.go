package endpoints

import (
	"context"
	"fmt"
	"time"

	"github.com/jamespfennell/transiter/internal/convert"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
)

func ListAlerts(ctx context.Context, r *Context, req *api.ListAlertsRequest) (*api.ListAlertsReply, error) {
	system, err := getSystem(ctx, r.Querier, req.SystemId)
	if err != nil {
		return nil, err
	}
	var alerts []db.Alert
	if len(req.AlertId) == 0 {
		alerts, err = r.Querier.ListAlertsInSystem(ctx, system.Pk)
	} else {
		alerts, err = r.Querier.ListAlertsInSystemAndByIDs(ctx, db.ListAlertsInSystemAndByIDsParams{
			SystemPk: system.Pk,
			Ids:      req.AlertId,
		})
	}
	if err != nil {
		return nil, err
	}
	apiAlerts, err := convertAlerts(ctx, r, system.ID, alerts)
	if err != nil {
		return nil, err
	}
	return &api.ListAlertsReply{
		Alerts: apiAlerts,
	}, nil
}

func GetAlert(ctx context.Context, r *Context, req *api.GetAlertRequest) (*api.Alert, error) {
	system, err := getSystem(ctx, r.Querier, req.SystemId)
	if err != nil {
		return nil, err
	}
	alert, err := r.Querier.GetAlertInSystem(ctx, db.GetAlertInSystemParams{
		SystemPk: system.Pk,
		AlertID:  req.AlertId,
	})
	if err != nil {
		return nil, noRowsToNotFound(nil, fmt.Sprintf("alert %q in system %q", req.AlertId, req.SystemId))
	}
	apiAlert, err := convertAlerts(ctx, r, system.ID, []db.Alert{alert})
	if err != nil {
		return nil, err
	}
	return apiAlert[0], nil
}

func convertAlerts(ctx context.Context, r *Context, systemID string, alerts []db.Alert) ([]*api.Alert, error) {
	var alertPks []int64
	for _, alert := range alerts {
		alertPks = append(alertPks, alert.Pk)
	}
	currentActivePeriods, allActivePeriods, err := buildActivePeriods(ctx, r, alertPks)
	if err != nil {
		return nil, err
	}
	var apiAlerts []*api.Alert
	for _, alert := range alerts {
		apiAlerts = append(apiAlerts, &api.Alert{
			Id:                  alert.ID,
			Resource:            r.Reference.Alert(alert.ID, systemID, alert.Cause, alert.Effect).Resource,
			System:              r.Reference.System(systemID),
			Cause:               convert.AlertCause(alert.Cause),
			Effect:              convert.AlertEffect(alert.Effect),
			CurrentActivePeriod: currentActivePeriods[alert.Pk],
			AllActivePeriods:    allActivePeriods[alert.Pk],
			Header:              convert.AlertText(alert.Header),
			Description:         convert.AlertText(alert.Description),
			Url:                 convert.AlertText(alert.Url),
		})
	}
	return apiAlerts, nil
}

func buildActivePeriods(ctx context.Context, r *Context, alertPks []int64) (map[int64]*api.Alert_ActivePeriod, map[int64][]*api.Alert_ActivePeriod, error) {
	rows, err := r.Querier.ListActivePeriodsForAlerts(ctx, alertPks)
	if err != nil {
		return nil, nil, err
	}
	current := map[int64]*api.Alert_ActivePeriod{}
	all := map[int64][]*api.Alert_ActivePeriod{}
	now := time.Now()
	for _, row := range rows {
		activePeriod := &api.Alert_ActivePeriod{
			StartsAt: convert.SQLNullTime(row.StartsAt),
			EndsAt:   convert.SQLNullTime(row.EndsAt),
		}
		all[row.Pk] = append(all[row.Pk], activePeriod)
		if row.StartsAt.Valid && now.Before(row.StartsAt.Time) {
			continue
		}
		if row.EndsAt.Valid && now.After(row.EndsAt.Time) {
			continue
		}
		current[row.Pk] = activePeriod
	}
	return current, all, nil
}
