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
		var wheelchairBoarding *bool
		switch stop.WheelchairBoarding {
		case gtfs.WheelchairBoarding_Possible:
			t := true
			wheelchairBoarding = &t
		case gtfs.WheelchairBoarding_NotPossible:
			f := false
			wheelchairBoarding = &f
		}
		pk, ok := oldIDToPk[stop.Id]
		if ok {
			err = updateCtx.Querier.UpdateStop(ctx, db.UpdateStopParams{
				Pk:                 pk,
				FeedPk:             updateCtx.FeedPk,
				Name:               convert.NullIfEmptyString(stop.Name),
				Type:               stop.Type.String(),
				Longitude:          convert.Gps(stop.Longitude),
				Latitude:           convert.Gps(stop.Latitude),
				Url:                convert.NullIfEmptyString(stop.Url),
				Code:               convert.NullIfEmptyString(stop.Code),
				Description:        convert.NullIfEmptyString(stop.Description),
				PlatformCode:       convert.NullIfEmptyString(stop.PlatformCode),
				Timezone:           convert.NullIfEmptyString(stop.Timezone),
				WheelchairBoarding: convert.NullBool(wheelchairBoarding),
				ZoneID:             convert.NullIfEmptyString(stop.ZoneId),
			})
		} else {
			pk, err = updateCtx.Querier.InsertStop(ctx, db.InsertStopParams{
				ID:                 stop.Id,
				SystemPk:           updateCtx.SystemPk,
				FeedPk:             updateCtx.FeedPk,
				Name:               convert.NullIfEmptyString(stop.Name),
				Type:               stop.Type.String(),
				Longitude:          convert.Gps(stop.Longitude),
				Latitude:           convert.Gps(stop.Latitude),
				Url:                convert.NullIfEmptyString(stop.Url),
				Code:               convert.NullIfEmptyString(stop.Code),
				Description:        convert.NullIfEmptyString(stop.Description),
				PlatformCode:       convert.NullIfEmptyString(stop.PlatformCode),
				Timezone:           convert.NullIfEmptyString(stop.Timezone),
				WheelchairBoarding: convert.NullBool(wheelchairBoarding),
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
