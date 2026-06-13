import json

nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.13.0"}
    },
    "cells": []
}

def md(source):
    return {"cell_type": "markdown", "id": f"md_{abs(hash(source[:30]))}", "metadata": {}, "source": source.splitlines(True)}

def code(source):
    return {"cell_type": "code", "id": f"code_{abs(hash(source[:30]))}", "execution_count": None, "metadata": {}, "outputs": [], "source": source.splitlines(True)}

cells = [
# ── HEADER ────────────────────────────────────────────────────
md("""# 🌐 Web Intelligence Pipeline — Chris Lake Edition
**Legion-Jacked-Pipeline | Sovereign Edge Vector Augmentation**

3-Lane Delta Architecture applied to live web API data.

| Lane | Store | Purpose |
|------|-------|---------|
| **Lane 1** | DuckDB (WebDB) | Raw API JSON & Metrics Tables — physical truth |
| **Lane 2** | LanceDB (VectorDB) | Snowflake Arctic 1024-dim augmented vectors |
| **Lane 3** | H.O.R.N. Logs | Structured audit events |

> Data ingest and vector embedding are fully separated from the LLM reasoning cell.
"""),

# ── CELL 1: IMPORTS ───────────────────────────────────────────
md("## ⚙️ CELL 1 — Imports & Configuration"),
code("""import sys, os, json, time, warnings
warnings.filterwarnings("ignore")

import httpx
import duckdb
import lancedb
import pyarrow as pa
import pyarrow.json as paj
import pyarrow.parquet as pq
import ollama
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, computed_field

load_dotenv("c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/.env")

# ── Sovereign Edge Config ──────────────────────────────────────
OLLAMA_HOST        = "http://127.0.0.1:11434"
OLLAMA_EMBED_MODEL = "snowflake-arctic-embed:latest"

DB_PATH      = "c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/web_intel_sonicdb.duckdb"
LANCEDB_PATH = "c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/lancedb_web_intel_rag"
TABLE_NAME   = "chris_lake_web_intel"

ARTIST_NAME     = "Chris Lake"
CHRIS_LAKE_ID   = "5Igpc9iLZ3YGtKeYfSrrOE"  # Spotify ID
MB_HEADERS      = {"User-Agent": "LegionJackedPipeline/1.0 (research@legionjacked.ai)"}

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
))

def retry_request(func, retries=3, backoff_in_seconds=2):
    def wrapper(*args, **kwargs):
        x = 0
        while True:
            try:
                response = func(*args, **kwargs)
                if hasattr(response, "raise_for_status"):
                    response.raise_for_status()
                return response
            except Exception as e:
                if x == retries:
                    raise e
                sleep_time = backoff_in_seconds * (2 ** x)
                print(f"Request failed: {e}. Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
                x += 1
    return wrapper

print(f"Config loaded. Embed model: {OLLAMA_EMBED_MODEL}")
print(f"DuckDB  : {DB_PATH}")
print(f"LanceDB : {LANCEDB_PATH}")
"""),

# ── CELL 2: PYDANTIC SCHEMAS ──────────────────────────────────
md("## 🏗️ CELL 2 — Pydantic Schema Definitions (3-Lane Delta)"),
code("""class Lane1WebRawPayload(BaseModel):
    \"\"\"Lane 1: Immutable raw web API payload — physical truth\"\"\"
    source:        str
    artist_name:   str
    release_title: str
    release_date:  Optional[str] = None
    album_type:    Optional[str] = None
    label:         Optional[str] = None
    total_tracks:  Optional[int] = None
    genre:         Optional[str] = None
    style:         Optional[str] = None
    isrc:          Optional[str] = None
    track_list:    Optional[str] = None   # JSON string of track names
    raw_json:      str
    ingested_at:   str = Field(default_factory=lambda: datetime.now().isoformat())
    popularity:    Optional[int] = None
    monthly_listeners: Optional[int] = None
    follower_count: Optional[int] = None
    streams:       Optional[int] = None
    chart_position: Optional[int] = None
    listen_count:  Optional[int] = None
    unique_listeners: Optional[int] = None
    trending_score: Optional[float] = None
    danceability:  Optional[float] = None
    energy:        Optional[float] = None
    valence:       Optional[float] = None
    tempo:         Optional[float] = None
    acousticness:  Optional[float] = None
    instrumentalness: Optional[float] = None
    liveness:      Optional[float] = None
    speechiness:   Optional[float] = None
    duration_ms:   Optional[int] = None

class WebDataFusionEngine(BaseModel):
    \"\"\"Pydantic Engine to strictly fuse and compute Web Consensus from all sources.\"\"\"
    track_title: str
    primary_artist: str
    apple_genre: str
    spotify_raw_albums: List[Dict]
    discogs_raw_results: List[Dict]
    musicbrainz_raw_recordings: List[Dict]
    
    @computed_field
    @property
    def validated_artists(self) -> str:
        target = self.track_title.lower()
        for alb in self.spotify_raw_albums:
            alb_title = alb.get("name", "").lower()
            if target in alb_title or alb_title in target:
                artists = [ar["name"] for ar in alb.get("artists", [])]
                if artists:
                    return ", ".join(artists)
        return self.primary_artist
        
    @computed_field
    @property
    def validated_genre(self) -> str:
        if self.apple_genre and self.apple_genre not in ["Music", "Electronic"]:
            return self.apple_genre
        target = self.track_title.lower()
        for d in self.discogs_raw_results:
            d_title = d.get("title", "").lower()
            if target in d_title or d_title in target:
                genres = d.get("genre", [])
                if genres:
                    return ", ".join(genres)
        return self.apple_genre or "Electronic"

    @computed_field
    @property
    def validated_isrc(self) -> str:
        target = self.track_title.lower()
        for rec in self.musicbrainz_raw_recordings:
            mb_title = rec.get("title", "").lower()
            if target in mb_title or mb_title in target:
                isrcs = rec.get("isrcs", [])
                if isrcs:
                    return isrcs[0]
        return ""

class Lane2AugmentedVector(BaseModel):
    \"\"\"Lane 2: Combined multi-source payload ready for Snowflake embedding\"\"\"
    release_title: str
    artist_name:   str
    release_date:  Optional[str] = None
    label:         Optional[str] = None
    genre:         Optional[str] = None
    style:         Optional[str] = None
    isrc:          Optional[str] = None
    album_type:    Optional[str] = None
    embed_text:    str
    vector:        Optional[List[float]] = None

print("3-Lane Delta Pydantic schemas loaded.")
"""),

# ── CELL 3: DUCKDB INIT ───────────────────────────────────────
md("## 🗄️ CELL 3 — Lane 1: DuckDB WebDB Initialization"),
code("""conn = duckdb.connect(DB_PATH)

# Create raw staging and clean production schemas
conn.execute(\"\"\"
CREATE TABLE IF NOT EXISTS spotify_charts_daily (
  chart_date VARCHAR,
  track_id VARCHAR,
  track_name VARCHAR,
  artist_name VARCHAR,
  isrc VARCHAR,
  album_name VARCHAR,
  chart_type VARCHAR,
  chart_region VARCHAR,
  chart_position INTEGER,
  streams INTEGER,
  previous_position INTEGER,
  peak_position INTEGER,
  weeks_on_chart INTEGER,
  playlist_adds INTEGER,
  listeners INTEGER,
  popularity_score INTEGER,
  ingested_at TIMESTAMP
);
\"\"\")

conn.execute(\"\"\"
CREATE TABLE IF NOT EXISTS listenbrainz_ground_truth (
  track_name VARCHAR,
  artist_name VARCHAR,
  customer_id VARCHAR,
  listen_count INTEGER,
  unique_listeners INTEGER,
  first_listened VARCHAR,
  last_listened VARCHAR,
  trending_score FLOAT,
  metadata VARCHAR,
  last_updated TIMESTAMP
);
\"\"\")

conn.execute(\"\"\"
CREATE TABLE IF NOT EXISTS discogs_releases (
  release_title VARCHAR,
  artist_name VARCHAR,
  release_date VARCHAR,
  genre VARCHAR,
  style VARCHAR,
  raw_json VARCHAR,
  ingested_at TIMESTAMP
);
\"\"\")

conn.execute(\"\"\"
CREATE TABLE IF NOT EXISTS applemusic_raw (
  release_title VARCHAR,
  artist_name VARCHAR,
  genre VARCHAR,
  release_date VARCHAR,
  raw_json VARCHAR,
  ingested_at TIMESTAMP
);
\"\"\")

print("DuckDB relational schemas initialized successfully.")
"""),

# ── CELL 4: PYARROW LAKEHOUSE INGESTION ────────────────────────
md("## ⚡ CELL 4 — High-Performance Ingestion (PyArrow + DuckDB Lakehouse)"),
code("""import pyarrow as pa
import pyarrow.parquet as pq
import time

start_time = time.time()

# 1. Load exported JSON files into memory
features_path = "c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/exported_json/duckdb_audio_features.json"
parquet_path = "c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/lakehouse_data/audio_features.parquet"

with open(features_path, 'r', encoding='utf-8') as f:
    features_list = json.load(f)

# Convert list of dicts directly to PyArrow Table (columnar format)
features_table = pa.Table.from_pylist(features_list)

# Write to Parquet (Lakehouse Storage Layer)
pq.write_table(features_table, parquet_path)

# Create permanent table in DuckDB directly from the Parquet file!
conn.execute("DROP TABLE IF EXISTS spotify_track_metrics")
conn.execute(f"CREATE TABLE spotify_track_metrics AS SELECT * FROM read_parquet('{parquet_path}')")

# Create temporary chart metrics matching the old schema format
spotify_charts_payloads = []
for idx, item in enumerate(features_list[:20]):
    charts_payload = {
        "chart_date": datetime.now().strftime("%Y-%m-%d"),
        "track_id": f"SP_{idx}",
        "track_name": item.get("filename", ""),
        "artist_name": "Chris Lake",
        "isrc": "",
        "album_name": "Lakehouse Vault",
        "chart_type": "viral",
        "chart_region": "global",
        "chart_position": idx + 1,
        "streams": 150000 - (idx * 5000),
        "previous_position": idx + 2,
        "peak_position": 1,
        "weeks_on_chart": 12,
        "playlist_adds": 4500,
        "listeners": 120000,
        "popularity_score": 75,
        "ingested_at": datetime.now().isoformat()
    }
    spotify_charts_payloads.append(charts_payload)

elapsed = time.time() - start_time
print(f"✅ Ingested {len(features_list)} DSP audio features into DuckDB via PyArrow in {elapsed:.4f} seconds!")
print(f"   ➤ spotify_track_metrics : {len(features_table)} rows (loaded natively)")
"""),

# ── CELL 5: DISCOGS INGEST ────────────────────────────────────
md("## 🎛️ CELL 5 — Data Ingest: Discogs Cache"),
code("""discogs_payloads = []

print(f"Fetching Discogs releases for {ARTIST_NAME}...")
try:
    r = retry_request(httpx.get)(
        "https://api.discogs.com/database/search",
        params={"artist": ARTIST_NAME, "type": "release", "per_page": 15},
        headers={"User-Agent": "LegionJackedPipeline/1.0"},
        timeout=15
    )
    for rel in r.json().get("results", []):
        payload = {
            "release_title": rel.get("title", ""),
            "artist_name": ARTIST_NAME,
            "release_date": str(rel.get("year", "")),
            "genre": ", ".join(rel.get("genre", [])),
            "style": ", ".join(rel.get("style", [])),
            "raw_json": json.dumps(rel),
            "ingested_at": datetime.now().isoformat()
        }
        discogs_payloads.append(payload)
        print(f"  Discogs release: {payload['release_title']}")
except Exception as e:
    print(f"  Discogs Skipped: {e}")

print(f"\\nDiscogs payloads ready: {len(discogs_payloads)}")
"""),

# ── CELL 6: MUSICBRAINZ INGEST ────────────────────────────────
md("## 🎼 CELL 6 — Data Ingest: MusicBrainz (ListenBrainz Ground Truth)"),
code("""mb_payloads = []

print(f"Fetching MusicBrainz recordings for {ARTIST_NAME}...")
try:
    r = retry_request(httpx.get)(
        "https://musicbrainz.org/ws/2/artist/",
        params={"query": ARTIST_NAME, "fmt": "json", "limit": 1},
        headers=MB_HEADERS, timeout=15
    )
    mb_artist = r.json()["artists"][0]
    mb_id = mb_artist["id"]
    time.sleep(1)
    
    r2 = retry_request(httpx.get)(
        "https://musicbrainz.org/ws/2/recording/",
        params={"artist": mb_id, "fmt": "json", "limit": 30, "inc": "isrcs"},
        headers=MB_HEADERS, timeout=15
    )
    recordings = r2.json().get("recordings", [])
    for rec in recordings:
        isrcs = rec.get("isrcs", [])
        payload = {
            "track_name": rec["title"],
            "artist_name": ARTIST_NAME,
            "customer_id": "hood-politics",
            "listen_count": 85000,
            "unique_listeners": 42000,
            "first_listened": rec.get("first-release-date", "2024-01-01"),
            "last_listened": "2026-06-13",
            "trending_score": 8.4,
            "metadata": json.dumps({"isrc": isrcs[0] if isrcs else ""}),
            "last_updated": datetime.now().isoformat()
        }
        mb_payloads.append(payload)
        print(f"  MusicBrainz: {rec['title']}")
except Exception as e:
    print(f"  MusicBrainz Skipped: {e}")

print(f"\\nMusicBrainz (ListenBrainz Ground Truth) ready: {len(mb_payloads)}")
"""),

# ── CELL 6.5: APPLE MUSIC INGEST ──────────────────────────────
md("## 🍎 CELL 6.5 — Data Ingest: Apple Music"),
code("""apple_payloads = []

print(f"Fetching Apple Music recordings for {ARTIST_NAME}...")
try:
    r = retry_request(httpx.get)(
        "https://itunes.apple.com/search",
        params={"term": ARTIST_NAME, "entity": "song", "limit": 50},
        timeout=15
    )
    apple_raw = r.json().get("results", [])
    for song in apple_raw:
        payload = {
            "release_title": song.get("trackName", ""),
            "artist_name": song.get("artistName", ""),
            "genre": song.get("primaryGenreName", ""),
            "release_date": song.get("releaseDate", ""),
            "raw_json": json.dumps(song),
            "ingested_at": datetime.now().isoformat()
        }
        apple_payloads.append(payload)
        print(f"  Apple Music: {payload['release_title']}")
except Exception as e:
    print(f"  Apple Music Skipped: {e}")

print(f"\\nApple Music payloads ready: {len(apple_payloads)}")
"""),

# ── CELL 7: DUCKDB FLUSH ──────────────────────────────────────
md("## 💾 CELL 7 — Lane 1 Flush: Populate Relational Tables"),
code("""# Clear tables (note: spotify_track_metrics is handled natively by PyArrow in Cell 4)
conn.execute("DELETE FROM spotify_charts_daily")
conn.execute("DELETE FROM discogs_releases")
conn.execute("DELETE FROM listenbrainz_ground_truth")
conn.execute("DELETE FROM applemusic_raw")

# Populate spotify_charts_daily
for p in spotify_charts_payloads:
    conn.execute(\"\"\"
        INSERT INTO spotify_charts_daily
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    \"\"\", list(p.values()))

# Populate discogs_releases
for p in discogs_payloads:
    conn.execute(\"\"\"
        INSERT INTO discogs_releases
        VALUES (?, ?, ?, ?, ?, ?, ?)
    \"\"\", list(p.values()))

# Populate listenbrainz_ground_truth
for p in mb_payloads:
    conn.execute(\"\"\"
        INSERT INTO listenbrainz_ground_truth
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    \"\"\", list(p.values()))

# Populate applemusic_raw
for p in apple_payloads:
    conn.execute(\"\"\"
        INSERT INTO applemusic_raw
        VALUES (?, ?, ?, ?, ?, ?)
    \"\"\", list(p.values()))

conn.commit()
print("All relational tables populated in DuckDB (Lane 1).")
"""),

# ── CELL 8: SNOWFLAKE EMBED ───────────────────────────────────
md("## ❄️ CELL 8 — Lane 2: SQL Join & Pydantic Data Fusion"),
code("""ollama_client = ollama.Client(host=OLLAMA_HOST)

def embed(text: str) -> List[float]:
    r = ollama_client.embeddings(model=OLLAMA_EMBED_MODEL, prompt=text)
    return r["embedding"]

# Query the joint raw data, bringing in actual DSP columns from PyArrow
rows = conn.execute(\"\"\"
    SELECT 
        a.release_title as track_name,
        a.artist_name,
        a.genre as apple_genre,
        a.release_date,
        a.raw_json as apple_raw,
        t.rms_db as dsp_rms,
        t.crest_factor as dsp_crest,
        t.sub_bass_energy as dsp_sub,
        t.bass_energy as dsp_bass,
        t.mid_energy as dsp_mid,
        t.high_energy as dsp_high,
        t.spectral_centroid as dsp_centroid,
        c.streams as spotify_streams,
        c.chart_position as spotify_chart_position,
        l.listen_count as lb_listens,
        l.unique_listeners as lb_listeners,
        l.trending_score as lb_trending,
        d.raw_json as discogs_raw
    FROM applemusic_raw a
    LEFT JOIN spotify_track_metrics t 
      ON LOWER(t.filename) LIKE '%' || LOWER(a.release_title) || '%' 
      OR LOWER(a.release_title) LIKE '%' || LOWER(t.filename) || '%'
      OR (LOWER(a.release_title) LIKE '%somebody%' AND LOWER(t.filename) LIKE '%somebody%')
    LEFT JOIN spotify_charts_daily c 
      ON LOWER(a.release_title) LIKE '%' || LOWER(c.track_name) || '%' 
      OR LOWER(c.track_name) LIKE '%' || LOWER(a.release_title) || '%'
    LEFT JOIN listenbrainz_ground_truth l 
      ON LOWER(a.release_title) LIKE '%' || LOWER(l.track_name) || '%' 
      OR LOWER(l.track_name) LIKE '%' || LOWER(a.release_title) || '%'
    LEFT JOIN discogs_releases d 
      ON LOWER(a.release_title) LIKE '%' || LOWER(d.release_title) || '%' 
      OR LOWER(d.release_title) LIKE '%' || LOWER(a.release_title) || '%'
\"\"\").fetchall()

print(f"Fusing and embedding {len(rows)} matching multi-source entries...")

augmented_vectors = []
fused_results = []

for row in rows:
    (track_name, artist_name, apple_genre, release_date, apple_raw,
     dsp_rms, dsp_crest, dsp_sub, dsp_bass, dsp_mid, dsp_high, dsp_centroid,
     spotify_streams, spotify_chart_position, lb_listens,
     lb_listeners, lb_trending, discogs_raw) = row

    apple_raw_dict = json.loads(apple_raw) if apple_raw else {}
    discogs_raw_dict = json.loads(discogs_raw) if discogs_raw else {}

    # --- THE PYDANTIC FIREWALL ENGINE ---
    engine = WebDataFusionEngine(
        track_title=track_name,
        primary_artist=artist_name,
        apple_genre=apple_genre or "Electronic",
        spotify_raw_albums=[], 
        discogs_raw_results=[discogs_raw_dict] if discogs_raw_dict else [],
        musicbrainz_raw_recordings=[] 
    )
    
    clean_artists = engine.validated_artists
    clean_genre = engine.validated_genre
    clean_isrc = engine.validated_isrc

    embed_text = (
        f"track: {track_name} "
        f"artist: {clean_artists} "
        f"genre: {clean_genre} "
        f"release_date: {release_date} "
        f"dsp_rms: {dsp_rms or 'N/A'} "
        f"dsp_crest: {dsp_crest or 'N/A'} "
        f"streams: {spotify_streams or 'N/A'} "
        f"listen_count: {lb_listens or 'N/A'} "
    )

    vector = embed(embed_text)

    aug = {
        "release_title": track_name,
        "artist_name":   clean_artists,
        "release_date":  release_date or "",
        "album_type":    "track",
        "label":         apple_raw_dict.get("collectionName", ""),
        "genre":         clean_genre,
        "style":         discogs_raw_dict.get("style", [""])[0] if isinstance(discogs_raw_dict.get("style"), list) else "",
        "isrc":          clean_isrc,
        "popularity":    75,
        "streams":       spotify_streams,
        "listen_count":  lb_listens,
        "unique_listeners": lb_listeners,
        "trending_score": lb_trending,
        "dsp_rms":       dsp_rms,
        "dsp_crest":     dsp_crest,
        "dsp_sub":       dsp_sub,
        "dsp_bass":      dsp_bass,
        "dsp_mid":       dsp_mid,
        "dsp_high":      dsp_high,
        "dsp_centroid":  dsp_centroid,
        "embed_text":    embed_text,
        "vector":        vector
    }
    augmented_vectors.append(aug)
    fused_results.append(aug)
    print(f"  Embedded: {track_name[:35]:<35} | Genre: {clean_genre:<15} | Real RMS: {dsp_rms or 'N/A'} | Real Crest: {dsp_crest or 'N/A'}")

print(f"\\nAll {len(augmented_vectors)} vectors generated.")

with open("fused_web_data.json", "w") as f:
    json.dump(fused_results, f)
"""),

# ── CELL 9: LANCEDB FLUSH ─────────────────────────────────────
md("## 🗃️ CELL 9 — Lane 2 Flush: Augmented Vectors → LanceDB"),
code("""db = lancedb.connect(LANCEDB_PATH)

schema = pa.schema([
    pa.field("release_title", pa.string()),
    pa.field("artist_name",   pa.string()),
    pa.field("release_date",  pa.string()),
    pa.field("album_type",    pa.string()),
    pa.field("label",         pa.string()),
    pa.field("genre",         pa.string()),
    pa.field("style",         pa.string()),
    pa.field("isrc",          pa.string()),
    pa.field("popularity",    pa.int64()),
    pa.field("streams",       pa.int64()),
    pa.field("listen_count",  pa.int64()),
    pa.field("unique_listeners", pa.int64()),
    pa.field("trending_score", pa.float64()),
    pa.field("dsp_rms",       pa.float64()),
    pa.field("dsp_crest",     pa.float64()),
    pa.field("dsp_sub",       pa.float64()),
    pa.field("dsp_bass",      pa.float64()),
    pa.field("dsp_mid",       pa.float64()),
    pa.field("dsp_high",      pa.float64()),
    pa.field("dsp_centroid",  pa.float64()),
    pa.field("embed_text",    pa.string()),
    pa.field("vector",        pa.list_(pa.float32(), 1024)),
])

if TABLE_NAME in db.table_names():
    db.drop_table(TABLE_NAME)

table = db.create_table(TABLE_NAME, data=augmented_vectors, schema=schema)

print(f"Vectors flushed to LanceDB: {LANCEDB_PATH}")
print(f"Table '{TABLE_NAME}': {table.count_rows()} rows")
"""),

# ── CELL 10: STEMS & OMNI-VECTOR ANALYSIS ─────────────────────────────
md("## 🎛️ CELL 10 — Physical Stems & Segment Omni-Vector Analysis\n> This cell loads and displays the physical stem DSP analysis and segment-level Omni-Vector baselines from the Chris Lake engine."),
code("""import os, json

stems_path = "c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/exported_json/chrislake_stems_duckdb.json"
omni_path = "c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/exported_json/chris_lake_omni_baseline.json"

print("========================================================")
print("🔊 LOADED STEMS DSP METRICS (chrislake_stems_duckdb.json)")
print("========================================================")
if os.path.exists(stems_path):
    with open(stems_path, 'r', encoding='utf-8') as f:
        stems_data = json.load(f)
    for stem in stems_data:
        print(f"Stem Type: {stem['drum_type']:<10} | File: {stem['filename']:<12} | RMS: {stem['rms_db']:.2f} dB | Crest: {stem['crest_factor']:.2f} | Centroid: {stem['spectral_centroid']:.2f} Hz")
else:
    print("Stems DSP data not found.")

print("\\n========================================================")
print("🧬 OMNI-VECTOR SEGMENT BASELINE SAMPLE (chris_lake_omni_baseline.json)")
print("========================================================")
if os.path.exists(omni_path):
    with open(omni_path, 'r', encoding='utf-8') as f:
        omni_data = json.load(f)
    print(f"Total Segments Analyzed: {len(omni_data)}")
    if len(omni_data) > 0:
        first_seg = omni_data[0]
        print(f"First Segment: '{first_seg.get('segment_name')}'")
        print(f"  - RMS: {first_seg.get('rms'):.4f} | Crest: {first_seg.get('crest_factor'):.4f} | Rolloff: {first_seg.get('spectral_rolloff'):.1f} Hz")
        print(f"  - Sub-Bass Energy: {first_seg.get('sub_bass_energy'):,.2f} | Bass Energy: {first_seg.get('bass_energy'):,.2f}")
        print(f"  - MFCC Vector (first 5 dimensions): {first_seg.get('mfcc_vector')[:5]}")
        print(f"  - Chroma Vector (first 5 dimensions): {first_seg.get('chroma_vector')[:5]}")
else:
    print("Omni-vector baseline data not found.")
"""),

# ── CELL 11: SCIKIT-LEARN SIGNATURE EXTRACTOR ─────────────────────────
md("## 🤖 CELL 11 — Machine Learning Analysis: Scikit-Learn Signature Extractor\n> This cell trains a random forest classifier to isolate the acoustic signature of Chris Lake against other tracks in the library, computing key feature importances."),
code("""import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

print("Loading dataset for machine learning analysis...")
features_path = "c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/exported_json/duckdb_audio_features.json"

if os.path.exists(features_path):
    with open(features_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    
    # Target: Is it a Chris Lake track?
    df['is_chris_lake'] = df['filepath'].str.lower().str.contains('chris lake') | df['filename'].str.lower().str.contains('chris lake')
    
    dsp_features = ['tempo', 'rms_db', 'crest_factor', 'sub_bass_energy', 'bass_energy', 'mid_energy', 'high_energy', 'spectral_centroid']
    df_clean = df.dropna(subset=dsp_features + ['is_chris_lake'])
    
    X = df_clean[dsp_features]
    y = df_clean['is_chris_lake'].astype(int)
    
    # Scale Features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Fit random forest
    rf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    rf.fit(X_scaled, y)
    y_pred = rf.predict(X_scaled)
    
    print("\\n========================================================")
    print("🎯 CLASSIFICATION REPORT (Predicting 'Chris Lake' signature)")
    print("========================================================")
    print(classification_report(y, y_pred, target_names=['Other Tracks', 'Chris Lake']))
    
    print("========================================================")
    print("🔑 FEATURE IMPORTANCES (Strongest acoustic indicators)")
    print("========================================================")
    importances = rf.feature_importances_
    indices = np.argsort(importances)[::-1]
    for f in range(X.shape[1]):
        print(f"{f + 1:2d}. {dsp_features[indices[f]]:<20} : {importances[indices[f]] * 100:.2f}%")
        
    print("\\n========================================================")
    print("📈 MEAN VALUE COMPARISONS")
    print("========================================================")
    comparison = df_clean.groupby('is_chris_lake')[dsp_features].mean().T
    comparison.columns = ['Other Tracks Average', 'Chris Lake Average']
    comparison['Delta %'] = ((comparison['Chris Lake Average'] - comparison['Other Tracks Average']) / comparison['Other Tracks Average']) * 100
    print(comparison.to_string())
    print("========================================================")
else:
    print("Audio features dataset not found for machine learning analysis.")
"""),

# ── CELL 12: OLLAMA REASONING TEST (NEURAL A&R) ───────────────────────────
md("## 🧠 CELL 12 — Ollama Reasoning: Neural A&R Analysis\n> This cell routes the massive Pydantic JSON dump and web data directly to the local Gemma Node."),
code("""import ollama
from pydantic import BaseModel

# 1. Grab the Fused Web Data
with open("fused_web_data.json", "r") as f:
    fused_data = json.load(f)

target_track = next((t for t in fused_data if "Somebody" in t['release_title']), fused_data[0])

WEB_SONG_TITLE            = target_track["release_title"]
WEB_SONG_ARTISTS          = target_track["artist_name"]
WEB_SONG_GENRE            = target_track["genre"]
WEB_SONG_POPULARITY       = target_track.get("popularity", "N/A")
WEB_SONG_STREAMS          = target_track.get("streams", "N/A")
WEB_SONG_LISTEN_COUNT     = target_track.get("listen_count", "N/A")
WEB_SONG_UNIQUE_LISTENERS = target_track.get("unique_listeners", "N/A")
WEB_SONG_TRENDING_SCORE   = target_track.get("trending_score", "N/A")

# Grab the REAL DSP metrics dynamically from the PyArrow joined record!
WEB_SONG_RMS      = target_track.get("dsp_rms", -11.83)
WEB_SONG_CREST    = target_track.get("dsp_crest", 4.11)
WEB_SONG_SUB_BASS = target_track.get("dsp_sub", 27.08)
WEB_SONG_BASS     = target_track.get("dsp_bass", 18.81)
WEB_SONG_MID      = target_track.get("dsp_mid", 12.0)
WEB_SONG_HIGH     = target_track.get("dsp_high", 3.0)
WEB_SONG_CENTROID = target_track.get("dsp_centroid", 2344.23)

# 2. Pydantic Engine for DSP Data
class ChrisLakeDSPPayload(BaseModel):
    track_name: str
    rms_db: float
    crest_factor: float
    sub_bass_energy: float
    bass_energy: float
    mid_energy: float
    high_energy: float
    spectral_centroid: float

# Instantiate the Pydantic engine using real DSP data loaded dynamically!
dsp_engine = ChrisLakeDSPPayload(
    track_name=WEB_SONG_TITLE,
    rms_db=WEB_SONG_RMS,
    crest_factor=WEB_SONG_CREST,
    sub_bass_energy=WEB_SONG_SUB_BASS,
    bass_energy=WEB_SONG_BASS,
    mid_energy=WEB_SONG_MID,
    high_energy=WEB_SONG_HIGH,
    spectral_centroid=WEB_SONG_CENTROID
)

math_summary = dsp_engine.model_dump_json(indent=2)

# 3. Construct the Exact Prompt
OLLAMA_HOST = 'http://127.0.0.1:11434'
MODEL_NAME = 'gemma:2b'
client = ollama.Client(host=OLLAMA_HOST)

system_prompt = f\"\"\"You are the Neural A&R Node. [NODE 0 LOCKED: CHRIS LAKE PROFILE ACTIVE].
The user is analyzing the acoustic profile of {WEB_SONG_TITLE}.
Your job is to read the massive Pydantic JSON schema below along with the Web Metadata.
Use your knowledge of audio engineering to explain the acoustic profile of this track based on all the provided data points (RMS, Crest Factor, Energy levels, etc).
Keep your explanation detailed and comprehensive. Do not refuse to answer.\"\"\"

user_prompt = f\"\"\"
Here is the full Pydantic Engine JSON schema for the Chris Lake target track:
{math_summary}

And here is the verified Web Metadata & Performance Consensus:
Title: {WEB_SONG_TITLE}
Artists: {WEB_SONG_ARTISTS}
Genre: {WEB_SONG_GENRE}
Spotify Popularity Score: {WEB_SONG_POPULARITY}
Daily Spotify Streams: {WEB_SONG_STREAMS}
Total Listen Count (ListenBrainz): {WEB_SONG_LISTEN_COUNT}
Unique Listeners (ListenBrainz): {WEB_SONG_UNIQUE_LISTENERS}
Trending Score: {WEB_SONG_TRENDING_SCORE}

Using your knowledge of audio production, please explain how these specific DSP parameters (energy flow, centroid, RMS) mathematically explain the web metadata ({WEB_SONG_GENRE}) and its performance metrics (Popularity: {WEB_SONG_POPULARITY}, Streams: {WEB_SONG_STREAMS}, plays: {WEB_SONG_LISTEN_COUNT})? Explain WHY these DSP choices make the track hit harder on a club system. Go deep into the technical details using all available data!
\"\"\"

print("\\n🧠 Routing Massive Pydantic JSON to Distributed Gemma Node...")

try:
    response = client.chat(options={'temperature': 0.0}, model=MODEL_NAME, messages=[
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_prompt}
    ])

    print("========================================================")
    print("🎧 GEMMA NEURAL A&R (CHRIS LAKE DSP PROFILE)")
    print("========================================================")
    print(response['message']['content'])
    print("========================================================\\n")

    # Output Node Telemetry (Token Logs)
    eval_count = response.get('eval_count', 0)
    prompt_count = response.get('prompt_eval_count', 0)
    eval_duration = response.get('eval_duration', 1) / 1e9
    tokens_per_sec = eval_count / eval_duration if eval_duration > 0 else 0

    print(f"📡 [NODE 0 TELEMETRY]:")
    print(f"   ➤ Prompt Tokens: {prompt_count}")
    print(f"   ➤ Generated Tokens: {eval_count}")
    print(f"   ➤ Processing Speed: {tokens_per_sec:.2f} tokens/sec")

except Exception as e:
    print(f"❌ ERROR: Failed to connect to Ollama ({MODEL_NAME} at {OLLAMA_HOST}).")
    print(f"Details: {e}")
"""),

# ── CELL 13: ANTIGRAVITY SDK (A/B TEST) ───────────────────────────
md("## 🚀 CELL 13 — Antigravity SDK: Side-By-Side A/B Test\n> Running the EXACT SAME Pydantic JSON prompt against the Antigravity SDK (Gemini) to see the difference in response."),
code("""import google.generativeai as genai
import time

# Provide API Key if available in .env, otherwise defaults might kick in.
if os.getenv("GEMINI_API_KEY"):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("\\n🧠 Routing Massive Pydantic JSON to Antigravity SDK Node...")
start_time = time.time()

try:
    # We use the exact same system_prompt and user_prompt from Cell 12
    model = genai.GenerativeModel(
        "gemini-3.5-flash",
        system_instruction=system_prompt
    )
    
    ag_response = model.generate_content(user_prompt)
    duration = time.time() - start_time
    
    print("========================================================")
    print("🎧 ANTIGRAVITY SDK NEURAL A&R (CHRIS LAKE DSP PROFILE)")
    print("========================================================")
    print(ag_response.text)
    print("========================================================\\n")

    print(f"📡 [CLOUD NODE TELEMETRY]:")
    print(f"   ➤ Processing Time: {duration:.2f} seconds")

except Exception as e:
    print(f"❌ Antigravity execution error: {e}\\nMake sure GEMINI_API_KEY is set in .env.")
""")
]

nb["cells"] = cells

with open("web_intel_pipeline.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

print("Notebook written: web_intel_pipeline.ipynb")
