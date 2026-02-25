"""
sequence_analysis.py

Extends parser.py with:
  1. Identification of unique event names across all components.
  2. Per-event sequence graph: for each unique event E, build a
     directed-graph of "what event comes next most often" by scanning
     all (event[i], event[i+1]) pairs within the same PID/component
     session.  The graph is stored as a dict-of-dicts with edge counts
     and can be rendered with graphviz (optional) or printed as text.
"""

import sys
import os
from collections import defaultdict, Counter

# ── re-use the existing parser ────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from parser import parse_log_file, parse_event  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# 1.  Unique event names
# ─────────────────────────────────────────────────────────────────────────────


def get_unique_event_names(parsed_logs: dict) -> set:
    """Return the set of all distinct event *names* (ignoring data values)."""
    names = set()
    for logs in parsed_logs.values():
        for log in logs:
            names.add(log.event["name"])
    return names


# ─────────────────────────────────────────────────────────────────────────────
# 2.  Sequence graph
# ─────────────────────────────────────────────────────────────────────────────


def build_sequence_graph(parsed_logs: dict, window: int = 1) -> dict:
    """
    Build a global transition graph over event names.

    For every consecutive pair (event_i, event_{i+window}) that share the
    same component *and* PID, increment edge[event_i][event_{i+window}].

    Returns
    -------
    graph : dict[str, Counter]
        graph[src][dst] = number of times dst followed src.
    """
    # Merge all logs into one time-ordered list per (component, pid)
    sessions: dict[tuple, list] = defaultdict(list)
    for component, logs in parsed_logs.items():
        for log in logs:
            sessions[(component, log.pid)].append(log)

    # Sort each session by timestamp string (lexicographic sort works here
    # because the format is YYYYMMDD-HH:MM:SS:mmm)
    for key in sessions:
        sessions[key].sort(key=lambda l: l.timestamp)

    graph: dict[str, Counter] = defaultdict(Counter)

    for session_logs in sessions.values():
        for i in range(len(session_logs) - window):
            src = session_logs[i].event["name"]
            dst = session_logs[i + window].event["name"]
            graph[src][dst] += 1

    return graph


def most_common_sequence(graph: dict, start_event: str, depth: int = 5) -> list:
    """
    Follow the single most-common successor at each step from start_event.

    Returns a list of (event_name, edge_count) tuples representing the path.
    The first tuple has edge_count=None (it is the starting node).
    """
    path = [(start_event, None)]
    visited = {start_event}
    current = start_event

    for _ in range(depth):
        successors = graph.get(current)
        if not successors:
            break
        # pick the most common successor not yet in path (avoid trivial cycles)
        ranked = successors.most_common()
        next_event = None
        for candidate, count in ranked:
            if candidate not in visited:
                next_event = (candidate, count)
                break
        if next_event is None:
            # allow revisit if no unvisited successor exists
            next_event = ranked[0]
            next_event = (next_event[0], next_event[1])
        path.append(next_event)
        visited.add(next_event[0])
        current = next_event[0]

    return path


# ─────────────────────────────────────────────────────────────────────────────
# 3.  Tree-structured "chunk" for each unique event
# ─────────────────────────────────────────────────────────────────────────────


def build_successor_tree(
    graph: dict, root: str, branching: int = 2, depth: int = 4
) -> dict:
    """
    Build a tree (dict) rooted at *root* showing the *branching* most-common
    successors at each level, up to *depth* levels deep.

    Return value structure:
        {
          "name": "<event>",
          "count": <edge weight from parent, None for root>,
          "children": [ <same structure>, ... ]
        }
    """

    def _recurse(node, remaining_depth, visited):
        successors = graph.get(node, Counter())
        children = []
        for child, cnt in successors.most_common(branching):
            if child in visited:
                continue
            child_tree = {"name": child, "count": cnt, "children": []}
            if remaining_depth > 1:
                child_tree["children"] = _recurse(
                    child, remaining_depth - 1, visited | {child}
                )
            children.append(child_tree)
        return children

    return {
        "name": root,
        "count": None,
        "children": _recurse(root, depth, {root}),
    }


def print_tree(node: dict, prefix: str = "", is_last: bool = True) -> None:
    connector = "└── " if is_last else "├── "
    count_str = f"  (×{node['count']})" if node["count"] is not None else ""
    print(prefix + (connector if prefix else "") + node["name"] + count_str)
    child_prefix = prefix + ("    " if is_last else "│   ")
    children = node["children"]
    for i, child in enumerate(children):
        print_tree(child, child_prefix, i == len(children) - 1)


# ─────────────────────────────────────────────────────────────────────────────
# 4.  Main demo
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    LOG_FILE = "HealthApp.log"

    print("Parsing log file …")
    parsed_logs = parse_log_file(LOG_FILE)

    # ── 1. Unique events ──────────────────────────────────────────────────────
    unique_events = get_unique_event_names(parsed_logs)
    print(f"\n{'='*60}")
    print(f"Unique event names ({len(unique_events)} total):")
    for name in sorted(unique_events):
        print(f"  {name}")

    # ── 2. Transition graph ───────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("Building sequence graph (window=1) …")
    graph = build_sequence_graph(parsed_logs, window=1)

    # ── 3. Successor trees for every unique event ─────────────────────────────
    print(f"\n{'='*60}")
    print("Most-common successor trees (branching=2, depth=4):\n")
    for event_name in sorted(unique_events):
        tree = build_successor_tree(graph, event_name, branching=2, depth=4)
        print_tree(tree)
        print()
