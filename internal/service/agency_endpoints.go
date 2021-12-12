package service

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	"github.com/jamespfennell/transiter/internal/apihelpers"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/service/errors"
)

func (t *TransiterService) ListAgenciesInSystem(ctx context.Context, req *api.ListAgenciesInSystemRequest) (*api.ListAgenciesInSystemReply, error) {
	s := t.NewSession(ctx)
	defer s.Cleanup()
	system, err := s.Querier.GetSystem(ctx, req.SystemId)
	if err != nil {
		if err == sql.ErrNoRows {
			err = errors.NewNotFoundError(fmt.Sprintf("system %q not found", req.SystemId))
		}
		return nil, err
	}
	agencies, err := s.Querier.ListAgenciesInSystem(ctx, system.Pk)
	if err != nil {
		return nil, err
	}
	reply := &api.ListAgenciesInSystemReply{}
	for _, agency := range agencies {
		api_agency := &api.AgencyPreviewWithAlerts{
			Id:     agency.ID,
			Name:   agency.Name,
			Alerts: []string{},
			Href:   s.Hrefs.Agency(req.SystemId, agency.ID),
		}
		reply.Agencies = append(reply.Agencies, api_agency)
	}
	return reply, s.Finish()
}

func (t *TransiterService) GetAgencyInSystem(ctx context.Context, req *api.GetAgencyInSystemRequest) (*api.Agency, error) {
	s := t.NewSession(ctx)
	defer s.Cleanup()
	agency, err := s.Querier.GetAgencyInSystem(ctx, db.GetAgencyInSystemParams{SystemID: req.SystemId, AgencyID: req.AgencyId})
	if err != nil {
		if err == sql.ErrNoRows {
			err = errors.NewNotFoundError(fmt.Sprintf("agency %q in system %q not found", req.AgencyId, req.SystemId))
		}
		return nil, err
	}
	routes, err := s.Querier.ListRoutesInAgency(ctx, agency.Pk)
	if err != nil {
		return nil, err
	}
	alerts, err := s.Querier.ListActiveAlertsForAgency(
		ctx, db.ListActiveAlertsForAgencyParams{
			AgencyPk:    agency.Pk,
			PresentTime: sql.NullTime{Valid: true, Time: time.Now()},
		})
	if err != nil {
		return nil, err
	}
	reply := &api.Agency{
		Id:       agency.ID,
		Name:     agency.Name,
		Url:      apihelpers.ConvertSqlNullString(agency.Url),
		Timezone: agency.Timezone,
		Language: apihelpers.ConvertSqlNullString(agency.Language),
		Phone:    apihelpers.ConvertSqlNullString(agency.Phone),
		FareUrl:  apihelpers.ConvertSqlNullString(agency.FareUrl),
		Email:    apihelpers.ConvertSqlNullString(agency.Email),
	}
	for _, route := range routes {
		reply.Routes = append(reply.Routes, &api.RoutePreview{
			Id:    route.ID,
			Color: route.Color.String,
			Href:  s.Hrefs.Route(req.SystemId, route.ID),
		})
	}
	for _, alert := range alerts {
		reply.Alerts = append(reply.Alerts, &api.AlertPreview{
			Id:     alert.ID,
			Cause:  alert.Cause,
			Effect: alert.Effect,
		})
	}
	return reply, s.Finish()
}
