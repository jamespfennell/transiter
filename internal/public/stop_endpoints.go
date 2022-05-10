package public

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

	"github.com/jamespfennell/transiter/internal/apihelpers"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/public/errors"
	"github.com/jamespfennell/transiter/internal/public/session"
)

func (t *Service) ListStopsInSystem(ctx context.Context, req *api.ListStopsInSystemRequest) (*api.ListStopsInSystemReply, error) {
	s := t.newSession(ctx)
	defer s.Cleanup()
	system, err := s.Querier.GetSystem(ctx, req.SystemId)
	if err != nil {
		if err == pgx.ErrNoRows {
			err = errors.NewNotFoundError(fmt.Sprintf("system %q not found", req.SystemId))
		}
		return nil, err
	}
	stops, err := s.Querier.ListStopsInSystem(ctx, system.Pk)
	if err != nil {
		return nil, err
	}
	result := &api.ListStopsInSystemReply{}
	for _, stop := range stops {
		result.Stops = append(result.Stops, &api.StopPreview{
			Id:   stop.ID,
			Name: stop.Name.String,
			Href: s.Hrefs.Stop(system.ID, stop.ID),
		})
	}
	return result, s.Finish()
}

func (t *Service) ListTransfersInSystem(ctx context.Context, req *api.ListTransfersInSystemRequest) (*api.ListTransfersInSystemReply, error) {
	s := t.newSession(ctx)
	defer s.Cleanup()
	system, err := s.Querier.GetSystem(ctx, req.SystemId)
	if err != nil {
		if err == pgx.ErrNoRows {
			err = errors.NewNotFoundError(fmt.Sprintf("system %q not found", req.SystemId))
		}
		return nil, err
	}
	transfers, err := s.Querier.ListTransfersInSystem(ctx, sql.NullInt64{Valid: true, Int64: system.Pk})
	if err != nil {
		return nil, err
	}
	reply := &api.ListTransfersInSystemReply{}
	for _, transfer := range transfers {
		transfer := transfer
		reply.Transfers = append(reply.Transfers, &api.Transfer{
			FromStop: &api.StopPreview{
				Id:   transfer.FromStopID,
				Name: transfer.FromStopName.String,
				Href: s.Hrefs.Stop(transfer.FromSystemID, transfer.FromStopID),
			},
			ToStop: &api.StopPreview{
				Id:   transfer.ToStopID,
				Name: transfer.ToStopName.String,
				Href: s.Hrefs.Stop(transfer.ToSystemID, transfer.ToStopID),
			},
			Type:            transfer.Type,
			MinTransferTime: transfer.MinTransferTime.Int32,
		})
	}
	return reply, nil
}

func (t *Service) GetStopInSystem(ctx context.Context, req *api.GetStopInSystemRequest) (*api.Stop, error) {
	startTime := time.Now()
	s := t.newSession(ctx)
	defer s.Cleanup()
	// TODO: we can probably remove this call? And just check that the stops tree is non-empty
	stop, err := s.Querier.GetStopInSystem(ctx, db.GetStopInSystemParams{SystemID: req.SystemId, StopID: req.StopId})
	if err != nil {
		if err == pgx.ErrNoRows {
			err = errors.NewNotFoundError(fmt.Sprintf("stop %q in system %q not found", req.StopId, req.SystemId))
		}
		return nil, err
	}
	stopTree, err := stoptree.NewStopTree(ctx, s.Querier, stop.Pk)
	if err != nil {
		return nil, err
	}

	var transfers []db.ListTransfersFromStopsRow
	stopPkToServiceMaps := map[int64][]*api.ServiceMapForStop{}
	stationPks := stopTree.StationPks()
	transfers, err = s.Querier.ListTransfersFromStops(ctx, stationPks)
	if err != nil {
		return nil, err
	}
	for _, transfer := range transfers {
		stationPks = append(stationPks, transfer.ToStopPk)
	}

	groupIDRows, err := s.Querier.ListServiceMapsGroupIDsForStops(ctx, stationPks)
	if err != nil {
		return nil, err
	}
	serviceMaps, err := s.Querier.ListServiceMapsForStops(ctx, stationPks)
	if err != nil {
		return nil, err
	}
	pkToGroupIdToRoutes := map[int64]map[string][]*api.RoutePreview{}

	for _, groupIDRow := range groupIDRows {
		if _, present := pkToGroupIdToRoutes[groupIDRow.Pk]; !present {
			pkToGroupIdToRoutes[groupIDRow.Pk] = map[string][]*api.RoutePreview{}
		}
		pkToGroupIdToRoutes[groupIDRow.Pk][groupIDRow.ID] = []*api.RoutePreview{}
	}
	for _, serviceMap := range serviceMaps {
		if _, present := pkToGroupIdToRoutes[serviceMap.StopPk]; !present {
			pkToGroupIdToRoutes[serviceMap.StopPk] = map[string][]*api.RoutePreview{}
		}
		route := &api.RoutePreview{
			Id:    serviceMap.RouteID,
			Color: serviceMap.RouteColor,
			Href:  s.Hrefs.Route(req.SystemId, serviceMap.RouteID),
		}
		if serviceMap.SystemID != req.SystemId {
			route.System = &api.System{
				Id: serviceMap.SystemID,
			}
		}
		pkToGroupIdToRoutes[serviceMap.StopPk][serviceMap.ServiceMapConfigID] = append(
			pkToGroupIdToRoutes[serviceMap.StopPk][serviceMap.ServiceMapConfigID], route)
	}
	for pk, groupIdToRoutes := range pkToGroupIdToRoutes {
		for groupId, routes := range groupIdToRoutes {
			stopPkToServiceMaps[pk] = append(stopPkToServiceMaps[pk],
				&api.ServiceMapForStop{
					GroupId: groupId,
					Routes:  routes,
				})
		}
	}

	directionNameMatcher, err := NewDirectionNameMatcher(ctx, s.Querier, stopTree.DescendentPks())
	if err != nil {
		return nil, err
	}

	alerts, err := s.Querier.ListActiveAlertsForStops(
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
	stopTimes, err = s.Querier.ListStopTimesAtStops(ctx, stopTree.DescendentPks())
	if err != nil {
		return nil, err
	}
	var routePks []int64
	var tripPks []int64
	for _, stopTime := range stopTimes {
		routePks = append(routePks, stopTime.RoutePk)
		tripPks = append(tripPks, stopTime.TripPk)
	}
	routes, err := s.Querier.ListRoutesByPk(ctx, routePks)
	if err != nil {
		return nil, err
	}
	for _, route := range routes {
		route := route
		routePkToRoute[route.Pk] = &route
	}
	rows, err := s.Querier.GetLastStopsForTrips(ctx, tripPks)
	if err != nil {
		return nil, err
	}
	for _, row := range rows {
		row := row
		tripPkToLastStop[row.TripPk] = &row
	}

	stopTreeResponse := buildStopTreeResponse(&s, req.SystemId, stop.Pk, stopTree, stopPkToServiceMaps)
	result := &api.Stop{
		Id:          stop.ID,
		Name:        stop.Name.String,
		Longitude:   convertGpsData(stop.Longitude),
		Latitude:    convertGpsData(stop.Latitude),
		Url:         apihelpers.ConvertSqlNullString(stop.Url),
		Directions:  directionNameMatcher.Directions(),
		ParentStop:  stopTreeResponse.ParentStop,
		ChildStops:  stopTreeResponse.ChildStops,
		ServiceMaps: stopTreeResponse.ServiceMaps,
	}
	for _, stopTime := range stopTimes {
		stopTime := stopTime
		route := routePkToRoute[stopTime.RoutePk]
		lastStop := tripPkToLastStop[stopTime.TripPk]
		apiStopTime := &api.Stop_StopTime{
			StopSequence: stopTime.StopSequence,
			Track:        apihelpers.ConvertSqlNullString(stopTime.Track),
			Future: stopTime.StopSequence >= 0 && (stopTime.CurrentStopSequence.Int32 <= stopTime.StopSequence ||
				!stopTime.CurrentStopSequence.Valid),
			Direction: directionNameMatcher.Match(&stopTime),
			Arrival:   buildEstimatedTime(stopTime.ArrivalTime, stopTime.ArrivalDelay, stopTime.ArrivalUncertainty),
			Departure: buildEstimatedTime(stopTime.DepartureTime, stopTime.DepartureDelay, stopTime.DepartureUncertainty),
			Trip: &api.TripPreview{
				Id:          stopTime.ID,
				DirectionId: stopTime.DirectionID.Bool,
				StartedAt:   apihelpers.ConvertSqlNullTime(stopTime.StartedAt),
				UpdatedAt:   apihelpers.ConvertSqlNullTime(stopTime.UpdatedAt),
				Route: &api.RoutePreview{
					Id:    route.ID,
					Color: route.Color,
					Href:  s.Hrefs.Route(req.SystemId, route.ID),
				},
				LastStop: &api.StopPreview{
					Id:   lastStop.ID,
					Name: lastStop.Name.String,
					Href: s.Hrefs.Stop(req.SystemId, lastStop.ID),
				},
				Href: s.Hrefs.Trip(req.SystemId, route.ID, stopTime.ID),
			},
		}
		if stopTime.VehicleID.Valid {
			apiStopTime.Trip.Vehicle = &api.VehiclePreview{
				Id: stopTime.VehicleID.String,
			}
		}
		result.StopTimes = append(result.StopTimes, apiStopTime)
	}
	for _, alert := range alerts {
		result.Alerts = append(result.Alerts, &api.AlertPreview{
			Id:     alert.ID,
			Effect: alert.Effect,
			Cause:  alert.Cause,
		})
	}
	for _, transfer := range transfers {
		fromStop := stopTree.Get(transfer.FromStopPk)
		result.Transfers = append(result.Transfers, &api.TransferAtStop{
			FromStop: &api.StopPreview{
				Id:   fromStop.ID,
				Name: fromStop.Name.String,
				Href: s.Hrefs.Stop(req.SystemId, fromStop.ID),
			},
			ToStop: &api.RelatedStop{
				Id:          transfer.ToID,
				Name:        transfer.ToName.String,
				ServiceMaps: stopPkToServiceMaps[transfer.ToStopPk],
				Href:        s.Hrefs.Stop(req.SystemId, transfer.ToID),
			},
			Type:            transfer.Type,
			MinTransferTime: apihelpers.ConvertSqlNullInt32(transfer.MinTransferTime),
			Distance:        apihelpers.ConvertSqlNullInt32(transfer.Distance),
		})
	}
	log.Println("GetStopInSystem took", time.Since(startTime))
	return result, s.Finish()
}

func buildStopTreeResponse(s *session.Session, systemID string,
	basePk int64, stopTree *stoptree.StopTree, serviceMaps map[int64][]*api.ServiceMapForStop) *api.RelatedStop {
	stopPkToResponse := map[int64]*api.RelatedStop{}
	stopTree.VisitDFS(func(node *stoptree.StopTreeNode) {
		if !stoptree.IsStation(node.Stop) && basePk != node.Stop.Pk {
			return
		}
		thisResponse := &api.RelatedStop{
			Id:          node.Stop.ID,
			Name:        node.Stop.Name.String,
			ServiceMaps: serviceMaps[node.Stop.Pk],
			Href:        s.Hrefs.Stop(systemID, node.Stop.ID),
		}
		if node.Parent != nil {
			if parentResponse, ok := stopPkToResponse[node.Parent.Stop.Pk]; ok {
				thisResponse.ParentStop = parentResponse
			}
		}
		for _, child := range node.Children {
			if childResponse, ok := stopPkToResponse[child.Stop.Pk]; ok {
				thisResponse.ChildStops = append(thisResponse.ChildStops, childResponse)
			}
		}
		stopPkToResponse[node.Stop.Pk] = thisResponse
	})
	return stopPkToResponse[basePk]
}

type DirectionNameMatcher struct {
	rules []db.DirectionNameRule
}

func NewDirectionNameMatcher(ctx context.Context, querier db.Querier, stopPks []int64) (*DirectionNameMatcher, error) {
	rules, err := querier.ListDirectionNameRulesForStops(ctx, stopPks)
	if err != nil {
		return nil, err
	}
	return &DirectionNameMatcher{rules: rules}, nil
}

func (m *DirectionNameMatcher) Match(stop_time *db.ListStopTimesAtStopsRow) *string {
	for _, rule := range m.rules {
		if stop_time.StopPk != rule.StopPk {
			continue
		}
		if stop_time.DirectionID.Valid &&
			rule.DirectionID.Valid &&
			stop_time.DirectionID.Bool != rule.DirectionID.Bool {
			continue
		}
		if stop_time.Track.Valid &&
			rule.Track.Valid &&
			stop_time.Track.String != rule.Track.String {
			continue
		}
		return &rule.Name
	}
	return nil
}

func (m *DirectionNameMatcher) Directions() []string {
	names := map[string]bool{}
	for _, rule := range m.rules {
		names[rule.Name] = true
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
		Time:        apihelpers.ConvertSqlNullTime(time),
		Delay:       apihelpers.ConvertSqlNullInt32(delay),
		Uncertainty: apihelpers.ConvertSqlNullInt32(uncertainty),
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
