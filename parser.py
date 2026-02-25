import re

class Log:
    def __init__(self, timestamp, component_name, pid, event):
        self.timestamp = timestamp;
        self.component_name = component_name;
        self.pid = int(pid);
        self.event = event;

    def __str__(self):
        return f"time: {self.timestamp} | component name: {self.component_name} | pid: {self.pid} | event: {self.event}"

def parse_event(content: str):
    """
    Splits event content into name + data.
    Example:
        'onStandStepChanged 3579'
        -> name='onStandStepChanged', data='3579'
    """
    parts = content.strip().split(" ", 1)
    name = parts[0]
    data = parts[1] if len(parts) > 1 else ""
    return {
        "name": name,
        "event_data": data
    }


def parse_log_file(filepath):
    logs = []

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

            logs.append(log)

    return logs


# === RUN ===
if __name__ == "__main__":
    parsed_logs = parse_log_file("HealthApp.log")

    # Print first few entries for testing
    for log in parsed_logs[:5]:
        print(log)
