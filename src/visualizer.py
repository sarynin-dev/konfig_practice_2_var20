"""Visualization module: D2 diagrams, PNG generation, and ASCII tree."""

import os
import shutil
import subprocess
from src.graph import DependencyGraph

D2_EXE_NAME = "d2"
D2_EXT = ".d2"
PNG_EXT = ".png"
BRANCH_MID = "├── "
BRANCH_LAST = "└── "
PREFIX_MID = "│   "
PREFIX_EMPTY = "    "
CYCLE_LABEL = " (цикл)"
RETURN_CODE_SUCCESS = 0


def generate_d2_text(graph: DependencyGraph) -> str:
    """Generate D2 diagram source representation from dependency graph."""
    lines = [f"# D2 Dependency Graph for {graph.root}"]
    cycle_set = set(graph.cycles)
    for src, targets in graph.adjacency.items():
        if not targets:
            lines.append(f'"{src}"')
            continue
        for dst in targets:
            if (src, dst) in cycle_set:
                lines.append(f'"{src}" -> "{dst}": "цикл"')
            else:
                lines.append(f'"{src}" -> "{dst}"')
    return "\n".join(lines)


def format_ascii_tree(graph: DependencyGraph) -> str:
    """Generate ASCII tree visualization of dependency graph."""
    lines = [graph.root]
    initial_children = graph.adjacency.get(graph.root, [])
    if not initial_children:
        return lines[0]

    stack: list[tuple[str, str, bool, set[str]]] = []
    total = len(initial_children)
    for idx, child in reversed(list(enumerate(initial_children))):
        is_last = idx == (total - 1)
        stack.append((child, "", is_last, {graph.root}))

    while stack:
        node, prefix, is_last, visited = stack.pop()
        connector = BRANCH_LAST if is_last else BRANCH_MID
        if node in visited:
            lines.append(f"{prefix}{connector}{node}{CYCLE_LABEL}")
            continue

        lines.append(f"{prefix}{connector}{node}")
        children = graph.adjacency.get(node, [])
        new_prefix = prefix + (PREFIX_EMPTY if is_last else PREFIX_MID)
        new_visited = visited | {node}
        child_count = len(children)
        for c_idx, c_node in reversed(list(enumerate(children))):
            c_last = c_idx == (child_count - 1)
            stack.append((c_node, new_prefix, c_last, new_visited))

    return "\n".join(lines)


def find_d2_executable() -> str | None:
    """Locate D2 executable in system PATH or standard directories."""
    direct = shutil.which(D2_EXE_NAME)
    if direct:
        return direct
    local_app = os.environ.get("LOCALAPPDATA", "")
    candidate = os.path.join(
        local_app, "d2", "PFiles64", "D2", "d2.exe"
    )
    if os.path.isfile(candidate):
        return candidate
    return None


def _render_fallback_png(graph: DependencyGraph, output_png: str) -> None:
    """Render graph to PNG image using matplotlib as fallback."""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axis("off")
    nodes = list(graph.adjacency.keys())
    if not nodes:
        nodes = [graph.root]
    y_pos = range(len(nodes))
    labels = [
        f"{n} -> {', '.join(graph.adjacency.get(n, [])) or 'none'}"
        for n in nodes
    ]
    ax.text(
        0.05,
        0.95,
        f"Dependency Graph: {graph.root}\n\n" + "\n".join(labels),
        verticalalignment="top",
        fontsize=10,
        family="monospace",
    )
    plt.tight_layout()
    plt.savefig(output_png, format="png", dpi=150)
    plt.close(fig)


def export_graph(
    graph: DependencyGraph,
    output_png: str,
) -> tuple[str, str]:
    """Export graph as D2 text file and render PNG image."""
    base_name, _ = os.path.splitext(output_png)
    d2_path = base_name + D2_EXT
    d2_content = generate_d2_text(graph)
    with open(d2_path, "w", encoding="utf-8") as file:
        file.write(d2_content)

    d2_exe = find_d2_executable()
    if d2_exe:
        cmd = [d2_exe, d2_path, output_png]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        if (
            proc.returncode == RETURN_CODE_SUCCESS
            and os.path.isfile(output_png)
        ):
            return d2_path, output_png

    _render_fallback_png(graph, output_png)
    return d2_path, output_png
