// Package static contains the code for updating the database from a GTFS static feed.
package static

import (
	"context"
	"fmt"

	"github.com/jamespfennell/gtfs"
	"github.com/jamespfennell/transiter/internal/convert"
	"github.com/jamespfennell/transiter/internal/db/dbwrappers"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/servicemaps"
	"github.com/jamespfennell/transiter/internal/update/common"
	"google.golang.org/protobuf/encoding/protojson"
)

func Parse(content []byte) (*gtfs.Static, error) {
	// TODO: support custom GTFS static options
	return gtfs.ParseStatic(content, gtfs.ParseStaticOptions{})
}

func Update(ctx context.Context, updateCtx common.UpdateContext, data *gtfs.Static) error {
	agencyIDToPk, err := updateAgencies(ctx, updateCtx, data.Agencies)
	if err != nil {
		return err
	}
	routeIDToPk, err := updateRoutes(ctx, updateCtx, data.Routes, agencyIDToPk)
	if err != nil {
		return err
	}
	stopIDToPk, err := updateStops(ctx, updateCtx, data.Stops)
	if err != nil {
		return err
	}
	if err := updateTransfers(ctx, updateCtx, data.Transfers, stopIDToPk); err != nil {
		return err
	}
	serviceIDToPk, err := updateServices(ctx, updateCtx, data.Services)
	if err != nil {
		return err
	}
	shapeIDToPk, err := updateShapes(ctx, updateCtx, data.Shapes)
	if err != nil {
		return err
	}
	err = updateScheduledTrips(ctx, updateCtx, data.Trips, routeIDToPk, serviceIDToPk, stopIDToPk, shapeIDToPk)
	if err != nil {
		return err
	}
	if err := servicemaps.UpdateStaticMaps(ctx, updateCtx.Querier, updateCtx.Logger, servicemaps.UpdateStaticMapsArgs{
		SystemPk:    updateCtx.SystemPk,
		Trips:       data.Trips,
		RouteIDToPk: routeIDToPk,
	}); err != nil {
		return err
	}
	return nil
}

func updateAgencies(ctx context.Context, updateCtx common.UpdateContext, agencies []gtfs.Agency) (map[string]int64, error) {
	oldIDToPk, err := dbwrappers.MapAgencyIDToPk(ctx, updateCtx.Querier, updateCtx.SystemPk)
	if err != nil {
		return nil, err
	}
	newIDToPk := map[string]int64{}
	for _, agency := range agencies {
		var err error
		pk, ok := oldIDToPk[agency.Id]
		if ok {
			err = updateCtx.Querier.UpdateAgency(ctx, db.UpdateAgencyParams{
				Pk:       pk,
				FeedPk:   updateCtx.FeedPk,
				Name:     agency.Name,
				Url:      agency.Url,
				Timezone: agency.Timezone,
				Language: convert.NullIfEmptyString(agency.Language),
				Phone:    convert.NullIfEmptyString(agency.Phone),
				FareUrl:  convert.NullIfEmptyString(agency.FareUrl),
				Email:    convert.NullIfEmptyString(agency.Email),
			})
		} else {
			pk, err = updateCtx.Querier.InsertAgency(ctx, db.InsertAgencyParams{
				ID:       agency.Id,
				SystemPk: updateCtx.SystemPk,
				FeedPk:   updateCtx.FeedPk,
				Name:     agency.Name,
				Url:      agency.Url,
				Timezone: agency.Timezone,
				Language: convert.NullIfEmptyString(agency.Language),
				Phone:    convert.NullIfEmptyString(agency.Phone),
				FareUrl:  convert.NullIfEmptyString(agency.FareUrl),
				Email:    convert.NullIfEmptyString(agency.Email),
			})
			oldIDToPk[agency.Id] = pk
		}
		if err != nil {
			return nil, err
		}
		newIDToPk[agency.Id] = pk
	}
	if err := updateCtx.Querier.DeleteStaleAgencies(ctx, db.DeleteStaleAgenciesParams{
		FeedPk:           updateCtx.FeedPk,
		UpdatedAgencyPks: common.MapValues(newIDToPk),
	}); err != nil {
		return nil, err
	}
	return newIDToPk, nil
}

func updateRoutes(ctx context.Context, updateCtx common.UpdateContext, routes []gtfs.Route, agencyIDToPk map[string]int64) (map[string]int64, error) {
	oldIDToPk, err := dbwrappers.MapRouteIDToPkInSystem(ctx, updateCtx.Querier, updateCtx.SystemPk)
	if err != nil {
		return nil, err
	}
	newIDToPk := map[string]int64{}
	for _, route := range routes {
		agencyPk, ok := agencyIDToPk[route.Agency.Id]
		if !ok {
			updateCtx.Logger.WarnCtx(ctx, fmt.Sprintf("route %q references agency %q that doesn't exist; skipping", route.Id, route.Agency.Id))
			continue
		}
		pk, ok := oldIDToPk[route.Id]
		if ok {
			err = updateCtx.Querier.UpdateRoute(ctx, db.UpdateRouteParams{
				Pk:                pk,
				FeedPk:            updateCtx.FeedPk,
				Color:             route.Color,
				TextColor:         route.TextColor,
				ShortName:         convert.NullIfEmptyString(route.ShortName),
				LongName:          convert.NullIfEmptyString(route.LongName),
				Description:       convert.NullIfEmptyString(route.Description),
				Url:               convert.NullIfEmptyString(route.Url),
				SortOrder:         convert.NullInt32(route.SortOrder),
				Type:              route.Type.String(),
				ContinuousPickup:  route.ContinuousPickup.String(),
				ContinuousDropOff: route.ContinuousDropOff.String(),
				AgencyPk:          agencyPk,
			})
		} else {
			pk, err = updateCtx.Querier.InsertRoute(ctx, db.InsertRouteParams{
				ID:                route.Id,
				SystemPk:          updateCtx.SystemPk,
				FeedPk:            updateCtx.FeedPk,
				Color:             route.Color,
				TextColor:         route.TextColor,
				ShortName:         convert.NullIfEmptyString(route.ShortName),
				LongName:          convert.NullIfEmptyString(route.LongName),
				Description:       convert.NullIfEmptyString(route.Description),
				Url:               convert.NullIfEmptyString(route.Url),
				SortOrder:         convert.NullInt32(route.SortOrder),
				Type:              route.Type.String(),
				ContinuousPickup:  route.ContinuousPickup.String(),
				ContinuousDropOff: route.ContinuousDropOff.String(),
				AgencyPk:          agencyPk,
			})
		}
		if err != nil {
			return nil, err
		}
		newIDToPk[route.Id] = pk
	}
	if err := updateCtx.Querier.DeleteStaleRoutes(ctx, db.DeleteStaleRoutesParams{
		FeedPk:          updateCtx.FeedPk,
		UpdatedRoutePks: common.MapValues(newIDToPk),
	}); err != nil {
		return nil, err
	}
	return newIDToPk, nil
}

func updateStops(ctx context.Context, updateCtx common.UpdateContext, stops []gtfs.Stop) (map[string]int64, error) {
	oldIDToPk, err := dbwrappers.MapStopIDToPkInSystem(ctx, updateCtx.Querier, updateCtx.SystemPk)
	if err != nil {
		return nil, err
	}
	newIDToPk := map[string]int64{}
	for _, stop := range stops {
		pk, ok := oldIDToPk[stop.Id]
		if ok {
			err = updateCtx.Querier.UpdateStop(ctx, db.UpdateStopParams{
				Pk:                 pk,
				FeedPk:             updateCtx.FeedPk,
				Name:               convert.NullIfEmptyString(stop.Name),
				Type:               stop.Type.String(),
				Location:           convert.Gps(stop.Longitude, stop.Latitude),
				Url:                convert.NullIfEmptyString(stop.Url),
				Code:               convert.NullIfEmptyString(stop.Code),
				Description:        convert.NullIfEmptyString(stop.Description),
				PlatformCode:       convert.NullIfEmptyString(stop.PlatformCode),
				Timezone:           convert.NullIfEmptyString(stop.Timezone),
				WheelchairBoarding: convert.WheelchairAccessible(stop.WheelchairBoarding),
				ZoneID:             convert.NullIfEmptyString(stop.ZoneId),
			})
		} else {
			pk, err = updateCtx.Querier.InsertStop(ctx, db.InsertStopParams{
				ID:                 stop.Id,
				SystemPk:           updateCtx.SystemPk,
				FeedPk:             updateCtx.FeedPk,
				Name:               convert.NullIfEmptyString(stop.Name),
				Type:               stop.Type.String(),
				Location:           convert.Gps(stop.Longitude, stop.Latitude),
				Url:                convert.NullIfEmptyString(stop.Url),
				Code:               convert.NullIfEmptyString(stop.Code),
				Description:        convert.NullIfEmptyString(stop.Description),
				PlatformCode:       convert.NullIfEmptyString(stop.PlatformCode),
				Timezone:           convert.NullIfEmptyString(stop.Timezone),
				WheelchairBoarding: convert.WheelchairAccessible(stop.WheelchairBoarding),
				ZoneID:             convert.NullIfEmptyString(stop.ZoneId),
			})
		}
		if err != nil {
			return nil, err
		}
		newIDToPk[stop.Id] = pk
	}
	if err := updateCtx.Querier.DeleteStaleStops(ctx, db.DeleteStaleStopsParams{
		FeedPk:         updateCtx.FeedPk,
		UpdatedStopPks: common.MapValues(newIDToPk),
	}); err != nil {
		return nil, err
	}
	// We now populate the parent stop field
	for _, stop := range stops {
		if stop.Parent == nil {
			continue
		}
		parentStopPk, ok := newIDToPk[stop.Parent.Id]
		if !ok {
			updateCtx.Logger.WarnCtx(ctx, fmt.Sprintf("stop %q references parent stop %q that doesn't exist", stop.Id, stop.Parent.Id))
			continue
		}
		if err := updateCtx.Querier.UpdateStop_Parent(ctx, db.UpdateStop_ParentParams{
			Pk:           newIDToPk[stop.Id],
			ParentStopPk: convert.NullInt64(&parentStopPk),
		}); err != nil {
			return nil, err
		}
	}
	return newIDToPk, nil
}

func updateTransfers(ctx context.Context, updateCtx common.UpdateContext, transfers []gtfs.Transfer, stopIDToPk map[string]int64) error {
	// Transfers are special because (a) they don't have an ID and (b) no other entity references them
	// by foriegn key. It is thus possible (and easier) to update transfers by deleting the existing transfers
	// and inserting the new ones.
	if err := updateCtx.Querier.DeleteTransfers(ctx, updateCtx.FeedPk); err != nil {
		return err
	}
	for _, transfer := range transfers {
		fromPk, ok := stopIDToPk[transfer.From.Id]
		if !ok {
			continue
		}
		toPk, ok := stopIDToPk[transfer.To.Id]
		if !ok {
			continue
		}
		if err := updateCtx.Querier.InsertTransfer(ctx, db.InsertTransferParams{
			SystemPk:        convert.NullInt64(&updateCtx.SystemPk),
			FeedPk:          updateCtx.FeedPk,
			FromStopPk:      fromPk,
			ToStopPk:        toPk,
			Type:            transfer.Type.String(),
			MinTransferTime: convert.NullInt32(transfer.MinTransferTime),
		}); err != nil {
			return err
		}
	}
	return nil
}

func updateServices(ctx context.Context, updateCtx common.UpdateContext, services []gtfs.Service) (map[string]int64, error) {
	serviceIdsInUpdate := []string{}
	for _, service := range services {
		serviceIdsInUpdate = append(serviceIdsInUpdate, service.Id)
	}

	err := updateCtx.Querier.DeleteScheduledServices(ctx, db.DeleteScheduledServicesParams{
		FeedPk:            updateCtx.FeedPk,
		SystemPk:          updateCtx.SystemPk,
		UpdatedServiceIds: serviceIdsInUpdate,
	})
	if err != nil {
		return nil, err
	}

	serviceIDToPk := map[string]int64{}
	for _, service := range services {
		pk, err := updateCtx.Querier.InsertScheduledService(ctx, db.InsertScheduledServiceParams{
			ID:        service.Id,
			SystemPk:  updateCtx.SystemPk,
			FeedPk:    updateCtx.FeedPk,
			StartDate: convert.Date(service.StartDate),
			EndDate:   convert.Date(service.EndDate),
			Monday:    convert.Bool(service.Monday),
			Tuesday:   convert.Bool(service.Tuesday),
			Wednesday: convert.Bool(service.Wednesday),
			Thursday:  convert.Bool(service.Thursday),
			Friday:    convert.Bool(service.Friday),
			Saturday:  convert.Bool(service.Saturday),
			Sunday:    convert.Bool(service.Sunday),
		})
		if err != nil {
			return nil, err
		}

		for _, addedDate := range service.AddedDates {
			if err := updateCtx.Querier.InsertScheduledServiceAddition(ctx, db.InsertScheduledServiceAdditionParams{
				ServicePk: pk,
				Date:      convert.Date(addedDate),
			}); err != nil {
				return nil, err
			}
		}

		for _, removedDate := range service.RemovedDates {
			if err := updateCtx.Querier.InsertScheduledServiceRemoval(ctx, db.InsertScheduledServiceRemovalParams{
				ServicePk: pk,
				Date:      convert.Date(removedDate),
			}); err != nil {
				return nil, err
			}
		}

		serviceIDToPk[service.Id] = pk
	}

	return serviceIDToPk, nil
}

func updateScheduledTrips(
	ctx context.Context,
	updateCtx common.UpdateContext,
	trips []gtfs.ScheduledTrip,
	routeIDToPk map[string]int64,
	serviceIDToPk map[string]int64,
	stopIDToPk map[string]int64,
	shapeIDToPk map[string]int64) error {

	var tripParams []db.InsertScheduledTripParams
	var tripIDs []string
	for _, trip := range trips {
		routePk, ok := routeIDToPk[trip.Route.Id]
		if !ok {
			updateCtx.Logger.Warn("Skipping trip with unknown route ID", "Route ID", trip.Route.Id)
			continue
		}
		servicePk, ok := serviceIDToPk[trip.Service.Id]
		if !ok {
			updateCtx.Logger.Warn("Skipping trip with unknown service ID", "Service ID", trip.Service.Id)
			continue
		}

		var shapePkOrNil *int64 = nil
		if trip.Shape != nil {
			if shapePk, ok := shapeIDToPk[trip.Shape.ID]; ok {
				shapePkOrNil = &shapePk
			} else {
				updateCtx.Logger.Warn("Trip with unknown shape ID", "Trip ID", trip.ID, "Shape ID", trip.Shape.ID)
			}
		}

		tripParams = append(tripParams, db.InsertScheduledTripParams{
			ID:                   trip.ID,
			RoutePk:              routePk,
			ServicePk:            servicePk,
			ShapePk:              convert.NullInt64(shapePkOrNil),
			Headsign:             convert.NullIfEmptyString(trip.Headsign),
			ShortName:            convert.NullIfEmptyString(trip.ShortName),
			DirectionID:          convert.DirectionID(trip.DirectionId),
			WheelchairAccessible: convert.WheelchairAccessible(trip.WheelchairAccessible),
			BikesAllowed:         convert.BikesAllowed(trip.BikesAllowed),
		})
		tripIDs = append(tripIDs, trip.ID)
	}

	if _, err := updateCtx.Querier.InsertScheduledTrip(ctx, tripParams); err != nil {
		return err
	}

	tripIDToPk, err := dbwrappers.MapScheduledTripIDToPkInSystem(ctx, updateCtx.Querier, updateCtx.SystemPk, tripIDs)
	if err != nil {
		return err
	}

	var stopTimeParams []db.InsertScheduledTripStopTimeParams
	for _, trip := range trips {
		tripPk := tripIDToPk[trip.ID]
		for _, stopTime := range trip.StopTimes {
			stopTimeParams = append(stopTimeParams, db.InsertScheduledTripStopTimeParams{
				TripPk:                tripPk,
				StopPk:                stopIDToPk[stopTime.Stop.Id],
				ArrivalTime:           convert.Duration(stopTime.ArrivalTime),
				DepartureTime:         convert.Duration(stopTime.DepartureTime),
				StopSequence:          int32(stopTime.StopSequence),
				Headsign:              convert.NullIfEmptyString(stopTime.Headsign),
				ContinuousDropOff:     stopTime.ContinuousDropOff.String(),
				ContinuousPickup:      stopTime.ContinuousPickup.String(),
				DropOffType:           stopTime.DropOffType.String(),
				ExactTimes:            stopTime.ExactTimes,
				PickupType:            stopTime.PickupType.String(),
				ShapeDistanceTraveled: convert.NullFloat64(stopTime.ShapeDistanceTraveled),
			})
		}

		for _, frequency := range trip.Frequencies {
			if err := updateCtx.Querier.InsertScheduledTripFrequency(ctx, db.InsertScheduledTripFrequencyParams{
				TripPk:         tripPk,
				StartTime:      int32(frequency.StartTime.Seconds()),
				EndTime:        int32(frequency.EndTime.Seconds()),
				Headway:        int32(frequency.Headway.Seconds()),
				FrequencyBased: convert.ExactTimesToIsFrequencyBased(frequency.ExactTimes),
			}); err != nil {
				return err
			}
		}
	}

	if _, err := updateCtx.Querier.InsertScheduledTripStopTime(ctx, stopTimeParams); err != nil {
		return err
	}

	return nil
}

func updateShapes(
	ctx context.Context,
	updateCtx common.UpdateContext,
	shapes []gtfs.Shape) (map[string]int64, error) {

	shapeIDsInUpdate := []string{}
	for _, shape := range shapes {
		shapeIDsInUpdate = append(shapeIDsInUpdate, shape.ID)
	}

	err := updateCtx.Querier.DeleteShapes(ctx, db.DeleteShapesParams{
		FeedPk:          updateCtx.FeedPk,
		SystemPk:        updateCtx.SystemPk,
		UpdatedShapeIds: shapeIDsInUpdate,
	})
	if err != nil {
		return nil, err
	}

	shapeIDToPk := map[string]int64{}
	for _, shape := range shapes {
		bytes, err := protojson.Marshal(convert.ApiShape(&shape))
		if err != nil {
			return nil, err
		}
		pk, err := updateCtx.Querier.InsertShape(ctx, db.InsertShapeParams{
			SystemPk: updateCtx.SystemPk,
			FeedPk:   updateCtx.FeedPk,
			ID:       shape.ID,
			Shape:    bytes,
		})
		if err != nil {
			return nil, err
		}

		shapeIDToPk[shape.ID] = pk
	}

	return shapeIDToPk, nil
}
