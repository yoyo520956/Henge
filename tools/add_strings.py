#!/usr/bin/env python3
"""Add or update entries in Henge's .strings tables.

Keeps the English and Simplified Chinese tables in step: an English source
string is added to en.lproj verbatim and to zh-Hans.lproj with the translation
given here, or with the English string itself when no translation is supplied
(which shows in the app as untranslated text, so it should be rare).

Usage:
    python3 tools/add_strings.py <key>|<translation> [<key>|<translation> ...]
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EN = os.path.join(ROOT, "ios/Henge/Resources/en.lproj/Localizable.strings")
ZH = os.path.join(ROOT, "ios/Henge/Resources/zh-Hans.lproj/Localizable.strings")

LINE = re.compile(r'^("(?:[^"\\]|\\.)*")\s*=\s*("(?:[^"\\]|\\.)*")\s*;\s*$')


def read(path):
    entries, order, head = {}, [], []
    with open(path) as f:
        for line in f:
            m = LINE.match(line)
            if m:
                key = m.group(1)
                if key not in entries:
                    order.append(key)
                entries[key] = m.group(2)
            elif line.strip().startswith("/*"):
                head.append(line.rstrip("\n"))
            elif not line.strip():
                head.append("")
    return entries, order, head


def write(path, entries, order, head):
    out = [h for h in head if h.strip()]
    out.append("")
    for key in order:
        out.append(f"{key} = {entries[key]};")
    with open(path, "w") as f:
        f.write("\n".join(out) + "\n")


def main():
    pairs = []
    for arg in sys.argv[1:]:
        if "|" not in arg:
            print(f"skip (no translation): {arg}")
            continue
        key, _, zh = arg.partition("|")
        pairs.append((key, zh))

    en_entries, en_order, en_head = read(EN)
    zh_entries, zh_order, zh_head = read(ZH)

    added = 0
    for key, zh in pairs:
        # The key is the English source string; the translation is the value.
        en_value = f'"{key}"'
        zh_value = f'"{zh}"'
        if en_value not in en_entries:
            en_order.append(en_value)
            added += 1
        en_entries[en_value] = en_value
        if en_value not in zh_entries:
            zh_order.append(en_value)
        zh_entries[en_value] = zh_value

    write(EN, en_entries, en_order, en_head)
    write(ZH, zh_entries, zh_order, zh_head)
    print(f"en: {len(en_order)} entries, zh: {len(zh_order)} entries, {added} new")


if __name__ == "__main__":
    main()
