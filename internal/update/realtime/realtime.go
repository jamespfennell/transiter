// Package realtime contains the code for updating the database from a GTFS realtime feed.
package realtime

import (
	"context"
	"math"

	"github.com/jamespfennell/gtfs"
	"github.com/jamespfennell/transiter/internal/convert"
	"github.com/jamespfennell/transiter/internal/db/dbwrappers"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/servicemaps"
	"github.com/jamespfennell/transiter/internal/update/common"
)

func Update(ctx context.Context, updateCtx common.UpdateContext, parsedEntities *gtfs.Realtime) error {
	if err := updateTrips(ctx, updateCtx, parsedEntities.Trips); err != nil {
		return err
	}
	return nil
}

func updateTrips(ctx context.Context, updateCtx common.UpdateContext, trips []gtfs.Trip) error {
	// ASSUMPTIONS: route ID is populated. If not, get it from the static data in an earlier phase

	stopIDToPk, err := dbwrappers.MapStopIDToPkInSystem(ctx, updateCtx.Querier, updateCtx.SystemPk, stopIDsInTrips(trips))
	if err != nil {
		return err
	}
	routeIDToPk, err := dbwrappers.MapRouteIDToPkInSystem(ctx, updateCtx.Querier, updateCtx.SystemPk, routeIDsInTrips(trips))
	if err != nil {
		return err
	}

	var routePks []int64
	for _, routePk := range routeIDToPk {
		routePks = append(routePks, routePk)
	}
	existingTrips, err := dbwrappers.ListTripsForUpdate(ctx, updateCtx.Querier, routePks)
	if err != nil {
		return err
	}

	var serviceMapTrips []servicemaps.Trip
	processedIds := map[dbwrappers.TripUID]bool{}

	for _, trip := range trips {
		routePk, ok := routeIDToPk[trip.ID.RouteID]
		if !ok {
			continue
		}

		uid := dbwrappers.TripUID{RoutePk: routePk, ID: trip.ID.ID}
		if processedIds[uid] {
			continue
		}
		processedIds[uid] = true

		existingTrip := existingTrips[uid]
		populateStopSequences(&trip, existingTrip, stopIDToPk)

		var tripPk int64
		if existingTrip != nil {
			if err := updateCtx.Querier.UpdateTrip(ctx, db.UpdateTripParams{
				Pk:          existingTrip.Pk,
				SourcePk:    updateCtx.UpdatePk,
				DirectionID: convert.DirectionID(trip.ID.DirectionID),
				//StartedAt:    trip.ID.StartDate, // TODO: also the start time?
			}); err != nil {
				return err
			}
			tripPk = existingTrip.Pk
		} else {
			var err error
			tripPk, err = updateCtx.Querier.InsertTrip(ctx, db.InsertTripParams{
				ID:          trip.ID.ID,
				RoutePk:     routePk,
				SourcePk:    updateCtx.UpdatePk,
				DirectionID: convert.DirectionID(trip.ID.DirectionID),
				//StartedAt:    trip.ID.StartDate, // TODO: also the start time?
			})
			if err != nil {
				return err
			}
		}

		stopSequenceToStopTimePk := map[int32]int64{}
		if existingTrip != nil {
			for _, stopTime := range existingTrip.StopTimes {
				stopSequenceToStopTimePk[stopTime.StopSequence] = stopTime.Pk
			}
		}
		serviceMapTrip := servicemaps.Trip{
			RoutePk:     routePk,
			DirectionID: convert.DirectionID(trip.ID.DirectionID),
		}
		for _, stopTime := range trip.StopTimeUpdates {
			if stopTime.StopID == nil {
				continue
			}
			stopPk, ok := stopIDToPk[*stopTime.StopID]
			if !ok {
				continue
			}
			if stopTime.StopSequence == nil {
				continue
			}
			serviceMapTrip.StopPks = append(serviceMapTrip.StopPks, stopPk)
			pk, ok := stopSequenceToStopTimePk[int32(*stopTime.StopSequence)]
			if ok {
				if err := updateCtx.Querier.UpdateTripStopTime(ctx, db.UpdateTripStopTimeParams{
					Pk:                   pk,
					StopPk:               stopPk,
					ArrivalTime:          convert.NullTime(stopTime.GetArrival().Time),
					ArrivalDelay:         convert.NullDuration(stopTime.GetArrival().Delay),
					ArrivalUncertainty:   convert.NullInt32(stopTime.GetArrival().Uncertainty),
					DepartureTime:        convert.NullTime(stopTime.GetDeparture().Time),
					DepartureDelay:       convert.NullDuration(stopTime.GetDeparture().Delay),
					DepartureUncertainty: convert.NullInt32(stopTime.GetDeparture().Uncertainty),
					StopSequence:         int32(*stopTime.StopSequence),
					Track:                convert.NullString(stopTime.NyctTrack),
				}); err != nil {
					return err
				}
				delete(stopSequenceToStopTimePk, int32(*stopTime.StopSequence))
			} else {
				if err := updateCtx.Querier.InsertTripStopTime(ctx, db.InsertTripStopTimeParams{
					TripPk:               tripPk,
					StopPk:               stopPk,
					ArrivalTime:          convert.NullTime(stopTime.GetArrival().Time),
					ArrivalDelay:         convert.NullDuration(stopTime.GetArrival().Delay),
					ArrivalUncertainty:   convert.NullInt32(stopTime.GetArrival().Uncertainty),
					DepartureTime:        convert.NullTime(stopTime.GetDeparture().Time),
					DepartureDelay:       convert.NullDuration(stopTime.GetDeparture().Delay),
					DepartureUncertainty: convert.NullInt32(stopTime.GetDeparture().Uncertainty),
					StopSequence:         int32(*stopTime.StopSequence),
					Track:                convert.NullString(stopTime.NyctTrack),
				}); err != nil {
					return err
				}
			}
		}
		serviceMapTrips = append(serviceMapTrips, serviceMapTrip)

		currentStopSequence := int32(math.MaxInt32)
		for _, stopTime := range trip.StopTimeUpdates {
			if stopTime.StopSequence != nil {
				currentStopSequence = int32(*trip.StopTimeUpdates[0].StopSequence)
				break
			}
		}
		if err := updateCtx.Querier.MarkTripStopTimesPast(ctx, db.MarkTripStopTimesPastParams{
			TripPk:              tripPk,
			CurrentStopSequence: currentStopSequence,
		}); err != nil {
			return err
		}
		var stopTimePks []int64
		for stopSequence, stopTimePk := range stopSequenceToStopTimePk {
			if stopSequence < currentStopSequence {
				continue
			}
			stopTimePks = append(stopTimePks, stopTimePk)
		}
		if err := updateCtx.Querier.DeleteTripStopTimes(ctx, stopTimePks); err != nil {
			return err
		}
	}

	potentiallyStaleRoutePks, err := updateCtx.Querier.DeleteStaleTrips(ctx, db.DeleteStaleTripsParams{
		FeedPk:   updateCtx.FeedPk,
		UpdatePk: updateCtx.UpdatePk,
	})
	if err != nil {
		return err
	}

	routePksSet := map[int64]bool{}
	for _, routePk := range routePks {
		routePksSet[routePk] = true
	}
	var staleRoutePks []int64
	for _, routePk := range potentiallyStaleRoutePks {
		if !routePksSet[routePk] {
			staleRoutePks = append(staleRoutePks, routePk)
		}
	}

	var oldServiceMapTrips []servicemaps.Trip
	for _, trip := range existingTrips {
		var stopPks []int64
		for _, stopTime := range trip.StopTimes {
			stopPks = append(stopPks, stopTime.StopPk)
		}
		oldServiceMapTrips = append(oldServiceMapTrips, servicemaps.Trip{
			RoutePk:     trip.RoutePk,
			DirectionID: trip.DirectionID,
			StopPks:     stopPks,
		})
	}

	if err := servicemaps.UpdateRealtimeMaps(ctx, updateCtx.Querier, servicemaps.UpdateRealtimeMapsArgs{
		SystemPk:      updateCtx.SystemPk,
		OldTrips:      oldServiceMapTrips,
		NewTrips:      serviceMapTrips,
		StaleRoutePks: staleRoutePks,
	}); err != nil {
		return err
	}
	return nil
}

func stopIDsInTrips(trips []gtfs.Trip) []string {
	set := map[string]bool{}
	for i := range trips {
		for j := range trips[i].StopTimeUpdates {
			stopID := trips[i].StopTimeUpdates[j].StopID
			if stopID == nil {
				continue
			}
			set[*stopID] = true
		}
	}
	var stopIDs []string
	for stopID := range set {
		stopIDs = append(stopIDs, stopID)
	}
	return stopIDs
}

func routeIDsInTrips(trips []gtfs.Trip) []string {
	set := map[string]bool{}
	for i := range trips {
		set[trips[i].ID.RouteID] = true
	}
	var routeIDs []string
	for routeID := range set {
		routeIDs = append(routeIDs, routeID)
	}
	return routeIDs
}

func populateStopSequences(trip *gtfs.Trip, current *dbwrappers.TripForUpdate, stopIDToPk map[string]int64) {
	stopPkToCurrentSequence := map[int64]int64{}
	if current != nil {
		for _, stopTime := range current.StopTimes {
			if _, ok := stopPkToCurrentSequence[stopTime.StopPk]; ok {
				// The trip does not have unique stops. In this case matching on existing stop times by stop ID
				// won't work.
				stopPkToCurrentSequence = map[int64]int64{}
				break
			}
			stopPkToCurrentSequence[stopTime.StopPk] = int64(stopTime.StopSequence)
		}
	}

	lastSequence := int64(-1)
	for i, stopTime := range trip.StopTimeUpdates {
		if stopTime.StopID == nil {
			continue
		}
		stopPk, ok := stopIDToPk[*stopTime.StopID]
		if !ok {
			continue
		}
		// If the stop sequence from the feed is valid, we use that.
		if stopTime.StopSequence != nil && lastSequence < int64(*stopTime.StopSequence) {
			lastSequence = int64(*stopTime.StopSequence)
			continue
		}
		currentSeq, ok := stopPkToCurrentSequence[stopPk]
		if !ok || currentSeq <= lastSequence {
			// If the stop sequence is invalid or this is a new stop, use an incrementing strategy.
			currentSeq = lastSequence + 1
		}
		lastSequence = currentSeq
		newSequence := uint32(currentSeq)
		trip.StopTimeUpdates[i].StopSequence = &newSequence
	}
}
