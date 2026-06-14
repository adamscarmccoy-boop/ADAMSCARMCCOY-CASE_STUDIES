import pandas as pd
import networkx as nx
from pyvis.network import Network
import os

OUT_DIR = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence"
PARQUET_IMPORTS = os.path.join(OUT_DIR, "lakehouse_data/code_imports_yours.parquet")
PARQUET_BLOCKS = os.path.join(OUT_DIR, "lakehouse_data/mined_code_yours.parquet")

print("Loading data...")
edges_df = pd.read_parquet(PARQUET_IMPORTS)
blocks_df = pd.read_parquet(PARQUET_BLOCKS)

# Identify node roles based on the code blocks they contain
node_roles = {}
for file_path, group in blocks_df.groupby('relative_path'):
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    
    # If the file has schemas, mark it as Schema layer
    if (group['code_role'] == 'schema').any():
        node_roles[module_name] = 'Schema (Pydantic)'
    elif (group['code_role'] == 'engine').any():
        node_roles[module_name] = 'Core Engine'
    elif (group['code_role'] == 'ingestion').any():
        node_roles[module_name] = 'Data Ingestion'
    else:
        node_roles[module_name] = 'Utility'

# Filter out MCP and APIs as requested
EXCLUDE = ['mcp', 'api', 'server', 'cli', 'app', 'test_']

def should_exclude(name):
    name_lower = name.lower()
    return any(ex in name_lower for ex in EXCLUDE)

filtered_edges = []
nodes_set = set()

for _, row in edges_df.iterrows():
    source = os.path.splitext(os.path.basename(row['source']))[0]
    target = row['imports']
    
    if should_exclude(source) or should_exclude(target):
        continue
        
    # Only keep internal imports (where we have data)
    if target in node_roles or source in node_roles:
        filtered_edges.append((source, target))
        nodes_set.add(source)
        nodes_set.add(target)

print(f"Filtered down to {len(nodes_set)} core nodes and {len(filtered_edges)} connections.")

# Build NetworkX graph
G = nx.DiGraph()
for src, tgt in filtered_edges:
    G.add_edge(src, tgt)

# Calculate centrality for sizing
centrality = nx.degree_centrality(G)

# Colors for roles
COLORS = {
    'Schema (Pydantic)': '#ff3cac', # Hot pink for schemas (The Glue)
    'Core Engine': '#00f0ff',       # Cyan for engines
    'Data Ingestion': '#ffe600',    # Yellow for data
    'Utility': '#444466'            # Dim gray for the rest
}

# Build Pyvis Network
net = Network(height="1000px", width="100%", bgcolor="#0d0d14", font_color="white", directed=True)
net.force_atlas_2based(gravity=-50, central_gravity=0.01, spring_length=100, spring_strength=0.08, damping=0.4, overlap=0)

for node in G.nodes():
    role = node_roles.get(node, 'Utility')
    color = COLORS.get(role, COLORS['Utility'])
    
    # Base size + centrality boost. Schemas get a base bump so they stand out
    base_size = 20 if role == 'Schema (Pydantic)' else 10
    size = base_size + (centrality.get(node, 0) * 100)
    
    title = f"Module: {node}\nRole: {role}"
    
    net.add_node(node, label=node, title=title, color=color, size=size)

for src, tgt in G.edges():
    net.add_edge(src, tgt, color='#333344', alpha=0.5)

out_file = os.path.join(OUT_DIR, "core_spider_web.html")
net.save_graph(out_file)
print(f"Spider web interactive map saved to: {out_file}")
