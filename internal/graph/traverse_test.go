package graph

import (
	"reflect"
	"testing"
)

func TestDepthFirstTraverse(t *testing.T) {
	for _, tc := range []struct {
		name          string
		graph         *Graph
		root          string
		wantPreOrder  []string
		wantPostOrder []string
	}{
		{
			name:          "three node path",
			graph:         ThreeNodePath(),
			root:          "a",
			wantPreOrder:  []string{"a", "b", "c"},
			wantPostOrder: []string{"c", "b", "a"},
		},
		{
			name:          "three node path start at b",
			graph:         ThreeNodePath(),
			root:          "b",
			wantPreOrder:  []string{"b", "c"},
			wantPostOrder: []string{"c", "b"},
		},
		{
			name:          "two node cycle",
			graph:         TwoNodeCycle(),
			root:          "a",
			wantPreOrder:  []string{"a", "b"},
			wantPostOrder: []string{"b", "a"},
		},
		{
			name:          "three node cycle",
			graph:         ThreeNodeCycle(),
			root:          "a",
			wantPreOrder:  []string{"a", "b", "c"},
			wantPostOrder: []string{"c", "b", "a"},
		},
		{
			name:          "forking joining paths",
			graph:         ForkingJoiningPaths(),
			root:          "a",
			wantPreOrder:  []string{"a", "b", "c", "d"},
			wantPostOrder: []string{"c", "b", "d", "a"},
		},
	} {
		for _, ttc := range []struct {
			name          string
			traversalType TraversalType
			want          []string
		}{
			{
				name:          "preorder",
				traversalType: PreOrder,
				want:          tc.wantPreOrder,
			},
			{
				name:          "postorder",
				traversalType: PostOrder,
				want:          tc.wantPostOrder,
			},
		} {
			t.Run(tc.name+"_"+ttc.name, func(t *testing.T) {
				gotNodes := DepthFirstTraverse(tc.graph.LabelToNode[tc.root], ttc.traversalType)
				var got []string
				for _, gotNode := range gotNodes {
					got = append(got, gotNode.GetLabel())
				}
				if !reflect.DeepEqual(ttc.want, got) {
					t.Errorf("DepthFirstTraverse() got = %+v, want = %+v", got, ttc.want)
				}

			})
		}
	}
}
