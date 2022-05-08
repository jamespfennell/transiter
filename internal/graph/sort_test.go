package graph

import (
	"reflect"
	"testing"
)

func TestSortBasic(t *testing.T) {
	for _, tc := range []struct {
		name  string
		graph *Graph
		want  []int64
	}{
		{
			name:  "forking joining paths",
			graph: ForkingJoiningPaths(),
			want:  []int64{1, 4, 2, 3},
		},
		{
			name:  "two paths",
			graph: TwoPaths(),
			want:  []int64{101, 102, 1, 2},
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			sorting, err := SortBasic(tc.graph)
			if err != nil {
				t.Errorf("SortBasic() err != nil, want = nil")
			}
			var got []int64
			for _, node := range sorting {
				got = append(got, node.GetLabel())
			}
			if !reflect.DeepEqual(tc.want, got) {
				t.Errorf("SortBasic() got = %+v, want = %+v", got, tc.want)
			}
		})
	}
}

func TestSortTree(t *testing.T) {
	for _, tc := range []struct {
		name string
		tree *Graph
		want []int64
	}{
		{
			name: "three node path",
			tree: ThreeNodePath(),
			want: []int64{1, 2, 3},
		},
		{
			name: "four node tree",
			tree: FourNodeTree(),
			want: []int64{1, 2, 3, 4},
		},
		{
			name: "five node tree",
			tree: FiveNodeTree(),
			want: []int64{1, 2, 3, 4, 5},
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			tree := ToTree(t, tc.tree)
			var got []int64
			for _, node := range SortTree(tree.Root) {
				got = append(got, node.GetLabel())
			}
			if !reflect.DeepEqual(tc.want, got) {
				t.Errorf("SortTree() got = %+v, want = %+v", got, tc.want)
			}
		})
	}
}
