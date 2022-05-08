package graph

import (
	"reflect"
	"testing"
)

func TestDepthFirstTraverse(t *testing.T) {
	for _, tc := range []struct {
		name          string
		graph         *Graph
		root          int64
		wantPreOrder  []int64
		wantPostOrder []int64
	}{
		{
			name:          "three node path",
			graph:         ThreeNodePath(),
			root:          1,
			wantPreOrder:  []int64{1, 2, 3},
			wantPostOrder: []int64{3, 2, 1},
		},
		{
			name:          "three node path start at b",
			graph:         ThreeNodePath(),
			root:          2,
			wantPreOrder:  []int64{2, 3},
			wantPostOrder: []int64{3, 2},
		},
		{
			name:          "two node cycle",
			graph:         TwoNodeCycle(),
			root:          1,
			wantPreOrder:  []int64{1, 2},
			wantPostOrder: []int64{2, 1},
		},
		{
			name:          "three node cycle",
			graph:         ThreeNodeCycle(),
			root:          1,
			wantPreOrder:  []int64{1, 2, 3},
			wantPostOrder: []int64{3, 2, 1},
		},
		{
			name:          "forking joining paths",
			graph:         ForkingJoiningPaths(),
			root:          1,
			wantPreOrder:  []int64{1, 2, 3, 4},
			wantPostOrder: []int64{3, 2, 4, 1},
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			for _, ttc := range []struct {
				name          string
				traversalType TraversalType
				want          []int64
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
				t.Run(ttc.name, func(t *testing.T) {
					gotNodes := DepthFirstTraverse(tc.graph.LabelToNode[tc.root], ttc.traversalType)
					var got []int64
					for _, gotNode := range gotNodes {
						got = append(got, gotNode.GetLabel())
					}
					if !reflect.DeepEqual(ttc.want, got) {
						t.Errorf("DepthFirstTraverse() got = %+v, want = %+v", got, ttc.want)
					}

				})
			}
		})
	}
}
