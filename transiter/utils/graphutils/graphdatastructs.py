
class DirectedPath():

    #def __init__(self):
    #    self._vertices = []

    def __init__(self, label_list):
        self._vertices = [DirectedPathVertex(label) for label in label_list]
        for i in range(len(self._vertices)-1):
            self._vertices[i].next = self._vertices[i+1]
            self._vertices[i+1].prev = self._vertices[i]

    def edges(self):
        for i in range(len(self._vertices)-1):
            yield (self._vertices[i], self._vertices[i+1])
    def first(self):
        return self._vertices[0]

    def vertices(self):
        return self._vertices


class DirectedPathVertex():

    def __init__(self, label):
        self.label = label
        self.prev = None
        self.next = None
    """
    @property
    def next(self):
        return self._next

    @next.setter(self, node):
        _add_directed_path_edge(self, node)

    @prev.setter(self, node):
        _add_directed_path_edge(node, self)
    """

"""
    def __repr__(self):
        line_1 = '{} vertex ({}); local graph structure: '.format(self.kind, self.stop_id)
        line_2 = ''
        if len(self.prev) > 0:
            line_2 += '({}) -> '.format(', '.join([v.stop_id for v in self.prev]))
        line_2 += '\033[1m({})\033[0m'.format(self.stop_id)
        if len(self.next) > 0:
            line_2 += ' -> ({})'.format(', '.join([v.stop_id for v in self.next]))

        return line_1 + line_2;
"""

class NotCastableAsAPathError(Exception):
    pass

class DirectedGraph():

    def __init__(self):
        self.sources = set()

    # TODO: implmenet this and use it
    #def add_edge(vertex_a, vertex_b):
    #    pass

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
        """
        def add_edges_from_vertex(vertex):
            visited.add(vertex)
            for next in vertex.next:
                edges_set.add((vertex.label, next.label))
                if next not in visited:
                    add_edges_from_vertex(next)
        visited = set()
        edges_set = set()
        for source in self.sources:
            if source not in visited:
                add_edges_from_vertex(source)
        return edges_set
        """

    def is_path(self):
        if len(self.sources) > 1:
            return False
        vertex = next(iter(self.sources))
        while len(vertex.next) > 0:
            if len(vertex.next) > 1:
                return False
            vertex = next(iter(vertex.next))
        return True


    def cast_to_path(self):
        if len(self.sources) > 1:
            raise NotCastableAsAPathError()
        vertex = next(iter(self.sources))
        label_list = [vertex.label]
        while len(vertex.next) > 0:
            if len(vertex.next) > 1:
                raise NotCastableAsAPathError()
            vertex = next(iter(vertex.next))
            label_list.append(vertex.label)
        return DirectedPath(label_list)



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





class DirectedGraphVertex():
    def __init__(self, label):
        self.label = label
        self.prev = set()
        self.next = set()
    """

        @property
        def next(self):
            return self._next

        @property
        def prev(self):
            return self._prev
    """

class SortedDirectedGraph(DirectedGraph):

    def __init__(self, directed_graph, order):
        self.sources = directed_graph.sources
        self._order = order

    def vertices(self):
        for vertex in self._order:
            yield vertex
