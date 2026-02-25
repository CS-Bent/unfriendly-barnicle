"""
sequence_analysis.py

CLI entry point for analysing event sequences in a HealthApp log file.
Imports functionality from event_names, sequence_graph and successor_tree.
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from parser import parse_log_file  # noqa: E402
from event_names import get_unique_event_names  # noqa: E402
from sequence_graph import build_sequence_graph  # noqa: E402
from successor_tree import build_successor_tree, print_tree  # noqa: E402


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
    args = ap.parse_args()

    print(f"Parsing log file: {args.log_file}")
    print(
        f"Threshold : transitions must occur ≥ {args.threshold} time(s) to form a chunk\n"
    )
    parsed_logs = parse_log_file(args.log_file)

    # ── 1. Unique events ──────────────────────────────────────────────────────
    unique_events = get_unique_event_names(parsed_logs)
    print(f"{'='*60}")
    print(f"Unique event names ({len(unique_events)} total):")
    for name in sorted(unique_events):
        print(f"  {name}")

    # ── 2. Transition graph ───────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"Building sequence graph (window={args.window}) …")
    graph = build_sequence_graph(parsed_logs, window=args.window)

    # ── 3. Successor trees for every unique event ─────────────────────────────
    print(f"\n{'='*60}")
    print(
        f"Most-common successor trees "
        f"(threshold={args.threshold}, branching={args.branching}, depth={args.depth}):\n"
    )
    for event_name in sorted(unique_events):
        tree = build_successor_tree(
            graph,
            event_name,
            branching=args.branching,
            depth=args.depth,
            threshold=args.threshold,
        )
        # only print trees that have at least one qualifying edge
        if tree["children"]:
            print_tree(tree)
            print()
