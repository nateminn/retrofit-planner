#!/usr/bin/env python3
"""Solar output by council: PVGIS modelled output where people live, for every council in the UK.

Sources, all free and open:
  1. European Commission Joint Research Centre, PVGIS 5.3 PVcalc API, PVGIS-SARAH3 database
     (2005 to 2023): 1 kWp of crystalline silicon panels, building mounted, 35 degree pitch,
     facing due south, 14% system losses. The same settings as the city table on the solar
     calculator, so London here matches London there.
  2. Where people live: population weighted centres of small areas.
       England and Wales: ONS MSOA (December 2021) population weighted centroids, equal weight
         (each MSOA has 5,000 to 15,000 people).
       Scotland: Scottish Government Intermediate Zone (2022) centroids, weighted by households.
       Northern Ireland: the council's largest town (no small area centroids are published as a
         service), listed in NI_TOWNS below.
     Up to POINTS areas per council, spread through the list, each run through PVGIS; the council
     figure is their weighted average. A geographic centre would put Gwynedd on Snowdon.
  3. ONS Local Authority Districts (May 2025) boundaries, ultra generalised: which council each
     point is in, and the map. Open Government Licence.

Writes docs/solar-councils.json (figures) and docs/maps/lad-2025-uk.json (map paths, with
Shetland moved into a box off the east coast and an enlarged London inset). PVGIS answers are
cached in the system temp folder, so a rerun only asks for new points.
Usage: python3 docs/superpowers/tools/pvgis_councils.py
"""
import json, math, pathlib, re, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from bus_councils import paths, LONDON_BOX   # the same map simplification as the heat pump map

ROOT = pathlib.Path(__file__).resolve().parents[3]
POINTS = 8
LAD = ('https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/LAD_MAY_2025_UK_BUC/FeatureServer/0/query'
       '?where=1%3D1&outFields=LAD25CD,LAD25NM,LAT,LONG&outSR={sr}&f=geojson')
MSOA = ('https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/MSOA_December_2021_EW_PWC_V2/FeatureServer/0/query'
        '?where=1%3D1&outFields=MSOA21CD&outSR=4326&resultOffset={off}&resultRecordCount=2000&f=geojson')
IZ = ('https://maps.gov.scot/server/rest/services/ScotGov/StatisticalUnits/MapServer/13/query'
      '?where=1%3D1&outFields=izcode,hhcnt2022&outSR=4326&returnGeometry=true&resultOffset={off}&resultRecordCount=500&orderByFields=objectid&f=geojson')
PVGIS = ('https://re.jrc.ec.europa.eu/api/v5_3/PVcalc?lat={lat:.4f}&lon={lon:.4f}&peakpower=1&loss=14&angle=35&aspect=0'
         '&mountingplace=building&raddatabase=PVGIS-SARAH3&outputformat=json')
NI_TOWNS = {   # the largest town in each Northern Ireland council
    'N09000001': ('Newtownabbey', 54.6597, -5.9087), 'N09000002': ('Portadown', 54.4203, -6.4436),
    'N09000003': ('Belfast', 54.5973, -5.9301), 'N09000004': ('Coleraine', 55.1326, -6.6646),
    'N09000005': ('Derry', 54.9966, -7.3086), 'N09000006': ('Omagh', 54.5977, -7.3100),
    'N09000007': ('Lisburn', 54.5162, -6.0580), 'N09000008': ('Ballymena', 54.8636, -6.2763),
    'N09000009': ('Dungannon', 54.5037, -6.7672), 'N09000010': ('Newry', 54.1751, -6.3402),
    'N09000011': ('Bangor', 54.6538, -5.6682)}
SHETLAND, SHIFT = 'S12000027', (120000, -300000)   # moved east and south, into a box off Aberdeenshire
NATION = {'E': None, 'W': 'Wales', 'S': 'Scotland', 'N': 'Northern Ireland'}
CACHE = pathlib.Path(tempfile.gettempdir()) / 'rp_pvgis_cache.json'


def get(url):
    r = subprocess.run(['curl', '-s', '-m', '120', '-L', url], capture_output=True)
    return r.stdout.decode('utf-8')


def pvgis(pt):
    lat, lon = pt
    for attempt in range(5):
        txt = get(PVGIS.format(lat=lat, lon=lon))
        try:
            d = json.loads(txt)
        except ValueError:
            time.sleep(2 + attempt * 4)
            continue
        if 'outputs' in d:
            f = d['outputs']['totals']['fixed']
            return {'kwh': f['E_y'], 'months': [m['E_m'] for m in d['outputs']['monthly']['fixed']], 'elevation': d['inputs']['location']['elevation']}
        return None   # PVGIS refused the point (over the sea)
    raise SystemExit('PVGIS did not answer for %s, %s' % (lat, lon))


def inside(x, y, ring):
    c = False
    for i in range(len(ring)):
        (x1, y1), (x2, y2) = ring[i - 1], ring[i]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def locate(lon, lat, lads):
    """The council a point is in; the nearest boundary vertex when the generalised outline misses it."""
    for c, rings, box in lads:
        if box[0] <= lon <= box[2] and box[1] <= lat <= box[3] and any(inside(lon, lat, r) for r in rings):
            return c
    best = min(((math.hypot((x - lon) * 0.6, y - lat), c) for c, rings, _ in lads for r in rings for x, y in r[::3]))
    return best[1]


def spread(items, k):
    if len(items) <= k:
        return items
    return [items[round(i * (len(items) - 1) / (k - 1))] for i in range(k)]


def main():
    sys.setrecursionlimit(20000)
    bus = json.loads((ROOT / 'docs' / 'bus-councils.json').read_text())['councils']
    wgs = {f['properties']['LAD25CD']: f for f in json.loads(get(LAD.format(sr=4326)))['features']}
    lads = []
    for c, f in wgs.items():
        g = f['geometry']
        rings = [p[0] for p in (g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']])]
        xs = [x for r in rings for x, _ in r]; ys = [y for r in rings for _, y in r]
        lads.append((c, rings, (min(xs), min(ys), max(xs), max(ys))))
    # small area points: (council, sort key, lat, lon, weight)
    pts = {c: [] for c in wgs}
    off = 0
    while True:
        feats = json.loads(get(MSOA.format(off=off)))['features']
        for f in feats:
            lon, lat = f['geometry']['coordinates']
            pts[locate(lon, lat, lads)].append((f['properties']['MSOA21CD'], lat, lon, 1))
        if len(feats) < 2000:
            break
        off += 2000
    off, n_iz = 0, 0
    while True:
        feats = json.loads(get(IZ.format(off=off)))['features']
        for f in feats:
            lon, lat = f['geometry']['coordinates']
            pts[locate(lon, lat, lads)].append((f['properties']['izcode'], lat, lon, f['properties']['hhcnt2022'] or 1))
        n_iz += len(feats)
        if len(feats) < 500:
            break
        off += 500
    if n_iz != 1334:
        raise SystemExit('expected 1,334 Intermediate Zones, got %d' % n_iz)
    for c, (town, lat, lon) in NI_TOWNS.items():
        pts[c] = [(town, lat, lon, 1)]
    empty = [wgs[c]['properties']['LAD25NM'] for c in wgs if not pts[c]]
    if empty:
        raise SystemExit('no small areas found in ' + ', '.join(empty))
    chosen = {c: spread(sorted(v), POINTS) for c, v in pts.items()}

    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    todo = sorted({(round(p[1], 4), round(p[2], 4)) for v in chosen.values() for p in v} - {tuple(map(float, k.split(','))) for k in cache})
    print('small areas', sum(len(v) for v in pts.values()), 'points to query', len(todo), 'cached', len(cache), flush=True)
    with ThreadPoolExecutor(3) as ex:
        for n, (pt, r) in enumerate(zip(todo, ex.map(pvgis, todo))):
            cache['%s,%s' % pt] = r
            if n % 200 == 0:
                print(n, pt, r and round(r['kwh']), flush=True)
                CACHE.write_text(json.dumps(cache))
    CACHE.write_text(json.dumps(cache))

    out = {}
    for c, f in sorted(wgs.items()):
        got = [(p, cache['%s,%s' % (round(p[1], 4), round(p[2], 4))]) for p in chosen[c]]
        got = [(p, r) for p, r in got if r]
        if not got:
            raise SystemExit('PVGIS refused every point in ' + f['properties']['LAD25NM'])
        w = sum(p[3] for p, _ in got)
        kwh = sum(r['kwh'] * p[3] for p, r in got) / w
        months = [round(sum(r['months'][i] * p[3] for p, r in got) / w, 1) for i in range(12)]
        region = bus[c]['region'] if c in bus else NATION[c[0]]
        out[c] = {'kwh': round(kwh), 'months': months, 'name': f['properties']['LAD25NM'].strip(), 'region': region, 'points': len(got),
                  'range': [round(min(r['kwh'] for _, r in got)), round(max(r['kwh'] for _, r in got))]}
        if c in NI_TOWNS:
            out[c]['town'] = NI_TOWNS[c][0]
    order = sorted(out, key=lambda c: -out[c]['kwh'])
    for i, c in enumerate(order):
        out[c]['rank'] = i + 1
    ys = sorted(v['kwh'] for v in out.values())
    median = (ys[len(ys) // 2] + ys[(len(ys) - 1) // 2]) / 2
    nations = {}
    for v in out.values():
        k = v['region'] if v['region'] in ('Wales', 'Scotland', 'Northern Ireland') else 'England'
        nations.setdefault(k, []).append(v['kwh'])
    data = {'queried': time.strftime('%Y-%m-%d'), 'points_per_council': POINTS,
            'settings': 'PVGIS 5.3, PVGIS-SARAH3 2005 to 2023, 1 kWp crystalline silicon, building mounted, 35 degree pitch, due south, 14% losses',
            'median': round(median), 'nations': {k: {'min': min(v), 'max': max(v), 'mean': round(sum(v) / len(v))} for k, v in nations.items()},
            'councils': out}
    (ROOT / 'docs' / 'solar-councils.json').write_text(json.dumps(data, indent=1, ensure_ascii=False))

    feats = json.loads(get(LAD.format(sr=27700)))['features']
    for f in feats:
        if f['properties']['LAD25CD'] == SHETLAND:
            g = f['geometry']
            polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
            g['coordinates'] = [[[[x + SHIFT[0], y + SHIFT[1]] for x, y in ring] for ring in poly] for poly in polys]
            g['type'] = 'MultiPolygon'
    main_map = paths(feats, 900, 15e6)
    london = paths([f for f in feats if f['properties']['LAD25CD'].startswith('E09')], 150, 1e5, box=LONDON_BOX, width=220)
    sh = [tuple(map(float, pt.split())) for pt in re.findall(r'[\d.]+ [\d.]+', main_map['paths'][SHETLAND])]
    box = [min(x for x, _ in sh) - 6, min(y for _, y in sh) - 6, max(x for x, _ in sh) + 6, max(y for _, y in sh) + 6]
    maps = {'main': dict(main_map, shetland_box=[round(v, 1) for v in box]), 'london': london,
            'source': ('ONS Local Authority Districts (May 2025) Boundaries UK BUC, retrieved from the ONS Open Geography Portal. Source: Office '
                       'for National Statistics licensed under the Open Government Licence v3.0. Contains OS data (c) Crown copyright and database '
                       'right 2025. Simplified for display; Shetland moved.')}
    (ROOT / 'docs' / 'maps' / 'lad-2025-uk.json').write_text(json.dumps(maps))
    print('councils %d, median %d kWh per kWp' % (len(out), median))
    print('top', [(out[c]['name'], out[c]['kwh']) for c in order[:5]], 'bottom', [(out[c]['name'], out[c]['kwh']) for c in order[-6:]])
    print('widest spread', sorted(((v['range'][1] - v['range'][0], v['name']) for v in out.values()), reverse=True)[:5])
    print('map', main_map['w'], main_map['h'], 'paths', len(main_map['paths']))


if __name__ == '__main__':
    main()
