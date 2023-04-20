package admin

import (
	"context"

	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/update"
)

func (s *Service) UpdateFeed(ctx context.Context, req *api.UpdateFeedRequest) (*api.UpdateFeedReply, error) {
	if err := update.Update(ctx, s.logger, s.pool, req.SystemId, req.FeedId); err != nil {
		return nil, err
	}
	return &api.UpdateFeedReply{}, nil
}
