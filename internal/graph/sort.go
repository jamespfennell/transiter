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
	var startingLabels []int64
	numInNodes := map[int64]int{}
	for _, node := range graph.LabelToNode {
		numInNodes[node.GetLabel()] = node.NumInNodes()
		if node.NumInNodes() == 0 {
			startingLabels = append(startingLabels, node.GetLabel())
		}
	}
	sort.Slice(startingLabels, func(i, j int) bool {
		return startingLabels[i] < startingLabels[j]
	})
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
	labelToWeight := map[int64]int{}
	traversal := DepthFirstTraverse(root, PostOrder)
	for _, node := range traversal {
		weight := 1
		for i := 0; i < node.NumOutNodes(); i++ {
			weight += labelToWeight[node.OutNode(i).GetLabel()]
		}
		labelToWeight[node.GetLabel()] = weight
	}
	for _, node := range traversal {
		children := node.(*TreeNode).Children
		// We sort the children to make the next traversal deterministic.
		sort.Slice(children, func(i, j int) bool {
			l := children[i]
			r := children[j]
			if labelToWeight[l.Label] == labelToWeight[r.Label] {
				return l.Label < r.Label
			}
			return labelToWeight[l.Label] < labelToWeight[r.Label]
		})
	}
	return DepthFirstTraverse(root, PreOrder)
}
