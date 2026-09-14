#!/usr/bin/env python3
"""Apply a title and description sweep from a JSON map. usage: titles_apply.py titles.json [--dry]
Replaces the old <title> text wherever it appears in <head> (title tag, og:title, schema headline or name)
and the old description wherever it appears (meta description, og:description, schema description)."""
import json, re, sys, html

spec = json.load(open(sys.argv[1], encoding='utf-8')); dry = '--dry' in sys.argv
changed = 0; problems = []
for path, want in spec.items():
    if path.startswith('_'): continue
    s = open(path, encoding='utf-8').read()
    head_end = s.index('</head>'); head = s[:head_end]; rest = s[head_end:]
    old_t = re.search(r'<title>(.*?)</title>', head, re.S).group(1).strip()
    old_d = re.search(r'<meta name="description" content="([^"]*)"', head).group(1)
    for key, old, new in (('title', old_t, want.get('title')), ('description', old_d, want.get('description'))):
        if not new or new == old: continue
        limit = 60 if key == 'title' else 155
        if '—' in new or '&' in new or '–' in new or len(new) > limit:
            problems.append('%s %s: %d chars%s' % (path, key, len(new), ' bad char' if any(c in new for c in '—&–') else '')); continue
        n = head.count(old)
        assert n >= 1, (path, key, 'old text not found')
        head = head.replace(old, new)
        # JSON-LD blocks escape nothing we use, but guard against the old text sitting inside a longer string
        print('%-52s %-11s %d places  (%d chars)' % (path, key, n, len(new)))
        changed += 1
    # keep the social card in step with the page: og:title and og:description mirror the final values
    t = re.search(r'<title>(.*?)</title>', head, re.S).group(1).strip()
    d = re.search(r'<meta name="description" content="([^"]*)"', head).group(1)
    head = re.sub(r'(<meta property="og:title" content=")[^"]*(")', lambda m: m.group(1) + t + m.group(2), head)
    head = re.sub(r'(<meta property="og:description" content=")[^"]*(")', lambda m: m.group(1) + d + m.group(2), head)
    if not dry: open(path, 'w', encoding='utf-8').write(head + rest)
print('fields changed:', changed, '(dry run)' if dry else '')
if problems: print('PROBLEMS:\n  ' + '\n  '.join(problems)); sys.exit(1)
