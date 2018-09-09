import re



#Benchmark performance again just doing it manually
re_string = '^[A-Z0-9]{6,8}-[A-Z0-9]{4,5}-(?P<day>Weekday|Sunday|Saturday)-[0-9]{2}_(?P<hour>[0-9]{2})(?P<minute>[0-9]{2})[0-9]{2}_(?P<route_id>[A-Z0-9]+)..(?P<direction>[SN])[A-Z0-9]{3,6}$'
re_pattern = re.compile(re_string)

def interpret_mta_trip_id(mta_trip_id):
    if mta_trip_id[0:4] == 'SIR-':
        mta_trip_id = mta_trip_id[4:]

    re_match = re_pattern.search(mta_trip_id)
    if re_match:
        #print(re_match.group('A'))
        total_hours = int(re_match.group('hour'))+int(re_match.group('minute'))/60
        return (re_match.group('day'), total_hours, re_match.group('route_id'),
        re_match.group('direction'))
    else:
        print('Error: could not match trip_id: {}'.format(mta_trip_id))
        return None

def construct(data_iter):


    route_1 = ['A02', 'A03', 'A05', 'A06', 'A07', 'A09', 'A12', 'A15', 'A24', 'A27', 'A28', 'A31', 'A32', 'A34', 'A36', 'A38', 'A40', 'A41', 'A42', 'A46', 'A48', 'A51', 'A55', 'A57', 'A59', 'A60', 'A61', 'H02', 'H03', 'H04', 'H06', 'H07', 'H08', 'H09', 'H10', 'H11']
    route_2 = ['A02', 'A03', 'A05', 'A06', 'A07', 'A09', 'A12', 'A15', 'A24', 'A27', 'A28', 'A31', 'A32', 'A34', 'A36', 'A38', 'A40', 'A41', 'A42', 'A46', 'A48', 'A51', 'A55', 'A57', 'A59', 'A60', 'A61', 'A63', 'A64', 'A65']
    #return



    g = route_graph_from_paths([route_2, route_1])
    #for sources in g:
    #    for (v_1, v_2) in sources.edges():
    #        print('({}, {})'.format(v_1.stop_id, v_2.stop_id))


    graph = DirectedGraph()
    graph.sources = g
    topological_sort(graph)
    return
    mta_trip_id = None
    recording = False
    stop_ids = []
    i = 1
    for row in data_iter:
        if row['trip_id'] != mta_trip_id:


            # This won't be executed for the last trip :/
            if recording:
                print(stop_ids)

            stop_ids = []
            mta_trip_id = row['trip_id']
            #print(mta_trip_id)
            (day, hour, route_id, direction) = interpret_mta_trip_id(mta_trip_id)
            if (hour < 12 or hour > 13 or route_id != 'A' or direction == 'N'):
                recording = False
                continue

            recording = True

        if recording:
            stop_id = row['stop_id'][:3]
            stop_ids.append(stop_id)


            #if result is None:
            #    return
            #print(result)
            i+=1
            #if i>100:
            #    break
        #if reading_rows
        #print(row)
#trip_id,arrival_time,departure_time,stop_id,stop_sequence,stop_headsign,pickup_type,drop_off_type,shape_dist_traveled
#ASP18GEN-1037-Sunday-00_000600_1..S03R,00:06:00,00:06:00,101S,1,,0,0,

# Lets revert to also having a PathVertex as well
class Node():

    def __init__(self, stop_id, kind='Path'):
        self.stop_id = stop_id
        self.next = set()
        self.prev = set()
        self.visited = False
        self.kind = kind
        pass

    def __repr__(self):
        line_1 = '{} vertex ({}); local graph structure: '.format(self.kind, self.stop_id)
        line_2 = ''
        if len(self.prev) > 0:
            line_2 += '({}) -> '.format(', '.join([v.stop_id for v in self.prev]))
        line_2 += '\033[1m({})\033[0m'.format(self.stop_id)
        if len(self.next) > 0:
            line_2 += ' -> ({})'.format(', '.join([v.stop_id for v in self.next]))

        return line_1 + line_2;

    def edges(self):
        for node in self.next:
            yield (self, node)
            yield from node.edges()
# slow? Maybe could do faster with just path node
            # Also in cyclic graph this leads to infinite loop
        pass


#use builtin enumerate

def list_to_nodes(l):

    a = 3
    b = 3
    c = a + b
    c = b +

    a = ase


    if len(l) == 0:
        return None

    first = Node(l[0])

    a = first

    for k in range(1,len(l)):
        b = Node(l[k])
        a.next.add(b)
        b.prev.add(a)
        a = b
    return first

def route_graph_from_paths(paths):
    # returns a lists of nodes representing the topoligically sorted
    # route map
    # Two step process: first construct the graph
    # The topoligically sort it
    if len(paths) == 0:
        return []

    # probaby we
    paths = [list_to_nodes(path) for path in paths]

    return graph_from_path_graphs(paths)

    print('# of sources: {}'.format(len(sources)))
    for source in sources:
        while(len(source.next) > 0):
            print(source)
            source = next(iter(source.next))
        print(source)




def _edge_tuples(origin):
    tuples = set()
    for vertex in origin.next:
        tuples.add((origin.stop_id, vertex.stop_id))
        if not vertex.visited:
            tuples.update(_edge_tuples(vertex))

    return tuples


def edge_tuples(sources):
    tuples = set()
    for source in sources:
        if not source.visited:
            tuples.update(_edge_tuples(source))
    return tuples


def graph_from_path_graphs(paths):

    sources = set()
    sinks = set()
    graph_vertices_by_label = {}
    nodes_by_stop_id = {} #deprecate

    for path in paths:

        last_path_vertex_already_in_graph = None


        # Add the first vertex of the path, if needed
        if path.stop_id not in graph_vertices_by_label:
            #print('creating source {}'.format(path.stop_id))
            graph_vertices_by_label[path.stop_id] = Node(path.stop_id, kind='Graph')
            #path_node_stop_ids.add(path.stop_id)
            sources.add(graph_vertices_by_label[path.stop_id])
        else:
            last_path_vertex_already_in_graph = path

        for (v_1, v_2) in path.edges():
            graph_v_1 = graph_vertices_by_label[v_1.stop_id]


            print('[0] edge ({},{})'.format(v_1.stop_id, v_2.stop_id))
            if v_2.stop_id not in graph_vertices_by_label:
                #print('creating {}'.format(v_2.stop_id))
                graph_vertices_by_label[v_2.stop_id] = Node(v_2.stop_id, kind='Graph')
                graph_v_2 = graph_vertices_by_label[v_2.stop_id]
                graph_v_1.next.add(graph_v_2)
                graph_v_2.prev.add(graph_v_1)
                continue

            graph_v_2 = graph_vertices_by_label[v_2.stop_id]
            print('[1] edge ({},{})'.format(v_1.stop_id, v_2.stop_id))

            if v_1 == last_path_vertex_already_in_graph:
                last_path_vertex_already_in_graph = v_2
                continue

            graph_v_1.next.add(graph_v_2)
            graph_v_2.prev.add(graph_v_1)
            if graph_v_2 in sources:
                sources.remove(graph_v_2)

            print('[2] edge ({},{})'.format(v_1.stop_id, v_2.stop_id))
            if last_path_vertex_already_in_graph is None:
                last_path_vertex_already_in_graph = v_2
                continue

            print('[3] edge ({},{})'.format(v_1.stop_id, v_2.stop_id))
            last_graph_vertex = graph_vertices_by_label[
                last_path_vertex_already_in_graph.stop_id]

            if graph_v_2 in last_graph_vertex.next:
                print('[4] edge ({},{})'.format(v_1.stop_id, v_2.stop_id))
                last_graph_vertex.next.remove(graph_v_2)
                graph_v_2.prev.remove(last_graph_vertex)

            last_path_vertex_already_in_graph = v_2

    return sources


"""
For tests, create lists of ids and then a list of tuples of edges

Paths: [['a', 'b', 'c'], ['a', 'w', 'z', 'b', 'c']
Edges: [(a,w) (w,z) (z,b)



We need a lot of tests!!

Make the tests and then continue debugging

"""




class DirectedGraph():

    def __init__(self):
        self.sources = None
        self.sinks = None

    #write an iterator over all nodes

class DirectedGraphNode():

    def __init__(self):
        self.prev = set()
        self.next = set()
        pass

def _add_directed_path_edge(node_a, node_b):
    pass

class DirectedPathNode():

    def __init__(self):
        self._prev = None
        self._next = None

    @property
    def next(self):
        return self._next

    @next.setter(self, node):
        _add_directed_path_edge(self, node)

    @prev.setter(self, node):
        _add_directed_path_edge(node, self)


# Generic top sort algoirithm with some special properties:
#   The connected components of the graph will be together
#   Nodes of the form A -> B -> C will be next to each toher
def topological_sort(graph):

    sorted_graph = []
    next_nodes = graph.sources

    # FIrst iterate over the graph and copy the next and previous sets
    # start at a node
    # keep on going until we get to a node that has alternative in edges
    #  (while doing this remember the first node with alternate out edges)
    #  such a node will not have in edges and so will be a candidate to
    #    start again
    #follow these edges backwards to eventually get to a node with no in edges



    #while len(next_nodes) > 0:
    return sorted_graph










def test_graph_from_path_graphs():
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

    for test in test_data:
        paths = [list_to_nodes(path) for path in test['paths']]
        g = graph_from_path_graphs(paths)
        if edge_tuples(g) == test['edges']:
            print('Test passed')
        else:
            print('Paths: {}'.format(test['paths']))
            print('Expected edges: {}'.format(test['edges']))
            print('Actual edges: {}'.format(edge_tuples(g)))
            print('Test failed')
    return


test_graph_from_path_graphs()
