"""
autonomous_search_clustering.py
================================
Reads directly from mined_code.parquet (built by code_mining_pipeline.ipynb).
Filters for the word AUTONOMOUS, then clusters with TF-IDF + auto-K KMeans.
Exact pattern from Cell 12 of the notebook. Zero file scanning.
"""
import sys
import duckdb
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

# Force UTF-8 stdout on Windows
try:
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ── Paths straight from notebook Cell 1 ───────────────────────────────────────
PARQUET_PATH = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/lakehouse_data/mined_code.parquet"

QUERY = "autonomous"

# ── 1. Load from parquet via DuckDB (same as Cell 12) ─────────────────────────
conn = duckdb.connect(database=":memory:")
conn.execute(f"CREATE TABLE mined_code AS SELECT * FROM read_parquet('{PARQUET_PATH}')")

df = conn.execute("SELECT symbol_name, type, source_file, docstring, code_content FROM mined_code").fetchdf()
df = df.fillna("")

print(f"Lakehouse loaded: {len(df)} code blocks")

# ── 2. Filter for AUTONOMOUS ───────────────────────────────────────────────────
df["combined"] = df["symbol_name"] + " " + df["docstring"] + " " + df["code_content"]
mask = df["combined"].str.contains(QUERY, case=False, na=False)
hits = df[mask].copy().reset_index(drop=True)

print(f"Matches for '{QUERY.upper()}': {len(hits)}")

if hits.empty:
    print("No matches found.")
    sys.exit(0)

# ── 3. TF-IDF vectorize (same as Cell 12) ─────────────────────────────────────
tfidf = TfidfVectorizer(max_features=2500, stop_words="english")
tfidf_matrix = tfidf.fit_transform(hits["combined"])

# ── 4. Auto-select K (same log heuristic as Cell 12) ──────────────────────────
num_docs = len(hits)
auto_k = int(np.clip(np.log2(num_docs) * 1.5, 2, 12)) if num_docs > 1 else 1
print(f"Auto-selected K={auto_k} clusters for {num_docs} documents\n")

# ── 5. KMeans ─────────────────────────────────────────────────────────────────
kmeans = KMeans(n_clusters=auto_k, random_state=42, n_init="auto")
hits["cluster"] = kmeans.fit_predict(tfidf_matrix)

terms = tfidf.get_feature_names_out()
order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]

# ── 6. Print clustered index ───────────────────────────────────────────────────
print("=== AUTONOMOUS CODE TAXONOMY ===\n")
for i in range(auto_k):
    cluster_rows = hits[hits["cluster"] == i]
    top_terms = [terms[ind] for ind in order_centroids[i, :5]]
    symbols = cluster_rows["symbol_name"].values

    print(f"Cluster {i} (Found {len(cluster_rows)} items)")
    print(f"   Keywords : {', '.join(top_terms)}")
    for _, row in cluster_rows.head(5).iterrows():
        print(f"   - {row['symbol_name']} ({row['type']}) | File: `{row['source_file']}`")
    print()
