// Package realtime contains the code for updating the database from a GTFS realtime feed.
package realtime

import (
	"context"
	"crypto/md5"
	"encoding/json"
	"fmt"
	"math"
	"time"

	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jamespfennell/gtfs"
	"github.com/jamespfennell/transiter/internal/convert"
	"github.com/jamespfennell/transiter/internal/db/dbwrappers"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/servicemaps"
	"github.com/jamespfennell/transiter/internal/update/common"
)

func Parse(content []byte, opts *api.GtfsRealtimeOptions) (*gtfs.Realtime, error) {
	ext, err := convert.GtfsRealtimeExtension(opts)
	if err != nil {
		return nil, err
	}
	return gtfs.ParseRealtime(content, &gtfs.ParseRealtimeOptions{
		Extension: ext,
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
	stopHeadsignMatcher, err := NewStopHeadsignMatcher(ctx, updateCtx.Querier, stopIDToPk, trips)
	if err != nil {
		return err
	}
	routeIDToPk, err := dbwrappers.MapRouteIDToPkInSystem(ctx, updateCtx.Querier, updateCtx.SystemPk, routeIDsInTrips(trips))
	if err != nil {
		return err
	}
	existingTrips, err := dbwrappers.ListTripsForUpdate(ctx, updateCtx.Querier, mapValues(routeIDToPk))
	if err != nil {
		return err
	}

	stagedUpdates := newStagedUpdates(trips)
	seenUIDs := map[dbwrappers.TripUID]bool{}
	tripUIDToPk := map[dbwrappers.TripUID]int64{}
	tripUIDToTrip := map[dbwrappers.TripUID]*gtfs.Trip{}
	for i := range trips {
		trip := &trips[i]
		routePk, ok := routeIDToPk[trip.ID.RouteID]
		if !ok {
			continue
		}
		// We need to guard against duplicate trip UIDs. If we try to insert two trips with
		// the same UID then the whole update will fail with a unique constraint violation.
		uid := dbwrappers.TripUID{RoutePk: routePk, ID: trip.ID.ID}
		if seenUIDs[uid] {
			continue
		}
		seenUIDs[uid] = true

		// We calculate a hash of the GTFS data to see if we can skip updating the stop times.
		// Skipping these stop times is a fairly significant optimization.
		var gtfsHash string
		{
			trip := *trip
			trip.Vehicle = nil
			var err error
			gtfsHash, err = common.HashValue(trip)
			if err != nil {
				return err
			}
		}
		var tripPk int64
		if existingTrip, ok := existingTrips[uid]; ok {
			// Even if the data is the same, we update the trip to update the source pk.
			stagedUpdates.updateTrips = append(stagedUpdates.updateTrips, db.UpdateTripParams{
				Pk:          existingTrip.Pk,
				SourcePk:    updateCtx.UpdatePk,
				DirectionID: convert.DirectionID(trip.ID.DirectionID),
				//StartedAt:    trip.ID.StartDate, // TODO: also the start time?
				GtfsHash: gtfsHash,
			})
			if existingTrip.GtfsHash == gtfsHash {
				continue
			}
			tripPk = existingTrip.Pk
		} else {
			var err error
			// We need the newly generated primary key from inserting a new trip, and there's so
			// simple way to do this in a batched approach. So we just issue one query per trip.
			// This code path is only run the first time a trip is seen in a feed, so it's not too
			// bad to do this.
			tripPk, err = updateCtx.Querier.InsertTrip(ctx, db.InsertTripParams{
				ID:          trip.ID.ID,
				RoutePk:     routePk,
				SourcePk:    updateCtx.UpdatePk,
				DirectionID: convert.DirectionID(trip.ID.DirectionID),
				//StartedAt:    trip.ID.StartDate, // TODO: also the start time?
				GtfsHash: gtfsHash,
			})
			if err != nil {
				return err
			}
		}
		tripUIDToPk[uid] = tripPk
		tripUIDToTrip[uid] = trip
	}

	// Next we update the stop times. Note that the tripUIDToPk map only contains trips whose
	// data has changed, so the following logic doesn't run for unchanged trips essentially.
	existingStopTimes, err := dbwrappers.ListStopTimesForUpdate(ctx, updateCtx.Querier, tripUIDToPk)
	if err != nil {
		return err
	}
	routePksWithPathChanges := map[int64]bool{}
	for uid, trip := range tripUIDToTrip {
		if pathChanged := calculateStopTimeChanges(ctx, updateCtx, updateStopTimesInDBArgs{
			tripPk:              tripUIDToPk[uid],
			trip:                trip,
			existingStopTimes:   existingStopTimes[uid],
			stopHeadsignMatcher: stopHeadsignMatcher,
			stopIDToPk:          stopIDToPk,
		}, &stagedUpdates); pathChanged {
			routePksWithPathChanges[uid.RoutePk] = true
		}
	}

	if err := stagedUpdates.run(ctx, updateCtx); err != nil {
		return err
	}

	routePksWithDeletedTrips, err := updateCtx.Querier.DeleteStaleTrips(ctx, db.DeleteStaleTripsParams{
		FeedPk:   updateCtx.FeedPk,
		UpdatePk: updateCtx.UpdatePk,
	})
	if err != nil {
		return err
	}
	for _, routePk := range routePksWithDeletedTrips {
		routePksWithPathChanges[routePk] = true
	}

	if err := servicemaps.UpdateRealtimeMaps(ctx, updateCtx.Querier, updateCtx.SystemPk, mapKeys(routePksWithPathChanges)); err != nil {
		return err
	}
	return nil
}

type stagedUpdates struct {
	updateTrips       []db.UpdateTripParams
	deleteStopTimes   []int64
	insertStopTimes   []db.InsertTripStopTimeParams
	markStopTimesPast []db.MarkTripStopTimesPastParams
}

func newStagedUpdates(trips []gtfs.Trip) stagedUpdates {
	nTrips := len(trips)
	var nStopTimes int
	for i := range trips {
		nStopTimes += len(trips[i].StopTimeUpdates)
	}
	return stagedUpdates{
		updateTrips:       make([]db.UpdateTripParams, 0, nTrips),
		deleteStopTimes:   make([]int64, 0, nStopTimes),
		insertStopTimes:   make([]db.InsertTripStopTimeParams, 0, nStopTimes),
		markStopTimesPast: make([]db.MarkTripStopTimesPastParams, 0, nTrips),
	}
}

func (s *stagedUpdates) run(ctx context.Context, updateCtx common.UpdateContext) error {
	if err := dbwrappers.BatchUpdate(ctx, updateCtx.Querier.UpdateTrip, s.updateTrips); err != nil {
		return err
	}
	if err := updateCtx.Querier.DeleteTripStopTimes(ctx, s.deleteStopTimes); err != nil {
		return err
	}
	if _, err := updateCtx.Querier.InsertTripStopTime(ctx, s.insertStopTimes); err != nil {
		return err
	}
	if err := dbwrappers.BatchUpdate(ctx, updateCtx.Querier.MarkTripStopTimesPast, s.markStopTimesPast); err != nil {
		return err
	}
	*s = stagedUpdates{}
	return nil
}

type updateStopTimesInDBArgs struct {
	stopHeadsignMatcher *StopHeadsignMatcher
	tripPk              int64
	trip                *gtfs.Trip
	existingStopTimes   []db.ListTripStopTimesForUpdateRow
	stopIDToPk          map[string]int64
}

// calculateStopTimeChanges updates the trip stop times in the database. The boolean return value indicates
// whether the path of the trip has changed.
func calculateStopTimeChanges(ctx context.Context, updateCtx common.UpdateContext, args updateStopTimesInDBArgs, t *stagedUpdates) bool {
	// Check to see if stop sequences should be reassigned by transiter (even if present in GTFS).
	reassignStopSequences := updateCtx.FeedConfig.GetGtfsRealtimeOptions().GetReassignStopSequences()

	populateStopSequences(args.trip, args.existingStopTimes, args.stopIDToPk, reassignStopSequences)
	stopSequenceToStopTimePk := map[int32]db.ListTripStopTimesForUpdateRow{}
	for _, stopTime := range args.existingStopTimes {
		stopSequenceToStopTimePk[stopTime.StopSequence] = stopTime
	}
	var pathChanged bool
	for _, stopTime := range args.trip.StopTimeUpdates {
		if stopTime.StopID == nil {
			continue
		}
		stopPk, ok := args.stopIDToPk[*stopTime.StopID]
		if !ok {
			continue
		}
		if stopTime.StopSequence == nil {
			continue
		}
		headsign := args.stopHeadsignMatcher.Match(stopPk, stopTime.NyctTrack)
		existingStopTime, ok := stopSequenceToStopTimePk[int32(*stopTime.StopSequence)]
		if ok {
			t.deleteStopTimes = append(t.deleteStopTimes, existingStopTime.Pk)
			delete(stopSequenceToStopTimePk, int32(*stopTime.StopSequence))
			if stopPk != existingStopTime.Pk {
				pathChanged = true
			}
		} else {
			pathChanged = true
		}
		t.insertStopTimes = append(t.insertStopTimes, db.InsertTripStopTimeParams{
			TripPk:               args.tripPk,
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
			Past:                 false,
		})
	}

	currentStopSequence := int32(math.MaxInt32)
	for _, stopTime := range args.trip.StopTimeUpdates {
		if stopTime.StopSequence != nil {
			currentStopSequence = int32(*stopTime.StopSequence)
			break
		}
	}
	t.markStopTimesPast = append(t.markStopTimesPast, db.MarkTripStopTimesPastParams{
		TripPk:              args.tripPk,
		CurrentStopSequence: currentStopSequence,
	})

	for stopSequence, stopTime := range stopSequenceToStopTimePk {
		if stopSequence < currentStopSequence {
			continue
		}
		t.deleteStopTimes = append(t.deleteStopTimes, stopTime.Pk)
		pathChanged = true
	}

	return pathChanged
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

func populateStopSequences(trip *gtfs.Trip, existingStopTimes []db.ListTripStopTimesForUpdateRow, stopIDToPk map[string]int64, reassignStopSequences bool) {
	useFeedStopSequences := !reassignStopSequences
	stopPkToCurrentSequence := map[int64]int64{}
	for _, stopTime := range existingStopTimes {
		if _, ok := stopPkToCurrentSequence[stopTime.StopPk]; ok {
			// The trip does not have unique stops. In this case matching on existing stop times by stop ID
			// won't work.
			stopPkToCurrentSequence = map[int64]int64{}
			break
		}
		stopPkToCurrentSequence[stopTime.StopPk] = int64(stopTime.StopSequence)
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
		// If using feed stop sequences and the stop sequence from the feed is valid, we use that.
		if useFeedStopSequences && stopTime.StopSequence != nil && lastSequence < int64(*stopTime.StopSequence) {
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
		agencyIDToPk, err = dbwrappers.MapAgencyIDToPk(ctx, updateCtx.Querier, updateCtx.SystemPk)
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

func convertOptionalTime(in *time.Time) pgtype.Timestamptz {
	if in == nil {
		return pgtype.Timestamptz{}
	}
	return pgtype.Timestamptz{
		Valid: true,
		Time:  *in,
	}
}

func mapValues[T comparable, V any](in map[T]V) []V {
	var out []V
	for _, v := range in {
		out = append(out, v)
	}
	return out
}

func mapKeys[T comparable, V any](in map[T]V) []T {
	var out []T
	for t := range in {
		out = append(out, t)
	}
	return out
}
