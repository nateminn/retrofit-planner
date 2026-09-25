#!/usr/bin/env python3
"""The short answer at the top of a page, with buttons that jump to its main sections.

Many pages are long and dense. Each one listed in docs/tldr.json gets, straight under its
<h1>, a box with three or four short points carrying the page's key figures and a row of
jump buttons to the sections people most want. It replaces the page's old "In this guide"
list (div.toc), which did the same job at five times the height.

docs/tldr.json maps a page ("guides/heat-pump-cost-4-bed-house") to:
  {"points": ["**£12,500 to £18,000** installed ...", ...],
   "jumps":  [["Prices", "What a 4-bed heat pump really costs in 2026"], ...]}
Points may use **bold**. A jump names its target by the section heading's exact text (or
by "#id"); a heading with no id is given one.

Every money figure, pence figure, percentage and kW figure in the points must also appear
in the page outside the box, so the summary can never say something the page does not.

On the 25 pages with a quote form, a "Get quotes" button (jump to "#quote") is worth adding.

Usage: python3 docs/superpowers/tools/tldr.py [--apply] [--data other.json]   (exit code 1 on any problem, or
       when a dry run over docs/tldr.json would change a page: a box is missing or out of date)
       --data checks another file's entries against the pages without writing anything.
"""
import html, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
APPLY = '--apply' in sys.argv
DATA = ROOT / 'docs' / 'tldr.json'
BLOCK_RE = re.compile(r'\n?<!-- tldr -->.*?<!-- /tldr -->\n?', re.S)
TOC_RE = re.compile(r'\n?[ \t]*<div class="toc">.*?</div>[ \t]*\n?', re.S)
FIG_RE = re.compile(r'£[\d,]+(?:\.\d+)?|\b\d[\d,]*(?:\.\d+)?(?:p\b|%| kW\b| per cent\b)')


def slug(text):
    s = re.sub(r'<[^>]+>', '', html.unescape(text)).lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s[:48].rstrip('-') or 'section'


def visible(s):
    s = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', s, flags=re.S)
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s)))


def render_point(p):
    p = html.escape(p, quote=False)
    return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', p)


def build(page, spec):
    f = ROOT / page / 'index.html'
    s = f.read_text()
    problems = []
    s = BLOCK_RE.sub('\n', s, count=1)
    s = TOC_RE.sub('\n', s, count=1)
    main_at = s.find('<main')
    ids = set(re.findall(r'\bid="([^"]+)"', s))
    links = []
    for label, target in spec['jumps']:
        if target.startswith('#'):
            if target[1:] not in ids:
                problems.append('%s: no element with id %s' % (page, target))
            links.append((label, target))
            continue
        m = None
        for h in re.finditer(r'<h2([^>]*)>(.*?)</h2>', s[main_at:], re.S):
            if re.sub(r'\s+', ' ', visible(h.group(2))).strip() == target:
                m = h
                break
        if not m:
            problems.append('%s: no section heading "%s"' % (page, target))
            continue
        idm = re.search(r'\bid="([^"]+)"', m.group(1))
        if idm:
            hid = idm.group(1)
        else:
            hid = slug(target)
            n = 2
            while hid in ids:
                hid = '%s-%d' % (slug(target), n)
                n += 1
            ids.add(hid)
            a, b = main_at + m.start(), main_at + m.end()
            s = s[:a] + '<h2 id="%s"%s>%s</h2>' % (hid, m.group(1), m.group(2)) + s[b:]
            main_at = s.find('<main')
        links.append((label, '#' + hid))
    points = ''.join('<li>%s</li>' % render_point(p) for p in spec['points'])
    jumps = ''.join('<a href="%s">%s</a>' % (href, html.escape(label)) for label, href in links)
    block = ('<!-- tldr -->\n<section class="tldr" aria-labelledby="tldr-h">'
             '<h2 id="tldr-h">%s</h2><ul class="tldr-points">%s</ul>'
             '<nav class="jump" aria-label="Jump to a section">%s</nav></section>\n<!-- /tldr -->'
             % (html.escape(spec.get('heading', 'The short answer')), points, jumps))
    h1 = s.find('</h1>', main_at)
    if h1 < 0:
        return s, ['%s: no <h1>' % page]
    at = h1 + len('</h1>')
    s = s[:at] + '\n' + block + s[at:]
    # every figure in the box must appear elsewhere on the page
    body = visible(BLOCK_RE.sub(' ', s))
    for p in spec['points']:
        for fig in FIG_RE.findall(p.replace('**', '')):
            if fig not in body:
                problems.append('%s: "%s" is in the short answer but nowhere else on the page' % (page, fig))
    if not 3 <= len(spec['points']) <= 4:
        problems.append('%s: %d points (use 3 or 4)' % (page, len(spec['points'])))
    return s, problems


def main():
    src = pathlib.Path(sys.argv[sys.argv.index('--data') + 1]) if '--data' in sys.argv else DATA
    data = json.loads(src.read_text()) if src.exists() else {}
    apply = APPLY and src == DATA
    problems, changed = [], 0
    for page, spec in data.items():
        new, p = build(page, spec)
        problems += p
        f = ROOT / page / 'index.html'
        if new != f.read_text():
            changed += 1
            if apply and not p:
                f.write_text(new)
    for p in problems:
        print('  ' + p)
    print('%s: %d pages with a short answer, %d %s' % ('FAIL' if problems else 'PASS', len(data), changed,
          'updated' if APPLY else 'would change'))
    # a dry run over docs/tldr.json that would change a page means a box is missing or stale
    return 1 if problems or (changed and not APPLY and src == DATA) else 0


if __name__ == '__main__':
    sys.exit(main())
