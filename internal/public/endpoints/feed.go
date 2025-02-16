package endpoints

import (
	"context"

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
	apiFeeds, err := buildApiFeeds(r, &system, feeds)
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
	apiFeeds, err := buildApiFeeds(r, &system, []db.Feed{feed})
	if err != nil {
		return nil, err
	}
	return apiFeeds[0], nil
}

func buildApiFeeds(r *Context, system *db.System, feeds []db.Feed) ([]*api.Feed, error) {
	var apiFeeds []*api.Feed
	for i := range feeds {
		feed := &feeds[i]
		apiFeeds = append(apiFeeds, &api.Feed{
			Id:                     feed.ID,
			System:                 r.Reference.System(system.ID),
			Resource:               r.Reference.Feed(feed.ID, system.ID).Resource,
			LastUpdateMs:           convert.SQLNullTimeMs(feed.LastUpdate),
			LastSuccessfulUpdateMs: convert.SQLNullTimeMs(feed.LastSuccessfulUpdate),
			LastSkippedUpdateMs:    convert.SQLNullTimeMs(feed.LastSkippedUpdate),
			LastFailedUpdateMs:     convert.SQLNullTimeMs(feed.LastFailedUpdate),
		})
	}
	return apiFeeds, nil
}
