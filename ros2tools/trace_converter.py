import re
import json


# trace_converter.py provides procedural parsing to JSON for babeltrace2 log files

def flatten_dict(d, parent_key='', sep='.'):
    """
    Recursively flattens a nested dictionary.
    
    :param d: The dictionary to flatten.
    :param parent_key: The base key string to prepend to each key.
    :param sep: The separator between parent and child keys.
    :return: A flattened dictionary.
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def trace_log_to_dict(input_file):
    pattern = re.compile(
        r"""
        \[(?P<timestamp>[^\]]+)\]\s+               # Timestamp in brackets
        \((?P<delta>[^\)]+)\)\s+                   # Delta time in parentheses
        (?P<hostname>[^\s]+)\s+                    # Hostname 
        (?P<event>[^\:]+:[^\:]+):\s+               # Event name
        (?P<data>.+)                               # Remaining data
        """,
        re.VERBOSE,
    )

    def parse_data_blocks(data):
        result = []
        for block in re.findall(r"\{([^\}]+)\}", data):
            key_value_pairs = {}
            for item in block.split(", "):
                if "=" in item:
                    key, value = item.split("=", 1)
                    key_value_pairs[key.strip()] = value.strip().strip('"')
            result.append(key_value_pairs)
        return result

    parsed_events = []
    unmatched_lines = []

    with open(input_file, "r") as infile:
        for line in infile:
            match = pattern.match(line.strip())
            if match:
                event = match.groupdict()
                data_blocks = parse_data_blocks(event["data"])
                # Flatten each data block and add to the event
                flattened_data = [flatten_dict(data_block) for data_block in data_blocks]
                # Merge flattened data into the event dictionary
                for data in flattened_data:
                    event.update(data)
                parsed_events.append(event)
            else:
                unmatched_lines.append(line.strip())

    if unmatched_lines:
        print(f"Unmatched {len(unmatched_lines)} lines:")
        for line in unmatched_lines[:5]:
            print(line)

    return parsed_events

def trace_log_to_dict_(input_file):
    pattern = re.compile(
        r"""
        \[(?P<timestamp>[^\]]+)\]\s+               # Timestamp in brackets
        \((?P<delta>[^\)]+)\)\s+                   # Delta time in parentheses
        (?P<hostname>[^\s]+)\s+                    # hostname 
        (?P<event>[^\:]+:[^\:]+):\s+               # Event name
        (?P<data>.+)                               # Remaining data
        """,
        re.VERBOSE,
    )

    def parse_data_blocks(data):
        result = []
        for block in re.findall(r"\{([^\}]+)\}", data):
            key_value_pairs = {}
            for item in block.split(", "):
                if "=" in item:
                    key, value = item.split("=", 1)
                    key_value_pairs[key.strip()] = value.strip().strip('"')
            result.append(key_value_pairs)
        return result

    parsed_events = []
    unmatched_lines = []

    with open(input_file, "r") as infile:
        for line in infile:
            match = pattern.match(line.strip())
            if match:
                event = match.groupdict()
                event["data"] = parse_data_blocks(event["data"])
                parsed_events.append(event)
            else:
                unmatched_lines.append(line.strip())

    if unmatched_lines:
        print(f"Unmatched {len(unmatched_lines)} lines:")
        for line in unmatched_lines[:5]:
            print(line)

    return parsed_events
