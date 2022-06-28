package endpoints

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"time"

	"github.com/jackc/pgx/v4"
	"github.com/jamespfennell/transiter/internal/convert"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/public/errors"
)

func ListRoutes(ctx context.Context, r *Context, req *api.ListRoutesRequest) (*api.ListRoutesReply, error) {
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
	routePkToAlertRows := map[int64][]*api.Alert_Preview{}
	for _, alert := range alerts {
		routePkToAlertRows[alert.RoutePk] = append(
			routePkToAlertRows[alert.RoutePk],
			convert.AlertPreview(alert.ID, alert.Cause, alert.Effect),
		)
	}
	reply := &api.ListRoutesReply{}
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

func GetRoute(ctx context.Context, r *Context, req *api.GetRouteRequest) (*api.Route, error) {
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
	configIDToServiceMap := map[string]*api.Route_ServiceMap{}
	for _, row := range serviceMapRows {
		if _, ok := configIDToServiceMap[row.ConfigID]; !ok {
			configIDToServiceMap[row.ConfigID] = &api.Route_ServiceMap{
				ConfigId: row.ConfigID,
			}
		}
		if !row.StopID.Valid {
			continue
		}
		configIDToServiceMap[row.ConfigID].Stops = append(
			configIDToServiceMap[row.ConfigID].Stops,
			&api.Stop_Preview{
				Id:   row.StopID.String,
				Name: row.StopName.String,
				Href: r.Href.Stop(req.SystemId, row.StopID.String),
			},
		)
	}
	serviceMapsReply := []*api.Route_ServiceMap{}
	for _, serviceMap := range configIDToServiceMap {
		serviceMapsReply = append(serviceMapsReply, serviceMap)
	}
	nullablePeriodicity, err := r.Querier.CalculatePeriodicityForRoute(ctx, db.CalculatePeriodicityForRouteParams{
		RoutePk: route.Pk,
		PresentTime: sql.NullTime{
			Valid: true,
			Time:  time.Now(),
		},
	})
	if err != nil {
		return nil, err
	}
	var periodicity *int32
	if nullablePeriodicity >= 0 {
		periodicity = &nullablePeriodicity
	}

	alerts, err := r.Querier.ListActiveAlertsForRoutes(
		ctx, db.ListActiveAlertsForRoutesParams{
			RoutePks:    []int64{route.Pk},
			PresentTime: sql.NullTime{Valid: true, Time: time.Now()},
		})
	if err != nil {
		return nil, err
	}
	var alertsReply []*api.Alert
	for _, alert := range alerts {
		alertsReply = append(alertsReply, &api.Alert{
			Id:     alert.ID,
			Cause:  convert.AlertCause(alert.Cause),
			Effect: convert.AlertEffect(alert.Effect),
			ActivePeriod: &api.Alert_ActivePeriod{
				StartsAt: convert.SQLNullTime(alert.StartsAt),
				EndsAt:   convert.SQLNullTime(alert.EndsAt),
			},
			Header:      convert.AlertText(alert.Header),
			Description: convert.AlertText(alert.Description),
			Url:         convert.AlertText(alert.Url),
		})
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
		Agency: &api.Agency_Preview{
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
