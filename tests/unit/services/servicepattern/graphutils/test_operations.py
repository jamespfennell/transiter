from transiter.services.servicemap.graphutils import operations, datastructures

import pytest


def test_split_into_connected_components__tree(tree):
    tree = tree.immutable()
    components = list(operations.split_into_connected_components(tree))

    assert [tree] == components


def test_split_into_connected_components__union(
    union__three_node_path__edge_into_three_cycle,
    three_node_path,
    edge_into_three_cycle,
):
    components = tuple(
        operations.split_into_connected_components(
            union__three_node_path__edge_into_three_cycle
        )
    )

    assert len(components) == 2

    assert components == (three_node_path, edge_into_three_cycle) or components == (
        edge_into_three_cycle,
        three_node_path,
    )


def test_cast_to_path__path(three_node_path):
    assert ["a", "b", "c"] == list(
        node.label for node in operations.cast_to_path(three_node_path).nodes()
    )


def test_cast_to_path__empty_graph(empty_graph):
    assert operations.cast_to_path(empty_graph) is None


def test_cast_to_path__disconnected_graph(disconnected_graph):
    assert operations.cast_to_path(disconnected_graph) is None


def test_cast_to_path__tree(non_trivial_tree):
    assert operations.cast_to_path(non_trivial_tree) is None


def test_cast_to_path__general_graph(non_sortable_graph):
    assert operations.cast_to_path(non_sortable_graph) is None


def test_get_root_of_tree__is_a_tree(tree):
    if len(tree) == 0:
        return

    expected_root = tree.get_node("a")

    actual_root = operations.cast_to_tree(tree).root

    assert expected_root == actual_root


def test_get_root_of_tree__not_a_tree(non_sortable_graph):
    assert operations.cast_to_tree(non_sortable_graph) is None


def test_cast_to_tree__empty_graph(empty_graph):
    assert operations.cast_to_tree(empty_graph) is None


def test_cast_to_tree__disconnected_graph(disconnected_graph):
    assert operations.cast_to_tree(disconnected_graph) is None


@pytest.mark.parametrize(
    "reduction_edges,redundant_edges",
    [
        [{("a", "b"), ("b", "c")}, {("a", "c")}],
        [
            {("a", "b"), ("b", "c"), ("c", "d"), ("d", "e")},
            {("a", "c"), ("c", "e"), ("a", "e")},
        ],
    ],
)
def test_transitive_reduction(reduction_edges: set, redundant_edges: set):
    graph = datastructures.Graph.build_from_edge_label_tuples(
        reduction_edges.union(redundant_edges)
    )
    expected_reduction = datastructures.Graph.build_from_edge_label_tuples(
        reduction_edges
    )

    actual_reduction = operations.calculate_transitive_reduction(graph)

    assert expected_reduction == actual_reduction


def test_transitive_reduction__singleton_graph(singleton_graph: datastructures.Graph,):
    graph = datastructures.MutableGraph(singleton_graph)
    graph.create_edge_using_labels("a", "a")

    reduction = operations.calculate_transitive_reduction(graph)

    assert singleton_graph == reduction


def test_transitive_reduction__no_change(tree):
    reduction = operations.calculate_transitive_reduction(tree)

    assert tree.immutable() == reduction


def test_transitive_reduction__cycle(edge_into_three_cycle):
    reduction = operations.calculate_transitive_reduction(edge_into_three_cycle)

    assert edge_into_three_cycle == reduction


def test_tgt_decomposition__tree(non_trivial_tree):
    tree_1, graph, tree_2 = operations.calculate_tgt_decomposition(non_trivial_tree)

    assert tree_1 is None
    assert graph is None
    assert tree_2 == non_trivial_tree


def test_tgt_decomposition__tree_mutable(non_trivial_tree):
    original = non_trivial_tree.immutable()
    tree_1, graph, tree_2 = operations.calculate_tgt_decomposition(
        non_trivial_tree.mutable()
    )

    assert tree_1 is None
    assert graph is None
    assert original == tree_2  # == original


def test_tgt_decomposition__tree_reverse(non_trivial_tree):
    non_trivial_tree.reverse()
    tree_1, graph, tree_2 = operations.calculate_tgt_decomposition(non_trivial_tree)

    assert tree_1 == non_trivial_tree
    assert graph is None
    assert tree_2 is None


def test_tgt_decomposition__cycle(cycle):
    tree_1, graph, tree_2 = operations.calculate_tgt_decomposition(cycle)

    assert tree_1 is None
    assert graph == cycle
    assert tree_2 is None


def test_tgt_decomposition__edge_into_four_cycle(
    four_node_cycle: datastructures.Graph,
):
    node_into_four_cycle = datastructures.MutableGraph(four_node_cycle)
    node_into_four_cycle.create_node("x")
    node_into_four_cycle.create_edge_using_labels("x", "a")

    tree_1, graph, tree_2 = operations.calculate_tgt_decomposition(node_into_four_cycle)

    assert tree_1 is None
    assert graph == node_into_four_cycle
    assert tree_2 is None


@pytest.fixture
def in_tree_piece():
    return datastructures.MutableGraph.build_from_edge_label_tuples(
        [("a2", "a1"), ("a3", "a1"), ("a4", "a1")]
    )


@pytest.fixture
def out_tree_piece():
    return datastructures.MutableGraph.build_from_edge_label_tuples(
        [("b1", "b2"), ("b1", "b3"), ("b1", "b4")]
    )


def test_tgt_decomposition__general_case_1(in_tree_piece, out_tree_piece):
    in_tree_piece.create_node("b1")
    in_tree_piece.create_edge_using_labels("a1", "b1")

    tree_1, graph, tree_2 = operations.calculate_tgt_decomposition(
        datastructures.Graph.union([in_tree_piece, out_tree_piece])
    )

    assert tree_1 == datastructures.Tree(in_tree_piece, in_tree_piece.get_node("b1"))
    assert graph is None
    assert tree_2 == datastructures.Tree(out_tree_piece, out_tree_piece.get_node("b1"))


def test_tgt_decomposition__general_case_2(in_tree_piece):
    out_tree_piece = datastructures.Graph.build_from_edge_label_tuples(
        [("a1", "b2"), ("a1", "b3")]
    )

    tree_1, graph, tree_2 = operations.calculate_tgt_decomposition(
        datastructures.Graph.union([in_tree_piece, out_tree_piece])
    )

    assert tree_1 == datastructures.Tree(in_tree_piece, in_tree_piece.get_node("a1"))
    assert graph is None
    assert tree_2 == datastructures.Tree(out_tree_piece, out_tree_piece.get_node("a1"))


def test_tgt_decomposition__general_case_3(in_tree_piece, out_tree_piece):
    middle_graph = datastructures.Graph.build_from_edge_label_tuples(
        [("a1", "c1"), ("c1", "b1"), ("a1", "c2"), ("c2", "b1")]
    )

    tree_1, graph, tree_2 = operations.calculate_tgt_decomposition(
        datastructures.Graph.union([in_tree_piece, middle_graph, out_tree_piece])
    )

    assert tree_1 == datastructures.Tree(in_tree_piece, in_tree_piece.get_node("a1"))
    assert graph == middle_graph
    assert tree_2 == datastructures.Tree(out_tree_piece, out_tree_piece.get_node("b1"))


def test_tgt_decomposition__general_case_4(in_tree_piece, out_tree_piece):
    in_tree_piece.create_node("a5")
    in_tree_piece.create_edge_using_labels("a1", "a5")
    middle_graph = datastructures.Graph.build_from_edge_label_tuples(
        [("a5", "c1"), ("c1", "b1"), ("a5", "c2"), ("c2", "b1")]
    )

    tree_1, graph, tree_2 = operations.calculate_tgt_decomposition(
        datastructures.Graph.union([in_tree_piece, middle_graph, out_tree_piece])
    )

    assert tree_1 == datastructures.Tree(in_tree_piece, in_tree_piece.get_node("a5"))
    assert graph == middle_graph
    assert tree_2 == datastructures.Tree(out_tree_piece, out_tree_piece.get_node("b1"))


def test_tgt_decomposition__general_case_5():
    middle_graph = datastructures.Graph.build_from_edge_label_tuples(
        [("a", "c"), ("c", "d"), ("b", "d"), ("c", "e"), ("e", "f")]
    )

    tree_1, graph, tree_2 = operations.calculate_tgt_decomposition(middle_graph)

    assert tree_1 is None
    assert graph == middle_graph
    assert tree_2 is None
