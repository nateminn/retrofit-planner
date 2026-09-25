#!/usr/bin/env python3
"""Put headings in order: no heading may skip a level below the one before it.

Screen reader users move through a page by headings, and Lighthouse and axe flag a jump
such as an h4 straight after an h1. Many guides used h4 for the "In this guide" box and
for callouts. This lowers the number of any heading that skips a level to one below the
heading before it (an h4 after an h1 becomes an h2, an h4 after an h2 becomes an h3).
css/style.css styles .toc, .callout and .next-steps headings at every level, so they
look the same as before.

Usage: python3 docs/superpowers/tools/heading_order.py [--apply]
"""
import collections, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
APPLY = '--apply' in sys.argv
H = re.compile(r'<(/?)h([1-6])\b([^>]*)>', re.I)
BOX = re.compile(r'<(div|aside|section|nav)\b[^>]*class="([^"]*)"', re.I)


def container(s, pos):
    """The class of the nearest box that opened before this heading, for the report."""
    last = None
    for m in BOX.finditer(s, 0, pos):
        last = m.group(2).split()[0]
    return last or '-'


def fix(s):
    out, last, prev, changes, pend = [], 0, 0, [], []
    main_start = s.find('<main')
    for m in H.finditer(s):
        closing, level = m.group(1), int(m.group(2))
        if m.start() < main_start or '<!-- site-footer -->' in s[max(0, m.start() - 4000):m.start()] and 'footer' in s[max(0, m.start() - 200):m.start()]:
            continue
        if closing:
            if pend and pend[-1][0] == level:
                _, new = pend.pop()
                out.append(s[last:m.start()] + '</h%d>' % new); last = m.end()
            continue
        new = level if (prev == 0 or level <= prev + 1) else prev + 1
        if new != level:
            changes.append((level, new, container(s, m.start()), re.sub(r'<[^>]+>', '', s[m.end():s.find('</h', m.end())])[:50]))
        out.append(s[last:m.start()] + '<h%d%s>' % (new, m.group(3))); last = m.end()
        pend.append((level, new))
        prev = new
    out.append(s[last:])
    return ''.join(out), changes


def main():
    boxes = collections.Counter(); pages = 0; total = 0
    for f in sorted(ROOT.rglob('*.html')):
        r = f.relative_to(ROOT)
        if r.parts[0] in ('docs', 'node_modules'):
            continue
        s = f.read_text()
        foot = s.find('<!-- site-footer -->')
        body, tail = (s[:foot], s[foot:]) if foot > 0 else (s, '')
        new, changes = fix(body)
        if changes:
            pages += 1; total += len(changes)
            for a, b, box, text in changes:
                boxes['h%d->h%d in %s' % (a, b, box)] += 1
            if APPLY:
                f.write_text(new + tail)
    for k, v in boxes.most_common():
        print('  %4d  %s' % (v, k))
    print('%d headings on %d pages %s' % (total, pages, 'fixed' if APPLY else 'would change (dry run, pass --apply)'))


if __name__ == '__main__':
    main()
