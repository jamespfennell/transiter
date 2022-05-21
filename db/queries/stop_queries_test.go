package queries

import (
	"context"
	"fmt"
	"reflect"
	"testing"

	"github.com/jackc/pgtype"
	"github.com/jamespfennell/gtfs"
	"github.com/jamespfennell/transiter/internal/convert"
	"github.com/jamespfennell/transiter/internal/db/dbtesting"
	"github.com/jamespfennell/transiter/internal/db/dbwrappers"
	"github.com/jamespfennell/transiter/internal/gen/db"
)

func TestMapStopIDToStationPk(t *testing.T) {
	type insertStopFunc func(string, gtfs.StopType, *int64) int64
	for _, tc := range []struct {
		name     string
		wantFunc func(insertStop insertStopFunc) map[string]int64
	}{
		{
			name: "platform and station",
			wantFunc: func(insertStop insertStopFunc) map[string]int64 {
				stationPk := insertStop("station", gtfs.Station, nil)
				platformPk := insertStop("platform", gtfs.Platform, &stationPk)
				insertStop("boarding", gtfs.BoardingArea, &platformPk)
				return map[string]int64{
					"station":  stationPk,
					"platform": stationPk,
					"boarding": stationPk,
				}
			},
		},
		{
			name: "platform with no parent station",
			wantFunc: func(insertStop insertStopFunc) map[string]int64 {
				platformPk := insertStop("platform", gtfs.Platform, nil)
				return map[string]int64{
					"platform": platformPk,
				}
			},
		},
		{
			name: "platform with grouped station",
			wantFunc: func(insertStop insertStopFunc) map[string]int64 {
				stationPk := insertStop("station", gtfs.GroupedStation, nil)
				insertStop("platform", gtfs.Platform, &stationPk)
				return map[string]int64{
					"station":  stationPk,
					"platform": stationPk,
				}
			},
		},
		{
			name: "two stations",
			wantFunc: func(insertStop insertStopFunc) map[string]int64 {
				parentPk := insertStop("parent", gtfs.Station, nil)
				childPk := insertStop("child", gtfs.Station, &parentPk)
				return map[string]int64{
					"parent": parentPk,
					"child":  childPk,
				}
			},
		},
		{
			name: "station and grouped station",
			wantFunc: func(insertStop insertStopFunc) map[string]int64 {
				parentPk := insertStop("parent", gtfs.GroupedStation, nil)
				childPk := insertStop("child", gtfs.Station, &parentPk)
				return map[string]int64{
					"parent": parentPk,
					"child":  childPk,
				}
			},
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			q := dbtesting.NewQuerier(t)
			systemPk := q.System1().Pk
			updatePk := q.Update1Pk()
			insertStop := func(id string, t gtfs.StopType, parentPk *int64) int64 {
				pk, err := q.InsertStop(context.Background(), db.InsertStopParams{
					ID:        id,
					SystemPk:  systemPk,
					SourcePk:  updatePk,
					Type:      t.String(),
					Longitude: pgtype.Numeric{Status: pgtype.Null},
					Latitude:  pgtype.Numeric{Status: pgtype.Null},
				})
				q.AssertNilErr(err, fmt.Sprintf("insert stop %q", id))
				err = q.UpdateStopParent(context.Background(), db.UpdateStopParentParams{
					Pk:           pk,
					ParentStopPk: convert.NullInt64(parentPk),
				})
				q.AssertNilErr(err, fmt.Sprintf("update parent of stop %q", id))
				return pk
			}
			want := tc.wantFunc(insertStop)
			got, err := dbwrappers.MapStopIDToStationPk(context.Background(), q, systemPk)
			if err != nil {
				t.Fatalf("MapStopIDToStationPk() err = %+v, want err = nil", err)
			}
			if !reflect.DeepEqual(got, want) {
				t.Fatalf("MapStopIDToStationPk()\n got = %+v\nwant = %+v", got, want)
			}
		})
	}
}
