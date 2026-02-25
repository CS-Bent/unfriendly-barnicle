import re

class Log:
    def __init__(self, timestamp, component_name, pid, event):
        self.timestamp = timestamp;
        self.component_name = component_name;
        self.pid = int(pid);
        self.event = event;

    def __str__(self):
        return f"time: {self.timestamp} | component name: {self.component_name} | pid: {self.pid} | event: {self.event}"

    def __repr__(self):
        return f"time: {self.timestamp} | component name: {self.component_name} | pid: {self.pid} | event: {self.event}"

def parse_event(content: str):
    content = content.strip()

    for i, ch in enumerate(content):
        if not ch.isalpha():  # first non-alphanumeric char
            return {
                "name": content[:i],
                "event_data": content[i+1:].strip()
            }

    # no delimiter found
    return {
        "name": content,
        "event_data": ""
    }

def parse_log_file(filepath):
    logs = {}

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Split into main sections
            parts = line.split("|", 3)
            if len(parts) != 4:
                continue  # skip malformed lines

            date_str, component, pid_str, content = parts

            log = Log(date_str, component, pid_str, content);
            if log not in logs:
                logs[log.component_name] = []

            logs[log.component_name].append(log)

    return logs


# === RUN ===
if __name__ == "__main__":
    parsed_logs = parse_log_file("HealthApp.log")

    # Print first few entries for testing
    for i, (k,v) in enumerate(parsed_logs.items()):
        print(f"key: {k}, value: {v[:1]}")

if __name__ == "__main__":
    parsed_logs = parse_log_file("HealthApp.log")

    # Collect unique event names
    unique_events = set(log["Event"]["name"] for log in parsed_logs)

    # Print results
    print("Total unique event names:", len(unique_events))
    print("\nEvent Names:")
    for name in sorted(unique_events):
        print(name)