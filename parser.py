import argparse;
import sys

class Log:
    def __init__(self, timestamp, component_name, pid, event):
        self.timestamp = timestamp
        self.component_name = component_name
        self.pid = int(pid)
        self.event = event

    def __str__(self):
        return f"time: {self.timestamp} | component name: {self.component_name} | pid: {self.pid} | event: {self.event}"

    def __repr__(self):
        return f"time: {self.timestamp} | component name: {self.component_name} | pid: {self.pid} | event: {self.event}"

def print_frequencies(d):
    arr = [];
    sum = 0;
    for (k, v) in d.items():
        arr.append((len(v), k));
        sum += len(v);
    arr = sorted(arr)[::-1];

    for (v, k) in arr:
        print(f"{k}: encountered {v} times, {v/sum*100:.2f}%")

def parse_event(content: str):
    content = content.strip()

    for i, ch in enumerate(content):
        if not ch.isalpha():  # first non-alphanumeric char
            return {"name": content[:i], "event_data": content[i + 1 :].strip()}

    # no delimiter found
    return {"name": content, "event_data": ""}



log_num = 0

def parse_log_file(filepath):
    global log_num
    logs = {}
    total = 0;

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split("|", 3)
            if len(parts) != 4:
                continue

            date_str, component, pid_str, content = parts

            event = parse_event(content)
            log = Log(date_str, component, pid_str, event)

            if component not in logs:
                logs[component] = []

            logs[component].append(log)
            total += 1

    return (logs, total)

def parse_arguments(args):
    if len(args) < 2:
        print("Please provide a filename as a command-line argument")
        sys.exit(1)
    
    abs_threshold = 100
    rel_threshold = 0.15
    args = args[1:]
    for i,arg in enumerate(args[:-2]):
        if arg == "-t":
            abs_threshold = int(args[i + 1])
        if arg == '-n':
            rel_threshold = float(args[i + 1])

    if abs_threshold < 0:
        print("=== WARNING ===")
        print("Absolute threshold must be greater/equal 0, using default value of 100")
        print()
        abs_threshold = 100
    if rel_threshold < 0.0 or rel_threshold > 1.0:
        print("=== WARNING ===")
        print("Relative threshold must be between 0 and 1 (inclusive), using default value of 0.15")
        print()
        rel_threshold = 0.15
    return (abs_threshold, rel_threshold, args[-1])




# === RUN ===
if __name__ == "__main__":
    (a, b, filename) = parse_arguments(sys.argv)

    parsed_logs = parse_log_file(filename)
    print(f"=== BASIC REPORT ===")
    print(f"# events: {log_num}")
    print()
    print(f"Event frequency: ")
    print_frequencies(parsed_logs);
    print()


"""
if __name__ == "__main__":
    parsed_logs, total = parse_log_file("HealthApp.log")

    # Collect unique event names
    unique_events = set(
        log.event["name"] for logs in parsed_logs.values() for log in logs
    )

    # Print results
    print("Total unique event names:", len(unique_events))
    print("\nEvent Names:")
    for name in sorted(unique_events):
        print(name)
"""
