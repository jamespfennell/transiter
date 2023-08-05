package endpoints

import (
	"context"
	"math"

	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jamespfennell/transiter/internal/convert"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/public/errors"
)

func ListVehicles(ctx context.Context, r *Context, req *api.ListVehiclesRequest) (*api.ListVehiclesReply, error) {
	system, err := getSystem(ctx, r.Querier, req.SystemId)
	if err != nil {
		return nil, err
	}

	numVehicles := r.EndpointOptions.MaxVehiclesPerRequest
	if numVehicles <= 0 {
		numVehicles = math.MaxInt32 - 1
	}
	if req.Limit != nil && *req.Limit < numVehicles {
		numVehicles = *req.Limit
	}
	var firstID string
	if req.FirstId != nil {
		firstID = *req.FirstId
	}

	var dbVehicles []db.ListVehiclesRow
	if req.GetSearchMode() == api.ListVehiclesRequest_DISTANCE {
		if req.Latitude == nil || req.Longitude == nil || req.MaxDistance == nil {
			return nil, errors.NewInvalidArgumentError("latitude, longitude, and max_distance are required when using DISTANCE search_mode")
		}
		if firstID != "" {
			return nil, errors.NewInvalidArgumentError("first_id can not be used when using DISTANCE search_mode")
		}
		dbVehiclesGeo, err := r.Querier.ListVehicles_Geographic(ctx, db.ListVehicles_GeographicParams{
			SystemPk:    system.Pk,
			NumVehicles: numVehicles,
			Latitude:    convert.Gps(req.Latitude),
			Longitude:   convert.Gps(req.Longitude),
			MaxDistance: convert.Gps(req.MaxDistance),
		})

		for _, dbVehicle := range dbVehiclesGeo {
			dbVehicles = append(dbVehicles, db.ListVehiclesRow{
				ID:                  dbVehicle.ID,
				Label:               dbVehicle.Label,
				LicensePlate:        dbVehicle.LicensePlate,
				CurrentStatus:       dbVehicle.CurrentStatus,
				Latitude:            dbVehicle.Latitude,
				Longitude:           dbVehicle.Longitude,
				Bearing:             dbVehicle.Bearing,
				Odometer:            dbVehicle.Odometer,
				Speed:               dbVehicle.Speed,
				CongestionLevel:     dbVehicle.CongestionLevel,
				UpdatedAt:           dbVehicle.UpdatedAt,
				CurrentStopSequence: dbVehicle.CurrentStopSequence,
				OccupancyStatus:     dbVehicle.OccupancyStatus,
				OccupancyPercentage: dbVehicle.OccupancyPercentage,
				StopID:              dbVehicle.StopID,
				StopName:            dbVehicle.StopName,
				TripID:              dbVehicle.TripID,
				TripDirectionID:     dbVehicle.TripDirectionID,
				RouteID:             dbVehicle.RouteID,
				RouteColor:          dbVehicle.RouteColor,
			})
		}

		if err != nil {
			return nil, err
		}
	} else {
		dbVehicles, err = r.Querier.ListVehicles(ctx, db.ListVehiclesParams{
			SystemPk:               system.Pk,
			FirstVehicleID:         convert.NullString(&firstID),
			NumVehicles:            numVehicles + 1,
			OnlyReturnSpecifiedIds: req.OnlyReturnSpecifiedIds,
			VehicleIds:             req.Id,
		})
		if err != nil {
			return nil, err
		}
	}

	apiVehicles, err := buildApiVehicles(ctx, r, &system, dbVehicles)
	if err != nil {
		return nil, err
	}

	var nextID *string
	if len(apiVehicles) == int(numVehicles+1) {
		nextID = &apiVehicles[len(apiVehicles)-1].Id
		apiVehicles = apiVehicles[:len(apiVehicles)-1]
	}

	return &api.ListVehiclesReply{
		Vehicles: apiVehicles,
		NextId:   nextID,
	}, nil
}

func GetVehicle(ctx context.Context, r *Context, req *api.GetVehicleRequest) (*api.Vehicle, error) {
	system, err := getSystem(ctx, r.Querier, req.SystemId)
	if err != nil {
		return nil, err
	}

	dbVehicle, err := r.Querier.GetVehicle(ctx, db.GetVehicleParams{
		SystemPk:  system.Pk,
		VehicleID: convert.NullString(&req.VehicleId),
	})
	if err != nil {
		return nil, err
	}

	apiVehicles, err := buildApiVehicles(ctx, r, &system, []db.ListVehiclesRow{
		{
			ID:                  dbVehicle.ID,
			Label:               dbVehicle.Label,
			LicensePlate:        dbVehicle.LicensePlate,
			CurrentStatus:       dbVehicle.CurrentStatus,
			Latitude:            dbVehicle.Latitude,
			Longitude:           dbVehicle.Longitude,
			Bearing:             dbVehicle.Bearing,
			Odometer:            dbVehicle.Odometer,
			Speed:               dbVehicle.Speed,
			CongestionLevel:     dbVehicle.CongestionLevel,
			UpdatedAt:           dbVehicle.UpdatedAt,
			CurrentStopSequence: dbVehicle.CurrentStopSequence,
			OccupancyPercentage: dbVehicle.OccupancyPercentage,
			OccupancyStatus:     dbVehicle.OccupancyStatus,
			StopID:              dbVehicle.StopID,
			StopName:            dbVehicle.StopName,
			TripID:              dbVehicle.TripID,
			TripDirectionID:     dbVehicle.TripDirectionID,
			RouteID:             dbVehicle.RouteID,
			RouteColor:          dbVehicle.RouteColor,
		},
	})
	if err != nil {
		return nil, err
	}

	return apiVehicles[0], nil
}

func buildApiVehicles(
	ctx context.Context,
	r *Context,
	system *db.System,
	vehicles []db.ListVehiclesRow) ([]*api.Vehicle, error) {
	var apiVehicles []*api.Vehicle
	for i := range vehicles {
		vehicle := &vehicles[i]
		apiVehicles = append(apiVehicles, &api.Vehicle{
			Id: *convert.SQLNullString(vehicle.ID),
			Trip: nullTripReferences(
				r,
				vehicle.TripID,
				nullRouteReferences(r, vehicle.RouteID, vehicle.RouteColor, system.ID),
				vehicle.TripDirectionID.Bool,
			),
			Latitude:        convert.SQLGps(vehicle.Latitude),
			Longitude:       convert.SQLGps(vehicle.Longitude),
			Bearing:         convert.SQLNullFloat4(vehicle.Bearing),
			Odometer:        convert.SQLNullFloat8(vehicle.Odometer),
			Speed:           convert.SQLNullFloat4(vehicle.Speed),
			StopSequence:    convert.SQLNullInt32(vehicle.CurrentStopSequence),
			Stop:            nullStopReference(r, vehicle.StopID, vehicle.StopName, system.ID),
			CurrentStatus:   convert.NullApiCurrentStatus(vehicle.CurrentStatus),
			UpdatedAt:       convert.SQLNullTime(vehicle.UpdatedAt),
			CongestionLevel: convert.ApiCongestionLevel(vehicle.CongestionLevel),
			OccupancyStatus: convert.NullApiOccupancyStatus(vehicle.OccupancyStatus),
		})
	}

	return apiVehicles, nil
}

func nullTripReferences(
	r *Context,
	tripID pgtype.Text,
	routeRef *api.Route_Reference,
	directionID bool) *api.Trip_Reference {
	if !tripID.Valid || routeRef == nil {
		return nil
	}
	return r.Reference.Trip(tripID.String, routeRef, nil, nil, directionID)
}

func nullRouteReferences(r *Context, routeID pgtype.Text, routeColor pgtype.Text, systemID string) *api.Route_Reference {
	if !routeID.Valid {
		return nil
	}
	return r.Reference.Route(routeID.String, systemID, *convert.SQLNullString(routeColor))
}

func nullStopReference(r *Context, stopID pgtype.Text, stopName pgtype.Text, systemID string) *api.Stop_Reference {
	if !stopID.Valid {
		return nil
	}
	return r.Reference.Stop(stopID.String, systemID, stopName)
}
