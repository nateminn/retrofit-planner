#!/usr/bin/env python3
"""Internal linking sweep: add a related-link card on each source page for the target guide,
unless the source already links to the target somewhere in its body (nav and footer ignored).
usage: link_sweep.py [--dry]"""
import re, sys, os

ICONS = {
    'house': '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>',
    'pound': '<line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
    'thermo': '<path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"/>',
    'file': '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>',
    'sun': '<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>',
    'layers': '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
    'droplet': '<path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/>',
    'chart': '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
    'zap': '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    'users': '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
}

# target slug: (card name, card description, icon, [source slugs])  ("_" prefix = calculator or tool page at site root)
PLAN = {
    'energy-bills-by-household-size': ('Bills by Household Size', '1 to 5+ person homes', 'users', ['average-energy-bills-uk', 'energy-bills-by-epc-rating', 'heat-pump-running-costs', 'warm-home-discount']),
    'underfloor-insulation-cost': ('Underfloor Insulation', 'Costs and savings', 'layers', ['is-loft-insulation-worth-it', 'is-cavity-wall-insulation-worth-it', 'solid-wall-insulation-cost', 'draught-proofing-guide', '_insulation-calculator']),
    'storage-heaters-vs-heat-pump': ('Storage Heaters vs Heat Pump', 'Save £1,200 to £2,700 a year', 'thermo', ['electric-boiler-vs-heat-pump', 'heat-pump-flat', 'heat-pump-running-costs', 'best-heat-pump-tariffs']),
    'heat-pump-cost-4-bed-house': ('4-Bed House Costs', 'Full 2026 breakdown', 'house', ['heat-pump-running-costs', 'radiator-sizing-heat-pump', 'boiler-upgrade-scheme-guide', '_heat-pump-calculator', 'heat-pump-vs-new-boiler']),
    'condensation-mould-guide': ('Condensation and Mould', 'Causes and fixes', 'droplet', ['draught-proofing-guide', 'is-cavity-wall-insulation-worth-it', 'solid-wall-insulation-cost', 'how-to-improve-epc-rating']),
    'warm-homes-plan-2026': ('Warm Homes Plan', 'What replaces ECO4', 'file', ['eco4-scheme-explained', 'great-british-insulation-scheme', 'home-upgrade-grant', '_grants']),
    'warm-home-discount': ('Warm Home Discount', '£150 off your bill', 'pound', ['average-energy-bills-uk', 'energy-bills-by-household-size', 'eco4-scheme-explained', '_grants']),
    'how-epc-points-are-calculated': ('How EPC Points Work', 'The scoring explained', 'chart', ['_epc-calculator', 'how-to-improve-epc-rating', 'epc-rating-landlords', 'energy-bills-by-epc-rating']),
    'heat-pump-flat': ('Heat Pumps in Flats', 'Costs, rules and options', 'house', ['heat-pump-cost-by-house-type', 'planning-permission-heat-pump', 'heat-pump-noise', 'storage-heaters-vs-heat-pump']),
    'solar-battery-storage-uk': ('Solar Battery Storage', 'Is a battery worth it?', 'zap', ['are-solar-panels-worth-it-uk', 'solar-panel-payback-uk', '_solar-calculator']),
    'home-upgrade-grant': ('Home Upgrade Grant', 'Up to £25,000 off-gas', 'pound', ['eco4-scheme-explained', '_grants', 'boiler-upgrade-scheme-guide', 'warm-homes-plan-2026']),
    'great-british-insulation-scheme': ('GB Insulation Scheme', 'Free insulation, no benefits needed', 'layers', ['eco4-scheme-explained', 'is-loft-insulation-worth-it', 'free-loft-insulation-uk', '_grants']),
    'heat-pump-cost-3-bed-semi': ('3-Bed Semi Costs', 'Prices, sizing, models', 'house', ['_heat-pump-calculator', 'radiator-sizing-heat-pump', 'heat-pump-vs-new-boiler']),
    'energy-bills-by-epc-rating': ('Bills by EPC Band', 'What each band pays', 'chart', ['_epc-calculator', 'how-epc-points-are-calculated', 'average-energy-bills-uk']),
    'solar-panel-payback-uk': ('Solar Payback', 'How long to break even', 'sun', ['_solar-calculator', 'are-solar-panels-worth-it-uk', 'solar-battery-storage-uk']),
    'radiator-sizing-heat-pump': ('Radiator Sizing', 'Do you need bigger?', 'thermo', ['_heat-pump-calculator', 'heat-pump-cost-4-bed-house', 'heat-pump-old-house']),
}

def page_path(slug):
    return (slug[1:] + '/index.html') if slug.startswith('_') else ('guides/' + slug + '/index.html')

def card(target, name, desc, icon):
    return ('<a href="/guides/%s/" class="related-link-card"><div class="rl-icon"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">%s</svg></div>'
            '<div class="rl-text"><div class="rl-name">%s</div><div class="rl-desc">%s</div></div></a>\n') % (target, ICONS[icon], name, desc)

dry = '--dry' in sys.argv
added = 0; touched = set(); skipped = 0
for target, (name, desc, icon, sources) in PLAN.items():
    assert os.path.exists(page_path(target)), target
    for src in sources:
        p = page_path(src); s = open(p, encoding='utf-8').read()
        body = re.sub(r'<nav.*?</nav>', '', s, flags=re.S); body = re.sub(r'<footer.*?</footer>', '', body, flags=re.S)
        if ('href="/guides/%s/"' % target) in body:
            skipped += 1; continue
        i = s.find('<div class="related-links">')
        if i < 0:
            print('%-40s <- %s   SKIPPED, no related-links block' % (target, src)); continue
        # cards are contiguous <a ... class="related-link-card">...</a> elements; insert after the last one
        cards = list(re.finditer(r'<a href="[^"]*" class="related-link-card">.*?</a>', s[i:], re.S))
        assert cards, ('no cards in block on', p)
        end = i + cards[-1].end()
        s = s[:end] + '\n' + card(target, name, desc, icon).rstrip('\n') + s[end:]
        if not dry: open(p, 'w', encoding='utf-8').write(s)
        touched.add(p); added += 1
        print('%-40s <- %s' % (target, src))
print('cards added', added, '| already linked', skipped, '| pages touched', len(touched), '(dry run)' if dry else '')
