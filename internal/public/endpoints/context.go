package endpoints

import (
	"context"
	"fmt"

	"github.com/jackc/pgx/v5"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/public/errors"
	"github.com/jamespfennell/transiter/internal/public/reference"
	"golang.org/x/exp/slog"
)

type EndpointOptions struct {
	// The maximum number of stops that can be returned in a single request.
	// Defaults to 100.
	MaxStopsPerRequest int32
	// The maximum number of vehicles that can be returned in a single request.
	// Defaults to 100.
	MaxVehiclesPerRequest int32
}

type Context struct {
	Querier         db.Querier
	Reference       reference.Generator
	Logger          *slog.Logger
	EndpointOptions EndpointOptions
}

func getSystem(ctx context.Context, querier db.Querier, id string) (db.System, error) {
	system, err := querier.GetSystem(ctx, id)
	return system, noRowsToNotFound(err, fmt.Sprintf("system %q", id))
}

func getFeed(ctx context.Context, querier db.Querier, systemID, feedID string) (db.System, db.Feed, error) {
	system, err := getSystem(ctx, querier, systemID)
	if err != nil {
		return system, db.Feed{}, err
	}
	feed, err := querier.GetFeed(ctx, db.GetFeedParams{SystemID: system.ID, FeedID: feedID})
	return system, feed, noRowsToNotFound(err, fmt.Sprintf("route %q in system %q", feedID, system.ID))
}

func getRoute(ctx context.Context, querier db.Querier, systemID, routeID string) (db.System, db.Route, error) {
	system, err := getSystem(ctx, querier, systemID)
	if err != nil {
		return system, db.Route{}, err
	}
	route, err := querier.GetRoute(ctx, db.GetRouteParams{SystemPk: system.Pk, RouteID: routeID})
	return system, route, noRowsToNotFound(err, fmt.Sprintf("route %q in system %q", routeID, system.ID))
}

func getStop(ctx context.Context, querier db.Querier, systemID, stopID string) (db.System, db.Stop, error) {
	system, err := getSystem(ctx, querier, systemID)
	if err != nil {
		return system, db.Stop{}, err
	}
	route, err := querier.GetStop(ctx, db.GetStopParams{SystemID: system.ID, StopID: stopID})
	return system, route, noRowsToNotFound(err, fmt.Sprintf("stop %q in system %q", stopID, system.ID))
}

func noRowsToNotFound(err error, notFoundText string) error {
	if err == pgx.ErrNoRows {
		err = errors.NewNotFoundError(notFoundText + " does not exist")
	}
	return err
}
