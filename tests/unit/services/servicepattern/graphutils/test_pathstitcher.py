import unittest
from transiter.services.servicemap.graphutils import graphdatastructs, pathstitcher


class TestPathSticher(unittest.TestCase):
    def tearDown(self):
        self.paths = [graphdatastructs.DirectedPath(path) for path in self.paths]
        graph = pathstitcher.stitch(self.paths)
        self.assertEqual(graph.edges(), self.edges)

    def test_stitch_1(self):
        """[Path stitcher] case 1"""
        self.paths = [["b", "w", "c"], ["b", "c"]]
        self.edges = {("b", "w"), ("w", "c")}

    def test_stitch_2(self):
        """[Path stitcher] case 2"""
        self.paths = [["a", "b", "c"], ["d", "b", "c"]]
        self.edges = {("a", "b"), ("d", "b"), ("b", "c")}

    def test_stitch_3(self):
        """[Path stitcher] case 3"""
        self.paths = [["a", "b", "c"], ["a", "b", "d"]]
        self.edges = {("a", "b"), ("b", "c"), ("b", "d")}

    def test_stitch_4(self):
        """[Path stitcher] case 4"""
        self.paths = [["a", "b", "c"], ["c", "d", "e"]]
        self.edges = {("a", "b"), ("b", "c"), ("c", "d"), ("d", "e")}

    def test_stitch_5(self):
        """[Path stitcher] case 5"""
        self.paths = [["a", "b", "c"], ["e", "f", "g"]]
        self.edges = {("a", "b"), ("b", "c"), ("e", "f"), ("f", "g")}

    def test_stitch_6(self):
        """[Path stitcher] case 6"""
        self.paths = [["b", "c"], ["b", "w", "c"]]
        self.edges = {("b", "w"), ("w", "c")}

    def test_stitch_7(self):
        """[Path stitcher] case 7"""
        self.paths = [["a", "b", "c"], ["a", "w", "c"]]
        self.edges = {("a", "b"), ("b", "c"), ("a", "w"), ("w", "c")}

    def test_stitch_8(self):
        """[Path stitcher] case 8"""
        self.paths = [["a", "b", "c"], ["z", "a", "b"]]
        self.edges = {("z", "a"), ("a", "b"), ("b", "c")}

    def test_stitch_10(self):
        """[Path stitcher] case 10"""
        self.paths = [["a", "b"]]
        self.edges = {("a", "b")}
