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
BACKUP_DIR = r"E:/"
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

# Scan Backup Workspace (Entire E: Drive with custom filters)
if os.path.exists(BACKUP_DIR):
    ignored_dirs = {
        'system volume information', '$recycle.bin', '.git', '.venv', 'node_modules', 
        'venv', 'env', '__pycache__', '.ipynb_checkpoints', '.cache', 'program files', 
        'programs', 'adobe', '.fseventsd', '.spotlight-v100', '.trashes', '.temporaryitems',
        'python2', 'python3', 'lib', 'include', 'tcl', 'libs'
    }
    for root, dirs, files in os.walk(BACKUP_DIR):
        # Filter out directories in-place to speed up walking
        dirs[:] = [d for d in dirs if d.lower() not in ignored_dirs and not d.startswith('.')]
        
        # Avoid scanning inside Ableton's Python packages or resources
        if 'resources\\\\python2' in root.lower() or 'core library' in root.lower():
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
"""),

# ── CELL 10: E DRIVE METADATA SUMMARY ──────────────────────────
md("""## 🎛️ CELL 10 — E: Drive 900GB Metadata & Vibe Index Analysis
We have integrated your massive **900GB E: Drive audio metadata library** which has been location-mapped, drum-type categorized, and vibe-vectored:
- **Total Rows**: 2,010 distinct tracks and samples (represented as 174,432 lines in `audio_vibe_gpu.csv` due to embedded vector newlines).
- **Locations**: Direct mappings to E: Drive (`E:\\music\\HOUSE\\...` and `E:\\OLD ABLETON\\ABELTON-000\\...`).
- **Target Subsets**: Categorized as `SAMPLE` (1,339) vs `SONG` (671), with detailed drum type breakdowns (`FULL_TRACK`, `SNARE`, `TOM`, `KICK`, `BASS`).
"""),

# ── CELL 11: E DRIVE QUERY ENGINE ─────────────────────────────
code("""# Query E Drive Audio Vibe CSV using DuckDB
import pandas as pd
import duckdb

csv_path = r"c:\\STUDIES_BACKUP\\Legion-Jacked-Pipeline\\data\\audio_vibe_gpu.csv"
if os.path.exists(csv_path):
    print("Connecting to audio_vibe_gpu using DuckDB...")
    # Read the CSV file into a temporary view
    vibe_df = pd.read_csv(csv_path)
    conn.execute("CREATE OR REPLACE TEMPORARY VIEW audio_vibe AS SELECT * FROM vibe_df")
    
    # Run a quick analytic query
    print("\\nTotal Records Mapped from E Drive:")
    print(conn.execute("SELECT COUNT(*) as total_records, source_type FROM audio_vibe GROUP BY source_type").fetchall())
    
    print("\\nTop 5 Folders with Most Assets on E Drive:")
    print(conn.execute("SELECT folder, COUNT(*) as count FROM audio_vibe GROUP BY folder ORDER BY count DESC LIMIT 5").fetchall())
else:
    print("audio_vibe_gpu.csv not found.")
"""),

# ── CELL 12: AUTONOMOUS SKLEARN ANALYSIS ──────────────────────
md("""## 🧠 CELL 12 — Autonomous Scikit-Learn Code Clustering & Taxonomy
Here we execute an unsupervised semantic analysis across the 2,586 decomposed Python code blocks to find patterns in your development architecture (e.g., separating database helpers, agent logic, DSP, and utility functions).
"""),
code("""t_start = time.perf_counter()
# Query the complete code lakehouse
code_df = conn.execute("SELECT symbol_name, type, docstring, code_content FROM mined_code").fetchdf()

# Handle NaNs and fill empty strings
code_df = code_df.fillna("")
code_df['combined_features'] = code_df['symbol_name'] + " " + code_df['docstring'] + " " + code_df['code_content']

print(f"Loaded {len(code_df)} code blocks for sklearn clustering.")

# TF-IDF Vectorization
tfidf = TfidfVectorizer(max_features=2500, stop_words='english')
tfidf_matrix = tfidf.fit_transform(code_df['combined_features'])

# Auto-selection of K using a simple heuristic (e.g., logarithmic scaling of data size, clamped to [5, 12])
num_docs = len(code_df)
auto_k = int(np.clip(np.log2(num_docs) * 1.5, 5, 12))
print(f"Autonomously selected K={auto_k} clusters based on document count.")

# K-Means
kmeans = KMeans(n_clusters=auto_k, random_state=42)
code_df['cluster'] = kmeans.fit_predict(tfidf_matrix)

# Show Top 5 symbols per cluster
terms = tfidf.get_feature_names_out()
order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]

print("\\n=== AUTONOMOUS CODE TAXONOMY ===")
for i in range(auto_k):
    cluster_symbols = code_df[code_df['cluster'] == i]['symbol_name'].values
    top_terms = [terms[ind] for ind in order_centroids[i, :5]]
    print(f"\\n📦 Cluster {i} (Count: {len(cluster_symbols)})")
    print(f"   ➤ Signature keywords: {', '.join(top_terms)}")
    print(f"   ➤ Representative symbols: {list(cluster_symbols[:5])}")

print(f"\\nUnsupervised clustering completed in {time.perf_counter() - t_start:.2f} seconds.")
"""),

# ── CELL 13: PYTORCH GENERATION WEIGHTS ────────────────────────
md("""## 🎛️ CELL 13 — Lane 2: PyTorch Neural Parameter Synthesis
This cell sets up a PyTorch pipeline to map 384-dimension audio vibe vectors or DSP metrics (RMS, Crest Factor, Sub-bass energy) to "generation weights" and mastering parameter targets.
"""),
code("""import torch
import torch.nn as nn
import torch.optim as optim

print(f"PyTorch version: {torch.__version__}")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Targeting device: {device}")

# Define a Parameter Synthesis Network
class AudioGenerationWeightNet(nn.Module):
    def __init__(self, input_dim=384, hidden_dim=128, output_dim=8):
        super(AudioGenerationWeightNet, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, output_dim),
            nn.Sigmoid() # Scale outputs between 0 and 1 (generation/compression ratios)
        )
        
    def forward(self, x):
        return self.network(x)

# Initialize model
model = AudioGenerationWeightNet(input_dim=384, hidden_dim=128, output_dim=8).to(device)
print(model)

# Demonstrate forward pass using one of your actual E-Drive vibe vectors
csv_path = r"c:\\STUDIES_BACKUP\\Legion-Jacked-Pipeline\\data\\audio_vibe_gpu.csv"
if os.path.exists(csv_path):
    # Load raw vibe data
    vibe_data = pd.read_csv(csv_path, nrows=5)
    
    # Parse the first vector string back to float array
    first_vec_str = vibe_data.iloc[0]['vector']
    # clean up string representation of numpy array
    clean_vec = [float(x) for x in first_vec_str.replace('[', '').replace(']', '').replace('\\n', ' ').split() if x]
    
    if len(clean_vec) == 384:
        input_tensor = torch.tensor([clean_vec], dtype=torch.float32).to(device)
        with torch.no_grad():
            output_weights = model(input_tensor)
        
        print("\\n--- Synthesis Test Run on E-Drive Vibe Vector ---")
        print(f"Input file: {vibe_data.iloc[0]['filename']}")
        print(f"Generated Weights Output Shape: {output_weights.shape}")
        print(f"Target Parameters (normalized scaling):\\n {output_weights.cpu().numpy()[0]}")
    else:
        print(f"Vector dimension mismatch: got {len(clean_vec)}, expected 384.")
else:
    print("audio_vibe_gpu.csv not found for test forward pass.")
""")
        
# ── CELL 14: DSP METHOD COMPARISON ────────────────────────────
,
# ── CELL 14: DSP METHOD COMPARISON ────────────────────────────
md("""## 🔬 CELL 14 — DSP Comparison: Frequency Domain (STFT) vs. Time Domain (SciPy SOS Filter)
This cell compares the calculations and execution speeds of the two primary audio analysis methods on a real E-Drive track.
"""),
code("""# DSP Comparison
import librosa
from scipy.signal import butter, sosfilt

# Load the first track from E-Drive
csv_path = r"c:\\STUDIES_BACKUP\\Legion-Jacked-Pipeline\\data\\audio_vibe_gpu.csv"
if os.path.exists(csv_path):
    vibe_data = pd.read_csv(csv_path, nrows=1)
    filepath = vibe_data.iloc[0]['filepath']
    
    if os.path.exists(filepath):
        print(f"Loading test file: {os.path.basename(filepath)}")
        y, sr = librosa.load(filepath, sr=22050, duration=60)
        
        # 1. Method 1: STFT
        t_start = time.perf_counter()
        stft = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
        freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
        power_spectrum = np.sum(stft**2, axis=1)

        sub_bass_mask = (freqs >= 20) & (freqs < 60)
        bass_mask = (freqs >= 60) & (freqs < 250)
        mid_mask = (freqs >= 250) & (freqs < 2000)
        high_mask = (freqs >= 2000) & (freqs < 20000)

        sub_bass_e1 = float(np.sum(power_spectrum[sub_bass_mask]))
        bass_e1 = float(np.sum(power_spectrum[bass_mask]))
        mid_e1 = float(np.sum(power_spectrum[mid_mask]))
        high_e1 = float(np.sum(power_spectrum[high_mask]))

        total_stft = sub_bass_e1 + bass_e1 + mid_e1 + high_e1
        m1_ratios = [sub_bass_e1/total_stft, bass_e1/total_stft, mid_e1/total_stft, high_e1/total_stft]
        t_stft = time.perf_counter() - t_start
        
        # 2. Method 2: SciPy SOS Bandpass
        t_start = time.perf_counter()
        def filter_band(data, low, high, fs):
            nyq = 0.5 * fs
            sos = butter(4, [low/nyq, high/nyq], btype='band', output='sos')
            return sosfilt(sos, data)
            
        sub_bass_sig = filter_band(y, 20, 60, sr)
        bass_sig = filter_band(y, 60, 250, sr)
        mid_sig = filter_band(y, 250, 2000, sr)
        high_sig = filter_band(y, 2000, 10000, sr)
        
        sub_bass_e2 = np.mean(sub_bass_sig**2)
        bass_e2 = np.mean(bass_sig**2)
        mid_e2 = np.mean(mid_sig**2)
        high_e2 = np.mean(high_sig**2)
        
        total_scipy = sub_bass_e2 + bass_e2 + mid_e2 + high_e2
        m2_ratios = [sub_bass_e2/total_scipy, bass_e2/total_scipy, mid_e2/total_scipy, high_e2/total_scipy]
        t_scipy = time.perf_counter() - t_start
        
        # Comparison Table
        bands = ["Sub-Bass (20-60Hz)", "Bass (60-250Hz)", "Mids (250-2kHz)", "Highs (2k-10kHz)"]
        print("\\n=== DSP METHOD COMPARISON SUMMARY ===")
        print(f"{'Band':<20} | {'Method 1 (STFT)':<18} | {'Method 2 (SciPy)':<18} | {'Difference':<10}")
        print("-" * 75)
        for idx, band in enumerate(bands):
            diff = abs(m1_ratios[idx] - m2_ratios[idx])
            print(f"{band:<20} | {m1_ratios[idx]:<18.4%} | {m2_ratios[idx]:<18.4%} | {diff:<10.4%}")
            
        print(f"\\nSTFT Duration : {t_stft:.6f}s")
        print(f"SciPy Duration: {t_scipy:.6f}s")
        print(f"Variance check passes (all < 0.5% difference): {all(abs(m1 - m2) < 0.005 for m1, m2 in zip(m1_ratios, m2_ratios))}")
    else:
        print(f"File not found: {filepath}")
else:
    print("audio_vibe_gpu.csv not found.")
""")
]

nb["cells"] = cells

with open("code_mining_pipeline.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

print("Notebook generated: code_mining_pipeline.ipynb")
