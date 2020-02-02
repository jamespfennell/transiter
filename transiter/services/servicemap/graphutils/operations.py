import collections
from typing import Iterator, Optional, Tuple

from . import datastructures, traversals


def split_into_connected_components(
    graph: datastructures.AbstractGraph,
) -> Iterator[datastructures.MutableGraph]:
    nodes_to_start_from = set(graph.nodes())
    if len(nodes_to_start_from) == 0:
        yield datastructures.Graph.build_from_edge_label_tuples([])
    while len(nodes_to_start_from) > 0:
        node_to_start_from = nodes_to_start_from.pop()
        nodes_in_this_component = set(
            traversals.pre_order_dfs_traversal(
                node_to_start_from, ignore_directionality=True
            )
        )
        nodes_to_start_from -= nodes_in_this_component
        yield datastructures.MutableGraph.build_from_nodes(nodes_in_this_component)


def cast_to_path(graph: datastructures.AbstractGraph) -> Optional[datastructures.Path]:
    """
    Cast the directed graph into a path.

    Returns None if this is not possible.
    """
    if len(graph) == 0:
        return None
    sources = list(graph.sources())
    if len(sources) != 1:
        # There is not a unique node with no in-edge
        return None
    source = sources[0]
    path = []
    for node in traversals.pre_order_dfs_traversal(source):
        if len(node.out_nodes) > 1 or len(node.in_nodes) > 1:
            # One node has more than 1 in-edge or out-edge
            return None
        path.append(node.label)

    # The following logic captures the case of a disconnected graph.
    if len(path) != len(graph):
        # The graph is disconnected
        return None

    return datastructures.Path(graph, source)


def cast_to_tree(graph: datastructures.AbstractGraph) -> Optional[datastructures.Tree]:
    sources = set(graph.sources())
    if len(sources) == 0 and len(graph) == 0:
        return None
    if len(sources) != 1:
        # Graph contains multiple nodes without in-edges
        return None
    root = sources.pop()

    num_nodes = 0
    num_edges = 0
    for node in traversals.pre_order_dfs_traversal(root):
        num_nodes += 1
        num_edges += len(node.out_nodes)

    if num_nodes != len(graph):
        # Graph is not connected"
        return None
    if num_nodes != num_edges + 1:
        # Graph contains a cycle
        return None

    return datastructures.Tree(graph, root)


def calculate_transitive_reduction(
    graph: datastructures.AbstractGraph,
) -> datastructures.MutableGraph:
    """
    Calculate the transitive reduction of a graph.

    WARNING: if the inputted graph is mutable, the reduction will be calculated in
    place!

    The transitive reduction of a graph is another graph. The reduction contains all of
    the nodes of the original graph. It includes all of the edges, except edges (a,b)
    for which there exists a path from a to b of length greater than 1. That is,
    performing a reduction removes the edges that are redundant from the topological
    sort perspective.

    The time complexity of this algorithm is O(max(V,E) * E)
    """
    reduction = graph.mutable()

    for node in reduction.nodes():
        if node in node.out_nodes:
            reduction.delete_edge_using_labels(node.label, node.label)

    edge_tuples = set(reduction.edge_tuples())
    while len(edge_tuples) > 0:
        in_node, search_root_node = edge_tuples.pop()
        for out_node in traversals.pre_order_dfs_traversal(search_root_node):
            if out_node == search_root_node:
                continue
            if out_node in in_node.out_nodes:
                reduction.delete_edge_using_labels(in_node.label, out_node.label)
                edge_tuples.discard((in_node, out_node))
    return reduction


def calculate_tgt_decomposition(
    graph: datastructures.AbstractGraph,
) -> Tuple[
    Optional[datastructures.Tree],
    Optional[datastructures.Graph],
    Optional[datastructures.Tree],
]:
    """
    Calculate the tree-graph-tree decomposition of a graph.

    WARNING: if the inputted graph is mutable, the decomposition will be calculated in
    place!
    """
    original_graph = graph.immutable()
    first_tree, sub_graph_1 = _extract_leading_tree(graph.mutable())
    if sub_graph_1 is None:
        return first_tree, None, None
    sub_graph_1.reverse()
    second_tree, sub_graph_2 = _extract_leading_tree(sub_graph_1)
    if sub_graph_2 is not None:
        sub_graph_2.reverse()
    if second_tree is not None:
        second_tree.reverse()

    if (
        sub_graph_2 is None
        and first_tree is not None
        and cast_to_path(first_tree) is not None
    ):
        return (
            None,
            None,
            datastructures.Tree(original_graph, next(iter(original_graph.sources()))),
        )

    return first_tree, sub_graph_2, second_tree


def _extract_leading_tree(
    graph: datastructures.MutableGraph,
) -> Tuple[
    Optional[datastructures.Tree], Optional[datastructures.MutableGraph],
]:
    # An entry is when a node is encountered in the following traversal algorithm
    node_to_num_entries = collections.defaultdict(lambda: 0)
    sources = set(graph.sources())
    if len(sources) == 0:
        return None, graph
    root = None
    while len(sources) > 0:
        node = sources.pop()
        while (
            node_to_num_entries[node] == len(node.in_nodes) and len(node.out_nodes) == 1
        ):
            node = next(iter(node.out_nodes))
            node_to_num_entries[node] += 1

        if len(node.out_nodes) != 1:
            # This ensures we find a unique root
            if root is not None and root is not node:
                return None, graph
            root = node

    # Edge case where the tree has only one node
    if len(node_to_num_entries) == 1 and len(graph) != 1:
        return None, graph

    for node, num_entries in node_to_num_entries.items():
        if len(node.in_nodes) != num_entries:
            return None, graph

    if len(node_to_num_entries) == len(graph):
        return datastructures.Tree(graph, root), None

    tree_backing_graph = datastructures.MutableGraph()
    for node in node_to_num_entries.keys():
        for in_node in node.in_nodes:
            tree_backing_graph.create_node(node.label)
            tree_backing_graph.create_node(in_node.label)
            tree_backing_graph.create_edge_using_labels(in_node.label, node.label)
    tree = datastructures.Tree(
        tree_backing_graph, tree_backing_graph.get_node(root.label)
    )

    for node in node_to_num_entries.keys():
        if node is root:
            continue
        graph.delete_node(node)

    return tree, graph
