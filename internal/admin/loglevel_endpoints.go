package admin

import (
	"context"

	"github.com/jamespfennell/transiter/internal/gen/api"
	"golang.org/x/exp/slog"
)

func (s *Service) GetLogLevel(ctx context.Context, req *api.GetLogLevelRequest) (*api.GetLogLevelReply, error) {
	return &api.GetLogLevelReply{
		LogLevel: s.levelVar.Level().String(),
	}, nil
}

func (s *Service) SetLogLevel(ctx context.Context, req *api.SetLogLevelRequest) (*api.SetLogLevelReply, error) {
	var l slog.Level
	if err := l.UnmarshalText([]byte(req.GetLogLevel())); err != nil {
		return nil, err
	}
	s.levelVar.Set(l)
	return &api.SetLogLevelReply{}, nil
}
