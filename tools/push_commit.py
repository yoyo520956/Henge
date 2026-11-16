#!/usr/bin/env python3
"""Push a set of files as ONE commit via GitHub's Git Data API.

The Contents API (tools/push_file_api.py, tools/push_tree.py) creates one
commit per file; on a repo whose workflow runs on push to main that fires one
CI run per file. This builds a tree and creates a single commit instead, so a
push triggers exactly one workflow run. It also avoids github.com's flaky HTTPS
endpoint entirely by talking to api.github.com.

Usage:
    python3 tools/push_commit.py "<message>" <repo-relative-path> [...]

The local file must exist at <repo-relative-path>. Before writing, the script
prints how the resulting tree differs from the current local git HEAD, so a
mistaken path list is visible.
"""
import base64
import json
import os
import subprocess
import sys

REPO = os.environ.get("GH_REPO", "yoyo520956/Henge")
BRANCH = os.environ.get("GH_BRANCH", "main")
PAYLOAD = "/tmp/_push_commit_payload.json"


def gh(args, payload=None):
    env = dict(os.environ)
    env["GH_TOKEN"] = os.environ["GITHUB_TOKEN"]
    cmd = ["gh", "api"] + args
    if payload is not None:
        with open(PAYLOAD, "w") as fp:
            json.dump(payload, fp)
        cmd += ["--input", PAYLOAD]
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout).strip()[:600])
    return json.loads(r.stdout) if r.stdout.strip() else {}


def remote_tree():
    ref = gh([f"repos/{REPO}/git/ref/heads/{BRANCH}"])
    base_commit = ref["object"]["sha"]
    base_tree = gh([f"repos/{REPO}/git/commits/{base_commit}"])["tree"]["sha"]
    listing = gh([f"repos/{REPO}/git/trees/{base_tree}?recursive=1"])
    blobs = {t["path"]: t["sha"] for t in listing.get("tree", []) if t["type"] == "blob"}
    return base_commit, base_tree, blobs


def local_tree():
    out = subprocess.run(["git", "-c", "core.quotePath=false", "ls-tree", "-r", "-z", "HEAD"],
                         capture_output=True, check=True).stdout
    blobs = {}
    for record in out.split(b"\0"):
        if not record:
            continue
        meta, _, path = record.partition(b"\t")
        blobs[path.decode("utf-8")] = meta.split()[2].decode()
    return blobs


def main():
    message = sys.argv[1]
    paths = sys.argv[2:]
    if not paths:
        sys.exit("no paths given")

    base_commit, base_tree, rblobs = remote_tree()
    lblobs = local_tree()

    # Report what the single commit will change relative to remote HEAD.
    local_sha = {}
    for p in paths:
        with open(p, "rb") as fp:
            data = fp.read()
        # git blob sha, to compare against both trees without an API round trip
        hdr = b"blob " + str(len(data)).encode() + b"\0"
        import hashlib
        local_sha[p] = hashlib.sha1(hdr + data).hexdigest()
    drift = sorted(set(lblobs) | set(rblobs))
    differences = [p for p in drift if lblobs.get(p) != rblobs.get(p)]
    print(f"remote HEAD {base_commit[:12]}; local HEAD files {len(lblobs)}, remote {len(rblobs)}")
    print(f"local-vs-remote differing paths ({len(differences)}):")
    for p in differences:
        print(f"  {p}")
    outside = [p for p in differences if p not in paths]
    if outside:
        print(f"NOTE: {len(outside)} differing path(s) are NOT in this push; "
              f"they stay at their remote version.")

    entries = []
    for p in paths:
        with open(p, "rb") as fp:
            data = fp.read()
        blob = gh(["--method", "POST", f"repos/{REPO}/git/blobs"],
                  {"content": base64.b64encode(data).decode(), "encoding": "base64"})
        entries.append({"path": p, "mode": "100644", "type": "blob", "sha": blob["sha"]})

    tree = gh(["--method", "POST", f"repos/{REPO}/git/trees"],
              {"base_tree": base_tree, "tree": entries})["sha"]
    commit = gh(["--method", "POST", f"repos/{REPO}/git/commits"],
                {"message": message, "tree": tree, "parents": [base_commit]})["sha"]
    gh(["--method", "PATCH", f"repos/{REPO}/git/refs/heads/{BRANCH}"], {"sha": commit})
    print(f"\npushed {len(paths)} files as ONE commit {commit[:12]}: {message}")


if __name__ == "__main__":
    main()
