#!/usr/bin/env python3
"""Fold long method notes behind a toggle, site wide.

A note of 30 words or more under a table or chart (p.note) is folded into
<details class="more note-more"><summary>The data behind this table</summary>...</details>,
so the reader sees the figures and opens the method only if they want it. Short notes stay
as they are. Every word stays on the page. Safe to re-run: folded notes are skipped.

Usage: python3 docs/superpowers/tools/notes_fold.py [--apply]
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
APPLY = '--apply' in sys.argv
NOTE = re.compile(r'<p class="(?:data-table )?note">(.*?)</p>', re.S)
MIN_WORDS = 30


def label(before):
    tail = before[-400:]
    t, f = tail.rfind('</table>'), tail.rfind('</figure>')
    if t == -1 and f == -1:
        return 'How we worked this out'
    return 'The data behind this table' if t > f else 'The data behind this chart'


def fold(s):
    out, last, n = [], 0, 0
    for m in NOTE.finditer(s):
        words = len(re.sub(r'<[^>]+>', ' ', m.group(1)).split())
        opened = s.rfind('<details', 0, m.start()) > s.rfind('</details>', 0, m.start())
        if words < MIN_WORDS or opened:
            continue
        out.append(s[last:m.start()])
        out.append('<details class="more note-more" data-af><summary>%s</summary>%s</details>' % (label(s[:m.start()]), m.group(0)))
        last, n = m.end(), n + 1
    out.append(s[last:])
    return ''.join(out), n


def main():
    total = pages = 0
    for f in sorted(ROOT.rglob('index.html')):
        if f.relative_to(ROOT).parts[0] in ('docs', 'node_modules', 'embed'):
            continue
        s = f.read_text()
        new, n = fold(s)
        if n:
            total += n; pages += 1
            if APPLY:
                f.write_text(new)
    print('%s %d notes on %d pages' % ('folded' if APPLY else 'would fold', total, pages))


if __name__ == '__main__':
    main()
