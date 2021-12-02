// Package service contains the implementation of the Transiter service.
package service

import (
	"context"
	"database/sql"

	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/service/session"
)

// TransiterService implements the Transiter service.
type TransiterService struct {
	database *sql.DB
	api.UnimplementedTransiterServer
}

func NewTransiterService(database *sql.DB) *TransiterService {
	return &TransiterService{database: database}
}

func (t *TransiterService) NewSession(ctx context.Context) session.Session {
	return session.NewSession(t.database, ctx)
}

func (t *TransiterService) Entrypoint(ctx context.Context, req *api.EntrypointRequest) (*api.EntrypointReply, error) {
	s := t.NewSession(ctx)
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
