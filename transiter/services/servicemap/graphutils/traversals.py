import enum
from typing import Iterator

from .datastructures import AbstractNode, Stack


class DfsTraversalOrder(enum.Enum):
    PRE_ORDER = 0
    POST_ORDER = 1


def pre_order_dfs_traversal(
    starting_node: AbstractNode, ignore_directionality=False, sorting_key=None,
) -> Iterator[AbstractNode]:

    yield from dfs_traversal(
        DfsTraversalOrder.PRE_ORDER, starting_node, ignore_directionality, sorting_key
    )


def post_order_dfs_traversal(
    starting_node: AbstractNode, ignore_directionality=False, sorting_key=None,
) -> Iterator[AbstractNode]:
    yield from dfs_traversal(
        DfsTraversalOrder.POST_ORDER, starting_node, ignore_directionality, sorting_key
    )


def dfs_traversal(
    order: DfsTraversalOrder,
    starting_node: AbstractNode,
    ignore_directionality=False,
    sorting_key=None,
) -> Iterator[AbstractNode]:
    visited_nodes = set()
    stack = Stack()
    stack.push((starting_node, False))
    while len(stack) > 0:
        node, second_visit = stack.pop()
        visited_nodes.add(node)
        if order == DfsTraversalOrder.POST_ORDER:
            if second_visit:
                yield node
                continue
            stack.push((node, True))
        else:
            yield node
        next_nodes = list(node.out_nodes)
        if ignore_directionality:
            next_nodes.extend(node.in_nodes)
        if sorting_key is not None:
            # The next nodes are placed on the stack in the order of the list here.
            # Therefore we reverse the list in the sorting to ensure they come off the
            # stack in the real order we want.
            next_nodes.sort(key=sorting_key, reverse=True)
        for next_node in next_nodes:
            if next_node not in visited_nodes:
                stack.push((next_node, False))
