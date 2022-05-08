package graph

type TraversalType bool

const (
	PreOrder  TraversalType = true
	PostOrder TraversalType = false
)

// DepthFirstTraverse performs a depth first traversal with the given root as the starting point.
func DepthFirstTraverse(root Node, t TraversalType) []Node {
	type elem struct {
		node            Node
		numOutNodesSeen int
	}
	var stack []elem
	stack = append(stack, elem{
		node:            root,
		numOutNodesSeen: 0,
	})
	addedToStack := map[int64]bool{}
	addedToStack[root.GetLabel()] = true
	var result []Node
	for len(stack) > 0 {
		last := &stack[len(stack)-1]
		if last.numOutNodesSeen == 0 && t == PreOrder {
			result = append(result, last.node)
		}
		if last.numOutNodesSeen == last.node.NumOutNodes() {
			if t == PostOrder {
				result = append(result, last.node)
			}
			stack = stack[0 : len(stack)-1]
		} else {
			newNode := last.node.OutNode(last.numOutNodesSeen)
			last.numOutNodesSeen++
			if addedToStack[newNode.GetLabel()] {
				continue
			}
			stack = append(stack, elem{
				node:            newNode,
				numOutNodesSeen: 0,
			})
			addedToStack[newNode.GetLabel()] = true
		}
	}
	return result
}
