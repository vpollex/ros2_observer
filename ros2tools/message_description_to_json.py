import subprocess
import json

def get_message_description(message_type):
    try:
        result = subprocess.run(
            ['ros2', 'interface', 'show', message_type],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e.stderr.strip()}")
        return None

def parse_description(description):
    lines = description.strip().split('\n')
    fields = []

    for line in lines:
        parts = line.split()
        if len(parts) >= 2:
            field_type = parts[0]
            field_name = parts[1]
            fields.append({'type': field_type, 'name': field_name})

    return {'fields': fields}

def description_to_json(message_type):
    description = get_message_description(message_type)
    if description:
        parsed_description = parse_description(description)
        return json.dumps(parsed_description, indent=2)
    else:
        return None

if __name__ == '__main__':
    import sys

    if len(sys.argv) != 2:
        print("Usage: python3 message_description_to_json.py <message_type>")
        sys.exit(1)

    message_type = sys.argv[1]
    json_description = description_to_json(message_type)
    if json_description:
        print(json_description)

