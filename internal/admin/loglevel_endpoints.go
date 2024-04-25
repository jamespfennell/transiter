package admin

import (
	"context"

	"github.com/jamespfennell/transiter/internal/gen/api"
	"golang.org/x/exp/slog"
)

func (s *Service) GetLogLevel(ctx context.Context, req *api.GetLogLevelRequest) (*api.GetLogLevelReply, error) {
	return &api.GetLogLevelReply{
		LogLevel: convertInternalLogLevelToApi(s.levelVar.Level()),
	}, nil
}

func (s *Service) SetLogLevel(ctx context.Context, req *api.SetLogLevelRequest) (*api.SetLogLevelReply, error) {
	s.levelVar.Set(convertApiLogLevelToInternal(req.GetLogLevel()))
	return &api.SetLogLevelReply{}, nil
}

func convertApiLogLevelToInternal(ll api.LogLevel) slog.Level {
	switch ll {
	case api.LogLevel_DEBUG:
		return slog.LevelDebug
	case api.LogLevel_WARN:
		return slog.LevelWarn
	case api.LogLevel_ERROR:
		return slog.LevelError
	default:
		return slog.LevelInfo
	}
}

func convertInternalLogLevelToApi(ll slog.Level) api.LogLevel {
	switch ll {
	case slog.LevelDebug:
		return api.LogLevel_DEBUG
	case slog.LevelWarn:
		return api.LogLevel_WARN
	case slog.LevelError:
		return api.LogLevel_ERROR
	default:
		return api.LogLevel_INFO
	}
}
