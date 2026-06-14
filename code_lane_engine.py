"""
CODE LANE ENGINE — Full codebase analysis pipeline
====================================================
Mines ALL .py files from Legion-Jacked-Pipeline
Outputs: parquets, classification, dependency graph, visuals
NO MUSIC. CODE ONLY.
"""
import sys, os, ast, json, time, re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # headless
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from collections import Counter, defaultdict
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, IsolationForest

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

ROOT = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline"
OUT  = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/lakehouse_data"
SKIP = {'.venv', '.venv_fresh', '__pycache__', 'node_modules', '.git', 
        'site-packages', 'venv', '.tox', 'dist', 'build', '.eggs'}

t0 = time.time()

def _ast_depth(node, depth=0):
    """Recursively compute max AST nesting depth."""
    max_d = depth
    for child in ast.iter_child_nodes(node):
        max_d = max(max_d, _ast_depth(child, depth + 1))
    return max_d

# ═══════════════════════════════════════════════════════════════════════
# PHASE 1: FULL AST MINE — every .py in Legion-Jacked-Pipeline
# ═══════════════════════════════════════════════════════════════════════
print("PHASE 1: Full AST Mine")
print("=" * 70)

blocks = []
file_stats = []
import_graph = defaultdict(set)  # file -> set of imports
parse_errors = []

for root_dir, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith('.')]
    for fname in files:
        if not fname.endswith('.py'):
            continue
        fp = os.path.join(root_dir, fname).replace("\\", "/")
        rel = os.path.relpath(fp, ROOT).replace("\\", "/")
        
        try:
            src = open(fp, encoding='utf-8', errors='ignore').read()
            tree = ast.parse(src, filename=fp)
        except SyntaxError:
            parse_errors.append(rel)
            continue
        
        # File-level stats
        lines = src.count('\n') + 1
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
                    import_graph[rel].add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ''
                imports.append(mod)
                import_graph[rel].add(mod)
        
        # Count top-level classes and functions
        top_classes = sum(1 for n in ast.iter_child_nodes(tree) if isinstance(n, ast.ClassDef))
        top_funcs = sum(1 for n in ast.iter_child_nodes(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
        
        file_stats.append({
            'filepath': fp,
            'relative_path': rel,
            'filename': fname,
            'lines': lines,
            'chars': len(src),
            'num_imports': len(imports),
            'num_classes': top_classes,
            'num_functions': top_funcs,
            'imports_list': '|'.join(sorted(set(imports))),
            'directory': os.path.dirname(rel),
        })
        
        # AST block extraction
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                sym_type = "class" if isinstance(node, ast.ClassDef) else "function"
                code_text = ast.unparse(node)
                docstring = ast.get_docstring(node) or ""
                
                # Complexity metrics
                num_branches = sum(1 for n in ast.walk(node) 
                                   if isinstance(n, (ast.If, ast.For, ast.While, ast.Try,
                                                     ast.With, ast.ExceptHandler)))
                num_returns = sum(1 for n in ast.walk(node) if isinstance(n, ast.Return))
                max_depth = _ast_depth(node)
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
                    'max_depth': max_depth,
                    'num_calls': num_calls,
                    'has_docstring': bool(docstring),
                    'is_async': isinstance(node, ast.AsyncFunctionDef),
                })


print(f"  Scanned: {len(file_stats)} .py files")
print(f"  Extracted: {len(blocks)} code blocks (functions + classes)")
print(f"  Parse errors: {len(parse_errors)} files skipped")

# ═══════════════════════════════════════════════════════════════════════
# PHASE 2: SAVE PARQUETS
# ═══════════════════════════════════════════════════════════════════════
print(f"\nPHASE 2: Save Parquets")
print("=" * 70)

df_blocks = pd.DataFrame(blocks)
df_files  = pd.DataFrame(file_stats)

# Save
blocks_path = os.path.join(OUT, 'mined_code_legion.parquet')
files_path  = os.path.join(OUT, 'code_file_stats.parquet')

df_blocks.to_parquet(blocks_path, index=False)
df_files.to_parquet(files_path, index=False)
print(f"  mined_code_legion.parquet: {len(df_blocks)} blocks ({os.path.getsize(blocks_path)//1024} KB)")
print(f"  code_file_stats.parquet:   {len(df_files)} files  ({os.path.getsize(files_path)//1024} KB)")

# ═══════════════════════════════════════════════════════════════════════
# PHASE 3: IMPORT DEPENDENCY GRAPH
# ═══════════════════════════════════════════════════════════════════════
print(f"\nPHASE 3: Import Dependency Analysis")
print("=" * 70)

# Flatten import graph
import_edges = []
for src_file, imports in import_graph.items():
    for imp in imports:
        import_edges.append({'source': src_file, 'imports': imp})

df_imports = pd.DataFrame(import_edges)

# Most imported libraries
import_counts = df_imports['imports'].value_counts().head(25)
print("  Top 25 imports across entire codebase:")
for imp, count in import_counts.items():
    print(f"    {count:>4}x  {imp}")

# Save
imports_path = os.path.join(OUT, 'code_import_graph.parquet')
df_imports.to_parquet(imports_path, index=False)
print(f"\n  code_import_graph.parquet: {len(df_imports)} edges")

# ═══════════════════════════════════════════════════════════════════════
# PHASE 4: TF-IDF + KMEANS CLUSTERING (full codebase)
# ═══════════════════════════════════════════════════════════════════════
print(f"\nPHASE 4: TF-IDF Clustering")
print("=" * 70)

df_blocks['combined'] = df_blocks['symbol_name'] + ' ' + df_blocks['docstring'] + ' ' + df_blocks['code_content']

tfidf = TfidfVectorizer(max_features=3000, stop_words='english')
tfidf_matrix = tfidf.fit_transform(df_blocks['combined'])

n_docs = len(df_blocks)
auto_k = int(np.clip(np.log2(n_docs) * 2, 5, 20))
print(f"  Documents: {n_docs}, Auto-K: {auto_k}")

km = KMeans(n_clusters=auto_k, random_state=42, n_init='auto')
df_blocks['cluster'] = km.fit_predict(tfidf_matrix)

terms = tfidf.get_feature_names_out()
centroids = km.cluster_centers_.argsort()[:, ::-1]

print(f"\n  CODE TAXONOMY ({auto_k} clusters):")
print("  " + "-" * 65)
for i in range(auto_k):
    cluster_rows = df_blocks[df_blocks['cluster'] == i]
    top_terms = [terms[j] for j in centroids[i, :6]]
    print(f"  Cluster {i:>2} ({len(cluster_rows):>4} blocks): {', '.join(top_terms)}")

# ═══════════════════════════════════════════════════════════════════════
# PHASE 5: CODE CLASSIFICATION — RandomForest
# ═══════════════════════════════════════════════════════════════════════
print(f"\nPHASE 5: Code Block Classification (RandomForest)")
print("=" * 70)

# Label by keywords in symbol name / code
def classify_code(row):
    name = row['symbol_name'].lower()
    code = row['code_content'].lower()[:500]
    doc  = row['docstring'].lower()
    combined = name + ' ' + code + ' ' + doc
    
    if any(w in name for w in ['test_', '_test', 'assert']):
        return 'test'
    if any(w in combined for w in ['engine', 'pipeline', 'processor', 'runner']):
        return 'engine'
    if any(w in combined for w in ['orchestrat', 'warden', 'dispatch', 'scheduler']):
        return 'orchestrator'
    if any(w in combined for w in ['ingest', 'load', 'import', 'fetch', 'download', 'scrape']):
        return 'ingestion'
    if any(w in combined for w in ['plot', 'chart', 'visual', 'dashboard', 'figure', 'matplotlib']):
        return 'visualization'
    if any(w in combined for w in ['api', 'route', 'endpoint', 'fastapi', 'flask', 'server']):
        return 'api'
    if any(w in combined for w in ['model', 'schema', 'pydantic', 'basemodel', 'dataclass']):
        return 'schema'
    if any(w in combined for w in ['audit', 'verify', 'check', 'validate', 'inspect']):
        return 'audit'
    if any(w in combined for w in ['deploy', 'docker', 'cloud', 'gcs', 'firebase', 'bigquery']):
        return 'deployment'
    if row['type'] == 'class':
        return 'class_other'
    return 'utility'

df_blocks['code_role'] = df_blocks.apply(classify_code, axis=1)

role_counts = df_blocks['code_role'].value_counts()
print("  Code block classification:")
for role, count in role_counts.items():
    print(f"    {role:<16} {count:>5} blocks")

# Now train RF on the structural features to predict role
STRUCT_FEATURES = ['char_len', 'lines_of_code', 'num_branches', 'num_returns',
                   'max_depth', 'num_calls', 'has_docstring', 'is_async']

df_blocks['has_docstring'] = df_blocks['has_docstring'].astype(int)
df_blocks['is_async'] = df_blocks['is_async'].astype(int)

X_code = df_blocks[STRUCT_FEATURES].fillna(0)
y_code = df_blocks['code_role']

scaler_code = StandardScaler()
X_code_scaled = scaler_code.fit_transform(X_code)

rf_code = RandomForestClassifier(n_estimators=300, random_state=42,
                                  class_weight='balanced', n_jobs=-1)
rf_code.fit(X_code_scaled, y_code)

# Feature importances for code structure
code_importances = rf_code.feature_importances_
print("\n  Structural feature importances (what defines code type):")
for feat, imp in sorted(zip(STRUCT_FEATURES, code_importances), key=lambda x: -x[1]):
    print(f"    {feat:<20} {imp*100:.1f}%")

# Isolation Forest for anomalous code blocks
iso_code = IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
df_blocks['code_anomaly'] = iso_code.fit_predict(X_code_scaled)
df_blocks['code_outlier'] = df_blocks['code_anomaly'] == -1

anomaly_blocks = df_blocks[df_blocks['code_outlier']].nlargest(10, 'char_len')
print(f"\n  Anomalous code blocks (unusual structure): {df_blocks['code_outlier'].sum()}")
for _, r in anomaly_blocks.head(5).iterrows():
    print(f"    [{r['char_len']:>7} chars] {r['symbol_name']} ({r['code_role']}) -> {os.path.basename(r['source_file'])}")

# ═══════════════════════════════════════════════════════════════════════
# PHASE 6: ARCHITECTURE SPINE — most connected files
# ═══════════════════════════════════════════════════════════════════════
print(f"\nPHASE 6: Architecture Spine")
print("=" * 70)

# Files with most code blocks
file_block_counts = df_blocks.groupby('relative_path').agg(
    total_blocks=('symbol_name', 'count'),
    total_chars=('char_len', 'sum'),
    classes=('type', lambda x: (x == 'class').sum()),
    functions=('type', lambda x: (x == 'function').sum()),
    avg_complexity=('num_branches', 'mean'),
    max_depth=('max_depth', 'max'),
).sort_values('total_chars', ascending=False)

print("  Top 15 files by total code volume:")
for path, row in file_block_counts.head(15).iterrows():
    print(f"    {row['total_chars']:>8} chars | {row['total_blocks']:>3} blocks | "
          f"{row['classes']:>2}C {row['functions']:>2}F | depth {row['max_depth']:>2} | {path}")

# Directory heatmap
dir_stats = df_files.groupby('directory').agg(
    files=('filename', 'count'),
    total_lines=('lines', 'sum'),
    total_chars=('chars', 'sum'),
    avg_imports=('num_imports', 'mean'),
).sort_values('total_chars', ascending=False)

print(f"\n  Top 10 directories by code volume:")
for d, row in dir_stats.head(10).iterrows():
    print(f"    {row['total_chars']:>9} chars | {row['files']:>3} files | {row['total_lines']:>6} lines | {d}")

# ═══════════════════════════════════════════════════════════════════════
# PHASE 7: VISUAL DASHBOARD — CODE LANE
# ═══════════════════════════════════════════════════════════════════════
print(f"\nPHASE 7: Visual Dashboard")
print("=" * 70)

PALETTE = ['#00f0ff','#ff3cac','#ffe600','#7dff8a','#ff6b35','#c77dff',
           '#ff4444','#44ff88','#8888ff','#ffaa00','#ff66cc']

fig = plt.figure(figsize=(24, 22), facecolor='#0d0d14')
gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.4, wspace=0.35)

# Panel A: Code Role Distribution
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_facecolor('#13131f')
roles = df_blocks['code_role'].value_counts()
colors_pie = [PALETTE[i % len(PALETTE)] for i in range(len(roles))]
wedges, texts, autotexts = ax1.pie(roles.values, labels=roles.index, autopct='%1.0f%%',
                                     colors=colors_pie, textprops={'color':'white', 'fontsize':7})
ax1.set_title('CODE ROLE DISTRIBUTION', color='white', fontsize=11, fontweight='bold')

# Panel B: Feature Importances (what defines code type)
ax2 = fig.add_subplot(gs[0, 1])
ax2.set_facecolor('#13131f')
sorted_feats = sorted(zip(STRUCT_FEATURES, code_importances), key=lambda x: x[1])
ax2.barh([f[0] for f in sorted_feats], [f[1] for f in sorted_feats],
         color=PALETTE[:len(sorted_feats)])
ax2.set_title('STRUCTURAL FEATURE IMPORTANCE', color='white', fontsize=11, fontweight='bold')
ax2.tick_params(colors='white')
for s in ['top','right']: ax2.spines[s].set_visible(False)
ax2.spines['bottom'].set_color('#333')
ax2.spines['left'].set_color('#333')

# Panel C: Top 10 largest files
ax3 = fig.add_subplot(gs[0, 2])
ax3.set_facecolor('#13131f')
top_files = file_block_counts.head(10)
ax3.barh([os.path.basename(p) for p in top_files.index][::-1],
         top_files['total_chars'].values[::-1], color='#00f0ff')
ax3.set_title('TOP 10 FILES BY CODE VOLUME', color='white', fontsize=11, fontweight='bold')
ax3.tick_params(colors='white', labelsize=7)
for s in ['top','right']: ax3.spines[s].set_visible(False)
ax3.spines['bottom'].set_color('#333')
ax3.spines['left'].set_color('#333')

# Panel D: Cluster sizes
ax4 = fig.add_subplot(gs[1, 0])
ax4.set_facecolor('#13131f')
cluster_sizes = df_blocks['cluster'].value_counts().sort_index()
ax4.bar(cluster_sizes.index, cluster_sizes.values,
        color=[PALETTE[i % len(PALETTE)] for i in cluster_sizes.index])
ax4.set_title(f'TF-IDF CODE CLUSTERS (K={auto_k})', color='white', fontsize=11, fontweight='bold')
ax4.set_xlabel('Cluster ID', color='#aaa')
ax4.set_ylabel('Blocks', color='#aaa')
ax4.tick_params(colors='white')
for s in ['top','right']: ax4.spines[s].set_visible(False)
ax4.spines['bottom'].set_color('#333')
ax4.spines['left'].set_color('#333')

# Panel E: Complexity vs Size scatter (colored by role)
ax5 = fig.add_subplot(gs[1, 1:])
ax5.set_facecolor('#13131f')
role_colors = {role: PALETTE[i % len(PALETTE)] for i, role in enumerate(roles.index)}
for role in roles.index:
    grp = df_blocks[df_blocks['code_role'] == role]
    ax5.scatter(grp['char_len'], grp['num_branches'],
                color=role_colors[role], alpha=0.5, s=15, label=role)
# Highlight outliers
outliers = df_blocks[df_blocks['code_outlier']]
ax5.scatter(outliers['char_len'], outliers['num_branches'],
            color='red', alpha=0.9, s=80, marker='X', label='ANOMALY', zorder=5)
ax5.set_title('CODE COMPLEXITY vs SIZE (colored by role)', color='white', fontsize=11, fontweight='bold')
ax5.set_xlabel('Character Length', color='#aaa')
ax5.set_ylabel('Branch Count (if/for/while/try)', color='#aaa')
ax5.tick_params(colors='white')
ax5.legend(fontsize=6, labelcolor='white', facecolor='#1a1a2e', ncol=3)
for s in ['top','right']: ax5.spines[s].set_visible(False)
ax5.spines['bottom'].set_color('#333')
ax5.spines['left'].set_color('#333')

# Panel F: Top 25 imports
ax6 = fig.add_subplot(gs[2, 0:2])
ax6.set_facecolor('#13131f')
top_imports = import_counts.head(20)
ax6.barh(top_imports.index[::-1], top_imports.values[::-1],
         color=[PALETTE[i % len(PALETTE)] for i in range(len(top_imports))])
ax6.set_title('TOP 20 IMPORTS ACROSS CODEBASE', color='white', fontsize=11, fontweight='bold')
ax6.tick_params(colors='white', labelsize=7)
for s in ['top','right']: ax6.spines[s].set_visible(False)
ax6.spines['bottom'].set_color('#333')
ax6.spines['left'].set_color('#333')

# Panel G: Directory heatmap
ax7 = fig.add_subplot(gs[2, 2])
ax7.set_facecolor('#13131f')
top_dirs = dir_stats.head(8)
dir_labels = [d if len(d) < 30 else '...' + d[-27:] for d in top_dirs.index]
ax7.barh(dir_labels[::-1], top_dirs['total_chars'].values[::-1], color='#c77dff')
ax7.set_title('DIRECTORY CODE VOLUME', color='white', fontsize=11, fontweight='bold')
ax7.tick_params(colors='white', labelsize=7)
for s in ['top','right']: ax7.spines[s].set_visible(False)
ax7.spines['bottom'].set_color('#333')
ax7.spines['left'].set_color('#333')

fig.suptitle('CODE LANE ENGINE -- Full Codebase Intelligence Dashboard',
             color='white', fontsize=16, fontweight='bold', y=0.98)

dashboard_path = os.path.join(os.path.dirname(OUT), 'code_lane_dashboard.png')
plt.savefig(dashboard_path, dpi=150, bbox_inches='tight', facecolor='#0d0d14')
plt.close()
print(f"  Dashboard saved -> {dashboard_path}")

# ═══════════════════════════════════════════════════════════════════════
# PHASE 8: SAVE ENRICHED PARQUET
# ═══════════════════════════════════════════════════════════════════════
enriched_path = os.path.join(OUT, 'mined_code_legion.parquet')
df_blocks.to_parquet(enriched_path, index=False)
print(f"\n  Final mined_code_legion.parquet: {len(df_blocks)} blocks with clusters + roles + anomalies")

# ═══════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════
elapsed = time.time() - t0
print(f"\n{'='*70}")
print(f"CODE LANE ENGINE COMPLETE in {elapsed:.1f}s")
print(f"{'='*70}")
print(f"  {len(df_files)} .py files scanned")
print(f"  {len(df_blocks)} code blocks extracted")
print(f"  {auto_k} semantic clusters identified")
print(f"  {len(role_counts)} code roles classified")
print(f"  {df_blocks['code_outlier'].sum()} structural anomalies flagged")
print(f"  {len(df_imports)} import edges mapped")
print(f"\nParquets:")
print(f"  {enriched_path}")
print(f"  {files_path}")
print(f"  {imports_path}")
print(f"\nDashboard:")
print(f"  {dashboard_path}")
