package endpoints

import (
	"context"
	"database/sql"
	"fmt"
	"strings"

	"github.com/jackc/pgx/v4"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/public/errors"
)

func ListSystems(ctx context.Context, r *Context, req *api.ListSystemsRequest) (*api.ListSystemsReply, error) {
	systems, err := r.Querier.ListSystems(ctx)
	if err != nil {
		return nil, err
	}
	res := api.ListSystemsReply{}
	for _, system := range systems {
		res.Systems = append(res.Systems, &api.System{
			Id:     system.ID,
			Name:   system.Name,
			Status: api.System_Status(api.System_Status_value[strings.ToUpper(system.Status)]),
			Href:   r.Href.System(system.ID),
		})
	}
	return &res, nil
}

func GetSystem(ctx context.Context, r *Context, req *api.GetSystemRequest) (*api.System, error) {
	system, err := r.Querier.GetSystem(ctx, req.SystemId)
	if err != nil {
		if err == pgx.ErrNoRows {
			err = errors.NewNotFoundError(fmt.Sprintf("system %q not found", req.SystemId))
		}
		return nil, err
	}
	numAgencies, err := r.Querier.CountAgenciesInSystem(ctx, system.Pk)
	if err != nil {
		// TODO: 501 internal error
		return nil, err
	}
	numFeeds, err := r.Querier.CountFeedsInSystem(ctx, system.Pk)
	if err != nil {
		return nil, err
	}
	numRoutes, err := r.Querier.CountRoutesInSystem(ctx, system.Pk)
	if err != nil {
		return nil, err
	}
	numStops, err := r.Querier.CountStopsInSystem(ctx, system.Pk)
	if err != nil {
		return nil, err
	}
	numTransfers, err := r.Querier.CountTransfersInSystem(ctx, sql.NullInt64{Valid: true, Int64: system.Pk})
	if err != nil {
		return nil, err
	}
	return &api.System{
		Id:        system.ID,
		Name:      system.Name,
		Status:    api.System_Status(api.System_Status_value[strings.ToUpper(system.Status)]),
		Agencies:  &api.CountAndHref{Count: numAgencies, Href: r.Href.AgenciesInSystem(req.SystemId)},
		Feeds:     &api.CountAndHref{Count: numFeeds, Href: r.Href.FeedsInSystem(req.SystemId)},
		Routes:    &api.CountAndHref{Count: numRoutes, Href: r.Href.RoutesInSystem(req.SystemId)},
		Stops:     &api.CountAndHref{Count: numStops, Href: r.Href.StopsInSystem(req.SystemId)},
		Transfers: &api.CountAndHref{Count: numTransfers, Href: r.Href.TransfersInSystem(req.SystemId)},
	}, nil
}
