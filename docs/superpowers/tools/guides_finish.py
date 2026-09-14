#!/usr/bin/env python3
"""Register new guides on the hub and in the sitemap. usage: guides_finish.py guides_meta.json
guides_meta.json: {slug: {"hub_title": ..., "blurb": ..., "after": <slug of the hub entry to insert after>}}
Idempotent: skips a slug already present on the hub or in the sitemap."""
import json, re, sys, os

meta = json.load(open(sys.argv[1], encoding='utf-8'))
hub = open('guides/index.html', encoding='utf-8').read()
smap = open('sitemap.xml', encoding='utf-8').read()
ICON = '<div class="gi-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg></div>'
ARROW = '<div class="gi-arrow"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg></div>'
added_hub = added_map = 0
for slug, m in meta.items():
    assert os.path.exists('guides/%s/index.html' % slug), slug
    for txt in (m['hub_title'], m['blurb']):
        assert '—' not in txt and '&' not in txt, (slug, 'bad char')
    if ('href="/guides/%s/"' % slug) not in hub:
        entry = ('            <a href="/guides/%s/" class="guide-item">\n                %s\n'
                 '                <div class="gi-content"><div class="gi-title">%s</div><div class="gi-desc">%s</div></div>\n'
                 '                <div class="gi-badges"><span class="gi-badge homeowner">For homeowners</span><span class="gi-badge new">New</span></div>\n'
                 '                %s\n            </a>\n') % (slug, ICON, m['hub_title'], m['blurb'], ARROW)
        anchor = re.search(r'            <a href="/guides/%s/" class="guide-item">.*?</a>\n' % re.escape(m['after']), hub, re.S)
        assert anchor, ('hub anchor not found', m['after'])
        hub = hub[:anchor.end()] + entry + hub[anchor.end():]; added_hub += 1
    loc = 'https://www.retrofitplanner.co.uk/guides/%s/' % slug
    if loc not in smap:
        after = '<url><loc>https://www.retrofitplanner.co.uk/guides/%s/</loc></url>\n' % m['after']
        assert after in smap, ('sitemap anchor not found', m['after'])
        smap = smap.replace(after, after + '  <url><loc>%s</loc></url>\n' % loc, 1); added_map += 1
open('guides/index.html', 'w', encoding='utf-8').write(hub)
open('sitemap.xml', 'w', encoding='utf-8').write(smap)
n = len(re.findall(r'class="guide-item"', hub))
hub2 = re.sub(r'(\d+) in-depth guides', '%d in-depth guides' % n, hub)
if hub2 != hub: open('guides/index.html', 'w', encoding='utf-8').write(hub2)
print('hub entries added', added_hub, '| sitemap entries added', added_map, '| guides on hub', n, '| sitemap urls', smap.count('<loc>'))
