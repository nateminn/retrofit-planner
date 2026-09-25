#!/usr/bin/env python3
"""Heat pumps by council: fetch, join and simplify the data behind /guides/heat-pumps-by-council/.

Three public sources, all Open Government Licence:
  1. DESNZ Boiler Upgrade Scheme statistics, Table Q1.2: heat pump grants paid by local
     authority since the scheme opened (found through the GOV.UK content API, so a new monthly
     release is picked up by changing RELEASE below).
  2. ONS Census 2021, TS041 number of households, by local authority as of April 2023 (Nomis),
     to turn counts into heat pumps per 10,000 households, the measure DESNZ uses for regions.
  3. ONS Local Authority Districts (May 2025) boundaries, ultra generalised, simplified here
     into an inline SVG map for England and Wales, with an enlarged London inset.

Writes docs/bus-councils.json (figures) and docs/maps/lad-2025-ew.json (map paths).
Usage: python3 docs/superpowers/tools/bus_councils.py
"""
import csv, io, json, math, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
RELEASE = 'government/statistics/boiler-upgrade-scheme-statistics-august-2026'
NOMIS = ('https://www.nomisweb.co.uk/api/v01/dataset/NM_2059_1.data.csv?date=latest&geography=TYPE424&measures=20100'
         '&select=GEOGRAPHY_NAME,GEOGRAPHY_CODE,OBS_VALUE')
LAD = ('https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/LAD_MAY_2025_UK_BUC/FeatureServer/0/query'
       '?where=1%3D1&outFields=LAD25CD,LAD25NM&outSR=27700&f=geojson')
LEAF = ('E06', 'E07', 'E08', 'E09', 'W06')
# Census 2021 households are on April 2023 codes; Barnsley and Sheffield were recoded in 2024
RECODE = {'E08000016': 'E08000038', 'E08000019': 'E08000039'}
LONDON_BOX = (503000, 155000, 563000, 201000)   # British National Grid bounds of the inset


def get(url, binary=False):
    r = subprocess.run(['curl', '-s', '-m', '240', '-L', url], capture_output=True)
    if r.returncode:
        raise SystemExit('download failed: ' + url)
    return r.stdout if binary else r.stdout.decode('utf-8')


def bus_table():
    import openpyxl
    d = json.loads(get('https://www.gov.uk/api/content/' + RELEASE))
    url = next(a['url'] for a in d['details']['attachments'] if a['url'].endswith('.xlsx'))
    wb = openpyxl.load_workbook(io.BytesIO(get(url, binary=True)), read_only=True, data_only=True)
    rows = [r for r in wb['Q1.2'].iter_rows(values_only=True)]
    title = rows[0][0]
    out, regions, region = {}, {}, None
    for r in rows:
        code = r[0]
        if not code or not isinstance(code, str) or len(code) != 9:
            continue
        if code.startswith(('E12', 'W92')):
            region = (r[1] or '').strip()
            regions[code] = {'name': region, 'hp': r[4]}
        if code.startswith(LEAF):
            name = (r[3] or r[2]).split(' [')[0].split(' / ')[0].strip()
            out[code] = {'name': name, 'hp': int(r[4]), 'region': region if code[0] == 'E' else 'Wales'}
    total = next(r[4] for r in rows if r[0] == 'K04000001')
    return title, url, out, regions, total, d['public_updated_at'][:10]


def households():
    hh = {}
    for r in csv.DictReader(io.StringIO(get(NOMIS))):
        hh[RECODE.get(r['GEOGRAPHY_CODE'], r['GEOGRAPHY_CODE'])] = int(r['OBS_VALUE'])
    return hh


def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy)
    dmax, idx = 0, 0
    for i in range(1, len(pts) - 1):
        x, y = pts[i]
        dd = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / L if L else math.hypot(x - x1, y - y1)
        if dd > dmax:
            dmax, idx = dd, i
    if dmax > eps:
        return rdp(pts[:idx + 1], eps)[:-1] + rdp(pts[idx:], eps)
    return [pts[0], pts[-1]]


def ring_area(r):
    return abs(sum(r[i][0] * r[i - 1][1] - r[i - 1][0] * r[i][1] for i in range(len(r)))) / 2


def paths(features, eps, min_area, box=None, width=440):
    rings = {}
    for f in features:
        g = f['geometry']
        polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
        keep = []
        for poly in polys:
            ring = poly[0]
            if ring_area(ring) < min_area:
                continue
            if box and not any(box[0] <= x <= box[2] and box[1] <= y <= box[3] for x, y in ring):
                continue
            mid = len(ring) // 2
            r = rdp(ring[:mid + 1], eps)[:-1] + rdp(ring[mid:], eps)
            if len(r) >= 4:
                keep.append(r)
        if keep:
            rings[f['properties']['LAD25CD']] = keep
    xs = [x for rs in rings.values() for r in rs for x, _ in r]
    ys = [y for rs in rings.values() for r in rs for _, y in r]
    minx, maxx, miny, maxy = (box[0], box[2], box[1], box[3]) if box else (min(xs), max(xs), min(ys), max(ys))
    s = width / (maxx - minx)
    out = {c: ''.join('M' + ' '.join('%.1f %.1f' % ((x - minx) * s, (maxy - y) * s) for x, y in r) + 'Z' for r in rs) for c, rs in rings.items()}
    return {'w': width, 'h': round((maxy - miny) * s), 'paths': out}


def main():
    sys.setrecursionlimit(20000)
    title, url, bus, regions, total, published = bus_table()
    hh = households()
    missing = [c for c in bus if c not in hh]
    if missing:
        raise SystemExit('no household count for ' + ', '.join(missing))
    if sum(v['hp'] for v in bus.values()) != total:
        raise SystemExit('council counts do not add up to the England and Wales total')
    for c, v in bus.items():
        v['households'] = hh[c]
        v['rate'] = round(v['hp'] / hh[c] * 10000, 1)
    order = sorted(bus, key=lambda c: -bus[c]['rate'])
    for i, c in enumerate(order):
        bus[c]['rank'] = i + 1
    all_hh = sum(v['households'] for v in bus.values())
    reg = {}
    for v in bus.values():
        r = reg.setdefault(v['region'], {'hp': 0, 'households': 0})
        r['hp'] += v['hp']; r['households'] += v['households']
    for r in reg.values():
        r['rate'] = round(r['hp'] / r['households'] * 10000, 1)
    data = {'title': title, 'source_url': url, 'published': published, 'total': total, 'households': all_hh,
            'rate': round(total / all_hh * 10000, 1), 'councils': bus, 'regions': reg}
    (ROOT / 'docs' / 'bus-councils.json').write_text(json.dumps(data, indent=1, ensure_ascii=False))
    feats = [f for f in json.loads(get(LAD))['features'] if f['properties']['LAD25CD'] in bus]
    main_map = paths(feats, 900, 15e6)
    london = paths([f for f in feats if f['properties']['LAD25CD'].startswith('E09')], 150, 1e5, box=LONDON_BOX, width=220)
    maps = {'main': main_map, 'london': london, 'source': ('ONS Local Authority Districts (May 2025) Boundaries UK BUC, retrieved from the ONS Open Geography '
            'Portal. Source: Office for National Statistics licensed under the Open Government Licence v3.0. Contains OS data (c) Crown copyright '
            'and database right 2025. Simplified for display.')}
    (ROOT / 'docs' / 'maps' / 'lad-2025-ew.json').write_text(json.dumps(maps))
    size = sum(len(p) for p in main_map['paths'].values()) + sum(len(p) for p in london['paths'].values())
    print('councils %d, total %d, England and Wales %.1f per 10,000 households, map %d KB' % (len(bus), total, data['rate'], size // 1024))
    print('top', [(bus[c]['name'], bus[c]['rate']) for c in order[:5]])


if __name__ == '__main__':
    main()
