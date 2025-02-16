// Package fixtures provides common test fixtures for Transiter end-to-end tests.
package fixtures

import (
	"fmt"
	"os"
	"strings"
	"testing"

	"github.com/google/uuid"
	sourceserver "github.com/jamespfennell/transiter/tests/endtoend/sourceserver/client"
	"github.com/jamespfennell/transiter/tests/endtoend/testutils"
	"github.com/jamespfennell/transiter/tests/endtoend/transiterclient"
	"google.golang.org/protobuf/proto"

	gtfsrt "github.com/jamespfennell/gtfs/proto"
)

func GTFSStaticDefaultZipBuilder() *testutils.ZipBuilder {
	return testutils.NewZipBuilder().
		AddOrReplaceFile("agency.txt", "agency_name,agency_url,agency_timezone", "AgencyName,AgencyURL,AgencyTimezone").
		AddOrReplaceFile("routes.txt", "route_id,route_type").
		AddOrReplaceFile("stops.txt", "stop_id").
		AddOrReplaceFile("stop_times.txt", "trip_id,stop_id,stop_sequence").
		AddOrReplaceFile("trips.txt", "trip_id,route_id,service_id")
}

const GTFSStaticFeedID = "gtfs_static"
const GTFSRealtimeFeedID = "gtfs_realtime"

const DefaultSystemConfig = `

name: {{.SystemName}}

feeds:

  - id: {{.StaticFeedID}}
    url: "{{.StaticFeedURL}}"
    parser: GTFS_STATIC
    requiredForInstall: true

  - id: {{.RealtimeFeedID}}
    url: {{.RealtimeFeedURL}}
    parser: GTFS_REALTIME
    schedulingPolicy: PERIODIC
    updatePeriodS: {{.RealtimePeriodicUpdatePeriod}}

`

func transiterHost() string {
	if host, ok := os.LookupEnv("TRANSITER_HOST"); ok {
		return host
	}
	return "http://localhost:8082"
}

func sourceServerHostWithinTransiter() string {
	if host, ok := os.LookupEnv("SOURCE_SERVER_HOST_WITHIN_TRANSITER"); ok {
		return host
	}
	return "http://localhost:8090"
}

func GetTransiterClient(t *testing.T) *transiterclient.TransiterClient {
	host := transiterHost()
	client := transiterclient.NewTransiterClient(host)
	if err := client.PingUntilOK(20); err != nil {
		t.Fatalf("failed to ping Transiter: %v", err)
	}
	return client
}

func GetSourceServerClient(t *testing.T) *sourceserver.SourceServerClient {
	client := sourceserver.NewSourceServerClient(sourceServerHostWithinTransiter())
	t.Cleanup(client.Close)
	return client
}

type InstallSystemOptions struct {
	SystemID              string
	Config                string
	RealtimeUpdatePeriodS float64
}

func DefaultInstallSystemOptions(t *testing.T) InstallSystemOptions {
	randomID := uuid.New().String()
	normalizedTestName := strings.ReplaceAll(t.Name(), "/", "_")
	return InstallSystemOptions{
		SystemID:              fmt.Sprintf("%s__%s", normalizedTestName, randomID),
		Config:                DefaultSystemConfig,
		RealtimeUpdatePeriodS: 10 * 60,
	}
}

type InstallSystemOption func(*InstallSystemOptions)

func WithSystemID(systemID string) InstallSystemOption {
	return func(opts *InstallSystemOptions) {
		opts.SystemID = systemID
	}
}

func WithConfig(config string) InstallSystemOption {
	return func(opts *InstallSystemOptions) {
		opts.Config = config
	}
}

func WithRealtimeUpdatePeriodS(periodS float64) InstallSystemOption {
	return func(opts *InstallSystemOptions) {
		opts.RealtimeUpdatePeriodS = periodS
	}
}
func UpdateSystem(t *testing.T, systemID, config, gtfsStaticTxtarZip string) (string, string, string) {
	return InstallSystem(t, gtfsStaticTxtarZip, WithSystemID(systemID), WithConfig(config))
}

func InstallSystem(t *testing.T, gtfsStaticTxtarZip string, opts ...InstallSystemOption) (string, string, string) {
	installOpts := DefaultInstallSystemOptions(t)
	for _, opt := range opts {
		opt(&installOpts)
	}
	sourceServer := GetSourceServerClient(t)

	// Create static feed
	staticFeedURL, err := sourceServer.Create("", "/"+installOpts.SystemID+"/gtfs-static.zip")
	if err != nil {
		t.Fatalf("failed to create static feed: %v", err)
	}
	if err != nil {
		t.Fatalf("failed to zip static feed: %v", err)
	}
	err = sourceServer.Put(staticFeedURL, gtfsStaticTxtarZip)
	if err != nil {
		t.Fatalf("failed to put static feed: %v", err)
	}

	// Create realtime feed
	realtimeFeedURL, err := sourceServer.Create("", "/"+installOpts.SystemID+"/gtfs-realtime.gtfs")
	if err != nil {
		t.Fatalf("failed to create realtime feed: %v", err)
	}

	config := testutils.CreateConfigFromTemplate(installOpts.Config, map[string]any{
		"SystemName":                   "Test System",
		"StaticFeedID":                 GTFSStaticFeedID,
		"StaticFeedURL":                fmt.Sprintf("%s/%s", sourceServerHostWithinTransiter(), staticFeedURL),
		"RealtimeFeedID":               GTFSRealtimeFeedID,
		"RealtimeFeedURL":              fmt.Sprintf("%s/%s", sourceServerHostWithinTransiter(), realtimeFeedURL),
		"RealtimePeriodicUpdatePeriod": installOpts.RealtimeUpdatePeriodS,
	})
	transiter := GetTransiterClient(t)
	err = transiter.InstallSystem(installOpts.SystemID, config)
	if err != nil {
		t.Fatalf("failed to install system: %v", err)
	}
	t.Cleanup(func() {
		transiter.DeleteSystem(installOpts.SystemID)
	})
	return installOpts.SystemID, staticFeedURL, realtimeFeedURL
}

func PublishGTFSStaticFeedAndUpdate(t *testing.T, systemID string, staticFeedURL string, content string) {
	sourceServerClient := GetSourceServerClient(t)
	err := sourceServerClient.Put(staticFeedURL, content)
	if err != nil {
		t.Fatalf("failed to put static feed: %v", err)
	}
	transiterClient := GetTransiterClient(t)
	err = transiterClient.PerformFeedUpdate(systemID, GTFSStaticFeedID)
	if err != nil {
		t.Fatalf("failed to perform feed update: %v", err)
	}
}

func PublicGTFSStaticFeed(t *testing.T, staticFeedURL string, content string) {
	sourceServerClient := GetSourceServerClient(t)
	err := sourceServerClient.Put(staticFeedURL, content)
	if err != nil {
		t.Fatalf("failed to put static feed: %v", err)
	}
}

func PublishGTFSRTMessageAndUpdate(t *testing.T, systemID string, realtimeFeedURL string, message *gtfsrt.FeedMessage) {
	PublishGTFSRTFeedMessage(t, realtimeFeedURL, message)
	transiterClient := GetTransiterClient(t)
	err := transiterClient.PerformFeedUpdate(systemID, GTFSRealtimeFeedID)
	if err != nil {
		t.Fatalf("failed to perform feed update: %v", err)
	}
}

func PublishGTFSRTFeedMessage(t *testing.T, realtimeFeedURL string, message *gtfsrt.FeedMessage) {
	sourceServerClient := GetSourceServerClient(t)
	serializedMessage, err := proto.Marshal(message)
	if err != nil {
		t.Fatalf("failed to marshal message: %v", err)
	}
	err = sourceServerClient.Put(realtimeFeedURL, string(serializedMessage))
	if err != nil {
		t.Fatalf("failed to put realtime feed: %v", err)
	}
}

func PublishGTFSRTStringFeedMessage(t *testing.T, realtimeFeedURL string, message string) {
	sourceServerClient := GetSourceServerClient(t)
	err := sourceServerClient.Put(realtimeFeedURL, message)
	if err != nil {
		t.Fatalf("failed to put realtime feed: %v", err)
	}
}
