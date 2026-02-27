"""
sequence_analysis.py
"""

import argparse
import sys
import os
from collections import defaultdict, Counter

"Import parser from parser.py"
sys.path.insert(0, os.path.dirname(__file__))
from parser import parse_log_file

"Print all of the frequencies of the software component"
def print_frequencies(d):
    arr = [];
    sum = 0;
    for (k, v) in d.items():
        arr.append((len(v), k));
        sum += len(v);
    arr = sorted(arr)[::-1];

    for (v, k) in arr:
        print(f"{k}: encountered {v} times, {v/sum*100:.2f}%")


"Return a set of all the unique event names of the dataset"
def get_unique_event_names(parsed_logs: dict) -> set:
    names = set()
    for logs in parsed_logs.values():
        for log in logs:
            names.add(log.event["name"])
    return names

"""
For every element i in the list, we check (i, i+{window}) in the list of events. window is 1 by default

For every pair (i, i+{window}) that share the
same component and PID, increment edge[event_i][event_{i+window}].

We group every event by component because they may occur in parallel and the cycle should still be identical even if the events of different components differ in order.

Returns
-------
graph : dict[str, Counter]
    graph[src][dst] = number of times dst followed src.
"""
def build_sequence_graph(parsed_logs: dict, window: int = 1) -> dict:
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


def build_successor_tree(
        graph: dict, root: str, branching: int = 2, depth: int = 4, threshold: int = 1, relative_threshold: float = 0.15, inverted: bool = False
) -> dict:
    """
    Build a tree (dict) rooted at *root* showing the *branching* most-common
    successors at each level, up to *depth* levels deep.

    Only edges with count >= *threshold* are considered;

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
    connector = "|---"

    count_str = f"  (x{node['count']})" if node["count"] is not None else ""

    print(prefix + (connector if prefix else "") + node["name"] + count_str)

    child_prefix = prefix + ("    " if is_last else "|   ")
    children = node["children"]

    for i, child in enumerate(children):
        print_tree(child, child_prefix, i == len(children) - 1)


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
        help="Minimum number of times an A->B transition must "
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
        help="Relative frequency that an A->B transition must "
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
            f"Threshold : transitions must occur >= {args.threshold} time(s) to form a chunk and must occur at a relative rate of >= {args.relative_threshold}\n"
        )
    else:
        print(
            f"Threshold : transitions must occur < {args.threshold} time(s) to form a chunk and must occur at a relative rate of < {args.relative_threshold}\n"
        )
    parsed_logs, total = parse_log_file(args.log_file)

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
