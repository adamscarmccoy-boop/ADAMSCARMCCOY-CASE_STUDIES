"""
WEB LAYER SCAN — dig into the 40 Python files that touch frontend/web
+ scan the actual sonic-architecture-framework React app
+ map the API endpoints
+ find the MCP server tools
"""
import sys, os, re, json
from collections import Counter

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

ROOT = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline"
SKIP = {'.venv','.venv_fresh','__pycache__','node_modules','.git','site-packages','venv'}

# ═══════════════════════════════════════════════════════════════════════
# PART 1: API ENDPOINTS — find all FastAPI/Flask routes
# ═══════════════════════════════════════════════════════════════════════
print("API ENDPOINTS ACROSS CODEBASE")
print("=" * 70)

routes = []
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
        for m in re.finditer(r'@(?:app|router)\.(get|post|put|delete|patch|websocket)\(["\']([^"\']+)', src):
            method = m.group(1).upper()
            path = m.group(2)
            routes.append((method, path, f, os.path.relpath(fp, ROOT).replace("\\", "/")))

print(f"Total API routes found: {len(routes)}")
for method, path, fname, rel in sorted(routes, key=lambda x: x[1]):
    print(f"  {method:<8} {path:<40} {fname}")

# ═══════════════════════════════════════════════════════════════════════
# PART 2: MCP TOOLS — find all MCP server tool definitions
# ═══════════════════════════════════════════════════════════════════════
print(f"\n\nMCP SERVER TOOLS")
print("=" * 70)

mcp_tools = []
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
        if 'mcp' not in src.lower() and 'tool' not in src.lower(): continue
        # Find @tool or @server.tool decorators
        for m in re.finditer(r'@(?:server\.tool|mcp\.tool|tool)\s*(?:\([^)]*\))?\s*(?:async\s+)?def\s+(\w+)', src):
            mcp_tools.append((m.group(1), f, os.path.relpath(fp, ROOT).replace("\\", "/")))
        # Also find tool registrations
        for m in re.finditer(r'(?:register_tool|add_tool)\(["\'](\w+)', src):
            mcp_tools.append((m.group(1), f, os.path.relpath(fp, ROOT).replace("\\", "/")))

print(f"Total MCP/tool definitions: {len(mcp_tools)}")
for name, fname, rel in sorted(mcp_tools, key=lambda x: x[0]):
    print(f"  {name:<40} {fname}")

# ═══════════════════════════════════════════════════════════════════════
# PART 3: SONIC ARCHITECTURE FRAMEWORK — the React app
# ═══════════════════════════════════════════════════════════════════════
print(f"\n\nSONIC ARCHITECTURE FRAMEWORK (React)")
print("=" * 70)

SAF_DIR = os.path.join(ROOT, "sonic-architecture-framework")
if os.path.isdir(SAF_DIR):
    saf_files = []
    for root_dir, dirs, files in os.walk(SAF_DIR):
        dirs[:] = [d for d in dirs if d not in SKIP and d != 'node_modules' and d != '.next']
        for f in files:
            if any(f.endswith(e) for e in ['.tsx','.ts','.js','.jsx','.css','.json']):
                fp = os.path.join(root_dir, f)
                rel = os.path.relpath(fp, SAF_DIR).replace("\\", "/")
                size = os.path.getsize(fp)
                saf_files.append((size, f, rel))
    
    print(f"Total source files: {len(saf_files)}")
    for size, name, path in sorted(saf_files, key=lambda x: -x[0])[:20]:
        print(f"  {size:>8} bytes  {name:<30} {path}")
    
    # Read App.tsx for component structure
    app_tsx = os.path.join(SAF_DIR, "src", "App.tsx")
    if os.path.exists(app_tsx):
        src = open(app_tsx, encoding='utf-8', errors='ignore').read()
        components = re.findall(r'(?:function|const)\s+(\w+)', src)
        imports = re.findall(r'import\s+.*?from\s+["\']([^"\']+)', src)
        print(f"\n  App.tsx components: {', '.join(list(set(components))[:15])}")
        print(f"  App.tsx imports from: {', '.join(list(set(imports))[:10])}")
else:
    print("  Directory not found")

# ═══════════════════════════════════════════════════════════════════════
# PART 4: FRONTEND DIR — Next.js app
# ═══════════════════════════════════════════════════════════════════════
print(f"\n\nFRONTEND (Next.js)")
print("=" * 70)

FRONT_DIR = os.path.join(ROOT, "frontend")
if os.path.isdir(FRONT_DIR):
    front_files = []
    for root_dir, dirs, files in os.walk(FRONT_DIR):
        dirs[:] = [d for d in dirs if d not in SKIP and d != 'node_modules' and d != '.next']
        for f in files:
            if any(f.endswith(e) for e in ['.tsx','.ts','.js','.jsx','.css','.json']):
                fp = os.path.join(root_dir, f)
                rel = os.path.relpath(fp, FRONT_DIR).replace("\\", "/")
                size = os.path.getsize(fp)
                front_files.append((size, f, rel))
    
    print(f"Total source files: {len(front_files)}")
    for size, name, path in sorted(front_files, key=lambda x: -x[0])[:15]:
        print(f"  {size:>8} bytes  {name:<30} {path}")
    
    page_tsx = os.path.join(FRONT_DIR, "src", "app", "page.tsx")
    if os.path.exists(page_tsx):
        src = open(page_tsx, encoding='utf-8', errors='ignore').read()
        components = re.findall(r'(?:function|const)\s+(\w+)', src)
        print(f"\n  page.tsx components: {', '.join(set(components)[:15])}")
else:
    print("  Directory not found")

# ═══════════════════════════════════════════════════════════════════════
# PART 5: HTML PAGES — docs, dashboards
# ═══════════════════════════════════════════════════════════════════════
print(f"\n\nHTML PAGES")
print("=" * 70)

html_files = []
for root_dir, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in SKIP and d != 'node_modules' and d != '.next']
    for f in files:
        if not f.endswith('.html'): continue
        fp = os.path.join(root_dir, f)
        size = os.path.getsize(fp)
        rel = os.path.relpath(fp, ROOT).replace("\\", "/")
        html_files.append((size, f, rel))

print(f"Total HTML files: {len(html_files)}")
for size, name, path in sorted(html_files, key=lambda x: -x[0])[:15]:
    print(f"  {size:>8} bytes  {name:<30} {os.path.dirname(path)}")

# ═══════════════════════════════════════════════════════════════════════
# PART 6: NOTEBOOKS — all .ipynb
# ═══════════════════════════════════════════════════════════════════════
print(f"\n\nNOTEBOOKS")
print("=" * 70)

nb_files = []
for root_dir, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in SKIP]
    for f in files:
        if not f.endswith('.ipynb'): continue
        fp = os.path.join(root_dir, f)
        size = os.path.getsize(fp)
        rel = os.path.relpath(fp, ROOT).replace("\\", "/")
        # Count cells
        try:
            nb = json.load(open(fp, encoding='utf-8'))
            cells = len(nb.get('cells', []))
        except:
            cells = 0
        nb_files.append((size, cells, f, rel))

print(f"Total notebooks: {len(nb_files)}")
for size, cells, name, path in sorted(nb_files, key=lambda x: -x[0])[:20]:
    print(f"  {size:>8} bytes  {cells:>3} cells  {name:<45} {os.path.dirname(path)}")
