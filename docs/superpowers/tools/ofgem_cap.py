#!/usr/bin/env python3
"""One place that knows the Ofgem cap, and one command to move the whole site to a new one.

Ofgem resets the cap every three months and announces it about five weeks ahead. The rates
are scattered across 29 pages, the chart and diagram generators, and two checkers, in both
pence form (26.32p) and decimal form (0.2632). Doing that by hand is how a site ends up
half refreshed.

    python3 docs/superpowers/tools/ofgem_cap.py --check
    python3 docs/superpowers/tools/ofgem_cap.py --set 25.11 7.42 55.10 30.20 \
        --period "1 January to 31 March 2027" --short "January to March 2027" --dry

Only the four cap figures are touched. The heat pump tariff (18p), the SEG rate (12p),
oil (9.0p) and LPG (9.5p) are different things and are deliberately left alone.
"""
import io, re, sys, glob, json, os

STATE = os.path.join(os.path.dirname(__file__), 'ofgem_cap.json')

CURRENT = {
    "elec": 26.32, "gas": 7.97, "elec_sc": 54.83, "gas_sc": 29.68,
    "period": "1 October to 31 December 2026",
    "short": "October to December 2026",
    "source": "https://www.ofgem.gov.uk/your-energy-supply/your-energy-bill/energy-price-cap-unit-rates-and-standing-charges",
    "checked": "2026-09-23",
}

def load():
    if os.path.exists(STATE):
        return json.load(open(STATE))
    return dict(CURRENT)

def files():
    return (sorted(set(glob.glob('index.html') + glob.glob('*/index.html')
                       + glob.glob('guides/*/index.html') + glob.glob('embed/*/index.html')))
            + ['docs/superpowers/tools/charts.py', 'docs/superpowers/tools/diagrams.py',
               'docs/superpowers/tools/model_check.py', 'docs/superpowers/tools/verify_model.py'])

def pence_re(v):
    """26.32 as a rate, not as part of a longer number or a money amount."""
    return re.compile(r'(?<![\d.£])' + re.escape(f'{v:.2f}') + r'(?![\d])')

def dec_re(v):
    return re.compile(r'(?<![\d.])' + re.escape(f'{v/100:.4f}') + r'(?![\d])')

def swap(text, old, new):
    n = 0
    for key in ('elec', 'gas', 'elec_sc', 'gas_sc'):
        o, w = old[key], new[key]
        if o == w:
            continue
        text, a = pence_re(o).subn(f'{w:.2f}', text)
        text, b = dec_re(o).subn(f'{w/100:.4f}', text)
        n += a + b
    for key in ('period', 'short'):
        if old[key] != new[key]:
            text, c = text.replace(old[key], new[key]), text.count(old[key])
            n += c
    return text, n

def check(cap):
    """What this can honestly verify.

    It cannot scan for "wrong rates": the site publishes many derived pence figures, such as
    the cost of a useful kWh of heat at a given COP, which are legitimately not the cap. What
    it CAN do is confirm the declared cap is actually present, that no superseded cap rate is
    left lying around unlabelled, and that the period label is not half updated.
    """
    SUPERSEDED = {
        # previous caps this site has carried, so a half finished refresh is caught
        '6.76': 'gas, January to March 2026',
        '24.86': 'electricity, January to March 2026',
        '25.73': 'electricity, July to September 2026',
        '6.99': 'gas, July to September 2026',
    }
    present, missing, leftovers, mixed = [], [], [], []
    labels = re.compile(r'(January to March|April to June|July to September|October to December) 20\d\d')
    for f in files():
        if not os.path.exists(f):
            continue
        s = io.open(f, encoding='utf-8').read()
        body = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', s, flags=re.S) if f.endswith('.html') else s
        has_cap = any(f"{cap[k]:.2f}" in body for k in ('elec', 'gas'))
        if has_cap:
            present.append(f)
            # a page quoting the cap should name the period it belongs to
            found = set(m.group(0) for m in labels.finditer(body))
            # "1 October 2026" is as good a label as "October to December 2026"
            start = re.match(r'(\d+ \w+) to \d+ \w+ (\d{4})', cap['period'])
            start_form = f"{start.group(1)} {start.group(2)}" if start else None
            named = cap['short'] in found or (start_form and start_form in body)
            if found and not named:
                mixed.append((f, sorted(found)))
        for val, what in SUPERSEDED.items():
            for m in re.finditer(r'(?<![\d.£])' + re.escape(val) + r'p(?![\w])', body):
                ctx = body[max(0, m.start() - 90):m.start() + 30]
                # a superseded rate is fine when the page says which period it was
                if not labels.search(ctx):
                    leftovers.append((f, val, what, ctx.strip()[-80:]))
    return present, leftovers, mixed

def canonical(cap, out='docs/superpowers/canonical-figures.md'):
    """Regenerate the canonical running cost table from the heat model and the current cap.

    Swapping the rate constants is only half a refresh: every derived figure on the guides
    (the £877 a year a 3-bed semi spends on gas, and so on) moves too, and those are baked
    into the HTML. This writes the table those pages must match, so the follow-up pass is
    mechanical and model_check.py can verify it.
    """
    import subprocess
    M = json.loads(subprocess.run(
        ['node', '-e', "global.window={};require('./js/heat-model.js');"
                       "console.log(JSON.stringify(window.RP_HEAT.model));"],
        capture_output=True, text=True).stdout)
    import sys as _sys, os as _os; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import prices as _prices
    GAS, ELEC, HPT, BOILER = cap['gas'] / 100, cap['elec'] / 100, _prices.HPT, 0.90
    LABEL = {'detached': 'Detached', 'semi': 'Semi-detached', 'end-terrace': 'End terrace',
             'mid-terrace': 'Mid terrace', 'bungalow': 'Bungalow', 'flat': 'Flat'}
    lines = [f"# Canonical heating figures", "",
             f"Generated from js/heat-model.js at the Ofgem cap for {cap['period']}:",
             f"electricity {cap['elec']}p, gas {cap['gas']}p. Heat pump tariff 18p effective, "
             f"boiler 90% efficient.", ""]
    for ins in ('good', 'average', 'poor'):
        cop = M['cop'][ins]
        lines += [f"## {ins.upper()} insulation (COP {cop})", "",
                  "| Property | Beds | Heat kWh | Gas £/yr | Heat pump, standard | Heat pump, 18p tariff |",
                  "|---|---|---|---|---|---|"]
        for t in LABEL:
            for b in (1, 2, 3, 4, 5):
                h = round(M['gas'][t][str(b)] * M['insulation'][ins] * BOILER)
                lines.append(f"| {LABEL[t]} | {b} | {h:,} | £{round(h/BOILER*GAS):,} | "
                             f"£{round(h/cop*ELEC):,} | £{round(h/cop*HPT):,} |")
        lines.append("")
    io.open(out, 'w', encoding='utf-8').write("\n".join(lines))
    return out, sum(1 for l in lines if l.startswith('| ') and not l.startswith('| Property'))

if __name__ == '__main__':
    cap = load()
    if '--set' in sys.argv:
        i = sys.argv.index('--set')
        new = dict(cap)
        new['elec'], new['gas'], new['elec_sc'], new['gas_sc'] = (float(x) for x in sys.argv[i+1:i+5])
        if '--period' in sys.argv: new['period'] = sys.argv[sys.argv.index('--period')+1]
        if '--short' in sys.argv:  new['short']  = sys.argv[sys.argv.index('--short')+1]
        dry = '--dry' in sys.argv
        total, touched = 0, []
        for f in files():
            if not os.path.exists(f):
                continue
            s = io.open(f, encoding='utf-8').read()
            out, n = swap(s, cap, new)
            if n:
                total += n; touched.append((f, n))
                if not dry:
                    io.open(f, 'w', encoding='utf-8').write(out)
        print(f"{'would change' if dry else 'changed'} {total} figures across {len(touched)} files")
        for f, n in touched[:60]:
            print(f"   {n:4}  {f}")
        if not dry:
            new['checked'] = None
            json.dump(new, open(STATE, 'w'), indent=1)
            print(f"\nstate written to {STATE}. Set 'checked' once you have verified against Ofgem.")
            f2, rows = canonical(new)
            print(f"canonical figures regenerated: {f2} ({rows} rows)")
            print("\nSTILL TO DO, because derived figures are baked into the pages:")
            print("  1. python3 docs/superpowers/tools/charts.py --replace")
            print("  2. python3 docs/superpowers/tools/diagrams.py --replace")
            print("  3. Update the running costs on the guides to match the canonical table,")
            print("     then: python3 docs/superpowers/tools/model_check.py")
            print("  4. python3 docs/superpowers/tools/gates.py")
        sys.exit(0)

    if '--canonical' in sys.argv:
        f2, rows = canonical(cap)
        print(f"wrote {f2} ({rows} rows) at the {cap['short']} cap")
        sys.exit(0)

    present, leftovers, mixed = check(cap)
    print(f"declared cap: electricity {cap['elec']}p, gas {cap['gas']}p, "
          f"standing {cap['elec_sc']}p and {cap['gas_sc']}p, {cap['period']}")
    print(f"  verified against Ofgem on {cap.get('checked') or 'NOT YET VERIFIED'}")
    print(f"  files carrying the cap: {len(present)}")
    if leftovers:
        print(f"\n  superseded cap rates with no period label: {len(leftovers)}")
        for f, v, what, ctx in leftovers[:10]:
            print(f"    {v}p ({what}) in {f}\n        ...{ctx}")
    if mixed:
        print(f"\n  pages quoting the cap but naming a different period: {len(mixed)}")
        for f, found in mixed[:10]:
            print(f"    {f}: {found}")
    if not leftovers and not mixed:
        print("\nPASS: the declared cap is consistent across the site")
    sys.exit(1 if (leftovers or mixed) else 0)
