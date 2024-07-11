package endpoints

import (
	"context"
	"math"
	"time"

	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jamespfennell/transiter/internal/db/dbwrappers"
	"github.com/jamespfennell/transiter/internal/public/errors"

	"github.com/jamespfennell/transiter/internal/convert"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
)

func ListStops(ctx context.Context, r *Context, req *api.ListStopsRequest) (*api.ListStopsReply, error) {
	system, err := getSystem(ctx, r.Querier, req.SystemId)
	if err != nil {
		return nil, err
	}
	filterByID := req.GetFilterById()
	//lint:ignore SA1019 we still consult the deprecated field as it's not been removed yet
	if req.GetOnlyReturnSpecifiedIds() {
		r.Monitoring.RecordDeprecatedFeatureUse("ListStopsRequest.only_return_specified_ids")
		filterByID = true
	}
	if !filterByID && len(req.Id) > 0 {
		return nil, errors.NewInvalidArgumentError("filter_by_id is false but IDs were provided")
	}
	if !req.GetFilterByType() && len(req.GetType()) > 0 {
		return nil, errors.NewInvalidArgumentError("filter_by_type is false but types were provided")
	}

	numStops := r.EndpointOptions.MaxEntitiesPerRequest
	if numStops <= 0 {
		// Avoid overflow since pagination over-fetches by one
		numStops = math.MaxInt32 - 1
	}
	if req.Limit != nil && *req.Limit < numStops {
		numStops = *req.Limit
	}
	var firstID string
	if req.FirstId != nil {
		firstID = *req.FirstId
	}

	var stops []db.Stop
	if req.GetSearchMode() == api.ListStopsRequest_DISTANCE {
		if req.Latitude == nil || req.Longitude == nil || req.MaxDistance == nil {
			return nil, errors.NewInvalidArgumentError("latitude, longitude, and max_distance are required when using DISTANCE search_mode")
		}
		if firstID != "" {
			return nil, errors.NewInvalidArgumentError("first_id can not be used when using DISTANCE search_mode")
		}
		stops, err = r.Querier.ListStops_Geographic(ctx, db.ListStops_GeographicParams{
			SystemPk:     system.Pk,
			Base:         convert.Gps(req.Longitude, req.Latitude),
			MaxDistance:  *req.MaxDistance,
			MaxResults:   numStops,
			FilterByType: req.GetFilterByType(),
			Types:        apiTypesToStrings(req.GetType()),
		})
	} else {
		stops, err = r.Querier.ListStops(ctx, db.ListStopsParams{
			SystemPk:     system.Pk,
			FirstStopID:  firstID,
			NumStops:     numStops + 1,
			FilterByID:   filterByID,
			StopIds:      req.Id,
			FilterByType: req.GetFilterByType(),
			Types:        apiTypesToStrings(req.GetType()),
		})
	}

	if err != nil {
		return nil, err
	}
	var nextID *string
	if len(stops) == int(numStops+1) {
		nextID = &stops[len(stops)-1].ID
		stops = stops[:len(stops)-1]
	}
	apiStops, err := buildStopsResponse(ctx, r, req.GetSystemId(), stops, req)
	if err != nil {
		return nil, err
	}
	return &api.ListStopsReply{
		Stops:  apiStops,
		NextId: nextID,
	}, nil
}

func apiTypesToStrings(in []api.Stop_Type) []string {
	var out []string
	for _, t := range in {
		out = append(out, t.String())
	}
	return out
}

func ListTransfers(ctx context.Context, r *Context, req *api.ListTransfersRequest) (*api.ListTransfersReply, error) {
	system, err := getSystem(ctx, r.Querier, req.SystemId)
	if err != nil {
		return nil, err
	}
	transfers, err := r.Querier.ListTransfersInSystem(ctx, system.Pk)
	if err != nil {
		return nil, err
	}
	apiTransfers, err := buildTransfersResponse(ctx, r, req.GetSystemId(), transfers)
	if err != nil {
		return nil, err
	}
	return &api.ListTransfersReply{Transfers: apiTransfers}, nil
}

func GetTransfer(ctx context.Context, r *Context, req *api.GetTransferRequest) (*api.Transfer, error) {
	_, transfer, err := getTransfer(ctx, r.Querier, req.SystemId, req.TransferId)
	if err != nil {
		return nil, err
	}
	apiTransfers, err := buildTransfersResponse(ctx, r, req.GetSystemId(), []db.Transfer{transfer})
	if err != nil {
		return nil, err
	}
	return apiTransfers[0], nil
}

func buildTransfersResponse(ctx context.Context, r *Context, systemID string, transfers []db.Transfer) ([]*api.Transfer, error) {
	stopPksMap := map[int64]bool{}
	for _, transfer := range transfers {
		stopPksMap[transfer.FromStopPk] = true
		stopPksMap[transfer.ToStopPk] = true
	}
	stops, err := r.Querier.ListStopsByPk(ctx, mapToSlice(stopPksMap))
	if err != nil {
		return nil, err
	}
	stopPkToApiPreview := map[int64]*api.Stop_Reference{}
	for _, stop := range stops {
		stopPkToApiPreview[stop.Pk] = r.Reference.Stop(stop.StopID, systemID, stop.Name)
	}
	var apiTransfers []*api.Transfer
	for _, transfer := range transfers {
		apiTransfers = append(apiTransfers, &api.Transfer{
			Id:              transfer.ID,
			FromStop:        stopPkToApiPreview[transfer.FromStopPk],
			ToStop:          stopPkToApiPreview[transfer.ToStopPk],
			Type:            convert.TransferType(transfer.Type),
			MinTransferTime: convert.SQLNullInt32(transfer.MinTransferTime),
		})
	}
	return apiTransfers, nil
}

func GetStop(ctx context.Context, r *Context, req *api.GetStopRequest) (*api.Stop, error) {
	_, stop, err := getStop(ctx, r.Querier, req.SystemId, req.StopId)
	if err != nil {
		return nil, err
	}
	apiStops, err := buildStopsResponse(ctx, r, req.SystemId, []db.Stop{stop}, req)
	if err != nil {
		return nil, err
	}
	return apiStops[0], nil
}

type stopRequest interface {
	GetSkipStopTimes() bool
	GetSkipServiceMaps() bool
	GetSkipAlerts() bool
	GetSkipTransfers() bool
}

func buildStopsResponse(ctx context.Context, r *Context, systemID string, stops []db.Stop, req stopRequest) ([]*api.Stop, error) {
	data, err := getRawStopData(ctx, r, stops, req)
	if err != nil {
		return nil, err
	}

	stopPkToApiPreview := map[int64]*api.Stop_Reference{}
	for i := range data.allStops {
		stop := &data.allStops[i]
		stopPkToApiPreview[stop.Pk] = r.Reference.Stop(stop.StopID, systemID, stop.Name)
	}
	routePkToApiPreview := map[int64]*api.Route_Reference{}
	for i := range data.allRoutes {
		route := &data.allRoutes[i]
		routePkToApiPreview[route.Pk] = r.Reference.Route(route.ID, systemID, route.Color)
	}
	stopPkToApiTransfers := buildStopPkToApiTransfers(data, stopPkToApiPreview)
	stopPkToApiServiceMaps := buildStopPkToApiServiceMaps(data, routePkToApiPreview)
	stopPkToApiAlerts := buildStopPkToApiAlerts(r, systemID, data)
	stopPkToApiStopTimes := buildStopPkToApiStopsTimes(r, data, routePkToApiPreview, stopPkToApiPreview, systemID)
	stopPkToApiHeadsignRules := buildStopPkToApiHeadsignRules(data, stopPkToApiPreview)
	stopPkToChildren := map[int64][]*api.Stop_Reference{}
	for stopPk, childPks := range data.stopPkToChildPks {
		for _, childPk := range childPks {
			stopPkToChildren[stopPk] = append(
				stopPkToChildren[stopPk],
				stopPkToApiPreview[childPk],
			)
		}
	}

	var result []*api.Stop
	for _, stop := range stops {
		stop := stop
		var parent *api.Stop_Reference
		if stop.ParentStopPk.Valid {
			parent = stopPkToApiPreview[stop.ParentStopPk.Int64]
		}
		result = append(result, &api.Stop{
			Id:                 stop.ID,
			Code:               convert.SQLNullString(stop.Code),
			Name:               convert.SQLNullString(stop.Name),
			Description:        convert.SQLNullString(stop.Description),
			ZoneId:             convert.SQLNullString(stop.ZoneID),
			Longitude:          stop.Location.NullableLongitude(),
			Latitude:           stop.Location.NullableLatitude(),
			Url:                convert.SQLNullString(stop.Url),
			Type:               convert.StopType(stop.Type),
			Timezone:           convert.SQLNullString(stop.Timezone),
			PlatformCode:       convert.SQLNullString(stop.PlatformCode),
			WheelchairBoarding: convert.SQLNullBool(stop.WheelchairBoarding),
			ParentStop:         parent,
			ChildStops:         stopPkToChildren[stop.Pk],
			Transfers:          stopPkToApiTransfers[stop.Pk],
			ServiceMaps:        stopPkToApiServiceMaps[stop.Pk],
			Alerts:             stopPkToApiAlerts[stop.Pk],
			StopTimes:          stopPkToApiStopTimes[stop.Pk],
			HeadsignRules:      stopPkToApiHeadsignRules[stop.Pk],
		})
	}
	return result, nil
}

type rawStopData struct {
	stopPkToDescendentPks map[int64]map[int64]bool
	transfers             []db.Transfer
	alerts                []db.ListActiveAlertsForStopsRow
	stopTimes             []db.ListTripStopTimesByStopsRow
	tripDestinations      []db.GetDestinationsForTripsRow
	serviceMaps           []db.ListServiceMapsForStopsRow
	serviceMapConfigIDs   []db.ListServiceMapsConfigIDsForStopsRow
	headsignRules         []db.StopHeadsignRule
	allStops              []db.ListStopsByPkRow
	allRoutes             []db.ListRoutesByPkRow
	stopPkToChildPks      map[int64][]int64
}

func getRawStopData(ctx context.Context, r *Context, stops []db.Stop, req stopRequest) (rawStopData, error) {
	var d rawStopData
	var err error

	var stopPks []int64
	var rootPks []int64
	for i := range stops {
		stopPks = append(stopPks, stops[i].Pk)
		if !stops[i].ParentStopPk.Valid {
			rootPks = append(rootPks, stops[i].Pk)
		}
	}

	d.stopPkToChildPks, err = dbwrappers.MapStopPkToChildPks(ctx, r.Querier, stopPks)
	if err != nil {
		return d, err
	}
	d.stopPkToDescendentPks, err = dbwrappers.MapStopPkToDescendentPks(ctx, r.Querier, stopPks)
	if err != nil {
		return d, err
	}
	allDescendentPksMap := map[int64]bool{}
	for _, descendentPks := range d.stopPkToDescendentPks {
		for descendentPk := range descendentPks {
			allDescendentPksMap[descendentPk] = true
		}
	}
	allDescendentPks := mapToSlice(allDescendentPksMap)

	if !req.GetSkipTransfers() {
		d.transfers, err = r.Querier.ListTransfersFromStops(ctx, allDescendentPks)
		if err != nil {
			return d, err
		}
	}
	if !req.GetSkipAlerts() {
		d.alerts, err = r.Querier.ListActiveAlertsForStops(ctx, db.ListActiveAlertsForStopsParams{
			StopPks:     allDescendentPks,
			PresentTime: pgtype.Timestamptz{Valid: true, Time: time.Now()},
		})
		if err != nil {
			return d, err
		}
	}
	if !req.GetSkipStopTimes() {
		d.stopTimes, err = r.Querier.ListTripStopTimesByStops(ctx, allDescendentPks)
		if err != nil {
			return d, err
		}
		tripPks := map[int64]bool{}
		for i := range d.stopTimes {
			tripPks[d.stopTimes[i].TripPk] = true
		}
		d.tripDestinations, err = r.Querier.GetDestinationsForTrips(ctx, mapToSlice(tripPks))
		if err != nil {
			return d, err
		}
	}
	if !req.GetSkipServiceMaps() {
		d.serviceMaps, err = r.Querier.ListServiceMapsForStops(ctx, rootPks)
		if err != nil {
			return d, err
		}
		d.serviceMapConfigIDs, err = r.Querier.ListServiceMapsConfigIDsForStops(ctx, rootPks)
		if err != nil {
			return d, err
		}
	}
	d.headsignRules, err = r.Querier.ListStopHeadsignRulesForStops(ctx, allDescendentPks)
	if err != nil {
		return d, err
	}

	allStopPksMap := allDescendentPksMap
	for i := range d.transfers {
		allStopPksMap[d.transfers[i].ToStopPk] = true
	}
	for i := range stops {
		parentPk := stops[i].ParentStopPk
		if parentPk.Valid {
			allStopPksMap[parentPk.Int64] = true
		}
	}
	for i := range d.tripDestinations {
		allStopPksMap[d.tripDestinations[i].DestinationPk] = true
	}
	d.allStops, err = r.Querier.ListStopsByPk(ctx, mapToSlice(allStopPksMap))
	if err != nil {
		return d, err
	}

	allRoutePksMap := map[int64]bool{}
	for i := range d.serviceMaps {
		allRoutePksMap[d.serviceMaps[i].RoutePk] = true
	}
	for i := range d.stopTimes {
		allRoutePksMap[d.stopTimes[i].RoutePk] = true
	}
	d.allRoutes, err = r.Querier.ListRoutesByPk(ctx, mapToSlice(allRoutePksMap))
	if err != nil {
		return d, err
	}

	return d, nil
}

func buildStopPkToApiTransfers(data rawStopData, stopPkToApiPreview map[int64]*api.Stop_Reference) map[int64][]*api.Transfer {
	m := map[int64][]*api.Transfer{}
	for _, transfer := range data.transfers {
		m[transfer.FromStopPk] = append(m[transfer.FromStopPk], &api.Transfer{
			Id:              transfer.ID,
			FromStop:        stopPkToApiPreview[transfer.FromStopPk],
			ToStop:          stopPkToApiPreview[transfer.ToStopPk],
			Type:            convert.TransferType(transfer.Type),
			MinTransferTime: convert.SQLNullInt32(transfer.MinTransferTime),
		})
	}
	return liftToAncestors(data, m)
}

func buildStopPkToApiServiceMaps(data rawStopData, routePkToApiPreview map[int64]*api.Route_Reference) map[int64][]*api.Stop_ServiceMap {
	m := map[int64]map[string][]int64{}
	for _, row := range data.serviceMapConfigIDs {
		if _, ok := m[row.Pk]; !ok {
			m[row.Pk] = map[string][]int64{}
		}
		m[row.Pk][row.ID] = []int64{}
	}
	for _, serviceMap := range data.serviceMaps {
		inner := m[serviceMap.StopPk]
		inner[serviceMap.ConfigID] = append(inner[serviceMap.ConfigID], serviceMap.RoutePk)
	}
	n := map[int64][]*api.Stop_ServiceMap{}
	for stopPk, configToRoutePks := range m {
		for configID, routePks := range configToRoutePks {
			apiMap := &api.Stop_ServiceMap{
				ConfigId: configID,
			}
			for _, routePk := range routePks {
				apiMap.Routes = append(apiMap.Routes, routePkToApiPreview[routePk])
			}
			n[stopPk] = append(n[stopPk], apiMap)
		}
	}
	return n
}

func buildStopPkToApiAlerts(r *Context, systemID string, data rawStopData) map[int64][]*api.Alert_Reference {
	m := map[int64][]*api.Alert_Reference{}
	for i := range data.alerts {
		alert := &data.alerts[i]
		m[alert.StopPk] = append(
			m[alert.StopPk],
			r.Reference.Alert(alert.ID, systemID, alert.Cause, alert.Effect),
		)
	}
	return liftToAncestors(data, m)
}

func buildStopPkToApiStopsTimes(
	r *Context,
	data rawStopData,
	routePkToApiPreview map[int64]*api.Route_Reference,
	stopPkToApiPreview map[int64]*api.Stop_Reference,
	systemID string) map[int64][]*api.StopTime {
	m := map[int64][]*api.StopTime{}
	tripPkToDestination := map[int64]*api.Stop_Reference{}
	for _, row := range data.tripDestinations {
		tripPkToDestination[row.TripPk] = stopPkToApiPreview[row.DestinationPk]
	}
	for i := range data.stopTimes {
		stopTime := &data.stopTimes[i]
		headsign := stopTime.Headsign
		// If the headsign is not calculated from realtime trip data,
		// try to fall back to the scheduled trip headsign
		if !headsign.Valid {
			headsign = stopTime.ScheduledTripHeadsign
		}

		apiStopTime := &api.StopTime{
			StopSequence: stopTime.StopSequence,
			Track:        convert.SQLNullString(stopTime.Track),
			Future:       !stopTime.Past,
			Headsign:     convert.SQLNullString(headsign),
			Arrival:      buildEstimatedTime(stopTime.ArrivalTime, stopTime.ArrivalDelay, stopTime.ArrivalUncertainty),
			Departure:    buildEstimatedTime(stopTime.DepartureTime, stopTime.DepartureDelay, stopTime.DepartureUncertainty),
			Trip: r.Reference.Trip(
				stopTime.ID,
				routePkToApiPreview[stopTime.RoutePk],
				tripPkToDestination[stopTime.TripPk],
				nil,
				stopTime.DirectionID.Bool,
			),
			Destination: tripPkToDestination[stopTime.TripPk],
			Stop:        stopPkToApiPreview[stopTime.StopPk],
		}
		if stopTime.VehicleID.Valid {
			vehicle := r.Reference.Vehicle(stopTime.VehicleID.String, systemID)
			//lint:ignore SA1019 we still populate the deprecated field until v2
			apiStopTime.Trip.Vehicle = vehicle
			apiStopTime.Vehicle = vehicle
		}

		m[stopTime.StopPk] = append(m[stopTime.StopPk], apiStopTime)
	}
	return liftToAncestors(data, m)
}

func buildStopPkToApiHeadsignRules(data rawStopData, stopPkToApiPreview map[int64]*api.Stop_Reference) map[int64][]*api.Stop_HeadsignRule {
	m := map[int64][]*api.Stop_HeadsignRule{}
	for i := range data.headsignRules {
		rule := &data.headsignRules[i]
		m[rule.StopPk] = append(
			m[rule.StopPk],
			&api.Stop_HeadsignRule{
				Stop:     stopPkToApiPreview[rule.StopPk],
				Priority: rule.Priority,
				Track:    convert.SQLNullString(rule.Track),
				Headsign: rule.Headsign,
			},
		)
	}
	return liftToAncestors(data, m)
}

func liftToAncestors[T any](data rawStopData, in map[int64][]T) map[int64][]T {
	out := map[int64][]T{}
	for stopPk, descendentPks := range data.stopPkToDescendentPks {
		var s []T
		for descendentPk := range descendentPks {
			s = append(s, in[descendentPk]...)
		}
		out[stopPk] = s
	}
	return out
}

func buildEstimatedTime(time pgtype.Timestamptz, delay, uncertainty pgtype.Int4) *api.StopTime_EstimatedTime {
	return &api.StopTime_EstimatedTime{
		Time:        convert.SQLNullTime(time),
		Delay:       convert.SQLNullInt32(delay),
		Uncertainty: convert.SQLNullInt32(uncertainty),
	}
}

func mapToSlice(m map[int64]bool) []int64 {
	var s []int64
	for elem := range m {
		s = append(s, elem)
	}
	return s
}
