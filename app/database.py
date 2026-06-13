import duckdb
import ollama
from jinja2 import Template
import os

from app.config import settings
from app.schemas import Lane1DuckDBAnalytics

def analyze_session_with_phi3(parquet_file_path: str, user_request: str) -> Lane1DuckDBAnalytics:
    """
    Queries cold storage Parquet rows via projection pushdowns and uses 
    local Phi-3 constraints to return verified, token-muzzled Pydantic analytics.
    """
    con = duckdb.connect(database=":memory:")
    con.execute(f"SET threads={settings.omp_num_threads};")
    
    # Extract records directly out of your local binary Parquet files
    raw_db_rows = con.execute(f"""
        SELECT track_id, track_name, track_type, active_plugins 
        FROM read_parquet('{parquet_file_path}')
        ORDER BY track_id ASC
    """).fetchall()
    
    # Compile prompt by feeding rows into separate Jinja template
    template_path = os.path.join(os.path.dirname(__file__), "templates", "session_prompt.jinja")
    with open(template_path, "r", encoding="utf-8") as f:
        template_str = f.read()

    jinja_compiler = Template(template_str)
    fully_rendered_prompt = jinja_compiler.render(
        track_data=raw_db_rows,
        query=user_request
    )
    
    # Pass the prompt to your offline model execution engine
    response = ollama.chat(
        model=settings.model_choice,
        messages=[{"role": "user", "content": fully_rendered_prompt}],
        options={"temperature": 0.0},
        format=Lane1DuckDBAnalytics.model_json_schema()  # <-- THE MUZZLE LINK
    )
    
    raw_ai_string = response['message']['content']
    validated_insight = Lane1DuckDBAnalytics.model_validate_json(raw_ai_string)
    
    return validated_insight
