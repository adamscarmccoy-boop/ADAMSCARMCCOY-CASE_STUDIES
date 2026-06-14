"""
CODE LANE ENGINE v2 — YOUR CODE ONLY
======================================
Filters out AI_Logs/pydantic, AI_Logs/instructor, site-packages
Adds: NetworkX dependency graph, UMAP galaxy map, radon complexity, scipy dendrogram
"""
import sys, os, ast, json, time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import networkx as nx
from collections import Counter, defaultdict
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.spatial.distance import pdist

try:
    import umap
    HAS_UMAP = True
except ImportError:
    HAS_UMAP = False

try:
    from radon.complexity import cc_visit
    from radon.metrics import mi_visit
    HAS_RADON = True
except ImportError:
    HAS_RADON = False

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

ROOT = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline"
OUT  = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/lakehouse_data"

# Filter out library source code — only YOUR code
SKIP_DIRS = {'.venv', '.venv_fresh', '__pycache__', 'node_modules', '.git',
             'site-packages', 'venv', '.tox', 'dist', 'build', '.eggs'}
SKIP_PATHS = ['AI_Logs/pydantic', 'AI_Logs/instructor', 'AI_Logs/openai',
              'gemma-tuner-multimodal-main', 'node_modules']

def _ast_depth(node, depth=0):
    max_d = depth
    for child in ast.iter_child_nodes(node):
        max_d = max(max_d, _ast_depth(child, depth + 1))
    return max_d

t0 = time.time()

# ═══════════════════════════════════════════════════════════════════════
# PHASE 1: MINE YOUR CODE ONLY
# ═══════════════════════════════════════════════════════════════════════
print("PHASE 1: Mining YOUR code (filtering libraries)")
print("=" * 70)

blocks = []
file_stats = []
import_graph = defaultdict(set)
file_sources = {}  # filepath -> source code (for radon)

for root_dir, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
    rel_dir = os.path.relpath(root_dir, ROOT).replace("\\", "/")
    
    # Skip library paths
    if any(rel_dir.startswith(sp) for sp in SKIP_PATHS):
        dirs.clear()
        continue
    
    for fname in files:
        if not fname.endswith('.py'):
            continue
        fp = os.path.join(root_dir, fname).replace("\\", "/")
        rel = os.path.relpath(fp, ROOT).replace("\\", "/")
        
        try:
            src = open(fp, encoding='utf-8', errors='ignore').read()
            tree = ast.parse(src, filename=fp)
        except SyntaxError:
            continue
        
        file_sources[rel] = src
        lines = src.count('\n') + 1
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split('.')[0])
                    import_graph[rel].add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                mod = (node.module or '').split('.')[0]
                if mod:
                    imports.append(mod)
                    import_graph[rel].add(mod)
        
        top_classes = sum(1 for n in ast.iter_child_nodes(tree) if isinstance(n, ast.ClassDef))
        top_funcs = sum(1 for n in ast.iter_child_nodes(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
        
        file_stats.append({
            'filepath': fp,
            'relative_path': rel,
            'filename': fname,
            'lines': lines,
            'chars': len(src),
            'num_imports': len(set(imports)),
            'num_classes': top_classes,
            'num_functions': top_funcs,
            'imports_list': '|'.join(sorted(set(imports))),
            'directory': os.path.dirname(rel) or '(root)',
        })
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                sym_type = "class" if isinstance(node, ast.ClassDef) else "function"
                code_text = ast.unparse(node)
                docstring = ast.get_docstring(node) or ""
                num_branches = sum(1 for n in ast.walk(node) 
                                   if isinstance(n, (ast.If, ast.For, ast.While, ast.Try,
                                                     ast.With, ast.ExceptHandler)))
                num_returns = sum(1 for n in ast.walk(node) if isinstance(n, ast.Return))
                num_calls = sum(1 for n in ast.walk(node) if isinstance(n, ast.Call))
                
                blocks.append({
                    'symbol_name': node.name,
                    'type': sym_type,
                    'source_file': fp,
                    'relative_path': rel,
                    'docstring': docstring,
                    'code_content': code_text,
                    'char_len': len(code_text),
                    'lines_of_code': code_text.count('\n') + 1,
                    'num_branches': num_branches,
                    'num_returns': num_returns,
                    'max_depth': _ast_depth(node),
                    'num_calls': num_calls,
                    'has_docstring': 1 if docstring else 0,
                    'is_async': 1 if isinstance(node, ast.AsyncFunctionDef) else 0,
                })

df_blocks = pd.DataFrame(blocks)
df_files = pd.DataFrame(file_stats)
print(f"  YOUR .py files: {len(df_files)}")
print(f"  YOUR code blocks: {len(df_blocks)}")

# ═══════════════════════════════════════════════════════════════════════
# PHASE 2: RADON COMPLEXITY (per file)
# ═══════════════════════════════════════════════════════════════════════
print(f"\nPHASE 2: Radon Complexity Analysis")
print("=" * 70)

radon_results = []
if HAS_RADON:
    for rel, src in file_sources.items():
        try:
            cc_blocks = cc_visit(src)
            mi_score = mi_visit(src, multi=False)
            avg_cc = np.mean([b.complexity for b in cc_blocks]) if cc_blocks else 0
            max_cc = max([b.complexity for b in cc_blocks]) if cc_blocks else 0
            radon_results.append({
                'relative_path': rel,
                'avg_cyclomatic': round(avg_cc, 2),
                'max_cyclomatic': max_cc,
                'maintainability_index': round(mi_score, 2),
                'num_complex_blocks': sum(1 for b in cc_blocks if b.complexity > 10),
            })
        except:
            pass
    
    df_radon = pd.DataFrame(radon_results)
    if not df_radon.empty:
        df_files = df_files.merge(df_radon, on='relative_path', how='left')
        df_files['avg_cyclomatic'] = df_files['avg_cyclomatic'].fillna(0)
        df_files['maintainability_index'] = df_files['maintainability_index'].fillna(100)
        
        print(f"  Analyzed {len(df_radon)} files")
        worst = df_files.nlargest(10, 'max_cyclomatic')
        print(f"\n  MOST COMPLEX FILES (highest cyclomatic complexity):")
        for _, r in worst.iterrows():
            print(f"    CC={r.get('max_cyclomatic',0):>3} MI={r.get('maintainability_index',0):>5.1f} | {r['filename']}")
else:
    print("  radon not available, skipping")

# ═══════════════════════════════════════════════════════════════════════
# PHASE 3: NETWORKX DEPENDENCY GRAPH
# ═══════════════════════════════════════════════════════════════════════
print(f"\nPHASE 3: NetworkX Dependency Graph")
print("=" * 70)

# Build file-to-file graph (only internal imports)
local_modules = {Path(f['filename']).stem for f in file_stats}
G = nx.DiGraph()
for src_file, imports in import_graph.items():
    G.add_node(src_file)
    for imp in imports:
        if imp in local_modules:
            G.add_edge(src_file, imp)

print(f"  Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")

# PageRank — most important files
if G.number_of_edges() > 0:
    pagerank = nx.pagerank(G, alpha=0.85)
    top_pr = sorted(pagerank.items(), key=lambda x: -x[1])[:15]
    print(f"\n  PAGERANK — Most architecturally important files:")
    for path, score in top_pr:
        print(f"    {score:.4f} | {path}")

    # Betweenness centrality — bridge files
    bc = nx.betweenness_centrality(G)
    top_bc = sorted(bc.items(), key=lambda x: -x[1])[:10]
    print(f"\n  BETWEENNESS CENTRALITY — Bridge/connector files:")
    for path, score in top_bc:
        if score > 0:
            print(f"    {score:.4f} | {path}")

# ═══════════════════════════════════════════════════════════════════════
# PHASE 4: TF-IDF + KMEANS + UMAP
# ═══════════════════════════════════════════════════════════════════════
print(f"\nPHASE 4: TF-IDF + KMeans + UMAP Galaxy")
print("=" * 70)

df_blocks['combined'] = df_blocks['symbol_name'] + ' ' + df_blocks['docstring'] + ' ' + df_blocks['code_content']
tfidf = TfidfVectorizer(max_features=3000, stop_words='english')
tfidf_matrix = tfidf.fit_transform(df_blocks['combined'])

n_docs = len(df_blocks)
auto_k = int(np.clip(np.log2(n_docs) * 1.8, 5, 15))
print(f"  Documents: {n_docs}, Auto-K: {auto_k}")

km = KMeans(n_clusters=auto_k, random_state=42, n_init='auto')
df_blocks['cluster'] = km.fit_predict(tfidf_matrix)

terms = tfidf.get_feature_names_out()
centroids = km.cluster_centers_.argsort()[:, ::-1]

print(f"\n  YOUR CODE TAXONOMY ({auto_k} clusters):")
for i in range(auto_k):
    cluster_rows = df_blocks[df_blocks['cluster'] == i]
    top_terms = [terms[j] for j in centroids[i, :6]]
    print(f"  Cluster {i:>2} ({len(cluster_rows):>4}): {', '.join(top_terms)}")

# UMAP 2D projection
umap_coords = None
if HAS_UMAP and n_docs > 50:
    print(f"\n  Running UMAP dimensionality reduction...")
    reducer = umap.UMAP(n_components=2, random_state=42, n_neighbors=15, min_dist=0.1)
    umap_coords = reducer.fit_transform(tfidf_matrix.toarray())
    df_blocks['umap_x'] = umap_coords[:, 0]
    df_blocks['umap_y'] = umap_coords[:, 1]
    print(f"  UMAP complete: {umap_coords.shape}")

# ═══════════════════════════════════════════════════════════════════════
# PHASE 5: CODE CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════
print(f"\nPHASE 5: Code Classification")
print("=" * 70)

def classify_code(row):
    name = row['symbol_name'].lower()
    code = row['code_content'].lower()[:500]
    doc = row['docstring'].lower()
    combined = name + ' ' + code + ' ' + doc
    if any(w in name for w in ['test_', '_test']): return 'test'
    if any(w in combined for w in ['engine', 'pipeline', 'processor']): return 'engine'
    if any(w in combined for w in ['orchestrat', 'warden', 'dispatch']): return 'orchestrator'
    if any(w in combined for w in ['ingest', 'load', 'fetch', 'download']): return 'ingestion'
    if any(w in combined for w in ['plot', 'chart', 'visual', 'dashboard', 'matplotlib']): return 'visualization'
    if any(w in combined for w in ['api', 'route', 'endpoint', 'fastapi']): return 'api'
    if any(w in combined for w in ['model', 'schema', 'pydantic', 'basemodel']): return 'schema'
    if any(w in combined for w in ['audit', 'verify', 'check', 'validate']): return 'audit'
    if any(w in combined for w in ['deploy', 'docker', 'cloud', 'gcs', 'firebase']): return 'deployment'
    if any(w in combined for w in ['sovereign', 'autonomous', 'swarm', 'agent']): return 'agent'
    if row['type'] == 'class': return 'class_other'
    return 'utility'

df_blocks['code_role'] = df_blocks.apply(classify_code, axis=1)
role_counts = df_blocks['code_role'].value_counts()
print("  Your code roles:")
for role, count in role_counts.items():
    print(f"    {role:<16} {count:>5}")

# IsolationForest
STRUCT_FEATURES = ['char_len','lines_of_code','num_branches','num_returns',
                   'max_depth','num_calls','has_docstring','is_async']
X_code = df_blocks[STRUCT_FEATURES].fillna(0)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_code)

iso = IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
df_blocks['code_outlier'] = iso.fit_predict(X_scaled) == -1

# ═══════════════════════════════════════════════════════════════════════
# PHASE 6: MEGA VISUAL DASHBOARD
# ═══════════════════════════════════════════════════════════════════════
print(f"\nPHASE 6: Visual Dashboard")
print("=" * 70)

PALETTE = ['#00f0ff','#ff3cac','#ffe600','#7dff8a','#ff6b35','#c77dff',
           '#ff4444','#44ff88','#8888ff','#ffaa00','#ff66cc','#66ffcc',
           '#ff99ff','#99ccff','#ffcc99']

fig = plt.figure(figsize=(28, 24), facecolor='#0d0d14')
gs = gridspec.GridSpec(3, 4, figure=fig, hspace=0.4, wspace=0.35)

# A: UMAP Galaxy Map
ax_umap = fig.add_subplot(gs[0, :2])
ax_umap.set_facecolor('#0a0a12')
if umap_coords is not None:
    for i in range(auto_k):
        mask = df_blocks['cluster'] == i
        ax_umap.scatter(df_blocks.loc[mask, 'umap_x'], df_blocks.loc[mask, 'umap_y'],
                        color=PALETTE[i % len(PALETTE)], alpha=0.6, s=8, label=f'C{i}')
    outliers = df_blocks[df_blocks['code_outlier']]
    ax_umap.scatter(outliers['umap_x'], outliers['umap_y'],
                    color='red', alpha=0.9, s=40, marker='X', zorder=5)
    ax_umap.legend(fontsize=5, ncol=5, labelcolor='white', facecolor='#1a1a2e',
                   loc='upper right')
ax_umap.set_title('UMAP CODE GALAXY -- Semantic Similarity Map', color='white',
                   fontsize=12, fontweight='bold')
ax_umap.tick_params(colors='#555')
for s in ax_umap.spines.values(): s.set_color('#222')

# B: Code Role Pie
ax_pie = fig.add_subplot(gs[0, 2])
ax_pie.set_facecolor('#13131f')
colors_pie = [PALETTE[i % len(PALETTE)] for i in range(len(role_counts))]
ax_pie.pie(role_counts.values, labels=role_counts.index, autopct='%1.0f%%',
           colors=colors_pie, textprops={'color':'white','fontsize':6})
ax_pie.set_title('CODE ROLE DISTRIBUTION', color='white', fontsize=11, fontweight='bold')

# C: Complexity vs Maintainability (radon)
ax_radon = fig.add_subplot(gs[0, 3])
ax_radon.set_facecolor('#13131f')
if HAS_RADON and 'max_cyclomatic' in df_files.columns:
    ax_radon.scatter(df_files['max_cyclomatic'], df_files['maintainability_index'],
                     c=df_files['chars'], cmap='plasma', alpha=0.6, s=20)
    ax_radon.set_xlabel('Max Cyclomatic Complexity', color='#aaa')
    ax_radon.set_ylabel('Maintainability Index', color='#aaa')
ax_radon.set_title('RADON: Complexity vs Maintainability', color='white',
                    fontsize=10, fontweight='bold')
ax_radon.tick_params(colors='white')
for s in ['top','right']: ax_radon.spines[s].set_visible(False)
ax_radon.spines['bottom'].set_color('#333')
ax_radon.spines['left'].set_color('#333')

# D: Cluster bar chart
ax_clust = fig.add_subplot(gs[1, 0])
ax_clust.set_facecolor('#13131f')
csizes = df_blocks['cluster'].value_counts().sort_index()
ax_clust.bar(csizes.index, csizes.values,
             color=[PALETTE[i % len(PALETTE)] for i in csizes.index])
ax_clust.set_title(f'TF-IDF CLUSTERS (K={auto_k})', color='white', fontsize=11, fontweight='bold')
ax_clust.tick_params(colors='white')
for s in ['top','right']: ax_clust.spines[s].set_visible(False)
ax_clust.spines['bottom'].set_color('#333')
ax_clust.spines['left'].set_color('#333')

# E: Complexity vs Size scatter
ax_cx = fig.add_subplot(gs[1, 1:3])
ax_cx.set_facecolor('#13131f')
role_colors = {role: PALETTE[i % len(PALETTE)] for i, role in enumerate(role_counts.index)}
for role in role_counts.index:
    grp = df_blocks[df_blocks['code_role'] == role]
    ax_cx.scatter(grp['char_len'], grp['num_branches'],
                  color=role_colors[role], alpha=0.5, s=12, label=role)
ax_cx.set_title('CODE SIZE vs COMPLEXITY (by role)', color='white', fontsize=11, fontweight='bold')
ax_cx.set_xlabel('Characters', color='#aaa')
ax_cx.set_ylabel('Branches', color='#aaa')
ax_cx.tick_params(colors='white')
ax_cx.legend(fontsize=5, ncol=3, labelcolor='white', facecolor='#1a1a2e')
for s in ['top','right']: ax_cx.spines[s].set_visible(False)
ax_cx.spines['bottom'].set_color('#333')
ax_cx.spines['left'].set_color('#333')

# F: Top files
ax_top = fig.add_subplot(gs[1, 3])
ax_top.set_facecolor('#13131f')
file_vols = df_blocks.groupby('relative_path')['char_len'].sum().nlargest(12)
ax_top.barh([os.path.basename(p) for p in file_vols.index][::-1],
            file_vols.values[::-1], color='#00f0ff')
ax_top.set_title('TOP FILES BY VOLUME', color='white', fontsize=10, fontweight='bold')
ax_top.tick_params(colors='white', labelsize=6)
for s in ['top','right']: ax_top.spines[s].set_visible(False)
ax_top.spines['bottom'].set_color('#333')
ax_top.spines['left'].set_color('#333')

# G: Top imports
ax_imp = fig.add_subplot(gs[2, 0:2])
ax_imp.set_facecolor('#13131f')
all_imports = []
for imps in import_graph.values():
    all_imports.extend(imps)
top_imp = pd.Series(all_imports).value_counts().head(20)
ax_imp.barh(top_imp.index[::-1], top_imp.values[::-1],
            color=[PALETTE[i % len(PALETTE)] for i in range(len(top_imp))])
ax_imp.set_title('TOP 20 IMPORTS (YOUR CODE)', color='white', fontsize=11, fontweight='bold')
ax_imp.tick_params(colors='white', labelsize=7)
for s in ['top','right']: ax_imp.spines[s].set_visible(False)
ax_imp.spines['bottom'].set_color('#333')
ax_imp.spines['left'].set_color('#333')

# H: Dendrogram (cluster hierarchy)
ax_dend = fig.add_subplot(gs[2, 2:])
ax_dend.set_facecolor('#13131f')
if auto_k > 2:
    cluster_centers = km.cluster_centers_
    Z = linkage(pdist(cluster_centers, 'cosine'), method='ward')
    dendrogram(Z, ax=ax_dend, labels=[f'C{i}' for i in range(auto_k)],
               leaf_font_size=8, color_threshold=0.5)
    ax_dend.tick_params(colors='white', labelsize=7)
ax_dend.set_title('CLUSTER HIERARCHY (Dendrogram)', color='white', fontsize=11, fontweight='bold')
for s in ['top','right']: ax_dend.spines[s].set_visible(False)
ax_dend.spines['bottom'].set_color('#333')
ax_dend.spines['left'].set_color('#333')

fig.suptitle('CODE LANE v2 -- YOUR Pipeline Intelligence (Libraries Filtered)',
             color='white', fontsize=16, fontweight='bold', y=0.99)

dash_path = os.path.join(os.path.dirname(OUT), 'code_lane_v2_dashboard.png')
plt.savefig(dash_path, dpi=150, bbox_inches='tight', facecolor='#0d0d14')
plt.close()

# ═══════════════════════════════════════════════════════════════════════
# PHASE 7: SAVE EVERYTHING
# ═══════════════════════════════════════════════════════════════════════
blocks_path = os.path.join(OUT, 'mined_code_yours.parquet')
files_path = os.path.join(OUT, 'code_file_stats_yours.parquet')
imports_path = os.path.join(OUT, 'code_imports_yours.parquet')

df_blocks.to_parquet(blocks_path, index=False)
df_files.to_parquet(files_path, index=False)

import_edges = []
for src, imps in import_graph.items():
    for imp in imps:
        import_edges.append({'source': src, 'imports': imp})
pd.DataFrame(import_edges).to_parquet(imports_path, index=False)

elapsed = time.time() - t0
print(f"\n{'='*70}")
print(f"CODE LANE v2 COMPLETE in {elapsed:.1f}s")
print(f"{'='*70}")
print(f"  {len(df_files)} YOUR .py files (libraries excluded)")
print(f"  {len(df_blocks)} code blocks")
print(f"  {auto_k} semantic clusters")
print(f"  {df_blocks['code_outlier'].sum()} anomalies")
print(f"  {len(import_edges)} import edges")
if HAS_RADON:
    print(f"  Radon: {len(radon_results)} files analyzed")
print(f"\nParquets: {blocks_path}")
print(f"          {files_path}")
print(f"          {imports_path}")
print(f"Dashboard: {dash_path}")
