"""Command line interface entry point for dependency visualizer."""

import sys
from src.config import ConfigError, format_config_kv, parse_arguments

EXIT_SUCCESS = 0
EXIT_FAILURE = 1


def main(args: list[str] | None = None) -> int:
    """Run CLI application."""
    try:
        config = parse_arguments(args)
        print(format_config_kv(config))
        return EXIT_SUCCESS
    except (ConfigError, SystemExit) as err:
        if isinstance(err, SystemExit):
            return int(err.code) if err.code is not None else EXIT_FAILURE
        sys.stderr.write(f"Configuration error: {err}\n")
        return EXIT_FAILURE


if __name__ == "__main__":
    sys.exit(main())
