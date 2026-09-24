#!/usr/bin/env python3
"""Find figures the old heat model produced that are still on the site.

The model was recalibrated on 24 September 2026 (heat pump efficiency from the
Electrification of Heat trial, installed cost from Boiler Upgrade Scheme medians). Every
page that quoted the old model has to move with it. This lists any page still carrying a
figure that only the old model produced: running costs, installed ranges, after-grant
ranges and efficiencies, plus retired claims such as a non-existent insulation scheme.

Pages that deliberately quote the old figures to compare them (the accuracy page) and the
methodology's one sentence about the old efficiency range are exempt.

Usage: python3 docs/superpowers/tools/stale_check.py   (exit code 1 if anything is found)
"""
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
EXEMPT = {'accuracy/index.html'}

# Old model outputs at average insulation, and ranges the guides quoted from it.
TOKENS = [
    # running costs, heat pump standard / tariff (old efficiency 2.9)
    '£899', '£614', '£1,193', '£816', '£956', '£654', '£580', '£397', '£572', '£391', '£841', '£575', '£1,593', '£1,089',
    # installed and after-grant ranges from the old cost model
    '£9,000 to £12,000', '£1,500 to £4,500', '£11,000 to £16,000', '£3,500 to £8,500', '£8,000 to £10,000',
    '£500 to £2,500', '£10,000 to £13,000', '£2,500 to £5,500', '£13,000 to £19,000', '£5,500 to £11,500',
    '£7,000 to £13,000', '£7,000 to £10,000', '£0 to £2,500', '£9,000 to £11,000',
    # retired claims
    'GB Energy Scheme', 'being phased out', 'gas ban likely',
]
EFFICIENCY = re.compile(r'\b(?:COP|SCOP|efficiency|coefficient of performance)[^.<]{0,60}\b(2\.9|3\.4|2\.6 to 3\.4)\b', re.I)


def visible(html):
    html = re.sub(r'<script(?![^>]*ld\+json).*?</script>', ' ', html, flags=re.S)
    html = re.sub(r'<style.*?</style>', ' ', html, flags=re.S)
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html))


def main():
    found = []
    for f in sorted(ROOT.rglob('*.html')):
        rel = f.relative_to(ROOT).as_posix()
        if rel.startswith('docs/') or rel in EXEMPT:
            continue
        text = visible(f.read_text())
        for t in TOKENS:
            for m in re.finditer(re.escape(t), text):
                ctx = text[max(0, m.start() - 70):m.end() + 50]
                if rel == 'methodology/index.html' and 'Until 24 September 2026' in ctx:
                    continue
                found.append((rel, t, ctx.strip()))
        for m in EFFICIENCY.finditer(text):
            ctx = text[max(0, m.start() - 30):m.end() + 40]
            if rel == 'methodology/index.html' and 'Until 24 September 2026' in text[max(0, m.start() - 200):m.end()]:
                continue
            found.append((rel, m.group(1), ctx.strip()))
    for rel, t, ctx in found:
        print('  %-48s %-22s ...%s...' % (rel[:48], t, ctx[:150]))
    pages = len(set(r for r, _, _ in found))
    print('%s: %d stale figures on %d pages' % ('FAIL' if found else 'PASS', len(found), pages))
    return 1 if found else 0


if __name__ == '__main__':
    sys.exit(main())
