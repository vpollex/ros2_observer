import json
import os
import networkx as nx
import plotly.graph_objects as go

OUTPUT_DIRECTORY = os.environ['ROS_HOME'] + "/ros2_node_inspector"
GRAPH_JSON_FILE = f"{OUTPUT_DIRECTORY}/graph.json"

with open(GRAPH_JSON_FILE, 'r') as file:
    graph_data = json.load(file)
    print(f"Graph: {GRAPH_JSON_FILE} loaded")

nodes = graph_data['nodes']
edges = graph_data['edges']

G = nx.DiGraph()

for node in nodes:
    G.add_node(node['id'], role=node['type'])

for edge in edges:
    G.add_edge(edge['source'], edge['target'])

pos = nx.spring_layout(G)

node_x = [pos[node][0] for node in G.nodes()]
node_y = [pos[node][1] for node in G.nodes()]
node_labels = [node['id'] for node in nodes]
node_roles = [G.nodes[node]['role'] for node in G.nodes()]

edge_x = []
edge_y = []
for edge in G.edges():
    x0, y0 = pos[edge[0]]
    x1, y1 = pos[edge[1]]
    edge_x.extend([x0, x1, None])
    edge_y.extend([y0, y1, None])

role_colors = {
    'node': 'green',
    'topic': 'blue'
}
node_colors = [role_colors.get(role, 'red') for role in node_roles]

edge_trace = go.Scatter(
    x=edge_x, y=edge_y,
    line=dict(width=0.5, color="#888"),
    hoverinfo="none",
    mode="lines"
)

node_trace = go.Scatter(
    x=node_x, y=node_y,
    mode="markers+text",
    text=node_labels,
    textposition="top center",
    marker=dict(
        size=10,
        color=node_colors,
        line_width=2
    )
)

fig = go.Figure(
    data=[edge_trace, node_trace],
    layout=go.Layout(
        title="Network Graph",
        titlefont_size=16,
        showlegend=False,
        hovermode="closest",
        margin=dict(b=0, l=0, r=0, t=0),
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=False, zeroline=False),
    )
)

output_file = f"{OUTPUT_DIRECTORY}/graph.html"
fig.write_html(output_file)
print(f"Graph saved as {output_file}")

