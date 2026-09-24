#!/usr/bin/env python3
"""Keep every indexable page's sharing tags in step with its title and description.

When a link is shared, Facebook, LinkedIn, WhatsApp and X read og: and twitter: tags,
not the title. Pages whose titles were rewritten kept old sharing text, and some pages
had none at all. For each page that is not noindex (the embed widgets are skipped):

- og:title and twitter:title are set to the <title>, og:description and
  twitter:description to the meta description;
- any of those four that are missing are added, with og:url from the canonical link,
  og:type website, og:site_name and twitter:card (summary, or summary_large_image where
  the page has an og:image) where those are missing too.

Usage: python3 docs/superpowers/tools/social_tags.py [--apply]
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
APPLY = '--apply' in sys.argv


def attr(s):
    return s.replace('"', '&quot;')


def set_meta(s, kind, key, value, anchor):
    """Set <meta kind="key" content="value">, adding it after anchor if it is missing."""
    rx = re.compile(r'<meta %s="%s" content="[^"]*">' % (kind, re.escape(key)))
    tag = '<meta %s="%s" content="%s">' % (kind, key, attr(value))
    if rx.search(s):
        return rx.sub(lambda _: tag, s, count=1), False
    i = s.index(anchor) + len(anchor)
    return s[:i] + '\n    ' + tag + s[i:], True


def main():
    changed = []
    for f in sorted(ROOT.rglob('*.html')):
        r = f.relative_to(ROOT)
        if r.parts[0] in ('docs', 'node_modules') or (r.parts[0] == 'embed' and len(r.parts) > 2):
            continue
        s0 = s = f.read_text()
        if re.search(r'<meta name="robots" content="[^"]*noindex', s):
            continue
        t = re.search(r'<title>(.*?)</title>', s)
        d = re.search(r'<meta name="description" content="([^"]*)"', s)
        if not t or not d:
            continue
        title, desc = t.group(1), d.group(1)
        anchor = d.group(0) + '>'
        added = []
        canon = re.search(r'<link rel="canonical" href="([^"]+)">', s)
        for kind, key, value in (('property', 'og:title', title), ('property', 'og:description', desc)):
            s, new = set_meta(s, kind, key, value, anchor)
            if new:
                added.append(key)
        if canon and 'property="og:url"' not in s:
            s, _ = set_meta(s, 'property', 'og:url', canon.group(1), anchor); added.append('og:url')
        if 'property="og:type"' not in s:
            s, _ = set_meta(s, 'property', 'og:type', 'website', anchor); added.append('og:type')
        if 'property="og:site_name"' not in s:
            s, _ = set_meta(s, 'property', 'og:site_name', 'Retrofit Planner', anchor); added.append('og:site_name')
        if 'name="twitter:card"' not in s:
            card = 'summary_large_image' if 'property="og:image"' in s else 'summary'
            s, _ = set_meta(s, 'name', 'twitter:card', card, anchor); added.append('twitter:card')
        for key, value in (('twitter:title', title), ('twitter:description', desc)):
            s, new = set_meta(s, 'name', key, value, anchor)
            if new:
                added.append(key)
        if s != s0:
            changed.append('%s%s' % (r, (' (added ' + ', '.join(added) + ')') if added else ''))
            if APPLY:
                f.write_text(s)
    for c in changed:
        print(' ', c)
    print('%d pages %s' % (len(changed), 'updated' if APPLY else 'would change (dry run, pass --apply)'))


if __name__ == '__main__':
    main()
