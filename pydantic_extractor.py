import ast
import os
import glob
import pandas as pd

OUT_DIR = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence"
LAKEHOUSE_DIR = os.path.join(OUT_DIR, "lakehouse_data")
os.makedirs(LAKEHOUSE_DIR, exist_ok=True)

schema_data = []

def extract_schemas_from_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        tree = ast.parse(content)
        module_name = os.path.basename(filepath)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                is_pydantic = False
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == 'BaseModel':
                        is_pydantic = True
                        break
                        
                if is_pydantic:
                    schema_name = node.name
                    fields = []
                    
                    for item in node.body:
                        if isinstance(item, ast.AnnAssign):
                            if isinstance(item.target, ast.Name):
                                field_name = item.target.id
                                fields.append(field_name)
                    
                    schema_data.append({
                        "file": module_name,
                        "schema_name": schema_name,
                        "fields": " ".join(fields),
                        "num_fields": len(fields)
                    })
    except Exception as e:
        pass

for py_file in glob.glob(os.path.join(OUT_DIR, "**/*.py"), recursive=True):
    if ".venv" in py_file or "node_modules" in py_file:
        continue
    extract_schemas_from_file(py_file)

df = pd.DataFrame(schema_data)
out_path = os.path.join(LAKEHOUSE_DIR, "pydantic_schemas.parquet")
df.to_parquet(out_path)

print(f"Extracted {len(df)} Pydantic schemas. Saved to {out_path}")
