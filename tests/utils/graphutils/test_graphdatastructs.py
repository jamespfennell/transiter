import unittest
from transiter.utils.graphutils import graphdatastructs


class TestGraphDataStructs(unittest.TestCase):
    def setUp(self):
        edges = [('a', 'b'), ('c', 'd'), ('b', 'c')]
        self.graph_1 = graphdatastructs.construct_graph_from_edge_tuples(edges)
        edges = [('a', 'b'), ('c', 'd'), ('c', 'b')]
        self.graph_2 = graphdatastructs.construct_graph_from_edge_tuples(edges)
        edges = [('a', 'b'), ('b', 'c'), ('b', 'd')]
        self.graph_3 = graphdatastructs.construct_graph_from_edge_tuples(edges)
        edges = [('a', 'b'), ('b', 'c'), ('c', 'a')]
        self.graph_4 = graphdatastructs.construct_graph_from_edge_tuples(edges)

    def test_is_path_1(self):
        self.assertTrue(self.graph_1.is_path())

    def test_is_path_2(self):
        self.assertFalse(self.graph_2.is_path())

    def test_is_path_3(self):
        self.assertFalse(self.graph_3.is_path())

    def test_is_path_4(self):
        self.assertFalse(self.graph_3.is_path())

    def test_cast_to_path_1(self):
        path = self.graph_1.cast_to_path()
        expected = ['a', 'b', 'c', 'd']
        i = 0
        for vertex in path.vertices():
            self.assertEquals(expected[i], vertex.label)
            i += 1

    def test_cast_to_path_2(self):
        self.assertRaises(graphdatastructs.NotCastableAsAPathError,
            self.graph_2.cast_to_path)

    def test_cast_to_path_3(self):
        self.assertRaises(graphdatastructs.NotCastableAsAPathError,
                          self.graph_3.cast_to_path)

    def test_equal_graphs_1(self):
        self.assertEqual(self.graph_1, self.graph_1)

    def test_equal_graphs_2(self):
        self.assertEqual(self.graph_2, self.graph_2)

    def test_equal_graphs_3(self):
        self.assertEqual(self.graph_3, self.graph_3)

    def test_not_equal_graphs_1_2(self):
        self.assertNotEqual(self.graph_1, self.graph_2)

    def test_not_equal_graphs_1_3(self):
        self.assertNotEqual(self.graph_1, self.graph_3)

    def test_not_equal_graphs_2_3(self):
        self.assertNotEqual(self.graph_2, self.graph_3)

    def test_not_equal_graphs_2_4(self):
        self.assertNotEqual(self.graph_2, self.graph_4)

