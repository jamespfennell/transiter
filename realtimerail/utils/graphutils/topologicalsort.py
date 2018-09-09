
class DirectedGraph():

    def __init__(self):
        self.sources = set()
        self.sinks = set()

    #write an iterator over all nodes

class DirectedGraphNode():

    def __init__(self, label=None):
        self.label = label
        self._prev = set()
        self._next = set()
        pass

    @property
    def next(self):
        return self._next

    @property
    def prev(self):
        return self._prev


def add_directed_graph_edge(from_node, to_node):
    from_node._next.add(to_node)
    to_node._prev.add(from_node)
    pass

def remove_directed_graph_edge(from_node, to_node):
    from_node._next.remove(to_node)
    to_node._prev.remove(from_node)

class DirectedPathNode():

    def __init__(self):
        self._prev = None
        self._next = None

    @property
    def next(self):
        return self._next

    @property
    def prev(self):
        return self._prev
# Next
# (1) Improve the algorithm to keep connected components together
# (2) How to conserve the edges?
# (3) Write many tests for this

# Generic top sort algoirithm with some special properties:
#   The connected components of the graph will be together (NOT TRUE SO FAR!)
#   Nodes of the form A -> B -> C will be next to each toher
def topological_sort(graph):

    sorted_graph = []
    sources = set(graph.sources)
    while(len(sources)>0):
        vertex = sources.pop()
        while(vertex is not None):
            sorted_graph.append(vertex)
            if len(vertex._next) == 0:
                vertex = None
                continue

            potential_vertex = None
            for next_vertex in [v for v in vertex._next]:
                remove_directed_graph_edge(vertex, next_vertex)
                if len(next_vertex._prev) == 0:
                    potential_vertex = next_vertex
                    sources.add(potential_vertex)
            if potential_vertex is not None:
                sources.remove(potential_vertex)
            vertex = potential_vertex

    return sorted_graph


def construct_graph_from_edge_tuples(edges):

    tag_to_vertex = {}
    for edge in edges:
        for tag in edge:
            if tag not in tag_to_vertex:
                tag_to_vertex[tag] = DirectedGraphNode(tag)
    for (tag_1, tag_2) in edges:
        add_directed_graph_edge(tag_to_vertex[tag_1], tag_to_vertex[tag_2])

    graph = DirectedGraph()
    for vertex in tag_to_vertex.values():
        if len(vertex._prev) == 0:
            graph.sources.add(vertex)
        if len(vertex._next) == 0:
            graph.sinks.add(vertex)

    return graph


def test():
    edges = [('a', 'b'), ('b', 'c'), ('d', 'c'), ('c', 'e'), ('c', 'f'), ('f', 'g')]
    graph = construct_graph_from_edge_tuples(edges)
    sorted_graph = topological_sort(graph)
    for vertex in sorted_graph:
        print(vertex.label)
    print('Hello')
