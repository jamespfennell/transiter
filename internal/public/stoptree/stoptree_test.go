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

func (q Querier) ListStopsInStopTree(ctx context.Context, basePk int64) ([]tdb.Stop, error) {
	return []tdb.Stop{
		{
			Pk:           1,
			ParentStopPk: sql.NullInt64{Valid: true, Int64: 3},
		},
		{
			Pk:           2,
			ParentStopPk: sql.NullInt64{Valid: true, Int64: 3},
		},
		{
			Pk: 3,
		},
	}, nil
}

func Test_Descendent(t *testing.T) {
	stopTree, _ := NewStopTree(context.Background(), Querier{}, 3)
	actual := stopTree.DescendentPks()
	expected := []int64{1, 2, 3}
	if !compareList(actual, expected) {
		t.Errorf("Actual %v != expected %v", actual, expected)
	}
}

func compareList(a, b []int64) bool {
	if len(a) != len(b) {
		return false
	}
	aMap := map[int64]bool{}
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
