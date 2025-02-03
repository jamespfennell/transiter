package endtoend

import (
	"testing"
	"time"

	gtfsrt "github.com/jamespfennell/gtfs/proto"
	"github.com/jamespfennell/transiter/tests/endtoend/fixtures"
	"github.com/jamespfennell/transiter/tests/endtoend/testutils"
	"github.com/jamespfennell/transiter/tests/endtoend/transiterclient"
)

func TestPeriodicUpdate(t *testing.T) {
	systemID, _, realtimeFeedURL := fixtures.InstallSystem(t,
		fixtures.GTFSStaticDefaultZipBuilder().MustBuild(), fixtures.WithRealtimeUpdatePeriodS(0.1))

	// Wait for a successful update
	feedContent := gtfsrt.FeedMessage{
		Header: &gtfsrt.FeedHeader{
			GtfsRealtimeVersion: testutils.Ptr("2.0"),
			Timestamp:           testutils.Ptr(uint64(0)),
		},
	}
	fixtures.PublishGTFSRTFeedMessage(t, realtimeFeedURL, &feedContent)
	watermark := waitForUpdate(t, systemID, lastSuccessfulUpdateMs, nil)

	// Wait for a skipped update
	watermark = waitForUpdate(t, systemID, lastSkippedUpdateMs, watermark)

	// Empty feed
	fixtures.PublishGTFSRTStringFeedMessage(t, realtimeFeedURL, "")
	watermark = waitForUpdate(t, systemID, lastFailedUpdateMs, watermark)

	// Wait for a successful update
	feedContent = gtfsrt.FeedMessage{
		Header: &gtfsrt.FeedHeader{
			GtfsRealtimeVersion: testutils.Ptr("2.0"),
			Timestamp:           testutils.Ptr(uint64(100)),
		},
	}
	fixtures.PublishGTFSRTFeedMessage(t, realtimeFeedURL, &feedContent)
	waitForUpdate(t, systemID, lastSuccessfulUpdateMs, watermark)

	// Invalid feed content
	fixtures.PublishGTFSRTStringFeedMessage(t, realtimeFeedURL, "not a valid GTFS realtime message")
	waitForUpdate(t, systemID, lastFailedUpdateMs, watermark)
}

type updateField string

const (
	lastSuccessfulUpdateMs updateField = "lastSuccessfulUpdateMs"
	lastSkippedUpdateMs    updateField = "lastSkippedUpdateMs"
	lastFailedUpdateMs     updateField = "lastFailedUpdateMs"
)

func waitForUpdate(t *testing.T, systemID string, field updateField, lowerBound *int64) *int64 {
	transiterClient := fixtures.GetTransiterClient(t)
	for i := 0; i < 40; i++ {
		time.Sleep(10 * time.Millisecond)
		feed, err := transiterClient.GetFeed(systemID, fixtures.GTFSRealtimeFeedID)
		if err != nil {
			t.Fatalf("failed to get feed: %v", err)
		}
		var lastRelevantUpdate *transiterclient.Int64String
		switch field {
		case lastSuccessfulUpdateMs:
			lastRelevantUpdate = feed.LastSuccessfulUpdateMs
		case lastSkippedUpdateMs:
			lastRelevantUpdate = feed.LastSkippedUpdateMs
		case lastFailedUpdateMs:
			lastRelevantUpdate = feed.LastFailedUpdateMs
		}
		if lastRelevantUpdate == nil {
			continue
		}
		if lowerBound == nil || *lowerBound < int64(*lastRelevantUpdate) {
			return testutils.Ptr(int64(*lastRelevantUpdate))
		}
	}
	t.Fatalf("update never appeared")
	return nil
}
