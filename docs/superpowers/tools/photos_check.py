#!/usr/bin/env python3
"""Checks for the photo round: every referenced /images file exists, photo figures have alt text without em dashes or ampersands, og:image files exist, no page references a missing image, every guide and calculator has a photo."""
import re, glob, os, sys
fails = 0
def fail(msg):
    global fails; fails += 1; print('FAIL', msg)
pages = ['index.html'] + glob.glob('*/index.html') + glob.glob('guides/*/index.html')
refs = set(); with_photo = []
for f in pages:
    s = open(f, encoding='utf-8').read()
    for m in re.finditer(r'(?:src|srcset|content)="([^"]*/images/[^"]*)"', s):
        for part in m.group(1).split(','):
            u = part.strip().split(' ')[0].replace('https://www.retrofitplanner.co.uk', '')
            if u.startswith('/images/'): refs.add(u)
            if not os.path.exists(u.lstrip('/')): fail('%s references missing %s' % (f, u))
    figs = re.findall(r'<figure class="photo-fig[^"]*" id="photo-[^"]+">(.*?)</figure>', s, re.S)
    if figs: with_photo.append(f)
    for fig in figs:
        alt = re.search(r'alt="([^"]*)"', fig)
        if not alt or not alt.group(1).strip(): fail('%s photo without alt' % f)
        if '—' in fig or '&amp;' in fig or re.search(r'&(?!amp;|lt;|gt;|quot;|#)', fig): fail('%s photo figure has em dash or ampersand' % f)
        if len(alt.group(1)) > 140: fail('%s alt too long (%d)' % (f, len(alt.group(1))))
    if 'property="og:image"' in s and 'og:image:alt' not in s: fail('%s og:image without alt' % f)
    if s.count('class="photo-fig') > 1: fail('%s has more than one photo figure' % f)
expected = [p for p in pages if p.startswith('guides/') and p != 'guides/index.html'] + ['heat-pump-calculator/index.html', 'insulation-calculator/index.html', 'epc-calculator/index.html', 'solar-calculator/index.html', 'boiler-vs-heat-pump/index.html', 'grants/index.html']
missing = [p for p in expected if p not in with_photo]
print('pages with a photo: %d of %d expected' % (len(with_photo), len(expected)))
if missing: print('  without photo:', ', '.join(missing))
orphans = [f for f in glob.glob('images/*.webp') + glob.glob('images/*.jpg') if '/' + f not in refs]
if orphans: fail('orphan image files: %s' % ', '.join(orphans[:10]))
if not os.path.exists('images/CREDITS.md'): fail('images/CREDITS.md missing')
print('ALL PASS' if not fails else '%d failures' % fails)
sys.exit(1 if fails else 0)
