#!/usr/bin/env python3
"""Energy use by council: median gas and electricity per home for every council in England and Wales.

Source: DESNZ NEED local authority tables, 2024 (published 11 June 2026, Open Government Licence),
found through the GOV.UK content API. Tables LA1 and LA2 give the median for all homes; LA5 and
LA6 by property type. The gas year runs mid-May 2024 to mid-May 2025; the electricity year
February 2024 to January 2025. Gas medians cover homes with a gas meter only.

Writes docs/energy-councils.json, keyed by the same council codes as docs/bus-councils.json.
Usage: python3 docs/superpowers/tools/need_councils.py
"""
import io, json, pathlib, subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
NEED = 'government/statistics/national-energy-efficiency-data-framework-need-consumption-data-tables-2026'
LEAF = ('E06', 'E07', 'E08', 'E09', 'W06')
TYPES = ['Detached', 'Semi detached', 'Mid terrace', 'End terrace', 'Bungalow', 'Converted flat', 'Purpose built flat']


def get(url):
    return subprocess.run(['curl', '-s', '-m', '240', '-L', url], capture_output=True).stdout


def table(wb, sheet, want):
    """{code: {label: median}} for the columns whose header is 'Median:<label>'."""
    rows = list(wb[sheet].iter_rows(values_only=True))
    hdr = next(r for r in rows if r and r[0] == 'Code')
    cols = {}
    for i, h in enumerate(hdr):
        if isinstance(h, str) and h.replace('\n', ' ').startswith('Median:'):
            label = h.split(':', 1)[1].replace('\n', ' ').strip()
            if label in want:
                cols[label] = i
    out = {}
    for r in rows:
        if r and isinstance(r[0], str) and (r[0].startswith(LEAF) or r[0] in ('K04000001', 'E92000001', 'W92000004') or r[0].startswith('E12')):
            out[r[0]] = {k: (round(r[i]) if isinstance(r[i], (int, float)) else None) for k, i in cols.items()}
            out[r[0]]['_name'] = (r[3] if r[3] and r[3] != 'All' else r[2] if r[2] and r[2] != 'All' else r[1])
    return out


def main():
    import openpyxl
    d = json.loads(get('https://www.gov.uk/api/content/' + NEED))
    url = next(a['url'] for a in d['details']['attachments'] if a['title'].startswith('Local authority table, England and Wales, 2024 (Excel)'))
    wb = openpyxl.load_workbook(io.BytesIO(get(url)), read_only=True, data_only=True)
    gas = table(wb, 'LA1', ['All dwellings'])
    elec = table(wb, 'LA2', ['All dwellings'])
    gas_t = table(wb, 'LA5', TYPES)
    elec_t = table(wb, 'LA6', TYPES)
    bus = json.loads((ROOT / 'docs' / 'bus-councils.json').read_text())['councils']
    missing = [c for c in bus if c not in gas or c not in elec]
    if missing:
        raise SystemExit('councils missing from NEED: ' + ', '.join('%s %s' % (c, bus[c]['name']) for c in missing))
    out = {}
    for c in bus:
        out[c] = {'gas': gas[c]['All dwellings'], 'elec': elec[c]['All dwellings'],
                  'gas_type': {k: gas_t[c].get(k) for k in TYPES}, 'elec_type': {k: elec_t[c].get(k) for k in TYPES}}
    regions = {c: {'name': gas[c]['_name'], 'gas': gas[c]['All dwellings'], 'elec': elec[c]['All dwellings']} for c in gas if c.startswith('E12') or c == 'W92000004'}
    data = {'source_url': url, 'published': d['public_updated_at'][:10], 'councils': out, 'regions': regions,
            'ew': {'gas': gas['K04000001']['All dwellings'], 'elec': elec['K04000001']['All dwellings'],
                   'gas_type': {k: gas_t['K04000001'].get(k) for k in TYPES}, 'elec_type': {k: elec_t['K04000001'].get(k) for k in TYPES}}}
    (ROOT / 'docs' / 'energy-councils.json').write_text(json.dumps(data, indent=1))
    g = sorted([c for c in out if out[c]['gas']], key=lambda c: -out[c]['gas'])   # the Isles of Scilly have no mains gas
    print('councils', len(out), 'England and Wales median gas', data['ew']['gas'], 'electricity', data['ew']['elec'])
    print('most gas', [(bus[c]['name'], out[c]['gas']) for c in g[:4]], 'least', [(bus[c]['name'], out[c]['gas']) for c in g[-4:]])


if __name__ == '__main__':
    main()
