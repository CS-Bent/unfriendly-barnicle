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
