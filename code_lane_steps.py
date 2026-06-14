"""
CODE LANE — Step-by-step sklearn analysis
==========================================
Reads mined_code_yours.parquet (already built)
Each step = its own Pydantic schema + its own sklearn pass
"""
import sys, os, json
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.metrics import silhouette_score

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

# ═══════════════════════════════════════════════════════════════════════
# PYDANTIC SCHEMAS — one per analysis step
# ═══════════════════════════════════════════════════════════════════════

class CodeCluster(BaseModel):
    """One semantic cluster of code blocks."""
    cluster_id: int
    size: int
    top_keywords: List[str]
    top_symbols: List[str]
    dominant_type: str  # function or class
    avg_char_len: float
    sample_files: List[str]

class StructuralProfile(BaseModel):
    """Structural complexity profile for a code block."""
    symbol_name: str
    source_file: str
    char_len: int
    branches: int
    depth: int
    calls: int
    anomaly: bool
    anomaly_score: float

class CodeRoleResult(BaseModel):
    """RandomForest classification of a code block's role."""
    role: str
    count: int
    avg_size: float
    top_symbols: List[str]

class OptimalKResult(BaseModel):
    """Result of silhouette analysis for finding best K."""
    k: int
    silhouette_score: float

class CodeLaneReport(BaseModel):
    """Full Code Lane analysis report."""
    total_blocks: int
    total_files: int
    optimal_k: int
    clusters: List[CodeCluster]
    structural_anomalies: List[StructuralProfile]
    role_breakdown: List[CodeRoleResult]
    silhouette_scores: List[OptimalKResult]

# ═══════════════════════════════════════════════════════════════════════
# LOAD
# ═══════════════════════════════════════════════════════════════════════
PARQUET = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/lakehouse_data/mined_code_yours.parquet"
df = pd.read_parquet(PARQUET)
print(f"Loaded: {len(df)} code blocks from {df['relative_path'].nunique()} files\n")

# ═══════════════════════════════════════════════════════════════════════
# STEP 1: Find optimal K with silhouette scores
# ═══════════════════════════════════════════════════════════════════════
print("STEP 1: Finding optimal K")
print("=" * 60)

df['combined'] = df['symbol_name'] + ' ' + df['docstring'].fillna('') + ' ' + df['code_content']
tfidf = TfidfVectorizer(max_features=2000)  # no stop_words filter — code is not english
tfidf_matrix = tfidf.fit_transform(df['combined'])

sil_results = []
for k in range(3, 20):
    km = KMeans(n_clusters=k, random_state=42, n_init='auto', max_iter=100)
    labels = km.fit_predict(tfidf_matrix)
    score = silhouette_score(tfidf_matrix, labels, sample_size=min(2000, len(df)))
    sil_results.append(OptimalKResult(k=k, silhouette_score=round(score, 4)))
    print(f"  K={k:>2}  silhouette={score:.4f}")

best = max(sil_results, key=lambda x: x.silhouette_score)
print(f"\n  Best K = {best.k} (silhouette = {best.silhouette_score})")

# ═══════════════════════════════════════════════════════════════════════
# STEP 2: Cluster with optimal K
# ═══════════════════════════════════════════════════════════════════════
print(f"\nSTEP 2: KMeans clustering (K={best.k})")
print("=" * 60)

km_final = KMeans(n_clusters=best.k, random_state=42, n_init='auto')
df['cluster'] = km_final.fit_predict(tfidf_matrix)

terms = tfidf.get_feature_names_out()
centroids = km_final.cluster_centers_.argsort()[:, ::-1]

clusters = []
for i in range(best.k):
    grp = df[df['cluster'] == i]
    top_kw = [terms[j] for j in centroids[i, :6]]
    top_sym = grp.nlargest(3, 'char_len')['symbol_name'].tolist()
    dom_type = grp['type'].mode().iloc[0] if len(grp) > 0 else 'unknown'
    sample_files = [os.path.basename(f) for f in grp['relative_path'].unique()[:3]]
    
    c = CodeCluster(
        cluster_id=i, size=len(grp), top_keywords=top_kw,
        top_symbols=top_sym, dominant_type=dom_type,
        avg_char_len=round(grp['char_len'].mean(), 1), sample_files=sample_files
    )
    clusters.append(c)
    print(f"  Cluster {i:>2} ({c.size:>4} blocks) [{c.dominant_type}]")
    print(f"    Keywords: {', '.join(c.top_keywords)}")
    print(f"    Biggest:  {', '.join(c.top_symbols)}")
    print(f"    Files:    {', '.join(c.sample_files)}")
    print()

# ═══════════════════════════════════════════════════════════════════════
# STEP 3: Structural analysis — IsolationForest anomalies
# ═══════════════════════════════════════════════════════════════════════
print("STEP 3: Structural anomaly detection (IsolationForest)")
print("=" * 60)

STRUCT = ['char_len', 'lines_of_code', 'num_branches', 'num_returns', 'max_depth', 'num_calls']
X_struct = df[STRUCT].fillna(0)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_struct)

iso = IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
iso.fit(X_scaled)
df['iso_score'] = iso.decision_function(X_scaled)
df['anomaly'] = iso.predict(X_scaled) == -1

anomalies = []
for _, r in df[df['anomaly']].nlargest(15, 'char_len').iterrows():
    a = StructuralProfile(
        symbol_name=r['symbol_name'], source_file=os.path.basename(r['source_file']),
        char_len=r['char_len'], branches=r['num_branches'],
        depth=r['max_depth'], calls=r['num_calls'],
        anomaly=True, anomaly_score=round(r['iso_score'], 4)
    )
    anomalies.append(a)
    print(f"  [{a.char_len:>7} chars] {a.symbol_name} | branches={a.branches} depth={a.depth} calls={a.calls}")
    print(f"               {a.source_file} (score={a.anomaly_score})")

print(f"\n  Total anomalies: {df['anomaly'].sum()} / {len(df)}")

# ═══════════════════════════════════════════════════════════════════════
# STEP 4: RandomForest — let the MODEL find the roles, not keywords
# ═══════════════════════════════════════════════════════════════════════
print(f"\nSTEP 4: RandomForest role classification")
print("=" * 60)

# Use cluster as the target — RF learns what structural features define each cluster
rf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
rf.fit(X_scaled, df['cluster'])

print("  Feature importances (what defines cluster membership):")
for feat, imp in sorted(zip(STRUCT, rf.feature_importances_), key=lambda x: -x[1]):
    bar = '#' * int(imp * 100)
    print(f"    {feat:<16} {imp*100:>5.1f}%  {bar}")

# Per-cluster structural profile
print(f"\n  Cluster structural profiles:")
print(f"  {'Cluster':>8} {'Size':>5} {'AvgLen':>8} {'AvgBranch':>10} {'AvgDepth':>9} {'AvgCalls':>9}")
print(f"  {'-'*55}")
role_results = []
for i in range(best.k):
    grp = df[df['cluster'] == i]
    top_sym = grp.nlargest(3, 'char_len')['symbol_name'].tolist()
    role_results.append(CodeRoleResult(
        role=f"cluster_{i}", count=len(grp),
        avg_size=round(grp['char_len'].mean(), 1), top_symbols=top_sym
    ))
    print(f"  {i:>8} {len(grp):>5} {grp['char_len'].mean():>8.0f} "
          f"{grp['num_branches'].mean():>10.1f} {grp['max_depth'].mean():>9.1f} "
          f"{grp['num_calls'].mean():>9.1f}")

# ═══════════════════════════════════════════════════════════════════════
# STEP 5: Assemble full report as Pydantic
# ═══════════════════════════════════════════════════════════════════════
print(f"\nSTEP 5: Pydantic Report Assembly")
print("=" * 60)

report = CodeLaneReport(
    total_blocks=len(df),
    total_files=df['relative_path'].nunique(),
    optimal_k=best.k,
    clusters=clusters,
    structural_anomalies=anomalies,
    role_breakdown=role_results,
    silhouette_scores=sil_results
)

# Save as JSON
report_path = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/lakehouse_data/code_lane_report.json"
with open(report_path, 'w', encoding='utf-8') as f:
    f.write(report.model_dump_json(indent=2))

print(f"  Report saved: {report_path}")
print(f"  {report.total_blocks} blocks | {report.total_files} files | K={report.optimal_k}")
print(f"  {len(report.structural_anomalies)} anomalies | {len(report.clusters)} clusters")
print(f"\nDone.")
