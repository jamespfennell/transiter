package admin

import (
	"context"
	"time"

	"github.com/jamespfennell/transiter/internal/gen/api"
)

func (s *Service) GetSchedulerStatus(ctx context.Context, req *api.GetSchedulerStatusRequest) (*api.GetSchedulerStatusReply, error) {
	reply := &api.GetSchedulerStatusReply{}
	feeds := s.scheduler.Status()
	for _, feed := range feeds {
		reply.Feeds = append(reply.Feeds, &api.GetSchedulerStatusReply_Feed{
			SystemId:             feed.SystemId,
			FeedId:               feed.FeedId,
			Period:               int32(feed.Period.Milliseconds()),
			LastSuccessfulUpdate: convert(feed.LastSuccessfulUpdate),
			LastFinishedUpdate:   convert(feed.LastFinishedUpdate),
			CurrentlyRunning:     feed.CurrentlyRunning,
		})
	}
	return reply, nil
}

func (s *Service) RefreshScheduler(ctx context.Context, req *api.RefreshSchedulerRequest) (*api.RefreshSchedulerReply, error) {
	if err := s.scheduler.RefreshAll(ctx); err != nil {
		return nil, err
	}
	return &api.RefreshSchedulerReply{}, nil
}

func convert(t time.Time) int64 {
	if t.IsZero() {
		return 0
	}
	return t.Unix()
}
