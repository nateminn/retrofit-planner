#!/usr/bin/env python3
"""Put the skip link on every page that has a main landmark.

A keyboard or screen reader user otherwise tabs through the whole nav on every page
before reaching the content. The pattern and its CSS already existed, on 6 pages out of
64, which is the awkward position of having built the thing and not shipped it.

Inserts immediately after <body> so it is the first focusable element, and only where
the page actually has an element with id="main" to jump to. Idempotent.
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
LINK = '<a class="skip-link" href="#main">Skip to content</a>'
BODY = re.compile(r'(<body[^>]*>)')

def main():
    added, already, notarget, nobody = [], [], [], []
    for f in sorted(ROOT.rglob('*.html')):
        if '.git' in f.parts:
            continue
        html = f.read_text()
        rel = f.relative_to(ROOT)
        if 'class="skip-link"' in html:
            already.append(rel); continue
        if not re.search(r'id="main"', html):
            notarget.append(rel); continue
        m = BODY.search(html)
        if not m:
            nobody.append(rel); continue
        f.write_text(html[:m.end()] + '\n' + LINK + html[m.end():])
        added.append(rel)
    print(f"skip link added to {len(added)} pages; {len(already)} already had it")
    for r in notarget: print(f"  no id=\"main\" target, skipped: {r}")
    for r in nobody:   print(f"  no <body>, skipped:           {r}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
