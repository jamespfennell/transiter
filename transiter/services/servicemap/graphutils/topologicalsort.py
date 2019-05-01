"""
This class contains algorithms for topologically sorting graphs.
"""

from transiter.services.servicemap.graphutils import graphdatastructs


class ImpossibleToTopologicallySortGraph(Exception):
    """
    Exception thrown if the inputted directed graph contains a cycle.
    """

    pass


def sort(graph: graphdatastructs.DirectedGraph) -> graphdatastructs.SortedDirectedGraph:
    """
    Topologically sort a directed graph.

    The algorithm here is the basic topological sort algorithm, except the
    sorting has the following property. If there are vertices A, B, C, such
    (A,B) and (B,C) are edges, and there are no other edges out of A and B
    and in to B and C, then A, B and C will be consecutive in the sorting.

    :param graph: the directed graph to sort
    :type graph: graphdatastructs.SortedDirectedGraph
    :return: the sorted graph
    :rtype: graphdatastructs.SortedDirectedGraph
    :raise: ImpossibleToTopologicallySortGraph: if the graph cannot be sorted;
        i.e., it contains a cycle.
    """
    sorted_graph = []
    sources = set(graph.sources)
    for vertex in graph.vertices():
        vertex.t_next = set(vertex.next)
        vertex.t_prev = set(vertex.prev)

    if len(sources) == 0:
        raise ImpossibleToTopologicallySortGraph()

    while len(sources) > 0:
        vertex = sources.pop()
        while vertex is not None:
            sorted_graph.append(vertex)
            if len(vertex.t_next) == 0:
                vertex = None
                continue

            potential_vertex = None
            could_be = False
            for next_vertex in [v for v in vertex.t_next]:
                could_be = True
                vertex.t_next.remove(next_vertex)
                next_vertex.t_prev.remove(vertex)
                # remove_directed_graph_edge(vertex, next_vertex)
                if len(next_vertex.t_prev) == 0:
                    potential_vertex = next_vertex
                    sources.add(potential_vertex)
            if could_be and potential_vertex is None and len(sources) == 0:
                raise ImpossibleToTopologicallySortGraph()
            # This step ensures that the next vertex considered is connected
            # to the vertex just considered
            if potential_vertex is not None:
                sources.remove(potential_vertex)
            vertex = potential_vertex

    for vertex in graph.vertices():
        del vertex.t_next
        del vertex.t_prev
    return graphdatastructs.SortedDirectedGraph(graph, sorted_graph)
