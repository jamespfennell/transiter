// Package public contains the implementation of the Transiter public API.
package public

import (
	"context"

	"github.com/jackc/pgx/v4"
	"github.com/jackc/pgx/v4/pgxpool"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/public/endpoints"
	"github.com/jamespfennell/transiter/internal/public/href"
)

// Server implements the Transiter public API.
type Server struct {
	pool *pgxpool.Pool
}

// New creates a new `Server` that uses the provided pool to connect to the database.
func New(pool *pgxpool.Pool) *Server {
	return &Server{pool: pool}
}

func (s *Server) Entrypoint(ctx context.Context, req *api.EntrypointRequest) (*api.EntrypointReply, error) {
	return run(ctx, s, endpoints.Entrypoint, req)
}

func (s *Server) ListSystems(ctx context.Context, req *api.ListSystemsRequest) (*api.ListSystemsReply, error) {
	return run(ctx, s, endpoints.ListSystems, req)
}

func (s *Server) GetSystem(ctx context.Context, req *api.GetSystemRequest) (*api.System, error) {
	return run(ctx, s, endpoints.GetSystem, req)
}

func (s *Server) ListAgenciesInSystem(ctx context.Context, req *api.ListAgenciesInSystemRequest) (*api.ListAgenciesInSystemReply, error) {
	return run(ctx, s, endpoints.ListAgenciesInSystem, req)
}

func (s *Server) GetAgencyInSystem(ctx context.Context, req *api.GetAgencyInSystemRequest) (*api.Agency, error) {
	return run(ctx, s, endpoints.GetAgencyInSystem, req)
}

func (s *Server) ListStopsInSystem(ctx context.Context, req *api.ListStopsInSystemRequest) (*api.ListStopsInSystemReply, error) {
	return run(ctx, s, endpoints.ListStopsInSystem, req)
}

func (s *Server) ListTransfersInSystem(ctx context.Context, req *api.ListTransfersInSystemRequest) (*api.ListTransfersInSystemReply, error) {
	return run(ctx, s, endpoints.ListTransfersInSystem, req)
}

func (s *Server) GetStopInSystem(ctx context.Context, req *api.GetStopInSystemRequest) (*api.Stop, error) {
	return run(ctx, s, endpoints.GetStopInSystem, req)
}

func (s *Server) ListRoutesInSystem(ctx context.Context, req *api.ListRoutesInSystemRequest) (*api.ListRoutesInSystemReply, error) {
	return run(ctx, s, endpoints.ListRoutesInSystem, req)
}

func (s *Server) GetRouteInSystem(ctx context.Context, req *api.GetRouteInSystemRequest) (*api.Route, error) {
	return run(ctx, s, endpoints.GetRouteInSystem, req)
}

func (s *Server) ListFeedsInSystem(ctx context.Context, req *api.ListFeedsInSystemRequest) (*api.ListFeedsInSystemReply, error) {
	return run(ctx, s, endpoints.ListFeedsInSystem, req)
}

func (s *Server) GetFeedInSystem(ctx context.Context, req *api.GetFeedInSystemRequest) (*api.Feed, error) {
	return run(ctx, s, endpoints.GetFeedInSystem, req)
}

func (s *Server) ListFeedUpdates(ctx context.Context, req *api.ListFeedUpdatesRequest) (*api.ListFeedUpdatesReply, error) {
	return run(ctx, s, endpoints.ListFeedUpdates, req)
}

func (s *Server) ListTripsInRoute(ctx context.Context, req *api.ListTripsInRouteRequest) (*api.ListTripsInRouteReply, error) {
	return run(ctx, s, endpoints.ListTripsInRoute, req)
}

func (s *Server) GetTrip(ctx context.Context, req *api.GetTripRequest) (*api.Trip, error) {
	return run(ctx, s, endpoints.GetTrip, req)
}

func run[S, T any](ctx context.Context, s *Server, f func(context.Context, *endpoints.Context, S) (T, error), req S) (T, error) {
	var t T
	if err := s.pool.BeginTxFunc(ctx, pgx.TxOptions{AccessMode: pgx.ReadOnly}, func(tx pgx.Tx) error {
		var err error
		t, err = f(ctx, &endpoints.Context{Querier: db.New(tx), Href: href.NewGenerator(ctx)}, req)
		return err
	}); err != nil {
		var t T
		return t, err
	}
	return t, nil
}
