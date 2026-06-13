from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

from app.extractor import extract_and_index_session
from app.database import analyze_session_with_phi3

app = FastAPI(
    title="Ableton Session Intelligence Node",
    version="1.0.0",
    description="H.O.R.N. Stack Local-First Execution Node."
)

class QueryPayload(BaseModel):
    session_file_path: str
    prompt_query: str

@app.post("/v1/agent/inference")
async def execute_pipeline_endpoint(payload: QueryPayload):
    try:
        # Step 1: Unpack and create matching Parquet files
        parquet_target = extract_and_index_session(payload.session_file_path)
        
        # Step 2: Route through DuckDB and your muzzled local Phi-3 engine
        validated_data = analyze_session_with_phi3(parquet_target, payload.prompt_query)
        
        return {
            "status": "success",
            "engine": "Ollama-Phi3",
            "lane_executed": 1,
            "data": validated_data.model_dump()
        }
    except Exception as e:
        logger.exception(f"Failed to execute pipeline for {payload.session_file_path}")
        raise HTTPException(status_code=500, detail=str(e))
