import json

nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.13.0"}
    },
    "cells": []
}

def md(source):
    return {"cell_type": "markdown", "id": f"md_{abs(hash(source[:30]))}", "metadata": {}, "source": source.splitlines(True)}

def code(source):
    return {"cell_type": "code", "id": f"code_{abs(hash(source[:30]))}", "execution_count": None, "metadata": {}, "outputs": [], "source": source.splitlines(True)}

cells = [
# ── HEADER ────────────────────────────────────────────────────
md("""# 🧬 Dual-Lane Code & Music Mining Lakehouse
**Legion-Jacked-Pipeline | Sovereign Edge Asset Miner**

This notebook implements a high-performance local indexing lakehouse that crawls, parses, structures, and clusters your codebase history alongside audio catalog databases.

| Lane | Assets | Technology |
|------|--------|------------|
| **Lane 1: Code** | Python AST blocks, classes, functions, docstrings | PyArrow, DuckDB, TF-IDF, K-Means |
| **Lane 2: Music** | Stem analyses, track properties, catalog JSONs | PyArrow, DuckDB, LanceDB |
"""),

# ── CELL 1: IMPORTS ───────────────────────────────────────────
md("## ⚙️ CELL 1 — Imports & Path Configurations"),
code("""import os, sys, json, time, warnings
import ast
import pyarrow as pa
import pyarrow.parquet as pq
import duckdb
import lancedb
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from dotenv import load_dotenv
from datetime import datetime

warnings.filterwarnings("ignore")

# Define target paths
BACKUP_DIR = r"E:/APP/antigravity_v2_full_backup/home/adamscarmccoy/antigravity-dna-v2/dna_analysis/ANTI-GRAVITY-SWARM-V2.0"
LOCAL_DIR  = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence"
EXPORT_DIR = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/exported_json"

LAKEHOUSE_DIR = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/lakehouse_data"
LANCEDB_DIR   = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/lancedb_web_intel_rag"

os.makedirs(LAKEHOUSE_DIR, exist_ok=True)

print("Imports complete.")
print(f"Local target directory: {LOCAL_DIR}")
print(f"Backup target directory: {BACKUP_DIR}")
print(f"JSON export directory: {EXPORT_DIR}")
"""),

# ── CELL 2: DUAL-LANE FILE SCANNER ────────────────────────────
md("## 📂 CELL 2 — Dual-Lane File Classifier"),
code("""t_start = time.perf_counter()

code_files = []
music_files = []

# Scan Local Workspace
for root, dirs, files in os.walk(LOCAL_DIR):
    if ".git" in root or ".venv" in root or "__pycache__" in root:
        continue
    for file in files:
        full_path = os.path.join(root, file).replace('\\\\', '/')
        if file.endswith('.py') or file.endswith('.ipynb'):
            code_files.append(full_path)

# Scan Backup Workspace (with fallback if disconnected)
if os.path.exists(BACKUP_DIR):
    for root, dirs, files in os.walk(BACKUP_DIR):
        if ".git" in root or "__pycache__" in root:
            continue
        for file in files:
            full_path = os.path.join(root, file).replace('\\\\', '/')
            if file.endswith('.py') or file.endswith('.ipynb'):
                code_files.append(full_path)
else:
    print(f"⚠️ Warning: Backup directory {BACKUP_DIR} not found. Operating on local workspace only.")

# Scan Exported JSON Folder (Music Lane)
if os.path.exists(EXPORT_DIR):
    for file in os.listdir(EXPORT_DIR):
        if file.endswith('.json'):
            music_files.append(os.path.join(EXPORT_DIR, file).replace('\\\\', '/'))

print(f"Scanned files in {time.perf_counter() - t_start:.4f} seconds:")
print(f"   ➤ Code Lane Files  : {len(code_files)}")
print(f"   ➤ Music Lane Files : {len(music_files)}")
"""),

# ── CELL 3: AST CODE PARSER ───────────────────────────────────
md("## 🐍 CELL 3 — Lane 1: AST Code Decomposition"),
code("""t_start = time.perf_counter()
parsed_code_blocks = []

for file_path in code_files:
    if file_path.endswith('.py'):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            tree = ast.parse(content, filename=file_path)
            
            # Extract functions
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    docstring = ast.get_docstring(node) or ""
                    code_lines = len(node.body)
                    parsed_code_blocks.append({
                        "symbol_name": node.name,
                        "type": "function",
                        "source_file": file_path,
                        "docstring": docstring,
                        "code_content": ast.unparse(node),
                        "lines_of_code": code_lines
                    })
                elif isinstance(node, ast.ClassDef):
                    docstring = ast.get_docstring(node) or ""
                    parsed_code_blocks.append({
                        "symbol_name": node.name,
                        "type": "class",
                        "source_file": file_path,
                        "docstring": docstring,
                        "code_content": ast.unparse(node),
                        "lines_of_code": len(node.body)
                    })
        except Exception as e:
            pass # Skip malformed python files

print(f"Decomposed {len(code_files)} python files into {len(parsed_code_blocks)} class/function blocks.")
print(f"AST Parsing completed in {time.perf_counter() - t_start:.4f} seconds.")
"""),

# ── CELL 4: MUSIC METADATA PARSER ─────────────────────────────
md("## 🎼 CELL 4 — Lane 2: Music Catalog Parser"),
code("""t_start = time.perf_counter()
parsed_music_blocks = []

for file_path in music_files:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        file_name = os.path.basename(file_path)
        
        if isinstance(data, list):
            for idx, item in enumerate(data):
                parsed_music_blocks.append({
                    "source_file": file_name,
                    "row_index": idx,
                    "title": item.get("filename", item.get("release_title", item.get("track_name", "Unknown"))),
                    "bpm": item.get("bpm", item.get("tempo", None)),
                    "key_signature": item.get("key_signature", item.get("key", None)),
                    "rms_db": item.get("rms_db", item.get("dsp_rms", None)),
                    "crest_factor": item.get("crest_factor", item.get("dsp_crest", None)),
                    "raw_json": json.dumps(item)
                })
        elif isinstance(data, dict):
            for k, v in data.items():
                parsed_music_blocks.append({
                    "source_file": file_name,
                    "row_index": 0,
                    "title": k,
                    "bpm": None,
                    "key_signature": None,
                    "rms_db": None,
                    "crest_factor": None,
                    "raw_json": json.dumps(v)
                })
    except Exception as e:
        print(f"Skipped parsing {file_path}: {e}")

print(f"Loaded {len(parsed_music_blocks)} music/metadata rows in {time.perf_counter() - t_start:.4f} seconds.")
"""),

# ── CELL 5: PYARROW LAKEHOUSE SERIALIZATION ────────────────────
md("## ⚡ CELL 5 — PyArrow & Parquet Storage Layer"),
code("""t_start = time.perf_counter()

# 1. Serialize Code Blocks
code_table = pa.Table.from_pylist(parsed_code_blocks)
code_parquet_path = os.path.join(LAKEHOUSE_DIR, "mined_code.parquet")
pq.write_table(code_table, code_parquet_path)

# 2. Serialize Music Blocks
music_table = pa.Table.from_pylist(parsed_music_blocks)
music_parquet_path = os.path.join(LAKEHOUSE_DIR, "mined_music.parquet")
pq.write_table(music_table, music_parquet_path)

print(f"Lakehouse Parquet files saved in {time.perf_counter() - t_start:.4f} seconds:")
print(f"   ➤ mined_code.parquet  : {len(code_table)} rows")
print(f"   ➤ mined_music.parquet : {len(music_table)} rows")
"""),

# ── CELL 6: DUCKDB SCHEMA LOAD ────────────────────────────────
md("## 🗄️ CELL 6 — DuckDB Relational Lakehouse Load"),
code("""conn = duckdb.connect(database=":memory:")

# Read Parquet direct projections
conn.execute(f"CREATE TABLE mined_code AS SELECT * FROM read_parquet('{code_parquet_path}')")
conn.execute(f"CREATE TABLE mined_music AS SELECT * FROM read_parquet('{music_parquet_path}')")

print("DuckDB Tables Loaded:")
print(conn.execute("show tables").fetchall())

# Fetch quick summaries
print("\\nDuckDB Mined Code Summary:")
print(conn.execute("SELECT type, COUNT(*), SUM(lines_of_code) as total_loc FROM mined_code GROUP BY type").fetchall())

print("\\nDuckDB Mined Music Summary:")
print(conn.execute("SELECT source_file, COUNT(*) FROM mined_music GROUP BY source_file LIMIT 10").fetchall())
"""),

# ── CELL 7: LANCEDB VECTOR INGESTION ──────────────────────────
md("## 🤖 CELL 7 — LanceDB Vector Store Ingestion"),
code("""db = lancedb.connect(LANCEDB_DIR)

# Drop tables if exist
if "mined_code_vectors" in db.table_names():
    db.drop_table("mined_code_vectors")
if "mined_music_vectors" in db.table_names():
    db.drop_table("mined_music_vectors")

# 1. Setup schemas for code vectors
code_schema = pa.schema([
    pa.field("symbol_name", pa.string()),
    pa.field("type",        pa.string()),
    pa.field("source_file", pa.string()),
    pa.field("docstring",   pa.string()),
    pa.field("code_content",pa.string()),
    pa.field("vector",      pa.list_(pa.float32(), 1024))
])

# For fast local indexing without LLM timeout, we populate empty/placeholder vectors
code_df = code_table.to_pandas()
code_df['vector'] = [ [0.0]*1024 for _ in range(len(code_df)) ]
code_table_db = db.create_table("mined_code_vectors", data=code_df[['symbol_name', 'type', 'source_file', 'docstring', 'code_content', 'vector']], schema=code_schema)

print(f"LanceDB tables initialized:")
print(f"   ➤ mined_code_vectors: {code_table_db.count_rows()} rows indexed")
"""),

# ── CELL 8: SCIKIT-LEARN CLUSTERING ───────────────────────────
md("## 🧠 CELL 8 — Scikit-Learn Clustering Engine (TF-IDF + K-Means)"),
code("""t_start = time.perf_counter()

# Extract code docstrings/content
code_data = code_table.to_pandas()
code_data['text_feature'] = code_data['symbol_name'] + " " + code_data['docstring'] + " " + code_data['type']

# TF-IDF Vectorizer
vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
tfidf_matrix = vectorizer.fit_transform(code_data['text_feature'])

# K-Means Clustering (K=8 groups of functionality)
n_clusters = min(8, len(code_data))
kmeans = KMeans(n_clusters=n_clusters, random_state=42)
code_data['cluster'] = kmeans.fit_predict(tfidf_matrix)

print(f"K-Means Clustering of {len(code_data)} code blocks into {n_clusters} clusters completed in {time.perf_counter() - t_start:.4f} seconds.")

# Print top keywords per cluster
order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
terms = vectorizer.get_feature_names_out()

print("\\nCluster Center Semantic Taxonomy:")
for i in range(n_clusters):
    top_terms = [terms[ind] for ind in order_centroids[i, :6]]
    print(f"  Cluster {i}: Keywords: {', '.join(top_terms)}")
"""),

# ── CELL 9: EXPORT MINED KNOWLEDGE BRIEF ──────────────────────
md("## 📝 CELL 9 — Exporter: Mined Knowledge Brief Case Study"),
code("""t_start = time.perf_counter()

# Add cluster labels to our original dataframe
code_data['cluster_label'] = code_data['cluster'].map(lambda c: f"Cluster {c}")

# Select representative code snippets from each cluster
brief_content = []
brief_content.append("# 🧬 Legion-Jacked-Pipeline: Mined Code & Music Knowledge Brief\\n")
brief_content.append(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
brief_content.append(f"Total Files Crawled: {len(code_files) + len(music_files)}")
brief_content.append(f"Total Code Blocks Decomposed: {len(parsed_code_blocks)}")
brief_content.append(f"Total Music Rows Cataloged: {len(parsed_music_blocks)}\\n")

brief_content.append("## 📂 Clustered Knowledge Index\\n")
for c in range(n_clusters):
    cluster_subset = code_data[code_data['cluster'] == c]
    brief_content.append(f"### 📦 Cluster {c} (Found {len(cluster_subset)} items)")
    # Sample items
    for idx, row in cluster_subset.head(3).iterrows():
        brief_content.append(f"- **{row['symbol_name']}** ({row['type']}) | File: `{row['source_file']}`")
    brief_content.append("")

out_brief_path = "c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/exported_json/mined_knowledge_brief.md"
with open(out_brief_path, 'w', encoding='utf-8') as f:
    f.write('\\n'.join(brief_content))

print(f"Mined Knowledge Brief Case Study written successfully to: {out_brief_path}")
print(f"Exporter finished in {time.perf_counter() - t_start:.4f} seconds.")
""")
]

nb["cells"] = cells

with open("code_mining_pipeline.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

print("Notebook generated: code_mining_pipeline.ipynb")
