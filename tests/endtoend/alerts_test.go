package endtoend

import (
	"fmt"
	"testing"
	"time"

	gtfsrt "github.com/jamespfennell/gtfs/proto"
	"github.com/jamespfennell/transiter/tests/endtoend/fixtures"
	"github.com/jamespfennell/transiter/tests/endtoend/testutils"
	"github.com/jamespfennell/transiter/tests/endtoend/transiterclient"
)

const AlertID = "alert_id"
const AgencyID = "agency_id"
const RouteID = "route_id"
const StopID = "stop_id"
const TripID = "trip_id"

const OneDayInSeconds = 60 * 60 * 24

var Timestamp1 = time.Now().Unix() - OneDayInSeconds
var Timestamp2 = time.Now().Unix() + OneDayInSeconds

var TestAlert = transiterclient.Alert{
	ID:     "alert_id",
	Cause:  "STRIKE",
	Effect: "MODIFIED_SERVICE",
	CurrentActivePeriod: transiterclient.AlertActivePeriod{
		StartsAt: transiterclient.Int64String(Timestamp1),
		EndsAt:   transiterclient.Int64String(Timestamp2),
	},
	AllActivePeriods: []transiterclient.AlertActivePeriod{
		{
			StartsAt: transiterclient.Int64String(Timestamp1),
			EndsAt:   transiterclient.Int64String(Timestamp2),
		},
	},
	Header: []transiterclient.AlertText{
		{
			Text:     "Advertencia",
			Language: "es",
		},
	},
	Description: []transiterclient.AlertText{
		{
			Text: "Description",
		},
	},
	URL: []transiterclient.AlertText{
		{
			Text:     "URL",
			Language: "en",
		},
	},
}

var TestAlertReference = transiterclient.AlertReference{
	ID:     TestAlert.ID,
	Cause:  TestAlert.Cause,
	Effect: TestAlert.Effect,
}

var AlertsGTFSStaticZip = fixtures.GTFSStaticDefaultZipBuilder().AddOrReplaceFile(
	"agency.txt",
	"agency_id,agency_name,agency_url,agency_timezone",
	fmt.Sprintf("%s,AgencyName,AgencyURL,AgencyTimezone", AgencyID),
).AddOrReplaceFile(
	"routes.txt",
	"route_id,route_type",
	fmt.Sprintf("%s,3", RouteID),
).AddOrReplaceFile(
	"stops.txt",
	"stop_id",
	StopID,
).MustBuild()

func TestAlerts(t *testing.T) {

	for _, tc := range []struct {
		name string
		test func(t *testing.T, client *transiterclient.TransiterClient, systemID string)
	}{
		{
			name: "list alerts",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string) {
				gotListAlerts, err := client.ListAlerts(systemID)
				if err != nil {
					t.Fatalf("failed to list alerts: %v", err)
				}
				testutils.AssertEqual(t, gotListAlerts.Alerts, []transiterclient.Alert{TestAlert})
			},
		},
		{
			name: "get alert",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string) {
				gotAlert, err := client.GetAlert(systemID, AlertID)
				if err != nil {
					t.Fatalf("failed to get alert: %v", err)
				}
				testutils.AssertEqual(t, *gotAlert, TestAlert)
			},
		},
		{
			name: "alert appears in list agencies",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string) {
				gotListAgencies, err := client.ListAgencies(systemID)
				if err != nil {
					t.Fatalf("failed to list agencies: %v", err)
				}
				testutils.AssertEqual(t, gotListAgencies.Agencies[0].Alerts, []transiterclient.AlertReference{TestAlertReference})
			},
		},
		{
			name: "alert appears in get agency",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string) {
				gotAgency, err := client.GetAgency(systemID, AgencyID)
				if err != nil {
					t.Fatalf("failed to get agency: %v", err)
				}
				testutils.AssertEqual(t, gotAgency.Alerts, []transiterclient.AlertReference{TestAlertReference})
			},
		},
		{
			name: "alert appears in list routes",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string) {
				gotListRoutes, err := client.ListRoutes(systemID)
				if err != nil {
					t.Fatalf("failed to list routes: %v", err)
				}
				testutils.AssertEqual(t, gotListRoutes.Routes[0].Alerts, []transiterclient.AlertReference{TestAlertReference})
			},
		},
		{
			name: "alert appears in get route",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string) {
				gotRoute, err := client.GetRoute(systemID, RouteID)
				if err != nil {
					t.Fatalf("failed to get route: %v", err)
				}
				testutils.AssertEqual(t, gotRoute.Alerts, []transiterclient.AlertReference{TestAlertReference})
			},
		},
		{
			name: "alert appears in list stops",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string) {
				gotListStops, err := client.ListStops(systemID)
				if err != nil {
					t.Fatalf("failed to list stops: %v", err)
				}
				testutils.AssertEqual(t, gotListStops.Stops[0].Alerts, []transiterclient.AlertReference{TestAlertReference})
			},
		},
		{
			name: "alert appears in get stop",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string) {
				gotStop, err := client.GetStop(systemID, StopID)
				if err != nil {
					t.Fatalf("failed to get stop: %v", err)
				}
				testutils.AssertEqual(t, gotStop.Alerts, []transiterclient.AlertReference{TestAlertReference})
			},
		},
		{
			name: "alert appears in list trips",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string) {
				gotListTrips, err := client.ListTrips(systemID, RouteID)
				if err != nil {
					t.Fatalf("failed to list trips: %v", err)
				}
				testutils.AssertEqual(t, gotListTrips.Trips[0].Alerts, []transiterclient.AlertReference{TestAlertReference})
			},
		},
		{
			name: "alert appears in get trip",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string) {
				gotTrip, err := client.GetTrip(systemID, RouteID, TripID)
				if err != nil {
					t.Fatalf("failed to get trip: %v", err)
				}
				testutils.AssertEqual(t, gotTrip.Alerts, []transiterclient.AlertReference{TestAlertReference})
			},
		},
	} {
		testName := fmt.Sprintf("%s/%s", "alerts", tc.name)
		t.Run(testName, func(t *testing.T) {
			systemID := installSystemAndPublishAlert(t)
			transiterClient := fixtures.GetTransiterClient(t)
			tc.test(t, transiterClient, systemID)
		})
	}

}

func installSystemAndPublishAlert(t *testing.T) string {
	systemID, _, realtimeFeedURL := fixtures.InstallSystem(t, AlertsGTFSStaticZip)
	message := gtfsrt.FeedMessage{
		Header: &gtfsrt.FeedHeader{
			GtfsRealtimeVersion: testutils.Ptr("2.0"),
			Timestamp:           testutils.Ptr(uint64(time.Now().Unix())),
		},
		Entity: []*gtfsrt.FeedEntity{
			{
				Id: testutils.Ptr(TripID),
				TripUpdate: &gtfsrt.TripUpdate{
					Trip: &gtfsrt.TripDescriptor{
						TripId:  testutils.Ptr(TripID),
						RouteId: testutils.Ptr(RouteID),
					},
				},
			},
			{
				Id: testutils.Ptr(AlertID),
				Alert: &gtfsrt.Alert{
					ActivePeriod: []*gtfsrt.TimeRange{
						{
							Start: testutils.Ptr(uint64(Timestamp1)),
							End:   testutils.Ptr(uint64(Timestamp2)),
						},
					},
					HeaderText: &gtfsrt.TranslatedString{
						Translation: []*gtfsrt.TranslatedString_Translation{
							{
								Text:     testutils.Ptr("Advertencia"),
								Language: testutils.Ptr("es"),
							},
						},
					},
					DescriptionText: &gtfsrt.TranslatedString{
						Translation: []*gtfsrt.TranslatedString_Translation{
							{
								Text: testutils.Ptr("Description"),
							},
						},
					},
					Url: &gtfsrt.TranslatedString{
						Translation: []*gtfsrt.TranslatedString_Translation{
							{
								Text:     testutils.Ptr("URL"),
								Language: testutils.Ptr("en"),
							},
						},
					},
					InformedEntity: []*gtfsrt.EntitySelector{
						{
							AgencyId: testutils.Ptr(AgencyID),
							RouteId:  testutils.Ptr(RouteID),
							StopId:   testutils.Ptr(StopID),
							Trip: &gtfsrt.TripDescriptor{
								TripId: testutils.Ptr(TripID),
							},
						},
					},
					Cause:  testutils.Ptr(gtfsrt.Alert_STRIKE),
					Effect: testutils.Ptr(gtfsrt.Alert_MODIFIED_SERVICE),
				},
			},
		},
	}
	fixtures.PublishGTFSRTMessageAndUpdate(t, systemID, realtimeFeedURL, &message)
	return systemID
}
