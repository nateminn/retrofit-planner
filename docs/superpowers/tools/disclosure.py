#!/usr/bin/env python3
"""Write the affiliate disclosure into the HTML of every page with a static paid link.

WHY STATIC AND NOT JUST THE SCRIPT. js/partners.js injects the same note at runtime, and
that is the right mechanism for a link that only becomes paid when a programme is switched
on. It is the wrong mechanism for the Amazon links, which are paid in the HTML as shipped.
If the script fails, is blocked, or simply has not run yet, those pages would show paid
links with nothing the reader can see. A disclosure that depends on JavaScript is a
disclosure you cannot promise, so for static paid links it goes in the markup.

partners.js skips injecting when a .affiliate-note is already present, so the two cannot
double up. Idempotent.
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
NOTE = ('<p class="affiliate-note" role="note">Some links on this page earn us a commission '
        'if you buy. It costs you nothing, and it never changes the numbers or which option '
        'this page recommends.</p>')
H1 = re.compile(r'(<h1\b[^>]*>.*?</h1>)', re.S)
SPONSORED = re.compile(r'<a[^>]+rel="[^"]*\bsponsored\b')

def main():
    done, skipped, failed = [], [], []
    for f in sorted(ROOT.rglob('*.html')):
        if '.git' in f.parts:
            continue
        html = f.read_text()
        rel = f.relative_to(ROOT)
        if not SPONSORED.search(html):
            continue
        if 'class="affiliate-note"' in html:
            skipped.append(rel); continue
        m = H1.search(html)
        if not m:
            failed.append((rel, 'no h1')); continue
        # the note must precede the first paid link in reading order, or it is not a disclosure
        if m.end() > SPONSORED.search(html).start():
            failed.append((rel, 'h1 comes after the first sponsored link')); continue
        f.write_text(html[:m.end()] + '\n' + NOTE + html[m.end():])
        done.append(rel)
    print(f"disclosure written into {len(done)} pages; {len(skipped)} already had one")
    for r, why in failed:
        print(f"  FAILED ({why}): {r}")
    return 1 if failed else 0

if __name__ == '__main__':
    sys.exit(main())
