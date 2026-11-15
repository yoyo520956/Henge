#!/usr/bin/env python3
"""Push every file that differs between a base ref and the working tree.

Used instead of `git push` when github.com's HTTPS endpoint is flaky while
api.github.com still answers. Each file goes through the Contents API, one
commit per file, which is slower than a real push but reliable.

Usage:
    python3 tools/push_tree.py <base-ref> <message>
"""
import base64
import json
import os
import subprocess
import sys

REPO = os.environ.get("GH_REPO", "yoyo520956/Henge")
BRANCH = os.environ.get("GH_BRANCH", "main")


def gh(args, payload=None):
    env = dict(os.environ)
    env["GH_TOKEN"] = os.environ["GITHUB_TOKEN"]
    cmd = ["gh", "api"] + args
    if payload is not None:
        with open("/tmp/_push_payload.json", "w") as f:
            json.dump(payload, f)
        cmd += ["--input", "/tmp/_push_payload.json"]
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[:400])
    return json.loads(r.stdout) if r.stdout.strip() else {}


def file_sha(path):
    try:
        return gh([f"repos/{REPO}/contents/{path}?ref={BRANCH}"])["sha"]
    except RuntimeError:
        return None


def main():
    base = sys.argv[1]
    message = sys.argv[2]

    out = subprocess.run(["git", "diff", "--name-status", base, "HEAD"],
                         capture_output=True, text=True, check=True).stdout
    changes = []
    for line in out.splitlines():
        status, _, path = line.partition("\t")
        changes.append((status.strip(), path.strip()))

    ok = fail = 0
    for status, path in changes:
        if status == "D":
            sha = file_sha(path)
            if not sha:
                continue
            try:
                gh(["--method", "DELETE", f"repos/{REPO}/contents/{path}",
                    "-f", f"message={message}", "-f", f"sha={sha}",
                    "-f", f"branch={BRANCH}"])
                print(f"deleted {path}")
                ok += 1
            except RuntimeError as e:
                print(f"FAIL delete {path}: {e}")
                fail += 1
            continue

        try:
            with open(path, "rb") as f:
                content = f.read()
        except FileNotFoundError:
            print(f"skip (missing locally) {path}")
            continue

        payload = {
            "message": message,
            "content": base64.b64encode(content).decode(),
            "branch": BRANCH,
        }
        sha = file_sha(path)
        if sha:
            payload["sha"] = sha
        try:
            gh(["--method", "PUT", f"repos/{REPO}/contents/{path}"], payload)
            print(f"pushed {path}")
            ok += 1
        except RuntimeError as e:
            print(f"FAIL {path}: {e}")
            fail += 1

    print(f"\npushed {ok}, failed {fail}")


if __name__ == "__main__":
    main()
