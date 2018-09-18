import unittest
from transiter.utils.graphutils import graphdatastructs
from transiter.utils.graphutils import topologicalsort


class TestTopologicalSort(unittest.TestCase):
    def test_sort(self):
        edges = [('a', 'b'), ('b', 'c'), ('d', 'c'), ('c', 'e'), ('c', 'f'), ('f', 'g')]
        graph = graphdatastructs.construct_graph_from_edge_tuples(edges)
        sorted_graph = topologicalsort.sort(graph)
        visited_labels = set()
        for vertex in sorted_graph.vertices():
            for prev in vertex.prev:
                self.assertTrue(prev.label in visited_labels)
            visited_labels.add(vertex.label)
