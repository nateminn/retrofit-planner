#!/usr/bin/env python3
"""Run the solar calculator for the cases the solar pages quote and check the pages still
quote what it produces.

The four solar pages repeat a handful of headline results: yearly benefit and payback for
3, 4, 5 and 6 kW systems in southern England, the 4 kW system with a battery, and the
same 4 kW system in Scotland. If the calculator changes (a new price cap, export rate or
cost band) and a page does not, this fails and says which figure moved.

Every case: south facing roof, household out half the day, typical 2,500 kWh user.

Usage: python3 docs/superpowers/tools/solar_check.py   (exit code 1 on any mismatch)
Needs Python Playwright with Chromium.
"""
import http.server, pathlib, re, socketserver, sys, threading

ROOT = pathlib.Path(__file__).resolve().parents[3]
PAGES = ['solar-calculator/index.html', 'guides/are-solar-panels-worth-it-uk/index.html',
         'guides/solar-panel-payback-uk/index.html', 'guides/solar-battery-storage-uk/index.html']
# (label, region, size, battery, pages that must quote the benefit, pages that must quote the payback)
CASES = [
    ('3 kW, south', 'south', '3', 'no', [0], [0]),
    ('4 kW, south', 'south', '4', 'no', [0, 1, 2, 3], [0, 1, 2, 3]),
    ('5 kW, south', 'south', '5', 'no', [0], [0]),
    ('6 kW, south', 'south', '6', 'no', [0], [0]),
    ('4 kW with battery, south', 'south', '4', 'yes', [1, 2, 3], [2, 3]),
    ('4 kW, Scotland', 'scotland', '4', 'no', [], [1, 2]),
]


def visible(path):
    s = (ROOT / path).read_text()
    s = re.sub(r'<script(?![^>]*ld\+json).*?</script>|<style.*?</style>', ' ', s, flags=re.S)
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s))


def main():
    from playwright.sync_api import sync_playwright

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=str(ROOT), **k)

        def log_message(self, *a):
            pass

    httpd = socketserver.TCPServer(('127.0.0.1', 0), Quiet)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    results = {}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.on('dialog', lambda d: d.dismiss())
            page.goto('http://127.0.0.1:%d/solar-calculator/' % httpd.server_address[1], wait_until='load')
            for label, region, size, battery, _, _ in CASES:
                for sel, val in (('#region', region), ('#roofDirection', 'south'), ('#systemSize', size),
                                 ('#occupancy', 'half'), ('#battery', battery)):
                    page.select_option(sel, val)
                page.evaluate('calculate()')
                text = re.sub(r'\s+', ' ', page.inner_text('#resultsContent'))
                benefit = re.search(r'TOTAL ANNUAL BENEFIT (£[\d,]+)', text, re.I)
                payback = re.search(r'PAYBACK PERIOD ([\d.]+) years', text, re.I)
                results[label] = (benefit.group(1) if benefit else None, payback.group(1) if payback else None)
            browser.close()
    finally:
        httpd.shutdown()

    texts = [visible(p) for p in PAGES]
    bad = []
    for label, _, _, _, ben_pages, pay_pages in CASES:
        benefit, payback = results[label]
        if benefit is None or payback is None:
            bad.append('%s: the calculator gave no result' % label)
            continue
        for i in ben_pages:
            if benefit not in texts[i]:
                bad.append('%s: %s does not quote the %s a year the calculator gives' % (label, PAGES[i], benefit))
        for i in pay_pages:
            if not re.search(r'\b%s years' % re.escape(payback), texts[i]):
                bad.append('%s: %s does not quote the %s year payback the calculator gives' % (label, PAGES[i], payback))
    for b in bad:
        print('  ' + b)
    print('%s: %d solar cases, %s' % ('FAIL' if bad else 'PASS', len(CASES),
          ', '.join('%s %s and %s years' % (k, v[0], v[1]) for k, v in results.items())))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
