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

func ListAgenciesInSystem(ctx context.Context, r *Context, req *api.ListAgenciesInSystemRequest) (*api.ListAgenciesInSystemReply, error) {
	system, err := r.Querier.GetSystem(ctx, req.SystemId)
	if err != nil {
		if err == pgx.ErrNoRows {
			err = errors.NewNotFoundError(fmt.Sprintf("system %q not found", req.SystemId))
		}
		return nil, err
	}
	agencies, err := r.Querier.ListAgenciesInSystem(ctx, system.Pk)
	if err != nil {
		return nil, err
	}
	reply := &api.ListAgenciesInSystemReply{}
	for _, agency := range agencies {
		// TODO: should probably batch these
		alerts, err := getAlertsForAgencies(ctx, r.Querier, []int64{agency.Pk})
		if err != nil {
			return nil, err
		}
		apiAgency := &api.AgencyPreviewWithAlerts{
			Id:     agency.ID,
			Name:   agency.Name,
			Alerts: alerts,
			Href:   r.Href.Agency(req.SystemId, agency.ID),
		}
		reply.Agencies = append(reply.Agencies, apiAgency)
	}
	return reply, nil
}

func GetAgencyInSystem(ctx context.Context, r *Context, req *api.GetAgencyInSystemRequest) (*api.Agency, error) {
	agency, err := r.Querier.GetAgencyInSystem(ctx, db.GetAgencyInSystemParams{SystemID: req.SystemId, AgencyID: req.AgencyId})
	if err != nil {
		if err == pgx.ErrNoRows {
			err = errors.NewNotFoundError(fmt.Sprintf("agency %q in system %q not found", req.AgencyId, req.SystemId))
		}
		return nil, err
	}
	routes, err := r.Querier.ListRoutesInAgency(ctx, agency.Pk)
	if err != nil {
		return nil, err
	}
	alerts, err := getAlertsForAgencies(ctx, r.Querier, []int64{agency.Pk})
	if err != nil {
		return nil, err
	}
	reply := &api.Agency{
		Id:       agency.ID,
		Name:     agency.Name,
		Url:      agency.Url,
		Timezone: agency.Timezone,
		Language: convert.SQLNullString(agency.Language),
		Phone:    convert.SQLNullString(agency.Phone),
		FareUrl:  convert.SQLNullString(agency.FareUrl),
		Email:    convert.SQLNullString(agency.Email),
		Alerts:   alerts,
	}
	for _, route := range routes {
		reply.Routes = append(reply.Routes, &api.RoutePreview{
			Id:    route.ID,
			Color: route.Color,
			Href:  r.Href.Route(req.SystemId, route.ID),
		})
	}

	return reply, nil
}

func getAlertsForAgencies(ctx context.Context, querier db.Querier, agencyPks []int64) ([]*api.AlertPreview, error) {
	dbAlerts, err := querier.ListActiveAlertsForAgencies(ctx, db.ListActiveAlertsForAgenciesParams{
		AgencyPks:   agencyPks,
		PresentTime: sql.NullTime{Valid: true, Time: time.Now()},
	})
	if err != nil {
		return nil, err
	}
	var alerts []*api.AlertPreview
	for _, alert := range dbAlerts {
		alerts = append(alerts, &api.AlertPreview{
			Id:     alert.ID,
			Cause:  alert.Cause,
			Effect: alert.Effect,
		})
	}
	return alerts, nil
}
