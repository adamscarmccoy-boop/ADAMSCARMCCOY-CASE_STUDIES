import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.database import analyze_session_with_phi3
from app.extractor import extract_and_index_session

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ableton Session Intelligence Node",
    version="1.0.0",
    description="H.O.R.N. Stack Local-First Execution Node."
)

class QueryPayload(BaseModel):
    session_file_path: str
    prompt_query: str

@app.get("/.well-known/agent-card.json")
async def get_agent_card():
    return {
        "name": "Gemini SDLC Agent",
        "description": "An agent that generates code based on natural language instructions and "
                       "streams file outputs.",
        "url": "http://localhost:51207/",
        "provider": {
            "organization": "Google",
            "url": "https://google.com"
        },
        "protocolVersion": "0.3.0",
        "version": "0.0.2",
        "capabilities": {
            "streaming": True,
            "pushNotifications": False,
            "stateTransitionHistory": True
        },
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer"
            },
            "basicAuth": {
                "type": "http",
                "scheme": "basic"
            }
        },
        "security": [
            {
                "bearerAuth": []
            },
            {
                "basicAuth": []
            }
        ],
        "defaultInputModes": [
            "text"
        ],
        "defaultOutputModes": [
            "text"
        ],
        "skills": [
            {
                "id": "code_generation",
                "name": "Code Generation",
                "description": "Generates code snippets or complete files based on user requests, "
                               "streaming the results.",
                "tags": [
                    "code",
                    "development",
                    "programming"
                ],
                "examples": [
                    "Write a python function to calculate fibonacci numbers.",
                    "Create an HTML file with a basic button that alerts \"Hello!\" when clicked."
                ],
                "inputModes": [
                    "text"
                ],
                "outputModes": [
                    "text"
                ]
            }
        ],
        "supportsAuthenticatedExtendedCard": False
    }

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
