#!/usr/bin/env python3
"""Remove the Google Fonts link tags now that the fonts are served from /fonts/.

Google Fonts sets no cookie, but every page view sends the visitor's IP to Google
just to render text. The site now sets no cookies at all, so leaving one unavoidable
third-party call in place undercuts that. Both families are SIL Open Font License,
which permits self hosting.

Replaces the stylesheet link with a preload of the two latin files actually needed
above the fold, so first paint does not wait on a CSS round trip to discover them.
Idempotent.
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]

PRELOAD = (
    '<link rel="preload" href="/fonts/fraunces-normal-3.woff2" as="font" type="font/woff2" crossorigin>\n'
    '<link rel="preload" href="/fonts/plus-jakarta-sans-normal-5.woff2" as="font" type="font/woff2" crossorigin>'
)
PATTERNS = [
    re.compile(r'\s*<link[^>]*href="https://fonts\.googleapis\.com/css2[^"]*"[^>]*>'),
    re.compile(r'\s*<link[^>]*href="https://fonts\.googleapis\.com"[^>]*>'),
    re.compile(r'\s*<link[^>]*href="https://fonts\.gstatic\.com"[^>]*>'),
]

def main():
    changed, already, missed = [], [], []
    for f in sorted(ROOT.rglob('*.html')):
        if '.git' in f.parts:
            continue
        html = f.read_text()
        rel = f.relative_to(ROOT)
        if 'fonts.googleapis.com' not in html and 'fonts.gstatic.com' not in html:
            (already if '/fonts/' in html else missed).append(rel); continue
        new = html
        for p in PATTERNS:
            new = p.sub('', new)
        if '<link rel="preload" href="/fonts/' not in new:
            new = new.replace('</head>', PRELOAD + '\n</head>', 1)
        f.write_text(new)
        changed.append(rel)
    print(f"google fonts removed from {len(changed)} pages; {len(already)} already self hosted")
    for r in missed: print(f"  no font reference at all: {r}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
