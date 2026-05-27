package graphql

import (
	"context"
	"fmt"
	"strings"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jamespfennell/transiter/db/types"
	db "github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/graphql/model"
)

func (r *queryResolver) Stops(ctx context.Context, systemID string, location model.LocationInput, radiusMeters *int, first *int) ([]*model.Stop, error) {
	radius := 500
	if radiusMeters != nil {
		radius = *radiusMeters
	}
	limit := 50
	if first != nil {
		limit = *first
	}
	if limit > 100 {
		limit = 100
	}

	var result []*model.Stop
	err := pgx.BeginTxFunc(ctx, r.Pool, pgx.TxOptions{AccessMode: pgx.ReadOnly}, func(tx pgx.Tx) error {
		querier := db.New(tx)
		system, err := querier.GetSystem(ctx, systemID)
		if err != nil {
			return fmt.Errorf("system %q not found", systemID)
		}
		stops, err := querier.ListStops_Geographic(ctx, db.ListStops_GeographicParams{
			SystemPk:     system.Pk,
			MaxDistance:  float64(radius) / 1000.0,
			MaxResults:   int32(limit),
			Base:         types.NewPoint(location.Lon, location.Lat),
			FilterByType: false,
		})
		if err != nil {
			return err
		}
		for i := range stops {
			result = append(result, dbStopToModel(&stops[i]))
		}
		return nil
	})
	if result == nil {
		result = []*model.Stop{}
	}
	return result, err
}

func (r *stopResolver) ParentStop(ctx context.Context, obj *model.Stop) (*model.Stop, error) {
	if obj.ParentStopPk == nil {
		return nil, nil
	}
	return getLoaders(ctx).ParentStop.Load(ctx, *obj.ParentStopPk)
}

func (r *stopResolver) ChildStops(ctx context.Context, obj *model.Stop) ([]*model.Stop, error) {
	return getLoaders(ctx).ChildStops.Load(ctx, obj.Pk)
}

func (r *stopResolver) StopTimes(ctx context.Context, obj *model.Stop, first *int) ([]*model.StopTime, error) {
	limit := 10
	if first != nil {
		limit = *first
	}
	if limit > 100 {
		limit = 100
	}
	all, err := getLoaders(ctx).StopTimes.Load(ctx, obj.Pk)
	if err != nil {
		return nil, err
	}
	if len(all) > limit {
		all = all[:limit]
	}
	return all, nil
}

func (r *stopTimeResolver) Trip(ctx context.Context, obj *model.StopTime) (*model.Trip, error) {
	return &model.Trip{
		ID:          obj.TripID,
		DirectionID: obj.DirectionID,
		RoutePk:     obj.RoutePk,
		RouteCache:  obj.RouteCache,
	}, nil
}

func (r *tripResolver) Route(ctx context.Context, obj *model.Trip) (*model.Route, error) {
	if obj.RouteCache != nil {
		return obj.RouteCache, nil
	}
	var result *model.Route
	err := pgx.BeginTxFunc(ctx, r.Resolver.Pool, pgx.TxOptions{AccessMode: pgx.ReadOnly}, func(tx pgx.Tx) error {
		querier := db.New(tx)
		routes, err := querier.ListRoutesByPk(ctx, []int64{obj.RoutePk})
		if err != nil {
			return err
		}
		if len(routes) == 0 {
			return fmt.Errorf("route with pk %d not found", obj.RoutePk)
		}
		result = &model.Route{
			ID:    routes[0].ID,
			Color: routes[0].Color,
		}
		return nil
	})
	return result, err
}

func (r *Resolver) Query() QueryResolver      { return &queryResolver{r} }
func (r *Resolver) Stop() StopResolver         { return &stopResolver{r} }
func (r *Resolver) StopTime() StopTimeResolver { return &stopTimeResolver{r} }
func (r *Resolver) Trip() TripResolver         { return &tripResolver{r} }

type queryResolver struct{ *Resolver }
type stopResolver struct{ *Resolver }
type stopTimeResolver struct{ *Resolver }
type tripResolver struct{ *Resolver }

// --- helpers ---

func dbStopToModel(s *db.Stop) *model.Stop {
	stop := &model.Stop{
		Pk:       s.Pk,
		SystemPk: s.SystemPk,
		ID:       s.ID,
		Type:     model.StopType(strings.ToUpper(s.Type)),
	}
	if s.Name.Valid {
		stop.Name = &s.Name.String
	}
	if s.Location.Valid {
		stop.Location.Lat = s.Location.Latitude
		stop.Location.Lon = s.Location.Longitude
	}
	if s.ParentStopPk.Valid {
		pk := s.ParentStopPk.Int64
		stop.ParentStopPk = &pk
	}
	return stop
}

func timestamptzToPtr(ts pgtype.Timestamptz) *int64 {
	if !ts.Valid {
		return nil
	}
	unix := ts.Time.Unix()
	return &unix
}

func int4ToPtr(v pgtype.Int4) *int32 {
	if !v.Valid {
		return nil
	}
	return &v.Int32
}
