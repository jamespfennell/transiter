from . import graphdatastructs

# Next
# (1) Improve the algorithm to keep connected components together
# (2) How to conserve the edges?
# (3) Write many tests for this

# Generic top sort algoirithm with some special properties:
#   The connected components of the graph will be together (NOT TRUE SO FAR!)
#   Nodes of the form A -> B -> C will be next to each toher
def sort(graph):

    sorted_graph = []
    sources = set(graph.sources)
    for vertex in graph.vertices():
        vertex.t_next = set(vertex.next)
        vertex.t_prev = set(vertex.prev)

    while(len(sources)>0):
        vertex = sources.pop()
        while(vertex is not None):
            sorted_graph.append(vertex)
            if len(vertex.t_next) == 0:
                vertex = None
                continue

            potential_vertex = None
            for next_vertex in [v for v in vertex.t_next]:
                vertex.t_next.remove(next_vertex)
                next_vertex.t_prev.remove(vertex)
                #remove_directed_graph_edge(vertex, next_vertex)
                if len(next_vertex.t_prev) == 0:
                    potential_vertex = next_vertex
                    sources.add(potential_vertex)
            if potential_vertex is not None:
                sources.remove(potential_vertex)
            vertex = potential_vertex

    for vertex in graph.vertices():
        del vertex.t_next
        del vertex.t_prev
    return graphdatastructs.SortedDirectedGraph(graph, sorted_graph)
