#!/usr/bin/env python3
"""Merge two .strings tables that both sides rewrote from scratch.

Both add/add conflicts in Localizable.strings and InfoPlist.strings produced two
complete tables rather than two edits to one table, so git cannot merge them.
The tables are key = "value" lines; the same key can appear with a different
value on each side (main kept some English placeholders, the branch localized
them).

Merge policy:
  * a key present on only one side is kept as-is
  * a key present on both sides keeps the branch value when the branch value
    differs from the English source, because that is the translation; main's
    value is kept when the branch merely repeats the source string
  * comments are carried over from either side, the branch's first
"""
import re
import sys

LINE = re.compile(r'^\s*"((?:[^"\\]|\\.)*)"\s*=\s*"((?:[^"\\]|\\.)*)"\s*;\s*$')
CONFLICT = re.compile(
    r'<<<<<<< HEAD\n(?P<head>.*?)\|\|\|\|\|\|\| [^\n]*\n(?P<base>.*?)=======\n'
    r'(?P<branch>.*?)>>>>>>> [^\n]*\n', re.S)


def parse(text):
    entries, order, comments = {}, [], []
    for line in text.splitlines():
        m = LINE.match(line)
        if m:
            key, value = m.group(1), m.group(2)
            if key not in entries:
                order.append(key)
            entries[key] = value
        elif line.strip().startswith("/*"):
            comments.append(line)
    return entries, order, comments


def merge(head_text, branch_text):
    head, head_order, head_comments = parse(head_text)
    branch, branch_order, branch_comments = parse(branch_text)

    merged, order = {}, []
    for key in head_order + branch_order:
        if key in merged:
            continue
        order.append(key)
        if key in head and key in branch:
            merged[key] = branch[key] if branch[key] != head[key] else head[key]
        elif key in branch:
            merged[key] = branch[key]
        else:
            merged[key] = head[key]

    comments = []
    for c in branch_comments + head_comments:
        if c not in comments:
            comments.append(c)

    out = list(comments)
    if out:
        out.append("")
    for key in order:
        out.append(f'"{key}" = "{merged[key]}";')
    return "\n".join(out) + "\n", len(order)


def main():
    path = sys.argv[1]
    text = open(path).read()
    marker = CONFLICT.search(text)
    if not marker:
        print("no conflict left in", path)
        return
    merged, count = merge(marker.group("head"), marker.group("branch"))
    out = text[:marker.start()] + merged + text[marker.end():]
    open(path, "w").write(out)
    print(f"{path}: merged into {count} entries")


if __name__ == "__main__":
    main()
