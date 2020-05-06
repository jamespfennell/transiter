from transiter.services.servicemap.graphutils import traversals


def test_pre_order_dfs_traversal__tree_3__root_node(tree_3):
    expected_labels = {("a", "b", "c", "d", "e"), ("a", "b", "c", "e", "d")}

    nodes = traversals.pre_order_dfs_traversal(tree_3.get_node("a"))
    actual_labels = tuple(node.label for node in nodes)

    assert actual_labels in expected_labels


def test_pre_order_dfs_traversal__tree_3__non_root_node(tree_3):
    expected_labels = {("c", "d", "e"), ("c", "e", "d")}

    nodes = traversals.pre_order_dfs_traversal(tree_3.get_node("c"))
    actual_labels = tuple(node.label for node in nodes)

    assert actual_labels in expected_labels


def test_pre_order_dfs_traversal__tree_3__non_root_node__reverse(tree_3):
    tree_3.reverse()
    nodes = traversals.pre_order_dfs_traversal(tree_3.get_node("c"))
    actual_labels = tuple(node.label for node in nodes)

    assert actual_labels == ("c", "b", "a")


def test_pre_order_dfs_traversal__tree_4__root_node(tree_4):
    expected_labels = {("a", "b", "c", "d", "e"), ("a", "d", "e", "b", "c")}
    nodes = traversals.pre_order_dfs_traversal(tree_4.get_node("a"))
    actual_labels = tuple(node.label for node in nodes)

    assert actual_labels in expected_labels


def test_pre_order_dfs_traversal__tree_4__root_node__with_sorting(tree_4):
    nodes = traversals.pre_order_dfs_traversal(
        tree_4.get_node("a"), sorting_key=lambda node: node.label
    )
    actual_labels = tuple(node.label for node in nodes)

    assert actual_labels == ("a", "b", "c", "d", "e")


def test_pre_order_dfs_traversal__tree_4__non_root_node_all(tree_4):
    expected_labels = {("b", "c", "a", "d", "e"), ("b", "a", "d", "e", "c")}

    nodes = traversals.pre_order_dfs_traversal(
        tree_4.get_node("b"), ignore_directionality=True
    )
    actual_labels = tuple(node.label for node in nodes)

    assert actual_labels in expected_labels


def test_pre_order_dfs_traversal__edge_into_three_cycle(edge_into_three_cycle):
    nodes = traversals.pre_order_dfs_traversal(edge_into_three_cycle.get_node("w"))
    actual_labels = tuple(node.label for node in nodes)

    assert actual_labels == ("w", "x", "y", "z")


def test_post_order_dfs_traversal__tree_3__root_node(tree_3):
    expected_labels = {("d", "e", "c", "b", "a"), ("e", "d", "c", "b", "a")}

    nodes = traversals.post_order_dfs_traversal(tree_3.get_node("a"))
    actual_labels = tuple(node.label for node in nodes)

    assert actual_labels in expected_labels


def test_post_order_dfs_traversal__tree_3__non_root_node(tree_3):
    expected_labels = {("e", "d", "c"), ("d", "e", "c")}

    nodes = traversals.post_order_dfs_traversal(tree_3.get_node("c"))
    actual_labels = tuple(node.label for node in nodes)

    assert actual_labels in expected_labels


def test_post_order_dfs_traversal__tree_3__non_root_node__reverse(tree_3):
    tree_3.reverse()
    nodes = traversals.post_order_dfs_traversal(tree_3.get_node("c"))
    actual_labels = tuple(node.label for node in nodes)

    assert actual_labels == ("a", "b", "c")


def test_post_order_dfs_traversal__tree_4__root_node(tree_4):
    expected_labels = {("c", "b", "e", "d", "a"), ("e", "d", "c", "b", "a")}
    nodes = traversals.post_order_dfs_traversal(tree_4.get_node("a"))
    actual_labels = tuple(node.label for node in nodes)

    assert actual_labels in expected_labels


def test_post_order_dfs_traversal__tree_4__root_node__with_sorting(tree_4):
    nodes = traversals.post_order_dfs_traversal(
        tree_4.get_node("a"), sorting_key=lambda node: node.label
    )
    actual_labels = tuple(node.label for node in nodes)

    assert actual_labels == ("c", "b", "e", "d", "a")


def test_post_order_dfs_traversal__tree_4__non_root_node_all(tree_4):
    expected_labels = {("c", "e", "d", "a", "b"), ("e", "d", "a", "c", "b")}

    nodes = traversals.post_order_dfs_traversal(
        tree_4.get_node("b"), ignore_directionality=True
    )
    actual_labels = tuple(node.label for node in nodes)

    assert actual_labels in expected_labels


def test_post_order_dfs_traversal__edge_into_three_cycle__root_node(
    edge_into_three_cycle,
):
    nodes = traversals.post_order_dfs_traversal(edge_into_three_cycle.get_node("w"))
    actual_labels = tuple(node.label for node in nodes)

    assert actual_labels == ("z", "y", "x", "w")
