package graph

import (
	"reflect"
	"testing"
)

func TestSortBasic(t *testing.T) {
	for _, tc := range []struct {
		name  string
		graph *Graph
		want  []string
	}{
		{
			name:  "forking joining paths",
			graph: ForkingJoiningPaths(),
			want:  []string{"a", "d", "b", "c"},
		},
		{
			name:  "two paths",
			graph: TwoPaths(),
			want:  []string{"a", "b", "x", "y"},
		},
	} {
		sorting, err := SortBasic(tc.graph)
		if err != nil {
			t.Errorf("SortBasic() err != nil, want = nil")
		}
		var got []string
		for _, node := range sorting {
			got = append(got, node.GetLabel())
		}
		if !reflect.DeepEqual(tc.want, got) {
			t.Errorf("SortBasic() got = %+v, want = %+v", got, tc.want)
		}
	}
}

func TestSortTree(t *testing.T) {
	for _, tc := range []struct {
		name string
		tree *Graph
		want []string
	}{
		{
			name: "three node path",
			tree: ThreeNodePath(),
			want: []string{"a", "b", "c"},
		},
		{
			name: "four node tree",
			tree: FourNodeTree(),
			want: []string{"a", "b", "c", "d"},
		},
		{
			name: "five node tree",
			tree: FiveNodeTree(),
			want: []string{"a", "b", "c", "d", "e"},
		},
	} {
		tree := ToTree(t, tc.tree)
		var got []string
		for _, node := range SortTree(tree.Root) {
			got = append(got, node.GetLabel())
		}
		if !reflect.DeepEqual(tc.want, got) {
			t.Errorf("SortTree() got = %+v, want = %+v", got, tc.want)
		}
	}
}
