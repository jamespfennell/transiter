package endpoints

import (
	"context"
	"fmt"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jamespfennell/transiter/internal/convert"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/public/errors"
)

func ListTrips(ctx context.Context, r *Context, req *api.ListTripsRequest) (*api.ListTripsReply, error) {
	system, route, err := getRoute(ctx, r.Querier, req.SystemId, req.RouteId)
	if err != nil {
		return nil, err
	}
	trips, err := r.Querier.ListTrips(ctx, db.ListTripsParams{
		SystemPk: system.Pk,
		RoutePks: []int64{route.Pk},
	})
	if err != nil {
		return nil, err
	}
	apiTrips, err := buildApiTrips(ctx, r, &system, &route, trips)
	if err != nil {
		return nil, err
	}
	return &api.ListTripsReply{
		Trips: apiTrips,
	}, nil
}

func GetTrip(ctx context.Context, r *Context, req *api.GetTripRequest) (*api.Trip, error) {
	system, route, err := getRoute(ctx, r.Querier, req.SystemId, req.RouteId)
	if err != nil {
		return nil, err
	}
	trip, err := r.Querier.GetTrip(ctx, db.GetTripParams{
		SystemPk: system.Pk,
		TripID:   req.TripId,
		RoutePk:  route.Pk,
	})
	if err != nil {
		if err == pgx.ErrNoRows {
			err = errors.NewNotFoundError(fmt.Sprintf("trip %q in route %q in system %q not found",
				req.TripId, req.RouteId, req.SystemId))
		}
		return nil, err
	}
	apiTrips, err := buildApiTrips(ctx, r, &system, &route, []db.ListTripsRow{{
		Pk:              trip.Pk,
		ID:              trip.ID,
		RoutePk:         trip.RoutePk,
		DirectionID:     trip.DirectionID,
		StartedAt:       trip.StartedAt,
		GtfsHash:        trip.GtfsHash,
		FeedPk:          trip.FeedPk,
		VehicleID:       trip.VehicleID,
		VehicleLocation: trip.VehicleLocation,
		ShapeID:         trip.ShapeID,
	}})
	if err != nil {
		return nil, err
	}
	return apiTrips[0], nil
}

func buildApiTrips(ctx context.Context, r *Context, system *db.System, route *db.Route, trips []db.ListTripsRow) ([]*api.Trip, error) {
	var tripPks []int64
	for i := range trips {
		tripPks = append(tripPks, trips[i].Pk)
	}

	alertPreviews, err := buildTripAlertPreviews(ctx, r, system.ID, tripPks)
	if err != nil {
		return nil, err
	}

	var apiTrips []*api.Trip
	for i := range trips {
		trip := &trips[i]
		stopTimes, err := r.Querier.ListStopsTimesForTrip(ctx, trip.Pk)
		if err != nil {
			return nil, err
		}
		reply := &api.Trip{
			Id:          trip.ID,
			DirectionId: trip.DirectionID.Bool,
			StartedAt:   convert.SQLNullTime(trip.StartedAt),
			Route:       r.Reference.Route(route.ID, system.ID, route.Color),
			Shape:       nullShapeReference(r, trip.ShapeID, system.ID),
			Alerts:      alertPreviews[trip.Pk],
		}
		if trip.VehicleID.Valid {
			reply.Vehicle = r.Reference.Vehicle(trip.VehicleID.String, system.ID)
		}
		for _, stopTime := range stopTimes {
			reply.StopTimes = append(reply.StopTimes, &api.StopTime{
				StopSequence: stopTime.StopSequence,
				Track:        convert.SQLNullString(stopTime.Track),
				Future:       !stopTime.Past,
				Arrival:      buildEstimatedTime(stopTime.ArrivalTime, stopTime.ArrivalDelay, stopTime.ArrivalUncertainty),
				Departure:    buildEstimatedTime(stopTime.DepartureTime, stopTime.DepartureDelay, stopTime.DepartureUncertainty),
				Stop:         r.Reference.Stop(stopTime.StopID, system.ID, stopTime.StopName),
			})
		}
		apiTrips = append(apiTrips, reply)
	}
	return apiTrips, nil
}

func buildTripAlertPreviews(ctx context.Context, r *Context, systemID string, tripPks []int64) (map[int64][]*api.Alert_Reference, error) {
	alerts, err := r.Querier.ListActiveAlertsForTrips(
		ctx, db.ListActiveAlertsForTripsParams{
			TripPks:     tripPks,
			PresentTime: pgtype.Timestamptz{Valid: true, Time: time.Now()},
		})
	if err != nil {
		return nil, err
	}
	m := map[int64][]*api.Alert_Reference{}
	for _, alert := range alerts {
		m[alert.TripPk] = append(
			m[alert.TripPk],
			r.Reference.Alert(alert.ID, systemID, alert.Cause, alert.Effect),
		)
	}
	return m, nil
}

func nullShapeReference(r *Context, shapeID pgtype.Text, systemID string) *api.Shape_Reference {
	if !shapeID.Valid {
		return nil
	}
	return r.Reference.Shape(shapeID.String, systemID)
}
