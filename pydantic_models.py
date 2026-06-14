from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class Lane1DuckDBAnalytics(BaseModel):
    session_id: str
    total_tracks: int
    dominant_tempo: Optional[float]
    dominant_key: Optional[str]
    mean_rms_db: Optional[float]
    crest_factor: Optional[float]
    top_plugins: List[str] = []

class CodeRoleResult(BaseModel):
    role: str
    count: int
    confidence: float = Field(..., ge=0.0, le=1.0)
