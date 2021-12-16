// Package public contains the implementation of the Transiter public API.
package public

import (
	"context"
	"database/sql"

	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/public/session"
)

// Service implements the Transiter public service.
type Service struct {
	database *sql.DB
	api.UnimplementedPublicServer
}

func New(database *sql.DB) *Service {
	return &Service{database: database}
}

func (t *Service) newSession(ctx context.Context) session.Session {
	return session.NewSession(t.database, ctx)
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
