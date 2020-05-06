import pytest

from transiter.services.servicemap.graphutils import datastructures


@pytest.fixture
def tree_1():
    graph = datastructures.Graph.build_from_edge_label_tuples(
        [("a", "b"), ("b", "c"), ("c", "d"), ("b", "e")]
    )
    return datastructures.Tree(graph, graph.get_node("a"))


@pytest.fixture
def tree_2():
    graph = datastructures.Graph.build_from_edge_label_tuples(
        [
            ("a", "b"),
            ("b", "c1"),
            ("c1", "c2"),
            ("c2", "c3"),
            ("b", "d"),
            ("d", "e1"),
            ("e1", "e2"),
            ("e2", "e3"),
            ("d", "f"),
        ]
    )
    return datastructures.Tree(graph, graph.get_node("a"))


@pytest.fixture
def tree_3():
    graph = datastructures.Graph.build_from_edge_label_tuples(
        [("a", "b"), ("b", "c"), ("c", "d"), ("c", "e")]
    )
    return datastructures.Tree(graph, graph.get_node("a"))


@pytest.fixture
def tree_4():
    graph = datastructures.Graph.build_from_edge_label_tuples(
        [("a", "b"), ("b", "c"), ("a", "d"), ("d", "e")]
    )
    return datastructures.Tree(graph, graph.get_node("a"))


@pytest.fixture
def singleton_graph():
    graph = datastructures.MutableGraph()
    graph.create_node("a")
    return graph


@pytest.fixture
def empty_graph():
    return datastructures.Graph.build_from_edge_label_tuples([])


@pytest.fixture
def edge_into_three_cycle():
    return datastructures.Graph.build_from_edge_label_tuples(
        [("w", "x"), ("x", "y"), ("y", "z"), ("z", "x")]
    )


@pytest.fixture
def three_node_path():
    return datastructures.Graph.build_from_edge_label_tuples([("a", "b"), ("b", "c")])


@pytest.fixture
def union__three_node_path__edge_into_three_cycle(
    three_node_path, edge_into_three_cycle
):
    return datastructures.Graph.union([three_node_path, edge_into_three_cycle])


@pytest.fixture(params=range(2))
def disconnected_graph(request, union__three_node_path__edge_into_three_cycle):
    graph_1 = datastructures.Graph.build_from_edge_label_tuples(
        [("a", "b"), ("c", "d"), ("d", "e"), ("e", "c")]
    )
    disconnected_graphs = [union__three_node_path__edge_into_three_cycle, graph_1]
    return disconnected_graphs[request.param]


@pytest.fixture
def opposite_trees_same_root():
    return datastructures.Graph.build_from_edge_label_tuples(
        [("a", "b"), ("b", "c"), ("d", "c"), ("c", "e"), ("c", "f"), ("f", "g")]
    )


@pytest.fixture
def one_node_cycle():
    return datastructures.Graph.build_from_edge_label_tuples([("a", "a")])


@pytest.fixture
def two_node_cycle():
    return datastructures.Graph.build_from_edge_label_tuples([("a", "b"), ("a", "a")])


@pytest.fixture
def four_node_cycle():
    return datastructures.Graph.build_from_edge_label_tuples(
        [("a", "b"), ("b", "c"), ("c", "d"), ("d", "a")]
    )


@pytest.fixture(params=range(4))
def non_trivial_tree(
    request, tree_1, tree_2, tree_3, tree_4,
):
    trees = [
        tree_1,
        tree_2,
        tree_3,
        tree_4,
    ]
    return trees[request.param]


@pytest.fixture(params=range(7))
def tree(
    request,
    tree_1,
    tree_2,
    tree_3,
    tree_4,
    empty_graph,
    singleton_graph,
    three_node_path,
):
    trees = [
        tree_1,
        tree_2,
        tree_3,
        tree_4,
        empty_graph,
        singleton_graph,
        three_node_path,
    ]
    return trees[request.param]


@pytest.fixture(params=range(8))
def sortable_graph(
    request,
    tree_1,
    tree_2,
    tree_3,
    tree_4,
    empty_graph,
    singleton_graph,
    three_node_path,
    opposite_trees_same_root,
):
    sortable_graphs = [
        tree_1,
        tree_2,
        tree_3,
        tree_4,
        empty_graph,
        singleton_graph,
        three_node_path,
        opposite_trees_same_root,
    ]
    return sortable_graphs[request.param]


@pytest.fixture(params=range(5))
def non_sortable_graph(
    request,
    edge_into_three_cycle,
    union__three_node_path__edge_into_three_cycle,
    one_node_cycle,
    two_node_cycle,
    four_node_cycle,
):
    non_sortable_graphs = [
        edge_into_three_cycle,
        union__three_node_path__edge_into_three_cycle,
        one_node_cycle,
        two_node_cycle,
        four_node_cycle,
    ]
    return non_sortable_graphs[request.param]


@pytest.fixture(params=range(3))
def cycle(
    request, one_node_cycle, two_node_cycle, four_node_cycle,
):
    non_sortable_graphs = [
        one_node_cycle,
        two_node_cycle,
        four_node_cycle,
    ]
    return non_sortable_graphs[request.param]
