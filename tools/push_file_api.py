#!/usr/bin/env python3
"""Push one file to a GitHub repo via the Contents API."""
import base64, json, os, subprocess, sys

repo = os.environ.get("GH_REPO", "yoyo520956/Henge")
branch = os.environ.get("GH_BRANCH", "main")
path = sys.argv[1]
local = sys.argv[2]

with open(local, "rb") as f:
    content = f.read()

env = dict(os.environ)
env["GH_TOKEN"] = os.environ["GITHUB_TOKEN"]

sha = subprocess.run(
    ["gh", "api", f"repos/{repo}/contents/{path}", "--jq", ".sha"],
    capture_output=True, text=True, env=env, check=True).stdout.strip()

payload = {
    "message": os.environ.get("MSG", f"update {path}"),
    "content": base64.b64encode(content).decode(),
    "sha": sha,
    "branch": branch,
}
with open("/tmp/_gh_payload.json", "w") as f:
    json.dump(payload, f)

res = subprocess.run(
    ["gh", "api", "--method", "PUT", f"repos/{repo}/contents/{path}",
     "--input", "/tmp/_gh_payload.json"],
    capture_output=True, text=True, env=env)
print(res.stdout or res.stderr)
sys.exit(res.returncode)
