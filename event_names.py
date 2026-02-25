"""
event_names.py

Identification of unique event names across all components.
"""


def get_unique_event_names(parsed_logs: dict) -> set:
    """Return the set of all distinct event *names* (ignoring data values)."""
    names = set()
    for logs in parsed_logs.values():
        for log in logs:
            names.add(log.event["name"])
    return names
