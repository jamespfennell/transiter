import pytest

from transiter.services.servicemap.graphutils import (
    topologicalsort,
    operations,
    datastructures,
)


def test_basic_sort(sortable_graph):
    sorted_graph = topologicalsort.basic_sort(sortable_graph)
    visited_labels = set()
    for vertex in sorted_graph.nodes():
        for prev in vertex.in_nodes:
            assert prev.label in visited_labels
        visited_labels.add(vertex.label)


def test_basic_sort__impossible_to_sort(non_sortable_graph):
    with pytest.raises(topologicalsort.ImpossibleToTopologicallySortGraph):
        topologicalsort.basic_sort(non_sortable_graph)


def test_optimal_sort_for_trees__tree_1(tree_1):
    tree = operations.cast_to_tree(tree_1)
    sorted_labels = [
        node.label for node in topologicalsort.optimal_sort_for_trees(tree).nodes()
    ]

    assert sorted_labels == ["a", "b", "e", "c", "d"]


def test_optimal_sort_for_trees__tree_2(tree_2):
    tree = operations.cast_to_tree(tree_2)
    sorted_labels = [
        node.label for node in topologicalsort.optimal_sort_for_trees(tree).nodes()
    ]

    assert sorted_labels == ["a", "b", "c1", "c2", "c3", "d", "f", "e1", "e2", "e3"]


def test_optimal_sort_for_trees__tree_2_reverse(tree_2):
    tree = operations.cast_to_tree(tree_2)
    tree.reverse()
    sorted_labels = [
        node.label for node in topologicalsort.optimal_sort_for_trees(tree).nodes()
    ]

    assert sorted_labels == list(
        reversed(["a", "b", "c1", "c2", "c3", "d", "f", "e1", "e2", "e3"])
    )


def test_tgt_sort__non_optimal_cases(sortable_graph):
    sorted_graph = topologicalsort.basic_sort(sortable_graph)
    visited_labels = set()
    for vertex in sorted_graph.nodes():
        for prev in vertex.in_nodes:
            assert prev.label in visited_labels
        visited_labels.add(vertex.label)


def test_tgt_sort___tree(non_trivial_tree):
    sorted_labels_1 = [
        node.label for node in topologicalsort.tgt_sort(non_trivial_tree).nodes()
    ]
    sorted_labels_2 = [
        node.label
        for node in topologicalsort.optimal_sort_for_trees(non_trivial_tree).nodes()
    ]

    assert sorted_labels_1 == sorted_labels_2


def test_tgt_sort___reversed_tree(non_trivial_tree):
    non_trivial_tree.reverse()

    sorted_labels_1 = [
        node.label for node in topologicalsort.tgt_sort(non_trivial_tree).nodes()
    ]
    sorted_labels_2 = [
        node.label
        for node in topologicalsort.optimal_sort_for_trees(non_trivial_tree).nodes()
    ]

    assert sorted_labels_1 == sorted_labels_2


def test_tgt_sort__full_case():
    graph = datastructures.Graph.build_from_edge_label_tuples(
        [
            ("a1", "a2"),
            ("a2", "a3"),
            ("a4", "a3"),
            ("a3", "c"),
            ("a1", "c"),
            ("c", "b1"),
            ("b1", "b2"),
            ("b2", "b3"),
            ("b1", "b4"),
        ]
    )

    sorted_labels = [node.label for node in topologicalsort.tgt_sort(graph).nodes()]

    assert ["a1", "a2", "a4", "a3", "c", "b1", "b4", "b2", "b3"] == sorted_labels
