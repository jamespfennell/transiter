// Package public contains the implementation of the Transiter public API.
package public

import (
	"context"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/monitoring"
	"github.com/jamespfennell/transiter/internal/public/endpoints"
	"github.com/jamespfennell/transiter/internal/public/reference"
)

// Server implements the Transiter public API.
type Server struct {
	pool            *pgxpool.Pool
	endpointOptions *endpoints.EndpointOptions
}

// New creates a new `Server` that uses the provided pool to connect to the database.
func New(pool *pgxpool.Pool, endpointOptions *endpoints.EndpointOptions) *Server {
	if endpointOptions == nil {
		endpointOptions = &endpoints.EndpointOptions{MaxStopsPerRequest: 100}
	}

	return &Server{pool: pool, endpointOptions: endpointOptions}
}

func (s *Server) Entrypoint(ctx context.Context, req *api.EntrypointRequest) (*api.EntrypointReply, error) {
	return run(ctx, s, "Entrypoint", endpoints.Entrypoint, req)
}

func (s *Server) ListSystems(ctx context.Context, req *api.ListSystemsRequest) (*api.ListSystemsReply, error) {
	return run(ctx, s, "ListSystems", endpoints.ListSystems, req)
}

func (s *Server) GetSystem(ctx context.Context, req *api.GetSystemRequest) (*api.System, error) {
	return run(ctx, s, "GetSystem", endpoints.GetSystem, req)
}

func (s *Server) ListAgencies(ctx context.Context, req *api.ListAgenciesRequest) (*api.ListAgenciesReply, error) {
	return run(ctx, s, "ListAgencies", endpoints.ListAgencies, req)
}

func (s *Server) GetAgency(ctx context.Context, req *api.GetAgencyRequest) (*api.Agency, error) {
	return run(ctx, s, "GetAgency", endpoints.GetAgency, req)
}

func (s *Server) ListStops(ctx context.Context, req *api.ListStopsRequest) (*api.ListStopsReply, error) {
	return run(ctx, s, "ListStops", endpoints.ListStops, req)
}

func (s *Server) ListTransfers(ctx context.Context, req *api.ListTransfersRequest) (*api.ListTransfersReply, error) {
	return run(ctx, s, "ListTransfers", endpoints.ListTransfers, req)
}

func (s *Server) GetStop(ctx context.Context, req *api.GetStopRequest) (*api.Stop, error) {
	return run(ctx, s, "GetStop", endpoints.GetStop, req)
}

func (s *Server) ListRoutes(ctx context.Context, req *api.ListRoutesRequest) (*api.ListRoutesReply, error) {
	return run(ctx, s, "ListRoutes", endpoints.ListRoutes, req)
}

func (s *Server) GetRoute(ctx context.Context, req *api.GetRouteRequest) (*api.Route, error) {
	return run(ctx, s, "GetRoute", endpoints.GetRoute, req)
}

func (s *Server) ListFeeds(ctx context.Context, req *api.ListFeedsRequest) (*api.ListFeedsReply, error) {
	return run(ctx, s, "ListFeeds", endpoints.ListFeeds, req)
}

func (s *Server) GetFeed(ctx context.Context, req *api.GetFeedRequest) (*api.Feed, error) {
	return run(ctx, s, "GetFeed", endpoints.GetFeed, req)
}

func (s *Server) ListFeedUpdates(ctx context.Context, req *api.ListFeedUpdatesRequest) (*api.ListFeedUpdatesReply, error) {
	return run(ctx, s, "ListFeedUpdates", endpoints.ListFeedUpdates, req)
}

func (s *Server) ListTrips(ctx context.Context, req *api.ListTripsRequest) (*api.ListTripsReply, error) {
	return run(ctx, s, "ListTrips", endpoints.ListTrips, req)
}

func (s *Server) GetTrip(ctx context.Context, req *api.GetTripRequest) (*api.Trip, error) {
	return run(ctx, s, "GetTrip", endpoints.GetTrip, req)
}

func (s *Server) ListAlerts(ctx context.Context, req *api.ListAlertsRequest) (*api.ListAlertsReply, error) {
	return run(ctx, s, "ListAlerts", endpoints.ListAlerts, req)
}

func (s *Server) GetAlert(ctx context.Context, req *api.GetAlertRequest) (*api.Alert, error) {
	return run(ctx, s, "GetAlert", endpoints.GetAlert, req)
}

func run[S, T any](ctx context.Context, s *Server, methodName string, f func(context.Context, *endpoints.Context, S) (T, error), req S) (T, error) {
	startTime := time.Now()
	var t T
	err := pgx.BeginTxFunc(ctx, s.pool, pgx.TxOptions{AccessMode: pgx.ReadOnly}, func(tx pgx.Tx) error {
		var err error
		t, err = f(ctx, &endpoints.Context{Querier: db.New(tx), Reference: reference.NewGenerator(ctx), EndpointOptions: *s.endpointOptions}, req)
		return err
	})
	monitoring.RecordPublicRequest(methodName, err, time.Since(startTime))
	return t, err
}
