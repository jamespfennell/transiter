// Package common contains types used by all update code.
package common

import (
	"crypto/md5"
	"encoding/json"
	"fmt"

	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"golang.org/x/exp/slog"
)

type UpdateContext struct {
	Querier    db.Querier
	Logger     *slog.Logger
	SystemPk   int64
	FeedPk     int64
	FeedConfig *api.FeedConfig
}

func GetFeedType(feedConfig *api.FeedConfig) string {
	if feedConfig == nil {
		return ""
	}
	if feedConfig.GetType() != "" {
		return feedConfig.GetType()
	}
	// Deprecated, but included for backwards compatibility
	return feedConfig.GetParser()
}

func UseAccessibilityInfoFromFeed(feedConfig *api.FeedConfig) bool {
	if feedConfig == nil {
		return true
	}

	feed_type := GetFeedType(feedConfig)

	// Default to static GTFS feeds having accessibility info
	if feedConfig.NyctSubwayOptions == nil {
		return feed_type == "GTFS_STATIC"
	}

	if feed_type == "GTFS_STATIC" || feed_type == "NYCT_SUBWAY_CSV" {
		return feedConfig.NyctSubwayOptions.UseAccessibilityInfo
	}

	// Accessibility info is not currently available for other feed types
	return false
}

func HashBytes(b []byte) string {
	return fmt.Sprintf("%x", md5.Sum(b))
}

func HashValue(a any) (string, error) {
	b, err := json.Marshal(a)
	if err != nil {
		return "", err
	}
	return HashBytes(b), nil
}

func MapValues[K comparable, V any](in map[K]V) []V {
	out := make([]V, 0, len(in))
	for _, v := range in {
		out = append(out, v)
	}
	return out
}

func MapKeys[T comparable, V any](in map[T]V) []T {
	var out []T
	for t := range in {
		out = append(out, t)
	}
	return out
}
