# 🎛️ Ableton Session Intelligence & Web Intelligence Engine (H.O.R.N. Stack)

A forensic-grade, local-first session intelligence, audio mastering, and web metadata consolidation engine for Ableton Live projects and digital DSP audio processing. This project implements a **3-Lane Delta Architecture** using **PyArrow + Parquet + DuckDB** for the relational data lakehouse, and **LanceDB** for vector embeddings. The intelligence layer is powered by offline hardware-muzzled LLMs (via Ollama) and cloud-grade models (via the Antigravity SDK) for comprehensive side-by-side Neural A&R profiling.

---

## ⚡ The H.O.R.N. Architectural Manifesto

*   **H — Hardware-Optimized:** Tensors, arrays, and model weights are pinned directly to local GPU VRAM/RAM pools with absolute zero cloud round-trip latencies.
*   **O — On-Demand / Offline:** 100% data privacy. No unreleased client audio or proprietary arrangement metadata is ever leaked to third-party web servers.
*   **R — Reproducible:** Structural ledger states are cataloged deterministically via DuckDB, LanceDB, and Parquet snapshots.
*   **N — Native:** The extraction layer hooks directly into native Ableton Live XML file formats without binary memory injections.

---

## 🏗️ 3-Lane Delta Architecture

The pipeline processes multi-source API metadata, physical track arrangements, and audio DSP characteristics across three strictly separated lanes:

```
                  ┌──────────────────────────────────────────────┐
                  │          Raw Multi-Source Ingestion          │
                  │   (Spotify, iTunes, MusicBrainz, Discogs)    │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼ (PyArrow / Columnar Parquet)
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                 3-LANE DELTA FRAMEWORK                                  │
├────────────────────────────────────────────────├────────────────────────────────────────┤
│ Lane 1: DuckDB Relational Lakehouse (Physical) │ Lane 2: LanceDB Vector Database        │
│   - Raw API tables                             │   - 1024-dim Snowflake Arctic Embeds   │
│   - Physical DSP audio features                │   - Full schema metadata filtering     │
├────────────────────────────────────────────────┴────────────────────────────────────────┤
│ Lane 3: H.O.R.N. Logs (Structured Audit Trail)                                          │
└────────────────────────────────────────┬────────────────────────────────────────────────┘
                                         │
                                         ▼
                        ┌─────────────────────────────────┐
                        │    Pydantic Fusion Firewall     │
                        │    (Deterministic Consensus)    │
                        └────────────────┬────────────────┘
                                         │
                                         ▼
                 ┌───────────────────────┴───────────────────────┐
                 │                                               │
                 ▼                                               ▼
      [Local Gemma via Ollama]                     [Cloud Gemini via Antigravity]
      - Zero-egress local node                     - High-capacity A/B testing
```

| Lane | Store / Mechanism | Purpose |
| :--- | :--- | :--- |
| **Lane 1** | DuckDB (Physical WebDB) | Houses immutable raw tables loaded natively via PyArrow from Parquet cold storage. Holds physical audio features (`dsp_rms`, `dsp_crest`, `dsp_sub`, etc.) and chart streams. |
| **Lane 2** | LanceDB (VectorDB) | Embedded vector store holding 1024-dimensional Snowflake Arctic embeddings. Built with a rich metadata schema to support complex vector searches filtering on physical DSP parameters. |
| **Lane 3** | H.O.R.N. Audits | Relational database containing detailed system execution metrics, execution times, and pipeline state logs. |

---

## ⚡ High-Performance Lakehouse Ingestion (PyArrow + Parquet)

To process massive audio datasets efficiently, the ingestion layer is built entirely on **PyArrow** and **Parquet**:
1. **Columnar Conversion**: Raw JSON arrays (containing thousands of physical DSP audio features) are loaded and structured into memory using PyArrow Tables.
2. **Parquet Cold Storage**: Data is flushed to `.parquet` files utilizing dictionary encoding and Snappy compression.
3. **DuckDB Direct Projection**: DuckDB queries and builds relational tables directly from the binary Parquet file using projection pushdowns:
   ```sql
   CREATE TABLE spotify_track_metrics AS 
   SELECT * FROM read_parquet('lakehouse_data/audio_features.parquet');
   ```
This architecture processes ingest and indexing pipelines under **1 second** even on large datasets.

---

## 🧬 Pydantic Data Fusion Engine

Rather than passing raw, unstructured text to language models, this system implements a strict **Pydantic Fusion Firewall** (`WebDataFusionEngine`). This firewall takes multi-source inputs (Discogs JSON, Apple Music catalogs, Spotify charts, MusicBrainz releases) and resolves:
* **Validated Artists**: Fuses artist collaborations into structured, unified strings.
* **Taxonomy & Genre Consensus**: Resolves conflicting genres using hierarchy rules (e.g., favoring specific iTunes electronic genres over broad Discogs categories).
* **ISRC Crossover**: Dynamically locates and binds the unique ISRC codes across tracks.

---

## 🧠 Neural A&R & Side-by-Side A/B Testing

Once the metadata and physical audio DSP metrics are fused, the pipeline evaluates the track's performance using local and cloud language models:
* **Context Injector**: The exact computed DSP characteristics (`dsp_rms`, `dsp_crest`, `dsp_sub`, `dsp_bass`, etc.) are structured alongside web performance metrics (popularity, listener counts, stream counts) and injected as pure variables into the prompts.
* **Local Node (Ollama)**: Evaluates the relationship between the physical mix (e.g., high crest factor, heavy sub-bass energy) and web streams offline using `gemma:2b`.
* **Cloud Node (Antigravity SDK / Google GenAI)**: Runs the identical context block against `gemini-3.5-flash` to evaluate local models vs. cloud reasoning capabilities side-by-side.

---

## 📁 Repository Directory Structure

```
├── ableton-session-intelligence/
│   ├── app/                         # FastAPI application backend
│   │   ├── api.py                   # REST endpoints exposing session data
│   │   ├── config.py                # Environment configuration using pydantic-settings
│   │   ├── database.py              # DuckDB database connectors and SQL executor
│   │   ├── extractor.py             # Binary ALS parser and gzip XML unpacker
│   │   ├── schemas.py               # Pydantic validation schemas
│   │   └── templates/               # Prompt templates directory
│   ├── exported_json/               # Raw DSP audio analysis exports (JSON formats)
│   ├── lakehouse_data/              # PyArrow Parquet cold storage layer
│   ├── lancedb_web_intel_rag/       # LanceDB vector database folder
│   ├── build_web_intel_notebook.py  # Python script to build the web intelligence notebook
│   ├── web_intel_pipeline.ipynb     # Interactive Jupyter notebook for the end-to-end pipeline
│   ├── master_batch.py              # Batch processing script for audio mastering
│   ├── main.py                      # Local web service launcher
│   ├── pyproject.toml               # Poetry/UV dependency configuration
│   └── requirements.txt             # Locked Python packages
```

---

## 🚀 Installation & Execution

### Prerequisites
* **Python 3.13+**
* **Ollama** running locally with the following models pulled:
  ```bash
  ollama pull gemma:2b
  ollama pull snowflake-arctic-embed:latest
  ```

### 1. Environment Setup
Clone the repository and set up a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory:
```env
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
GEMINI_API_KEY=your_gemini_api_key
```

### 3. Build the Pipeline Notebook
Generate the updated web intelligence notebook:
```bash
python build_web_intel_notebook.py
```

### 4. Execute the Pipeline In-Place
Execute the pipeline using `nbconvert` to run all cells (including data ingestion, Pydantic fusion, LanceDB writing, and local/cloud LLM analysis) and write outputs directly to the notebook:
```bash
jupyter nbconvert --to notebook --execute web_intel_pipeline.ipynb --inplace
```

---

## 🏗️ Professional Engineering Standards

*   **Continuous Integration**: GitHub Actions configuration (`.github/workflows/python-app.yml`) running automated test checks.
*   **Static Type Checking & Linting**: Strictly compliant with `mypy` and formatted via `ruff`.
*   **Pre-commit Validation**: Enforced via hooks in `.pre-commit-config.yaml` to ensure clean, PEP8 compliant code blocks before commits.
*   **Interoperability**: Completely compliant with Ableton Live files using native parsing libraries, requiring no external binary injection.
