package endpoints

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

func ListRoutesInSystem(ctx context.Context, r *Context, req *api.ListRoutesInSystemRequest) (*api.ListRoutesInSystemReply, error) {
	system, err := r.Querier.GetSystem(ctx, req.SystemId)
	if err != nil {
		if err == pgx.ErrNoRows {
			err = errors.NewNotFoundError(fmt.Sprintf("system %q not found", req.SystemId))
		}
		return nil, err
	}
	routes, err := r.Querier.ListRoutesInSystem(ctx, system.Pk)
	if err != nil {
		return nil, err
	}
	var routePks []int64
	for _, route := range routes {
		routePks = append(routePks, route.Pk)
	}
	alerts, err := r.Querier.ListActiveAlertsForRoutes(
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
			Href:   r.Href.Route(system.ID, route.ID),
		})
	}
	return reply, nil
}

func GetRouteInSystem(ctx context.Context, r *Context, req *api.GetRouteInSystemRequest) (*api.Route, error) {
	startTime := time.Now()
	route, err := r.Querier.GetRouteInSystem(ctx, db.GetRouteInSystemParams{SystemID: req.SystemId, RouteID: req.RouteId})
	if err != nil {
		if err == pgx.ErrNoRows {
			err = errors.NewNotFoundError(fmt.Sprintf("route %q in system %q not found", req.RouteId, req.SystemId))
		}
		return nil, err
	}
	serviceMapRows, err := r.Querier.ListServiceMapsForRoute(ctx, route.Pk)
	if err != nil {
		return nil, err
	}
	groupIDToServiceMap := map[string]*api.ServiceMapForRoute{}
	for _, row := range serviceMapRows {
		if _, ok := groupIDToServiceMap[row.GroupID]; !ok {
			groupIDToServiceMap[row.GroupID] = &api.ServiceMapForRoute{
				GroupId: row.GroupID,
			}
		}
		if !row.StopID.Valid {
			continue
		}
		groupIDToServiceMap[row.GroupID].Stops = append(
			groupIDToServiceMap[row.GroupID].Stops,
			&api.StopPreview{
				Id:   row.StopID.String,
				Name: row.StopName.String,
				Href: r.Href.Stop(req.SystemId, row.StopID.String),
			},
		)
	}
	serviceMapsReply := []*api.ServiceMapForRoute{}
	for _, serviceMap := range groupIDToServiceMap {
		serviceMapsReply = append(serviceMapsReply, serviceMap)
	}
	periodicityI, err := r.Querier.CalculatePeriodicityForRoute(ctx, route.Pk)
	if err != nil {
		return nil, err
	}
	var periodicity *float64
	if convert, ok := periodicityI.(float64); ok && convert > 0 {
		convert := math.Floor(convert/6) / 10
		periodicity = &convert
	}

	alerts, err := r.Querier.ListActiveAlertsForRoutes(
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
	alertMessages, err := r.Querier.ListMessagesForAlerts(ctx, alertPks)
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
				StartsAt: convert.SQLNullTime(alert.StartsAt),
				EndsAt:   convert.SQLNullTime(alert.EndsAt),
			},
		}
		for _, message := range alertMessages {
			if message.AlertPk != alert.Pk {
				continue
			}
			apiAlert.Messages = append(apiAlert.Messages, &api.Alert_Message{
				Header:      message.Header,
				Description: message.Description,
				Url:         convert.SQLNullString(message.Url),
				Language:    convert.SQLNullString(message.Language),
			})
		}
		alertsReply = append(alertsReply, &apiAlert)
	}

	reply := &api.Route{
		Id:                route.ID,
		ShortName:         convert.SQLNullString(route.ShortName),
		LongName:          convert.SQLNullString(route.LongName),
		Color:             route.Color,
		TextColor:         route.TextColor,
		Description:       convert.SQLNullString(route.Description),
		Url:               convert.SQLNullString(route.Url),
		SortOrder:         convert.SQLNullInt32(route.SortOrder),
		ContinuousPickup:  route.ContinuousPickup,
		ContinuousDropOff: route.ContinuousDropOff,
		Type:              route.Type,
		Periodicity:       periodicity,
		Agency: &api.AgencyPreview{
			Id:   route.AgencyID,
			Name: route.AgencyName,
			Href: r.Href.Agency(req.SystemId, route.AgencyID),
		},
		ServiceMaps: serviceMapsReply,
		Alerts:      alertsReply,
	}
	log.Println("GetRouteInSystem took", time.Since(startTime))
	return reply, nil
}
