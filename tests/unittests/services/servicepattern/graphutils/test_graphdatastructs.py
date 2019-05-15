import unittest

from transiter.services.servicemap.graphutils import graphdatastructs


class TestGraphDataStructs(unittest.TestCase):
    def setUp(self):
        edges = [("a", "b"), ("c", "d"), ("b", "c")]
        self.graph_1 = graphdatastructs.construct_graph_from_edge_tuples(edges)
        edges = [("a", "b"), ("c", "d"), ("c", "b")]
        self.graph_2 = graphdatastructs.construct_graph_from_edge_tuples(edges)
        edges = [("a", "b"), ("b", "c"), ("b", "d")]
        self.graph_3 = graphdatastructs.construct_graph_from_edge_tuples(edges)
        edges = [("a", "b"), ("b", "c"), ("c", "a")]
        self.graph_4 = graphdatastructs.construct_graph_from_edge_tuples(edges)
        edges = [("a", "b"), ("b", "c"), ("c", "d"), ("d", "b")]
        self.graph_5 = graphdatastructs.construct_graph_from_edge_tuples(edges)

    def test_is_path_1(self):
        """[Graph data structs] Is path - true"""
        self.assertTrue(self.graph_1.is_path())

    def test_is_path_2(self):
        """[Graph data structs] Is path - false, case 1"""
        self.assertFalse(self.graph_2.is_path())

    def test_is_path_3(self):
        """[Graph data structs] Is path - false, case 2"""
        self.assertFalse(self.graph_3.is_path())

    def test_is_path_4(self):
        """[Graph data structs] Test is path - incorrect result case"""
        # These are not the right results.
        # https://github.com/jamespfennell/transiter/issues/8
        self.assertTrue(self.graph_4.is_path())
        self.graph_4.cast_to_path()

    def test_is_path_5(self):
        """[Graph data structs] Test is path - loop inside"""
        self.assertFalse(self.graph_5.is_path())

    def test_cast_to_path_1(self):
        """[Graph data structs] Case to path - works"""
        path = self.graph_1.cast_to_path()
        expected = ["a", "b", "c", "d"]
        i = 0
        for vertex in path.vertices():
            self.assertEquals(expected[i], vertex.label)
            i += 1

    def test_cast_to_path_2(self):
        """[Graph data structs] Case to path - impossible, case 1"""
        self.assertRaises(
            graphdatastructs.NotCastableAsAPathError, self.graph_2.cast_to_path
        )

    def test_cast_to_path_3(self):
        """[Graph data structs] Case to path - impossible, case 2"""
        self.assertRaises(
            graphdatastructs.NotCastableAsAPathError, self.graph_3.cast_to_path
        )

    def test_equal_graphs_1(self):
        """[Graph data structs] Graphs are equal - case 1"""
        self.assertEqual(self.graph_1, self.graph_1)

    def test_equal_graphs_2(self):
        """[Graph data structs] Graphs are equal - case 2"""
        self.assertEqual(self.graph_2, self.graph_2)

    def test_equal_graphs_3(self):
        """[Graph data structs] Graphs are equal - case 3"""
        self.assertEqual(self.graph_3, self.graph_3)

    def test_not_equal_graphs_1_2(self):
        """[Graph data structs] Graphs are not equal - case 1"""
        self.assertNotEqual(self.graph_1, self.graph_2)

    def test_not_equal_graphs_1_3(self):
        """[Graph data structs] Graphs are not equal - case 2"""
        self.assertNotEqual(self.graph_1, self.graph_3)

    def test_not_equal_graphs_2_3(self):
        """[Graph data structs] Graphs are not equal - case 3"""
        self.assertNotEqual(self.graph_2, self.graph_3)

    def test_not_equal_graphs_2_4(self):
        """[Graph data structs] Graphs are not equal - case 4"""
        self.assertNotEqual(self.graph_2, self.graph_4)
