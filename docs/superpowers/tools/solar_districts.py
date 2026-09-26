#!/usr/bin/env python3
"""Solar output by postcode district: the table behind the solar calculator's postcode box.

For every postcode district in Great Britain (the first half of a postcode, such as BS6), the
PVGIS output of 1 kW of panels facing due south at 35 degrees, at the district's centre of
homes. Same PVGIS settings as pvgis_councils.py and the calculator's city table.

Sources, both free and open:
  1. Ordnance Survey Code-Point Open (Open Government Licence): every live GB postcode with its
     grid reference and council. A district's centre is the mean of its postcodes, and postcodes
     follow addresses, so it sits where the homes are rather than in the hills.
  2. PVGIS 5.3, PVGIS-SARAH3 (European Commission Joint Research Centre).

Each district also carries the calculator region its homes are mostly in (through the council,
using docs/bus-councils.json regions for England and Wales). The calculator applies one
allowance for shading and dirt (SOLAR.derate) on top of PVGIS's own 14% losses, and each
region's figure is the same allowance applied to the household weighted mean of its districts.

Writes docs/solar-districts.json (full detail) and js/solar-districts.js (the compact table the
calculator loads). Northern Ireland, the Channel Islands and the Isle of Man are not in
Code-Point Open and are not covered, as before.
Usage: python3 docs/superpowers/tools/solar_districts.py            rebuild (downloads, queries PVGIS)
       python3 docs/superpowers/tools/solar_districts.py --check    the calculator's derate and regional
                                                                    figures match docs/solar-districts.json
"""
import csv, io, json, math, pathlib, subprocess, sys, tempfile, time, zipfile
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pvgis_councils import pvgis, CACHE

ROOT = pathlib.Path(__file__).resolve().parents[3]
CODEPOINT = 'https://api.os.uk/downloads/v1/products/CodePointOpen/downloads?area=GB&format=CSV&redirect'
COLS = ['Postcode', 'Positional_quality_indicator', 'Eastings', 'Northings', 'Country_code', 'NHS_regional_HA_code',
        'NHS_HA_code', 'Admin_county_code', 'Admin_district_code', 'Admin_ward_code']
CALC_REGION = {'London': 'south', 'South East': 'south', 'South West': 'south', 'East': 'south', 'East Midlands': 'midlands',
               'West Midlands': 'midlands', 'North East': 'north', 'North West': 'north', 'Yorkshire and the Humber': 'north',
               'Wales': 'wales', 'Scotland': 'scotland'}


def osgb_to_wgs84(E, N):
    """British National Grid easting/northing to WGS84 latitude/longitude (Ordnance Survey's
    published transverse Mercator inverse and a Helmert shift; good to about 5 metres)."""
    a, b, F0 = 6377563.396, 6356256.909, 0.9996012717
    lat0, lon0, N0, E0 = math.radians(49), math.radians(-2), -100000, 400000
    e2 = 1 - b * b / (a * a); n = (a - b) / (a + b)
    lat, M = lat0, 0
    while True:
        lat = (N - N0 - M) / (a * F0) + lat
        Ma = (1 + n + 5 / 4 * n ** 2 + 5 / 4 * n ** 3) * (lat - lat0)
        Mb = (3 * n + 3 * n ** 2 + 21 / 8 * n ** 3) * math.sin(lat - lat0) * math.cos(lat + lat0)
        Mc = (15 / 8 * n ** 2 + 15 / 8 * n ** 3) * math.sin(2 * (lat - lat0)) * math.cos(2 * (lat + lat0))
        Md = 35 / 24 * n ** 3 * math.sin(3 * (lat - lat0)) * math.cos(3 * (lat + lat0))
        M = b * F0 * (Ma - Mb + Mc - Md)
        if abs(N - N0 - M) < 0.00001:
            break
    s, c, t = math.sin(lat), math.cos(lat), math.tan(lat)
    nu = a * F0 / math.sqrt(1 - e2 * s * s); rho = a * F0 * (1 - e2) / (1 - e2 * s * s) ** 1.5; eta2 = nu / rho - 1
    VII = t / (2 * rho * nu); VIII = t / (24 * rho * nu ** 3) * (5 + 3 * t * t + eta2 - 9 * t * t * eta2)
    IX = t / (720 * rho * nu ** 5) * (61 + 90 * t * t + 45 * t ** 4)
    X = 1 / (c * nu); XI = 1 / (c * 6 * nu ** 3) * (nu / rho + 2 * t * t)
    XII = 1 / (c * 120 * nu ** 5) * (5 + 28 * t * t + 24 * t ** 4); XIIA = 1 / (c * 5040 * nu ** 7) * (61 + 662 * t * t + 1320 * t ** 4 + 720 * t ** 6)
    dE = E - E0
    lat = lat - VII * dE ** 2 + VIII * dE ** 4 - IX * dE ** 6
    lon = lon0 + X * dE - XI * dE ** 3 + XII * dE ** 5 - XIIA * dE ** 7
    # OSGB36 to WGS84 by Helmert transformation
    s_, c_ = math.sin(lat), math.cos(lat); nu = a / math.sqrt(1 - e2 * s_ * s_)
    x, y, z = nu * c_ * math.cos(lon), nu * c_ * math.sin(lon), (1 - e2) * nu * s_
    tx, ty, tz, sc = 446.448, -125.157, 542.060, -20.4894e-6
    rx, ry, rz = [math.radians(v / 3600) for v in (0.1502, 0.2470, 0.8421)]
    x2 = tx + (1 + sc) * x - rz * y + ry * z; y2 = ty + rz * x + (1 + sc) * y - rx * z; z2 = tz - ry * x + rx * y + (1 + sc) * z
    a2, b2 = 6378137.0, 6356752.3142; e22 = 1 - b2 * b2 / (a2 * a2); p = math.hypot(x2, y2)
    lat = math.atan2(z2, p * (1 - e22))
    for _ in range(10):
        nu = a2 / math.sqrt(1 - e22 * math.sin(lat) ** 2); lat = math.atan2(z2 + e22 * nu * math.sin(lat), p)
    return math.degrees(lat), math.degrees(math.atan2(y2, x2))


def check():
    import re
    d = json.loads((ROOT / 'docs' / 'solar-districts.json').read_text())
    src = (ROOT / 'solar-calculator' / 'index.html').read_text()
    derate = float(re.search(r'derate: ([0-9.]+)', src).group(1))
    gen = dict(re.findall(r'(\w+): (\d+)', re.search(r'generation: \{([^}]*)\}', src).group(1)))
    bad = []
    for reg, v in d['regions'].items():
        want = int(5 * round(derate * v['weighted_kwh'] / 5))
        if int(gen[reg]) != want:
            bad.append('%s: calculator %s, districts give %d' % (reg, gen[reg], want))
    table = (ROOT / 'js' / 'solar-districts.js').read_text()
    if table.count('":[') != len(d['districts']):
        bad.append('js/solar-districts.js is out of date')
    print(('FAIL: ' + '; '.join(bad)) if bad else 'PASS: solar calculator regions match %d postcode districts' % len(d['districts']))
    return 1 if bad else 0


def main():
    if '--check' in sys.argv:
        sys.exit(check())
    bus = json.loads((ROOT / 'docs' / 'bus-councils.json').read_text())['councils']
    zpath = pathlib.Path(tempfile.gettempdir()) / 'codepo_gb.zip'
    if not zpath.exists():
        subprocess.run(['curl', '-s', '-L', '-m', '600', '-o', str(zpath), CODEPOINT], check=True)
    z = zipfile.ZipFile(zpath)
    sums = defaultdict(lambda: [0.0, 0.0, 0, Counter(), Counter()])
    for name in z.namelist():
        if not (name.endswith('.csv') and '/CSV/' in name):
            continue
        for r in csv.reader(io.TextIOWrapper(z.open(name), encoding='utf-8')):
            row = dict(zip(COLS, r))
            e, n = int(row['Eastings'] or 0), int(row['Northings'] or 0)
            if not e or not n or row['Positional_quality_indicator'] == '90':
                continue
            pc = row['Postcode'].replace(' ', '')
            district = pc[:-3]
            d = sums[district]
            d[0] += e; d[1] += n; d[2] += 1; d[3][row['Admin_district_code']] += 1; d[4][row['Country_code']] += 1
    print('districts', len(sums), 'postcodes', sum(v[2] for v in sums.values()), flush=True)
    out = {}
    for dist, (se, sn, k, councils, countries) in sums.items():
        lat, lon = osgb_to_wgs84(se / k, sn / k)
        council = councils.most_common(1)[0][0]
        country = countries.most_common(1)[0][0]
        if council in bus:
            region = CALC_REGION[bus[council]['region']]
        else:
            region = {'E92000001': None, 'W92000004': 'wales', 'S92000003': 'scotland'}.get(country)
        out[dist] = {'lat': round(lat, 4), 'lon': round(lon, 4), 'postcodes': k, 'council': council, 'region': region}
    missing = [d for d, v in out.items() if not v['region']]
    if missing:
        raise SystemExit('no region for ' + ', '.join(sorted(missing)[:20]))

    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    todo = sorted({(v['lat'], v['lon']) for v in out.values()} - {tuple(map(float, key.split(','))) for key in cache})
    print('points to query', len(todo), 'cached', len(cache), flush=True)
    with ThreadPoolExecutor(3) as ex:
        for i, (pt, r) in enumerate(zip(todo, ex.map(pvgis, todo))):
            cache['%s,%s' % pt] = r
            if i % 200 == 0:
                print(i, pt, r and round(r['kwh']), flush=True)
                CACHE.write_text(json.dumps(cache))
    CACHE.write_text(json.dumps(cache))
    refused = []
    for dist, v in out.items():
        r = cache['%s,%s' % (v['lat'], v['lon'])]
        if r is None:
            refused.append(dist)
            continue
        v['kwh'] = round(r['kwh'])
    for dist in refused:   # a centre over water (an island district): take the council's other districts
        v = out[dist]
        same = [w['kwh'] for d, w in out.items() if w['council'] == v['council'] and 'kwh' in w]
        v['kwh'] = round(sum(same) / len(same)); v['from_council'] = True
    regions = {}
    for reg in ('south', 'midlands', 'north', 'wales', 'scotland'):
        ds = [v for v in out.values() if v['region'] == reg]
        regions[reg] = {'districts': len(ds), 'weighted_kwh': round(sum(v['kwh'] * v['postcodes'] for v in ds) / sum(v['postcodes'] for v in ds), 1),
                        'min': min(v['kwh'] for v in ds), 'max': max(v['kwh'] for v in ds)}
    data = {'built': time.strftime('%Y-%m-%d'), 'codepoint': z.namelist()[0].split('/')[0] if '/' in z.namelist()[0] else 'Code-Point Open',
            'regions': regions, 'refused': refused, 'districts': dict(sorted(out.items()))}
    (ROOT / 'docs' / 'solar-districts.json').write_text(json.dumps(data, indent=1))
    letter = {'south': 's', 'midlands': 'm', 'north': 'n', 'wales': 'w', 'scotland': 'c'}
    table = ','.join('"%s":[%d,"%s"]' % (d, v['kwh'], letter[v['region']]) for d, v in sorted(out.items()))
    (ROOT / 'js' / 'solar-districts.js').write_text(
        '/* PVGIS output in kWh a year for 1 kW of panels facing south at 35 degrees, by postcode district, at the\n'
        '   centre of each district\'s homes, and the calculator region its homes are mostly in (s south,\n'
        '   m midlands, n north, w wales, c Scotland). Built by docs/superpowers/tools/solar_districts.py\n'
        '   from Ordnance Survey Code-Point Open and PVGIS 5.3. Read in the browser only. */\n'
        'window.RP_SOLAR_AREA={%s};\n' % table)
    print('regions', json.dumps(regions))
    print('refused', refused)


if __name__ == '__main__':
    main()
