// Package graph contains type definitions for graphs and algorithms that operate on them.
//
// This package is used in service maps logic.
package graph

type Node interface {
	GetLabel() int64
	NumInNodes() int
	InNode(i int) Node
	NumOutNodes() int
	OutNode(i int) Node
}

type Graph struct {
	LabelToNode map[int64]*GraphNode
}

func (graph *Graph) NumNodes() int {
	return len(graph.LabelToNode)
}

type GraphNode struct {
	Label    int64
	InNodes  []*GraphNode
	OutNodes []*GraphNode
}

func (n *GraphNode) GetLabel() int64 {
	return n.Label
}

func (n *GraphNode) NumInNodes() int {
	return len(n.InNodes)
}

func (n *GraphNode) InNode(i int) Node {
	return n.InNodes[i]
}

func (n *GraphNode) NumOutNodes() int {
	return len(n.OutNodes)
}

func (n *GraphNode) OutNode(i int) Node {
	return n.OutNodes[i]
}

type Edge struct {
	FromLabel int64
	ToLabel   int64
}

// EdgeSetsEqual returns whether the provided sets of edges have the same elements.
func EdgeSetsEqual(lhs, rhs map[Edge]bool) bool {
	if len(lhs) != len(rhs) {
		return false
	}
	for edge := range lhs {
		if !rhs[edge] {
			return false
		}
	}
	return true
}

func NewGraph(edges ...Edge) *Graph {
	g := &Graph{
		LabelToNode: map[int64]*GraphNode{},
	}
	for _, edge := range edges {
		if _, ok := g.LabelToNode[edge.FromLabel]; !ok {
			g.LabelToNode[edge.FromLabel] = &GraphNode{
				Label: edge.FromLabel,
			}
		}
		if _, ok := g.LabelToNode[edge.ToLabel]; !ok {
			g.LabelToNode[edge.ToLabel] = &GraphNode{
				Label: edge.ToLabel,
			}
		}
		source := g.LabelToNode[edge.FromLabel]
		target := g.LabelToNode[edge.ToLabel]
		source.OutNodes = append(source.OutNodes, target)
		target.InNodes = append(target.InNodes, source)
	}
	return g
}

type Tree struct {
	Root        *TreeNode
	LabelToNode map[int64]*TreeNode
}

type TreeNode struct {
	Label    int64
	Parent   *TreeNode
	Children []*TreeNode
}

func (n *TreeNode) GetLabel() int64 {
	return n.Label
}

func (n *TreeNode) NumInNodes() int {
	if n.Parent != nil {
		return 1
	}
	return 0
}

func (n *TreeNode) InNode(i int) Node {
	if i == 0 && n.Parent != nil {
		return n.Parent
	}
	panic("out of bounds error")
}

func (n *TreeNode) NumOutNodes() int {
	return len(n.Children)
}

func (n *TreeNode) OutNode(i int) Node {
	return n.Children[i]
}

// NewTreeFromGraph attempts to convert the provided graph to a tree.
//
// The second return value is true if and only if this conversion is possible.
func NewTreeFromGraph(graph *Graph) (*Tree, bool) {
	var source *GraphNode
	for _, node := range graph.LabelToNode {
		if len(node.InNodes) > 0 {
			continue
		}
		if source != nil {
			// Graph has multiple nodes that could be the root (e.g., have no in-edges)
			return nil, false
		}
		source = node
	}
	if source == nil {
		// Graph is empty or has no root
		return nil, false
	}
	tree := &Tree{
		LabelToNode: map[int64]*TreeNode{},
	}
	traversal := DepthFirstTraverse(source, PreOrder)
	if len(traversal) != graph.NumNodes() {
		// Graph is disconnected
		return nil, false
	}
	numEdges := 0
	for i := len(traversal) - 1; i >= 0; i-- {
		graphNode := traversal[i]
		treeNode := &TreeNode{
			Label: graphNode.GetLabel(),
		}
		numEdges += graphNode.NumOutNodes()
		for i := 0; i < graphNode.NumOutNodes(); i++ {
			childGraphNode := graphNode.OutNode(i)
			childTreeNode, ok := tree.LabelToNode[childGraphNode.GetLabel()]
			if !ok {
				// Node has a child that hasn't been seen yet, so the graph cannot be topologically sorted
				// and hence cannot be a tree.
				return nil, false
			}
			treeNode.Children = append(treeNode.Children, childTreeNode)
			childTreeNode.Parent = treeNode
		}
		tree.LabelToNode[graphNode.GetLabel()] = treeNode
	}
	if len(traversal) != numEdges+1 {
		// Graph consists of a single connected component which can be topologically sorted
		// but there are additional edges (V!=E+1) so the graph is not a tree. Close, though!
		return nil, false
	}
	tree.Root = tree.LabelToNode[source.Label]
	return tree, true
}
