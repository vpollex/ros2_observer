import sys
import yaml
import json

def yaml_to_json(yaml_file):
    with open(yaml_file, 'r') as yf:
        documents = yaml.safe_load_all(yf)
        data = list(documents)
    print(json.dumps(data, indent=4))

if __name__ == "__main__":
    yaml_to_json("y.yaml")

