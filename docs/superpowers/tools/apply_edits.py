#!/usr/bin/env python3
"""Apply exact-string edits with assertions.
Usage: python3 docs/superpowers/tools/apply_edits.py edits_bus [--check]
The module must define EDITS = {path: [(old, new) | (old, new, count), ...]}.
Every old string must occur exactly `count` times (default 1) in the file, or the
file is left untouched and the script exits 1. --check only verifies presence."""
import importlib, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
mod = importlib.import_module(sys.argv[1])
check_only = '--check' in sys.argv
problems = []
for path, edits in mod.EDITS.items():
    s = open(path, encoding='utf-8').read()
    for e in edits:
        old, new = e[0], e[1]
        count = e[2] if len(e) > 2 else 1
        n = s.count(old)
        if n != count:
            problems.append('%s: expected %d, found %d: %r' % (path, count, n, old[:90]))
            continue
        if '—' in new:
            problems.append('%s: replacement contains an em dash: %r' % (path, new[:90]))
            continue
        s = s.replace(old, new)
    if not problems and not check_only:
        open(path, 'w', encoding='utf-8').write(s)
if problems:
    print('\n'.join(problems))
    sys.exit(1)
print(('checked' if check_only else 'applied') + ' %d files, %d edits' %
      (len(mod.EDITS), sum(len(v) for v in mod.EDITS.values())))
