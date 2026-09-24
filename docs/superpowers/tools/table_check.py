#!/usr/bin/env python3
"""Check property-by-property tables against the shared heat model.

WHY THIS EXISTS SEPARATELY FROM model_check.py. That tool asks whether a page states
the model's heat demand for its one property basis. It cannot police a table listing
seven house types, because there is no single basis to compare against. Seven of the
site's biggest pages are exactly that shape, and they drifted for months: a 5-bed
detached was 24,000 kWh in one table, 26,370 implied by another and 19,500 in the model.

Worse, storage-heaters-vs-heat-pump drifted invisibly because its table states only
derived costs and never a kWh figure, so a scan looking for kWh could not see it. This
tool works from the costs back to the model, which is what catches that case.

WHAT IT DOES. For each table named in SPECS, map every row's property label to a model
cell, work out what each column should hold, and compare. Anything outside tolerance is
reported with both figures and the arithmetic.

WHAT IT DELIBERATELY DOES NOT DO. It does not check solar generation, EPC band medians
or electricity baseload. Those are real quantities the heat model does not produce, and
pretending otherwise would generate noise that gets ignored, which is how the first
drift went unnoticed.
"""
import json, re, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]

GAS_P, ELEC_P, HPT_P = 0.0797, 0.2632, 0.18
GAS_STANDING, ELEC_STANDING = 108.33, 200.13

M = json.loads(subprocess.run(
    ['node', '-e',
     "global.window={};require('./js/heat-model.js');const H=window.RP_HEAT;const o={};"
     "for(const t of ['detached','semi','mid-terrace','end-terrace','bungalow','flat'])"
     "for(const b of [1,2,3,4,5])for(const i of ['poor','average','good','excellent'])"
     "o[t+'|'+b+'|'+i]={gas:H.gasKwh(t,b,i),heat:H.heatDemand(t,b,i),cop:H.cop(i)};"
     "console.log(JSON.stringify(o));"],
    capture_output=True, text=True, cwd=ROOT).stdout)

# Row label to model cell. Ordered: the first pattern that matches wins, so put the
# more specific ones first.
LABELS = [
    (r'^1[\s-]*2 bed flat',            ('flat', 2)),      # a range label; use the larger
    (r'^(\d)[\s-]*bed flat',           ('flat', None)),
    (r'^flat$',                        ('flat', 2)),
    (r'mid[\s-]*terrace.*\((\d) bed',  ('mid-terrace', None)),
    (r'^(\d)[\s-]*bed (?:mid[\s-]*)?terrace', ('mid-terrace', None)),
    (r'^(\d)[\s-]*bed end[\s-]*terrace', ('end-terrace', None)),
    (r'end[\s-]*terrace.*\((\d) bed',  ('end-terrace', None)),
    (r'^(\d)[\s-]*bed semi',           ('semi', None)),
    (r'semi.*\((\d) bed',              ('semi', None)),
    (r'^(\d)[\s-]*bed detached',       ('detached', None)),
    (r'detached.*\((\d) bed',          ('detached', None)),
    (r'^(\d)[\s-]*bed bungalow',       ('bungalow', None)),
    (r'bungalow.*\((\d) bed',          ('bungalow', None)),
]

# Some tables carry the insulation in the row label rather than in a column, e.g.
# "Semi-detached (3 bed, old)" or "3 bed semi (good insulation)".
LABEL_INSULATION = [
    (r'\bold\b|poorly insulated|solid wall', 'poor'),
    (r'good insulation|well[\s-]*insulated', 'good'),
    (r'average insulation', 'average'),
]

def insulation_from_label(label):
    lab = label.strip().lower()
    for pat, ins in LABEL_INSULATION:
        if re.search(pat, lab):
            return ins
    return None

def cell_for(label):
    lab = label.strip().lower()
    for pat, (ptype, fixed_beds) in LABELS:
        m = re.search(pat, lab)
        if not m:
            continue
        beds = fixed_beds if fixed_beds else int(m.group(1))
        return ptype, beds
    return None

# Column header to the quantity it should hold.
def quantity_for(header):
    h = header.lower()
    # A saving is a difference between two of the other columns, not a quantity the
    # model produces. Its header usually contains "HP tariff", so this has to come
    # first or every saving column is checked as though it were a running cost.
    if 'saving' in h:                                 return None
    if 'heat demand' in h:                            return 'heat_kwh'
    if 'kwh' in h and 'gas' in h:                     return 'gas_kwh'
    if 'electric boiler' in h:                        return 'elec_boiler'
    if 'storage heater' in h:                         return None      # Economy 7, supplier set
    if 'hp tariff' in h or 'heat pump tariff' in h:   return 'hp_tariff'
    if 'heat pump' in h or h.startswith('hp '):       return 'hp_standard'
    if 'gas' in h:                                    return 'gas_cost'
    return None

def expected(qty, ptype, beds, insulation, standing):
    c = M['%s|%d|%s' % (ptype, beds, insulation)]
    if qty == 'gas_kwh':      return c['gas']
    if qty == 'heat_kwh':     return c['heat']
    if qty == 'gas_cost':     return c['gas'] * GAS_P + (GAS_STANDING if standing else 0)
    if qty == 'hp_standard':  return c['heat'] / c['cop'] * ELEC_P + (ELEC_STANDING if standing else 0)
    if qty == 'hp_tariff':    return c['heat'] / c['cop'] * HPT_P + (ELEC_STANDING if standing else 0)
    if qty == 'elec_boiler':  return c['heat'] * ELEC_P + (ELEC_STANDING if standing else 0)
    return None

# page, table index, insulation basis, whether money columns carry the standing charge.
# insulation may be a column index instead, when the table states it per row.
SPECS = [
    dict(page='guides/average-energy-bills-uk/index.html',      table=1, insulation=2, standing=True),
    dict(page='guides/average-energy-bills-uk/index.html',      table=0, insulation='average', standing=True,
         only=['gas_cost']),
    dict(page='guides/energy-bills-by-household-size/index.html', table=1, insulation='good', standing=True,
         only=['gas_cost']),
    dict(page='guides/heat-pump-running-costs/index.html',      table=0, insulation='average', standing=False),
    dict(page='guides/heat-pump-cost-by-house-type/index.html', table=5, insulation='average', standing=False),
    dict(page='guides/storage-heaters-vs-heat-pump/index.html', table=0, insulation='average', standing=False),
    dict(page='guides/electric-boiler-vs-heat-pump/index.html', table=0, insulation='average', standing=False),
    dict(page='guides/heat-pump-vs-new-boiler/index.html',      table=1, insulation='average', standing=False),
]

def tol(qty, exp):
    # kWh: the model is a median fitted to NEED, so a page rounding to the nearest 500
    # is fine. Money: 3 per cent or £12, whichever is larger, absorbs rounding in the
    # page's own intermediate steps without hiding a real drift.
    if qty.endswith('_kwh'):
        return max(300, exp * 0.05)
    return max(12, exp * 0.03)

def cells(row):
    return [' '.join(re.sub(r'<[^>]+>', ' ', c).split())
            for c in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.S)]

def money(s):
    m = re.match(r'^£?([\d,]+)(?:\s*to\s*£?([\d,]+))?$', s.strip())
    if not m: return None
    lo = float(m.group(1).replace(',', ''))
    return lo if not m.group(2) else (lo, float(m.group(2).replace(',', '')))

def main():
    problems, checked, unmapped = [], 0, []
    for spec in SPECS:
        f = ROOT / spec['page']
        if not f.exists():
            problems.append((spec['page'], '', 'page missing', '', '')); continue
        tables = re.findall(r'<table[^>]*>(.*?)</table>', f.read_text(), re.S)
        if spec['table'] >= len(tables):
            problems.append((spec['page'], '', 'table %d not found' % spec['table'], '', '')); continue
        rows = re.findall(r'<tr>(.*?)</tr>', tables[spec['table']], re.S)
        header = cells(rows[0])
        name = spec['page'].replace('guides/', '').replace('/index.html', '')
        for row in rows[1:]:
            c = cells(row)
            if not c: continue
            cell = cell_for(c[0])
            if not cell:
                unmapped.append('%s: %s' % (name, c[0])); continue
            ptype, beds = cell
            ins = insulation_from_label(c[0]) or spec['insulation']
            if isinstance(ins, int):
                ins = c[ins].strip().lower()
                if ins not in ('poor', 'average', 'good', 'excellent'):
                    unmapped.append('%s: insulation %r' % (name, ins)); continue
            for i, head in enumerate(header[1:], start=1):
                if i >= len(c): continue
                qty = quantity_for(head)
                if not qty: continue
                if spec.get('only') and qty not in spec['only']: continue
                got = money(c[i])
                if got is None: continue
                exp = expected(qty, ptype, beds, ins, spec['standing'])
                if exp is None: continue
                checked += 1
                lo, hi = (got, got) if isinstance(got, float) else got
                t = tol(qty, exp)
                if not (lo - t <= exp <= hi + t):
                    problems.append((name, c[0], head, c[i], '%.0f' % exp))
    for name, row, col, got, exp in problems:
        print('  %-30s %-22s %-26s page %s, model %s' % (name, row[:22], col[:26], got, exp))
    if unmapped:
        print('  unmapped rows (not failures, but nothing checked them):')
        for u in sorted(set(unmapped)): print('    %s' % u)
    print('%s: %d table cells checked against js/heat-model.js, %d disagree'
          % ('FAIL' if problems else 'PASS', checked, len(problems)))
    return 1 if problems else 0

if __name__ == '__main__':
    sys.exit(main())
