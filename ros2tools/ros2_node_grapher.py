import os
import json
import networkx as nx
import plotly.graph_objects as go
import graphviz
import numpy as np

OUTPUT_DIRECTORY = os.environ.get('ROS_HOME', '.') + "/ros2_node_inspector"


class ROS2NodeGrapher:
    def __init__(self, graph_json_file):
        self.graph_json_file = graph_json_file
        self.graph = nx.DiGraph()

        if not os.path.exists(OUTPUT_DIRECTORY):
            os.makedirs(OUTPUT_DIRECTORY)

        self._load_graph_data()

    def _load_graph_data(self):
        with open(self.graph_json_file, 'r') as file:
            graph_data = json.load(file)
        print(f"Graph: {self.graph_json_file} loaded")

        for node in graph_data['nodes']:
            self.graph.add_node(node['id'], role=node['type'])

        for edge in graph_data['edges']:
            self.graph.add_edge(edge['source'], edge['target'])

    def create_graph(self):
        """Generate and save an undirected graph visualization as graph.html."""
        pos = nx.spring_layout(self.graph)
        self._generate_plot(pos, "graph.html", directed=False)

    def create_directed_graph(self):
        """Generate and save a directed graph visualization as directed_graph.html."""
        pos = nx.spring_layout(self.graph)
        self._generate_plot(pos, "directed_graph.html", directed=True)

    def _generate_plot(self, pos, output_file_name, directed):
        node_x = [pos[node][0] for node in self.graph.nodes()]
        node_y = [pos[node][1] for node in self.graph.nodes()]
        node_labels = list(self.graph.nodes())
        node_roles = [self.graph.nodes[node]['role'] for node in self.graph.nodes()]

        edge_x = []
        edge_y = []
        for edge in self.graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        role_colors = {'node': 'green', 'topic': 'blue'}
        node_colors = [role_colors.get(role, 'red') for role in node_roles]

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.1, color="#888"),
            hoverinfo="none",
            mode="lines"
        )

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode="markers+text",
            text=node_labels,
            textposition="top center",
            marker=dict(
                size=25,
                color=node_colors,
                line_width=2
            )
        )

        annotations = []
        if directed:
            for edge in self.graph.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]

                dx, dy = x1 - x0, y1 - y0
                norm = np.sqrt(dx**2 + dy**2)
                scale = 0.1
                x0_edge = x0 + dx / norm * scale
                y0_edge = y0 + dy / norm * scale
                x1_edge = x1 - dx / norm * scale
                y1_edge = y1 - dy / norm * scale

                annotations.append(
                    dict(
                        ax=x0_edge,
                        ay=y0_edge,
                        x=x1_edge,
                        y=y1_edge,
                        xref="x",
                        yref="y",
                        axref="x",
                        ayref="y",
                        showarrow=True,
                        arrowhead=3,
                        arrowsize=4,
                        arrowwidth=0.5,
                        arrowcolor="#888",
                    )
                )

        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title="Directed Network Graph" if directed else "Network Graph",
                titlefont_size=16,
                showlegend=False,
                hovermode="closest",
                margin=dict(b=0, l=0, r=0, t=0),
                annotations=annotations,
                xaxis=dict(showgrid=False, zeroline=False),
                yaxis=dict(showgrid=False, zeroline=False),
            )
        )

        output_path = os.path.join(OUTPUT_DIRECTORY, output_file_name)
        fig.write_html(output_path)
        print(f"Graph saved as {output_path}")

    def generate_dot_graph(self):
        """
        Generate a Graphviz DOT representation of the graph, save it as a .dot file,
        and convert it to a .png file.
        """
        dot_file_path = os.path.join(OUTPUT_DIRECTORY, "graph.dot")
        png_file_path = os.path.join(OUTPUT_DIRECTORY, "graph.png")

        print(f"Generating DOT graph at: {dot_file_path}")

        dot = graphviz.Digraph(format="png")
        for node in self.graph.nodes():
            dot.node(node, label=node)

        for edge in self.graph.edges():
            dot.edge(edge[0], edge[1])

        with open(dot_file_path, "w") as file:
            file.write(dot.source)

        dot.render(dot_file_path, cleanup=False)
        print(f"DOT graph converted to PNG and saved as {png_file_path}")


if __name__ == "__main__":
    GRAPH_JSON_FILE = os.path.join(OUTPUT_DIRECTORY, "graph.json")

    grapher = ROS2NodeGrapher(GRAPH_JSON_FILE)
    grapher.create_graph()
    grapher.create_directed_graph()
    grapher.generate_dot_graph()

