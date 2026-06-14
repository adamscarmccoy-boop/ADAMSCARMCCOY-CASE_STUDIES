import sys, os, json, time, warnings
warnings.filterwarnings("ignore")

import httpx
import duckdb
import lancedb
import pyarrow as pa
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# We won't test Ollama here, just LanceDB + DuckDB I/O
print(f"LanceDB version: {lancedb.__version__}")
print(f"DuckDB version: {duckdb.__version__}")

DB_PATH      = r"c:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\web_intel_sonicdb.duckdb"
LANCEDB_PATH = r"c:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag"
TABLE_NAME   = "chris_lake_web_intel"

print(f"\n1. Connecting to DuckDB at {DB_PATH}")
conn = duckdb.connect(DB_PATH)
conn.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER, val TEXT)")
conn.execute("INSERT INTO test_table VALUES (1, 'test')")
res = conn.execute("SELECT * FROM test_table").fetchall()
print(f"   DuckDB write/read success: {res}")

print(f"\n2. Connecting to LanceDB at {LANCEDB_PATH}")
try:
    db = lancedb.connect(LANCEDB_PATH)
    
    schema = pa.schema([
        pa.field("release_title", pa.string()),
        pa.field("embed_text",    pa.string()),
        pa.field("vector",        pa.list_(pa.float32(), 1024)),
    ])
    
    if TABLE_NAME in db.table_names():
        db.drop_table(TABLE_NAME)
        
    # Dummy data
    import numpy as np
    dummy_vector = np.random.rand(1024).astype(np.float32).tolist()
    
    data = [{
        "release_title": "Test Release",
        "embed_text": "This is a test",
        "vector": dummy_vector
    }]
    
    table = db.create_table(TABLE_NAME, data=data, schema=schema)
    print(f"   LanceDB write success! Table rows: {table.count_rows()}")
    
except Exception as e:
    print(f"   LANCEDB ERROR: {e}")

print("\nSmoke test complete.")
