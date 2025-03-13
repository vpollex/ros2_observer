import re
import json
import datetime
import time


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
            if isinstance(v, str) and v.isdigit():
                v = int(v)
            items.append((new_key, v))
    return dict(items)

def convert_timestamp_to_unix_ns(timestamp_str):
    """
    Convert a timestamp string like "11:11:49.443960423" to a Unix timestamp in nanoseconds.
    
    :param timestamp_str: The timestamp string to convert
    :return: Unix timestamp in nanoseconds as a 64-bit integer
    """
    try:
        today = datetime.datetime.now().date()
        
        hours, minutes, seconds_frac = timestamp_str.split(':')
        seconds_parts = seconds_frac.split('.')
        seconds = seconds_parts[0]
        
        nanoseconds = 0
        if len(seconds_parts) > 1:
            nano_str = seconds_parts[1].ljust(9, '0')[:9]
            nanoseconds = int(nano_str)
        
        dt = datetime.datetime.combine(
            today,
            datetime.time(int(hours), int(minutes), int(seconds))
        )
        
        unix_seconds = int(dt.timestamp())
        unix_ns = unix_seconds * 1_000_000_000 + nanoseconds
        
        return int(unix_ns)
    except Exception as e:
        print(f"Error converting timestamp '{timestamp_str}': {e}")
        return None

def convert_delta_to_ns(delta_str):
    """
    Convert a delta string like "+0.000014778" to nanoseconds as a 64-bit integer.
    
    :param delta_str: The delta string to convert
    :return: Delta in nanoseconds as a 64-bit integer
    """
    try:
        if "?" in delta_str:
            return 0
            
        if delta_str.startswith('+'):
            delta_str = delta_str[1:]
        
        delta_sec = float(delta_str)
        delta_ns = int(delta_sec * 1_000_000_000)
        
        return int(delta_ns)
    except Exception as e:
        print(f"Error converting delta '{delta_str}': {e}")
        return 0

def parse_value(value):
    """
    Parse a value string to convert it to appropriate data type.
    
    :param value: String value to parse
    :return: Parsed value (integer, float, or original string)
    """
    if isinstance(value, str):
        if value.isdigit():
            return int(value)
        try:
            float_val = float(value)
            if float_val.is_integer():
                return int(float_val)
            return float_val
        except ValueError:
            pass
    return value

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
                    value = value.strip().strip('"')
                    key_value_pairs[key.strip()] = parse_value(value)
            result.append(key_value_pairs)
        return result

    parsed_events = []
    unmatched_lines = []

    with open(input_file, "r") as infile:
        for line in infile:
            match = pattern.match(line.strip())
            if match:
                event = match.groupdict()
                
                original_timestamp = event["timestamp"]
                unix_timestamp_ns = convert_timestamp_to_unix_ns(original_timestamp)
                if unix_timestamp_ns is not None:
                    event["original_timestamp"] = original_timestamp
                    event["timestamp"] = unix_timestamp_ns
                
                original_delta = event["delta"]
                delta_ns = convert_delta_to_ns(original_delta)
                event["original_delta"] = original_delta
                event["delta"] = delta_ns
                
                data_blocks = parse_data_blocks(event["data"])
                flattened_data = [flatten_dict(data_block) for data_block in data_blocks]
                for data in flattened_data:
                    for key, value in data.items():
                        data[key] = parse_value(value)
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
                    value = value.strip().strip('"')
                    key_value_pairs[key.strip()] = parse_value(value)
            result.append(key_value_pairs)
        return result

    parsed_events = []
    unmatched_lines = []

    with open(input_file, "r") as infile:
        for line in infile:
            match = pattern.match(line.strip())
            if match:
                event = match.groupdict()
                
                original_timestamp = event["timestamp"]
                unix_timestamp_ns = convert_timestamp_to_unix_ns(original_timestamp)
                if unix_timestamp_ns is not None:
                    event["original_timestamp"] = original_timestamp
                    event["timestamp"] = unix_timestamp_ns
                
                original_delta = event["delta"]
                delta_ns = convert_delta_to_ns(original_delta)
                event["original_delta"] = original_delta
                event["delta"] = delta_ns
                
                event["data"] = parse_data_blocks(event["data"])
                parsed_events.append(event)
            else:
                unmatched_lines.append(line.strip())

    if unmatched_lines:
        print(f"Unmatched {len(unmatched_lines)} lines:")
        for line in unmatched_lines[:5]:
            print(line)

    return parsed_events

class Int64Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, int):
            return int(obj)
        return super(Int64Encoder, self).default(obj)

def save_to_json(parsed_events, output_file):
    with open(output_file, 'w') as f:
        json.dump(parsed_events, f, cls=Int64Encoder, indent=2)
