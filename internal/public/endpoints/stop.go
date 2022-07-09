package endpoints

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"sort"
	"time"

	"github.com/jackc/pgtype"
	"github.com/jackc/pgx/v4"
	"github.com/jamespfennell/transiter/internal/public/stoptree"

	"github.com/jamespfennell/transiter/internal/convert"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/public/errors"
)

func ListStops(ctx context.Context, r *Context, req *api.ListStopsRequest) (*api.ListStopsReply, error) {
	system, err := getSystem(ctx, r.Querier, req.SystemId)
	if err != nil {
		return nil, err
	}
	stops, err := r.Querier.ListStopsInSystem(ctx, system.Pk)
	if err != nil {
		return nil, err
	}
	result := &api.ListStopsReply{}
	for _, stop := range stops {
		result.Stops = append(result.Stops, &api.Stop_Preview{
			Id:   stop.ID,
			Name: stop.Name.String,
			Href: r.Href.Stop(system.ID, stop.ID),
		})
	}
	return result, nil
}

func ListTransfers(ctx context.Context, r *Context, req *api.ListTransfersRequest) (*api.ListTransfersReply, error) {
	system, err := r.Querier.GetSystem(ctx, req.SystemId)
	if err != nil {
		if err == pgx.ErrNoRows {
			err = errors.NewNotFoundError(fmt.Sprintf("system %q not found", req.SystemId))
		}
		return nil, err
	}
	transfers, err := r.Querier.ListTransfersInSystem(ctx, sql.NullInt64{Valid: true, Int64: system.Pk})
	if err != nil {
		return nil, err
	}
	reply := &api.ListTransfersReply{}
	for _, transfer := range transfers {
		transfer := transfer
		reply.Transfers = append(reply.Transfers, &api.Transfer{
			FromStop: &api.Stop_Preview{
				Id:   transfer.FromStopID,
				Name: transfer.FromStopName.String,
				Href: r.Href.Stop(transfer.FromSystemID, transfer.FromStopID),
			},
			ToStop: &api.Stop_Preview{
				Id:   transfer.ToStopID,
				Name: transfer.ToStopName.String,
				Href: r.Href.Stop(transfer.ToSystemID, transfer.ToStopID),
			},
			Type:            convert.TransferType(transfer.Type),
			MinTransferTime: convert.SQLNullInt32(transfer.MinTransferTime),
		})
	}
	return reply, nil
}

func GetStop(ctx context.Context, r *Context, req *api.GetStopRequest) (*api.Stop, error) {
	startTime := time.Now()
	// TODO: we can probably remove this call? And just check that the stops tree is non-empty
	stop, err := r.Querier.GetStopInSystem(ctx, db.GetStopInSystemParams{SystemID: req.SystemId, StopID: req.StopId})
	if err != nil {
		if err == pgx.ErrNoRows {
			err = errors.NewNotFoundError(fmt.Sprintf("stop %q in system %q not found", req.StopId, req.SystemId))
		}
		return nil, err
	}
	stopTree, err := stoptree.NewStopTree(ctx, r.Querier, stop.Pk)
	if err != nil {
		return nil, err
	}

	var transfers []db.ListTransfersFromStopsRow
	stopPkToServiceMaps := map[int64][]*api.Stop_ServiceMap{}
	stationPks := stopTree.StationPks()
	transfers, err = r.Querier.ListTransfersFromStops(ctx, stationPks)
	if err != nil {
		return nil, err
	}
	for _, transfer := range transfers {
		stationPks = append(stationPks, transfer.ToStopPk)
	}

	configIDRows, err := r.Querier.ListServiceMapsConfigIDsForStops(ctx, stationPks)
	if err != nil {
		return nil, err
	}
	serviceMaps, err := r.Querier.ListServiceMapsForStops(ctx, stationPks)
	if err != nil {
		return nil, err
	}
	pkToConfigIDToRoutes := map[int64]map[string][]*api.Route_Preview{}

	for _, configIDRow := range configIDRows {
		if _, present := pkToConfigIDToRoutes[configIDRow.Pk]; !present {
			pkToConfigIDToRoutes[configIDRow.Pk] = map[string][]*api.Route_Preview{}
		}
		pkToConfigIDToRoutes[configIDRow.Pk][configIDRow.ID] = []*api.Route_Preview{}
	}
	for _, serviceMap := range serviceMaps {
		if _, present := pkToConfigIDToRoutes[serviceMap.StopPk]; !present {
			pkToConfigIDToRoutes[serviceMap.StopPk] = map[string][]*api.Route_Preview{}
		}
		route := &api.Route_Preview{
			Id:    serviceMap.RouteID,
			Color: serviceMap.RouteColor,
			Href:  r.Href.Route(req.SystemId, serviceMap.RouteID),
		}
		if serviceMap.SystemID != req.SystemId {
			route.System = &api.System{
				Id: serviceMap.SystemID,
			}
		}
		pkToConfigIDToRoutes[serviceMap.StopPk][serviceMap.ServiceMapConfigID] = append(
			pkToConfigIDToRoutes[serviceMap.StopPk][serviceMap.ServiceMapConfigID], route)
	}
	for pk, configIDToRoutes := range pkToConfigIDToRoutes {
		for configID, routes := range configIDToRoutes {
			stopPkToServiceMaps[pk] = append(stopPkToServiceMaps[pk],
				&api.Stop_ServiceMap{
					ConfigId: configID,
					Routes:   routes,
				})
		}
	}

	stopHeadsignMatcher, err := NewStopHeadsignMatcher(ctx, r.Querier, stopTree.DescendentPks())
	if err != nil {
		return nil, err
	}

	alerts, err := r.Querier.ListActiveAlertsForStops(
		ctx, db.ListActiveAlertsForStopsParams{
			StopPks:     []int64{stop.Pk},
			PresentTime: sql.NullTime{Valid: true, Time: time.Now()},
		})
	if err != nil {
		return nil, err
	}
	// TODO: alerts

	var stopTimes []db.ListStopTimesAtStopsRow
	routePkToRoute := map[int64]*db.Route{}
	tripPkToLastStop := map[int64]*db.GetLastStopsForTripsRow{}
	stopTimes, err = r.Querier.ListStopTimesAtStops(ctx, stopTree.DescendentPks())
	if err != nil {
		return nil, err
	}
	var routePks []int64
	var tripPks []int64
	for _, stopTime := range stopTimes {
		routePks = append(routePks, stopTime.RoutePk)
		tripPks = append(tripPks, stopTime.TripPk)
	}
	routes, err := r.Querier.ListRoutesByPk(ctx, routePks)
	if err != nil {
		return nil, err
	}
	for _, route := range routes {
		route := route
		routePkToRoute[route.Pk] = &route
	}
	rows, err := r.Querier.GetLastStopsForTrips(ctx, tripPks)
	if err != nil {
		return nil, err
	}
	for _, row := range rows {
		row := row
		tripPkToLastStop[row.TripPk] = &row
	}

	stopTreeResponse := buildStopTreeResponse(r, req.SystemId, stop.Pk, stopTree, stopPkToServiceMaps)
	result := &api.Stop{
		Id:            stop.ID,
		Name:          convert.SQLNullString(stop.Name),
		Longitude:     convertGpsData(stop.Longitude),
		Latitude:      convertGpsData(stop.Latitude),
		Url:           convert.SQLNullString(stop.Url),
		StopHeadsigns: stopHeadsignMatcher.AllHeadsigns(),
		ParentStop:    stopTreeResponse.ParentStop,
		ChildStops:    stopTreeResponse.ChildStops,
		ServiceMaps:   stopTreeResponse.ServiceMaps,
	}
	for _, stopTime := range stopTimes {
		stopTime := stopTime
		route := routePkToRoute[stopTime.RoutePk]
		lastStop := tripPkToLastStop[stopTime.TripPk]
		apiStopTime := &api.Stop_StopTime{
			StopSequence: stopTime.StopSequence,
			Track:        convert.SQLNullString(stopTime.Track),
			Future:       !stopTime.Past,
			Headsign:     stopHeadsignMatcher.Match(&stopTime),
			Arrival:      buildEstimatedTime(stopTime.ArrivalTime, stopTime.ArrivalDelay, stopTime.ArrivalUncertainty),
			Departure:    buildEstimatedTime(stopTime.DepartureTime, stopTime.DepartureDelay, stopTime.DepartureUncertainty),
			Trip: &api.Trip_Preview{
				Id:          stopTime.ID,
				DirectionId: stopTime.DirectionID.Bool,
				StartedAt:   convert.SQLNullTime(stopTime.StartedAt),
				Route: &api.Route_Preview{
					Id:    route.ID,
					Color: route.Color,
					Href:  r.Href.Route(req.SystemId, route.ID),
				},
				LastStop: &api.Stop_Preview{
					Id:   lastStop.ID,
					Name: lastStop.Name.String,
					Href: r.Href.Stop(req.SystemId, lastStop.ID),
				},
				Href: r.Href.Trip(req.SystemId, route.ID, stopTime.ID),
			},
		}
		if stopTime.VehicleID.Valid {
			apiStopTime.Trip.Vehicle = &api.Vehicle_Preview{
				Id: stopTime.VehicleID.String,
			}
		}
		result.StopTimes = append(result.StopTimes, apiStopTime)
	}
	for _, alert := range alerts {
		result.Alerts = append(result.Alerts, convert.AlertPreview(alert.ID, alert.Cause, alert.Effect))
	}
	for _, transfer := range transfers {
		fromStop := stopTree.Get(transfer.FromStopPk)
		result.Transfers = append(result.Transfers, &api.Transfer{
			FromStop: &api.Stop_Preview{
				Id:   fromStop.ID,
				Name: fromStop.Name.String,
				Href: r.Href.Stop(req.SystemId, fromStop.ID),
			},
			ToStop: &api.Stop_Preview{
				Id:   transfer.ToID,
				Name: transfer.ToName.String,
				// TODO ServiceMaps: stopPkToServiceMaps[transfer.ToStopPk],
				Href: r.Href.Stop(req.SystemId, transfer.ToID),
			},
			Type:            convert.TransferType(transfer.Type),
			MinTransferTime: convert.SQLNullInt32(transfer.MinTransferTime),
			Distance:        convert.SQLNullInt32(transfer.Distance),
		})
	}
	log.Println("GetStopInSystem took", time.Since(startTime))
	return result, nil
}

// TODO: destroy this garbage
type tempType struct {
	ParentStop  *api.Stop_Preview
	ChildStops  []*api.Stop_Preview
	ServiceMaps []*api.Stop_ServiceMap

	ID   string
	Name string
	Href *string
}

// TODO: no need for this nonsense in general
func buildStopTreeResponse(r *Context, systemID string,
	basePk int64, stopTree *stoptree.StopTree, serviceMaps map[int64][]*api.Stop_ServiceMap) tempType {
	stopPkToResponse := map[int64]tempType{}
	stopTree.VisitDFS(func(node *stoptree.StopTreeNode) {
		if !stoptree.IsStation(node.Stop) && basePk != node.Stop.Pk {
			return
		}
		thisResponse := tempType{
			ID:          node.Stop.ID,
			Name:        node.Stop.Name.String,
			ServiceMaps: serviceMaps[node.Stop.Pk],
			Href:        r.Href.Stop(systemID, node.Stop.ID),
		}
		if node.Parent != nil {
			if parentResponse, ok := stopPkToResponse[node.Parent.Stop.Pk]; ok {
				thisResponse.ParentStop = &api.Stop_Preview{
					Id:   parentResponse.ID,
					Name: parentResponse.Name,
					Href: parentResponse.Href,
				}
			}
		}
		for _, child := range node.Children {
			if childResponse, ok := stopPkToResponse[child.Stop.Pk]; ok {
				thisResponse.ChildStops = append(thisResponse.ChildStops, &api.Stop_Preview{
					Id:   childResponse.ID,
					Name: childResponse.Name,
					Href: childResponse.Href,
				})
			}
		}
		stopPkToResponse[node.Stop.Pk] = thisResponse
	})
	return stopPkToResponse[basePk]
}

type StopHeadsignMatcher struct {
	rules []db.StopHeadsignRule
}

func NewStopHeadsignMatcher(ctx context.Context, querier db.Querier, stopPks []int64) (*StopHeadsignMatcher, error) {
	rules, err := querier.ListStopHeadsignRulesForStops(ctx, stopPks)
	if err != nil {
		return nil, err
	}
	return &StopHeadsignMatcher{rules: rules}, nil
}

func (m *StopHeadsignMatcher) Match(stopTime *db.ListStopTimesAtStopsRow) *string {
	for _, rule := range m.rules {
		if stopTime.StopPk != rule.StopPk {
			continue
		}
		if stopTime.Track.Valid &&
			rule.Track.Valid &&
			stopTime.Track.String != rule.Track.String {
			continue
		}
		return &rule.Headsign
	}
	return nil
}

func (m *StopHeadsignMatcher) AllHeadsigns() []string {
	names := map[string]bool{}
	for _, rule := range m.rules {
		names[rule.Headsign] = true
	}
	var result []string
	for name := range names {
		result = append(result, name)
	}
	sort.Strings(result)
	return result
}

func buildEstimatedTime(time sql.NullTime, delay sql.NullInt32, uncertainty sql.NullInt32) *api.EstimatedTime {
	return &api.EstimatedTime{
		Time:        convert.SQLNullTime(time),
		Delay:       convert.SQLNullInt32(delay),
		Uncertainty: convert.SQLNullInt32(uncertainty),
	}
}

func convertGpsData(n pgtype.Numeric) *float64 {
	if n.Status != pgtype.Present {
		return nil
	}
	var r float64
	n.AssignTo(&r)
	return &r
}