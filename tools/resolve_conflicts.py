#!/usr/bin/env python3
"""Resolve the se3-low-memory-zh merge conflicts in Henge's iOS sources.

Rule set, derived from reading every conflict block:

* Most blocks are "main already localized it with String(describing:) wrappers,
  the branch localized it with the direct argument". Both are correct; the
  branch form is the one the localization tables were written against, so the
  branch side wins.
* A handful of blocks are real feature differences where main carries code the
  branch never saw (Mac Apps button, Instant Resume, the footprint log after
  boot). Those need both sides, merged by hand.

The script takes the branch side by default and reports the blocks it marked
for manual handling.
"""
import re
import subprocess
import sys

FILES = subprocess.run(
    ["git", "diff", "--name-only", "--diff-filter=U"],
    capture_output=True, text=True).stdout.split()

BLOCK = re.compile(
    r'<<<<<<< HEAD\n(?P<head>.*?)\|\|\|\|\|\|\| [^\n]*\n(?P<base>.*?)=======\n(?P<branch>.*?)>>>>>>> [^\n]*\n',
    re.S)

# Blocks where main has functionality the branch lacks; these are listed by
# (file, index) and are resolved by hand instead of by this script.
MANUAL = {
    ("ios/Henge/HomeView.swift", 0),
    ("ios/Henge/HomeView.swift", 3),
    ("ios/Henge/SessionView.swift", 7),
    ("ios/Henge/SettingsView.swift", 6),
}

manual_report = []

for path in FILES:
    if path.endswith(".strings"):
        continue
    src = open(path).read()
    blocks = list(BLOCK.finditer(src))
    if not blocks:
        continue
    out = []
    last = 0
    for i, m in enumerate(blocks):
        out.append(src[last:m.start()])
        key = (path, i)
        if key in MANUAL:
            manual_report.append((path, i, m.group("head"), m.group("branch")))
            # Keep the whole conflict verbatim; resolved by hand after.
            out.append(m.group(0))
        else:
            out.append(m.group("branch"))
        last = m.end()
    out.append(src[last:])
    open(path, "w").write("".join(out))
    print(f"{path}: resolved {len(blocks) - len([k for k in MANUAL if k[0] == path])}"
          f"/{len(blocks)} blocks automatically")

if manual_report:
    print("\nMANUAL blocks left in place:")
    for path, i, head, branch in manual_report:
        print(f"  {path} block {i+1}")
    sys.exit(2)
