package common

import (
	"testing"

	"github.com/jamespfennell/transiter/internal/gen/api"
)

func TestGetFeedType(t *testing.T) {
	feedConfig := &api.FeedConfig{
		Type: "GTFS_STATIC",
	}
	if got := GetFeedType(feedConfig); got != "GTFS_STATIC" {
		t.Errorf("GetFeedType() = %v, want %v", got, "GTFS_STATIC")
	}
}

func TestGetFeedTypeNone(t *testing.T) {
	feedConfig := &api.FeedConfig{}
	if got := GetFeedType(feedConfig); got != "" {
		t.Errorf("GetFeedType() = %v, want %v", got, "")
	}

	feedConfig = nil
	if got := GetFeedType(feedConfig); got != "" {
		t.Errorf("GetFeedType() = %v, want %v", got, "")
	}
}

func TestGetFeedTypeFromParser(t *testing.T) {
	feedConfig := &api.FeedConfig{
		Parser: "GTFS_STATIC",
	}
	if got := GetFeedType(feedConfig); got != "GTFS_STATIC" {
		t.Errorf("GetFeedType() = %v, want %v", got, "GTFS_STATIC")
	}
}

func TestGetFeedTypeBothTypeAndParser(t *testing.T) {
	feedConfig := &api.FeedConfig{
		Parser: "Foo",
		Type:   "GTFS_STATIC",
	}
	if got := GetFeedType(feedConfig); got != "GTFS_STATIC" {
		t.Errorf("GetFeedType() = %v, want %v", got, "GTFS_STATIC")
	}
}

func TestUseAccessibilityInfoFromFeedStaticFeed(t *testing.T) {
	var feedConfig = &api.FeedConfig{
		Type: "GTFS_STATIC",
	}
	if got := UseAccessibilityInfoFromFeed(feedConfig); got != true {
		t.Errorf("UseAccessibilityInfoFromFeed() = %v, want %v", got, true)
	}

	feedConfig = &api.FeedConfig{
		Type: "GTFS_STATIC",
		NyctSubwayOptions: &api.FeedConfig_NyctSubwayOptions{
			UseAccessibilityInfo: true,
		},
	}
	if got := UseAccessibilityInfoFromFeed(feedConfig); got != true {
		t.Errorf("UseAccessibilityInfoFromFeed() = %v, want %v", got, true)
	}

	feedConfig = &api.FeedConfig{
		Type: "GTFS_STATIC",
		NyctSubwayOptions: &api.FeedConfig_NyctSubwayOptions{
			UseAccessibilityInfo: false,
		},
	}
	if got := UseAccessibilityInfoFromFeed(feedConfig); got != false {
		t.Errorf("UseAccessibilityInfoFromFeed() = %v, want %v", got, false)
	}
}

func TestUseAccessibilityInfoFromFeedNyctSubwayCsvFeed(t *testing.T) {
	var feedConfig = &api.FeedConfig{
		Type: "NYCT_SUBWAY_CSV",
	}
	if got := UseAccessibilityInfoFromFeed(feedConfig); got != false {
		t.Errorf("UseAccessibilityInfoFromFeed() = %v, want %v", got, false)
	}

	feedConfig = &api.FeedConfig{
		Type: "NYCT_SUBWAY_CSV",
		NyctSubwayOptions: &api.FeedConfig_NyctSubwayOptions{
			UseAccessibilityInfo: true,
		},
	}
	if got := UseAccessibilityInfoFromFeed(feedConfig); got != true {
		t.Errorf("UseAccessibilityInfoFromFeed() = %v, want %v", got, true)
	}

	feedConfig = &api.FeedConfig{
		Type: "NYCT_SUBWAY_CSV",
		NyctSubwayOptions: &api.FeedConfig_NyctSubwayOptions{
			UseAccessibilityInfo: false,
		},
	}
	if got := UseAccessibilityInfoFromFeed(feedConfig); got != false {
		t.Errorf("UseAccessibilityInfoFromFeed() = %v, want %v", got, false)
	}
}

func TestUseAccessibilityInfoFromFeedRealtimeFeed(t *testing.T) {
	var feedConfig = &api.FeedConfig{
		Type: "GTFS_REALTIME",
	}
	if got := UseAccessibilityInfoFromFeed(feedConfig); got != false {
		t.Errorf("UseAccessibilityInfoFromFeed() = %v, want %v", got, false)
	}

	feedConfig = &api.FeedConfig{
		Type: "GTFS_REALTIME",
		NyctSubwayOptions: &api.FeedConfig_NyctSubwayOptions{
			UseAccessibilityInfo: true,
		},
	}
	if got := UseAccessibilityInfoFromFeed(feedConfig); got != false {
		t.Errorf("UseAccessibilityInfoFromFeed() = %v, want %v", got, false)
	}

	feedConfig = &api.FeedConfig{
		Type: "GTFS_REALTIME",
		NyctSubwayOptions: &api.FeedConfig_NyctSubwayOptions{
			UseAccessibilityInfo: false,
		},
	}
	if got := UseAccessibilityInfoFromFeed(feedConfig); got != false {
		t.Errorf("UseAccessibilityInfoFromFeed() = %v, want %v", got, false)
	}
}
