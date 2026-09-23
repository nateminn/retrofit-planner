#!/usr/bin/env python3
"""Load js/partners.js on every page that carries a paid link.

partners.js is what puts the visible commission disclosure on the page. A page with
affiliate links and no partners.js has the rel="sponsored" attribute and nothing the
reader can actually see, which is a signal to a search engine, not a disclosure to a
person. This finds every page with a sponsored link or a data-partner slot, and makes
sure the script is loaded there.

Inserts before /js/nav.js, which is the last script on nearly every page. Idempotent.
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
NAV = '<script src="/js/nav.js" defer></script>'
TAG = '<script src="/js/partners.js" defer></script>'

def needs(html):
    return bool(re.search(r'<a[^>]+rel="[^"]*\bsponsored\b', html)) or 'data-partner=' in html

def main():
    added, already, nomain, noanchor = [], [], [], []
    for f in sorted(ROOT.rglob('*.html')):
        if '.git' in f.parts:
            continue
        html = f.read_text()
        if not needs(html):
            continue
        rel = f.relative_to(ROOT)
        if '/js/partners.js' in html:
            already.append(rel); continue
        if '<main' not in html:
            nomain.append(rel); continue
        if NAV not in html:
            noanchor.append(rel); continue
        f.write_text(html.replace(NAV, TAG + '\n' + NAV, 1))
        added.append(rel)
    print(f"added partners.js to {len(added)} pages; {len(already)} already had it")
    for r in noanchor: print(f"  NO NAV ANCHOR, skipped: {r}")
    for r in nomain:   print(f"  NO <main>, skipped:     {r}")
    return 1 if (noanchor or nomain) else 0

if __name__ == '__main__':
    sys.exit(main())
