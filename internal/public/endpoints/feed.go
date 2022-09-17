package endpoints

import (
	"context"
	"fmt"

	"github.com/jamespfennell/transiter/internal/convert"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
)

func ListFeeds(ctx context.Context, r *Context, req *api.ListFeedsRequest) (*api.ListFeedsReply, error) {
	system, err := getSystem(ctx, r.Querier, req.SystemId)
	if err != nil {
		return nil, err
	}
	feeds, err := r.Querier.ListFeeds(ctx, system.Pk)
	if err != nil {
		return nil, err
	}
	apiFeeds, err := buildApiFeeds(ctx, r, &system, feeds)
	if err != nil {
		return nil, err
	}
	return &api.ListFeedsReply{
		Feeds: apiFeeds,
	}, nil
}

func GetFeed(ctx context.Context, r *Context, req *api.GetFeedRequest) (*api.Feed, error) {
	system, feed, err := getFeed(ctx, r.Querier, req.SystemId, req.FeedId)
	if err != nil {
		return nil, err
	}
	apiFeeds, err := buildApiFeeds(ctx, r, &system, []db.Feed{feed})
	if err != nil {
		return nil, err
	}
	return apiFeeds[0], nil
}

func buildApiFeeds(ctx context.Context, r *Context, system *db.System, feeds []db.Feed) ([]*api.Feed, error) {
	var apiFeeds []*api.Feed
	for i := range feeds {
		feed := &feeds[i]
		numUpdates, err := r.Querier.CountUpdatesInFeed(ctx, feed.Pk)
		if err != nil {
			return nil, err
		}
		apiFeeds = append(apiFeeds, &api.Feed{
			Id:                     feed.ID,
			PeriodicUpdateEnabled:  feed.PeriodicUpdateEnabled,
			PeriodicUpdatePeriodMs: convert.SQLNullInt64(feed.PeriodicUpdatePeriod),
			Updates: &api.ChildResources{
				Count: numUpdates,
				Href:  r.Reference.FeedUpdatesHref(system.ID, feed.ID),
			},
		})
	}
	return apiFeeds, nil
}

func ListFeedUpdates(ctx context.Context, r *Context, req *api.ListFeedUpdatesRequest) (*api.ListFeedUpdatesReply, error) {
	_, feed, err := getFeed(ctx, r.Querier, req.SystemId, req.FeedId)
	if err != nil {
		return nil, err
	}
	updates, err := r.Querier.ListUpdatesInFeed(ctx, feed.Pk)
	if err != nil {
		return nil, err
	}
	reply := &api.ListFeedUpdatesReply{}
	for _, update := range updates {
		reply.Updates = append(reply.Updates, &api.FeedUpdate{
			Id:            fmt.Sprintf("%d", update.Pk),
			StartedAt:     update.StartedAt.Unix(),
			Finished:      update.Finished,
			FinishedAt:    convert.SQLNullTime(update.FinishedAt),
			Result:        convert.FeedUpdateResult(update.Result),
			ContentHash:   convert.SQLNullString(update.ContentHash),
			ContentLength: convert.SQLNullInt32(update.ContentLength),
			ErrorMessage:  convert.SQLNullString(update.ErrorMessage),
		})
	}
	return reply, nil
}
