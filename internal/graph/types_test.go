package graph

import "testing"

func TestNewTreeFromGraph_Success(t *testing.T) {
	for _, tc := range []struct {
		name  string
		graph *Graph
	}{
		{
			name:  "three node path",
			graph: ThreeNodePath(),
		},
		{
			name:  "tree",
			graph: FourNodeTree(),
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			_, ok := NewTreeFromGraph(tc.graph)
			if !ok {
				t.Errorf("NewTreeFromGraph(%+v) got = <nil>, false; want <non-nil>, true", tc.graph)
			}
		})
	}
}

func TestNewTreeFromGraph_Failure(t *testing.T) {
	for _, tc := range []struct {
		name  string
		graph *Graph
		edges []Edge
	}{
		{
			name:  "empty graph",
			graph: Empty(),
		},
		{
			name:  "two paths",
			graph: TwoPaths(),
		},
		{
			name: "cycle",
			edges: []Edge{
				{1, 2},
				{2, 1},
			},
		},
		{
			name: "edge into cycle",
			edges: []Edge{
				// Edge into
				{1, 101},
				// Cycle
				{101, 102},
				{102, 101},
			},
		},
		{
			name: "disconnected graph with tree and cycle",
			edges: []Edge{
				// Tree
				{1, 2},
				// Cycle
				{101, 102},
				{102, 103},
				{103, 101},
			},
		},
		{
			name:  "non-tree top sortable",
			graph: ForkingJoiningPaths(),
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			if tc.graph == nil {
				tc.graph = NewGraph(tc.edges...)
			}
			tree, ok := NewTreeFromGraph(tc.graph)
			if ok {
				t.Errorf("NewTreeFromGraph(%+v) got = %+v, true; want = nil, false", tc.graph, tree)
			}
		})
	}
}

func ToTree(t *testing.T, graph *Graph) *Tree {
	tree, ok := NewTreeFromGraph(graph)
	if !ok {
		t.Fatalf("could not convert graph to tree. Graph: %+v", graph)
	}
	return tree
}

func Empty() *Graph {
	return NewGraph()
}

func TwoNodeCycle() *Graph {
	return NewGraph([]Edge{
		{1, 2},
		{2, 1},
	}...)
}

func ThreeNodeCycle() *Graph {
	return NewGraph([]Edge{
		{1, 2},
		{2, 3},
		{3, 1},
	}...)
}

func ForkingJoiningPaths() *Graph {
	return NewGraph([]Edge{
		{1, 2},
		{2, 3},
		{1, 4},
		{4, 3},
	}...)
}

func TwoPaths() *Graph {
	return NewGraph([]Edge{
		{1, 2},
		{101, 102},
	}...)
}

func ThreeNodePath() *Graph {
	return NewGraph([]Edge{
		{1, 2},
		{2, 3},
	}...)
}

func FourNodeTree() *Graph {
	return NewGraph([]Edge{
		{1, 2},
		{1, 3},
		{3, 4},
	}...)
}

func FiveNodeTree() *Graph {
	return NewGraph([]Edge{
		{1, 2},
		{2, 3},
		{1, 4},
		{4, 5},
	}...)
}

func FiveNodeTreeAsTree() *Tree {
	tree, _ := NewTreeFromGraph(FiveNodeTree())
	return tree
}
