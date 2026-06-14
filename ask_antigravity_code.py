"""
Ask Antigravity to review the Chat Export and Walkthrough,
and generate a 3-page summary for the user's resume/portfolio.
"""
import os, sys
from google import genai
from google.genai import types
from dotenv import load_dotenv

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

load_dotenv()
client = genai.Client()

print("Uploading chat_export.html...")
chat_file = client.files.upload(
    file="chat_export.html",
    config=types.UploadFileConfig(mime_type="text/plain")
)

# Use the walkthrough markdown as the structured findings
walkthrough_path = r"C:\Users\adams\.gemini\antigravity-ide\brain\ab68d511-5685-4692-8293-08a6b2fa31c1\walkthrough.md"
print(f"Uploading {walkthrough_path}...")
walkthrough_file = client.files.upload(
    file=walkthrough_path,
    config=types.UploadFileConfig(mime_type="text/plain")
)

prompt = """
You are a senior technical writer and engineering leader. I am giving you:
1. `chat_export.html` - A transcript of the AI-human pairing session where we mined, analyzed, and mapped the entire "Legion-Jacked-Pipeline" codebase.
2. `walkthrough.md` - The final architecture report, metrics, and resume section we produced.

YOUR JOB:
Synthesize this entire session and the findings into a cohesive, highly professional **3-page project summary** (approx 1200-1500 words). 
This document is meant to be shown to tech companies to prove the massive scale of my work over the past year.

Please structure it beautifully using Markdown:
- **Executive Summary:** High-level overview of the Legion-Jacked-Pipeline (autonomous audio intelligence).
- **System Architecture:** Detailed breakdown of the 5 layers (Data, Engines, Intelligence, API, Frontends).
- **Machine Learning & DSP Innovations:** The RandomForest scoring, IsolationForest anomaly detection, and Code Lane mining.
- **Engineering Scale & Complexity:** Highlight the Rust core, 66 API routes, React/Next.js layers, Tailscale mesh, GPU-async client.
- **My Role & Impact:** Frame this as my magnum opus, showing my ability to architect and build a multi-language (Python, Rust, TS), full-stack AI platform.

Make it read like a top-tier staff engineer's design document or a whitepaper for a portfolio.
"""

print("Streaming Gemini response...\n" + "="*70)

out_file = "legion_pipeline_whitepaper.md"
with open(out_file, "w", encoding="utf-8") as out:
    try:
        response = client.models.generate_content_stream(
            model="gemini-2.5-flash",
            contents=[chat_file, walkthrough_file, prompt]
        )
        for chunk in response:
            text = chunk.text or ""
            print(text, end="", flush=True)
            out.write(text)
    except Exception as e:
        print(f"\nError: {e}")

print("\n" + "="*70)
print(f"Saved to {out_file}")
