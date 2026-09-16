#!/usr/bin/env python3
"""Add or refresh <lastmod> on every sitemap URL, from the file's last git commit date.
lastmod means "this file changed", which git answers exactly. Article dateModified is a
stronger editorial claim about the content and is deliberately left alone."""
import re, os, json, subprocess, sys

SITE = 'https://www.retrofitplanner.co.uk'
smap = open('sitemap.xml', encoding='utf-8').read()

def page_for(loc):
    path = loc.replace(SITE, '').strip('/')
    return os.path.join(path, 'index.html') if path else 'index.html'

def date_for(p):
    if not os.path.isfile(p): return None
    out = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', p], capture_output=True, text=True).stdout.strip()
    if out: return out
    # not yet committed, so the file is new: its change date is today
    return subprocess.run(['date', '+%Y-%m-%d'], capture_output=True, text=True).stdout.strip() or None

changed = missing = 0
def fix(m):
    global changed, missing
    url, loc = m.group(0), m.group(1)
    d = date_for(page_for(loc))
    if not d: missing += 1; return url
    url = re.sub(r'<lastmod>[^<]*</lastmod>', '', url)
    url = url.replace('</loc>', '</loc><lastmod>%s</lastmod>' % d, 1)
    changed += 1
    return url

smap = re.sub(r'<url><loc>([^<]+)</loc>.*?</url>', fix, smap, flags=re.S)
if '--dry' not in sys.argv:
    open('sitemap.xml', 'w', encoding='utf-8').write(smap)
print('lastmod set on %d urls, %d skipped (no date found)' % (changed, missing))
