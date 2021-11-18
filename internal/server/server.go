// Package server contains the implementation of the Transiter service.
package server

import (
	"context"
	"database/sql"

	"strings"

	"github.com/jamespfennell/transiter/internal/gen/api"
	tdb "github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/util"
	_ "github.com/lib/pq"
)

// TransiterServer implements the Transiter service.
type TransiterServer struct {
	querier tdb.Querier
	api.UnimplementedTransiterServer
}

func NewTransiterServer(querier tdb.Querier) *TransiterServer {
	return &TransiterServer{querier: querier}
}

func (t *TransiterServer) Entrypoint(ctx context.Context, req *api.EntrypointRequest) (*api.EntrypointReply, error) {
	numSystems, err := t.querier.CountSystems(ctx)
	if err != nil {
		return nil, err
	}
	hrefGenerator := util.NewHrefGenerator(ctx)
	return &api.EntrypointReply{
		Transiter: &api.EntrypointReply_TransiterDetails{
			Version: "1.0.0alpha",
			Href:    "https://github.com/jamespfennell/transiter",
		},
		Systems: &api.CountAndHref{
			Count: numSystems,
			Href:  hrefGenerator.Systems(),
		},
	}, nil
}

func (t *TransiterServer) ListSystems(ctx context.Context, req *api.ListSystemsRequest) (*api.ListSystemsReply, error) {
	systems, err := t.querier.ListSystems(ctx)
	if err != nil {
		return nil, err
	}
	res := api.ListSystemsReply{}
	for _, system := range systems {
		res.Systems = append(res.Systems, &api.SystemShort{
			Id:     system.ID,
			Name:   system.Name,
			Status: api.SystemStatus(api.SystemStatus_value[strings.ToUpper(system.Status)]),
		})
	}
	return &res, nil
}

func (t *TransiterServer) GetSystem(ctx context.Context, req *api.GetSystemRequest) (*api.GetSystemReply, error) {
	system, err := t.querier.GetSystem(ctx, req.Id)
	if err != nil {
		// TODO: unknown error
		return nil, err
	}
	numAgencies, err := t.querier.CountAgenciesInSystem(ctx, system.Pk)
	if err != nil {
		return nil, err
	}
	numFeeds, err := t.querier.CountFeedsInSystem(ctx, system.Pk)
	if err != nil {
		return nil, err
	}
	numRoutes, err := t.querier.CountRoutesInSystem(ctx, system.Pk)
	if err != nil {
		return nil, err
	}
	numStops, err := t.querier.CountStopsInSystem(ctx, system.Pk)
	if err != nil {
		return nil, err
	}
	numTransfers, err := t.querier.CountTransfersInSystem(ctx, sql.NullInt32{Valid: true, Int32: system.Pk})
	if err != nil {
		return nil, err
	}
	return &api.GetSystemReply{
		Id:        system.ID,
		Name:      system.Name,
		Status:    api.SystemStatus(api.SystemStatus_value[strings.ToUpper(system.Status)]),
		Agencies:  &api.CountAndHref{Count: numAgencies, Href: ""},
		Feeds:     &api.CountAndHref{Count: numFeeds, Href: ""},
		Routes:    &api.CountAndHref{Count: numRoutes, Href: ""},
		Stops:     &api.CountAndHref{Count: numStops, Href: ""},
		Transfers: &api.CountAndHref{Count: numTransfers, Href: ""},
	}, nil
}
