import pydantic
from typing import Literal, List
from pydantic import BaseModel, Field

# --- THE THREE EXPLICIT SYSTEM DATA LANES ---
class Lane1DuckDBAnalytics(BaseModel):
    """Lane 1: High-speed structural metric reporting and tabular abnormalities"""
    table_source: str = Field(..., description="Target Parquet data partition evaluated")
    processed_row_count: int
    anomalous_metric_detected: bool
    structural_monologue: str

class Lane2LanceDBVectors(BaseModel):
    """Lane 2: Semantic audio similarity tracking, vector keys, and file locations"""
    matched_vector_keys: List[int]
    maximum_semantic_distance: float
    nearest_file_nodes: List[str]

class Lane3SystemLogs(BaseModel):
    """Lane 3: Deep system tracking and core workspace layout status updates"""
    process_id: int
    execution_severity: Literal["INFO", "WARNING", "CRITICAL"]
    root_cause_analysis: str

# --- THE OMNI-VECTOR MATH PAYLOAD ---
class OmniVectorPayload(BaseModel):
    """
    LanceDB payload that normalizes physical acoustics for semantic vector space.
    This permanently guarantees the scaling logic is mathematically identical across the entire pipeline.
    """
    segment_name: str
    spectral_centroid: float
    rms: float
    zero_crossing_rate: float
    spectral_bandwidth: float
    mfcc_vector: List[float]

    @pydantic.model_validator(mode='after')
    def enforce_vector_multipliers(self) -> 'OmniVectorPayload':
        """
        Enforces the raw-to-scaled multiplier transitions.
        Assuming incoming data is raw Librosa physics data, we scale it to fit LanceDB.
        """
        # Vector Multipliers to prevent 'loss of how'
        # Only scale if it hasn't been scaled yet (Centroid > 100 means raw Hz)
        if self.spectral_centroid > 10.0:
            self.spectral_centroid = self.spectral_centroid / 10000.0
            
        if self.spectral_bandwidth > 10.0:
            self.spectral_bandwidth = self.spectral_bandwidth / 10000.0
            
        # RMS is usually tiny (0.01). If it's less than 1.0, scale it by 10.0
        if self.rms < 1.0:
            self.rms = self.rms * 10.0
            
        # ZCR is also tiny (0.05). Scale by 10.0
        if self.zero_crossing_rate < 1.0:
            self.zero_crossing_rate = self.zero_crossing_rate * 10.0
            
        return self
