import httpx
import sys
import base64

sys.stdout.reconfigure(encoding='utf-8')

OWNER = "adamscarmccoy-boop"
REPO  = "ADAMSCARMCCOY-CASE_STUDIES"
BASE  = f"https://api.github.com/repos/{OWNER}/{REPO}"
HEADERS = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}

def check():
    # --- 1. README ---
    print("=" * 60)
    print("README CHECK")
    print("=" * 60)
    r = httpx.get(f"{BASE}/readme", headers=HEADERS)
    if r.status_code == 200:
        data = r.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        print(content[:2000])  # Print first 2000 chars
    else:
        print(f"README not found: {r.status_code}")

    # --- 2. GitHub Actions Runs ---
    print("\n" + "=" * 60)
    print("GITHUB ACTIONS STATUS")
    print("=" * 60)
    r = httpx.get(f"{BASE}/actions/runs", headers=HEADERS, params={"per_page": 5})
    if r.status_code == 200:
        runs = r.json().get("workflow_runs", [])
        if not runs:
            print("No workflow runs found yet. Actions may not have triggered.")
        for run in runs:
            status = run.get("status")
            conclusion = run.get("conclusion") or "in_progress"
            name = run.get("name")
            branch = run.get("head_branch")
            url = run.get("html_url")
            print(f"  [{conclusion.upper()}] {name} @ {branch}")
            print(f"   -> {url}")
    else:
        print(f"Actions API error: {r.status_code}")

    # --- 3. Workflows registered ---
    print("\n" + "=" * 60)
    print("REGISTERED WORKFLOWS")
    print("=" * 60)
    r = httpx.get(f"{BASE}/actions/workflows", headers=HEADERS)
    if r.status_code == 200:
        workflows = r.json().get("workflows", [])
        if not workflows:
            print("No workflows registered yet.")
        for wf in workflows:
            print(f"  [{wf['state'].upper()}] {wf['name']} -> {wf['path']}")
    else:
        print(f"Workflows API error: {r.status_code}")

if __name__ == "__main__":
    check()
