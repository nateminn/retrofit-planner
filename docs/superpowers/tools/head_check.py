#!/usr/bin/env python3
"""Every content page: title 60 or fewer, description 155 or fewer, og:title equals title, no em dash or ampersand in the title. Exit 1 on any problem."""
import re, glob, sys
import os
skip = ('methodology/', 'terms/', 'about/', 'privacy/', 'contact/', 'thank-you/') + tuple(x for x in os.environ.get('HEAD_CHECK_SKIP', '').split(',') if x)
bad = []
for f in ['index.html'] + glob.glob('*/index.html') + glob.glob('guides/*/index.html'):
    if f.startswith(skip): continue
    s = open(f, encoding='utf-8').read(); h = s[:s.find('</head>')]
    t = re.search(r'<title>(.*?)</title>', h, re.S).group(1).strip()
    d = re.search(r'<meta name="description" content="([^"]*)"', h); og = re.search(r'og:title" content="([^"]*)"', h)
    if len(t) > 60 or (d and len(d.group(1)) > 155) or (og and og.group(1) != t) or '—' in h or '&' in t:
        bad.append('  %-52s title %d desc %s og-match %s' % (f, len(t), len(d.group(1)) if d else '-', (og.group(1) == t) if og else '-'))
print('head problems: %d' % len(bad)); print('\n'.join(bad))
sys.exit(1 if bad else 0)
