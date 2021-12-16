package stoptree

import (
	"context"
	"database/sql"
	"testing"

	tdb "github.com/jamespfennell/transiter/internal/gen/db"
)

type Querier struct {
	tdb.Querier
}

func (q Querier) ListStopsInStopTree(ctx context.Context, basePk int32) ([]tdb.Stop, error) {
	return []tdb.Stop{
		{
			Pk:           1,
			ParentStopPk: sql.NullInt32{Valid: true, Int32: 3},
		},
		{
			Pk:           2,
			ParentStopPk: sql.NullInt32{Valid: true, Int32: 3},
		},
		{
			Pk: 3,
		},
	}, nil
}

func Test_Descendent(t *testing.T) {
	stopTree, _ := NewStopTree(context.Background(), Querier{}, 3)
	actual := stopTree.DescendentPks()
	expected := []int32{1, 2, 3}
	if !compareList(actual, expected) {
		t.Errorf("Actual %v != expected %v", actual, expected)
	}
}

func compareList(a, b []int32) bool {
	if len(a) != len(b) {
		return false
	}
	aMap := map[int32]bool{}
	for _, aElem := range a {
		aMap[aElem] = true
	}
	for _, bElem := range b {
		if !aMap[bElem] {
			return false
		}
	}
	return true
}
