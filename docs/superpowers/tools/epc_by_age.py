#!/usr/bin/env python3
"""EPC rating by house age: fetch and parse the data behind the /guides/epc-rating-*-house/ pages.

Sources, all Open Government Licence, found through the GOV.UK content API:
  English Housing Survey live tables, 2024 sheet (MHCLG):
    DA7101 energy performance: EPC band shares and mean SAP rating by dwelling age
    DA6201 insulation: wall type and insulation, loft insulation, double glazing by age
    DA6101 heating: main fuel and heat pumps by age
  NEED consumption tables 2026 (DESNZ), 2024 meter readings, England and Wales:
    headline Table 7c median gas use by property age (all homes)
    gas per square metre Table 4.2c median gas use per m2 by property age (houses)

The survey tables are ODS; a small reader below avoids installing a package.
Writes docs/epc-by-age.json.  Usage: python3 docs/superpowers/tools/epc_by_age.py
"""
import io, json, pathlib, subprocess, zipfile
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[3]
EHS = 'government/statistical-data-sets/energy-performance'
NEED = 'government/statistics/national-energy-efficiency-data-framework-need-consumption-data-tables-2026'
T, O, X = ('{urn:oasis:names:tc:opendocument:xmlns:table:1.0}', '{urn:oasis:names:tc:opendocument:xmlns:office:1.0}',
           '{urn:oasis:names:tc:opendocument:xmlns:text:1.0}')
AGES = ['pre-1919', '1919-44', '1945-64', '1965-80', '1981-90', '1991-2002', '2003-2013', 'post-2013']


def get(url, binary=True):
    r = subprocess.run(['curl', '-s', '-m', '240', '-L', url], capture_output=True)
    return r.stdout if binary else r.stdout.decode()


def api(path):
    return json.loads(get('https://www.gov.uk/api/content/' + path, binary=False))


def ods_sheet(data, name):
    root = ET.fromstring(zipfile.ZipFile(io.BytesIO(data)).read('content.xml'))
    for t in root.iter(T + 'table'):
        if t.get(T + 'name') != name:
            continue
        rows = []
        for r in t.iter(T + 'table-row'):
            cells = []
            for c in r:
                if c.tag not in (T + 'table-cell', T + 'covered-table-cell'):
                    continue
                n = min(int(c.get(T + 'number-columns-repeated', '1')), 60)
                v = c.get(O + 'value')
                txt = ' '.join(''.join(p.itertext()) for p in c.iter(X + 'p'))
                cells.extend([float(v) if v is not None else (txt or None)] * n)
            while cells and cells[-1] is None:
                cells.pop()
            if cells:
                rows.append(cells)
        return rows
    raise SystemExit('no sheet ' + name)


def age_rows(rows, labels, stop_at=None):
    """The percentage block: first occurrence of each age label."""
    out = {}
    for r in rows:
        key = str(r[0]).strip() if r and r[0] else ''
        key = key.replace('post 2013', 'post-2013')
        if key in labels and key not in out and len(r) > 8:   # skip label-only rows such as 'all dwellings' in the title block
            out[key] = [None if (x == 'u' or x is None) else x for x in r[1:]]
    return out


def main():
    att = {a['title'].split(':')[0].strip(): a['url'] for a in api(EHS)['details']['attachments']}
    ehs_date = api(EHS)['public_updated_at'][:10]
    perf = age_rows(ods_sheet(get(att['DA7101']), '2024'), AGES + ['all dwellings'])
    ins = age_rows(ods_sheet(get(att['DA6201']), '2024'), AGES + ['all dwellings'])
    heat = age_rows(ods_sheet(get(att['DA6101']), '2024'), AGES + ['all dwellings'])
    ages = {}
    for a in AGES + ['all dwellings']:
        p, i, h = perf[a], ins[a], heat[a]
        ages[a] = {
            'bands': dict(zip(['A/B', 'C', 'A/B/C', 'D', 'E', 'F', 'G', 'E/F/G', 'SAP'], p[:9])),
            'walls': dict(zip(['cavity insulated', 'cavity insulated as built', 'cavity uninsulated', 'solid insulated', 'solid uninsulated', 'other'], i[:6])),
            'loft': dict(zip(['none', 'under 100mm', '100 to 150mm', '150mm or more', 'flat roof or unknown', 'no loft'], i[6:12])),
            'glazing_all': i[15], 'homes_000': i[16],
            'gas': h[3], 'oil': h[4], 'electric': h[7], 'heat_pump': h[15],
        }
    need_att = {a['title']: a['url'] for a in api(NEED)['details']['attachments']}
    import openpyxl
    head = openpyxl.load_workbook(io.BytesIO(get(need_att['Headline consumption tables: England and Wales, 2024 (Excel)'])), read_only=True, data_only=True)
    rows = list(head['Table_7'].iter_rows(values_only=True))
    hdr = next(r for r in rows if r and r[0] == 'Year')
    y24 = next(r for r in rows if r and r[0] == 2024)
    third = [i for i, v in enumerate(hdr) if v == 'Year'][2]      # the median block
    need_all = {hdr[i]: round(y24[i]) for i in range(third + 1, third + 12) if isinstance(y24[i], (int, float))}
    m2 = openpyxl.load_workbook(io.BytesIO(get(need_att['Gas consumption per square metre in houses: England and Wales, 2024 (Excel)'])), read_only=True, data_only=True)
    rows = list(m2['Table_4.2'].iter_rows(values_only=True))
    hdr = next(r for r in rows if r and r[0] == 'Year')
    y24 = next(r for r in rows if r and r[0] == 2024)
    third = [i for i, v in enumerate(hdr) if v == 'Year'][2]
    need_m2 = {hdr[i]: round(y24[i]) for i in range(third + 1, third + 9) if isinstance(y24[i], (int, float))}
    data = {'ehs_published': ehs_date, 'need_published': api(NEED)['public_updated_at'][:10], 'ages': ages,
            'need_gas_median': need_all, 'need_gas_per_m2_houses': need_m2}
    (ROOT / 'docs' / 'epc-by-age.json').write_text(json.dumps(data, indent=1))
    print('EHS', ehs_date, {a: (ages[a]['bands']['A/B/C'], ages[a]['bands']['SAP']) for a in AGES})
    print('NEED median gas', need_all); print('NEED per m2 houses', need_m2)


if __name__ == '__main__':
    main()
