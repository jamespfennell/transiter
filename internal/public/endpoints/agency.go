package endpoints

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	"github.com/jackc/pgx/v4"
	"github.com/jamespfennell/transiter/internal/convert"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/public/errors"
)

func ListAgencies(ctx context.Context, r *Context, req *api.ListAgenciesRequest) (*api.ListAgenciesReply, error) {
	system, err := getSystem(ctx, r.Querier, req.SystemId)
	if err != nil {
		return nil, err
	}
	dbAgencies, err := r.Querier.ListAgencies(ctx, system.Pk)
	if err != nil {
		return nil, err
	}
	agencies, err := buildApiAgencies(ctx, r, req.SystemId, dbAgencies)
	if err != nil {
		return nil, err
	}
	return &api.ListAgenciesReply{Agencies: agencies}, nil
}

func GetAgency(ctx context.Context, r *Context, req *api.GetAgencyRequest) (*api.Agency, error) {
	system, err := getSystem(ctx, r.Querier, req.SystemId)
	if err != nil {
		return nil, err
	}
	dbAgency, err := r.Querier.GetAgency(ctx, db.GetAgencyParams{
		SystemPk: system.Pk,
		AgencyID: req.AgencyId,
	})
	if err != nil {
		if err == pgx.ErrNoRows {
			err = errors.NewNotFoundError(fmt.Sprintf("agency %q in system %q not found", req.AgencyId, req.SystemId))
		}
		return nil, err
	}
	agencies, err := buildApiAgencies(ctx, r, req.SystemId, []db.Agency{dbAgency})
	if err != nil {
		return nil, err
	}
	return agencies[0], nil
}

func buildApiAgencies(ctx context.Context, r *Context, systemID string, dbAgencies []db.Agency) ([]*api.Agency, error) {
	var apiAgencies []*api.Agency
	for _, dbAgency := range dbAgencies {
		routes, err := r.Querier.ListRoutesInAgency(ctx, dbAgency.Pk)
		if err != nil {
			return nil, err
		}
		alerts, err := getAlertsForAgencies(ctx, r, systemID, []int64{dbAgency.Pk})
		if err != nil {
			return nil, err
		}
		apiAgency := &api.Agency{
			Id:       dbAgency.ID,
			Name:     dbAgency.Name,
			Url:      dbAgency.Url,
			Timezone: dbAgency.Timezone,
			Language: convert.SQLNullString(dbAgency.Language),
			Phone:    convert.SQLNullString(dbAgency.Phone),
			FareUrl:  convert.SQLNullString(dbAgency.FareUrl),
			Email:    convert.SQLNullString(dbAgency.Email),
			Alerts:   alerts,
		}
		for _, route := range routes {
			apiAgency.Routes = append(apiAgency.Routes, r.Reference.Route(route.ID, systemID, route.Color))
		}
		apiAgencies = append(apiAgencies, apiAgency)
	}
	return apiAgencies, nil
}

func getAlertsForAgencies(ctx context.Context, r *Context, systemID string, agencyPks []int64) ([]*api.Alert_Reference, error) {
	dbAlerts, err := r.Querier.ListActiveAlertsForAgencies(ctx, db.ListActiveAlertsForAgenciesParams{
		AgencyPks:   agencyPks,
		PresentTime: sql.NullTime{Valid: true, Time: time.Now()},
	})
	if err != nil {
		return nil, err
	}
	var alerts []*api.Alert_Reference
	for _, alert := range dbAlerts {
		alerts = append(alerts, r.Reference.Alert(alert.ID, systemID, alert.Cause, alert.Effect))
	}
	return alerts, nil
}
