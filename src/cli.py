"""Command line interface entry point for dependency visualizer."""

import sys
from src.config import Config, ConfigError, parse_arguments
from src.graph import (
    DependencyGraph,
    build_graph_dfs,
    format_load_order,
    parse_test_repo_file,
)
from src.maven import MavenError, get_direct_dependencies
from src.visualizer import export_graph, format_ascii_tree

EXIT_SUCCESS = 0
EXIT_FAILURE = 1


def format_graph_summary(graph: DependencyGraph) -> str:
    """Format dependency graph traversal summary."""
    lines = [f"Граф зависимостей для пакета: {graph.root}"]
    for node, deps in graph.adjacency.items():
        deps_str = ", ".join(deps) if deps else "(нет зависимостей)"
        lines.append(f"  {node} -> {deps_str}")
    if graph.cycles:
        lines.append("Обнаружены циклические зависимости:")
        for src, dst in graph.cycles:
            lines.append(f"  [ЦИКЛ] {src} -> {dst}")
    else:
        lines.append("Циклических зависимостей не обнаружено.")
    return "\n".join(lines)


def _display_and_export(graph: DependencyGraph, config: Config) -> None:
    """Print summaries, ASCII tree, and export D2 and PNG diagrams."""
    print(format_graph_summary(graph))
    print()
    print(format_load_order(graph))
    if config.ascii_tree:
        print("\nДерево зависимостей (ASCII):")
        print(format_ascii_tree(graph))
    d2_path, png_path = export_graph(graph, config.output)
    print(f"\nДиаграмма D2 сохранена в: {d2_path}")
    print(f"Изображение графа сохранено в: {png_path}")


def run_test_mode(config: Config) -> int:
    """Execute dependency resolution in test repository mode."""
    try:
        repo_data = parse_test_repo_file(config.repo)
        if config.package not in repo_data:
            sys.stderr.write(
                f"Пакет {config.package} не найден в тестовом репозитории.\n"
            )
            return EXIT_FAILURE
        graph = build_graph_dfs(
            config.package,
            lambda node: repo_data.get(node, []),
        )
        _display_and_export(graph, config)
        return EXIT_SUCCESS
    except Exception as err:
        sys.stderr.write(f"Ошибка в тестовом режиме: {err}\n")
        return EXIT_FAILURE


def run_maven_mode(config: Config) -> int:
    """Execute dependency resolution in real Maven repository mode."""
    cache: dict[str, list[str]] = {}

    def _fetch_neighbors(node: str) -> list[str]:
        """Fetch neighbor dependencies for a package node."""
        if node in cache:
            return cache[node]
        try:
            _, direct_deps = get_direct_dependencies(config.repo, node)
            dep_names = [d.to_string() for d in direct_deps]
            cache[node] = dep_names
            return dep_names
        except MavenError as err:
            sys.stderr.write(f"Предупреждение: {err}\n")
            cache[node] = []
            return []

    try:
        graph = build_graph_dfs(config.package, _fetch_neighbors)
        _display_and_export(graph, config)
        return EXIT_SUCCESS
    except Exception as err:
        sys.stderr.write(f"Ошибка в режиме Maven: {err}\n")
        return EXIT_FAILURE


def main(args: list[str] | None = None) -> int:
    """Run CLI application."""
    try:
        config = parse_arguments(args)
        if config.test_mode:
            return run_test_mode(config)
        return run_maven_mode(config)
    except (ConfigError, SystemExit) as err:
        if isinstance(err, SystemExit):
            return int(err.code) if err.code is not None else EXIT_FAILURE
        sys.stderr.write(f"Configuration error: {err}\n")
        return EXIT_FAILURE


if __name__ == "__main__":
    sys.exit(main())
