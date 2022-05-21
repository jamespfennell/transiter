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
			SystemId:             feed.SystemID,
			FeedId:               feed.FeedID,
			Period:               feed.Period.Milliseconds(),
			LastSuccessfulUpdate: convert(feed.LastSuccessfulUpdate),
			LastFinishedUpdate:   convert(feed.LastFinishedUpdate),
			CurrentlyRunning:     feed.CurrentlyRunning,
		})
	}
	return reply, nil
}

func (s *Service) ResetScheduler(ctx context.Context, req *api.ResetSchedulerRequest) (*api.ResetSchedulerReply, error) {
	if err := s.scheduler.ResetAll(ctx); err != nil {
		return nil, err
	}
	return &api.ResetSchedulerReply{}, nil
}

func convert(t time.Time) int64 {
	if t.IsZero() {
		return 0
	}
	return t.Unix()
}
