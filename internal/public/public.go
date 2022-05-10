// Package public contains the implementation of the Transiter public API.
package public

import (
	"context"

	"github.com/jackc/pgx/v4/pgxpool"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/public/session"
)

// Service implements the Transiter public service.
type Service struct {
	pool *pgxpool.Pool
	api.UnimplementedPublicServer
}

func New(pool *pgxpool.Pool) *Service {
	return &Service{pool: pool}
}

func (t *Service) newSession(ctx context.Context) session.Session {
	return session.NewSession(ctx, t.pool)
}

func (t *Service) Entrypoint(ctx context.Context, req *api.EntrypointRequest) (*api.EntrypointReply, error) {
	s := t.newSession(ctx)
	defer s.Cleanup()
	numSystems, err := s.Querier.CountSystems(ctx)
	if err != nil {
		return nil, err
	}
	return &api.EntrypointReply{
		Transiter: &api.EntrypointReply_TransiterDetails{
			Version: "1.0.0alpha",
			Href:    "https://github.com/jamespfennell/transiter",
		},
		Systems: &api.CountAndHref{
			Count: numSystems,
			Href:  s.Hrefs.Systems(),
		},
	}, s.Finish()
}
