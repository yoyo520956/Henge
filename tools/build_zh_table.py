#!/usr/bin/env python3
"""Build the zh-Hans table for the current source tree.

Keys are the English source text. Chinese translations are reused from an
earlier table whenever the English text matches (format specifiers are matched
positionally), so only genuinely new strings need translating.
"""
import re, glob, json, os, sys

SPEC = re.compile(r'%(?:\d+\$)?[-+ #0]*[\d*]*(?:\.\d+)?(?:hh|h|ll|l|L|z|q)?[diouxXeEfgGaAcCsSpn%@]')

def unescape(t):
    return (t.replace('\\"', '"').replace('\\\\', '\\')
             .replace('\\n', '\n').replace('\\t', '\t'))

def canon(key):
    return SPEC.sub('#', key)

def specs(key):
    return SPEC.findall(key)

def extract_keys():
    keys = set()
    pat = re.compile(r'L\.(?:s|f)\(\s*"((?:[^"\\]|\\.)*)"')
    for f in glob.glob('ios/Henge/**/*.swift', recursive=True):
        src = open(f, encoding='utf-8').read()
        for m in pat.finditer(src):
            keys.add(unescape(m.group(1)))
    return sorted(keys)

def rewrite_specs(translation, old_key, new_key):
    old = specs(old_key)
    new = specs(new_key)
    if len(old) != len(new):
        return None
    if old == new:
        return translation
    out, idx, pos = [], 0, 0
    for m in SPEC.finditer(translation):
        out.append(translation[pos:m.start()])
        out.append(new[idx])
        idx += 1
        pos = m.end()
    out.append(translation[pos:])
    return ''.join(out)

def main():
    old_map = json.load(open('tools/zh_map_all.json', encoding='utf-8'))
    by_canon = {}
    for k, v in old_map.items():
        by_canon.setdefault(canon(k), []).append((k, v))

    keys = extract_keys()
    resolved, unresolved = {}, []
    for k in keys:
        c = canon(k)
        cands = by_canon.get(c)
        if not cands:
            unresolved.append(k)
            continue
        exact = [p for p in cands if p[0] == k]
        if exact:
            resolved[k] = exact[0][1]
            continue
        ok = None
        for ok_key, ok_val in cands:
            r = rewrite_specs(ok_val, ok_key, k)
            if r is not None:
                ok = r
                break
        if ok is None:
            unresolved.append(k)
        else:
            resolved[k] = ok

    print('keys: %d  reused: %d  unresolved: %d' % (len(keys), len(resolved), len(unresolved)))
    json.dump(resolved, open('tools/zh_resolved.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1, sort_keys=True)
    json.dump(unresolved, open('tools/zh_unresolved.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    for k in unresolved:
        print('NEEDS: %s' % k)

if __name__ == '__main__':
    main()
