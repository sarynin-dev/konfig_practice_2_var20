"""Unit tests for dependency graph traversal and test repo parsing."""

import os
import unittest
from src.graph import (
    GraphError,
    build_graph_dfs,
    parse_test_repo_file,
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


class TestGraph(unittest.TestCase):
    """Test suite for iterative DFS and cycle handling."""

    def test_parse_linear_file(self) -> None:
        """Test parsing valid linear dependency file."""
        path = os.path.join(DATA_DIR, "linear.txt")
        graph_dict = parse_test_repo_file(path)
        self.assertEqual(graph_dict.get("A"), ["B"])
        self.assertEqual(graph_dict.get("B"), ["C"])
        self.assertEqual(graph_dict.get("C"), [])

    def test_parse_invalid_file(self) -> None:
        """Test error when package name is not uppercase Latin."""
        bad_path = os.path.join(DATA_DIR, "bad_syntax.tmp")
        with open(bad_path, "w", encoding="utf-8") as file:
            file.write("pkg1: pkg2\n")
        try:
            with self.assertRaises(GraphError):
                parse_test_repo_file(bad_path)
        finally:
            if os.path.exists(bad_path):
                os.remove(bad_path)

    def test_dfs_linear_graph(self) -> None:
        """Test iterative DFS traversal on linear graph."""
        path = os.path.join(DATA_DIR, "linear.txt")
        repo = parse_test_repo_file(path)
        graph = build_graph_dfs("A", lambda node: repo.get(node, []))

        self.assertEqual(graph.root, "A")
        self.assertEqual(graph.adjacency["A"], ["B"])
        self.assertEqual(graph.adjacency["B"], ["C"])
        self.assertEqual(graph.adjacency["C"], [])
        self.assertFalse(graph.cycles)

    def test_dfs_diamond_graph(self) -> None:
        """Test iterative DFS traversal on diamond graph."""
        path = os.path.join(DATA_DIR, "branching.txt")
        repo = parse_test_repo_file(path)
        graph = build_graph_dfs("A", lambda node: repo.get(node, []))

        self.assertEqual(graph.adjacency["A"], ["B", "C"])
        self.assertIn("D", graph.adjacency["B"])
        self.assertIn("D", graph.adjacency["C"])
        self.assertFalse(graph.cycles)

    def test_dfs_cycle_detection(self) -> None:
        """Test iterative DFS detects cycles without infinite looping."""
        path = os.path.join(DATA_DIR, "cycle.txt")
        repo = parse_test_repo_file(path)
        graph = build_graph_dfs("A", lambda node: repo.get(node, []))

        self.assertTrue(graph.cycles)
        self.assertIn(("C", "A"), graph.cycles)

    def test_dfs_self_cycle(self) -> None:
        """Test iterative DFS detects self cycle."""
        path = os.path.join(DATA_DIR, "self_cycle.txt")
        repo = parse_test_repo_file(path)
        graph = build_graph_dfs("A", lambda node: repo.get(node, []))

        self.assertTrue(graph.cycles)
        self.assertIn(("A", "A"), graph.cycles)

    def test_load_order_linear(self) -> None:
        """Test bottom-up dependency load order on linear graph."""
        path = os.path.join(DATA_DIR, "linear.txt")
        repo = parse_test_repo_file(path)
        graph = build_graph_dfs("A", lambda node: repo.get(node, []))
        self.assertEqual(graph.load_order, ["C", "B", "A"])

    def test_load_order_branching(self) -> None:
        """Test dependency load order on diamond branching graph."""
        path = os.path.join(DATA_DIR, "branching.txt")
        repo = parse_test_repo_file(path)
        graph = build_graph_dfs("A", lambda node: repo.get(node, []))
        self.assertEqual(graph.load_order[-1], "A")
        self.assertEqual(graph.load_order[0], "D")
        self.assertTrue(
            graph.load_order.index("D") < graph.load_order.index("B")
        )
        self.assertTrue(
            graph.load_order.index("D") < graph.load_order.index("C")
        )


if __name__ == "__main__":
    unittest.main()
