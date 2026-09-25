#!/usr/bin/env python3
"""The data register on /accuracy/: every source, what we use it for, when the publisher last
updated it, when our figures last changed, and when we last checked it.

docs/data-sources.json holds the register. "Updated on our site" is not typed in by hand: it
is the date of the first commit that contains each figure as it stands today (the entry's
probe), so it moves by itself when a figure changes.

Usage: python3 docs/superpowers/tools/data_sources.py            dry run: exit 1 if the page is out of date
       python3 docs/superpowers/tools/data_sources.py --apply    write the table into accuracy/index.html
       python3 docs/superpowers/tools/data_sources.py --check    ask the GOV.UK content API whether any
                                                                 GOV.UK source has been updated since the
                                                                 date we recorded, and report it
"""
import datetime, html, json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
REG = ROOT / 'docs' / 'data-sources.json'
PAGE = ROOT / 'accuracy' / 'index.html'
START, END = '<!-- data-register -->', '<!-- /data-register -->'


def long_date(iso):
    d = datetime.date.fromisoformat(iso)
    return '%d %s %d' % (d.day, d.strftime('%B'), d.year)


def our_update(probe):
    f, needle = probe
    out = subprocess.run(['git', 'log', '-S', needle, '--format=%cs', '--', f], capture_output=True, text=True, cwd=ROOT).stdout.split()
    in_file = needle in (ROOT / f).read_text()
    if not in_file:
        raise SystemExit('probe not found in %s: %r' % (f, needle))
    if not out:   # not committed yet: it changes with this commit
        return long_date(datetime.date.today().isoformat())
    return long_date(out[-1])   # oldest commit that introduced the figure as it stands


def render(reg):
    items = []
    for s in reg['sources']:
        items.append('<li><h3><a href="%s" target="_blank" rel="noopener">%s</a></h3><p class="ds-pub">%s</p><p>%s</p>'
                     '<dl class="ds-dates"><div><dt>Publisher last updated it</dt><dd>%s</dd></div><div><dt>Our figures last changed</dt><dd>%s</dd></div>'
                     '<div><dt>We last checked it</dt><dd>%s</dd></div></dl></li>'
                     % (html.escape(s['url'], quote=True), html.escape(s['name']), html.escape(s['publisher']), html.escape(s['use']),
                        html.escape(s['published']), our_update(s['probe']), html.escape(s['checked'])))
    table = '<ul class="ds-list">%s</ul>' % ''.join(items)
    assumptions = '<ul>%s</ul>' % ''.join('<li>%s</li>' % html.escape(a) for a in reg['assumptions'])
    return table, assumptions


def main():
    reg = json.loads(REG.read_text())
    if '--check' in sys.argv:
        newer = []
        for s in reg['sources']:
            if not s.get('govuk'):
                continue
            # curl rather than urllib: Python's certificate store fails on some machines
            d = json.loads(subprocess.run(['curl', '-s', '-m', '30', 'https://www.gov.uk/api/content/' + s['govuk']], capture_output=True, text=True).stdout)
            pub = long_date(d['public_updated_at'][:10])
            flag = '' if pub in s['published'] else '   <- updated since we recorded it'
            if flag:
                newer.append(s['name'])
            print('  %-70s GOV.UK says %s%s' % (s['name'][:70], pub, flag))
        print('%s: %d GOV.UK sources checked' % ('NEWER VERSIONS' if newer else 'UP TO DATE', sum(1 for s in reg['sources'] if s.get('govuk'))))
        return 1 if newer else 0
    table, assumptions = render(reg)
    s = PAGE.read_text()
    new = s
    for key, block in (('table', table), ('assumptions', assumptions)):
        a, b = START.replace('register', 'register:' + key), END.replace('register', 'register:' + key)
        if a not in new:
            raise SystemExit('accuracy/index.html has no %s marker' % a)
        new = re.sub(re.escape(a) + '.*?' + re.escape(b), lambda m: a + block + b, new, flags=re.S)
    new = re.sub(r'<strong>\d+ sources, with their dates\.</strong>', '<strong>%d sources, with their dates.</strong>' % len(reg['sources']), new)
    if '--apply' in sys.argv:
        PAGE.write_text(new)
        print('APPLIED: %d sources' % len(reg['sources']))
        return 0
    print('%s: data register on /accuracy/ %s' % ('PASS' if new == s else 'FAIL', 'matches docs/data-sources.json' if new == s else 'is out of date (run with --apply)'))
    return 0 if new == s else 1


if __name__ == '__main__':
    sys.exit(main())
