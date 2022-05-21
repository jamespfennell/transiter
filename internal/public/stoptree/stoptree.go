// Package stoptree is used for creating the tree of stops corresponding to a single stop.
package stoptree

import (
	"context"

	tdb "github.com/jamespfennell/transiter/internal/gen/db"
)

type StopTree struct {
	pkToNode map[int64]*StopTreeNode
	base     *StopTreeNode
}

type StopTreeNode struct {
	Parent   *StopTreeNode
	Children []*StopTreeNode
	Stop     *tdb.Stop
}

func NewStopTree(ctx context.Context, querier tdb.Querier, basePk int64) (*StopTree, error) {
	allStops, err := querier.ListStopsInStopTree(ctx, basePk)
	if err != nil {
		return nil, err
	}
	tree := StopTree{
		pkToNode: map[int64]*StopTreeNode{},
	}
	for _, stop := range allStops {
		stop := stop
		tree.pkToNode[stop.Pk] = &StopTreeNode{
			Stop: &stop,
		}
	}
	tree.base = tree.pkToNode[basePk]
	for _, stop := range allStops {
		if stop.ParentStopPk.Valid {
			parentPk := stop.ParentStopPk.Int64
			tree.pkToNode[stop.Pk].Parent = tree.pkToNode[parentPk]
			tree.pkToNode[parentPk].Children = append(
				tree.pkToNode[parentPk].Children,
				tree.pkToNode[stop.Pk],
			)
		}
	}
	return &tree, nil
}

func (tree *StopTree) StationPks() []int64 {
	var result []int64
	for pk, stop := range tree.pkToNode {
		if IsStation(stop.Stop) || stop.Stop.Pk == tree.base.Stop.Pk {
			result = append(result, pk)
		}
	}
	return result
}

func (tree *StopTree) DescendentPks() []int64 {
	pksToVisit := []int64{tree.base.Stop.Pk}
	var result []int64
	for len(pksToVisit) > 0 {
		pk := pksToVisit[len(pksToVisit)-1]
		pksToVisit = pksToVisit[:len(pksToVisit)-1]
		result = append(result, pk)
		for _, child := range tree.pkToNode[pk].Children {
			pksToVisit = append(pksToVisit, child.Stop.Pk)
		}
	}
	return result
}

func (tree *StopTree) VisitDFS(visitFunc func(node *StopTreeNode)) {
	stack := []*StopTreeNode{tree.base}
	seenPks := map[int64]bool{}
	seenPks[tree.base.Stop.Pk] = true
	visitedOncePks := map[int64]bool{}
	for len(stack) > 0 {
		node := stack[len(stack)-1]
		stack = stack[:len(stack)-1]
		if visitedOncePks[node.Stop.Pk] {
			visitFunc(node)
			continue
		}

		stack = append(stack, node)
		visitedOncePks[node.Stop.Pk] = true
		neighors := append([]*StopTreeNode{}, node.Children...)
		if node.Parent != nil {
			neighors = append(neighors, node.Parent)
		}
		for _, neighbor := range neighors {
			if seenPks[neighbor.Stop.Pk] {
				continue
			}
			seenPks[neighbor.Stop.Pk] = true
			stack = append(stack, neighbor)
		}
	}
}

func (tree *StopTree) Get(stopPk int64) *tdb.Stop {
	node := tree.pkToNode[stopPk]
	if node == nil {
		return nil
	}
	return node.Stop
}

func IsStation(stop *tdb.Stop) bool {
	return stop.Type == "STATION" || stop.Type == "GROUPED_STATION" || !stop.ParentStopPk.Valid
}
