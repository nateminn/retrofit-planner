#!/usr/bin/env python3
"""Keep /guides/ in step with the guides themselves.

1. Every card takes the guide's own meta description, so the index can never quote a
   price, or promise a section, that the guide no longer has.
2. Guides not yet on the index are added to their section (NEW below).
3. Section header counts and the category nav counts are recounted from the cards.

Usage: python3 docs/superpowers/tools/sync_guides_index.py [--apply]
"""
import re, sys, html, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
APPLY = '--apply' in sys.argv
INDEX = ROOT / 'guides' / 'index.html'

# slug: (section id, title, thumbnail slug, badge html)
NEW = {
    'what-size-heat-pump': ('heat-pumps', 'What Size Heat Pump Do I Need?', 'heat-pump-cost-by-house-type', '<span class="gi-badge homeowner">For homeowners</span><span class="gi-badge new">New</span>'),
    'heat-pump-cost-3-bed-mid-terrace': ('heat-pumps', 'Heat Pump Cost for a 3-Bed Mid-Terrace', 'heat-pump-cost-2-bed-terrace', '<span class="gi-badge homeowner">For homeowners</span><span class="gi-badge new">New</span>'),
    'heat-pump-1930s-semi': ('heat-pumps', 'Heat Pump for a 1930s Semi', 'heat-pump-cost-3-bed-semi', '<span class="gi-badge homeowner">For homeowners</span><span class="gi-badge new">New</span>'),
    'energy-bills-1-bed-flat': ('bills', 'Average Energy Bill for a 1 Bed Flat', 'energy-bills-by-household-size', '<span class="gi-badge new">New</span>'),
    'energy-bills-2-bed-house': ('bills', 'Average Energy Bill for a 2 Bed House', 'energy-bills-by-household-size', '<span class="gi-badge new">New</span>'),
    'energy-bills-3-bed-house': ('bills', 'Average Energy Bill for a 3 Bed House', 'average-energy-bills-uk', '<span class="gi-badge new">New</span>'),
    'energy-bills-4-bed-house': ('bills', 'Average Energy Bill for a 4 Bed House', 'average-energy-bills-uk', '<span class="gi-badge new">New</span>'),
    'energy-bills-5-bed-house': ('bills', 'Average Energy Bill for a 5 Bed House', 'average-energy-bills-uk', '<span class="gi-badge new">New</span>'),
    'insulation-cost-by-house-type': ('insulation', 'Insulation Cost by House Type', 'insulation-calculator', '<span class="gi-badge homeowner">For homeowners</span><span class="gi-badge landlord">For landlords</span><span class="gi-badge new">New</span>'),
    'insulation-cost-semi-detached-house': ('insulation', 'Insulation Cost for a Semi-Detached House', 'is-cavity-wall-insulation-worth-it', '<span class="gi-badge homeowner">For homeowners</span><span class="gi-badge new">New</span>'),
    'insulation-cost-detached-house': ('insulation', 'Insulation Cost for a Detached House', 'solid-wall-insulation-cost', '<span class="gi-badge homeowner">For homeowners</span><span class="gi-badge new">New</span>'),
    'insulation-cost-terraced-house': ('insulation', 'Insulation Cost for a Terraced House', 'is-loft-insulation-worth-it', '<span class="gi-badge homeowner">For homeowners</span><span class="gi-badge landlord">For landlords</span><span class="gi-badge new">New</span>'),
    'insulation-cost-bungalow': ('insulation', 'Insulation Cost for a Bungalow', 'underfloor-insulation-cost', '<span class="gi-badge homeowner">For homeowners</span><span class="gi-badge new">New</span>'),
    'insulation-cost-flat': ('insulation', 'Insulation Cost for a Flat', 'how-long-loft-insulation-lasts', '<span class="gi-badge homeowner">For homeowners</span><span class="gi-badge new">New</span>'),
}
ARROW = '<div class="gi-arrow"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg></div>'


def meta_description(slug):
    f = ROOT / 'guides' / slug / 'index.html'
    if not f.exists():
        return None
    m = re.search(r'<meta name="description" content="([^"]*)"', f.read_text())
    return html.unescape(m.group(1)) if m else None


def main():
    s = INDEX.read_text()
    changed = []

    def fix_desc(m):
        slug, desc = m.group(1), m.group(3)
        md = meta_description(slug)
        if not md or md == html.unescape(desc):
            return m.group(0)
        changed.append(slug)
        return m.group(0).replace('<div class="gi-desc">%s</div>' % desc, '<div class="gi-desc">%s</div>' % html.escape(md, quote=False))
    s = re.sub(r'<a href="/guides/([^/"]+)/" class="guide-item">(.*?)<div class="gi-desc">(.*?)</div>', fix_desc, s, flags=re.S)

    added = []
    for slug, (section, title, thumb, badges) in NEW.items():
        if 'href="/guides/%s/"' % slug in s or not (ROOT / 'guides' / slug / 'index.html').exists():
            continue
        md = meta_description(slug) or ''
        card = ('            <a href="/guides/%s/" class="guide-item">\n'
                '                <div class="gi-thumb"><img src="/images/%s-240.webp" width="240" height="240" alt="" loading="lazy" decoding="async"></div>\n'
                '<div class="gi-content"><div class="gi-title">%s</div><div class="gi-desc">%s</div></div>\n'
                '                <div class="gi-badges">%s</div>\n'
                '                %s\n'
                '            </a>\n') % (slug, thumb, title, html.escape(md, quote=False), badges, ARROW)
        sec = s.index('<section class="guide-section" id="%s">' % section)
        lst = s.index('<div class="guide-list">', sec)
        # the list closes at the </div> that balances it
        depth, i = 0, lst
        for mm in re.finditer(r'<(/?)div\b[^>]*>', s[lst:]):
            depth += -1 if mm.group(1) else 1
            if depth == 0:
                i = lst + mm.start()
                break
        s = s[:i] + card + s[i:]
        added.append(slug)

    # recount every section and the nav
    for mm in re.finditer(r'<section class="guide-section" id="([^"]+)">', s):
        pass
    sections = re.findall(r'<section class="guide-section" id="([^"]+)">', s)
    for sid in sections:
        start = s.index('<section class="guide-section" id="%s">' % sid)
        end = s.find('<section class="guide-section"', start + 10)
        end = end if end > 0 else s.index('</main>') if '</main>' in s else len(s)
        n = s[start:end].count('class="guide-item"')
        seg = s[start:end]
        seg2 = re.sub(r'<span class="count">\d+ guides?</span>', '<span class="count">%d guide%s</span>' % (n, '' if n == 1 else 's'), seg, count=1)
        s = s[:start] + seg2 + s[end:]
        s = re.sub(r'(<a href="#%s"[^>]*>.*?<span class="g-count">)\d+(</span>)' % re.escape(sid), lambda x: x.group(1) + str(n) + x.group(2), s, count=1, flags=re.S)
    total = s.count('class="guide-item"')
    s = re.sub(r'<p>\d+ guides backed by', '<p>%d guides backed by' % total, s, count=1)
    print('descriptions synced:', len(changed), changed)
    print('cards added:', added)
    if APPLY:
        INDEX.write_text(s)
        print('APPLIED')
    else:
        print('dry run, pass --apply')


if __name__ == '__main__':
    main()
