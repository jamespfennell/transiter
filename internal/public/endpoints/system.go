package endpoints

import (
	"context"
	"strings"

	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
)

func ListSystems(ctx context.Context, r *Context, req *api.ListSystemsRequest) (*api.ListSystemsReply, error) {
	systems, err := r.Querier.ListSystems(ctx)
	if err != nil {
		return nil, err
	}
	apiSystems, err := buildApiSystems(ctx, r, systems)
	if err != nil {
		return nil, err
	}
	return &api.ListSystemsReply{
		Systems: apiSystems,
	}, nil
}

func GetSystem(ctx context.Context, r *Context, req *api.GetSystemRequest) (*api.System, error) {
	system, err := getSystem(ctx, r.Querier, req.SystemId)
	if err != nil {
		return nil, err
	}
	apiSystems, err := buildApiSystems(ctx, r, []db.System{system})
	if err != nil {
		return nil, err
	}
	return apiSystems[0], nil
}

func buildApiSystems(ctx context.Context, r *Context, systems []db.System) ([]*api.System, error) {
	var apiSystems []*api.System
	for i := range systems {
		system := &systems[i]
		numAgencies, err := r.Querier.CountAgenciesInSystem(ctx, system.Pk)
		if err != nil {
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
		numTransfers, err := r.Querier.CountTransfersInSystem(ctx, system.Pk)
		if err != nil {
			return nil, err
		}
		apiSystems = append(apiSystems, &api.System{
			Id:        system.ID,
			Name:      system.Name,
			Status:    api.System_Status(api.System_Status_value[strings.ToUpper(system.Status)]),
			Agencies:  r.Reference.AgenciesChildResources(system.ID, numAgencies),
			Feeds:     &api.ChildResources{Count: numFeeds, Url: r.Reference.FeedsURL(system.ID)},
			Routes:    r.Reference.RoutesChildResources(system.ID, numRoutes),
			Stops:     r.Reference.StopsChildResources(system.ID, numStops),
			Transfers: &api.ChildResources{Count: numTransfers, Url: r.Reference.TransfersURL(system.ID)},
		})
	}
	return apiSystems, nil
}
