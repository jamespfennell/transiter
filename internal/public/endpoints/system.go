package endpoints

import (
	"context"
	"database/sql"
	"strings"

	"github.com/jamespfennell/transiter/internal/gen/api"
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
			// TODO: should resource all have HREFs too, for the list endpoints? Href:   r.Href.System(system.ID),
		})
	}
	return &res, nil
}

func GetSystem(ctx context.Context, r *Context, req *api.GetSystemRequest) (*api.System, error) {
	system, err := getSystem(ctx, r.Querier, req.SystemId)
	if err != nil {
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
		Agencies:  &api.System_ChildEntities{Count: numAgencies, Href: r.Reference.AgenciesHref(req.SystemId)},
		Feeds:     &api.System_ChildEntities{Count: numFeeds, Href: r.Reference.FeedsHref(req.SystemId)},
		Routes:    &api.System_ChildEntities{Count: numRoutes, Href: r.Reference.RoutesHref(req.SystemId)},
		Stops:     &api.System_ChildEntities{Count: numStops, Href: r.Reference.StopsHref(req.SystemId)},
		Transfers: &api.System_ChildEntities{Count: numTransfers, Href: r.Reference.TransfersHref(req.SystemId)},
	}, nil
}
