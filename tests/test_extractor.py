import pytest

from app.schemas import Lane1DuckDBAnalytics


def test_duckdb_analytics_schema():
    """Verify that the Lane1DuckDBAnalytics Pydantic model enforces required fields correctly."""
    feature = Lane1DuckDBAnalytics(
        table_source="parquet_partition_1",
        processed_row_count=1500,
        anomalous_metric_detected=False,
        structural_monologue="All stems are perfectly aligned and RMS levels hold."
    )
    assert feature.table_source == "parquet_partition_1"
    assert feature.processed_row_count == 1500

def test_missing_fields_validation():
    """Verify Pydantic correctly raises errors for missing tracking fields."""
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        # Missing required fields should crash rather than pass silently
        Lane1DuckDBAnalytics(table_source="parquet_partition_2")

def test_omni_vector_scaling():
    """
    Verify that the OmniVectorPayload mathematically enforces the LanceDB scaling factors 
    to ensure we never lose the 'how' of the physics extraction.
    """
    from app.schemas import OmniVectorPayload
    
    # Simulate raw Librosa acoustic inputs that were pulled from DuckDB
    raw_payload = OmniVectorPayload(
        segment_name="drop_1_kick",
        spectral_centroid=3500.0,  # Raw Hz
        rms=0.05,                  # Raw energy
        zero_crossing_rate=0.08,   # Raw crossings
        spectral_bandwidth=2500.0, # Raw Hz
        mfcc_vector=[0.0] * 13
    )
    
    # Assert that the vector multipliers ( /10000.0, *10.0 ) are flawlessly enforced
    assert raw_payload.spectral_centroid == 0.35
    assert raw_payload.rms == 0.5
    assert raw_payload.zero_crossing_rate == 0.8
    assert raw_payload.spectral_bandwidth == 0.25
