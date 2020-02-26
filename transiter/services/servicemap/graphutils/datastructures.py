"""
This module contains the graph data structures used in Transiter.

The data structures here are somewhat complex, and potentially over-engineered, but
are an attempt to address the following issues:

(1) Many graphs in Transiter are immutable. An ordered graph cannot have its nodes
    edges changed, for example, without potentially breaking the ordering property.
    The same applied for a tree and a path. Thus, significant effort is made to
    support immutable graphs.

(2) On the other hand, enforcing immutability throughout the code base can be
    inefficient as it means small operations involve copying the graph to a new,
    mutable graph before the operation and, potentially, copying the results to
    a new immutable graph after the operation.

(3) Given the existence of an immutable graph type, an immutable tree type is more
    efficiently implemented by composing the graph rather than inheriting from it.
    This way the internal graph data structures don't need to be copied as part of
    the initialization operation.

This has led to the following class layout:

- An abstract class AbstractGraph which describes the basic operations on a graph.
    This class contains nodes of type AbstractNode.

- A concrete Graph class which implements AbstractGraph and provides an immutable
    graph type. Its nodes are of type Graph.Node.

- A concrete MutableGraph class which extends Graph to contain mutable methods. It
    uses nodes of type MutableGraph.Node, which support mutation.

- An semi-abstract class ComposedGraph which enables creating graphs that are
    based on other graphs by composition. ComposedGraph implements AbstractGraph. A
    ComposedGraph contains an immutable backing graph, and all of the AbstractGraph
    methods are delegated to this backing graph.

- Concrete OrderedGraph, Tree, OrderedTree and Path which extend ComposedGraph
    and provide additional features -- for example, iterating over the nodes in an
    OrderedGraph returns the nodes as given by the order.
"""

from abc import abstractmethod, ABCMeta
from collections import defaultdict
from typing import Iterator, Set, FrozenSet, Iterable, Tuple, Optional, Dict, Collection


class AbstractNode(metaclass=ABCMeta):
    """
    Interface for Transiter's node types.
    """

    label = None

    @property
    @abstractmethod
    def in_nodes(self) -> Collection["AbstractNode"]:
        """
        Return all nodes A such that (A, this node) is an edge of the graph.
        """

    @property
    @abstractmethod
    def out_nodes(self) -> Collection["AbstractNode"]:
        """
        Return all nodes A such that (this node, A) is an edge of the graph.
        """


class AbstractGraph(metaclass=ABCMeta):
    """
    Interface for Transiter's graph types.
    """

    @abstractmethod
    def reverse(self) -> None:
        """
        Reverse the orientation of the graph.

        This switches the orientation of each edge in the graph from (node_1 -> node_2)
        to (node_2 -> node_1). Implementations below achieve this in O(1).
        """

    @abstractmethod
    def edge_label_tuples(self) -> Iterator[Tuple]:
        """
        Return all tuples (label_1, label_2) corresponding to edges of the graph.
        """

    @abstractmethod
    def get_node(self, label) -> Optional[AbstractNode]:
        """
        Return a node given its label, or None if no such node exists.
        """

    @abstractmethod
    def nodes(self) -> Iterator[AbstractNode]:
        """
        Return all nodes in the graph.
        """

    @abstractmethod
    def sources(self) -> Iterator[AbstractNode]:
        """
        Return all nodes that have no in-edges.
        """

    @abstractmethod
    def immutable(self) -> "Graph":
        """
        Return an immutable graph that is identical to this graph.
        """

    @abstractmethod
    def mutable(self) -> "MutableGraph":
        """
        Return a mutable graph that is identical to this graph.
        """

    @abstractmethod
    def __len__(self):
        """
        Return the number of nodes in the graph.
        """

    def __eq__(self, other):
        if not isinstance(other, AbstractGraph):
            print("This graph is not equal to a non-AbstractGraph object")
            return False
        if len(self) != len(other):
            print(
                f"This graph has a different number of nodes ({len(self)})"
                f" than the other graph ({len(other)})"
            )
            return False
        for other_node in other.nodes():
            other_label = other_node.label
            self_node = self.get_node(other_label)
            if self_node is None:
                print(
                    f"The other graph has a node with label '{other_label}'"
                    f" that this node does not have"
                )
                return False
            self_out_node_labels = set(node.label for node in self_node.out_nodes)
            other_out_node_labels = set(node.label for node in other_node.out_nodes)
            if self_out_node_labels != other_out_node_labels:
                print(
                    "The other graph has a different edge set than this graph\n"
                    f"This: edges from {other_label} to {self_out_node_labels}\n"
                    f"Other: edges from {other_label} to {other_out_node_labels}"
                )
                return False
        return True


class Graph(AbstractGraph):
    """
    Immutable graph implementation of an abstract graph.
    """

    class Orientation:
        """
        Data structure that records the orientation of a directed graph.

        This data structure is basically a wrapper around a boolean variable which
        records whether the graph has its initial orientation (Orientation.INITIAL)
        or has been reversed (Orientation.REVERSED).

        The structure mainly exists for memory efficiency purposes. Instead of using
        this structure, it would be possible for each Node in a graph to hold a
        reference to the graph it is in, and then store the orientation as a variable
        of the graph. However this introduces a circular reference which makes the
        graph less to garbage collect. Instead, the graph and every node hold a
        reference to an instance of this class.
        """

        INITIAL = False
        REVERSED = True

        def __init__(self):
            self._orientation = self.INITIAL

        def reverse(self):
            self._orientation = self._orientation is False

        def __eq__(self, other):
            return self._orientation is other

    class Node(AbstractNode):
        """
        Data structure representing a node in an immutable graph.

        WARNING: this data structure should not be initialized directly. It should only
        exist and be used within the context of a graph. If you use it outside that
        context it may spontaneously lose all of its edges.
        """

        def __init__(self, label, orientation: "Graph.Orientation"):
            self.label = label
            self._adjacent_nodes = {
                True: None,
                False: None,
            }  # type: Dict[bool, Optional[FrozenSet[Graph.Node]]]
            self._orientation = orientation

        @property
        def in_nodes(self) -> FrozenSet["Graph.Node"]:
            return self._get_nodes(self._orientation == Graph.Orientation.INITIAL)

        @property
        def out_nodes(self) -> FrozenSet["Graph.Node"]:
            return self._get_nodes(self._orientation == Graph.Orientation.REVERSED)

        @in_nodes.setter
        def in_nodes(self, nodes: Iterator["Graph.Node"]) -> None:
            """
            Set the in nodes of this node.

            Note that in line with the data structure being immutable this operation
            can only be performed once.
            """
            self._set_nodes(self._orientation == Graph.Orientation.INITIAL, nodes)

        @out_nodes.setter
        def out_nodes(self, nodes: Iterator["Graph.Node"]) -> None:
            """
            Set the out nodes of this node.

            Note that in line with the data structure being immutable this operation
            can only be performed once.
            """
            self._set_nodes(self._orientation == Graph.Orientation.REVERSED, nodes)

        def _get_nodes(self, key) -> FrozenSet["Graph.Node"]:
            if self._adjacent_nodes[key] is None:
                raise RuntimeError(
                    "Attempting to access the edges of an immutable "
                    "node before they have been set."
                )
            return self._adjacent_nodes[key]

        def _set_nodes(self, key, nodes):
            if self._adjacent_nodes[key] is not None:
                raise RuntimeError(
                    "Attempting to set the edges of an immutable node again."
                )
            self._adjacent_nodes[key] = frozenset(nodes)

        def _clear_edges(self):
            """
            Remove all of the edges of this node. This method is only used to enable
            safer garbage collection and should in general not be used as it breaks the
            immutable nature of the data structure.
            """
            self._adjacent_nodes = {True: None, False: None}

        def __eq__(self, other):
            return self.label == other.label

        def __hash__(self):
            return hash(self.label)

        def __repr__(self):
            return (
                f"Graph.Node(label={self.label}, "
                f"in_nodes={list(node.label for node in self.in_nodes)}, "
                f"out_nodes={list(node.label for node in self.out_nodes)})"
            )

    def __init__(self, graph: "AbstractGraph" = None):
        self._orientation = self.Orientation()
        self._label_to_node = {}
        if graph is None:
            return
        self._init_label_to_node(
            graph.edge_label_tuples(), [node.label for node in graph.nodes()]
        )

    def _init_label_to_node(self, edge_label_tuples, additional_labels=None):
        label_to_in_nodes = defaultdict(lambda: set())
        label_to_out_nodes = defaultdict(lambda: set())

        if additional_labels is not None:
            for label in additional_labels:
                self._create_node(label)

        for label_1, label_2 in edge_label_tuples:
            for label in (label_1, label_2):
                self._create_node(label)
            label_to_in_nodes[label_2].add(self._label_to_node[label_1])
            label_to_out_nodes[label_1].add(self._label_to_node[label_2])

        for label in self._label_to_node.keys():
            self._label_to_node[label].in_nodes = label_to_in_nodes[label]
            self._label_to_node[label].out_nodes = label_to_out_nodes[label]

    def _create_node(self, label) -> "Graph.Node":
        if label not in self._label_to_node:
            self._label_to_node[label] = self.Node(label, self._orientation)
        return self._label_to_node[label]

    # Implementation of abstract methods

    def reverse(self) -> None:
        self._orientation.reverse()

    def edge_label_tuples(self) -> Iterator[Tuple]:
        for in_node in self.nodes():
            for out_node in in_node.out_nodes:
                yield in_node.label, out_node.label

    def get_node(self, label) -> Optional["Graph.Node"]:
        return self._label_to_node.get(label)

    def nodes(self) -> Iterator["Graph.Node"]:
        yield from self._label_to_node.values()

    def sources(self) -> Iterator["Graph.Node"]:
        for node in self.nodes():
            if len(node.in_nodes) == 0:
                yield node

    def immutable(self) -> "Graph":
        return self

    def mutable(self) -> "MutableGraph":
        return MutableGraph(self)

    # Class methods for creating immutable graphs

    @classmethod
    def build_from_edge_label_tuples(cls, tuples, additional_labels=None) -> "Graph":
        """
        Build a graph from a iterator of edge label tuples.
        """
        graph = cls()
        graph._init_label_to_node(tuples, additional_labels)
        return graph

    @classmethod
    def build_from_nodes(cls, nodes: Iterable[Node]) -> "Graph":
        """
        Build a graph from nodes of another graph.
        """
        labels = set()
        edge_label_tuples = set()
        for node in nodes:
            labels.add(node.label)
            for out_node in node.out_nodes:
                edge_label_tuples.add((node.label, out_node.label))
        return cls.build_from_edge_label_tuples(edge_label_tuples, labels)

    @classmethod
    def union(cls, graphs: Iterable[AbstractGraph]) -> "Graph":
        """
        Build a graph as a union of other graphs.
        """
        edge_label_tuples = set()
        for component in graphs:
            edge_label_tuples.update(component.edge_label_tuples())
        return cls.build_from_edge_label_tuples(edge_label_tuples)

    def __del__(self):
        """
        Perform pre-deletion memory clean-up.

        Before deleting the graph, clear all of the circular references in the graph's
        nodes. This ensures that the graph and all its dependencies can be garbage
        collected using Python's synchronous (i.e., reference count based) garbage
        collection procedure, rather than relying on the asynchronous procedure. As
        well as being more memory efficient, this helps avoid memory leaks.
        """
        for node in self.nodes():
            # I know we're being bold, but keeping _clear_edges protected is worth
            # it to prevent others being even more bold.
            # noinspection PyProtectedMember
            node._clear_edges()

    def __contains__(self, item):
        if isinstance(item, AbstractNode):
            item = item.label
        return item in self._label_to_node

    def __len__(self):
        return len(self._label_to_node)


class MutableGraph(Graph):
    """
    Mutable graph implementation of an abstract graph.
    """

    class Node(Graph.Node):
        """
        Mutable node type.
        """

        def __init__(self, label, orientation: "Graph.Orientation"):
            self.label = label
            self._adjacent_nodes = {True: set(), False: set()}
            self._orientation = orientation

        def _get_nodes(self, key) -> Set["MutableGraph.Node"]:
            if self._adjacent_nodes[key] is None:
                return set()
            return self._adjacent_nodes[key]

        def _set_nodes(self, key, nodes):
            self._adjacent_nodes[key] = set(nodes)

    def edge_tuples(self):
        """
        Return all (A, B) node tuples where A -> B is an edge.
        """
        for in_node in self.nodes():
            for out_node in in_node.out_nodes:
                yield in_node, out_node

    def create_node(self, label):
        """
        Create a node with the given label.
        """
        return self._create_node(label)

    def create_edge_using_labels(self, label_1, label_2) -> None:
        """
        Create an edge between two nodes identified by their labels.

        Raises a ValueError if the graph does not contain nodes with the given labels.
        """
        for label in (label_1, label_2):
            if label not in self._label_to_node:
                raise ValueError(f"Graph has no node with label '{label}'")
        node_1 = self._label_to_node[label_1]
        node_2 = self._label_to_node[label_2]
        node_1.out_nodes.add(node_2)
        node_2.in_nodes.add(node_1)

    def delete_node(self, node) -> None:
        """
        Delete a node from the graph, along with all edges it is in.
        """
        for in_node_label in set(in_node.label for in_node in node.in_nodes):
            self.delete_edge_using_labels(in_node_label, node.label)
        for out_node_label in set(out_node.label for out_node in node.out_nodes):
            self.delete_edge_using_labels(node.label, out_node_label)
        del self._label_to_node[node.label]

    def delete_edge_using_labels(self, label_1, label_2) -> None:
        """
        Delete an edge from the graph using the labels of the adjacent nodes.
        """
        for label in (label_1, label_2):
            if label not in self._label_to_node:
                raise ValueError(f"Graph has no node with label '{label}'")
        node_1 = self._label_to_node[label_1]
        node_2 = self._label_to_node[label_2]
        if node_1 not in node_2.in_nodes:
            raise ValueError(f"Graph has no node edge ({label_1}, {label_2})")
        node_2.in_nodes.remove(node_1)
        node_1.out_nodes.remove(node_2)

    def immutable(self) -> "Graph":
        return Graph(self)

    def mutable(self) -> "MutableGraph":
        return self


def _delegating_method_factory(method_name):
    def delegating_method(self, *args, **kwargs):
        return getattr(self.backing_graph, method_name)(*args, **kwargs)

    return delegating_method


# Methods are added dynamically using the delegating method factory.
# noinspection PyAbstractClass
class ComposedGraph(AbstractGraph):
    """
    Objects of this type are graphs with additional metadata.

    The backing graph is stored via composition, as opposed to inheritance.
    """

    def __init__(self, graph: AbstractGraph):
        self._backing_graph = graph.immutable()

    @property
    def backing_graph(self):
        return self._backing_graph

    # AbstractGraph's __abstractmethod__ variable exists!
    # noinspection PyUnresolvedReferences
    for method_name in AbstractGraph.__abstractmethods__:
        vars()[method_name] = _delegating_method_factory(method_name)


# noinspection PyAbstractClass
class Tree(ComposedGraph):
    """
    Rooted tree type.
    """

    def __init__(self, graph: AbstractGraph, root: AbstractNode):
        """
        Initialize a new tree.

        Note that this is a good faith constructor. No attempt is made to verify that
        the graph is a tree, or that the root is in fact the root of the tree.

        :param graph: the graph to cast as a Tree
        :param root: the root of the tree
        """
        ComposedGraph.__init__(self, graph)
        self.root = self.get_node(root.label)

    def is_out_tree(self) -> bool:
        return not self.is_out_tree()

    def is_in_tree(self) -> bool:
        return len(self.root.in_nodes) == 1

    def __eq__(self, other):
        return AbstractGraph.__eq__(self, other) and self.root.label == other.root.label


# noinspection PyAbstractClass
class OrderedGraph(ComposedGraph):
    """
    Graph with a defined ordering of nodes.
    """

    def __init__(self, graph: AbstractGraph, ordering: Iterator[AbstractNode]):
        ComposedGraph.__init__(self, graph)
        self._ordering = [self._backing_graph.get_node(node.label) for node in ordering]

    def nodes(self):
        yield from self._ordering

    def reverse(self) -> None:
        self._backing_graph.reverse()
        self._ordering.reverse()


# noinspection PyAbstractClass
class Path(OrderedGraph):
    """
    A path graph data type.
    """

    def __init__(self, graph: AbstractGraph, head: AbstractNode):
        ordering = [head]
        while len(head.out_nodes) > 0:
            head = next(iter(head.out_nodes))
            ordering.append(head)
        OrderedGraph.__init__(self, graph, ordering)

    @classmethod
    def build_from_label_list(cls, label_list):
        if len(set(label_list)) != len(label_list):
            raise ValueError("Label list must contain unique elements")
        edge_tuples = set()
        for i in range(len(label_list) - 1):
            edge_tuples.add((label_list[i], label_list[i + 1]))
        graph = Graph.build_from_edge_label_tuples(edge_tuples, label_list)
        return cls(graph, graph.get_node(label_list[0]))


# noinspection PyAbstractClass
class OrderedTree(OrderedGraph, Tree):
    """
    A type representing a rooted tree with a defined ordering.
    """

    def __init__(self, tree: Tree, ordering: Iterator[AbstractNode]):
        OrderedGraph.__init__(self, tree, ordering)
        self.root = tree.root

    def reverse(self) -> None:
        self._backing_graph.reverse()
        self._ordering.reverse()


class Stack:
    def __init__(self, initial_elements: Iterable = None):
        if initial_elements is None:
            initial_elements = []
        self._store = list(initial_elements)

    def push(self, element):
        self._store.append(element)

    def pop(self):
        if len(self._store) == 0:
            raise LookupError("Stack has zero elements; cannot pop.")
        return self._store.pop()

    def __len__(self):
        return len(self._store)
