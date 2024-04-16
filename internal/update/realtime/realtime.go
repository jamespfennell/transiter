// Package realtime contains the code for updating the database from a GTFS realtime feed.
package realtime

import (
	"context"
	"crypto/md5"
	"crypto/sha256"
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
	if err := updateVehicles(ctx, updateCtx, data.Vehicles); err != nil {
		return err
	}
	return nil
}

func updateTrips(ctx context.Context, updateCtx common.UpdateContext, trips []gtfs.Trip) error {
	var tripEntitiesInFeed []gtfs.Trip
	for _, trip := range trips {
		// Only insert trips that are in the feed.
		if trip.IsEntityInMessage {
			tripEntitiesInFeed = append(tripEntitiesInFeed, trip)
		}
	}

	stopIDToPk, err := dbwrappers.MapStopIDToPkInSystem(ctx, updateCtx.Querier, updateCtx.SystemPk, stopIDsInTrips(tripEntitiesInFeed))
	if err != nil {
		return err
	}
	stopHeadsignMatcher, err := NewStopHeadsignMatcher(ctx, updateCtx.Querier, stopIDToPk, tripEntitiesInFeed)
	if err != nil {
		return err
	}

	var routePks []int64

	// Collect all trips without a route ID in update
	var tripIDsWithoutRouteIDs []string
	for _, trip := range tripEntitiesInFeed {
		if trip.ID.RouteID == "" {
			tripIDsWithoutRouteIDs = append(tripIDsWithoutRouteIDs, trip.ID.ID)
		}
	}

	// Try to get route IDs for trips without route IDs in update from static data
	var tripIDToRoutePk map[string]int64
	if len(tripIDsWithoutRouteIDs) > 0 {
		tripIDToRoutePk, err = dbwrappers.MapScheduledTripIDToRoutePkInSystem(ctx, updateCtx.Querier, updateCtx.SystemPk, tripIDsWithoutRouteIDs)
		if err != nil {
			return err
		}
		routePks = common.MapValues(tripIDToRoutePk)
	}

	// For all trips with provided route IDs, get the corresponding route Pks
	var routeIDToPk map[string]int64
	routeIDsInTrips := routeIDsInTrips(tripEntitiesInFeed)
	if len(routeIDsInTrips) > 0 {
		routeIDToPk, err = dbwrappers.MapRouteIDToPkInSystem(ctx, updateCtx.Querier, updateCtx.SystemPk, routeIDsInTrips)
		if err != nil {
			return err
		}
		routePks = append(routePks, common.MapValues(routeIDToPk)...)
	}

	existingTrips, err := dbwrappers.ListTripsForUpdate(ctx, updateCtx.Querier, updateCtx.SystemPk, routePks)
	if err != nil {
		return err
	}

	stagedUpdates := newStagedUpdates(tripEntitiesInFeed)
	seenUIDs := map[dbwrappers.TripUID]bool{}
	tripUIDToPk := map[dbwrappers.TripUID]int64{}
	tripUIDToTrip := map[dbwrappers.TripUID]*gtfs.Trip{}
	activeTripPks := []int64{}
	for i := range tripEntitiesInFeed {
		trip := &tripEntitiesInFeed[i]

		var routePk int64
		var routeOk bool
		// If empty route ID, try to infer from static data.
		if trip.ID.RouteID == "" {
			routePk, routeOk = tripIDToRoutePk[trip.ID.ID]
		} else {
			routePk, routeOk = routeIDToPk[trip.ID.RouteID]
		}
		if !routeOk {
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
		h := sha256.New()
		var gtfsHash string
		{
			h.Reset()
			trip.Hash(h)
			if trip.Vehicle != nil {
				trip.Vehicle.Hash(h)
			}
			gtfsHash = fmt.Sprintf("%x", h.Sum(nil))
		}
		var tripPk int64
		if existingTrip, ok := existingTrips[uid]; ok {
			if existingTrip.GtfsHash == gtfsHash && existingTrip.FeedPk == updateCtx.FeedPk {
				activeTripPks = append(activeTripPks, existingTrip.Pk)
				continue
			}
			stagedUpdates.updateTrips = append(stagedUpdates.updateTrips, db.UpdateTripParams{
				Pk:          existingTrip.Pk,
				FeedPk:      updateCtx.FeedPk,
				DirectionID: convert.DirectionID(trip.ID.DirectionID),
				//StartedAt:    trip.ID.StartDate, // TODO: also the start time?
				GtfsHash: gtfsHash,
			})
			tripPk = existingTrip.Pk
		} else {
			var err error
			// TODO: we should batch this
			tripPk, err = updateCtx.Querier.InsertTrip(ctx, db.InsertTripParams{
				ID:          trip.ID.ID,
				RoutePk:     routePk,
				FeedPk:      updateCtx.FeedPk,
				DirectionID: convert.DirectionID(trip.ID.DirectionID),
				//StartedAt:    trip.ID.StartDate, // TODO: also the start time?
				GtfsHash: gtfsHash,
			})
			if err != nil {
				return err
			}
		}
		activeTripPks = append(activeTripPks, tripPk)
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
		FeedPk:         updateCtx.FeedPk,
		UpdatedTripPks: activeTripPks,
	})
	if err != nil {
		return err
	}
	for _, routePk := range routePksWithDeletedTrips {
		routePksWithPathChanges[routePk] = true
	}

	if err := servicemaps.UpdateRealtimeMaps(ctx, updateCtx.Querier, updateCtx.Logger, updateCtx.SystemPk, common.MapKeys(routePksWithPathChanges)); err != nil {
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
		if trips[i].ID.RouteID == "" {
			continue
		}
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
		if _, duplicateAlert := idToHash[alert.ID]; duplicateAlert {
			updateCtx.Logger.DebugCtx(ctx, fmt.Sprintf("skipping alert with duplicate ID %q", alert.ID))
			continue
		}
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
	newPks, err := insertAlerts(ctx, updateCtx, alertsToInsert, idToHash)
	if err != nil {
		return err
	}
	if err := updateCtx.Querier.DeleteStaleAlerts(ctx, db.DeleteStaleAlertsParams{
		FeedPk:          updateCtx.FeedPk,
		UpdatedAlertPks: concatenate(unchangedAlertPks, newPks),
	}); err != nil {
		return err
	}
	return nil
}

func concatenate[V any](in1, in2 []V) []V {
	out := make([]V, 0, len(in1)+len(in2))
	out = append(out, in1...)
	out = append(out, in2...)
	return out
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

func insertAlerts(ctx context.Context, updateCtx common.UpdateContext, alerts []*gtfs.Alert, idToHash map[string]string) ([]int64, error) {
	// There are generally few agencies, so if an agency is referenced in informed entities we just retrieve all of them.
	// This saves us from writing a specific SQL query for this case.
	var agencyReferenced bool
	var routeIDs []string
	var stopIDs []string
	var tripIDs []string
	var newAlertPks []int64
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
			if informedEntity.TripID != nil && informedEntity.TripID.ID != "" {
				tripIDs = append(tripIDs, informedEntity.TripID.ID)
			}
		}
	}
	agencyIDToPk := map[string]int64{}
	if agencyReferenced {
		var err error
		agencyIDToPk, err = dbwrappers.MapAgencyIDToPk(ctx, updateCtx.Querier, updateCtx.SystemPk)
		if err != nil {
			return nil, err
		}
	}
	routeIDToPk, err := dbwrappers.MapRouteIDToPkInSystem(ctx, updateCtx.Querier, updateCtx.SystemPk, routeIDs)
	if err != nil {
		return nil, err
	}
	stopIDToPk, err := dbwrappers.MapStopIDToPkInSystem(ctx, updateCtx.Querier, updateCtx.SystemPk, stopIDs)
	if err != nil {
		return nil, err
	}
	tripIDToPk, err := dbwrappers.MapTripIDToPkInSystem(ctx, updateCtx.Querier, updateCtx.SystemPk, tripIDs)
	if err != nil {
		return nil, err
	}
	scheduledTripIDToPk, err := dbwrappers.MapScheduledTripIDToPkInSystem(ctx, updateCtx.Querier, updateCtx.SystemPk, tripIDs)
	if err != nil {
		return nil, err
	}

	for _, alert := range alerts {
		pk, err := updateCtx.Querier.InsertAlert(ctx, db.InsertAlertParams{
			ID:          alert.ID,
			SystemPk:    updateCtx.SystemPk,
			FeedPk:      updateCtx.FeedPk,
			Cause:       alert.Cause.String(),
			Effect:      alert.Effect.String(),
			Header:      convertAlertText(alert.Header),
			Description: convertAlertText(alert.Description),
			Url:         convertAlertText(alert.URL),
			Hash:        idToHash[alert.ID],
		})
		if err != nil {
			return nil, err
		}
		newAlertPks = append(newAlertPks, pk)
		for _, informedEntity := range alert.InformedEntities {
			if informedEntity.AgencyID != nil {
				if agencyPk, ok := agencyIDToPk[*informedEntity.AgencyID]; ok {
					if err := updateCtx.Querier.InsertAlertAgency(ctx, db.InsertAlertAgencyParams{
						AlertPk:  pk,
						AgencyPk: agencyPk,
					}); err != nil {
						return nil, err
					}
				}
			}
			if informedEntity.RouteID != nil {
				if routePk, ok := routeIDToPk[*informedEntity.RouteID]; ok {
					if err := updateCtx.Querier.InsertAlertRoute(ctx, db.InsertAlertRouteParams{
						AlertPk: pk,
						RoutePk: routePk,
					}); err != nil {
						return nil, err
					}
				}
			}
			if informedEntity.StopID != nil {
				if stopPk, ok := stopIDToPk[*informedEntity.StopID]; ok {
					if err := updateCtx.Querier.InsertAlertStop(ctx, db.InsertAlertStopParams{
						AlertPk: pk,
						StopPk:  stopPk,
					}); err != nil {
						return nil, err
					}
				}
			}
			if informedEntity.TripID != nil {
				tripID := informedEntity.TripID.ID
				var tripPkOrNil *int64 = nil
				if tripPk, ok := tripIDToPk[tripID]; ok {
					tripPkOrNil = &tripPk
				}
				var scheduledTripPkOrNil *int64 = nil
				if scheduledTripPk, ok := scheduledTripIDToPk[tripID]; ok {
					scheduledTripPkOrNil = &scheduledTripPk
				}
				if tripPkOrNil != nil || scheduledTripPkOrNil != nil {
					err := updateCtx.Querier.InsertAlertTrip(ctx, db.InsertAlertTripParams{
						AlertPk:         pk,
						TripPk:          convert.NullInt64(tripPkOrNil),
						ScheduledTripPk: convert.NullInt64(scheduledTripPkOrNil),
					})
					if err != nil {
						return nil, err
					}
				}
			}
			if informedEntity.RouteType != gtfs.RouteType_Unknown {
				if err := updateCtx.Querier.InsertAlertRouteType(ctx, db.InsertAlertRouteTypeParams{
					AlertPk:   pk,
					RouteType: informedEntity.RouteType.String(),
				}); err != nil {
					return nil, err
				}
			}
		}
		for _, activePeriod := range alert.ActivePeriods {
			if err := updateCtx.Querier.InsertAlertActivePeriod(ctx, db.InsertAlertActivePeriodParams{
				AlertPk:  pk,
				StartsAt: convertOptionalTime(activePeriod.StartsAt),
				EndsAt:   convertOptionalTime(activePeriod.EndsAt),
			}); err != nil {
				return nil, err
			}
		}
	}
	return newAlertPks, nil
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

func updateVehicles(ctx context.Context, updateCtx common.UpdateContext, vehicles []gtfs.Vehicle) error {
	var validVehicleEntities []gtfs.Vehicle
	for _, vehicle := range vehicles {
		if !vehicle.IsEntityInMessage {
			continue
		}
		// Note: We can insert a vehicle with no ID if it has an associated
		// trip, per the GTFS-realtime spec. For now, we'll just skip them.
		if vehicle.GetID().ID == "" {
			updateCtx.Logger.DebugCtx(ctx, "Vehicle has no ID or empty ID")
			continue
		}
		validVehicleEntities = append(validVehicleEntities, vehicle)
	}

	if len(validVehicleEntities) == 0 {
		return updateCtx.Querier.DeleteVehicles(ctx, db.DeleteVehiclesParams{
			FeedPk: updateCtx.FeedPk,
		})
	}

	var vehicleIDs []string
	var stopIDs []string
	var tripIDs []string
	for i := range validVehicleEntities {
		vehicle := &validVehicleEntities[i]
		vehicleIDs = append(vehicleIDs, vehicle.ID.ID)
		if vehicle.StopID != nil {
			stopIDs = append(stopIDs, *vehicle.StopID)
		}
		if vehicle.GetTrip().ID.ID != "" {
			tripIDs = append(tripIDs, vehicle.GetTrip().ID.ID)
		}
	}

	// This statement also acquires a lock on the rows in the trip table associated
	// with vehicles being inserted/updated.
	tripIDToPk, err := dbwrappers.MapTripIDToPkInSystem(ctx, updateCtx.Querier, updateCtx.SystemPk, tripIDs)
	if err != nil {
		return err
	}

	tripPkToVehicleID, err := dbwrappers.MapTripPkToVehicleID(ctx, updateCtx.Querier, updateCtx.SystemPk, vehicleIDs)
	if err != nil {
		return err
	}

	// This statement does not currently lock the rows in the stop table associated
	// with vehicles being inserted/updated. However, changes to the stop table should
	// be rare, so conflicts should not be a major issue.
	stopIDToPk, err := dbwrappers.MapStopIDToPkInSystem(ctx, updateCtx.Querier, updateCtx.SystemPk, stopIDs)
	if err != nil {
		return err
	}

	err = updateCtx.Querier.DeleteVehicles(ctx, db.DeleteVehiclesParams{
		SystemPk:   updateCtx.SystemPk,
		FeedPk:     updateCtx.FeedPk,
		VehicleIds: vehicleIDs,
		TripPks:    common.MapValues(tripIDToPk),
	})
	if err != nil {
		return err
	}

	insertedVehicleIDs := map[string]bool{}
	insertedTripIDs := map[string]bool{}
	var insertVehicleParams []db.InsertVehicleParams
	for _, vehicle := range validVehicleEntities {
		if _, ok := insertedVehicleIDs[vehicle.ID.ID]; ok {
			updateCtx.Logger.DebugCtx(ctx, "Duplicate vehicle ID in same update", vehicle.ID.ID)
			continue
		}
		insertedVehicleIDs[vehicle.ID.ID] = true

		if _, ok := insertedTripIDs[vehicle.GetTrip().ID.ID]; ok {
			updateCtx.Logger.DebugCtx(ctx, "Duplicate trip ID in same update", vehicle.GetTrip().ID.ID)
			continue
		}

		var tripPkOrNil *int64 = nil
		if vehicle.GetTrip().ID.ID != "" {
			// Check that the trip ID is not associated with multiple vehicle IDs.
			if tripPk, ok := tripIDToPk[vehicle.GetTrip().ID.ID]; ok {
				if vehicleIDForTripPk, ok := tripPkToVehicleID[tripPk]; ok {
					if vehicleIDForTripPk != vehicle.ID.ID {
						updateCtx.Logger.DebugCtx(ctx, "Trip ID has multiple vehicle IDs", vehicle.GetTrip().ID.ID)
						continue
					}
				}
			} else {
				// If trip ID points to a trip that doesn't exist, skip it.
				updateCtx.Logger.DebugCtx(ctx, "Trip ID not found", vehicle.GetTrip().ID.ID)
				continue
			}

			tripPkOrNil = ptr(tripIDToPk[vehicle.GetTrip().ID.ID])
			insertedTripIDs[vehicle.GetTrip().ID.ID] = true
		}

		var stopPkOrNil *int64 = nil
		if vehicle.StopID != nil {
			if stopID, ok := stopIDToPk[*vehicle.StopID]; ok {
				stopPkOrNil = &stopID
			}
		}

		var latitude, longitude, bearing, speed *float32 = nil, nil, nil, nil
		var odometer *float64 = nil
		if vehicle.Position != nil {
			latitude = vehicle.Position.Latitude
			longitude = vehicle.Position.Longitude
			bearing = vehicle.Position.Bearing
			odometer = vehicle.Position.Odometer
			speed = vehicle.Position.Speed
		}

		insertVehicleParams = append(insertVehicleParams, db.InsertVehicleParams{
			ID:                  convert.NullIfEmptyString(vehicle.ID.ID),
			SystemPk:            updateCtx.SystemPk,
			TripPk:              convert.NullInt64(tripPkOrNil),
			FeedPk:              updateCtx.FeedPk,
			CurrentStopPk:       convert.NullInt64(stopPkOrNil),
			Label:               convert.NullIfEmptyString(vehicle.ID.Label),
			LicensePlate:        convert.NullIfEmptyString(vehicle.ID.LicensePlate),
			CurrentStatus:       convert.NullVehicleCurrentStatus(vehicle.CurrentStatus),
			Latitude:            convert.Gps(latitude),
			Longitude:           convert.Gps(longitude),
			Bearing:             convert.NullFloat32(bearing),
			Odometer:            convert.NullFloat64(odometer),
			Speed:               convert.NullFloat32(speed),
			CongestionLevel:     convert.CongestionLevel(vehicle.CongestionLevel),
			UpdatedAt:           convert.NullTime(vehicle.Timestamp),
			CurrentStopSequence: convert.NullUInt32ToSigned(vehicle.CurrentStopSequence),
			OccupancyStatus:     convert.NullOccupancyStatus(vehicle.OccupancyStatus),
			OccupancyPercentage: convert.NullUInt32ToSigned(vehicle.OccupancyPercentage),
		})
	}

	_, err = updateCtx.Querier.InsertVehicle(ctx, insertVehicleParams)
	return err
}

func ptr[T any](t T) *T {
	return &t
}
