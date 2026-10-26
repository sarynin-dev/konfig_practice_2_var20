"""Configuration module for dependency visualizer CLI."""

import argparse
import os
from dataclasses import dataclass

DEFAULT_REPO = "https://repo1.maven.org/maven2"
DEFAULT_OUTPUT = "graph.png"
PNG_EXTENSION = ".png"
HTTP_PREFIX = "http://"
HTTPS_PREFIX = "https://"
COLON_DELIMITER = ":"
ZERO_COUNT = 0
MIN_COORDINATE_PARTS = 2
MAX_COORDINATE_PARTS = 3


@dataclass
class Config:
    """Class representing CLI configuration parameters."""

    package: str
    repo: str
    test_mode: bool
    output: str
    ascii_tree: bool


class ConfigError(ValueError):
    """Exception raised for invalid configuration parameters."""


def validate_test_repo(path: str) -> None:
    """Validate repository path in test mode."""
    if not os.path.isfile(path):
        raise ConfigError(
            f"Test repository file not found: {path}"
        )


def validate_real_repo(url: str) -> None:
    """Validate repository URL in real mode."""
    is_http = url.startswith(HTTP_PREFIX)
    is_https = url.startswith(HTTPS_PREFIX)
    if not (is_http or is_https):
        raise ConfigError(
            f"Repository URL must start with http:// or https://: {url}"
        )


def validate_test_package(name: str) -> None:
    """Validate package identifier in test mode."""
    if not name.isupper() or not name.isalpha():
        raise ConfigError(
            f"Test package must be uppercase Latin letters: {name}"
        )


def validate_maven_package(name: str) -> None:
    """Validate Maven package coordinate format."""
    parts = name.split(COLON_DELIMITER)
    parts_count = len(parts)
    is_valid_count = (
        parts_count >= MIN_COORDINATE_PARTS
        and parts_count <= MAX_COORDINATE_PARTS
    )
    if not is_valid_count or any(not p.strip() for p in parts):
        raise ConfigError(
            f"Package coordinate must be groupId:artifactId[:version]: {name}"
        )


def validate_config(config: Config) -> None:
    """Validate all configuration fields."""
    if not config.package or not config.package.strip():
        raise ConfigError("Package name must not be empty.")

    if not config.output.lower().endswith(PNG_EXTENSION):
        raise ConfigError(
            f"Output file must have {PNG_EXTENSION} extension: {config.output}"
        )

    if config.test_mode:
        validate_test_package(config.package)
        validate_test_repo(config.repo)
    else:
        validate_maven_package(config.package)
        validate_real_repo(config.repo)


def build_parser() -> argparse.ArgumentParser:
    """Build command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Maven dependency graph visualizer"
    )
    parser.add_argument(
        "--package",
        "-p",
        type=str,
        required=True,
        help="Package name or coordinates (groupId:artifactId[:version])",
    )
    parser.add_argument(
        "--repo",
        "-r",
        type=str,
        default=DEFAULT_REPO,
        help="Repository URL or path to test repository file",
    )
    parser.add_argument(
        "--test-mode",
        "-t",
        action="store_true",
        help="Enable test repository mode",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=DEFAULT_OUTPUT,
        help="Output PNG image file name",
    )
    parser.add_argument(
        "--ascii-tree",
        "-a",
        action="store_true",
        help="Display dependency tree in ASCII format",
    )
    return parser


def parse_arguments(raw_args: list[str] | None = None) -> Config:
    """Parse CLI arguments into a validated Config object."""
    parser = build_parser()
    args = parser.parse_args(raw_args)
    config = Config(
        package=args.package,
        repo=args.repo,
        test_mode=bool(args.test_mode),
        output=args.output,
        ascii_tree=bool(args.ascii_tree),
    )
    validate_config(config)
    return config


def format_config_kv(config: Config) -> str:
    """Format configuration parameters as key-value pairs."""
    lines = [
        f"package: {config.package}",
        f"repo: {config.repo}",
        f"test_mode: {config.test_mode}",
        f"output: {config.output}",
        f"ascii_tree: {config.ascii_tree}",
    ]
    return "\n".join(lines)
