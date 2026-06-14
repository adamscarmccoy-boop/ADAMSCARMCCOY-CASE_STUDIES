# Legion-Jacked-Pipeline — Full Codebase Intelligence Report

![Architecture Map](C:/Users/adams/.gemini/antigravity-ide/brain/ab68d511-5685-4692-8293-08a6b2fa31c1/architecture_map.png)

---

## What We Found

### The Numbers

| Metric | Count |
|---|---|
| Python files (YOUR code) | **280** |
| Python code blocks (functions + classes) | **1,115** |
| Total .py files (including libs) | 1,311 |
| JavaScript/TypeScript files | 72 |
| Rust source files (pydantic-core) | 125 |
| Jupyter notebooks | 29 |
| Ableton Live Sets | 55 |
| DuckDB databases | 6 |
| LanceDB vector stores | 102 `.lance` files |
| Parquet data lake files | 60 |
| API routes | 66 |
| MCP server tools | 35 |
| Import dependency edges | 1,437 |

---

### Architecture — 5 Layers

**Layer 1: Data Sources**
- 6 DuckDB databases (`web_intel_sonicdb.duckdb` at 6MB is the largest — Spotify + Discogs + DSP)
- 102 LanceDB vector files (Snowflake Arctic embeddings for semantic search)
- 60 parquet files in the lakehouse
- 55 Ableton `.als` session files
- 38 `.wav` audio files

**Layer 2: Engines (the God Classes)**

| Engine | Size | Methods | Role |
|---|---|---|---|
| `AutonomousLearningEngine` | 17,889 chars | 16 public | Market scoring, collision matching, tempo alignment, production quality |
| `SovereignEngine` | 16,013 chars | 6 public | Pure math catalog intelligence. **Zero LLM calls.** |
| `RateLimitedGPUClient` | 9,753 chars | 9 public | GPU-accelerated AudioCraft MusicGen with async rate limiting |
| `SovereignChat` | 6,203 chars | 1 public | Natural language → SQL → catalog query |
| `SovereignDiagnosticEngine` | 5,618 chars | 1 public | Delta + FX chains → structured LLM diagnosis |
| `SovereignIntelligencePipeline` | 4,589 chars | 2 public | Full signal chain: `.als` → parse → analyze → diagnose |
| `AbletonSessionParser` | 3,592 chars | 1 public | Parse gzipped XML `.als` → tracks + FX chains |

**Layer 3: ML/Intelligence**
- RandomForest multi-class classifier (artist style fingerprinting)
- IsolationForest anomaly detection (56 structural anomalies flagged)
- KMeans + TF-IDF clustering (15 semantic code clusters)
- UMAP dimensionality reduction (code galaxy map)
- Radon cyclomatic complexity analysis (280 files)

**Layer 4: API & Tools**
- `mcp_server.py`: 24 MCP tools — analyze, generate, query, stem separate, VRAM management
- `mcp_api_server.py`: 24 REST routes — DuckDB, LanceDB, Firebase, OS operations
- `sovereign_chat.py`: 5 routes — chat, track lookup, neighbors, release readiness
- `sonic_server.py` / `VERTEXINABOX.py`: OpenAI-compatible `/v1/chat/completions`
- WebSocket live log streaming

**Layer 5: Frontends**
- `sonic-architecture-framework/` — React + Vite + Framer Motion dashboard (49KB `App.tsx`)
  - Components: `GlassPanel`, `DataPulse`, `TechnicalLabel`, `AudioVisualizer`
  - `geminiService.ts` — Gemini API integration
- `frontend/` — Next.js app with `AudioVisualizer.tsx`
- `gemma-tuner-multimodal-main/` — Three.js 3D visualization + Chart.js dashboards

---

### Code Quality Insights (Radon)

| File | Cyclomatic Complexity | Maintainability Index | Status |
|---|---|---|---|
| `sovereign_chat.py` | CC=35 | MI=21.3 | Complex but manageable |
| `gpu_track_generator_async.py` | CC=33 | MI=23.4 | GPU async adds complexity |
| `mcp_api_server.py` | CC=27 | MI=1.2 | **Critical debt — needs refactor** |
| `build_sonic_core_batched.py` | CC=33 | MI=34.6 | Batch processing |
| `music_catelog.py` | CC=29 | MI=38.7 | Export logic |

---

### Code Taxonomy (15 clusters, what your code actually IS)

| Cluster | Size | Identity | Key Files |
|---|---|---|---|
| **Vector DB queries** | 38 | LanceDB + DuckDB access layer | ai_chat.py, legion_chat.py |
| **Sovereign engines** | 27 | Core math analysis (delta, RMS) | sovereign_engine.py |
| **Pydantic schemas** | 62 | Pure BaseModel definitions | api_server.py, mcp_api_server.py |
| **DSP signal math** | 14 | Butterworth filters, SOS, spectral | blind_audit_v5.py |
| **API/response handlers** | 193 | Request/response processing | agent_research.py, ai_chat.py |
| **Class constructors** | 80 | `__init__`, property, self patterns | cortex.py, sovereign_chat.py |
| **Librosa extraction** | 44 | Feature extraction pipeline | build_sonic_core*.py |
| **Audio generation** | 43 | Kick synthesis, mixing, mastering | math_music_generator.py |
| **Execution engines** | 75 | Task runners, subprocess, status | execution_worker.py |

---

## Next Steps

1. **Notebook consolidation** — Integrate the Gemini-generated cells (16-22) into `code_mining_pipeline.ipynb` and `web_intel_pipeline.ipynb`
2. **Forest Engine tuning** — Run `forest_engine_cell.py` with more artist targets + market data fusion
3. **MCP server refactor** — `mcp_api_server.py` has MI=1.2 (critical). Break into modules.
4. **Antigravity review loop** — Feed `code_lane_report.json` + this walkthrough back through `ask_antigravity.py` for Gemini to generate optimization recommendations
5. **Dashboard integration** — Wire `code_lane_v2_dashboard.png` and `forest_engine_dashboard.png` into the React `sonic-architecture-framework`
6. **Cross-language graph** — Map Python ↔ TypeScript ↔ Rust connections for a full dependency visual

---

## Experience & Resume

### Technical Skills Demonstrated

**Machine Learning & Data Science**
- Scikit-learn: RandomForestClassifier, IsolationForest, KMeans, StandardScaler, TF-IDF vectorization
- UMAP dimensionality reduction for high-dimensional code/audio feature spaces
- Radon static analysis for automated code quality metrics
- Cross-validated multi-class classification with balanced class weights
- Anomaly detection on 46-dimensional DSP feature vectors (Omni-Vectors)

**Audio/DSP Engineering**
- Librosa-based feature extraction pipeline: MFCC (13 coefficients), chroma, spectral centroid/rolloff/bandwidth/contrast, onset strength, harmonic/percussive ratio
- Butterworth filter design, stem separation, AudioCraft MusicGen integration
- Ableton Live `.als` XML parsing → automated session analysis
- Sub-bass/bass/mid/high energy band decomposition
- Crest factor, RMS, transient density, zero-crossing rate analysis

**Full-Stack Development**
- Python: FastAPI, Pydantic, DuckDB, LanceDB, Instructor (structured LLM output)
- React/TypeScript: Vite, Framer Motion, Three.js 3D visualization
- Next.js: Server-side rendered audio dashboard
- MCP (Model Context Protocol): 35-tool server for AI agent integration
- OpenAI-compatible API endpoints (`/v1/chat/completions`)

**Data Engineering**
- DuckDB embedded analytics (6 databases, 12,000+ records)
- LanceDB vector storage with Snowflake Arctic Embed
- Apache Parquet lakehouse architecture (60 files)
- Multi-source data fusion: Spotify API + Discogs + MusicBrainz + local DSP
- AST-based code mining: 1,115 blocks extracted, classified, and clustered

**Infrastructure & DevOps**
- GPU-accelerated async processing with rate-limited semaphore patterns
- Tailscale mesh networking for zero-egress sovereign edge deployment
- Firebase integration for cloud state management
- Ollama + Phi-3 local LLM inference (zero cloud dependency option)
- Google Gemini 2.5 Flash API integration for code review automation

**Architecture & Design Patterns**
- Sovereign Edge Architecture: 100% local-first, zero data egress
- Pydantic-driven schema validation across 140 model definitions
- Event-driven async processing with `asyncio.Semaphore`
- Plugin architecture: MCP tools, LanceDB adapters, Gemini service modules
- Multi-lane analysis: Code Lane (AST mining) + Music Lane (DSP/market) running in parallel

### Project Summary (for resume)

> **Legion-Jacked Pipeline** — Full-stack autonomous audio intelligence platform
>
> Designed and built a local-first ML pipeline that analyzes 1,000+ audio tracks across 46 DSP dimensions, fuses market data from Spotify/Discogs/MusicBrainz, and generates production recommendations using RandomForest classification and IsolationForest anomaly detection. The system includes a 35-tool MCP server, GPU-accelerated audio generation via AudioCraft, React/Three.js dashboards, and a Pydantic-validated schema layer backed by a Rust core. Architecture follows zero-data-egress principles with Tailscale mesh networking and local LLM inference via Ollama.
>
> **Tech stack:** Python, Rust, TypeScript/React, FastAPI, DuckDB, LanceDB, scikit-learn, librosa, Pydantic, MCP, Gemini API, AudioCraft, Three.js, Next.js
