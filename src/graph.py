"""Dependency graph traversal, cycle detection, and test repo parsing."""

from collections import deque
from dataclasses import dataclass, field

STATE_UNVISITED = "unvisited"
STATE_VISITING = "visiting"
STATE_VISITED = "visited"
COLON_CHAR = ":"
COMMA_CHAR = ","
ARROW_STR = "->"
EMPTY_STR = ""
START_INDEX = 1


@dataclass
class DependencyGraph:
    """Directed dependency graph with cycle detection results."""

    root: str
    adjacency: dict[str, list[str]] = field(default_factory=dict)
    cycles: list[tuple[str, str]] = field(default_factory=list)
    load_order: list[str] = field(default_factory=list)

    def get_dependencies(self, node: str) -> list[str]:
        """Return direct dependencies of given node."""
        return self.adjacency.get(node, [])


def format_load_order(graph: DependencyGraph) -> str:
    """Format dependency load order (bottom-up / topological)."""
    lines = [f"Порядок загрузки зависимостей для {graph.root}:"]
    for idx, pkg in enumerate(graph.load_order, start=START_INDEX):
        lines.append(f"  {idx}. {pkg}")
    return "\n".join(lines)


class GraphError(ValueError):
    """Exception raised for graph traversal and format errors."""


def _parse_line_deps(raw_deps: str) -> list[str]:
    """Parse comma- or space-separated dependency list."""
    cleaned = raw_deps.replace(COMMA_CHAR, " ")
    tokens = cleaned.split()
    return [tok.strip() for tok in tokens if tok.strip()]


def _parse_repo_line(line: str) -> tuple[str, list[str]] | None:
    """Parse a single line of test repository definition."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    sep = COLON_CHAR if COLON_CHAR in stripped else ARROW_STR
    if sep not in stripped:
        raise GraphError(f"Invalid syntax in test repo: {stripped}")
    parts = stripped.split(sep, 1)
    source = parts[0].strip()
    if not source.isupper() or not source.isalpha():
        raise GraphError(
            f"Test package must be uppercase Latin letters: {source}"
        )
    targets = _parse_line_deps(parts[1])
    for target in targets:
        if not target.isupper() or not target.isalpha():
            raise GraphError(
                f"Target package must be uppercase Latin: {target}"
            )
    return source, targets


def parse_test_repo_file(file_path: str) -> dict[str, list[str]]:
    """Parse graph definition file for test repository mode."""
    graph: dict[str, list[str]] = {}
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            entry = _parse_repo_line(line)
            if entry is not None:
                source, targets = entry
                graph[source] = targets
    return graph


def _handle_neighbor(
    current: str,
    neighbor: str,
    state: dict[str, str],
    graph: DependencyGraph,
) -> bool:
    """Record edge and cycle. Return True if neighbor needs exploration."""
    graph.adjacency[current].append(neighbor)
    neighbor_state = state.get(neighbor, STATE_UNVISITED)
    if neighbor_state == STATE_VISITING:
        graph.cycles.append((current, neighbor))
        return False
    if neighbor_state == STATE_UNVISITED:
        state[neighbor] = STATE_VISITING
        return True
    return False


def build_graph_dfs(
    root: str,
    get_neighbors_func,
) -> DependencyGraph:
    """Build dependency graph using iterative non-recursive DFS."""
    graph = DependencyGraph(root=root)
    state: dict[str, str] = {root: STATE_VISITING}
    stack: deque[tuple[str, int]] = deque([(root, 0)])
    cached_neighbors: dict[str, list[str]] = {}

    while stack:
        current, idx = stack.pop()
        if current not in cached_neighbors:
            cached_neighbors[current] = list(get_neighbors_func(current))
            graph.adjacency[current] = []

        neighbors = cached_neighbors[current]
        pushed = False

        while idx < len(neighbors):
            neighbor = neighbors[idx]
            idx += 1
            if _handle_neighbor(current, neighbor, state, graph):
                stack.append((current, idx))
                stack.append((neighbor, 0))
                pushed = True
                break

        if not pushed:
            state[current] = STATE_VISITED
            if current not in graph.load_order:
                graph.load_order.append(current)

    return graph
