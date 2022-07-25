// Package realtime contains the code for updating the database from a GTFS realtime feed.
package realtime

import (
	"context"
	"crypto/md5"
	"database/sql"
	"encoding/json"
	"fmt"
	"math"
	"time"

	"github.com/jamespfennell/gtfs"
	"github.com/jamespfennell/gtfs/extensions"
	"github.com/jamespfennell/gtfs/extensions/nyctalerts"
	"github.com/jamespfennell/gtfs/extensions/nycttrips"
	"github.com/jamespfennell/transiter/config"
	"github.com/jamespfennell/transiter/internal/convert"
	"github.com/jamespfennell/transiter/internal/db/dbwrappers"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/servicemaps"
	"github.com/jamespfennell/transiter/internal/update/common"
)

func Parse(content []byte, opts config.GtfsRealtimeOptions) (*gtfs.Realtime, error) {
	var extension extensions.Extension
	switch opts.Extension {
	case config.NyctTrips:
		var extensionOpts nycttrips.ExtensionOpts
		if opts.NyctTripsOptions != nil {
			extensionOpts = *opts.NyctTripsOptions
		}
		extension = nycttrips.Extension(extensionOpts)
	case config.NyctAlerts:
		var extensionOpts nyctalerts.ExtensionOpts
		if opts.NyctAlertsOptions != nil {
			extensionOpts = *opts.NyctAlertsOptions
		}
		extension = nyctalerts.Extension(extensionOpts)
	}
	return gtfs.ParseRealtime(content, &gtfs.ParseRealtimeOptions{
		Extension: extension,
	})
}

func Update(ctx context.Context, updateCtx common.UpdateContext, data *gtfs.Realtime) error {
	if err := updateTrips(ctx, updateCtx, data.Trips); err != nil {
		return err
	}
	if err := updateAlerts(ctx, updateCtx, data.Alerts); err != nil {
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

	stopHeadsignMatcher, err := NewStopHeadsignMatcher(ctx, updateCtx.Querier, stopIDToPk, trips)
	if err != nil {
		return err
	}

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
			headsign := stopHeadsignMatcher.Match(stopPk, stopTime.NyctTrack)
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
					Headsign:             convert.NullString(headsign),
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
					Headsign:             convert.NullString(headsign),
				}); err != nil {
					return err
				}
			}
		}
		serviceMapTrips = append(serviceMapTrips, serviceMapTrip)

		currentStopSequence := int32(math.MaxInt32)
		for _, stopTime := range trip.StopTimeUpdates {
			if stopTime.StopSequence != nil {
				currentStopSequence = int32(*stopTime.StopSequence)
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

type StopHeadsignMatcher struct {
	rules map[int64][]db.StopHeadsignRule
}

func NewStopHeadsignMatcher(ctx context.Context, querier db.Querier, stopIDToPk map[string]int64, trips []gtfs.Trip) (*StopHeadsignMatcher, error) {
	stopPksSet := map[int64]bool{}
	for i := range trips {
		for j := range trips[i].StopTimeUpdates {
			stopID := trips[i].StopTimeUpdates[j].StopID
			if stopID == nil {
				continue
			}
			stopPk, ok := stopIDToPk[*stopID]
			if !ok {
				continue
			}
			stopPksSet[stopPk] = true
		}
	}
	var stopPks []int64
	for stopPk := range stopPksSet {
		stopPks = append(stopPks, stopPk)
	}
	rows, err := querier.ListStopHeadsignRulesForStops(ctx, stopPks)
	if err != nil {
		return nil, err
	}
	rules := map[int64][]db.StopHeadsignRule{}
	for _, row := range rows {
		rules[row.StopPk] = append(rules[row.StopPk], row)
	}
	return &StopHeadsignMatcher{rules: rules}, nil
}

func (m *StopHeadsignMatcher) Match(stopPk int64, track *string) *string {
	for _, rule := range m.rules[stopPk] {
		if track != nil &&
			rule.Track.Valid &&
			*track != rule.Track.String {
			continue
		}
		return &rule.Headsign
	}
	return nil
}

func updateAlerts(ctx context.Context, updateCtx common.UpdateContext, alerts []gtfs.Alert) error {
	idToPkAndHash, err := mapAlertIDToPkAndHash(ctx, updateCtx, alerts)
	if err != nil {
		return err
	}
	idToHash := map[string]string{}
	var unchangedAlertPks []int64
	var updatedAlertPks []int64
	var alertsToInsert []*gtfs.Alert
	for i := range alerts {
		alert := &alerts[i]
		idToHash[alert.ID] = calculateHash(alert)
		if pkAndHash, alreadyExists := idToPkAndHash[alert.ID]; alreadyExists {
			if idToHash[alert.ID] == pkAndHash.Hash {
				unchangedAlertPks = append(unchangedAlertPks, pkAndHash.Pk)
				continue
			}
			updatedAlertPks = append(updatedAlertPks, pkAndHash.Pk)
		}
		alertsToInsert = append(alertsToInsert, alert)
	}
	if err := updateCtx.Querier.DeleteAlerts(ctx, updatedAlertPks); err != nil {
		return err
	}
	if err := insertAlerts(ctx, updateCtx, alertsToInsert, idToHash); err != nil {
		return err
	}
	if err := updateCtx.Querier.MarkAlertsFresh(ctx, db.MarkAlertsFreshParams{
		AlertPks: unchangedAlertPks,
		UpdatePk: updateCtx.UpdatePk,
	}); err != nil {
		return err
	}
	if err := updateCtx.Querier.DeleteStaleAlerts(ctx, db.DeleteStaleAlertsParams{
		FeedPk:   updateCtx.FeedPk,
		UpdatePk: updateCtx.UpdatePk,
	}); err != nil {
		return err
	}
	return nil
}

type pkAndHash struct {
	Pk   int64
	Hash string
}

func mapAlertIDToPkAndHash(ctx context.Context, updateCtx common.UpdateContext, alerts []gtfs.Alert) (map[string]pkAndHash, error) {
	var ids []string
	for i := range alerts {
		ids = append(ids, alerts[i].ID)
	}
	rows, err := updateCtx.Querier.ListAlertPksAndHashes(ctx, db.ListAlertPksAndHashesParams{
		AlertIds: ids,
		SystemPk: updateCtx.SystemPk,
	})
	if err != nil {
		return nil, err
	}
	m := map[string]pkAndHash{}
	for _, row := range rows {
		m[row.ID] = pkAndHash{
			Pk:   row.Pk,
			Hash: row.Hash,
		}
	}
	return m, nil
}

func calculateHash(alert *gtfs.Alert) string {
	b, err := json.Marshal(alert)
	if err != nil {
		// This case will probably never happen
		return fmt.Sprintf("error-hash-%s: %s", time.Now(), err)
	}
	return fmt.Sprintf("%x", md5.Sum(b))
}

func insertAlerts(ctx context.Context, updateCtx common.UpdateContext, alerts []*gtfs.Alert, idToHash map[string]string) error {
	// There are generally few agencies, so if an agency is referenced in informed entities we just retrieve all of them.
	// This saves us from writing a specific SQL query for this case.
	var agencyReferenced bool
	var routeIDs []string
	var stopIDs []string
	for _, alert := range alerts {
		for _, informedEntity := range alert.InformedEntities {
			if informedEntity.AgencyID != nil {
				agencyReferenced = true
			}
			if informedEntity.RouteID != nil {
				routeIDs = append(routeIDs, *informedEntity.RouteID)
			}
			if informedEntity.StopID != nil {
				stopIDs = append(stopIDs, *informedEntity.StopID)
			}
		}
	}
	agencyIDToPk := map[string]int64{}
	if agencyReferenced {
		var err error
		agencyIDToPk, err = dbwrappers.MapAgencyIDToPkInSystem(ctx, updateCtx.Querier, updateCtx.SystemPk)
		if err != nil {
			return err
		}
	}
	routeIDToPk, err := dbwrappers.MapRouteIDToPkInSystem(ctx, updateCtx.Querier, updateCtx.SystemPk, routeIDs)
	if err != nil {
		return err
	}
	stopIDToPk, err := dbwrappers.MapStopIDToPkInSystem(ctx, updateCtx.Querier, updateCtx.SystemPk, stopIDs)
	if err != nil {
		return err
	}
	for _, alert := range alerts {
		pk, err := updateCtx.Querier.InsertAlert(ctx, db.InsertAlertParams{
			ID:          alert.ID,
			SystemPk:    updateCtx.SystemPk,
			SourcePk:    updateCtx.UpdatePk,
			Cause:       alert.Cause.String(),
			Effect:      alert.Effect.String(),
			Header:      convertAlertText(alert.Header),
			Description: convertAlertText(alert.Description),
			Url:         convertAlertText(alert.URL),
			Hash:        idToHash[alert.ID],
		})
		if err != nil {
			return err
		}
		for _, informedEntity := range alert.InformedEntities {
			if informedEntity.AgencyID != nil {
				if agencyPk, ok := agencyIDToPk[*informedEntity.AgencyID]; ok {
					if err := updateCtx.Querier.InsertAlertAgency(ctx, db.InsertAlertAgencyParams{
						AlertPk:  pk,
						AgencyPk: agencyPk,
					}); err != nil {
						return err
					}
				}
			}
			if informedEntity.RouteID != nil {
				if routePk, ok := routeIDToPk[*informedEntity.RouteID]; ok {
					if err := updateCtx.Querier.InsertAlertRoute(ctx, db.InsertAlertRouteParams{
						AlertPk: pk,
						RoutePk: routePk,
					}); err != nil {
						return err
					}
				}
			}
			if informedEntity.StopID != nil {
				if stopPk, ok := stopIDToPk[*informedEntity.StopID]; ok {
					if err := updateCtx.Querier.InsertAlertStop(ctx, db.InsertAlertStopParams{
						AlertPk: pk,
						StopPk:  stopPk,
					}); err != nil {
						return err
					}
				}
			}
		}
		for _, activePeriod := range alert.ActivePeriods {
			if err := updateCtx.Querier.InsertAlertActivePeriod(ctx, db.InsertAlertActivePeriodParams{
				AlertPk:  pk,
				StartsAt: convertOptionalTime(activePeriod.StartsAt),
				EndsAt:   convertOptionalTime(activePeriod.EndsAt),
			}); err != nil {
				return err
			}
		}
	}
	return nil
}

func convertAlertText(text []gtfs.AlertText) string {
	b, _ := json.Marshal(text)
	return string(b)
}

func convertOptionalTime(in *time.Time) sql.NullTime {
	if in == nil {
		return sql.NullTime{}
	}
	return sql.NullTime{
		Valid: true,
		Time:  *in,
	}
}
