"""Unit tests for visualization: D2 text, PNG export, and ASCII tree."""

import os
import tempfile
import unittest
from src.graph import DependencyGraph
from src.visualizer import (
    export_graph,
    format_ascii_tree,
    generate_d2_text,
)


class TestVisualizer(unittest.TestCase):
    """Test suite for D2 generator, PNG exporter, and ASCII tree."""

    def test_generate_d2_linear(self) -> None:
        """Test D2 syntax for linear dependency graph."""
        graph = DependencyGraph(
            root="A",
            adjacency={"A": ["B"], "B": ["C"], "C": []},
        )
        d2_text = generate_d2_text(graph)
        self.assertIn('"A" -> "B"', d2_text)
        self.assertIn('"B" -> "C"', d2_text)
        self.assertIn('"C"', d2_text)

    def test_generate_d2_cycle(self) -> None:
        """Test D2 syntax annotates detected cycles."""
        graph = DependencyGraph(
            root="A",
            adjacency={"A": ["B"], "B": ["C"], "C": ["A"]},
            cycles=[("C", "A")],
        )
        d2_text = generate_d2_text(graph)
        self.assertIn('"C" -> "A": "цикл"', d2_text)

    def test_ascii_tree_formatting(self) -> None:
        """Test ASCII tree format with branches and cycle indicators."""
        graph = DependencyGraph(
            root="A",
            adjacency={"A": ["B", "C"], "B": ["D"], "C": [], "D": []},
        )
        tree = format_ascii_tree(graph)
        self.assertIn("A", tree)
        self.assertIn("├── B", tree)
        self.assertIn("└── C", tree)
        self.assertIn("D", tree)

    def test_export_png_and_d2(self) -> None:
        """Test exporting D2 file and rendering PNG image."""
        graph = DependencyGraph(
            root="A",
            adjacency={"A": ["B"], "B": []},
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_png = os.path.join(tmp_dir, "test_graph.png")
            d2_path, png_path = export_graph(graph, out_png)
            self.assertTrue(os.path.isfile(d2_path))
            self.assertTrue(os.path.isfile(png_path))
            self.assertGreater(os.path.getsize(png_path), 0)


if __name__ == "__main__":
    unittest.main()
