from . import graphdatastructs

def stitch(paths, quiet=True):
    def gobble(message):
        pass
    if quiet:
        print = gobble

    sources = set()
    sinks = set()
    graph_vertices_by_label = {}

    for path in paths:

        last_path_vertex_already_in_graph = None


        # Add the first vertex of the path, if needed
        first_vertex = path.first()
        if first_vertex.label not in graph_vertices_by_label:
            #print('creating source {}'.format(path.stop_id))
            graph_vertices_by_label[first_vertex.label] = graphdatastructs.DirectedGraphVertex(first_vertex.label)
            sources.add(graph_vertices_by_label[first_vertex.label])
        else:
            last_path_vertex_already_in_graph = first_vertex

        for (v_1, v_2) in path.edges():
            graph_v_1 = graph_vertices_by_label[v_1.label]


            print('[0] edge ({},{})'.format(v_1.label, v_2.label))
            if v_2.label not in graph_vertices_by_label:
                #print('creating {}'.format(v_2.stop_id))
                graph_vertices_by_label[v_2.label] = graphdatastructs.DirectedGraphVertex(v_2.label)
                graph_v_2 = graph_vertices_by_label[v_2.label]
                graph_v_1.next.add(graph_v_2)
                graph_v_2.prev.add(graph_v_1)
                continue

            graph_v_2 = graph_vertices_by_label[v_2.label]
            print('[1] edge ({},{})'.format(v_1.label, v_2.label))

            if v_1 == last_path_vertex_already_in_graph:
                last_path_vertex_already_in_graph = v_2
                continue

            graph_v_1.next.add(graph_v_2)
            graph_v_2.prev.add(graph_v_1)
            if graph_v_2 in sources:
                sources.remove(graph_v_2)

            print('[2] edge ({},{})'.format(v_1.label, v_2.label))
            if last_path_vertex_already_in_graph is None:
                last_path_vertex_already_in_graph = v_2
                continue

            print('[3] edge ({},{})'.format(v_1.label, v_2.label))
            last_graph_vertex = graph_vertices_by_label[
                last_path_vertex_already_in_graph.label]

            if graph_v_2 in last_graph_vertex.next:
                print('[4] edge ({},{})'.format(v_1.label, v_2.label))
                last_graph_vertex.next.remove(graph_v_2)
                graph_v_2.prev.remove(last_graph_vertex)

            last_path_vertex_already_in_graph = v_2

    graph = graphdatastructs.DirectedGraph()
    graph.sources = sources
    return graph





def test_stitch():
    test_data = [
        {
            'paths': [['b', 'w', 'c'],['b', 'c']],
            'edges': set([('b','w'), ('w', 'c')])
        },
        {
            'paths': [['a', 'b', 'c'], ['d', 'b', 'c']],
            'edges': set([('a', 'b'), ('d', 'b'), ('b', 'c')])
        },
        {
            'paths': [['a', 'b', 'c'], ['a', 'b', 'd']],
            'edges': set([('a', 'b'), ('b', 'c'), ('b', 'd')])
        },
        {
            'paths': [['a', 'b', 'c'], ['c', 'd', 'e']],
            'edges': set([('a', 'b'), ('b', 'c'), ('c', 'd'), ('d', 'e')])
        },
        {
            'paths': [['a', 'b', 'c'], ['e', 'f', 'g']],
            'edges': set([('a', 'b'), ('b', 'c'), ('e', 'f'), ('f', 'g')])
        },
        {
            'paths': [['b', 'c'],['b', 'w', 'c']],
            'edges': set([('b','w'), ('w', 'c')])
        },
        {
            'paths': [['a', 'b', 'c'], ['a', 'w', 'c']],
            'edges': set([('a', 'b'), ('b', 'c'), ('a', 'w'), ('w', 'c')])
        }
        ]

    passed = True
    print('Testing stitch()')
    for test in test_data:
        paths = [graphdatastructs.DirectedPath(path) for path in test['paths']]
        graph = stitch(paths)
        if graph.edges() == test['edges']:
            print(' - test passed')
        else:
            print('Paths: {}'.format(test['paths']))
            print('Expected edges: {}'.format(test['edges']))
            print('Actual edges: {}'.format(graph.edges()))
            print('Test failed')
            passed = False
    if passed:
        print('Test suite passed')
    return passed
#test_stitch()
