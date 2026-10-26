"""Unit tests for configuration and CLI argument parsing."""

import tempfile
import unittest
from src.config import (
    Config,
    ConfigError,
    format_config_kv,
    parse_arguments,
    validate_config,
)

SAMPLE_PACKAGE = "org.example:sample-lib:1.0.0"
SAMPLE_URL = "https://repo1.maven.org/maven2"
SAMPLE_PNG = "output.png"
EMPTY_STRING = ""


class TestConfig(unittest.TestCase):
    """Test suite for CLI configuration validation and parsing."""

    def test_valid_config(self) -> None:
        """Test parsing valid arguments in real Maven mode."""
        args = [
            "--package",
            SAMPLE_PACKAGE,
            "--repo",
            SAMPLE_URL,
            "--output",
            SAMPLE_PNG,
            "--ascii-tree",
        ]
        cfg = parse_arguments(args)
        self.assertEqual(cfg.package, SAMPLE_PACKAGE)
        self.assertEqual(cfg.repo, SAMPLE_URL)
        self.assertEqual(cfg.output, SAMPLE_PNG)
        self.assertFalse(cfg.test_mode)
        self.assertTrue(cfg.ascii_tree)

    def test_format_kv(self) -> None:
        """Test key-value formatting of configuration parameters."""
        cfg = Config(
            package=SAMPLE_PACKAGE,
            repo=SAMPLE_URL,
            test_mode=False,
            output=SAMPLE_PNG,
            ascii_tree=True,
        )
        output = format_config_kv(cfg)
        self.assertIn("package: org.example:sample-lib:1.0.0", output)
        self.assertIn("repo: https://repo1.maven.org/maven2", output)
        self.assertIn("test_mode: False", output)
        self.assertIn("output: output.png", output)
        self.assertIn("ascii_tree: True", output)

    def test_missing_package_error(self) -> None:
        """Test error when required package argument is missing."""
        with self.assertRaises(SystemExit):
            parse_arguments(["--repo", SAMPLE_URL])

    def test_invalid_package_coordinate_error(self) -> None:
        """Test error when Maven package coordinate has invalid format."""
        with self.assertRaises(ConfigError):
            parse_arguments(["--package", "invalid-package-format"])

    def test_invalid_repo_url_error(self) -> None:
        """Test error when repository URL protocol is invalid."""
        with self.assertRaises(ConfigError):
            parse_arguments(
                [
                    "--package",
                    SAMPLE_PACKAGE,
                    "--repo",
                    "ftp://invalid.repo.org",
                ]
            )

    def test_invalid_output_extension_error(self) -> None:
        """Test error when output file does not end with .png."""
        with self.assertRaises(ConfigError):
            parse_arguments(
                [
                    "--package",
                    SAMPLE_PACKAGE,
                    "--output",
                    "graph.pdf",
                ]
            )

    def test_test_mode_valid(self) -> None:
        """Test valid test mode configuration with existing file."""
        with tempfile.NamedTemporaryFile(suffix=".txt") as tmp:
            args = [
                "--package",
                "A",
                "--repo",
                tmp.name,
                "--test-mode",
            ]
            cfg = parse_arguments(args)
            self.assertEqual(cfg.package, "A")
            self.assertTrue(cfg.test_mode)

    def test_test_mode_missing_file_error(self) -> None:
        """Test error in test mode when repository file does not exist."""
        cfg = Config(
            package="A",
            repo="non_existent_file.txt",
            test_mode=True,
            output=SAMPLE_PNG,
            ascii_tree=False,
        )
        with self.assertRaises(ConfigError):
            validate_config(cfg)

    def test_test_mode_invalid_package_error(self) -> None:
        """Test error in test mode when package is not uppercase Latin."""
        with tempfile.NamedTemporaryFile(suffix=".txt") as tmp:
            with self.assertRaises(ConfigError):
                parse_arguments(
                    [
                        "--package",
                        "package_123",
                        "--repo",
                        tmp.name,
                        "--test-mode",
                    ]
                )


if __name__ == "__main__":
    unittest.main()
