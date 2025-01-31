package endtoend

import (
	"fmt"
	"testing"

	gtfsrt "github.com/jamespfennell/gtfs/proto"
	"github.com/jamespfennell/transiter/tests/endtoend/fixtures"
	"github.com/jamespfennell/transiter/tests/endtoend/testutils"
	"github.com/jamespfennell/transiter/tests/endtoend/transiterclient"
)

var Shape1 = transiterclient.Shape{
	ID: "shape_1",
	Points: []transiterclient.ShapePoint{
		{Latitude: 100, Longitude: 200},
		{Latitude: 150, Longitude: 250},
		{Latitude: 200, Longitude: 300},
	},
}

var Shape2 = transiterclient.Shape{
	ID: "shape_2",
	Points: []transiterclient.ShapePoint{
		{Latitude: 200, Longitude: 300},
		{Latitude: 250, Longitude: 350},
		{Latitude: 300, Longitude: 400},
	},
}

var Shape3 = transiterclient.Shape{
	ID: "shape_3",
	Points: []transiterclient.ShapePoint{
		{Latitude: -10, Longitude: -20},
	},
}

var ShapesGTFSStaticZip = fixtures.GTFSStaticDefaultZipBuilder().AddOrReplaceFile(
	"routes.txt",
	"route_id,route_type",
	fmt.Sprintf("%s,2", RouteID),
).AddOrReplaceFile(
	"shapes.txt",
	"shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence",
	fmt.Sprintf("%s,100,200,0", Shape1.ID),
	fmt.Sprintf("%s,150,250,1", Shape1.ID),
	fmt.Sprintf("%s,200,300,2", Shape1.ID),
	fmt.Sprintf("%s,200,300,0", Shape2.ID),
	fmt.Sprintf("%s,250,350,1", Shape2.ID),
	fmt.Sprintf("%s,300,400,2", Shape2.ID),
	fmt.Sprintf("%s,-10,-20,0", Shape3.ID),
).AddOrReplaceFile(
	"calendar.txt",
	"service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date",
	"Weekday,1,1,1,1,1,0,0,20180101,20181231",
).AddOrReplaceFile(
	"trips.txt",
	"route_id,service_id,trip_id,direction_id,shape_id",
	fmt.Sprintf("%s,Weekday,%s,1,%s", RouteID, TripID, Shape1.ID),
).MustBuild()

func TestShapes(t *testing.T) {
	for _, tc := range []struct {
		name string
		test func(t *testing.T, client *transiterclient.TransiterClient, systemID string, realtimeFeedURL string)
	}{
		{
			name: "list shapes",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string, realtimeFeedURL string) {
				gotListShapes, err := client.ListShapes(systemID)
				if err != nil {
					t.Fatalf("failed to list shapes: %v", err)
				}
				testutils.AssertEqual(t, gotListShapes.Shapes, []transiterclient.Shape{Shape1, Shape2, Shape3})
			},
		},
		{
			name: "list shapes with pagination",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string, realtimeFeedURL string) {
				gotListShapes, err := client.ListShapes(systemID, transiterclient.QueryParam{
					Key:   "limit",
					Value: "2",
				})
				if err != nil {
					t.Fatalf("failed to list shapes with pagination: %v", err)
				}
				testutils.AssertEqual(t, gotListShapes, &transiterclient.ListShapesResponse{
					Shapes: []transiterclient.Shape{Shape1, Shape2},
					NextID: testutils.Ptr(Shape3.ID),
				})

				gotListShapes, err = client.ListShapes(systemID,
					transiterclient.QueryParam{Key: "limit", Value: "2"},
					transiterclient.QueryParam{Key: "first_id", Value: *gotListShapes.NextID},
				)
				if err != nil {
					t.Fatalf("failed to list shapes with pagination (second page): %v", err)
				}
				testutils.AssertEqual(t, gotListShapes, &transiterclient.ListShapesResponse{
					Shapes: []transiterclient.Shape{Shape3},
					NextID: nil,
				})
			},
		},
		{
			name: "list shapes with filtering",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string, realtimeFeedURL string) {
				gotListShapes, err := client.ListShapes(systemID,
					transiterclient.QueryParam{Key: "filter_by_id", Value: "true"},
					transiterclient.QueryParam{Key: "id[]", Value: Shape1.ID},
					transiterclient.QueryParam{Key: "id[]", Value: Shape3.ID},
				)
				if err != nil {
					t.Fatalf("failed to list shapes with filtering: %v", err)
				}
				testutils.AssertEqual(t, gotListShapes.Shapes, []transiterclient.Shape{Shape1, Shape3})
			},
		},
		{
			name: "get shape",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string, realtimeFeedURL string) {
				for _, wantShape := range []transiterclient.Shape{Shape1, Shape2, Shape3} {
					gotShape, err := client.GetShape(systemID, wantShape.ID)
					if err != nil {
						t.Fatalf("failed to get shape %s: %v", wantShape.ID, err)
					}
					testutils.AssertEqual(t, gotShape, &wantShape)
				}
			},
		},
		{
			name: "trip view",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string, realtimeFeedURL string) {
				message := gtfsrt.FeedMessage{
					Header: &gtfsrt.FeedHeader{
						GtfsRealtimeVersion: testutils.Ptr("2.0"),
						Timestamp:           testutils.Ptr(uint64(0)),
					},
					Entity: []*gtfsrt.FeedEntity{
						{
							Id: testutils.Ptr("trip_update_1"),
							TripUpdate: &gtfsrt.TripUpdate{
								Trip: &gtfsrt.TripDescriptor{
									TripId:      testutils.Ptr(TripID),
									RouteId:     testutils.Ptr(RouteID),
									DirectionId: testutils.Ptr(uint32(1)),
								},
							},
						},
					},
				}
				fixtures.PublishGTFSRTMessageAndUpdate(t, systemID, realtimeFeedURL, &message)

				gotTrip, err := client.GetTrip(systemID, RouteID, TripID)
				if err != nil {
					t.Fatalf("failed to get trip: %v", err)
				}
				testutils.AssertEqual(t, gotTrip.Shape, &transiterclient.ShapeReference{ID: Shape1.ID})
			},
		},
	} {
		testName := fmt.Sprintf("%s/%s", "shapes", tc.name)
		t.Run(testName, func(t *testing.T) {
			systemID, _, realtimeFeedURL := fixtures.InstallSystem(t, ShapesGTFSStaticZip)
			transiterClient := fixtures.GetTransiterClient(t)
			tc.test(t, transiterClient, systemID, realtimeFeedURL)
		})
	}
}
