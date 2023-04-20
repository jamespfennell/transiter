package endpoints

import (
	"context"
	"fmt"
	"time"

	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jamespfennell/transiter/internal/convert"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
)

func ListRoutes(ctx context.Context, r *Context, req *api.ListRoutesRequest) (*api.ListRoutesReply, error) {
	system, err := getSystem(ctx, r.Querier, req.SystemId)
	if err != nil {
		return nil, err
	}
	routes, err := r.Querier.ListRoutes(ctx, system.Pk)
	if err != nil {
		return nil, err
	}
	apiRoutes, err := buildApiRoutes(ctx, r, req, routes)
	if err != nil {
		return nil, err
	}
	return &api.ListRoutesReply{
		Routes: apiRoutes,
	}, nil
}

func GetRoute(ctx context.Context, r *Context, req *api.GetRouteRequest) (*api.Route, error) {
	_, route, err := getRoute(ctx, r.Querier, req.SystemId, req.RouteId)
	if err != nil {
		return nil, err
	}
	apiRoutes, err := buildApiRoutes(ctx, r, req, []db.Route{route})
	if err != nil {
		return nil, err
	}
	return apiRoutes[0], nil
}

type routeRequest interface {
	GetSystemId() string
	GetSkipEstimatedHeadways() bool
	GetSkipServiceMaps() bool
	GetSkipAlerts() bool
}

func buildApiRoutes(ctx context.Context, r *Context, req routeRequest, routes []db.Route) ([]*api.Route, error) {
	startTime := time.Now()
	var routePks []int64
	for i := range routes {
		routePks = append(routePks, routes[i].Pk)
	}
	var err error
	serviceMaps := map[int64][]*api.Route_ServiceMap{}
	if !req.GetSkipServiceMaps() {
		serviceMaps, err = buildServiceMaps(ctx, r, req.GetSystemId(), routePks)
		if err != nil {
			return nil, err
		}
	}
	estimatedHeadways := map[int64]*int32{}
	if !req.GetSkipEstimatedHeadways() {
		estimatedHeadways, err = buildEstimateHeadwaysForRoutes(ctx, r.Querier, routePks)
		if err != nil {
			return nil, err
		}
	}
	alerts := map[int64][]*api.Alert_Reference{}
	if !req.GetSkipAlerts() {
		alerts, err = buildAlertPreviews(ctx, r, req.GetSystemId(), routePks)
		if err != nil {
			return nil, err
		}
	}
	agencies, err := buildAgencies(ctx, r, req.GetSystemId(), routes)
	if err != nil {
		return nil, err
	}
	var apiRoutes []*api.Route
	for i := range routes {
		route := &routes[i]
		apiRoutes = append(apiRoutes, &api.Route{
			Id:                route.ID,
			ShortName:         convert.SQLNullString(route.ShortName),
			LongName:          convert.SQLNullString(route.LongName),
			Color:             route.Color,
			TextColor:         route.TextColor,
			Description:       convert.SQLNullString(route.Description),
			Url:               convert.SQLNullString(route.Url),
			SortOrder:         convert.SQLNullInt32(route.SortOrder),
			ContinuousPickup:  convert.ContinuousPolicy(route.ContinuousPickup),
			ContinuousDropOff: convert.ContinuousPolicy(route.ContinuousDropOff),
			Type:              convert.RouteType(route.Type),
			EstimatedHeadway:  estimatedHeadways[route.Pk],
			Agency:            agencies[route.AgencyPk],
			ServiceMaps:       serviceMaps[route.Pk],
			Alerts:            alerts[route.Pk],
		})
	}
	r.Logger.DebugCtx(ctx, fmt.Sprintf("buildRouteResource(%v) took %s\n", routePks, time.Since(startTime)))
	return apiRoutes, nil
}

func buildEstimateHeadwaysForRoutes(ctx context.Context, querier db.Querier, routePks []int64) (map[int64]*int32, error) {
	rows, err := querier.EstimateHeadwaysForRoutes(ctx, db.EstimateHeadwaysForRoutesParams{
		RoutePks: routePks,
		PresentTime: pgtype.Timestamptz{
			Valid: true,
			Time:  time.Now(),
		},
	})
	if err != nil {
		return nil, err
	}
	m := map[int64]*int32{}
	for _, row := range rows {
		m[row.RoutePk] = &row.EstimatedHeadway
	}
	return m, nil
}

func buildAlertPreviews(ctx context.Context, r *Context, systemID string, routePks []int64) (map[int64][]*api.Alert_Reference, error) {
	alerts, err := r.Querier.ListActiveAlertsForRoutes(
		ctx, db.ListActiveAlertsForRoutesParams{
			RoutePks:    routePks,
			PresentTime: pgtype.Timestamptz{Valid: true, Time: time.Now()},
		})
	if err != nil {
		return nil, err
	}
	m := map[int64][]*api.Alert_Reference{}
	for _, alert := range alerts {
		m[alert.RoutePk] = append(
			m[alert.RoutePk],
			r.Reference.Alert(alert.ID, systemID, alert.Cause, alert.Effect),
		)
	}
	return m, nil
}

func buildServiceMaps(ctx context.Context, r *Context, systemID string, routePks []int64) (map[int64][]*api.Route_ServiceMap, error) {
	serviceMapRows, err := r.Querier.ListServiceMapsForRoutes(ctx, routePks)
	if err != nil {
		return nil, err
	}
	routePkToConfigIDToMap := map[int64]map[string]*api.Route_ServiceMap{}
	for _, routePk := range routePks {
		routePkToConfigIDToMap[routePk] = map[string]*api.Route_ServiceMap{}
	}
	for _, row := range serviceMapRows {
		if _, ok := routePkToConfigIDToMap[row.RoutePk][row.ConfigID]; !ok {
			routePkToConfigIDToMap[row.RoutePk][row.ConfigID] = &api.Route_ServiceMap{
				ConfigId: row.ConfigID,
			}
		}
		// TODO: having this here covers the case when the service map is empty. Can it be more explicit?
		if !row.StopID.Valid {
			continue
		}
		serviceMap := routePkToConfigIDToMap[row.RoutePk][row.ConfigID]
		serviceMap.Stops = append(serviceMap.Stops, r.Reference.Stop(row.StopID.String, systemID, row.StopName))
	}
	m := map[int64][]*api.Route_ServiceMap{}
	for routePk, configIDToMap := range routePkToConfigIDToMap {
		for _, serviceMap := range configIDToMap {
			m[routePk] = append(m[routePk], serviceMap)
		}
	}
	return m, nil
}

func buildAgencies(ctx context.Context, r *Context, systemID string, routes []db.Route) (map[int64]*api.Agency_Reference, error) {
	var agencyPks []int64
	for i := range routes {
		agencyPks = append(agencyPks, routes[i].AgencyPk)
	}
	rows, err := r.Querier.ListAgenciesByPk(ctx, agencyPks)
	if err != nil {
		return nil, err
	}
	m := map[int64]*api.Agency_Reference{}
	for _, row := range rows {
		m[row.Pk] = r.Reference.Agency(row.ID, systemID, row.Name)
	}
	return m, err
}
