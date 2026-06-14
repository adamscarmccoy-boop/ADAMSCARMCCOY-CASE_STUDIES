import json
import os
import duckdb
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

load_dotenv()

class OperationReadiness(BaseModel):
    is_ready: bool
    missing_resources: List[str] = []
    remediation_steps: List[str] = []

db_tables = {
    'web_intel_sonicdb.duckdb': ['applemusic_raw', 'discogs_releases', 'listenbrainz_ground_truth', 'spotify_charts_daily', 'spotify_track_metrics', 'test_table', 'web_intel_raw'],
    'sonic_core_v2.duckdb': ['agent_analysis_logs', 'audio_features', 'interaction_logs', 't_core_memory', 'tool_index']
}
available_files = ['langgraph_gemini_test.py', 'sovereign_schemas.py', 'update_nb.py', 'antigravity_horn_audit.ipynb']

def test_query(q):
    client = genai.Client()
    system_prompt = (
        "You are the Pre-Flight Database & File Readiness Validator.\n"
        "Compare the User Query against the available Database Tables and Workspace Files.\n"
        "Determine if the query targets tables, databases, or files that do not exist.\n"
        "Return the validation verdict strictly as an OperationReadiness JSON object."
    )
    user_prompt = f"""
    User Query: {q}
    
    [DATABASE TABLES]
    {json.dumps(db_tables, indent=2)}
    
    [WORKSPACE FILES]
    {json.dumps(available_files, indent=2)}
    """
    
    response = client.models.generate_content(
        model='gemini-flash-latest',
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type='application/json',
            response_schema=OperationReadiness,
            temperature=0.0
        )
    )
    v = OperationReadiness.model_validate_json(response.text)
    print(f'=== QUERY: "{q}" ===')
    print('Is Ready:', v.is_ready)
    print('Missing:', v.missing_resources)
    print('Remediation:', v.remediation_steps)
    print()

test_query('Find the top 10 streaming tracks from spotify_charts_daily')
test_query('Query soundcloud_metadata to find track key alignments')
