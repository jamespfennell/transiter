package queries

import (
	"context"
	"fmt"
	"reflect"
	"testing"

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
	} {
		t.Run(tc.name, func(t *testing.T) {
			q := dbtesting.NewQuerier(t)
			system := q.NewSystem("system1")
			insertStop := func(id string, t gtfs.StopType, parentPk *int64) int64 {
				stop := system.NewStop(id, db.InsertStopParams{
					Type: t.String(),
				})
				err := q.UpdateStopParent(context.Background(), db.UpdateStopParentParams{
					Pk:           stop.Pk,
					ParentStopPk: convert.NullInt64(parentPk),
				})
				q.AssertNilErr(err, fmt.Sprintf("update parent of stop %q", id))
				return stop.Pk
			}
			want := tc.wantFunc(insertStop)
			got, err := dbwrappers.MapStopIDToStationPk(context.Background(), q, system.Data.Pk)
			if err != nil {
				t.Fatalf("MapStopIDToStationPk() err = %+v, want err = nil", err)
			}
			if !reflect.DeepEqual(got, want) {
				t.Fatalf("MapStopIDToStationPk()\n got = %+v\nwant = %+v", got, want)
			}
		})
	}
}
