"""
This module contains a single path stitcher algorithm.

Stitching means combining multiple paths with shared vertices into a single
graph. Using an adjacency matrix representation this is trivial but highly
space inefficient.

The present algorithm does not use an adjacency matrix. In addition, it
also makes some 'optimizations' to make subsequent topological sorting
of the graph easier. Specifically, given two paths:

    A--B--C--D
    A-----C--E

the algorithm will output

    A--B--C--D
           \
            E

In future versions of Transiter this behaviour will change because we don't
really want to lose the edges here. Instead, the path sticher will mark
certain edges 'redundant for sorting'. This way we can keep the edges but
still make it easier to sort.
"""
from . import graphdatastructs


def stitch(paths) -> graphdatastructs.DirectedGraph:
    """
    Stitch the paths. See module docs for details.

    :param paths: list of lists of strings with the vertex labels
    :return: the graph
    """
    sources = set()
    sinks = set()
    graph_vertices_by_label = {}

    for path in paths:

        last_path_vertex_already_in_graph = None

        # Add the first vertex of the path, if needed
        first_vertex = path.first()
        if first_vertex.label not in graph_vertices_by_label:
            # print('creating source {}'.format(path.stop_id))
            graph_vertices_by_label[
                first_vertex.label
            ] = graphdatastructs.DirectedGraphVertex(first_vertex.label)
            sources.add(graph_vertices_by_label[first_vertex.label])
        else:
            last_path_vertex_already_in_graph = first_vertex

        for (v_1, v_2) in path.edges():
            graph_v_1 = graph_vertices_by_label[v_1.label]
            if v_2.label not in graph_vertices_by_label:
                # print('creating {}'.format(v_2.stop_id))
                graph_vertices_by_label[
                    v_2.label
                ] = graphdatastructs.DirectedGraphVertex(v_2.label)
                graph_v_2 = graph_vertices_by_label[v_2.label]
                graph_v_1.next.add(graph_v_2)
                graph_v_2.prev.add(graph_v_1)
                continue

            graph_v_2 = graph_vertices_by_label[v_2.label]

            if v_1 == last_path_vertex_already_in_graph:
                last_path_vertex_already_in_graph = v_2
                continue

            graph_v_1.next.add(graph_v_2)
            graph_v_2.prev.add(graph_v_1)
            if graph_v_2 in sources:
                sources.remove(graph_v_2)

            if last_path_vertex_already_in_graph is None:
                last_path_vertex_already_in_graph = v_2
                continue

            last_graph_vertex = graph_vertices_by_label[
                last_path_vertex_already_in_graph.label
            ]

            if graph_v_2 in last_graph_vertex.next:
                last_graph_vertex.next.remove(graph_v_2)
                graph_v_2.prev.remove(last_graph_vertex)

            last_path_vertex_already_in_graph = v_2

    graph = graphdatastructs.DirectedGraph()
    graph.sources = sources
    return graph
