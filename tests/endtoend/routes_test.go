package endtoend

import (
	"fmt"
	"testing"

	"github.com/jamespfennell/transiter/tests/endtoend/fixtures"
	"github.com/jamespfennell/transiter/tests/endtoend/testutils"
	"github.com/jamespfennell/transiter/tests/endtoend/transiterclient"
)

var RoutesGTFSStaticZip = fixtures.GTFSStaticDefaultZipBuilder().AddOrReplaceFile(
	"routes.txt",
	"route_id,route_color,route_text_color,route_short_name,route_long_name,route_desc,route_type,route_url,route_sort_order,continuous_pickup,continuous_drop_off",
	"RouteID1,RouteColor1,RouteTextColor1,RouteShortName1,RouteLongName1,RouteDesc1,1,RouteUrl1,50,2,3",
	"RouteID2,RouteColor2,RouteTextColor2,RouteShortName2,RouteLongName2,RouteDesc2,2,RouteUrl2,25,0,1",
).MustBuild()

var UpdatedRoutesGTFSStaticZip = fixtures.GTFSStaticDefaultZipBuilder().AddOrReplaceFile(
	"routes.txt",
	"route_id,route_color,route_text_color,route_short_name,route_long_name,route_desc,route_type,route_url,route_sort_order,continuous_pickup,continuous_drop_off",
	"RouteID1,RouteColor3,RouteTextColor3,RouteShortName3,RouteLongName3,RouteDesc3,3,RouteUrl3,75,3,2",
).MustBuild()

func TestRoutes(t *testing.T) {
	for _, tc := range []struct {
		name string
		test func(t *testing.T, client *transiterclient.TransiterClient, systemID string, staticFeedURL string)
	}{
		{
			name: "list and get route",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string, staticFeedURL string) {
				route1 := transiterclient.Route{
					ID:                "RouteID1",
					URL:               "RouteUrl1",
					Color:             "RouteColor1",
					TextColor:         "RouteTextColor1",
					ShortName:         "RouteShortName1",
					LongName:          "RouteLongName1",
					Description:       "RouteDesc1",
					SortOrder:         50,
					ContinuousPickup:  "PHONE_AGENCY",
					ContinuousDropOff: "COORDINATE_WITH_DRIVER",
					Type:              "SUBWAY",
					ServiceMaps:       []transiterclient.ServiceMapInRoute{},
					Alerts:            []transiterclient.AlertReference{},
				}
				route2 := transiterclient.Route{
					ID:                "RouteID2",
					URL:               "RouteUrl2",
					Color:             "RouteColor2",
					TextColor:         "RouteTextColor2",
					ShortName:         "RouteShortName2",
					LongName:          "RouteLongName2",
					Description:       "RouteDesc2",
					SortOrder:         25,
					ContinuousPickup:  "ALLOWED",
					ContinuousDropOff: "NOT_ALLOWED",
					Type:              "RAIL",
					ServiceMaps:       []transiterclient.ServiceMapInRoute{},
					Alerts:            []transiterclient.AlertReference{},
				}

				gotSystem, err := client.GetSystem(systemID)
				if err != nil {
					t.Fatalf("failed to get system: %v", err)
				}
				testutils.AssertEqual(t, gotSystem.Routes, &transiterclient.ChildResources{
					Count: 2,
					Path:  fmt.Sprintf("systems/%s/routes", systemID),
				})

				params := []transiterclient.QueryParam{
					{Key: "skip_service_maps", Value: "true"},
				}
				gotListRoutes, err := client.ListRoutes(systemID, params...)
				if err != nil {
					t.Fatalf("failed to list routes: %v", err)
				}
				testutils.AssertEqual(t, gotListRoutes.Routes, []transiterclient.Route{route1, route2})

				gotRoute, err := client.GetRoute(systemID, "RouteID1", params...)
				if err != nil {
					t.Fatalf("failed to get route: %v", err)
				}
				testutils.AssertEqual(t, gotRoute, &route1)
			},
		},
		{
			name: "update",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string, staticFeedURL string) {
				updatedRoute := transiterclient.Route{
					ID:                "RouteID1",
					URL:               "RouteUrl3",
					Color:             "RouteColor3",
					TextColor:         "RouteTextColor3",
					ShortName:         "RouteShortName3",
					LongName:          "RouteLongName3",
					Description:       "RouteDesc3",
					SortOrder:         75,
					ContinuousPickup:  "COORDINATE_WITH_DRIVER",
					ContinuousDropOff: "PHONE_AGENCY",
					Type:              "BUS",
					ServiceMaps:       []transiterclient.ServiceMapInRoute{},
					Alerts:            []transiterclient.AlertReference{},
				}
				fixtures.PublishGTFSStaticFeedAndUpdate(t, systemID, staticFeedURL, UpdatedRoutesGTFSStaticZip)
				params := []transiterclient.QueryParam{
					{Key: "skip_service_maps", Value: "true"},
				}
				gotListRoutes, err := client.ListRoutes(systemID, params...)
				if err != nil {
					t.Fatalf("failed to list routes: %v", err)
				}
				testutils.AssertEqual(t, gotListRoutes.Routes, []transiterclient.Route{updatedRoute})
			},
		},
	} {
		testName := fmt.Sprintf("%s/%s", "routes", tc.name)
		t.Run(testName, func(t *testing.T) {
			systemID, staticFeedURL, _ := fixtures.InstallSystem(t, RoutesGTFSStaticZip)
			transiterClient := fixtures.GetTransiterClient(t)
			tc.test(t, transiterClient, systemID, staticFeedURL)
		})
	}

}
