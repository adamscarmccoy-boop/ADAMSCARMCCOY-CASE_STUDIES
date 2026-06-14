import ast, os, duckdb, pandas as pd
import numpy as np

LEGION_DIR   = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline"
PARQUET_PATH = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/lakehouse_data/mined_code.parquet"
KEYWORDS     = ["orchestrator", "warden", "langgraph", "graph", "lane", "engine", "forest"]
SKIP         = {".venv", ".venv_fresh", "__pycache__", "node_modules", ".git", "venv"}

# ── 1. Scan Legion parent dir ──────────────────────────────────────────
legion_blocks = []
for root, dirs, files in os.walk(LEGION_DIR):
    dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith(".")]
    for file in files:
        if not file.endswith(".py"): continue
        fp = os.path.join(root, file).replace("\\", "/")
        try:
            src = open(fp, encoding="utf-8", errors="ignore").read()
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    t = "class" if isinstance(node, ast.ClassDef) else "function"
                    legion_blocks.append({
                        "symbol_name":  node.name,
                        "type":         t,
                        "source_file":  fp,
                        "docstring":    ast.get_docstring(node) or "",
                        "code_content": ast.unparse(node),
                        "lines_of_code": len(node.body)
                    })
        except: pass

df_local = pd.DataFrame(legion_blocks)

# ── 2. Load existing parquet ───────────────────────────────────────────
conn = duckdb.connect(":memory:")
conn.execute(f"CREATE TABLE existing AS SELECT * FROM read_parquet('{PARQUET_PATH}')")
df_existing = conn.execute("SELECT * FROM existing WHERE source_file LIKE '%.py'").df()

# ── 3. Combine ─────────────────────────────────────────────────────────
df = pd.concat([df_existing, df_local], ignore_index=True).drop_duplicates(
    subset=["symbol_name", "source_file"]
)
df["char_len"] = df["code_content"].str.len()

# ── 4. ALL keywords — show TOP 3 each with char count ─────────────────
print(f"{'KEYWORD':<16} {'CHARS':>8}  {'TYPE':<10} {'SYMBOL':<40} FILE")
print("-" * 140)
for kw in KEYWORDS:
    mask = (
        df["symbol_name"].str.lower().str.contains(kw, na=False) |
        df["code_content"].str.lower().str.contains(kw, na=False) |
        df["docstring"].str.lower().str.contains(kw, na=False)
    )
    hits = df[mask].nlargest(3, "char_len")
    for _, r in hits.iterrows():
        fname = os.path.basename(r["source_file"])
        print(f"{kw.upper():<16} {r['char_len']:>8,}  {r['type']:<10} {r['symbol_name']:<40} {fname}")
    if hits.empty:
        print(f"{kw.upper():<16} {'—':>8}  no matches")
    print()
