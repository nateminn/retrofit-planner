#!/usr/bin/env python3
"""Check that guide pages agree with the shared heat model in js/heat-model.js.

Two checks:
Each guide with a known property basis must state the model's heat demand for that
property somewhere on the page. Prose drifting from the calculators is how the site
ended up with three different answers for the same house.
"""
import io, re, sys, glob, json, subprocess

GAS, ELEC, HPT, OIL, BOILER = 0.0797, 0.2632, 0.18, 0.090, 0.90

M = json.loads(subprocess.run(
    ['node', '-e', "global.window={};require('./js/heat-model.js');"
                   "console.log(JSON.stringify(window.RP_HEAT.model));"],
    capture_output=True, text=True).stdout)

BASIS = {
    'heat-pump-cost-2-bed-terrace':  ('mid-terrace', 2, 'average'),
    'heat-pump-cost-3-bed-semi':     ('semi', 3, 'average'),
    'heat-pump-cost-3-bed-detached': ('detached', 3, 'average'),
    'heat-pump-cost-4-bed-house':    ('detached', 4, 'average'),
    'heat-pump-cost-5-bed-house':    ('detached', 5, 'average'),
    'heat-pump-cost-bungalow':       ('bungalow', 3, 'average'),
    'heat-pump-victorian-terrace':   ('mid-terrace', 3, 'poor'),
    'heat-pump-flat':                ('flat', 2, 'average'),
    'heat-pump-cost-end-terrace':    ('end-terrace', 3, 'average'),
    'heat-pump-1960s-house':         ('semi', 3, 'average'),
    'heat-pump-cost-2-bed-bungalow': ('bungalow', 2, 'average'),
    # Added after the September 2026 drift audit. These six state a single property
    # basis and had all wandered off it: 12,000 and 15,000 kWh for a 3-bed semi the
    # model puts at 9,900. The other seven pages that state a kWh figure present many
    # property types in one table, which a single-basis check cannot police, so they
    # are deliberately not here and need a different check.
    'boiler-upgrade-scheme-guide':   ('semi', 3, 'average'),
    'home-upgrade-grant':            ('semi', 3, 'average'),
    'best-heat-pump-tariffs':        ('semi', 3, 'average'),
    'heat-pump-vs-new-boiler':       ('semi', 3, 'average'),
    'electric-boiler-vs-heat-pump':  ('semi', 3, 'average'),
    # Added after storage-heaters-vs-heat-pump was found carrying the same wrong demand
    # ladder. The original audit scoped itself to pages stating a kWh figure, and this
    # page states only derived costs, so it was invisible to that scan.
    'storage-heaters-vs-heat-pump':  ('semi', 3, 'average'),
}

def heat(t, b, ins):
    return round(M['gas'][t][str(b)] * M['insulation'][ins] * BOILER)

# These guides express heat demand both in prose ("12,000 kWh of heat demand") and in
# table cells ("8,000 kWh | 4 to 5 kW | ..."), so match any kWh figure in the plausible
# heat demand range rather than one sentence shape.
DEMAND = re.compile(r'([\d,]{3,7})\s*kWh', re.I)

def check(path):
    """A guide may quote other properties for comparison, so the test is not "mentions the
    right number somewhere". It is that the guide's OWN property figure is present AND that
    the figures it does quote are all cells of the model, so nothing is invented."""
    slug = path.split('/')[-2]
    basis = BASIS.get(slug)
    if not basis:
        return []
    s = io.open(path, encoding='utf-8').read()
    body = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', s, flags=re.S)
    body = re.sub(r'<[^>]+>', ' ', body)
    body = re.sub(r'\s+', ' ', body)
    stated = sorted({int(m.group(1).replace(',', '')) for m in DEMAND.finditer(body)})
    stated = [h for h in stated if 2000 <= h <= 40000]
    want = heat(*basis)
    problems = []

    if not any(abs(h - want) <= max(300, want * 0.05) for h in stated):
        problems.append(f"does not state its own figure of {want:,} kWh "
                        f"({basis[1]}-bed {basis[0]}, {basis[2]} insulation). Found: "
                        + (', '.join(f'{h:,}' for h in stated) if stated else 'none'))

    # every other kWh figure should be a real cell of the model, not an invented number
    cells = sorted({heat(t, b, i) for t in M['gas'] for b in '12345' for i in M['insulation']})
    stray = [h for h in stated
             if not any(abs(h - c) <= max(300, c * 0.05) for c in cells)]
    if stray:
        problems.append("heat demand figures matching no cell of the model: "
                        + ', '.join(f'{h:,}' for h in stray))
    return problems

if __name__ == '__main__':
    paths = sys.argv[1:] or sorted(glob.glob('guides/*/index.html'))
    bad = 0
    for p in paths:
        probs = sorted(set(check(p)))
        if probs:
            bad += 1
            print(f"  {p.split('/')[-2]}")
            for x in probs[:6]:
                print(f"      {x}")
    print(("FAIL: %d guide(s) disagree with js/heat-model.js" % bad) if bad
          else "PASS: every heat demand figure matches js/heat-model.js")
    sys.exit(1 if bad else 0)
