import unittest
from transiter.utils.graphutils import graphdatastructs
from transiter.utils.graphutils import pathstitcher


class TestPathSticher(unittest.TestCase):
    def test_stitch_1(self):
        paths = [['b', 'w', 'c'],['b', 'c']]
        edges = set([('b','w'), ('w', 'c')])
        self._process_test(paths, edges)

    def test_stitch_2(self):
        paths = [['a', 'b', 'c'], ['d', 'b', 'c']]
        edges = set([('a', 'b'), ('d', 'b'), ('b', 'c')])
        self._process_test(paths, edges)

    def test_stitch_3(self):
        paths = [['a', 'b', 'c'], ['a', 'b', 'd']]
        edges = set([('a', 'b'), ('b', 'c'), ('b', 'd')])
        self._process_test(paths, edges)


    def test_stitch_4(self):
        paths = [['a', 'b', 'c'], ['c', 'd', 'e']]
        edges = set([('a', 'b'), ('b', 'c'), ('c', 'd'), ('d', 'e')])
        self._process_test(paths, edges)


    def test_stitch_5(self):
        paths = [['a', 'b', 'c'], ['e', 'f', 'g']]
        edges = set([('a', 'b'), ('b', 'c'), ('e', 'f'), ('f', 'g')])
        self._process_test(paths, edges)


    def test_stitch_6(self):
        paths = [['b', 'c'],['b', 'w', 'c']]
        edges = set([('b','w'), ('w', 'c')])
        self._process_test(paths, edges)


    def test_stitch_7(self):
        paths = [['a', 'b', 'c'], ['a', 'w', 'c']]
        edges = set([('a', 'b'), ('b', 'c'), ('a', 'w'), ('w', 'c')])
        self._process_test(paths, edges)


    def test_stitch_8(self):
        paths = [['a', 'b', 'c'], ['z', 'a', 'b']]
        edges = set([('z', 'a'), ('a', 'b'), ('b', 'c')])
        self._process_test(paths, edges)


    def _process_test(self, paths, edges):
        paths = [graphdatastructs.DirectedPath(path) for path in paths]
        graph = pathstitcher.stitch(paths)
        self.assertEqual(graph.edges(), edges)
