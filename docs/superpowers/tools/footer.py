#!/usr/bin/env python3
"""Replace the footer Guides column on every page with the canonical block."""
import glob, re

CANON = ('<div class="footer-col"><h4>Guides</h4>'
         '<a href="/guides/heat-pump-cost-4-bed-house/">Heat Pump Cost: 4-Bed House</a>'
         '<a href="/guides/heat-pump-cost-by-house-type/">Costs by House Type</a>'
         '<a href="/guides/heat-pump-running-costs/">Heat Pump Running Costs</a>'
         '<a href="/guides/best-heat-pump-tariffs/">Best Heat Pump Tariffs</a>'
         '<a href="/guides/boiler-upgrade-scheme-guide/">BUS Grant Guide</a>'
         '<a href="/guides/how-epc-points-are-calculated/">How EPC Points Are Calculated</a>'
         '</div>')
PATTERN = re.compile(r'<div class="footer-col">\s*<h4>Guides</h4>.*?</div>', re.S)

pages = sorted(set(glob.glob('index.html') + glob.glob('*/index.html') + glob.glob('guides/*/index.html')) - {'thank-you/index.html'})
if glob.glob('404.html'):
    pages.append('404.html')
changed = 0
for f in pages:
    s = open(f, encoding='utf-8').read()
    n = len(PATTERN.findall(s))
    assert n == 1, '%s: expected 1 Guides block, found %d' % (f, n)
    new = PATTERN.sub(lambda m: CANON, s)
    if new != s:
        open(f, 'w', encoding='utf-8').write(new)
        changed += 1
print('pages scanned %d, rewritten %d' % (len(pages), changed))
