// Package public contains the implementation of the Transiter public API.
package public

import (
	"context"

	"github.com/jackc/pgx/v4"
	"github.com/jackc/pgx/v4/pgxpool"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/public/endpoints"
	"github.com/jamespfennell/transiter/internal/public/reference"
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

func (s *Server) ListAgencies(ctx context.Context, req *api.ListAgenciesRequest) (*api.ListAgenciesReply, error) {
	return run(ctx, s, endpoints.ListAgencies, req)
}

func (s *Server) GetAgency(ctx context.Context, req *api.GetAgencyRequest) (*api.Agency, error) {
	return run(ctx, s, endpoints.GetAgency, req)
}

func (s *Server) ListStops(ctx context.Context, req *api.ListStopsRequest) (*api.ListStopsReply, error) {
	return run(ctx, s, endpoints.ListStops, req)
}

func (s *Server) ListTransfers(ctx context.Context, req *api.ListTransfersRequest) (*api.ListTransfersReply, error) {
	return run(ctx, s, endpoints.ListTransfers, req)
}

func (s *Server) GetStop(ctx context.Context, req *api.GetStopRequest) (*api.Stop, error) {
	return run(ctx, s, endpoints.GetStop, req)
}

func (s *Server) ListRoutes(ctx context.Context, req *api.ListRoutesRequest) (*api.ListRoutesReply, error) {
	return run(ctx, s, endpoints.ListRoutes, req)
}

func (s *Server) GetRoute(ctx context.Context, req *api.GetRouteRequest) (*api.Route, error) {
	return run(ctx, s, endpoints.GetRoute, req)
}

func (s *Server) ListFeeds(ctx context.Context, req *api.ListFeedsRequest) (*api.ListFeedsReply, error) {
	return run(ctx, s, endpoints.ListFeeds, req)
}

func (s *Server) GetFeed(ctx context.Context, req *api.GetFeedRequest) (*api.Feed, error) {
	return run(ctx, s, endpoints.GetFeed, req)
}

func (s *Server) ListFeedUpdates(ctx context.Context, req *api.ListFeedUpdatesRequest) (*api.ListFeedUpdatesReply, error) {
	return run(ctx, s, endpoints.ListFeedUpdates, req)
}

func (s *Server) ListTrips(ctx context.Context, req *api.ListTripsRequest) (*api.ListTripsReply, error) {
	return run(ctx, s, endpoints.ListTrips, req)
}

func (s *Server) GetTrip(ctx context.Context, req *api.GetTripRequest) (*api.Trip, error) {
	return run(ctx, s, endpoints.GetTrip, req)
}

func (s *Server) ListAlerts(ctx context.Context, req *api.ListAlertsRequest) (*api.ListAlertsReply, error) {
	return run(ctx, s, endpoints.ListAlerts, req)
}

func (s *Server) GetAlert(ctx context.Context, req *api.GetAlertRequest) (*api.Alert, error) {
	return run(ctx, s, endpoints.GetAlert, req)
}

func run[S, T any](ctx context.Context, s *Server, f func(context.Context, *endpoints.Context, S) (T, error), req S) (T, error) {
	var t T
	if err := s.pool.BeginTxFunc(ctx, pgx.TxOptions{AccessMode: pgx.ReadOnly}, func(tx pgx.Tx) error {
		var err error
		t, err = f(ctx, &endpoints.Context{Querier: db.New(tx), Reference: reference.NewGenerator(ctx)}, req)
		return err
	}); err != nil {
		var t T
		return t, err
	}
	return t, nil
}
