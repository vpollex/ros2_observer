import subprocess
import json
import yaml
import sys
import re
import os

try:
    from ros2tools.util import *
    from ros2tools.util import run_command

except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), "."))
    from util import *
    from util import run_command
    from trace_converter import *



EMPTY_MESSAGE_COMMAND_TEMPLATE = 'ros2 topic pub -1 {topic} {data_type} "{{}}" >/dev/null 2>&1 && sleep 1s && ros2 topic echo {topic} --once | grep -v "WARNING"'
EMPTY_MESSAGE_COMMAND_TEMPLATE_RAW = 'ros2 topic pub -1 {topic} {data_type} "{{}}"'

class ROS2Tools:
 
    PRIMITIVE_TYPES = [
        "bool", 
        "byte", 
        "char", 
        "float32",
        "float64", 
        "int8", 
        "uint8", 
        "int16", 
        "uint16", 
        "int32", 
        "uint32", 
        "int64", 
        "uint64", 
        "string", 
        "wstring"
    ]

    @staticmethod
    def filter_edges(graph):
        node_types = {node['id']: node['type'] for node in graph['nodes']}
    
        filtered_edges = [
            edge for edge in graph['edges']
            if node_types.get(edge['source']) != 'topic' and node_types.get(edge['target']) != 'topic'
        ]
    
        return filtered_edges

    @staticmethod
    def find_edge(edges, node_a, node_b, topic):
        """
        Finds an edge from node_a to node_b through a topic.

        Parameters:
        - edges (list of dict): A list of edge dictionaries with 'source' and 'target' keys.
        - node_a (str): The identifier for the first node.
        - node_b (str): The identifier for the second node.
        - topic (str): The topic identifier.

        Returns:
        - dict or None: A dictionary representing the edge {'source': node_a, 'target': node_b} 
                        if both edges are found, otherwise None.
        """
        # Find edge_a
        edge_a = next((edge for edge in edges if edge['source'] == node_a['node'] and edge['target'] == topic['topic']), None)
        
        # Find edge_b
        edge_b = next((edge for edge in edges if edge['source'] == topic and edge['target'] == node_b['node']), None)
        
        # Check if both edges are found
        if edge_a and edge_b:
            return {"source": node_a['node'], "target": node_b['node'], 'topic': topic}
        
        return None

    @staticmethod
    def generate_graph(nodes):
        graph = {'nodes':[], 'edges':[]}
        edges=[]
        publisher_edges=[]
        subscriber_edges=[]
        consolidated_edges=[]
        topics=[]
        for node in nodes:
            if not node:
                continue
            graph['nodes'].append({'id':node['node'], 'type':'node'})
            for topic in node['topics']:
                #graph['nodes'].append({'id':topic['topic'], 'type':'topic'})
                topics.append(topic)
                if topic['role'] == "subscriber":
                    edge = {'source':topic['topic'], 'target':node['node'], 'node':node['node'], 'topic':topic['topic'], 'type':'subscriber'}
                    edges.append(edge)
                    subscriber_edges.append(edge)

                elif topic['role'] == "publisher":
                    edge ={'source':node['node'], 'target':topic['topic'], 'node':node['node'], 'topic':topic['topic'], 'type':'publisher'}
                    edges.append(edge)
                    publisher_edges.append(edge)

        for publisher_edge in publisher_edges:
            for subscriber_edge in subscriber_edges:
                if publisher_edge['topic'] == subscriber_edge['topic']:
                    if publisher_edge['source'] != subscriber_edge['target']:
                        consolidated_edge = {'source':publisher_edge['source'], 'target':subscriber_edge['target'], 'topic':publisher_edge['topic']}
                        print(consolidated_edge)
                        consolidated_edges.append(consolidated_edge)


        graph['edges'] = consolidated_edges
        return graph

    @staticmethod
    def parse_typedef_text(typedef_text, interface_text):
        if not typedef_text:
            return {}

        if not interface_text:
            return {}

        typedef_pattern = re.compile(
            r'^(?P<datatype>[a-zA-Z0-9_/]+)'         # Datatype (e.g., uint32, SetPoint)
            r'(?P<constraint><=?\d+)?'               # Optional constraint (e.g., <=255 for strings)
            r'(\[(?P<array_constraint>[^\]]*)\])?'   # Optional array brackets (e.g., [])
            r'\s+(?P<label>[a-zA-Z0-9_]+)'           # Label (e.g., set_points, request_id)
            r'(?:\s*=\s*(?P<value>[^\s]+))?'         # Optional value after '=' (e.g., constants)
            r'(?:\s+(?P<value_no_equals>[^\s]+))?'   # Optional value without '=' (e.g., constants with no equals)
            r'$'
        )

        match = typedef_pattern.match(typedef_text)

        if not match:
            return None

        datatype = match.group('datatype')
        label = match.group('label')
        array_constraint = match.group('array_constraint') or ""
        value = match.group('value') or match.group('value_no_equals') or ""
        constraint = match.group('constraint') or ""

        if value:
            typedef_type = "constant"
        elif "[]" in typedef_text or array_constraint:
            typedef_type = "array" if datatype in ROS2Tools.PRIMITIVE_TYPES else "object_array"
        elif datatype in ROS2Tools.PRIMITIVE_TYPES:
            typedef_type = "primitive"
        else:
            typedef_type = "object"

        typedef_dict = {
            "type": typedef_type,
            "datatype": datatype,
            "label": label,
            "array_constraint": array_constraint,
            "constraint": constraint,
            "value": value,
            "typedef_text": typedef_text
        }

        if typedef_dict['type'] in ["object", "object_array"]:
            typedef_dict['fields'] = []
            typedef_dict['object_interface_text'] = ROS2Tools.get_object_interface_text(interface_text, typedef_text)
            if typedef_dict['object_interface_text']:
                typedef_dict["fields"] = ROS2Tools.get_fields(typedef_dict['object_interface_text'])

        return typedef_dict

    @staticmethod
    def get_fields(interface_text):
        lines = interface_text.splitlines()
        return [ROS2Tools.parse_typedef_text(line, interface_text) for line in lines if line.strip() and not line.startswith((' ', '\t'))]

    @staticmethod
    def remove_parent_object_nesting(text):
        lines = text.splitlines()

        if not lines:
            return text

        first_line = next((line for line in lines if line.strip()), "")
        leading_whitespace = len(first_line) - len(first_line.lstrip())

        if first_line.startswith(" " * leading_whitespace):
            whitespace_char = ' '
        elif first_line.startswith("\t" * leading_whitespace):
            whitespace_char = '\t'
        else:
            return text

        for line in lines:
            if line.strip() and not line.startswith(whitespace_char * leading_whitespace):
                return text

        adjusted_lines = []
        for line in lines:
            if line.startswith(whitespace_char * leading_whitespace):
                adjusted_lines.append(line[leading_whitespace:])
            else:
                adjusted_lines.append(line)

        return "\n".join(adjusted_lines)

    @staticmethod
    def remove_one_level_of_nesting(text):
        lines = text.splitlines()
        
        if not lines:
            return text
        
        first_line = lines[0]
        leading_whitespace = len(first_line) - len(first_line.lstrip())
        
        if leading_whitespace == 0:
            return text
        
        if first_line.startswith(" " * leading_whitespace):
            whitespace_char = ' '
        elif first_line.startswith("\t" * (leading_whitespace // len("\t"))):
            whitespace_char = '\t'
        else:
            whitespace_char = None
        
        if whitespace_char is None:
            return text
        
        adjusted_lines = []
        for line in lines:
            if line.startswith(whitespace_char * leading_whitespace):
                adjusted_lines.append(line[leading_whitespace:])
            else:
                adjusted_lines.append(line)

        return "\n".join(adjusted_lines)

    @staticmethod
    def get_object_interface_text(interface_text, field_text):
        lines = interface_text.splitlines()
        object_lines = [] 
        print(f"  typedef text: {field_text}")
        counter = -1
        for line in lines:
            if line.strip() == field_text.lstrip():
                counter += 1
                continue

            if counter >= 0:
                if line == line.lstrip():
                    break
                else:
                    object_lines.append(line)

        return ROS2Tools.remove_parent_object_nesting("\n".join(object_lines))
        # return remove_one_level_of_nesting("\n".join(object_lines))

    @staticmethod
    def trim_whitespace_around_equals(input_string):
        parts = input_string.split('=', 1)
        if len(parts) == 1:
            return input_string.strip()
        left_part = parts[0].strip()
        right_part = parts[1].strip()
        return f"{left_part}={right_part}"

    @staticmethod
    def parse_interface_text(interface_text):
        return ROS2Tools.get_fields(interface_text)

    @staticmethod
    def trim_comments(text):
        """
        Remove comments (lines starting with #) from the given text.
        """
        lines = text.splitlines()
        trimmed_lines = []

        for line in lines:
            stripped_line = line.lstrip()
            if stripped_line.startswith("#"):
                continue

            if "#" in line:
                line = line.split("#", 1)[0].rstrip()

            if line.strip():
                trimmed_lines.append(line)

        return "\n".join(trimmed_lines)

    @staticmethod
    def get_interface_text(message_type):
        """
        Fetch and return the trimmed interface description of the specified message type.
        """
        output = ROS2Tools.trim_comments(run_command(f"ros2 interface show {message_type}")[0])
        print("interface description:")
        print(f"{output}")
        return output

    @staticmethod
    def get_topic_info(topic_name):
        """
        Get the type of a given ROS 2 topic using `ros2 topic info`.
        """
        info = run_command(f'ros2 topic info {topic_name} | sed "/  Service Servers:/q"')[0]
        if info:
            lines = info.split("\n")
            for line in lines:
                if line.startswith("Type:"):
                    return line.split()[1]
        return None

    @staticmethod
    def get_node_info(node_name):
        """
        Fetch information about a given node using `ros2 node info`.
        """
        node_info = run_command(f"ros2 node info --no-daemon {node_name} | sed '/Service Servers:/q' | sed '/Service Servers:/d'")[0]
        if not node_info:
            node_info = run_command(f"ros2 node info --no-daemon /{node_name} | sed '/Service Servers:/q' | sed '/Service Servers:/d'")[0]
        if not node_info:
            return None

        #data = ROS2Tools.parse_node_info(node_name, info)
        #data = []
        #data["node_name"] = node_name
        print(node_info)
        return node_info

    @staticmethod
    def get_nodes():
        """
        Get the list of active ROS 2 nodes using `ros2 node list`.
        """
        node_list = run_command("ros2 node list --all --no-daemon | grep -v ros2cli | sort | uniq")[0]
        if not node_list:
            return []

        nodes = node_list.split("\n")
        return nodes

    @staticmethod
    def get_interface_info(message_type):
        output = ROS2Tools.trim_comments(run_command(f"ros2 interface show {message_type}")[0])
        return output

    @staticmethod
    def get_node(node_name):
        """
        Search for a node by its name, allowing partial matches even when the 
        node name includes arbitrary prefixes. If found, returns the full node name.
        If not found, raises an Exception.
        """
        nodes = ROS2Tools.get_nodes()
        
        available_nodes = "\n".join(nodes)
        for node in nodes:
            if node.endswith(node_name):
                return node
        raise Exception(f"ERROR: No node with the name: '{node_name}' not found. Did you run the scenario? \nAvailable nodes:\n{available_nodes}\n Run a scenario and try again.")
        for node in nodes:
            if node.endswith(node_name):
                return node

    @staticmethod
    def get_node_summary(node_name):

        node_summary = {"node": node_name}
        node_info = ROS2Tools.get_node_info(node_name) 
        if node_info is None or node_info == "":
            print(f"Failed to get information for node '{node_name}'")
            return

        publishers = []
        subscribers = []
        topics = []


        lines = node_info.strip().split('\n')
        is_publisher_section = False
        is_subscriber_section = False

        for line in lines:
            if 'Publishers:' in line:
                is_publisher_section = True
                is_subscriber_section = False
                continue
            elif 'Subscribers:' in line:
                is_publisher_section = False
                is_subscriber_section = True
                continue
        
            if is_publisher_section:
                parts = line.split(':', 1)
                topic = parts[0].strip()
                if parts == "":
                    continue
                datatype = parts[1].strip()
                interface_text = ROS2Tools.get_interface_info(datatype)
                interface = ROS2Tools.parse_interface_text(interface_text)
                topics.append({'topic':topic, 
                               'role':'publisher',
                               'datatype': datatype,
                               'interface_text': interface_text,
                               'interface': interface})

            if is_subscriber_section:
                parts = line.split(':', 1)
                if parts == "":
                    continue
                topic = parts[0].strip()
                datatype = parts[1].strip()
                interface_text = ROS2Tools.get_interface_info(datatype)
                interface = ROS2Tools.parse_interface_text(interface_text)
                topics.append({'topic':topic, 
                               'role':'subscriber',
                               'datatype': datatype,
                               'interface_text': interface_text,
                               'interface': interface})

 
        #node_summary['publishers'] = publishers
        #node_summary['subscribers'] = subscribers
        node_summary['topics'] = topics
        return node_summary

