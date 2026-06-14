import os, json, urllib.request

OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
MODEL = os.environ.get('LEGION_LLM', 'phi3:3.8b')

SYSTEM = (
    "You are an assistant that writes Jinja2 prompt templates. "
    "Given a schema and example fields, output only a Jinja2 template file that will render the data_context JSON. "
    "Do not add commentary. Keep the template minimal and include placeholders for 'query' and 'data_context'."
)

USER = (
    "Produce a Jinja2 template named session_prompt.jinja that renders a system instruction, the user query, "
    "and the serialized data_context. The data_context is a JSON array of track objects with fields: "
    "session_name, track_name, tempo, key, rms_db, crest_factor, sub_bass_energy, active_plugins, filename. "
    "Return the template content only."
)

payload = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": USER}
    ],
    "stream": False,
    "options": {"temperature": 0.0, "num_predict": 512}
}

req = urllib.request.Request(
    f"{OLLAMA_URL}/api/chat",
    data=json.dumps(payload).encode('utf-8'),
    headers={"Content-Type": "application/json"},
    method='POST'
)

try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode())
    # Ollama responds with message content under ['message']['content'] or similar formats
    content = ''
    if isinstance(data, dict):
        # try common locations
        if 'message' in data and isinstance(data['message'], dict):
            content = data['message'].get('content', '')
        elif 'choices' in data and data['choices']:
            ch = data['choices'][0]
            content = ch.get('message', {}).get('content', '') if isinstance(ch.get('message', {}), dict) else ch.get('text', '')
        else:
            # fallback: try to stringify
            content = json.dumps(data)

    out_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'session_prompt.jinja')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('WROTE_TEMPLATE', out_path)
except Exception as e:
    print('ERROR_GENERATING_TEMPLATE', str(e))
