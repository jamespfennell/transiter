package service

import (
	"context"
	"database/sql"
	"fmt"

	"github.com/jamespfennell/transiter/internal/apihelpers"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/service/errors"
)

func (t *TransiterService) ListTripsInRoute(ctx context.Context, req *api.ListTripsInRouteRequest) (*api.ListTripsInRouteReply, error) {
	s := t.NewSession(ctx)
	defer s.Cleanup()
	route, err := s.Querier.GetRouteInSystem(ctx,
		db.GetRouteInSystemParams{SystemID: req.SystemId, RouteID: req.RouteId})
	if err != nil {
		if err == sql.ErrNoRows {
			err = errors.NewNotFoundError(fmt.Sprintf("route %q in system %q not found", req.RouteId, req.SystemId))
		}
		return nil, err
	}
	trips, err := s.Querier.ListTripsInRoute(ctx, route.Pk)
	if err != nil {
		return nil, err
	}
	var tripPks []int32
	for _, trip := range trips {
		tripPks = append(tripPks, trip.Pk)
	}
	// TODO: deduplicate this between the GetStop endpoint
	rows, err := s.Querier.GetLastStopsForTrips(ctx, tripPks)
	if err != nil {
		return nil, err
	}
	tripPkToLastStop := map[int32]*db.GetLastStopsForTripsRow{}
	for _, row := range rows {
		row := row
		tripPkToLastStop[row.TripPk] = &row
	}

	reply := &api.ListTripsInRouteReply{}
	for _, trip := range trips {
		trip := trip
		lastStop := tripPkToLastStop[trip.Pk]
		api_trip := &api.TripPreviewWithAlerts{
			Id:          trip.ID,
			DirectionId: trip.DirectionID.Bool,
			StartedAt:   apihelpers.ConvertSqlNullTime(trip.StartedAt),
			UpdatedAt:   apihelpers.ConvertSqlNullTime(trip.UpdatedAt),
			LastStop: &api.StopPreview{
				Id:   lastStop.ID,
				Name: lastStop.Name,
				Href: s.Hrefs.Stop(req.SystemId, lastStop.ID),
			},
			Href: s.Hrefs.Trip(req.SystemId, route.ID, trip.ID),
		}
		if trip.VehicleID.Valid {
			api_trip.Vehicle = &api.VehiclePreview{
				Id: trip.VehicleID.String,
			}
		}
		reply.Trips = append(reply.Trips, api_trip)
	}
	return reply, s.Finish()
}

func (t *TransiterService) GetTrip(ctx context.Context, req *api.GetTripRequest) (*api.Trip, error) {
	s := t.NewSession(ctx)
	defer s.Cleanup()
	trip, err := s.Querier.GetTrip(ctx, db.GetTripParams{
		SystemID: req.SystemId, RouteID: req.RouteId, TripID: req.TripId})
	if err != nil {
		if err == sql.ErrNoRows {
			err = errors.NewNotFoundError(fmt.Sprintf("trip %q in route %q in system %q not found",
				req.TripId, req.RouteId, req.SystemId))
		}
		return nil, err
	}
	stopTimes, err := s.Querier.ListStopsTimesForTrip(ctx, trip.Pk)
	if err != nil {
		return nil, err
	}
	reply := &api.Trip{
		Id:          trip.ID,
		DirectionId: trip.DirectionID.Bool,
		StartedAt:   apihelpers.ConvertSqlNullTime(trip.StartedAt),
		UpdatedAt:   apihelpers.ConvertSqlNullTime(trip.UpdatedAt),
		Route: &api.RoutePreview{
			Id:    trip.RouteID,
			Color: trip.RouteColor.String,
			Href:  s.Hrefs.Route(req.SystemId, req.RouteId),
		},
		Href: s.Hrefs.Trip(req.SystemId, req.RouteId, req.TripId),
	}
	if trip.VehicleID.Valid {
		reply.Vehicle = &api.VehiclePreview{
			Id: trip.VehicleID.String,
		}
	}
	for _, stopTime := range stopTimes {
		reply.StopTimes = append(reply.StopTimes, &api.Trip_StopTime{
			StopSequence: stopTime.StopSequence,
			Track:        apihelpers.ConvertSqlNullString(stopTime.Track),
			Future: stopTime.StopSequence >= 0 && (trip.CurrentStopSequence.Int32 <= stopTime.StopSequence ||
				!trip.CurrentStopSequence.Valid),
			Arrival:   buildEstimatedTime(stopTime.ArrivalTime, stopTime.ArrivalDelay, stopTime.ArrivalUncertainty),
			Departure: buildEstimatedTime(stopTime.DepartureTime, stopTime.DepartureDelay, stopTime.DepartureUncertainty),
			Stop: &api.StopPreview{
				Id:   stopTime.StopID,
				Name: stopTime.StopName,
				Href: s.Hrefs.Stop(req.SystemId, stopTime.StopID),
			},
		})
	}
	return reply, s.Finish()
}
