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
				stationPk := insertStop("station", gtfs.StopType_Station, nil)
				platformPk := insertStop("platform", gtfs.StopType_Platform, &stationPk)
				insertStop("boarding", gtfs.StopType_BoardingArea, &platformPk)
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
				platformPk := insertStop("platform", gtfs.StopType_Platform, nil)
				return map[string]int64{
					"platform": platformPk,
				}
			},
		},
		{
			name: "two stations",
			wantFunc: func(insertStop insertStopFunc) map[string]int64 {
				parentPk := insertStop("parent", gtfs.StopType_Station, nil)
				childPk := insertStop("child", gtfs.StopType_Station, &parentPk)
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
				err := q.UpdateStop_Parent(context.Background(), db.UpdateStop_ParentParams{
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

func TestMapStopPkToDescendentPks(t *testing.T) {
	q := dbtesting.NewQuerier(t)
	system := q.NewSystem("system1")
	insertStop := func(id string, t gtfs.StopType, parentPk *int64) int64 {
		stop := system.NewStop(id, db.InsertStopParams{
			Type: t.String(),
		})
		err := q.UpdateStop_Parent(context.Background(), db.UpdateStop_ParentParams{
			Pk:           stop.Pk,
			ParentStopPk: convert.NullInt64(parentPk),
		})
		q.AssertNilErr(err, fmt.Sprintf("update parent of stop %q", id))
		return stop.Pk
	}

	gen1 := insertStop("gen1", gtfs.StopType_Station, nil)
	_ = insertStop("gen2A", gtfs.StopType_Platform, &gen1)
	gen2B := insertStop("gen2B", gtfs.StopType_Platform, &gen1)
	gen3A := insertStop("gen3A", gtfs.StopType_Platform, &gen2B)
	gen3B := insertStop("gen3B", gtfs.StopType_Platform, &gen2B)
	gen4 := insertStop("gen4", gtfs.StopType_Platform, &gen3B)

	want := map[int64]map[int64]bool{
		gen2B: {gen2B: true, gen3A: true, gen3B: true, gen4: true},
		gen3B: {gen3B: true, gen4: true},
	}

	got, err := dbwrappers.MapStopPkToDescendentPks(context.Background(), q, []int64{gen2B, gen3B})
	if err != nil {
		t.Fatalf("MapStopPkToDescendentPks() err = %+v, want err = nil", err)
	}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("MapStopPkToDescendentPks()\n got = %+v\nwant = %+v", got, want)
	}
}
