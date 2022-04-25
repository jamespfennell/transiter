package graph

import (
	"fmt"
	"sort"
)

var (
	ErrGraphNotSortable = fmt.Errorf("the provided graph is not topologically sortable because it contains a cycle")
)

func SortBasic(graph *Graph) ([]Node, error) {
	var result []Node
	var stack []Node
	var startingLabels []string
	numInNodes := map[string]int{}
	for _, node := range graph.LabelToNode {
		numInNodes[node.GetLabel()] = node.NumInNodes()
		if node.NumInNodes() == 0 {
			startingLabels = append(startingLabels, node.GetLabel())
		}
	}
	sort.Sort(sort.Reverse(sort.StringSlice(startingLabels)))
	for _, label := range startingLabels {
		stack = append(stack, graph.LabelToNode[label])
	}
	for len(stack) > 0 {
		next := stack[len(stack)-1]
		result = append(result, next)
		stack = stack[:len(stack)-1]
		for j := 0; j < next.NumOutNodes(); j++ {
			outNode := next.OutNode(j)
			numInNodes[outNode.GetLabel()] -= 1
			if numInNodes[outNode.GetLabel()] == 0 {
				stack = append(stack, outNode)
			}
		}
	}
	if len(result) != len(graph.LabelToNode) {
		return nil, ErrGraphNotSortable
	}
	return result, nil
}

// SortTree topologically sorts the provided tree.
//
// The algorithm minimizes the total length of the edges.
func SortTree(root *TreeNode) []Node {
	labelToWeight := map[string]int{}
	traversal := DepthFirstTraverse(root, PostOrder)
	for _, node := range traversal {
		weight := 1
		for i := 0; i < node.NumOutNodes(); i++ {
			weight += labelToWeight[node.OutNode(i).GetLabel()]
		}
		labelToWeight[node.GetLabel()] = weight
	}
	for _, node := range traversal {
		sort.Sort(treeChildrenSorter{
			labelToWeight: labelToWeight,
			node:          node.(*TreeNode),
		})
	}
	return DepthFirstTraverse(root, PreOrder)
}

type treeChildrenSorter struct {
	labelToWeight map[string]int
	node          *TreeNode
}

func (n treeChildrenSorter) Len() int {
	return n.node.NumOutNodes()
}

func (n treeChildrenSorter) Less(i, j int) bool {
	l := n.node.Children[i]
	r := n.node.Children[j]
	if n.labelToWeight[l.Label] == n.labelToWeight[r.Label] {
		return l.Label < r.Label
	}
	return n.labelToWeight[l.Label] < n.labelToWeight[r.Label]
}

func (n treeChildrenSorter) Swap(i, j int) {
	n.node.Children[i], n.node.Children[j] = n.node.Children[j], n.node.Children[i]
}
