package endpoints

import (
	"context"
	"fmt"
	"time"

	"github.com/jackc/pgx/v4"
	"github.com/jamespfennell/transiter/internal/convert"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/public/errors"
)

func ListFeeds(ctx context.Context, r *Context, req *api.ListFeedsRequest) (*api.ListFeedsReply, error) {
	system, err := getSystem(ctx, r.Querier, req.SystemId)
	if err != nil {
		return nil, err
	}
	feeds, err := r.Querier.ListFeedsInSystem(ctx, system.Pk)
	if err != nil {
		return nil, err
	}
	result := &api.ListFeedsReply{}
	for _, feed := range feeds {
		feed := feed
		apiFeed := &api.Feed_Preview{
			Id:                    feed.ID,
			PeriodicUpdateEnabled: feed.PeriodicUpdateEnabled,
			PeriodicUpdatePeriod:  periodicUpdatePeriod(&feed),
			Href:                  r.Href.Feed(system.ID, feed.ID),
		}
		result.Feeds = append(result.Feeds, apiFeed)
	}
	return result, nil
}

func GetFeed(ctx context.Context, r *Context, req *api.GetFeedRequest) (*api.Feed, error) {
	feed, err := r.Querier.GetFeedInSystem(ctx, db.GetFeedInSystemParams{SystemID: req.SystemId, FeedID: req.FeedId})
	if err != nil {
		if err == pgx.ErrNoRows {
			err = errors.NewNotFoundError(fmt.Sprintf("feed %q in system %q not found", req.FeedId, req.SystemId))
		}
		return nil, err
	}
	reply := &api.Feed{
		Id:                    feed.ID,
		PeriodicUpdateEnabled: feed.PeriodicUpdateEnabled,
		PeriodicUpdatePeriod:  periodicUpdatePeriod(&feed),
		Updates: &api.Feed_Updates{
			Href: r.Href.FeedUpdates(req.SystemId, req.FeedId),
		},
	}
	return reply, nil
}

func ListFeedUpdates(ctx context.Context, r *Context, req *api.ListFeedUpdatesRequest) (*api.ListFeedUpdatesReply, error) {
	feed, err := r.Querier.GetFeedInSystem(ctx, db.GetFeedInSystemParams{SystemID: req.SystemId, FeedID: req.FeedId})
	if err != nil {
		if err == pgx.ErrNoRows {
			err = errors.NewNotFoundError(fmt.Sprintf("feed %q in system %q not found", req.FeedId, req.SystemId))
		}
		return nil, err
	}
	updates, err := r.Querier.ListUpdatesInFeed(ctx, feed.Pk)
	if err != nil {
		return nil, err
	}
	reply := &api.ListFeedUpdatesReply{}
	for _, update := range updates {
		// TODO: update the public API field names to match the database
		reply.Updates = append(reply.Updates, &api.FeedUpdate{
			Id:            fmt.Sprintf("%d", update.Pk),
			Status:        update.Status,
			Result:        convert.SQLNullString(update.Result),
			StackTrace:    convert.SQLNullString(update.ErrorMessage),
			ContentHash:   convert.SQLNullString(update.ContentHash),
			ContentLength: convert.SQLNullInt32(update.ContentLength),
			CompletedAt:   convert.SQLNullTime(update.EndedAt),
		})
	}
	return reply, nil
}

func periodicUpdatePeriod(feed *db.Feed) *string {
	if feed.PeriodicUpdatePeriod.Valid && feed.PeriodicUpdatePeriod.Int32 > 0 {
		d := (time.Millisecond * time.Duration(feed.PeriodicUpdatePeriod.Int32)).String()
		return &d
	}
	return nil
}