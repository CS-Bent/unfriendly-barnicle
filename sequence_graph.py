"""
sequence_graph.py

Per-event sequence graph: for each unique event E, build a directed-graph
of "what event comes next most often" by scanning all (event[i], event[i+1])
pairs within the same PID/component session.  The graph is stored as a
dict-of-dicts with edge counts.
"""

from collections import defaultdict, Counter


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


def most_common_sequence(
    graph: dict, start_event: str, depth: int = 5, threshold: int = 1
) -> list:
    """
    Follow the single most-common successor at each step from start_event,
    only considering edges whose count meets *threshold*.

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
        ranked = [(c, cnt) for c, cnt in successors.most_common() if cnt >= threshold]
        next_event = None
        for candidate, count in ranked:
            if candidate not in visited:
                next_event = (candidate, count)
                break
        if next_event is None:
            if not ranked:
                break  # all successors below threshold — stop the chain
            # allow revisit if no unvisited successor exists
            next_event = (ranked[0][0], ranked[0][1])
        path.append(next_event)
        visited.add(next_event[0])
        current = next_event[0]

    return path
