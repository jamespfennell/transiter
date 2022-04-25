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
				{"a", "b"},
				{"b", "a"},
			},
		},
		{
			name: "edge into cycle",
			edges: []Edge{
				// Edge into
				{"a", "x"},
				// Cycle
				{"x", "y"},
				{"y", "x"},
			},
		},
		{
			name: "disconnected graph with tree and cycle",
			edges: []Edge{
				// Tree
				{"a", "b"},
				// Cycle
				{"x", "y"},
				{"y", "z"},
				{"z", "x"},
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
		{"a", "b"},
		{"b", "a"},
	}...)
}

func ThreeNodeCycle() *Graph {
	return NewGraph([]Edge{
		{"a", "b"},
		{"b", "c"},
		{"c", "a"},
	}...)
}

func ForkingJoiningPaths() *Graph {
	return NewGraph([]Edge{
		{"a", "b"},
		{"b", "c"},
		{"a", "d"},
		{"d", "c"},
	}...)
}

func TwoPaths() *Graph {
	return NewGraph([]Edge{
		{"a", "b"},
		{"x", "y"},
	}...)
}

func ThreeNodePath() *Graph {
	return NewGraph([]Edge{
		{"a", "b"},
		{"b", "c"},
	}...)
}

func FourNodeTree() *Graph {
	return NewGraph([]Edge{
		{"a", "b"},
		{"a", "c"},
		{"c", "d"},
	}...)
}

func FiveNodeTree() *Graph {
	return NewGraph([]Edge{
		{"a", "b"},
		{"b", "c"},
		{"a", "d"},
		{"d", "e"},
	}...)
}

func FiveNodeTree_Tree() *Tree {
	tree, _ := NewTreeFromGraph(FiveNodeTree())
	return tree
}
