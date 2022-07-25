package endpoints

import (
	"context"
	"fmt"

	"github.com/jackc/pgx/v4"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/public/errors"
	"github.com/jamespfennell/transiter/internal/public/href"
)

type Context struct {
	Querier db.Querier
	Href    href.Generator
}

func getSystem(ctx context.Context, querier db.Querier, id string) (db.System, error) {
	system, err := querier.GetSystem(ctx, id)
	return system, noRowsToNotFound(err, fmt.Sprintf("system %q", id))
}

func getRoute(ctx context.Context, querier db.Querier, systemID, routeID string) (db.System, db.Route, error) {
	system, err := getSystem(ctx, querier, systemID)
	if err != nil {
		return system, db.Route{}, err
	}
	route, err := querier.GetRouteInSystem(ctx, db.GetRouteInSystemParams{SystemPk: system.Pk, RouteID: routeID})
	return system, route, noRowsToNotFound(err, fmt.Sprintf("route %q in system %q", routeID, system.ID))
}

func getStop(ctx context.Context, querier db.Querier, systemID, stopID string) (db.System, db.Stop, error) {
	system, err := getSystem(ctx, querier, systemID)
	if err != nil {
		return system, db.Stop{}, err
	}
	route, err := querier.GetStopInSystem(ctx, db.GetStopInSystemParams{SystemID: system.ID, StopID: stopID})
	return system, route, noRowsToNotFound(err, fmt.Sprintf("stop %q in system %q", stopID, system.ID))
}

func noRowsToNotFound(err error, notFoundText string) error {
	if err == pgx.ErrNoRows {
		err = errors.NewNotFoundError(notFoundText + " does not exist")
	}
	return err
}
