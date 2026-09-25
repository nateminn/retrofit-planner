#!/usr/bin/env python3
"""Every page that keeps its own copy of the energy prices must agree with js/heat-model.js.

The shared model holds the site's prices (RP_HEAT.prices). Several pages still carry their
own copy in their scripts, because they run without the model or predate it. A price change
made in one place and not another is how two tools end up quoting different running costs
for the same home, so this reads each copy and compares it with the model.

Usage: python3 docs/superpowers/tools/prices_check.py   (exit code 1 on any mismatch)
"""
import pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import prices

ROOT = pathlib.Path(__file__).resolve().parents[3]
MODEL = {'gas': prices.GAS, 'electricity': prices.ELEC, 'oil': prices.OIL, 'lpg': prices.LPG, 'hpTariff': prices.HPT}

# (file, price, regex whose first group is the number)
COPIES = [
    ('heat-pump-calculator/index.html', 'electricity', r'energyPrices: \{ electricity: ([\d.]+)'),
    ('heat-pump-calculator/index.html', 'gas', r'energyPrices: \{[^}]*gas: ([\d.]+)'),
    ('heat-pump-calculator/index.html', 'oil', r'energyPrices: \{[^}]*oil: ([\d.]+)'),
    ('heat-pump-calculator/index.html', 'lpg', r'energyPrices: \{[^}]*lpg: ([\d.]+)'),
    ('embed/heat-pump-calculator/index.html', 'electricity', r'var PRICE=\{electricity:([\d.]+)'),
    ('embed/heat-pump-calculator/index.html', 'gas', r'var PRICE=\{[^}]*gas:([\d.]+)'),
    ('embed/heat-pump-calculator/index.html', 'oil', r'var PRICE=\{[^}]*oil:([\d.]+)'),
    ('embed/heat-pump-calculator/index.html', 'lpg', r'var PRICE=\{[^}]*lpg:([\d.]+)'),
    ('embed/heat-pump-calculator/index.html', 'hpTariff', r'TARIFF=([\d.]+)'),
    ('boiler-vs-heat-pump/index.html', 'gas', r'gasRate: ([\d.]+)'),
    ('boiler-vs-heat-pump/index.html', 'electricity', r'elecRate: ([\d.]+)'),
    ('boiler-vs-heat-pump/index.html', 'hpTariff', r'hpTariff: ([\d.]+)'),
    ('js/retrofit-plan.js', 'gas', r'var PRICE = \{ gas: ([\d.]+)'),
    ('js/retrofit-plan.js', 'oil', r'var PRICE = \{[^}]*oil: ([\d.]+)'),
    ('js/retrofit-plan.js', 'lpg', r'var PRICE = \{[^}]*lpg: ([\d.]+)'),
    ('js/retrofit-plan.js', 'electricity', r'var PRICE = \{[^}]*electric: ([\d.]+)'),
    ('js/retrofit-plan.js', 'hpTariff', r'var HP_TARIFF = ([\d.]+)'),
    ('insulation-calculator/index.html', 'gas', r'fuelPrices: \{ gas: ([\d.]+)'),
    ('insulation-calculator/index.html', 'oil', r'fuelPrices: \{[^}]*oil: ([\d.]+)'),
    ('insulation-calculator/index.html', 'lpg', r'fuelPrices: \{[^}]*lpg: ([\d.]+)'),
    ('insulation-calculator/index.html', 'electricity', r'fuelPrices: \{[^}]*electricity: ([\d.]+)'),
    ('guides/average-energy-bills-uk/index.html', 'gas', r'var RG=([\d.]+)'),
    ('guides/average-energy-bills-uk/index.html', 'electricity', r'RE=([\d.]+)'),
    ('guides/average-energy-bills-uk/index.html', 'oil', r'ROIL=([\d.]+)'),
    ('guides/average-energy-bills-uk/index.html', 'lpg', r'RLPG=([\d.]+)'),
    ('solar-calculator/index.html', 'electricity', r'electricityRate: ([\d.]+)'),
]


def main():
    bad = []
    for f, price, rx in COPIES:
        s = (ROOT / f).read_text()
        m = re.search(rx, s)
        if not m:
            bad.append('%s: could not find its %s price' % (f, price))
        elif abs(float(m.group(1)) - MODEL[price]) > 1e-9:
            bad.append('%s: %s is %s, the model says %s' % (f, price, m.group(1), MODEL[price]))
    for b in bad:
        print('  ' + b)
    print('%s: %d page price copies checked against RP_HEAT.prices' % ('FAIL' if bad else 'PASS', len(COPIES)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
