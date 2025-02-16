package endtoend

import (
	"fmt"
	"testing"

	"github.com/jamespfennell/transiter/tests/endtoend/fixtures"
	"github.com/jamespfennell/transiter/tests/endtoend/testutils"
	"github.com/jamespfennell/transiter/tests/endtoend/transiterclient"
)

var FeedIDs = []string{fixtures.GTFSRealtimeFeedID, fixtures.GTFSStaticFeedID}

var StaticFeed = transiterclient.Feed{
	ID: fixtures.GTFSStaticFeedID,
}

var RealTimeFeed = transiterclient.Feed{
	ID: fixtures.GTFSRealtimeFeedID,
}

func TestInstallSystem(t *testing.T) {
	for _, tc := range []struct {
		name string
		test func(t *testing.T, client *transiterclient.TransiterClient, systemID string)
	}{
		{
			name: "get system",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string) {
				gotSystem, err := client.GetSystem(systemID)
				if err != nil {
					t.Fatalf("failed to get system: %v", err)
				}
				wantSystem := &transiterclient.System{
					ID:        systemID,
					Name:      "Test System",
					Status:    "ACTIVE",
					Agencies:  &transiterclient.ChildResources{Count: 1, Path: fmt.Sprintf("systems/%s/agencies", systemID)},
					Feeds:     &transiterclient.ChildResources{Count: 2, Path: fmt.Sprintf("systems/%s/feeds", systemID)},
					Routes:    &transiterclient.ChildResources{Count: 0, Path: fmt.Sprintf("systems/%s/routes", systemID)},
					Stops:     &transiterclient.ChildResources{Count: 0, Path: fmt.Sprintf("systems/%s/stops", systemID)},
					Transfers: &transiterclient.ChildResources{Count: 0, Path: fmt.Sprintf("systems/%s/transfers", systemID)},
				}
				testutils.AssertEqual(t, gotSystem, wantSystem)
			},
		},
		{
			name: "list feeds",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string) {
				gotListFeeds, err := client.ListFeeds(systemID)
				if err != nil {
					t.Fatalf("failed to list feeds: %v", err)
				}
				wantListFeeds := []transiterclient.Feed{
					RealTimeFeed,
					StaticFeed,
				}
				for idx := range gotListFeeds.Feeds {
					gotListFeeds.Feeds[idx].LastSuccessfulUpdateMs = nil
				}
				testutils.AssertEqual(t, gotListFeeds.Feeds, wantListFeeds)
			},
		},
		{
			name: "get feed",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string) {
				gotFeed, err := client.GetFeed(systemID, fixtures.GTFSRealtimeFeedID)
				if err != nil {
					t.Fatalf("failed to get feed: %v", err)
				}
				testutils.AssertEqual(t, gotFeed, &RealTimeFeed)
			},
		},
		{
			name: "update system",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string) {
				gotSystem, err := client.GetSystem(systemID)
				if err != nil {
					t.Fatalf("failed to get system: %v", err)
				}
				testutils.AssertEqual(t, gotSystem.Name, "Test System")

				config := `
name: New Name
feeds:
- id: new_feed
  url: "https://www.example.com"
  parser: GTFS_STATIC
  requiredForInstall: false
`
				fixtures.UpdateSystem(t, systemID, config, fixtures.GTFSStaticDefaultZipBuilder().MustBuild())

				gotSystem, err = client.GetSystem(systemID)
				if err != nil {
					t.Fatalf("failed to get system: %v", err)
				}
				testutils.AssertEqual(t, gotSystem.Name, "New Name")
				wFeedsChildResources := &transiterclient.ChildResources{
					Count: 1,
					Path:  fmt.Sprintf("systems/%s/feeds", systemID),
				}
				testutils.AssertEqual(t, gotSystem.Feeds, wFeedsChildResources)

				gotListFeeds, err := client.ListFeeds(systemID)
				if err != nil {
					t.Fatalf("failed to list feeds: %v", err)
				}
				testutils.AssertEqual(t, gotListFeeds.Feeds, []transiterclient.Feed{{ID: "new_feed"}})
			},
		},
		{
			name: "delete system",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string) {
				client.DeleteSystem(systemID)
				_, err := client.GetSystem(systemID)
				testutils.AssertHTTPErrorCode(t, err, 404)
			},
		},
	} {
		testName := fmt.Sprintf("%s/%s", "installsystem", tc.name)
		t.Run(testName, func(t *testing.T) {
			systemID, _, _ := fixtures.InstallSystem(t, fixtures.GTFSStaticDefaultZipBuilder().MustBuild())
			transiterClient := fixtures.GetTransiterClient(t)
			tc.test(t, transiterClient, systemID)
		})
	}
}
