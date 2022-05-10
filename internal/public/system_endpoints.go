package public

import (
	"context"
	"database/sql"
	"fmt"
	"strings"

	"github.com/jackc/pgx/v4"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/public/errors"
)

func (t *Service) ListSystems(ctx context.Context, req *api.ListSystemsRequest) (*api.ListSystemsReply, error) {
	s := t.newSession(ctx)
	defer s.Cleanup()
	systems, err := s.Querier.ListSystems(ctx)
	if err != nil {
		return nil, err
	}
	res := api.ListSystemsReply{}
	for _, system := range systems {
		res.Systems = append(res.Systems, &api.System{
			Id:     system.ID,
			Name:   system.Name,
			Status: api.System_Status(api.System_Status_value[strings.ToUpper(system.Status)]),
			Href:   s.Hrefs.System(system.ID),
		})
	}
	return &res, s.Finish()
}

func (t *Service) GetSystem(ctx context.Context, req *api.GetSystemRequest) (*api.System, error) {
	s := t.newSession(ctx)
	defer s.Cleanup()
	system, err := s.Querier.GetSystem(ctx, req.SystemId)
	if err != nil {
		if err == pgx.ErrNoRows {
			err = errors.NewNotFoundError(fmt.Sprintf("system %q not found", req.SystemId))
		}
		return nil, err
	}
	numAgencies, err := s.Querier.CountAgenciesInSystem(ctx, system.Pk)
	if err != nil {
		// TODO: 501 internal error
		return nil, err
	}
	numFeeds, err := s.Querier.CountFeedsInSystem(ctx, system.Pk)
	if err != nil {
		return nil, err
	}
	numRoutes, err := s.Querier.CountRoutesInSystem(ctx, system.Pk)
	if err != nil {
		return nil, err
	}
	numStops, err := s.Querier.CountStopsInSystem(ctx, system.Pk)
	if err != nil {
		return nil, err
	}
	numTransfers, err := s.Querier.CountTransfersInSystem(ctx, sql.NullInt64{Valid: true, Int64: system.Pk})
	if err != nil {
		return nil, err
	}
	return &api.System{
		Id:        system.ID,
		Name:      system.Name,
		Status:    api.System_Status(api.System_Status_value[strings.ToUpper(system.Status)]),
		Agencies:  &api.CountAndHref{Count: numAgencies, Href: s.Hrefs.AgenciesInSystem(req.SystemId)},
		Feeds:     &api.CountAndHref{Count: numFeeds, Href: s.Hrefs.FeedsInSystem(req.SystemId)},
		Routes:    &api.CountAndHref{Count: numRoutes, Href: s.Hrefs.RoutesInSystem(req.SystemId)},
		Stops:     &api.CountAndHref{Count: numStops, Href: s.Hrefs.StopsInSystem(req.SystemId)},
		Transfers: &api.CountAndHref{Count: numTransfers, Href: s.Hrefs.TransfersInSystem(req.SystemId)},
	}, s.Finish()
}
