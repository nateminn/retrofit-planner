#!/usr/bin/env python3
"""Guard for the price refresh. Reproduces the figures currently on the pages from the
site's stated model at the OLD rates (tolerance 2 pounds), then prints the NEW figures."""
import sys
OLD = dict(E=0.245, G=0.0676, SCE=0.6164, SCG=0.3165, HP=0.16)
NEW = dict(E=0.2632, G=0.0797, SCE=0.5483, SCG=0.2968, HP=0.18)
def gas(d, r): return round(d / 0.9 * r['G'])
def hpstd(d, r, cop=2.9): return round(d / cop * r['E'])
def hptar(d, r, rate=None): return round(d / 2.9 * (rate or r['HP']))
def eboil(d, r): return round(d * r['E'])
def bill_gas(k, r): return round(k * r['G'] + 365 * r['SCG'])
def bill_elec(k, r): return round(k * r['E'] + 365 * r['SCE'])
D5 = (8000, 12000, 15000, 18000, 22000)
D4 = (8000, 12000, 15000, 18000)
checks = [
 ('running-costs gas', [gas(d, OLD) for d in D5], [601, 901, 1127, 1352, 1653]),
 ('running-costs hp standard', [hpstd(d, OLD) for d in D5], [676, 1014, 1267, 1521, 1859]),
 ('running-costs hp tariff 16p', [hptar(d, OLD) for d in D5], [441, 662, 828, 993, 1214]),
 ('running-costs hp tariff upper bound (19.2p on the page)', [hptar(d, OLD, 0.192) for d in D5], [529, 794, 993, 1192, 1457]),
 ('electric boiler', [eboil(d, OLD) for d in D4], [1960, 2940, 3675, 4410]),
 ('vs-boiler 15yr running totals', [(901 + 100) * 15, (1014 + 65) * 15, (662 + 65) * 15], [15015, 16185, 10905]),
 ('avg-bills gas by kWh', [bill_gas(k, OLD) for k in (5500, 8500, 14000)], [487, 690, 1062]),
 ('avg-bills elec by kWh', [bill_elec(k, OLD) for k in (1800, 2300, 2700, 3500)], [666, 789, 887, 1083]),
 ('solar 45% self-use', [round(g * 0.45 * OLD['E']) for g in (2850, 3800, 3320, 5700)], [314, 419, 366, 628]),
 ('solar 80% self-use with battery', [round(3800 * 0.8 * OLD['E'])], [745]),
 ('solar export 55% at 8p', [round(g * 0.55 * 0.08) for g in (2850, 3800, 3320, 5700)], [125, 167, 146, 250]),
 ('ground source 4-bed COP 3.7 at 16p', [round(18000 / 3.7 * 0.16)], [778]),
]
ok = True
for name, got, exp in checks:
    good = all(abs(a - b) <= 2 for a, b in zip(got, exp)) and len(got) == len(exp)
    ok &= good
    print(('PASS ' if good else 'FAIL ') + name + ('' if good else '  got %s expected %s' % (got, exp)))
known = [(11500, 905), (18000, 1347), (24000, 1856)]
print('KNOWN avg-bills gas rows that do not reproduce (recompute from the stated kWh):',
      [(k, bill_gas(k, OLD), page) for k, page in known])
print()
print('NEW gas 8k..22k        ', [gas(d, NEW) for d in D5])
print('NEW hp standard        ', [hpstd(d, NEW) for d in D5])
print('NEW hp tariff 18p      ', [hptar(d, NEW) for d in D5])
print('NEW hp tariff 17p      ', [hptar(d, NEW, 0.17) for d in D5])
print('NEW hp tariff 20p      ', [hptar(d, NEW, 0.20) for d in D5])
print('NEW electric boiler    ', [eboil(d, NEW) for d in D4])
print('NEW avg-bills gas      ', [bill_gas(k, NEW) for k in (5500, 8500, 11500, 14000, 18000, 24000)])
print('NEW avg-bills elec     ', [bill_elec(k, NEW) for k in (1800, 2300, 2700, 3500)])
print('NEW ofgem typical 2500/9500', bill_elec(2500, NEW) + bill_gas(9500, NEW))
print('NEW solar 45%          ', [round(g * 0.45 * NEW['E']) for g in (2850, 3800, 3320, 5700)], 'battery 80%:', round(3800 * 0.8 * NEW['E']))
print('NEW 4-bed: gas %d, hp std %d, hp tariff %d, elec boiler %d, gshp %d, semi14k gas %d hp %d tariff %d' % (
    gas(18000, NEW), hpstd(18000, NEW), hptar(18000, NEW), eboil(18000, NEW), round(18000 / 3.7 * 0.18),
    gas(14000, NEW), hpstd(14000, NEW), hptar(14000, NEW)))
sys.exit(0 if ok else 1)
