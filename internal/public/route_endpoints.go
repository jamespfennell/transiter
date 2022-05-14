package public

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"math"
	"time"

	"github.com/jackc/pgx/v4"
	"github.com/jamespfennell/transiter/internal/convert"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/public/errors"
)

func (t *Service) ListRoutesInSystem(ctx context.Context, req *api.ListRoutesInSystemRequest) (*api.ListRoutesInSystemReply, error) {
	s := t.newSession(ctx)
	defer s.Cleanup()
	system, err := s.Querier.GetSystem(ctx, req.SystemId)
	if err != nil {
		if err == pgx.ErrNoRows {
			err = errors.NewNotFoundError(fmt.Sprintf("system %q not found", req.SystemId))
		}
		return nil, err
	}
	routes, err := s.Querier.ListRoutesInSystem(ctx, system.Pk)
	if err != nil {
		return nil, err
	}
	var routePks []int64
	for _, route := range routes {
		routePks = append(routePks, route.Pk)
	}
	alerts, err := s.Querier.ListActiveAlertsForRoutes(
		ctx, db.ListActiveAlertsForRoutesParams{
			RoutePks:    routePks,
			PresentTime: sql.NullTime{Valid: true, Time: time.Now()},
		})
	if err != nil {
		return nil, err
	}
	routePkToAlertRows := map[int64][]*api.AlertPreview{}
	for _, alert := range alerts {
		routePkToAlertRows[alert.RoutePk] = append(routePkToAlertRows[alert.RoutePk], &api.AlertPreview{
			Id:     alert.ID,
			Cause:  alert.Cause,
			Effect: alert.Effect,
		})
	}
	reply := &api.ListRoutesInSystemReply{}
	for _, route := range routes {
		reply.Routes = append(reply.Routes, &api.RoutePreviewWithAlerts{
			Id:     route.ID,
			Color:  route.Color,
			Alerts: routePkToAlertRows[route.Pk],
			Href:   s.Hrefs.Route(system.ID, route.ID),
		})
	}
	return reply, s.Finish()
}

func (t *Service) GetRouteInSystem(ctx context.Context, req *api.GetRouteInSystemRequest) (*api.Route, error) {
	startTime := time.Now()
	s := t.newSession(ctx)
	defer s.Cleanup()
	route, err := s.Querier.GetRouteInSystem(ctx, db.GetRouteInSystemParams{SystemID: req.SystemId, RouteID: req.RouteId})
	if err != nil {
		if err == pgx.ErrNoRows {
			err = errors.NewNotFoundError(fmt.Sprintf("route %q in system %q not found", req.RouteId, req.SystemId))
		}
		return nil, err
	}
	service_map_rows, err := s.Querier.ListServiceMapsForRoute(ctx, route.Pk)
	if err != nil {
		return nil, err
	}
	groupIdToServiceMap := map[string]*api.ServiceMapForRoute{}
	for _, row := range service_map_rows {
		if _, ok := groupIdToServiceMap[row.GroupID]; !ok {
			groupIdToServiceMap[row.GroupID] = &api.ServiceMapForRoute{
				GroupId: row.GroupID,
			}
		}
		if !row.StopID.Valid {
			continue
		}
		groupIdToServiceMap[row.GroupID].Stops = append(
			groupIdToServiceMap[row.GroupID].Stops,
			&api.StopPreview{
				Id:   row.StopID.String,
				Name: row.StopName.String,
				Href: s.Hrefs.Stop(req.SystemId, row.StopID.String),
			},
		)
	}
	serviceMapsReply := []*api.ServiceMapForRoute{}
	for _, serviceMap := range groupIdToServiceMap {
		serviceMapsReply = append(serviceMapsReply, serviceMap)
	}
	periodicityI, err := s.Querier.CalculatePeriodicityForRoute(ctx, route.Pk)
	if err != nil {
		return nil, err
	}
	var periodicity *float64
	if convert, ok := periodicityI.(float64); ok && convert > 0 {
		convert := math.Floor(convert/6) / 10
		periodicity = &convert
	}

	alerts, err := s.Querier.ListActiveAlertsForRoutes(
		ctx, db.ListActiveAlertsForRoutesParams{
			RoutePks:    []int64{route.Pk},
			PresentTime: sql.NullTime{Valid: true, Time: time.Now()},
		})
	if err != nil {
		return nil, err
	}
	var alertPks []int64
	for _, alert := range alerts {
		alertPks = append(alertPks, alert.Pk)
	}
	alertMessages, err := s.Querier.ListMessagesForAlerts(ctx, alertPks)
	if err != nil {
		return nil, err
	}
	var alertsReply []*api.Alert
	for _, alert := range alerts {
		apiAlert := api.Alert{
			Id:     alert.ID,
			Cause:  alert.Cause,
			Effect: alert.Effect,
			ActivePeriod: &api.Alert_ActivePeriod{
				StartsAt: convert.SqlNullTime(alert.StartsAt),
				EndsAt:   convert.SqlNullTime(alert.EndsAt),
			},
		}
		for _, message := range alertMessages {
			if message.AlertPk != alert.Pk {
				continue
			}
			apiAlert.Messages = append(apiAlert.Messages, &api.Alert_Message{
				Header:      message.Header,
				Description: message.Description,
				Url:         convert.SqlNullString(message.Url),
				Language:    convert.SqlNullString(message.Language),
			})
		}
		alertsReply = append(alertsReply, &apiAlert)
	}

	reply := &api.Route{
		Id:                route.ID,
		ShortName:         convert.SqlNullString(route.ShortName),
		LongName:          convert.SqlNullString(route.LongName),
		Color:             route.Color,
		TextColor:         route.TextColor,
		Description:       convert.SqlNullString(route.Description),
		Url:               convert.SqlNullString(route.Url),
		SortOrder:         convert.SqlNullInt32(route.SortOrder),
		ContinuousPickup:  route.ContinuousPickup,
		ContinuousDropOff: route.ContinuousDropOff,
		Type:              route.Type,
		Periodicity:       periodicity,
		Agency: &api.AgencyPreview{
			Id:   route.AgencyID,
			Name: route.AgencyName,
			Href: s.Hrefs.Agency(req.SystemId, route.AgencyID),
		},
		ServiceMaps: serviceMapsReply,
		Alerts:      alertsReply,
	}
	log.Println("GetRouteInSystem took", time.Since(startTime))
	return reply, s.Finish()
}
