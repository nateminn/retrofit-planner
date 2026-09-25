#!/usr/bin/env python3
"""Find figures the old heat model produced that are still on the site.

The model was recalibrated on 24 September 2026 (heat pump efficiency from the
Electrification of Heat trial, installed cost from Boiler Upgrade Scheme medians). Every
page that quoted the old model has to move with it. This lists any page still carrying a
figure that only the old model produced: running costs, installed ranges, after-grant
ranges and efficiencies, plus retired claims such as a non-existent insulation scheme.

Pages that deliberately quote the old figures to compare them (the accuracy page) and the
methodology's one sentence about the old efficiency range are exempt.

On 25 September 2026 the prices moved: heating oil to 11.3p, the heat pump tariff to
19.8p and a new gas boiler to about £3,500. The canon keeps the figures from before that
change as "prior", and this also flags any prior tariff or oil figure, or a saving worked
out from one, that still sits near the word it belongs to.

Usage: python3 docs/superpowers/tools/stale_check.py   (exit code 1 if anything is found)
"""
import json, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
EXEMPT = {'accuracy/index.html'}

# Old model outputs at average insulation, and ranges the guides quoted from it.
TOKENS = [
    # running costs, heat pump standard / tariff (old efficiency 2.9)
    '£899', '£614', '£1,193', '£816', '£956', '£654', '£580', '£397', '£572', '£391', '£841', '£575', '£1,593', '£1,089',
    # installed and after-grant ranges from the old cost model
    '£9,000 to £12,000', '£1,500 to £4,500', '£11,000 to £16,000', '£3,500 to £8,500', '£8,000 to £10,000',
    '£500 to £2,500', '£10,000 to £13,000', '£2,500 to £5,500', '£13,000 to £19,000', '£5,500 to £11,500',
    '£7,000 to £10,000', '£0 to £2,500', '£9,000 to £11,000',
    # retired claims
    'GB Energy Scheme', 'gas ban likely',
]
# Generic ranges that other measures legitimately share only count near a heat pump.
HEAT_PUMP_ONLY = {'£500 to £2,500', '£8,000 to £10,000', '£0 to £2,500'}
BOILER_PHASE = re.compile(r'boilers?[^.<]{0,40}(?:being |be )?phased out', re.I)
EFFICIENCY = re.compile(r'\b(?:COP|SCOP|efficiency|coefficient of performance)[^.<]{0,60}\b(2\.9|3\.4|2\.6 to 3\.4)\b', re.I)


def price_tokens():
    """Figures that only the pre 25 September 2026 prices produced, each with the words
    that must be nearby for it to count, and none equal to any figure the model gives now."""
    canon = json.loads((ROOT / 'docs' / 'model-canon.json').read_text())
    now = set()
    for c in canon.values():
        n = c['new']
        for v in n.values():
            if isinstance(v, (int, float)):
                now.add(round(v))
        costs = ('gas_cost', 'gas_cost_with_standing', 'oil_cost', 'lpg_cost', 'electric_boiler', 'hp_standard', 'hp_tariff')
        for a in costs:
            for b in costs:
                now.add(abs(round(n[a] - n[b])))   # any difference between two of today's running costs
    toks = {}
    for c in canon.values():
        p, n = c.get('prior'), c['new']
        if not p:
            continue
        cands = [(p['hp_tariff'], n['hp_tariff'], 'tariff'), (p['oil_cost'], n['oil_cost'], r'\boil\b|kerosene'),
                 (p['gas_cost'] - p['hp_tariff'], n['gas_cost'] - n['hp_tariff'], 'tariff'),
                 (p['oil_cost'] - p['hp_tariff'], n['oil_cost'] - n['hp_tariff'], r'\boil\b'),
                 (p['oil_cost'] - p['hp_standard'], n['oil_cost'] - n['hp_standard'], r'\boil\b'),
                 (p['electric_boiler'] - p['hp_tariff'], n['electric_boiler'] - n['hp_tariff'], 'tariff'),
                 (p['lpg_cost'] - p['hp_tariff'], n['lpg_cost'] - n['hp_tariff'], 'tariff')]
        for old, new, near in cands:
            old = round(old)
            if old != round(new) and old >= 100 and old not in now:
                toks['£{:,}'.format(old)] = near
    return toks


PRICE_TEXT = [  # (pattern, words that must be near, or None)
    (r'\b18p\b', r'heat pump tariff|tariff at|on an? 18p'),
    (r'\b9\.0p\b', None),
    (r'\b9p per kWh', r'\boil\b'),
    (r'£1,500 to £3,500', r'boiler'),
    (r'[Kk]erosene (cost|has been) (more|dearer)', None),
    (r'below September 2026', None),
]


def visible(html):
    # Titles and meta, og and twitter descriptions are what searchers see first, so they count.
    heads = ' '.join(re.findall(r'<title>(.*?)</title>', html) +
                     re.findall(r'<meta (?:name|property)="(?:description|og:title|og:description|twitter:title|twitter:description)" content="([^"]*)"', html))
    html = heads + ' . ' + html
    html = re.sub(r'<script(?![^>]*ld\+json).*?</script>', ' ', html, flags=re.S)
    html = re.sub(r'<text class="tick"[^>]*>.*?</text>', ' ', html, flags=re.S)   # chart axis labels
    html = re.sub(r'<style.*?</style>', ' ', html, flags=re.S)
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html))


PRICE_TOKENS = price_tokens()
# The accuracy page reports what changed and when, so it may quote the old figures. The
# pages build_new_pages.py writes take every figure from the model, so only their wording
# is checked (PRICE_TEXT); their tables are full of monthly figures that match old ones by chance.
PRICE_EXEMPT = {'accuracy/index.html'}
GENERATED = {'guides/%s/index.html' % g for g in (
    'what-size-heat-pump', 'energy-bills-1-bed-flat', 'energy-bills-2-bed-house', 'energy-bills-3-bed-house',
    'energy-bills-4-bed-house', 'energy-bills-5-bed-house', 'heat-pump-cost-3-bed-mid-terrace', 'heat-pump-1930s-semi',
    'insulation-cost-by-house-type', 'insulation-cost-semi-detached-house', 'insulation-cost-detached-house',
    'insulation-cost-terraced-house', 'insulation-cost-bungalow', 'insulation-cost-flat',
    'solar-panel-payback-by-region', 'solar-panel-payback-south-england', 'solar-panel-payback-midlands', 'solar-panel-payback-north-england', 'solar-panel-payback-wales', 'solar-panel-payback-scotland', 'heat-pumps-by-council')}


def main():
    found = []
    for f in sorted(ROOT.rglob('*.html')):
        rel = f.relative_to(ROOT).as_posix()
        if rel.startswith('docs/') or rel in EXEMPT:
            continue
        text = visible(f.read_text())
        for t in TOKENS:
            for m in re.finditer(re.escape(t), text):
                ctx = text[max(0, m.start() - 70):m.end() + 50]
                if rel == 'methodology/index.html' and 'Until 24 September 2026' in ctx:
                    continue
                if t in HEAT_PUMP_ONLY and 'heat pump' not in text[max(0, m.start() - 160):m.end() + 80].lower():
                    continue
                found.append((rel, t, ctx.strip()))
        for m in BOILER_PHASE.finditer(text):
            found.append((rel, 'boilers phased out', text[max(0, m.start() - 40):m.end() + 30].strip()))
        if rel not in PRICE_EXEMPT:
            for tok, near in ({} if rel in GENERATED else PRICE_TOKENS).items():
                for m in re.finditer(re.escape(tok) + r'(?![\d,])', text):
                    win = text[max(0, m.start() - 160):m.end() + 100]
                    if re.search(near, win, re.I):
                        found.append((rel, tok + ' (before 25 Sep)', text[max(0, m.start() - 70):m.end() + 50].strip()))
            for pat, near in PRICE_TEXT:
                for m in re.finditer(pat, text):
                    win = text[max(0, m.start() - 160):m.end() + 100]
                    if near is None or re.search(near, win, re.I):
                        found.append((rel, m.group(0) + ' (before 25 Sep)', text[max(0, m.start() - 70):m.end() + 50].strip()))
        for m in EFFICIENCY.finditer(text):
            ctx = text[max(0, m.start() - 30):m.end() + 40]
            if rel == 'methodology/index.html' and 'Until 24 September 2026' in text[max(0, m.start() - 200):m.end()]:
                continue
            found.append((rel, m.group(1), ctx.strip()))
    allow = set()
    af = ROOT / 'docs' / 'superpowers' / 'tools' / 'stale_allow.txt'
    if af.exists():
        for line in af.read_text().splitlines():
            if line.strip() and not line.startswith('#'):
                page, tok = line.split('\t')[:2]
                allow.add((page, tok))
    found = [(r, t, c) for r, t, c in found if (r, t.replace(' (before 25 Sep)', '')) not in allow]
    for rel, t, ctx in found:
        print('  %-48s %-22s ...%s...' % (rel[:48], t, ctx[:150]))
    pages = len(set(r for r, _, _ in found))
    print('%s: %d stale figures on %d pages' % ('FAIL' if found else 'PASS', len(found), pages))
    return 1 if found else 0


if __name__ == '__main__':
    sys.exit(main())
