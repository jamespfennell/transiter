package endpoints

import (
	"context"
	"fmt"

	"github.com/jackc/pgx/v4"
	"github.com/jamespfennell/transiter/internal/convert"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/public/errors"
)

func ListTrips(ctx context.Context, r *Context, req *api.ListTripsRequest) (*api.ListTripsReply, error) {
	_, route, err := getRoute(ctx, r.Querier, req.SystemId, req.RouteId)
	if err != nil {
		return nil, err
	}
	trips, err := r.Querier.ListTripsInRoute(ctx, route.Pk)
	if err != nil {
		return nil, err
	}
	var tripPks []int64
	for _, trip := range trips {
		tripPks = append(tripPks, trip.Pk)
	}
	// TODO: deduplicate this between the GetStop endpoint
	rows, err := r.Querier.GetLastStopsForTrips(ctx, tripPks)
	if err != nil {
		return nil, err
	}
	tripPkToLastStop := map[int64]*db.GetLastStopsForTripsRow{}
	for _, row := range rows {
		row := row
		tripPkToLastStop[row.TripPk] = &row
	}

	reply := &api.ListTripsReply{}
	for _, trip := range trips {
		trip := trip
		lastStop := tripPkToLastStop[trip.Pk]
		apiTrip := &api.Trip_Preview{
			Id:          trip.ID,
			DirectionId: trip.DirectionID.Bool,
			StartedAt:   convert.SQLNullTime(trip.StartedAt),
			LastStop: &api.Stop_Preview{
				Id:   lastStop.ID,
				Name: lastStop.Name.String,
				Href: r.Href.Stop(req.SystemId, lastStop.ID),
			},
			Href: r.Href.Trip(req.SystemId, route.ID, trip.ID),
		}
		if trip.VehicleID.Valid {
			apiTrip.Vehicle = &api.Vehicle_Preview{
				Id: trip.VehicleID.String,
			}
		}
		reply.Trips = append(reply.Trips, apiTrip)
	}
	return reply, nil
}

func GetTrip(ctx context.Context, r *Context, req *api.GetTripRequest) (*api.Trip, error) {
	trip, err := r.Querier.GetTrip(ctx, db.GetTripParams{
		SystemID: req.SystemId, RouteID: req.RouteId, TripID: req.TripId})
	if err != nil {
		if err == pgx.ErrNoRows {
			err = errors.NewNotFoundError(fmt.Sprintf("trip %q in route %q in system %q not found",
				req.TripId, req.RouteId, req.SystemId))
		}
		return nil, err
	}
	stopTimes, err := r.Querier.ListStopsTimesForTrip(ctx, trip.Pk)
	if err != nil {
		return nil, err
	}
	reply := &api.Trip{
		Id:          trip.ID,
		DirectionId: trip.DirectionID.Bool,
		StartedAt:   convert.SQLNullTime(trip.StartedAt),
		Route: &api.Route_Preview{
			Id:    trip.RouteID,
			Color: trip.RouteColor,
			Href:  r.Href.Route(req.SystemId, req.RouteId),
		},
		Href: r.Href.Trip(req.SystemId, req.RouteId, req.TripId),
	}
	if trip.VehicleID.Valid {
		reply.Vehicle = &api.Vehicle_Preview{
			Id: trip.VehicleID.String,
		}
	}
	for _, stopTime := range stopTimes {
		reply.StopTimes = append(reply.StopTimes, &api.StopTime{
			StopSequence: stopTime.StopSequence,
			Track:        convert.SQLNullString(stopTime.Track),
			Future:       !stopTime.Past,
			Arrival:      buildEstimatedTime(stopTime.ArrivalTime, stopTime.ArrivalDelay, stopTime.ArrivalUncertainty),
			Departure:    buildEstimatedTime(stopTime.DepartureTime, stopTime.DepartureDelay, stopTime.DepartureUncertainty),
			Stop: &api.Stop_Preview{
				Id:   stopTime.StopID,
				Name: stopTime.StopName.String,
				Href: r.Href.Stop(req.SystemId, stopTime.StopID),
			},
		})
	}
	return reply, nil
}
