package public

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	"github.com/jamespfennell/transiter/internal/apihelpers"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/public/errors"
)

func (t *Service) ListFeedsInSystem(ctx context.Context, req *api.ListFeedsInSystemRequest) (*api.ListFeedsInSystemReply, error) {
	s := t.newSession(ctx)
	defer s.Cleanup()
	system, err := s.Querier.GetSystem(ctx, req.SystemId)
	if err != nil {
		if err == sql.ErrNoRows {
			err = errors.NewNotFoundError(fmt.Sprintf("system %q not found", req.SystemId))
		}
		return nil, err
	}
	feeds, err := s.Querier.ListFeedsInSystem(ctx, system.Pk)
	if err != nil {
		return nil, err
	}
	result := &api.ListFeedsInSystemReply{}
	for _, feed := range feeds {
		feed := feed
		api_feed := &api.FeedPreview{
			Id:                feed.ID,
			AutoUpdateEnabled: feed.AutoUpdateEnabled,
			AutoUpdatePeriod:  autoUpdatePeriod(&feed),
			Href:              s.Hrefs.Feed(system.ID, feed.ID),
		}
		result.Feeds = append(result.Feeds, api_feed)
	}
	return result, s.Finish()
}

func (t *Service) GetFeedInSystem(ctx context.Context, req *api.GetFeedInSystemRequest) (*api.Feed, error) {
	s := t.newSession(ctx)
	defer s.Cleanup()
	feed, err := s.Querier.GetFeedInSystem(ctx, db.GetFeedInSystemParams{SystemID: req.SystemId, FeedID: req.FeedId})
	if err != nil {
		if err == sql.ErrNoRows {
			err = errors.NewNotFoundError(fmt.Sprintf("feed %q in system %q not found", req.FeedId, req.SystemId))
		}
		return nil, err
	}
	reply := &api.Feed{
		Id:                feed.ID,
		AutoUpdateEnabled: feed.AutoUpdateEnabled,
		AutoUpdatePeriod:  autoUpdatePeriod(&feed),
		Updates: &api.Feed_Updates{
			Href: s.Hrefs.FeedUpdates(req.SystemId, req.FeedId),
		},
	}
	return reply, s.Finish()
}

func (t *Service) ListFeedUpdates(ctx context.Context, req *api.ListFeedUpdatesRequest) (*api.ListFeedUpdatesReply, error) {
	s := t.newSession(ctx)
	defer s.Cleanup()
	feed, err := s.Querier.GetFeedInSystem(ctx, db.GetFeedInSystemParams{SystemID: req.SystemId, FeedID: req.FeedId})
	if err != nil {
		if err == sql.ErrNoRows {
			err = errors.NewNotFoundError(fmt.Sprintf("feed %q in system %q not found", req.FeedId, req.SystemId))
		}
		return nil, err
	}
	updates, err := s.Querier.ListUpdatesInFeed(ctx, feed.Pk)
	if err != nil {
		return nil, err
	}
	reply := &api.ListFeedUpdatesReply{}
	for _, update := range updates {
		reply.Updates = append(reply.Updates, &api.FeedUpdate{
			Id:            fmt.Sprintf("%d", update.Pk),
			Type:          update.UpdateType,
			Status:        update.Status.String,
			Result:        apihelpers.ConvertSqlNullString(update.Result),
			StackTrace:    apihelpers.ConvertSqlNullString(update.ResultMessage),
			ContentHash:   apihelpers.ConvertSqlNullString(update.ContentHash),
			ContentLength: apihelpers.ConvertSqlNullInt32(update.ContentLength),
			CompletedAt:   apihelpers.ConvertSqlNullTime(update.CompletedAt),
		})
	}
	return reply, s.Finish()
}

func autoUpdatePeriod(feed *db.Feed) *string {
	if feed.AutoUpdatePeriod.Valid && feed.AutoUpdatePeriod.Int32 > 0 {
		d := (time.Millisecond * time.Duration(feed.AutoUpdatePeriod.Int32)).String()
		return &d
	}
	return nil
}
