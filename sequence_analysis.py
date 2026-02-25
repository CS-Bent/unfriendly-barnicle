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

import argparse
import sys
import os
from collections import defaultdict, Counter

# ── re-use the existing parser ────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from parser import parse_log_file, parse_event  # noqa: E402

def print_frequencies(d):
    arr = [];
    sum = 0;
    for (k, v) in d.items():
        arr.append((len(v), k));
        sum += len(v);
    arr = sorted(arr)[::-1];

    for (v, k) in arr:
        print(f"{k}: encountered {v} times, {v/sum*100:.2f}%")

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


# ─────────────────────────────────────────────────────────────────────────────
# 3.  Tree-structured "chunk" for each unique event
# ─────────────────────────────────────────────────────────────────────────────


def build_successor_tree(
        graph: dict, root: str, branching: int = 2, depth: int = 4, threshold: int = 1, relative_threshold: float = 0.15, inverted: bool = False
) -> dict:
    """
    Build a tree (dict) rooted at *root* showing the *branching* most-common
    successors at each level, up to *depth* levels deep.

    Only edges with count >= *threshold* are considered; a branch is pruned
    entirely once no qualifying successors remain.

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
        # filter by threshold before picking top-branching candidates

        sucs = successors.most_common()
        total = sum(j for _,j in sucs)
        
        qualified = [
            (c, cnt)
            for c, cnt in sucs
            if (inverted and cnt < threshold and relative_threshold > cnt/total and c not in visited) or
                (not inverted and cnt >= threshold and relative_threshold <= cnt/total and c not in visited)
        ]
        for child, cnt in qualified[:branching]:
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
    ap = argparse.ArgumentParser(
        description="Analyse event sequences in a HealthApp log file."
    )
    ap.add_argument(
        "log_file",
        nargs="?",
        default="HealthApp.log",
        help="Path to the log file (default: HealthApp.log)",
    )
    ap.add_argument(
        "--threshold",
        "-t",
        type=int,
        default=1,
        help="Minimum number of times an A→B transition must "
        "occur to be included in a chunk (default: 1).",
    )
    ap.add_argument(
        "--branching",
        "-b",
        type=int,
        default=2,
        help="Max successors shown per node in the tree (default: 2).",
    )
    ap.add_argument(
        "--depth",
        "-d",
        type=int,
        default=4,
        help="Max depth of each successor tree (default: 4).",
    )
    ap.add_argument(
        "--window",
        "-w",
        type=int,
        default=1,
        help="Look-ahead window when building transition pairs (default: 1).",
    )
    ap.add_argument(
        "--relative_threshold",
        "-r",
        type=float,
        default=0.15,
        help="Relative frequency that an A→B transition must "
        "occur to be included in a chunk (default: 1).",
    )
    ap.add_argument(
        "--inverted",
        "-i",
    )
    args = ap.parse_args()

    print(f"Parsing log file: {args.log_file}")
    if args.inverted is None:
        print(
            f"Threshold : transitions must occur ≥ {args.threshold} time(s) to form a chunk and must occur at a relative rate of ≥ {args.relative_threshold}\n"
        )
    else:
        print(
            f"Threshold : transitions must occur < {args.threshold} time(s) to form a chunk and must occur at a relative rate of < {args.relative_threshold}\n"
        )
    parsed_logs, total = parse_log_file(args.log_file)

    # ── 1. Unique events ──────────────────────────────────────────────────────
    unique_events = get_unique_event_names(parsed_logs)
    print(f"{'='*60}")
    print(f"Total amount of events: {total}")
    print()
    print(f"Component frequency:")
    print_frequencies(parsed_logs)
    print()
    print(f"Unique event names ({len(unique_events)} total):")
    for name in sorted(unique_events):
        print(f"  {name}")

    graph = build_sequence_graph(parsed_logs, window=args.window)

    # ── 3. Successor trees for every unique event ─────────────────────────────
    print(f"\n{'='*60}")
    print(
        f"Filtered successor trees "
        f"(threshold={args.threshold}, branching={args.branching}, depth={args.depth}):\n"
    )
    for event_name in sorted(unique_events):
        tree = build_successor_tree(
            graph,
            event_name,
            branching=args.branching,
            depth=args.depth,
            threshold=args.threshold,
            relative_threshold=args.relative_threshold,
            inverted=(args.inverted is not None)
        )
        # only print trees that have at least one qualifying edge
        if tree["children"]:
            print_tree(tree)
            print()
