import unittest

from transiter.services.servicemap.graphutils import graphdatastructs, topologicalsort


class TestTopologicalSort(unittest.TestCase):
    def test_sort(self):
        """[Topological sort] Sort"""
        edges = [("a", "b"), ("b", "c"), ("d", "c"), ("c", "e"), ("c", "f"), ("f", "g")]
        graph = graphdatastructs.construct_graph_from_edge_tuples(edges)
        sorted_graph = topologicalsort.sort(graph)
        visited_labels = set()
        for vertex in sorted_graph.vertices():
            for prev in vertex.prev:
                self.assertTrue(prev.label in visited_labels)
            visited_labels.add(vertex.label)

    def test_impossible_to_sort_one(self):
        """[Topological sort] Impossible to sort, case 1"""
        edges = [("a", "b"), ("b", "c"), ("c", "d"), ("d", "a")]
        graph = graphdatastructs.construct_graph_from_edge_tuples(edges)
        self.assertRaises(
            topologicalsort.ImpossibleToTopologicallySortGraph,
            topologicalsort.sort,
            graph,
        )

    def test_impossible_to_sort_two(self):
        """[Topological sort] Impossible to sort, case 2"""
        edges = [("a", "b"), ("b", "c"), ("c", "d"), ("d", "b")]
        graph = graphdatastructs.construct_graph_from_edge_tuples(edges)
        self.assertRaises(
            topologicalsort.ImpossibleToTopologicallySortGraph,
            topologicalsort.sort,
            graph,
        )

    def test_impossible_to_sort_three(self):
        """[Topological sort] Impossible to sort, case 3"""
        edges = [("a", "b"), ("a", "a")]
        graph = graphdatastructs.construct_graph_from_edge_tuples(edges)
        self.assertRaises(
            topologicalsort.ImpossibleToTopologicallySortGraph,
            topologicalsort.sort,
            graph,
        )
