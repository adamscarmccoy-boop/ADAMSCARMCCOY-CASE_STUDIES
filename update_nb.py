import json
import re

with open('gemini_code_lane_cells.md', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# find all cell objects
# They look like { "cell_type": ... }
cells = []
matches = re.finditer(r'\{\s*"cell_type":\s*".*?\}', text, re.DOTALL)
# wait, regex for nested brackets is hard.
# Let's just find the first { "cell_type" and the last } before ```
start = text.find('{\n "cell_type"')
end = text.rfind('}')
if start != -1 and end != -1:
    json_str = '[' + text[start:end+1] + ']'
    try:
        cells = json.loads(json_str)
        with open('code_mining_pipeline.ipynb', 'r', encoding='utf-8') as f:
            nb = json.load(f)
            
        nb['cells'].extend(cells)
        
        with open('code_mining_pipeline.ipynb', 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=1)
            
        print('Successfully appended cells to notebook.')
    except Exception as e:
        print('Error:', e)
else:
    print("Could not find cells.")
