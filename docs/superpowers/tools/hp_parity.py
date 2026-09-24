#!/usr/bin/env python3
"""Check that the embeddable heat pump widget gives the same money figures as the full
heat pump calculator, for every property type, bedroom count, heating system and
insulation level, with no bill typed and with two typed bills.

The /embed/ page promises that a reader who follows the widget's link sees the same
numbers. Both pages load /js/heat-model.js, but each has its own page script, so this
runs both in a headless browser and compares what they actually show: installed cost,
cost after the grant, yearly saving (heat pump tariff and standard tariff), payback,
and the current heating and heat pump running costs.

Usage: python3 docs/superpowers/tools/hp_parity.py   (exit code 1 on any mismatch)
Needs Python Playwright with Chromium.
"""
import http.server, json, pathlib, re, socketserver, sys, threading

ROOT = pathlib.Path(__file__).resolve().parents[3]
IDS = ['installCost', 'afterGrant', 'annualSaving', 'savingDetail', 'payback', 'gasCost', 'hpCost']

SWEEP = """([calcName, ids]) => {
  const opts = id => [...document.getElementById(id).options].map(o => o.value).filter(Boolean);
  const out = {};
  for (const t of opts('propertyType')) for (const b of opts('bedrooms'))
  for (const h of opts('currentHeating')) for (const i of opts('insulation'))
  for (const bill of ['', '900', '1600']) {
    document.getElementById('propertyType').value = t;
    document.getElementById('bedrooms').value = b;
    document.getElementById('currentHeating').value = h;
    document.getElementById('insulation').value = i;
    document.getElementById('annualBill').value = bill;
    window[calcName]();
    out[[t, b, h, i, bill].join('|')] = ids.map(id => {
      const e = document.getElementById(id);
      return e ? e.textContent : null;
    });
  }
  return out;
}"""


def money(text):
    """The figures in a result, ignoring the words around them."""
    if text is None:
        return None
    t = text.replace(',', '')
    nums = re.findall(r'£\d+(?:\.\d+)?|\d+(?:\.\d+)? years?|Immediate|Under a year|No payback|Over 50 years|About the same', t)
    return tuple(nums)


def main():
    from playwright.sync_api import sync_playwright

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=str(ROOT), **k)

        def log_message(self, *a):
            pass

    httpd = socketserver.TCPServer(('127.0.0.1', 0), Quiet)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    errors = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            results = {}
            for name, path, fn in (('calculator', 'heat-pump-calculator', 'calculate'),
                                   ('widget', 'embed/heat-pump-calculator', 'calc')):
                page = browser.new_page()
                page.on('pageerror', lambda e, n=name: errors.append('%s: %s' % (n, e)))
                page.on('dialog', lambda d: d.dismiss())
                page.goto('http://127.0.0.1:%d/%s/' % (port, path), wait_until='load')
                results[name] = page.evaluate(SWEEP, [fn, IDS])
            browser.close()
    finally:
        httpd.shutdown()

    a, b = results['calculator'], results['widget']
    bad = []
    for key in sorted(a):
        if key not in b:
            bad.append((key, 'missing from widget', '', ''))
            continue
        for idx, id_ in enumerate(IDS):
            if b[key][idx] is None or a[key][idx] is None:
                continue
            if money(a[key][idx]) != money(b[key][idx]):
                bad.append((key, id_, a[key][idx], b[key][idx]))
    for key, id_, x, y in bad[:12]:
        print('  %-44s %-13s calculator %r  widget %r' % (key, id_, x[:70], y[:70]))
    for e in errors[:5]:
        print('  page error', e)
    ok = not bad and not errors
    print('%s: heat pump widget and calculator agree on %d of %d combinations, %d figures each'
          % ('PASS' if ok else 'FAIL', len(a) - len({k for k, *_ in bad}), len(a), len(IDS)))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
