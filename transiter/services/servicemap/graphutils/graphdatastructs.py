"""
This module contains the graph data structures used in the service map code.
"""


class DirectedPath:
    def __init__(self, label_list):
        self._vertices = [DirectedPathVertex(label) for label in label_list]
        for i in range(len(self._vertices) - 1):
            self._vertices[i].next = self._vertices[i + 1]
            self._vertices[i + 1].prev = self._vertices[i]

    def edges(self):
        for i in range(len(self._vertices) - 1):
            yield (self._vertices[i], self._vertices[i + 1])

    def first(self):
        return self._vertices[0]

    def vertices(self):
        return self._vertices


class DirectedPathVertex:
    def __init__(self, label):
        self.label = label
        self.prev = None
        self.next = None


class NotCastableAsAPathError(Exception):
    """
    Thrown if a non-path directed graph is attempted to be case to a path.
    """

    pass


class DirectedGraph:
    def __init__(self):
        self.sources = set()

    def vertices(self):
        def add_vertices_from_vertex(vertex):
            visited.add(vertex)
            for next in vertex.next:
                if next not in visited:
                    add_vertices_from_vertex(next)

        visited = set()
        for source in self.sources:
            if source not in visited:
                add_vertices_from_vertex(source)
        return visited

    def edges(self):
        edges = set()
        for vertex in self.vertices():
            for next in vertex.next:
                edges.add((vertex.label, next.label))
        return edges

    def is_path(self):
        try:
            self.cast_to_path()
            return True
        except NotCastableAsAPathError:
            return False

    def cast_to_path(self) -> DirectedPath:
        """
        Cast the directed graph into a path.

        Raises NotCastableAsPathError if this is not possible! Consider using
        is_path instead for test for this case.
        """
        visited_labels = set()
        if len(self.sources) == 0:
            return DirectedPath([])
        if len(self.sources) > 1:
            raise NotCastableAsAPathError()
        vertex = next(iter(self.sources))
        label_list = [vertex.label]
        while len(vertex.next) > 0:
            if vertex.label in visited_labels:
                raise NotCastableAsAPathError()
            visited_labels.add(vertex.label)
            if len(vertex.next) > 1:
                raise NotCastableAsAPathError()
            vertex = next(iter(vertex.next))
            label_list.append(vertex.label)
        return DirectedPath(label_list)

    def __eq__(self, other):
        label_to_this_vs = {v.label: v for v in self.vertices()}
        label_to_other_vs = {v.label: v for v in other.vertices()}

        for label, this_vs in label_to_this_vs.items():
            other_vs = label_to_other_vs.get(label, None)
            if other_vs is None:
                return False
            if len(this_vs.prev - other_vs.prev) != 0:
                return False
            if len(this_vs.next - other_vs.next) != 0:
                return False
            del label_to_other_vs[label]

        return len(label_to_other_vs) == 0


def construct_graph_from_edge_tuples(edges):
    tag_to_vertex = {}
    for edge in edges:
        for tag in edge:
            if tag not in tag_to_vertex:
                tag_to_vertex[tag] = DirectedGraphVertex(tag)
    for (tag_1, tag_2) in edges:
        tag_to_vertex[tag_1].next.add(tag_to_vertex[tag_2])
        tag_to_vertex[tag_2].prev.add(tag_to_vertex[tag_1])

    graph = DirectedGraph()
    for vertex in tag_to_vertex.values():
        if len(vertex.prev) == 0:
            graph.sources.add(vertex)

    return graph


class DirectedGraphVertex:
    def __init__(self, label):
        self.label = label
        self.prev = set()
        self.next = set()


class SortedDirectedGraph(DirectedGraph):
    def __init__(self, directed_graph, order):
        self.sources = directed_graph.sources
        self._order = order

    def vertices(self):
        for vertex in self._order:
            yield vertex
