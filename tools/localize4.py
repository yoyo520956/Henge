#!/usr/bin/env python3
"""Fix L.s(...) calls that still hold a Swift interpolation: turn them into
L.f(...) with %@ placeholders and String(describing:) arguments."""
import re, sys

def find_interps(body):
    out = []
    i = 0
    while i < len(body):
        if body[i] == '\\' and i + 1 < len(body) and body[i+1] == '(':
            depth = 0
            j = i + 1
            in_str = False
            escape_next = False
            found = False
            while j < len(body):
                c = body[j]
                if escape_next:
                    escape_next = False
                    j += 1
                    continue
                if c == '\\':
                    escape_next = True
                    j += 1
                    continue
                if in_str:
                    if c == '"':
                        in_str = False
                    j += 1
                    continue
                if c == '"':
                    in_str = True
                    j += 1
                    continue
                if c == '(':
                    depth += 1
                elif c == ')':
                    depth -= 1
                    if depth == 0:
                        out.append((i, j + 1, body[i+2:j]))
                        i = j + 1
                        found = True
                        break
                j += 1
            if not found:
                i += 1
                continue
            continue
        i += 1
    return out

CALL = re.compile(r'L\.s\("((?:[^"\\]|\\.)*)"\)')

def process(src):
    changed = True
    rounds = 0
    while changed and rounds < 5:
        changed = False
        rounds += 1
        out = ''
        pos = 0
        for m in CALL.finditer(src):
            body = m.group(1)
            interps = find_interps(body)
            if not interps:
                continue
            key = ''
            args = []
            last = 0
            for (s, e, expr) in interps:
                key += body[last:s] + '%@'
                args.append('String(describing: %s)' % expr.strip())
                last = e
            key += body[last:]
            esc = key.replace('\\', '\\\\').replace('"', '\\"')
            repl = 'L.f("%s"%s)' % (esc, ''.join(', ' + a for a in args))
            out += src[pos:m.start()] + repl
            pos = m.end()
            changed = True
        src = out + src[pos:]
    return src

if __name__ == '__main__':
    for path in sys.argv[1:]:
        src = open(path, encoding='utf-8').read()
        dst = process(src)
        if dst != src:
            open(path, 'w', encoding='utf-8').write(dst)
            print('fixed', path)