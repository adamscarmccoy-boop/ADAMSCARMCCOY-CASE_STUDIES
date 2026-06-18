# Lead Assessment Framework

This framework defines the baseline capabilities, architectural strengths, and project preferences for evaluating incoming contract work or leads.

## Core Strengths & Capabilities (The H.O.R.N. Stack)

1.  **Metadata Fusion (Pydantic Fusion Firewall)**
    *   Ability to ingest, standardize, and resolve conflicts from multi-source APIs (Spotify, MusicBrainz, Apple Music, Discogs).
    *   Strong focus on deterministic consensus (e.g., ISRC binding, taxonomy resolution).

2.  **3-Lane Delta Architecture (Lakehouse & VectorDB)**
    *   **Lane 1 (Relational):** High-performance PyArrow and Parquet ingestion into DuckDB. Ideal for physical metrics (audio DSP characteristics) and massive datasets.
    *   **Lane 2 (Vector):** LanceDB with 1024-dimensional embeddings (e.g., Snowflake Arctic) for complex semantic search and metadata filtering.
    *   **Lane 3 (Audit):** Relational tracking of execution metrics and state logs.

3.  **Hardware-Optimized Local Intelligence (Offline LLMs)**
    *   Zero-egress, 100% data privacy workflows using local hardware (e.g., Ollama with models like `gemma:2b`, `phi3`).
    *   Neural A&R profiling: Evaluating relationships between physical audio attributes and web metrics without cloud round-trips.
    *   Integration of DuckDB analytics tightly coupled with local LLM routing (e.g., Phi-3 engines).

4.  **Cloud A/B Testing Capabilities**
    *   Side-by-side comparison of local models vs. cloud-grade models (e.g., Google Gemini via Antigravity SDK).

5.  **Native File Extraction & API Engineering**
    *   Expertise in binary ALS parsing and gzip XML unpacking for direct Ableton Live session data extraction.
    *   Building high-performance APIs (e.g., FastAPI) to serve forensic-grade audio/session intelligence layers.

## Contract Preferences

*   **Duration:** Preference for shorter, highly-detailed work (e.g., 4-5 week turnarounds). Efficiency creates future margin.
*   **Budget:** Comfortable with established budgets (e.g., $6.5K - $8K range for a 4-5 week sprint). Look for headroom as a sign of a serious client.
*   **Scope Pattern Match:** High fit for projects requiring metadata consolidation, local audio/DSP analysis, and local reasoning pipelines.
*   **Client Profile:** Technical clients who understand data architecture (lakehouse, vector DBs) and value privacy/local execution.

## Evaluation Criteria (Risk Flags)

*   **Data Quality:** Lack of mention regarding data quality or cleaning requires an immediate 10% timeline buffer.
*   **Timeline Padding:** Generous timelines (e.g., 8 weeks for a 4-week scope) are ideal buffer rooms.
*   **Scope Creep:** Always reserve a portion of the budget/timeline for potential scope creep ($1K-$1.5K buffer).
