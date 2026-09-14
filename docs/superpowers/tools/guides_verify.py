#!/usr/bin/env python3
"""Structural and arithmetic checks for the September 2026 property guides. Applies title fixes from FIX. Exit 1 on hard failures."""
import re, json, html, sys, os, glob
SITE = 'https://www.retrofitplanner.co.uk'
EXPECT = {  # slug: (demand kWh, expected running-table figures)
 'heat-pump-cost-2-bed-terrace': ['£708', '£726', '£497'],
 'heat-pump-cost-3-bed-detached': ['£1,417', '£1,452', '£993'],
 'heat-pump-cost-5-bed-house': ['£2,125', '£2,178', '£1,490'],
 'heat-pump-cost-bungalow': ['£1,151', '£1,180', '£807', '£1,376', '£1,453'],
 'heat-pump-victorian-terrace': ['£1,417', '£1,452', '£993'],
}
FIX = {
 'heat-pump-cost-2-bed-terrace': 'Heat Pump Cost for a 2-Bed Terrace UK 2026: From £8,000',
 'heat-pump-cost-3-bed-detached': 'Heat Pump Cost for a 3-Bed Detached UK 2026: From £10,000',
 'heat-pump-cost-5-bed-house': 'Heat Pump Cost for a 5-Bed House UK 2026: From £13,000',
}
ROWS2 = ['Heat pump unit and installation', 'BUS grant', 'Net heat pump cost', 'Radiator upgrades', 'Hot water cylinder', 'Pipework modifications', 'Concrete plinth', 'Total out of pocket']
valid = {'/' + p.replace('index.html', '') for p in ['index.html'] + glob.glob('*/index.html') + glob.glob('guides/*/index.html')}
def tables(s):
    out = []
    for t in re.findall(r'<table class="data-table">.*?</table>', s, re.S):
        out.append([[html.unescape(re.sub(r'<[^>]+>', '', c)).strip() for c in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', r, re.S)] for r in re.findall(r'<tr[^>]*>(.*?)</tr>', t, re.S)])
    return out
hard = 0
for slug, expect in EXPECT.items():
    p = 'guides/%s/index.html' % slug; s = open(p, encoding='utf-8').read(); issues = []; warn = []
    if slug in FIX:
        old = re.search(r'<title>(.*?)</title>', s, re.S).group(1).strip()
        s = s.replace(old, FIX[slug]); open(p, 'w', encoding='utf-8').write(s)
    head = s[:s.find('</head>')]
    t = re.search(r'<title>(.*?)</title>', head, re.S).group(1).strip(); d = re.search(r'<meta name="description" content="([^"]*)"', head).group(1)
    if len(t) > 60: issues.append('title %d' % len(t))
    if len(d) > 155: issues.append('description %d' % len(d))
    if ('href="%s/guides/%s/"' % (SITE, slug)) not in head: issues.append('canonical')
    if 'og:image' in head: issues.append('og:image present')
    for bad in ('photo-fig', 'chart-fig', 'diagram-fig', 'charts.js'): 
        if bad in s: issues.append(bad + ' present')
    if '—' in s or '–' in s: issues.append('dash')
    body = s[s.find('<main'):s.find('</main>')]
    if re.search(r'>[^<]*&(?!amp;|lt;|gt;|quot;|#)[^<]*<', body): issues.append('ampersand in text')
    if re.search(r'[\U0001F300-\U0001FAFF☀-➿]', s): issues.append('emoji')
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
    faq = None
    for b in blocks:
        try: j = json.loads(b)
        except Exception as e: issues.append('json-ld parse: ' + str(e)[:40]); continue
        if j.get('@type') == 'FAQPage': faq = j
        if j.get('@type') == 'Article' and j.get('datePublished') != '2026-09-14': warn.append('datePublished ' + str(j.get('datePublished')))
    faqsec = body[body.find('<h2 id="faq"'):] if '<h2 id="faq"' in body else body
    h3s = [html.unescape(re.sub(r'<[^>]+>', '', x)).strip() for x in re.findall(r'<h3>(.*?)</h3>', faqsec, re.S)]
    if not faq or len(faq.get('mainEntity', [])) != 6: issues.append('faq count')
    elif [q['name'] for q in faq['mainEntity']] != h3s[:6]: warn.append('faq names differ from h3s')
    links = set(re.findall(r'href="(/[^"#]*)"', body))
    off = [l for l in links if l not in valid]
    if off: issues.append('links off site: ' + ', '.join(off))
    if len(links) < 15: issues.append('only %d internal links' % len(links))
    ids = set(re.findall(r'<h2 id="([^"]+)"', body)); toc = set(re.findall(r'href="#([^"]+)"', body))
    if toc - ids: issues.append('toc anchors missing: ' + ', '.join(sorted(toc - ids)))
    tb = tables(body)
    if len(tb) < 5: issues.append('only %d tables' % len(tb))
    else:
        rows2 = [r[0] for r in tb[1][1:]]
        if rows2 != ROWS2: issues.append('table2 rows: ' + ' | '.join(rows2))
        rows5 = [r[0] for r in tb[4][1:]]
        for need in ('Gas boiler', 'Heat pump (standard tariff)', 'Heat pump (heat pump tariff)'):
            if need not in rows5: issues.append('table5 missing ' + need)
        cells = ' '.join(c for r in tb[4] for c in r)
        for v in expect:
            if v not in cells: issues.append('table5 lacks ' + v)
    words = len(re.sub(r'<[^>]+>', ' ', body).split())
    print('%-32s title %2d desc %3d links %2d tables %d words %4d  %s%s' % (slug, len(t), len(d), len(links), len(tb), words, ('ISSUES: ' + '; '.join(issues)) if issues else 'ok', ('  warn: ' + '; '.join(warn)) if warn else ''))
    hard += bool(issues)
sys.exit(1 if hard else 0)
