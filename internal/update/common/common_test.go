package common

import (
	"testing"

	"github.com/jamespfennell/transiter/internal/gen/api"
)

func TestGetFeedType(t *testing.T) {
	feed_config := &api.FeedConfig{
		Type: "GTFS_STATIC",
	}
	if got := GetFeedType(feed_config); got != "GTFS_STATIC" {
		t.Errorf("GetFeedType() = %v, want %v", got, "GTFS_STATIC")
	}
}

func TestGetFeedTypeNone(t *testing.T) {
	feed_config := &api.FeedConfig{}
	if got := GetFeedType(feed_config); got != "" {
		t.Errorf("GetFeedType() = %v, want %v", got, "")
	}

	feed_config = nil
	if got := GetFeedType(feed_config); got != "" {
		t.Errorf("GetFeedType() = %v, want %v", got, "")
	}
}

func TestGetFeedTypeFromParser(t *testing.T) {
	feed_config := &api.FeedConfig{
		Parser: "GTFS_STATIC",
	}
	if got := GetFeedType(feed_config); got != "GTFS_STATIC" {
		t.Errorf("GetFeedType() = %v, want %v", got, "GTFS_STATIC")
	}
}

func TestGetFeedTypeBothTypeAndParser(t *testing.T) {
	feed_config := &api.FeedConfig{
		Parser: "Foo",
		Type:   "GTFS_STATIC",
	}
	if got := GetFeedType(feed_config); got != "GTFS_STATIC" {
		t.Errorf("GetFeedType() = %v, want %v", got, "GTFS_STATIC")
	}
}

func TestUseAccessibilityInfoFromFeedStaticFeed(t *testing.T) {
	var feed_config = &api.FeedConfig{
		Type: "GTFS_STATIC",
	}
	if got := UseAccessibilityInfoFromFeed(feed_config); got != true {
		t.Errorf("UseAccessibilityInfoFromFeed() = %v, want %v", got, true)
	}

	feed_config = &api.FeedConfig{
		Type: "GTFS_STATIC",
		NyctSubwayOptions: &api.FeedConfig_NyctSubwayOptions{
			UseAccessibilityInfo: true,
		},
	}
	if got := UseAccessibilityInfoFromFeed(feed_config); got != true {
		t.Errorf("UseAccessibilityInfoFromFeed() = %v, want %v", got, true)
	}

	feed_config = &api.FeedConfig{
		Type: "GTFS_STATIC",
		NyctSubwayOptions: &api.FeedConfig_NyctSubwayOptions{
			UseAccessibilityInfo: false,
		},
	}
	if got := UseAccessibilityInfoFromFeed(feed_config); got != false {
		t.Errorf("UseAccessibilityInfoFromFeed() = %v, want %v", got, false)
	}
}

func TestUseAccessibilityInfoFromFeedNyctSubwayCsvFeed(t *testing.T) {
	var feed_config = &api.FeedConfig{
		Type: "NYCT_SUBWAY_CSV",
	}
	if got := UseAccessibilityInfoFromFeed(feed_config); got != false {
		t.Errorf("UseAccessibilityInfoFromFeed() = %v, want %v", got, false)
	}

	feed_config = &api.FeedConfig{
		Type: "NYCT_SUBWAY_CSV",
		NyctSubwayOptions: &api.FeedConfig_NyctSubwayOptions{
			UseAccessibilityInfo: true,
		},
	}
	if got := UseAccessibilityInfoFromFeed(feed_config); got != true {
		t.Errorf("UseAccessibilityInfoFromFeed() = %v, want %v", got, true)
	}

	feed_config = &api.FeedConfig{
		Type: "NYCT_SUBWAY_CSV",
		NyctSubwayOptions: &api.FeedConfig_NyctSubwayOptions{
			UseAccessibilityInfo: false,
		},
	}
	if got := UseAccessibilityInfoFromFeed(feed_config); got != false {
		t.Errorf("UseAccessibilityInfoFromFeed() = %v, want %v", got, false)
	}
}

func TestUseAccessibilityInfoFromFeedRealtimeFeed(t *testing.T) {
	var feed_config = &api.FeedConfig{
		Type: "GTFS_REALTIME",
	}
	if got := UseAccessibilityInfoFromFeed(feed_config); got != false {
		t.Errorf("UseAccessibilityInfoFromFeed() = %v, want %v", got, false)
	}

	feed_config = &api.FeedConfig{
		Type: "GTFS_REALTIME",
		NyctSubwayOptions: &api.FeedConfig_NyctSubwayOptions{
			UseAccessibilityInfo: true,
		},
	}
	if got := UseAccessibilityInfoFromFeed(feed_config); got != false {
		t.Errorf("UseAccessibilityInfoFromFeed() = %v, want %v", got, false)
	}

	feed_config = &api.FeedConfig{
		Type: "GTFS_REALTIME",
		NyctSubwayOptions: &api.FeedConfig_NyctSubwayOptions{
			UseAccessibilityInfo: false,
		},
	}
	if got := UseAccessibilityInfoFromFeed(feed_config); got != false {
		t.Errorf("UseAccessibilityInfoFromFeed() = %v, want %v", got, false)
	}
}
