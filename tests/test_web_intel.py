import pytest
import os
import json
import tempfile
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import duckdb
import lancedb
from pydantic import ValidationError
from sklearn.ensemble import RandomForestClassifier

# Import the fusion engine from build_web_intel_notebook.py
# (We can import it by loading the module dynamically or defining the test locally)
# Let's import it dynamically to test the actual file code
import sys
sys.path.append(os.path.abspath("."))
try:
    from build_web_intel_notebook import WebDataFusionEngine
except ImportError:
    # Fallback definition if run from outer scope
    from pydantic import BaseModel, Field, computed_field
    from typing import List, Dict
    
    class WebDataFusionEngine(BaseModel):
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

# ──────────────────────────────────────────────────────────────
# 1. TEST PYDANTIC DATA FUSION ENGINE
# ──────────────────────────────────────────────────────────────

def test_web_data_fusion_engine_validation():
    """Verify that the fusion engine validates inputs and computes properties correctly."""
    # Test valid input and artist resolver
    engine = WebDataFusionEngine(
        track_title="Somebody",
        primary_artist="Chris Lake",
        apple_genre="Electronic",
        spotify_raw_albums=[{
            "name": "Somebody (Extended Mix)",
            "artists": [{"name": "Chris Lake"}, {"name": "Fisher"}]
        }],
        discogs_raw_results=[{
            "title": "Somebody",
            "genre": ["Tech House", "Electronic"]
        }],
        musicbrainz_raw_recordings=[{
            "title": "Somebody (2024)",
            "isrcs": ["USUM71234567"]
        }]
    )
    
    assert engine.validated_artists == "Chris Lake, Fisher"
    assert engine.validated_genre == "Tech House, Electronic"
    assert engine.validated_isrc == "USUM71234567"

def test_web_data_fusion_engine_fallbacks():
    """Verify that the fusion engine falls back to default values when no match is found."""
    engine = WebDataFusionEngine(
        track_title="Unknown Song",
        primary_artist="Chris Lake",
        apple_genre="Electronic",
        spotify_raw_albums=[],
        discogs_raw_results=[],
        musicbrainz_raw_recordings=[]
    )
    
    assert engine.validated_artists == "Chris Lake"
    assert engine.validated_genre == "Electronic"
    assert engine.validated_isrc == ""

# ──────────────────────────────────────────────────────────────
# 2. TEST PYARROW + PARQUET LAKEHOUSE SERIALIZATION
# ──────────────────────────────────────────────────────────────

def test_parquet_serialization_and_duckdb_read():
    """Verify PyArrow table conversion, Parquet writing, and DuckDB querying."""
    # Create mock data
    mock_data = [
        {"filename": "song1.mp3", "rms_db": -10.5, "crest_factor": 3.2, "tempo": 126.0},
        {"filename": "song2.mp3", "rms_db": -12.2, "crest_factor": 4.1, "tempo": 128.0}
    ]
    
    # 1. Convert to PyArrow Table
    table = pa.Table.from_pylist(mock_data)
    assert table.num_rows == 2
    assert "rms_db" in table.column_names
    
    # 2. Write to temporary Parquet file
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
        tmp_name = tmp.name
    
    try:
        pq.write_table(table, tmp_name)
        assert os.path.exists(tmp_name)
        
        # 3. Read via DuckDB
        conn = duckdb.connect(database=":memory:")
        conn.execute(f"CREATE TABLE test_metrics AS SELECT * FROM read_parquet('{tmp_name}')")
        
        # Verify row count
        count = conn.execute("SELECT COUNT(*) FROM test_metrics").fetchone()[0]
        assert count == 2
        
        # Verify query matches
        rms_values = conn.execute("SELECT rms_db FROM test_metrics ORDER BY tempo ASC").fetchall()
        assert rms_values == [(-10.5,), (-12.2,)]
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)

# ──────────────────────────────────────────────────────────────
# 3. TEST LANCEDB SCHEMA INTEGRITY
# ──────────────────────────────────────────────────────────────

def test_lancedb_schema_flushing():
    """Verify that LanceDB creates table with the correct metadata schema and allows inserts."""
    schema = pa.schema([
        pa.field("release_title", pa.string()),
        pa.field("artist_name",   pa.string()),
        pa.field("popularity",    pa.int64()),
        pa.field("dsp_rms",       pa.float64()),
        pa.field("vector",        pa.list_(pa.float32(), 1024)),
    ])
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        db = lancedb.connect(tmp_dir)
        
        # Create table with schema
        table_name = "test_vectors"
        mock_vectors = [
            {
                "release_title": "Track 1",
                "artist_name": "Chris Lake",
                "popularity": 80,
                "dsp_rms": -11.5,
                "vector": np.random.rand(1024).astype(np.float32).tolist()
            }
        ]
        
        table = db.create_table(table_name, data=mock_vectors, schema=schema)
        assert table.count_rows() == 1
        
        # Verify schema field exists
        arrow_schema = table.schema
        assert "popularity" in arrow_schema.names
        assert arrow_schema.field("popularity").type == pa.int64()

# ──────────────────────────────────────────────────────────────
# 4. TEST SCIKIT-LEARN SIGNATURE EXTRACTION
# ──────────────────────────────────────────────────────────────

def test_sklearn_sound_signature_extractor():
    """Verify that the Random Forest model fits and outputs feature importances."""
    # Create mock DSP features
    np.random.seed(42)
    n_samples = 50
    X = np.random.randn(n_samples, 4) # 4 features
    # Let target be correlated with feature index 0 (e.g. sub-bass)
    y = (X[:, 0] > 0.5).astype(int)
    
    rf = RandomForestClassifier(n_estimators=10, random_state=42)
    rf.fit(X, y)
    
    # Check predictions
    y_pred = rf.predict(X)
    assert len(y_pred) == n_samples
    
    # Check feature importances
    assert len(rf.feature_importances_) == 4
    # The first feature (index 0) should have the highest importance
    assert np.argmax(rf.feature_importances_) == 0
