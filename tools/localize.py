#!/usr/bin/env python3
"""Wrap Henge's user-visible SwiftUI string literals in L.s(...)/L.f(...).

Handles literal-only arguments (L.s) and literals with Swift interpolation
(L.f with %@ placeholders and String(describing:) arguments).
"""
import re, sys, os

def split_top(s):
    """Split a call's argument list on top-level commas."""
    parts, depth, cur, i, in_str = [], 0, '', 0, False
    while i < len(s):
        c = s[i]
        if in_str:
            if c == '\\':
                cur += s[i:i+2]; i += 2; continue
            if c == '"': in_str = False
            cur += c; i += 1; continue
        if c == '"': in_str = True; cur += c; i += 1; continue
        if c in '([{': depth += 1
        elif c in ')]}': depth -= 1
        if c == ',' and depth == 0:
            parts.append(cur); cur = ''; i += 1; continue
        cur += c; i += 1
    parts.append(cur)
    return parts

def find_call_end(s, open_idx):
    depth, i, in_str = 0, open_idx, False
    while i < len(s):
        c = s[i]
        if in_str:
            if c == '\\': i += 2; continue
            if c == '"': in_str = False
            i += 1; continue
        if c == '"': in_str = True; i += 1; continue
        if c in '([{': depth += 1
        elif c in ')]}':
            depth -= 1
            if depth == 0: return i
        i += 1
    return -1

INTERP = re.compile(r'\\\(([^()]*)\)')

def literal_to_call(text):
    if not (text.startswith('"') and text.endswith('"')):
        return None
    body = text[1:-1]
    if body.startswith('"') and body.endswith('"') and len(body) > 1:
        return None
    interps = INTERP.findall(body)
    if not interps:
        return 's', body, []
    key = INTERP.sub('%@', body)
    args = ['String(describing: %s)' % e.strip() for e in interps]
    return 'f', key, args

NAMES = r'(?:Text|Button|Section|LabeledContent|TextField|Toggle|Label|Picker|confirmationDialog|alert|ContentUnavailableView|\.accessibilityLabel|\.accessibilityHint|\.accessibilityValue)'

def process(text):
    out = text
    for _ in range(6):
        before = out
        i = 0
        buf = ''
        while True:
            m = re.search(NAMES + r'\s*\(', out[i:])
            if not m:
                buf += out[i:]
                break
            name = m.group(0)
            name = name[:name.index('(')].strip()
            open_idx = i + m.end() - 1
            close = find_call_end(out, open_idx)
            if close < 0:
                buf += out[i:open_idx+1]; i = open_idx + 1; continue
            inner = out[open_idx+1:close]
            parts = split_top(inner)
            first = parts[0].strip()
            lit = literal_to_call(first)
            if lit is None:
                buf += out[i:close+1]; i = close + 1; continue
            kind, key, args = lit
            if kind == 'f' and not args:
                buf += out[i:close+1]; i = close + 1; continue
            esc_key = key.replace('\\', '\\\\').replace('"', '\\"')
            if kind == 's':
                repl = 'L.s("%s")' % esc_key
                tail = ')'
            else:
                repl = 'L.f("%s"%s' % (esc_key, ''.join(', ' + a for a in args))
                tail = '))'
            new_inner = repl + inner[len(parts[0]):] + tail
            buf += out[i:open_idx+1] + new_inner
            i = close + 1
        out = buf
        if out == before:
            break
    return out

if __name__ == '__main__':
    total = 0
    for path in sys.argv[1:]:
        src = open(path, encoding='utf-8').read()
        dst = process(src)
        if dst != src:
            open(path, 'w', encoding='utf-8').write(dst)
            total += 1
            print('%-44s %d L.* calls' % (os.path.basename(path),
                  dst.count('L.s(') + dst.count('L.f(')))
    print('files changed:', total)
