"""Tests verifying compliance with repository guidelines and rules."""

import ast
import os
import tokenize
import unittest

MAX_LINE_LENGTH = 79
MAX_FUNCTION_LINES = 40
MAX_FUNCTION_ARGS = 7
MAX_CYCLOMATIC_COMPLEXITY = 10
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def compute_complexity(node: ast.AST) -> int:
    """Compute McCabe cyclomatic complexity for an AST node."""
    complexity = 1
    for child in ast.walk(node):
        is_branch = isinstance(
            child,
            (
                ast.If,
                ast.While,
                ast.For,
                ast.AsyncFor,
                ast.ExceptHandler,
                ast.With,
                ast.AsyncWith,
            ),
        )
        is_bool_op = isinstance(child, ast.BoolOp)
        if is_branch:
            complexity += 1
        elif is_bool_op:
            complexity += len(child.values) - 1
    return complexity


class TestCodeStyle(unittest.TestCase):
    """Test suite ensuring project adheres to all formatting rules."""

    def get_py_files(self) -> list[str]:
        """Collect all python source files."""
        files = []
        for dir_name in ["src", "tests"]:
            full_dir = os.path.join(PROJECT_ROOT, dir_name)
            for root, _, filenames in os.walk(full_dir):
                for filename in filenames:
                    if filename.endswith(".py"):
                        files.append(os.path.join(root, filename))
        return files

    def test_line_length(self) -> None:
        """Check rule P2: no line exceeds 79 characters."""
        for file_path in self.get_py_files():
            with open(file_path, "r", encoding="utf-8") as file:
                lines = file.readlines()
            for index, line in enumerate(lines):
                stripped = line.rstrip("\r\n")
                self.assertLessEqual(
                    len(stripped),
                    MAX_LINE_LENGTH,
                    f"Line {index + 1} exceeds {MAX_LINE_LENGTH} chars: "
                    f"{file_path} ({len(stripped)} chars)",
                )

    def test_functions_and_docstrings(self) -> None:
        """Check rules F1, A1, K1, C1, M1 for functions and classes."""
        for file_path in self.get_py_files():
            with open(file_path, "r", encoding="utf-8") as file:
                source = file.read()
            tree = ast.parse(source, filename=file_path)

            self.assertIsNotNone(
                ast.get_docstring(tree),
                f"Missing module docstring in {file_path}",
            )

            for node in ast.walk(tree):
                self._check_ast_node(node, file_path)

    def _check_ast_node(self, node: ast.AST, file_path: str) -> None:
        """Check AST node for functions, complexity, and magic numbers."""
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self._check_function(node, file_path)
        elif isinstance(node, ast.ClassDef):
            self.assertIsNotNone(
                ast.get_docstring(node),
                f"Missing class docstring for {node.name} in {file_path}",
            )
        elif isinstance(node, ast.Compare):
            self._check_compare(node, file_path)

    def _check_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        file_path: str,
    ) -> None:
        """Check function length, argument count, and complexity."""
        length = node.end_lineno - node.lineno + 1
        self.assertLessEqual(
            length,
            MAX_FUNCTION_LINES,
            f"Function {node.name} has {length} lines in {file_path}",
        )
        total_args = len(node.args.args)
        self.assertLessEqual(
            total_args,
            MAX_FUNCTION_ARGS,
            f"Function {node.name} has {total_args} args in {file_path}",
        )
        self.assertIsNotNone(
            ast.get_docstring(node),
            f"Missing function docstring for {node.name} in {file_path}",
        )
        comp = compute_complexity(node)
        self.assertLessEqual(
            comp,
            MAX_CYCLOMATIC_COMPLEXITY,
            f"Complexity {comp} in {node.name} ({file_path})",
        )

    def _check_compare(self, node: ast.AST, file_path: str) -> None:
        """Check rule M1: no numeric literals in comparisons."""
        for item in [node.left] + node.comparators:
            is_num_literal = (
                isinstance(item, ast.Constant)
                and isinstance(item.value, (int, float))
            )
            self.assertFalse(
                is_num_literal,
                f"Magic number {getattr(item, 'value', None)} in comparison "
                f"at line {node.lineno} in {file_path}",
            )

    def test_no_inline_comments(self) -> None:
        """Check rule K1: no comments used instead of docstrings."""
        for file_path in self.get_py_files():
            with tokenize.open(file_path) as fp:
                for tok in tokenize.generate_tokens(fp.readline):
                    if tok.type == tokenize.COMMENT:
                        msg = (
                            f"Rule K1 violation in {file_path}:"
                            f"{tok.start[0]}: {tok.string}"
                        )
                        self.fail(msg)

    def test_import_aliases_pep8(self) -> None:
        """Check rule I1: import aliases follow snake_case."""
        for file_path in self.get_py_files():
            with open(file_path, "r", encoding="utf-8") as fp:
                tree = ast.parse(fp.read(), filename=file_path)
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    for alias in node.names:
                        if alias.asname and not alias.asname.islower():
                            self.fail(
                                f"Rule I1 violation: alias {alias.asname} "
                                f"not snake_case in {file_path}"
                            )


if __name__ == "__main__":
    unittest.main()
