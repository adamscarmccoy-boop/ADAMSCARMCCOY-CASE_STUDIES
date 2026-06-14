import json
import os

NOTEBOOK_PATH = "antigravity_horn_audit.ipynb"

# 1. Load the existing notebook
if not os.path.exists(NOTEBOOK_PATH):
    print(f"Error: {NOTEBOOK_PATH} not found.")
    exit(1)

with open(NOTEBOOK_PATH, "r", encoding="utf-8") as f:
    nb = json.load(f)

# 2. Define the source lines for the dynamic code cell
code_source = [
    "import os\n",
    "import json\n",
    "import duckdb\n",
    "from google import genai\n",
    "from google.genai import types\n",
    "from pydantic import BaseModel, Field\n",
    "from typing import List\n",
    "from dotenv import load_dotenv\n",
    "\n",
    "load_dotenv()\n",
    "\n",
    "# ─── 1. PYDANTIC READINESS SCHEMATION ───\n",
    "class OperationReadiness(BaseModel):\n",
    "    is_ready: bool = Field(\n",
    "        description=\"True if all required session features, database tables, and API environment configs are present to perform the requested operation.\"\n",
    "    )\n",
    "    missing_resources: List[str] = Field(\n",
    "        default_factory=list,\n",
    "        description=\"List of missing database tables, files, or variables needed to run the operation.\"\n",
    "    )\n",
    "    remediation_steps: List[str] = Field(\n",
    "        default_factory=list,\n",
    "        description=\"Actionable steps or commands the user must run to provision the missing tables or files.\"\n",
    "    )\n",
    "\n",
    "# ─── 2. DYNAMIC METADATA DISCOVERY ───\n",
    "def discover_pipeline_state() -> dict:\n",
    "    \"\"\"Discovers all available database tables and workspace files to feed into the readiness check.\"\"\"\n",
    "    state = {\n",
    "        \"db_tables\": {},\n",
    "        \"available_files\": [f for f in os.listdir(\".\") if f.endswith(\".py\") or f.endswith(\".ipynb\") or f.endswith(\".md\")]\n",
    "    }\n",
    "    \n",
    "    # Check web_intel_sonicdb.duckdb\n",
    "    db1 = \"web_intel_sonicdb.duckdb\"\n",
    "    if os.path.exists(db1):\n",
    "        try:\n",
    "            conn = duckdb.connect(db1)\n",
    "            state[\"db_tables\"][db1] = [r[0] for r in conn.execute(\"SHOW TABLES\").fetchall()]\n",
    "            conn.close()\n",
    "        except Exception as e:\n",
    "            state[\"db_tables\"][db1] = f\"Error reading tables: {e}\"\n",
    "            \n",
    "    # Check sonic_core_v2.duckdb\n",
    "    db2 = \"C:/STUDIES_BACKUP/Legion-Jacked-Pipeline/AI_Logs/sonic_core_v2.duckdb\"\n",
    "    if os.path.exists(db2):\n",
    "        try:\n",
    "            conn = duckdb.connect(db2)\n",
    "            state[\"db_tables\"][\"sonic_core_v2.duckdb\"] = [r[0] for r in conn.execute(\"SHOW TABLES\").fetchall()]\n",
    "            conn.close()\n",
    "        except Exception as e:\n",
    "            state[\"db_tables\"][\"sonic_core_v2.duckdb\"] = f\"Error reading tables: {e}\"\n",
    "            \n",
    "    return state\n",
    "\n",
    "# ─── 3. PRE-FLIGHT VERIFIER ───\n",
    "def check_session_readiness(user_query: str, pipeline_state: dict) -> OperationReadiness:\n",
    "    \"\"\"\n",
    "    Pre-flight validation using structured Gemini schema inference to check if the agent\n",
    "    is ready to execute or if it requires more input parameters.\n",
    "    \"\"\"\n",
    "    client = genai.Client()\n",
    "    \n",
    "    system_prompt = (\n",
    "        \"You are the Pre-Flight Database & File Readiness Validator.\\n\"\n",
    "        \"Your task is to compare the User's Query against the available Database Tables and Workspace Files.\\n\"\n",
    "        \"Verify if the tables or files targeted by the query actually exist in the provided state.\\n\"\n",
    "        \"If any table, database, or file referenced in the query is missing, set is_ready to False.\\n\"\n",
    "        \"Return the validated verdict using the OperationReadiness schema.\"\n",
    "    )\n",
    "    \n",
    "    user_prompt = f\"\"\"\n",
    "    User Query: {{user_query}}\n",
    "    \n",
    "    [DATABASE TABLES CURRENTLY LOADED]\n",
    "    {{json.dumps(pipeline_state['db_tables'], indent=2)}}\n",
    "    \n",
    "    [WORKSPACE FILES AVAILABLE]\n",
    "    {{json.dumps(pipeline_state['available_files'], indent=2)}}\n",
    "    \n",
    "    API Key Setup: {{'GEMINI_API_KEY present' if os.environ.get('GEMINI_API_KEY') else 'GEMINI_API_KEY MISSING'}}\n",
    "    \"\"\"\n",
    "    \n",
    "    response = client.models.generate_content(\n",
    "        model=\"gemini-flash-latest\", # Quota-safe 1.5 Flash endpoint\n",
    "        contents=user_prompt.replace('{{user_query}}', user_query)\n",
    "                            .replace('{{json.dumps(pipeline_state[\\'db_tables\\'], indent=2)}}', json.dumps(pipeline_state['db_tables'], indent=2))\n",
    "                            .replace('{{json.dumps(pipeline_state[\\'available_files\\'], indent=2)}}', json.dumps(pipeline_state['available_files'], indent=2))\n",
    "                            .replace(\"{{'GEMINI_API_KEY present' if os.environ.get('GEMINI_API_KEY') else 'GEMINI_API_KEY MISSING'}}\", 'GEMINI_API_KEY present' if os.environ.get('GEMINI_API_KEY') else 'GEMINI_API_KEY MISSING'),\n",
    "        config=types.GenerateContentConfig(\n",
    "            system_instruction=system_prompt,\n",
    "            response_mime_type=\"application/json\",\n",
    "            response_schema=OperationReadiness,\n",
    "            temperature=0.0\n",
    "        )\n",
    "    )\n",
    "    \n",
    "    return OperationReadiness.model_validate_json(response.text)\n",
    "\n",
    "# ─── 4. EXECUTE TEST RUNS ───\n",
    "pipeline_state = discover_pipeline_state()\n",
    "print(f\"\ud83d\udce6 Discovered Pipeline State: {json.dumps(pipeline_state, indent=2)}\")\n",
    "print(\"=\" * 70)\n",
    "\n",
    "# Query 1: Valid table query\n",
    "q1 = \"Get track details and dsp_rms from spotify_charts_daily.\"\n",
    "print(f\"\\n\ud83d\udd0d Testing Query 1: '{q1}'\")\n",
    "verdict1 = check_session_readiness(q1, pipeline_state)\n",
    "print(f\"Ready? {'\ud83d\udfe2 YES' if verdict1.is_ready else '\ud83d\udd34 NO'}\")\n",
    "if not verdict1.is_ready:\n",
    "    print(f\"  Missing: {verdict1.missing_resources}\")\n",
    "    print(f\"  Remediation: {verdict1.remediation_steps}\")\n",
    "\n",
    "# Query 2: Invalid table query\n",
    "q2 = \"Audit soundcloud_metadata and check rhythm vectors.\"\n",
    "print(f\"\\n\ud83d\udd0d Testing Query 2: '{q2}'\")\n",
    "verdict2 = check_session_readiness(q2, pipeline_state)\n",
    "print(f\"Ready? {'\ud83d\udfe2 YES' if verdict2.is_ready else '\ud83d\udd34 NO'}\")\n",
    "if not verdict2.is_ready:\n",
    "    print(f\"  Missing: {verdict2.missing_resources}\")\n",
    "    print(f\"  Remediation: {verdict2.remediation_steps}\")\n"
]

# 3. Locate the dynamic_readiness_code cell and replace its source
found = False
for cell in nb["cells"]:
    if cell.get("id") == "dynamic_readiness_code":
        cell["source"] = code_source
        found = True
        break

if not found:
    print("Warning: Cell with id 'dynamic_readiness_code' not found. Appending instead.")
    nb["cells"].append({
        "cell_type": "code",
        "execution_count": None,
        "id": "dynamic_readiness_code",
        "metadata": {},
        "outputs": [],
        "source": code_source
    })

# 4. Save the notebook
with open(NOTEBOOK_PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

print("Notebook cell successfully updated with dynamic variables checking context.")
