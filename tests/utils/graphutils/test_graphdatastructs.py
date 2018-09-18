import unittest
from transiter.utils.graphutils import graphdatastructs


class TestGraphDataStructs(unittest.TestCase):
    def setUp(self):
        edges = [('a', 'b'), ('c', 'd'), ('b', 'c')]
        self.graph_one = graphdatastructs.construct_graph_from_edge_tuples(edges)
        edges = [('a', 'b'), ('c', 'd'), ('c', 'b')]
        self.graph_two = graphdatastructs.construct_graph_from_edge_tuples(edges)

    def test_is_path_1(self):
        self.assertTrue(self.graph_one.is_path())

    def test_is_path_2(self):
        self.assertFalse(self.graph_two.is_path())

    def test_cast_to_path_1(self):
        path = self.graph_one.cast_to_path()
        expected = ['a', 'b', 'c', 'd']
        i = 0
        for vertex in path.vertices():
            self.assertEquals(expected[i], vertex.label)
            i += 1

    def test_cast_to_path_2(self):
        self.assertRaises(graphdatastructs.NotCastableAsAPathError,
            self.graph_two.cast_to_path)
