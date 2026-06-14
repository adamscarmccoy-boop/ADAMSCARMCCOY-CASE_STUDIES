import pandas as pd
import networkx as nx
import os

OUT_DIR = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence"
PARQUET_IMPORTS = os.path.join(OUT_DIR, "lakehouse_data/code_imports_yours.parquet")
PARQUET_BLOCKS = os.path.join(OUT_DIR, "lakehouse_data/mined_code_yours.parquet")

print("Loading raw code data from Parquet...")
edges_df = pd.read_parquet(PARQUET_IMPORTS)
blocks_df = pd.read_parquet(PARQUET_BLOCKS)

G = nx.DiGraph()
for _, row in edges_df.iterrows():
    source = os.path.splitext(os.path.basename(row['source']))[0]
    target = row['imports']
    G.add_edge(source, target)

print("\n--- RUNNING RAW INTERFERENCE SEARCH ---")

# 1. Circular Dependencies (Deadlocks / Interferences)
try:
    cycles = list(nx.simple_cycles(G))
    real_cycles = [c for c in cycles if len(c) > 1] # Ignore self-loops for now
    if real_cycles:
        print(f"\n[!] WARNING: Found {len(real_cycles)} Circular Dependency Interferences:")
        for i, cycle in enumerate(real_cycles[:5]):
            print(f"  Cycle {i+1}: {' -> '.join(cycle)} -> {cycle[0]}")
        if len(real_cycles) > 5:
            print("  ...and more.")
    else:
        print("\n[+] No circular dependency interferences found. Data flow is strictly directional.")
except Exception as e:
    print("Could not calculate cycles.")

# 2. Namespace Collisions (Duplicate function/class names across different files)
# The column is 'block_name' in mined_code_yours.parquet
if 'block_name' in blocks_df.columns:
    name_counts = blocks_df['block_name'].value_counts()
    collisions = name_counts[name_counts > 1]

    collisions = collisions[~collisions.index.str.startswith('__')]

    if not collisions.empty:
        print(f"\n[!] WARNING: Found {len(collisions)} Namespace Collisions (Same name, different logic):")
        for name, count in collisions.head(5).items():
            files = blocks_df[blocks_df['block_name'] == name]['relative_path'].unique()
            print(f"  '{name}' is defined {count} times across: {', '.join([os.path.basename(f) for f in files])}")
    else:
        print("\n[+] No namespace collisions found.")

# 3. Architectural Bottlenecks (Code blocks being imported by almost everything)
in_degrees = dict(G.in_degree())
sorted_bottlenecks = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)

print(f"\n[!] Top 3 Architectural Bottlenecks (High Interference Risk if changed):")
for node, degree in sorted_bottlenecks[:3]:
    print(f"  Module '{node}' is imported by {degree} other files.")

print("\nSearch complete.")
