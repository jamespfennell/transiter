package static

import (
	"context"
	"math"
	"math/big"
	"testing"

	"github.com/google/go-cmp/cmp"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jamespfennell/gtfs"
	"github.com/jamespfennell/transiter/internal/convert"
	"github.com/jamespfennell/transiter/internal/db/dbtesting"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/update/common"
)

const (
	routeID1 = "routeID1"
	stopID1  = "stopID1"
	stopID2  = "stopID2"
)

func TestUpdate(t *testing.T) {
	for _, tc := range []struct {
		name                 string
		updates              []*gtfs.Static
		wantStops            []db.Stop
		wantStopIDToParentID map[string]string
	}{
		{
			name: "stop added",
			updates: []*gtfs.Static{
				{
					Stops: []gtfs.Stop{
						{
							Id:                 stopID1,
							Code:               "1",
							Name:               "2",
							Description:        "3",
							ZoneId:             "4",
							Longitude:          ptr(float64(5.5)),
							Latitude:           ptr(float64(6.6)),
							Url:                "7",
							Type:               gtfs.StopType_Station,
							Timezone:           "8",
							WheelchairBoarding: gtfs.WheelchairBoarding_NotPossible,
							PlatformCode:       "9",
						},
					},
				},
			},
			wantStops: []db.Stop{
				{
					ID:                 stopID1,
					Code:               dbString("1"),
					Name:               dbString("2"),
					Description:        dbString("3"),
					ZoneID:             dbString("4"),
					Longitude:          convert.Gps(ptr(float64(5.5))),
					Latitude:           convert.Gps(ptr(float64(6.6))),
					Url:                dbString("7"),
					Type:               gtfs.StopType_Station.String(),
					Timezone:           dbString("8"),
					WheelchairBoarding: pgtype.Bool{Valid: true, Bool: false},
					PlatformCode:       dbString("9"),
				},
			},
		},
		{
			name: "stop deleted",
			updates: []*gtfs.Static{
				{
					Stops: []gtfs.Stop{
						{
							Id:   stopID1,
							Type: gtfs.StopType_Station,
						},
					},
				},
				{},
			},
			wantStops: nil,
		},
		{
			name: "stop parent and child",
			updates: []*gtfs.Static{
				{
					Stops: []gtfs.Stop{
						{
							Id:   stopID1,
							Type: gtfs.StopType_Station,
						},
						{
							Id:     stopID2,
							Type:   gtfs.StopType_Platform,
							Parent: &gtfs.Stop{Id: stopID1},
						},
					},
				},
			},
			wantStops: []db.Stop{
				{
					ID:   stopID1,
					Type: gtfs.StopType_Station.String(),
				},
				{
					ID:   stopID2,
					Type: gtfs.StopType_Platform.String(),
				},
			},
			wantStopIDToParentID: map[string]string{
				stopID2: stopID1,
			},
		},
		{
			name: "stop parent deleted",
			updates: []*gtfs.Static{
				{
					Stops: []gtfs.Stop{
						{
							Id:   stopID1,
							Type: gtfs.StopType_Station,
						},
						{
							Id:     stopID2,
							Type:   gtfs.StopType_Platform,
							Parent: &gtfs.Stop{Id: stopID1},
						},
					},
				},
				{
					Stops: []gtfs.Stop{
						{
							Id:   stopID2,
							Type: gtfs.StopType_Platform,
						},
					},
				},
			},
			wantStops: []db.Stop{
				{
					ID:   stopID2,
					Type: gtfs.StopType_Platform.String(),
				},
			},
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			querier := dbtesting.NewQuerier(t)
			system := querier.NewSystem("system")
			feed := system.NewFeed("feedID")

			ctx := context.Background()
			updateCtx := common.UpdateContext{
				Querier:  querier,
				SystemPk: system.Data.Pk,
				FeedPk:   feed.Data.Pk,
				FeedConfig: &api.FeedConfig{
					Parser: "GTFS_STATIC",
				},
			}

			for i, update := range tc.updates {
				err := Update(ctx, updateCtx, update)
				if err != nil {
					t.Fatalf("Update(update %d) got = %v, want = <nil>", err, i)
				}
			}

			gotStops, stopIDToParentID := listStops(ctx, t, querier, updateCtx.SystemPk)
			if diff := cmp.Diff(gotStops, tc.wantStops, cmp.Comparer(compareBigInt)); diff != "" {
				t.Errorf("ListStops() got = %v, want = %v, diff = %s", gotStops, tc.wantStops, diff)
			}
			if tc.wantStopIDToParentID == nil {
				tc.wantStopIDToParentID = map[string]string{}
			}
			if diff := cmp.Diff(stopIDToParentID, tc.wantStopIDToParentID); diff != "" {
				t.Errorf("ListStops() stopIDToParentID = %v, want = %v, diff = %s", stopIDToParentID, tc.wantStopIDToParentID, diff)
			}
		})
	}
}

func listStops(ctx context.Context, t *testing.T, querier db.Querier, systemPk int64) ([]db.Stop, map[string]string) {
	stops, err := querier.ListStops(ctx, db.ListStopsParams{SystemPk: systemPk, NumStops: math.MaxInt32})
	if err != nil {
		t.Errorf("ListStops() err = %v, want = nil", err)
	}
	stopPkToParentPk := map[int64]int64{}
	pkToID := map[int64]string{}
	for i := range stops {
		stop := &stops[i]
		if stop.ParentStopPk.Valid {
			stopPkToParentPk[stop.Pk] = stop.ParentStopPk.Int64
		}
		pkToID[stop.Pk] = stop.ID
		stop.Pk = 0
		stop.ParentStopPk = pgtype.Int8{}
		stop.FeedPk = 0
		stop.SystemPk = 0
	}
	stopIDToParentID := map[string]string{}
	for stopPk, parentPk := range stopPkToParentPk {
		stopIDToParentID[pkToID[stopPk]] = pkToID[parentPk]
	}
	return stops, stopIDToParentID
}

func ptr[T any](t T) *T {
	return &t
}

func dbString(s string) pgtype.Text {
	return pgtype.Text{Valid: true, String: s}
}

func compareBigInt(a, b *big.Int) bool {
	return a.Cmp(b) == 0
}
