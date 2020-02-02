"""
This class contains algorithms for topologically sorting graphs.
"""

from transiter.services.servicemap.graphutils import (
    datastructures,
    operations,
    traversals,
)


class ImpossibleToTopologicallySortGraph(Exception):
    """
    Exception thrown if the inputted directed graph contains a cycle.
    """


def basic_sort(graph: datastructures.AbstractGraph) -> datastructures.OrderedGraph:
    """
    Topologically sort a directed graph.

    The algorithm here is the basic topological sort algorithm, except the
    sorting has the following property. If there are vertices A, B, C, such
    (A,B) and (B,C) are edges, and there are no other edges out of A and B
    and in to B and C, then A, B and C will be consecutive in the sorting.

    Raises ImpossibleToTopologicallySortGraph: if the graph cannot be sorted;
    i.e., it contains a cycle.
    """
    sorted_nodes = []
    admissible_next_nodes = datastructures.Stack(graph.sources())
    node_to_in_node_count = {node: len(node.in_nodes) for node in graph.nodes()}

    while len(admissible_next_nodes) > 0:
        node = admissible_next_nodes.pop()
        sorted_nodes.append(node)
        for candidate_next_node in node.out_nodes:
            node_to_in_node_count[candidate_next_node] -= 1
            if node_to_in_node_count[candidate_next_node] == 0:
                admissible_next_nodes.push(candidate_next_node)

    if len(graph) != len(sorted_nodes):
        raise ImpossibleToTopologicallySortGraph

    return datastructures.OrderedGraph(graph, sorted_nodes)


def optimal_sort_for_trees(graph: datastructures.Tree) -> datastructures.OrderedTree:
    graph_reversed = False
    if graph.is_in_tree():
        graph.reverse()
        graph_reversed = True
    node_to_descendents_count = {}
    for node in traversals.post_order_dfs_traversal(graph.root):
        node_to_descendents_count[node] = 1 + sum(
            node_to_descendents_count[child_node] for child_node in node.out_nodes
        )
    ordered_graph = datastructures.OrderedTree(
        graph,
        traversals.pre_order_dfs_traversal(
            graph.root, sorting_key=node_to_descendents_count.get
        ),
    )
    if graph_reversed:
        ordered_graph.reverse()
    return ordered_graph


def tgt_sort(graph: datastructures.AbstractGraph) -> datastructures.OrderedGraph:
    tree_1, inner_graph, tree_2 = operations.calculate_tgt_decomposition(
        operations.calculate_transitive_reduction(graph.immutable())
    )

    labels = []
    for sub_graph, sorting_method in (
        (tree_1, optimal_sort_for_trees),
        (inner_graph, basic_sort),
        (tree_2, optimal_sort_for_trees),
    ):
        if sub_graph is None:
            continue
        new_labels = [node.label for node in sorting_method(sub_graph).nodes()]
        if len(labels) > 0:
            assert labels[-1] == new_labels[0]
            labels += new_labels[1:]
        else:
            labels = new_labels
    return datastructures.OrderedGraph(
        graph, [graph.get_node(label) for label in labels]
    )
