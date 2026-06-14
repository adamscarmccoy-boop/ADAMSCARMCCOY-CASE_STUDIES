"""Deep scan: Rust + JS/TS + God class methods — all in one"""
import sys, os, re
from collections import Counter
import pandas as pd

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

ROOT = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline"
SKIP = {'.venv','.venv_fresh','__pycache__','node_modules','.git','site-packages','venv'}

# ═══════════════════════════════════════════════════════════════════════
# PART 1: RUST
# ═══════════════════════════════════════════════════════════════════════
print("RUST CODEBASE")
print("=" * 70)

rust_files = []
rust_symbols = []
for root_dir, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in SKIP]
    for f in files:
        if not f.endswith('.rs'): continue
        fp = os.path.join(root_dir, f)
        rel = os.path.relpath(fp, ROOT).replace("\\", "/")
        src = open(fp, encoding='utf-8', errors='ignore').read()
        rust_files.append((len(src), f, rel))
        for m in re.finditer(r'(pub\s+)?(struct|enum|impl|fn|trait)\s+(\w+)', src):
            rust_symbols.append((m.group(2), m.group(3), rel, f, bool(m.group(1))))

print(f"Total .rs files: {len(rust_files)}")
print(f"Total symbols: {len(rust_symbols)}")

rust_types = Counter(s[0] for s in rust_symbols)
print(f"Breakdown: {dict(rust_types)}")

print("\nTop 15 Rust files by size:")
for size, name, path in sorted(rust_files, key=lambda x: -x[0])[:15]:
    print(f"  {size:>8} chars  {name:<35} {os.path.dirname(path)}")

print("\nPublic structs/enums/traits:")
seen = set()
for stype, name, path, fname, public in sorted(rust_symbols, key=lambda x: x[1]):
    if stype in ('struct','enum','trait') and public and name not in seen:
        seen.add(name)
        print(f"  {stype:<8} {name:<35} {fname}")

# ═══════════════════════════════════════════════════════════════════════
# PART 2: JS/TS
# ═══════════════════════════════════════════════════════════════════════
print("\n\nJS/TS CODEBASE")
print("=" * 70)

js_blocks = []
for root_dir, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in SKIP]
    rel_dir = os.path.relpath(root_dir, ROOT).replace("\\", "/")
    if any(rel_dir.startswith(s) for s in ['AI_Logs/pydantic','AI_Logs/instructor','AI_Logs/openai']):
        dirs.clear()
        continue
    for f in files:
        if not any(f.endswith(e) for e in ['.js','.ts','.tsx','.jsx']): continue
        if 'min.js' in f or 'chunk' in f: continue
        fp = os.path.join(root_dir, f)
        rel = os.path.relpath(fp, ROOT).replace("\\", "/")
        src = open(fp, encoding='utf-8', errors='ignore').read()
        for m in re.finditer(r'(export\s+)?(default\s+)?(function|class|const|interface|type)\s+(\w+)', src):
            js_blocks.append({
                'kind': m.group(3), 'name': m.group(4),
                'exported': bool(m.group(1)), 'file': rel,
                'filename': f, 'chars': len(src)
            })

print(f"Total JS/TS symbols: {len(js_blocks)}")
kind_counts = Counter(b['kind'] for b in js_blocks)
print(f"Types: {dict(kind_counts)}")

by_file = {}
for b in js_blocks:
    by_file.setdefault(b['file'], []).append(b)

print("\nKey JS/TS files:")
for f in sorted(by_file, key=lambda x: -by_file[x][0]['chars'])[:15]:
    blocks = by_file[f]
    exported = [b['name'] for b in blocks if b['exported']]
    chars = blocks[0]['chars']
    fname = os.path.basename(f)
    exp_str = ", ".join(exported[:6]) if exported else "(none)"
    print(f"  {chars:>6} chars  {fname:<30} exports: {exp_str}")

# ═══════════════════════════════════════════════════════════════════════
# PART 3: GOD CLASS DEEP DIVE
# ═══════════════════════════════════════════════════════════════════════
print("\n\nGOD CLASS DEEP DIVE")
print("=" * 70)

PARQUET = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/lakehouse_data/mined_code_yours.parquet"
df = pd.read_parquet(PARQUET)

TARGETS = ['AutonomousLearningEngine','SovereignEngine','RateLimitedGPUClient',
           'SovereignChat','SovereignDiagnosticEngine','ExecutionEngine',
           'SovereignIntelligencePipeline','AbletonSessionParser','LMStudioClient']

for target in TARGETS:
    rows = df[df['symbol_name'] == target]
    if rows.empty: continue
    r = rows.iloc[0]
    code = r['code_content']
    methods = re.findall(r'def (\w+)\(', code)
    props = [m for m in methods if not m.startswith('_')]
    privates = [m for m in methods if m.startswith('_') and not m.startswith('__')]
    dunders = [m for m in methods if m.startswith('__')]
    
    fname = os.path.basename(r['source_file'])
    print(f"\n{target} ({r['type']}) -- {fname}")
    print(f"  {r['char_len']} chars | {r['num_branches']} branches | depth={r['max_depth']} | {r['num_calls']} calls")
    print(f"  Public ({len(props)}):  {', '.join(props[:15])}")
    if privates:
        print(f"  Private ({len(privates)}): {', '.join(privates[:10])}")
    if dunders:
        print(f"  Dunders ({len(dunders)}): {', '.join(dunders)}")
    if r['docstring']:
        print(f"  Doc: {r['docstring'][:120]}")

# ═══════════════════════════════════════════════════════════════════════
# PART 4: CROSS-REFERENCE — What imports what
# ═══════════════════════════════════════════════════════════════════════
print("\n\nCROSS-LANGUAGE MAP")
print("=" * 70)

# Find which Python files reference JS/TS/React/frontend
py_web_refs = []
for root_dir, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in SKIP]
    rel_dir = os.path.relpath(root_dir, ROOT).replace("\\", "/")
    if any(rel_dir.startswith(s) for s in ['AI_Logs/pydantic','AI_Logs/instructor','AI_Logs/openai']):
        dirs.clear()
        continue
    for f in files:
        if not f.endswith('.py'): continue
        fp = os.path.join(root_dir, f)
        src = open(fp, encoding='utf-8', errors='ignore').read()
        if any(w in src for w in ['react', 'tsx', 'frontend', 'vite', 'next', 'tailwind']):
            rel = os.path.relpath(fp, ROOT).replace("\\", "/")
            py_web_refs.append(rel)

print(f"Python files referencing web/frontend: {len(py_web_refs)}")
for p in py_web_refs[:15]:
    print(f"  {p}")
