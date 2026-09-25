#!/usr/bin/env python3
"""Run the solar calculator for every region and save what the solar payback by region pages quote.

The region pages must say exactly what the calculator says, so their figures come from running
the calculator itself in a headless browser: every system size, roof direction, occupancy and
the battery, for a household using 2,500 kWh a year (a bill of about £860). The results go to
docs/solar-regions.json, which build_new_pages.py reads.

Usage: python3 docs/superpowers/tools/solar_regions.py           write docs/solar-regions.json
       python3 docs/superpowers/tools/solar_regions.py --check   exit 1 if the calculator no
                                                                 longer gives the saved figures
Needs Python Playwright with Chromium.
"""
import http.server, json, pathlib, re, socketserver, sys, threading

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = ROOT / 'docs' / 'solar-regions.json'
REGIONS = ['south', 'midlands', 'north', 'wales', 'scotland']
num = lambda s: float(s.replace(',', '').replace('£', ''))


def parse(text):
    t = re.sub(r'\s+', ' ', text)
    g = lambda rx: re.search(rx, t, re.I)
    out = {'gen': num(g(r'ANNUAL GENERATION ([\d,]+) kWh').group(1)),
           'benefit': num(g(r'TOTAL ANNUAL BENEFIT £([\d,]+)').group(1)),
           'payback': g(r'PAYBACK PERIOD ([\d.]+ years|None)').group(1),
           'net25': num(g(r'Net (?:profit|loss) over 25 years £([\d,]+)').group(1)) * (-1 if 'Net loss over 25 years' in t else 1),
           'self_pct': int(g(r'used at home, (\d+)% of output').group(1))}
    m = g(r'PANELS ONLY OR WITH A BATTERY.*?Upfront cost £([\d,]+) £([\d,]+) Used at home (\d+)% of output (\d+)% of output Saving and export a year £([\d,]+) £([\d,]+) Payback ([\d.]+ years|Never) ([\d.]+ years|Never) 25 years, after costs (Loses )?£([\d,]+) (Loses )?£([\d,]+)')
    out['battery'] = {'cost': num(m.group(2)), 'self_pct': int(m.group(4)), 'benefit': num(m.group(6)), 'payback': m.group(8),
                      'net25': num(m.group(12)) * (-1 if m.group(11) else 1)}
    mm = g(r'YOUR OUTPUT MONTH BY MONTH ((?:\d+ [A-Z][a-z]{2} ?){12})')
    out['months'] = [int(x) for x in re.findall(r'(\d+) [A-Z][a-z]{2}', mm.group(1))]
    lo, hi = g(r'On a 4.1p flat SEG rate £([\d,]+)/yr, payback ([\d.]+ years|never)'), g(r'On a 17.5p installer-linked rate £([\d,]+)/yr, payback ([\d.]+ years|never)')
    out['seg'] = {'4.1p': [num(lo.group(1)), lo.group(2)], '17.5p': [num(hi.group(1)), hi.group(2)]}
    return out


def harvest():
    from playwright.sync_api import sync_playwright

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=str(ROOT), **k)

        def log_message(self, *a):
            pass

    httpd = socketserver.TCPServer(('127.0.0.1', 0), Quiet)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    data = {}
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(); page = b.new_page()
            page.goto('http://127.0.0.1:%d/solar-calculator/' % httpd.server_address[1], wait_until='load')

            def run(region, roof='south', size='4', occ='half', battery='no', pitch='35'):
                for sel, val in (('#region', region), ('#roofDirection', roof), ('#systemSize', size), ('#occupancy', occ), ('#battery', battery)):
                    page.select_option(sel, val)
                page.evaluate("document.getElementById('roofPitch').value = '%s'" % pitch)
                page.evaluate('calculate()')
                return parse(page.inner_text('#resultsContent'))

            for r in REGIONS:
                d = {'sizes': {s: run(r, size=s) for s in ('3', '4', '5', '6')}}
                d['roofs'] = {roof: run(r, roof=roof) for roof in ('south-east', 'south-west', 'east', 'west', 'north')}
                d['occupancy'] = {o: run(r, occ=o) for o in ('home', 'out')}
                data[r] = d
            b.close()
    finally:
        httpd.shutdown()
    return data


def main():
    data = harvest()
    if '--check' in sys.argv:
        saved = json.loads(OUT.read_text())
        bad = [r for r in REGIONS if saved.get(r) != data[r]]
        for r in bad:
            print('  %s: the calculator now gives different figures; rerun this tool and build_new_pages.py' % r)
        print('%s: solar region figures match the calculator for %d regions' % ('FAIL' if bad else 'PASS', len(REGIONS)))
        return 1 if bad else 0
    OUT.write_text(json.dumps(data, indent=1))
    print('wrote', OUT.relative_to(ROOT), {r: (data[r]['sizes']['4']['benefit'], data[r]['sizes']['4']['payback']) for r in REGIONS})
    return 0


if __name__ == '__main__':
    sys.exit(main())
