import json
import os

transcript_path = r"C:\Users\adams\.gemini\antigravity-ide\brain\ab68d511-5685-4692-8293-08a6b2fa31c1\.system_generated\logs\transcript.jsonl"
output_path = r"c:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\chat_export.html"

html_content = [
    "<html><head><style>",
    "body { font-family: sans-serif; background: #0d0d14; color: #fff; padding: 20px; line-height: 1.5; }",
    ".USER { background: #1a1a2e; padding: 15px; margin-bottom: 15px; border-left: 4px solid #00f0ff; border-radius: 4px; }",
    ".MODEL { background: #222; padding: 15px; margin-bottom: 15px; border-left: 4px solid #ff3cac; border-radius: 4px; }",
    ".SYSTEM { background: #111; padding: 10px; margin-bottom: 10px; border-left: 4px solid #888; color: #888; font-size: 0.85em; border-radius: 4px; }",
    "</style></head><body>",
    "<h2>Session Chat Export</h2>"
]

if os.path.exists(transcript_path):
    with open(transcript_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                source = data.get('source', 'UNKNOWN')
                content = data.get('content', '')
                if source == 'USER_EXPLICIT': source = 'USER'
                
                content_html = content.replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
                
                # Only log USER and MODEL responses, system messages are usually just tool outputs
                if source in ['USER', 'MODEL']:
                    html_content.append(f'<div class="{source}"><b>{source}</b><br><br>{content_html}</div>')
            except Exception as e:
                pass

html_content.append("</body></html>")

with open(output_path, 'w', encoding='utf-8') as f:
    f.write("\n".join(html_content))

print(f"Exported to {output_path}")
