#!/usr/bin/env python3
"""Sitewide label and date sweep for touched pages only."""
import glob, re

UNTOUCHED = {
 'epc-calculator/index.html', 'contact/index.html', 'privacy/index.html', 'terms/index.html', 'thank-you/index.html',
 'guides/condensation-mould-guide/index.html', 'guides/heat-pump-noise/index.html',
 'guides/how-to-improve-epc-rating/index.html', 'guides/planning-permission-heat-pump/index.html',
 'guides/radiator-sizing-heat-pump/index.html', 'guides/warm-homes-plan-2026/index.html',
}
LABELS = [
 ('>Ofgem Q1 2026 price cap</a>', '>Ofgem price cap, October to December 2026</a>'),
 ('>Ofgem Q1 2026</a>', '>Ofgem price cap, October to December 2026</a>'),
 ('Ofgem</a> Q1 2026 price cap', 'Ofgem</a> price cap, October to December 2026'),
 ('Ofgem</a> Q1 2026', 'Ofgem</a> price cap, October to December 2026'),
 ('Updated March 2026', 'Updated September 2026'),
]
pages = sorted(set(glob.glob('index.html') + glob.glob('*/index.html') + glob.glob('guides/*/index.html')))
report = {}
for f in pages:
    if f in UNTOUCHED:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    for old, new in LABELS:
        s = s.replace(old, new)
    if f.startswith('guides/') and f != 'guides/index.html':
        s, n = re.subn(r'"dateModified": ?"2026-03-\d\d"', '"dateModified":"2026-09-06"', s)
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        report[f] = True
    left = re.findall(r'.{0,50}Q1 2026.{0,30}', s)
    if left and f != 'guides/heat-pump-cost-4-bed-house/index.html':
        print('LEFTOVER', f, left)
print('rewritten %d pages' % len(report))
