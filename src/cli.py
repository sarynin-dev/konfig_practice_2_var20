"""Command line interface entry point for dependency visualizer."""

import sys
from src.config import ConfigError, parse_arguments
from src.maven import MavenError, get_direct_dependencies

EXIT_SUCCESS = 0
EXIT_FAILURE = 1


def format_direct_dependencies(
    package_name: str,
    deps: list[object],
) -> str:
    """Format direct dependencies for console output."""
    header = f"Прямые зависимости для пакета {package_name}:"
    if not deps:
        return f"{header}\n  (зависимостей нет)"
    lines = [header]
    for dep in deps:
        lines.append(f"  - {dep.to_string()}")
    return "\n".join(lines)


def run_stage2(package: str, repo: str) -> int:
    """Execute Stage 2: fetch and display direct Maven dependencies."""
    try:
        resolved_name, deps = get_direct_dependencies(repo, package)
        output_text = format_direct_dependencies(resolved_name, deps)
        print(output_text)
        return EXIT_SUCCESS
    except (MavenError, Exception) as err:
        sys.stderr.write(f"Ошибка получения зависимостей: {err}\n")
        return EXIT_FAILURE


def main(args: list[str] | None = None) -> int:
    """Run CLI application."""
    try:
        config = parse_arguments(args)
        if not config.test_mode:
            return run_stage2(config.package, config.repo)
        return EXIT_SUCCESS
    except (ConfigError, SystemExit) as err:
        if isinstance(err, SystemExit):
            return int(err.code) if err.code is not None else EXIT_FAILURE
        sys.stderr.write(f"Configuration error: {err}\n")
        return EXIT_FAILURE


if __name__ == "__main__":
    sys.exit(main())
