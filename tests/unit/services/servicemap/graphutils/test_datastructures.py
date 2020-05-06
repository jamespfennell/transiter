import pytest

from transiter.services.servicemap.graphutils import datastructures


# This function tests datastructures.Graph.__del__
def test_gc():
    graph = datastructures.Graph.build_from_edge_label_tuples(
        [("a", "b"), ("b", "c"), ("c", "a")]
    )
    nodes = list(graph.nodes())

    for node in nodes:
        assert len(node.in_nodes) != 0
        assert len(node.out_nodes) != 0

    del graph

    for node in nodes:
        with pytest.raises(RuntimeError):
            node.in_nodes
        with pytest.raises(RuntimeError):
            node.out_nodes


def test_equality__not_a_graph(tree_1):
    assert tree_1 != 1


def test_equality__different_labels(tree_1, tree_2):
    assert tree_1 != tree_2


def test_equality__different_labels_reverse(tree_1, tree_2):
    assert tree_2 != tree_1


def test_path__build_from_label_list():

    path_1 = datastructures.Graph.build_from_edge_label_tuples(
        [("a", "b"), ("b", "c"), ("c", "d")]
    )
    path_2 = datastructures.Path.build_from_label_list(["a", "b", "c", "d"])

    assert path_1 == path_2


def test_path__build_from_label_list__bad_list():

    with pytest.raises(ValueError):
        datastructures.Path.build_from_label_list(["a", "b", "c", "a"])
