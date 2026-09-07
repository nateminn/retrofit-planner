#!/usr/bin/env python3
"""Static gates for the fix-and-freshen round. Run from the repo root.
Usage: python3 docs/superpowers/tools/gates.py [--stage b|c|d]
Stage b: rules + links + footer + redirects (after commit B).
Stage c: adds zero stale price/label tokens (after commit C).
Stage d: adds 4-bed guide size checks (after commit D). Default: d (everything).
Exit code 1 if any check for the stage fails."""
import glob, json, os, re, sys

STAGE = 'd'
if '--stage' in sys.argv:
    STAGE = sys.argv[sys.argv.index('--stage') + 1]
ORDER = {'b': 1, 'c': 2, 'd': 3}

PAGES = sorted(set(glob.glob('index.html') + glob.glob('*/index.html') + glob.glob('guides/*/index.html')) - {'thank-you/index.html'})
ALL_HTML = PAGES + (['404.html'] if os.path.exists('404.html') else [])
failures = []

def check(name, ok, detail=''):
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ('  ' + detail)))
    if not ok:
        failures.append(name)

def visible_text(html):
    t = re.sub(r'<script.*?</script>', ' ', html, flags=re.S)
    t = re.sub(r'<style.*?</style>', ' ', t, flags=re.S)
    return re.sub(r'<[^>]+>', ' ', t)

contents = {f: open(f, encoding='utf-8').read() for f in ALL_HTML}

# --- stage b checks ---
bad = [f for f, s in contents.items() if '—' in s]
check('no em dashes', not bad, str(bad))

emoji = re.compile('[\U0001F300-\U0001FAFF☀-➿]')
bad = [f for f, s in contents.items() if emoji.search(s)]
check('no emoji', not bad, str(bad))

bad = [f for f, s in contents.items() if '2028' in s and 'Boiler Upgrade' in s and re.search(r'(until|to|runs? until) (April|March) 2028', s)]
check('no BUS 2028 claims', not bad, str(bad))

missing = set()
for f, s in contents.items():
    for href in re.findall(r'href="(/[^"#?]*)"', s):
        if re.search(r'\.(css|ico|png|xml|txt|webmanifest|js|html)$', href):
            target = href.lstrip('/')
        else:
            target = href.strip('/') + '/index.html' if href != '/' else 'index.html'
        if not os.path.exists(target):
            missing.add((f, href))
check('all internal links resolve', not missing, str(sorted(missing))[:600])

bad = []
for f, s in contents.items():
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        try:
            json.loads(m.group(1))
        except Exception as e:
            bad.append((f, str(e)[:60]))
check('all JSON-LD parses', not bad, str(bad))

footers = {}
for f, s in contents.items():
    m = re.search(r'<div class="footer-col">\s*<h4>Guides</h4>.*?</div>', s, re.S)
    footers[f] = re.sub(r'\s+', '', m.group(0)) if m else None
distinct = set(footers.values())
check('footer Guides block identical on all pages', len(distinct) == 1 and None not in distinct,
      'distinct=%d missing=%s' % (len(distinct), [f for f, v in footers.items() if v is None]))

check('_redirects has 9 rules', os.path.exists('_redirects') and
      len([l for l in open('_redirects') if l.strip() and not l.startswith('#')]) == 9)
check('404.html exists', os.path.exists('404.html'))
stray = [d for d in glob.glob('guides/*') if '{' in d]
check('no stray brace directory', not stray, str(stray))

# --- stage c checks ---
if ORDER[STAGE] >= 2:
    stale = re.compile(r'24\.5p|6\.76p|61\.64p|31\.65p|Q1 2026|0\.245,|0\.0676|15 to 18p|~16p|16p/kWh|£1,738')
    bad = {}
    annotation = re.compile(r'January to March 2026 gas price of 6\.76p per kWh')
    for f, s in contents.items():
        if STAGE == 'c' and f == 'guides/heat-pump-cost-4-bed-house/index.html':
            continue  # rewritten in commit D
        hits = sorted(set(stale.findall(annotation.sub('', s))))
        if hits:
            bad[f] = hits
    check('zero stale price/label tokens', not bad, str(bad)[:800])

    touched = [f for f in PAGES if f not in (
        'epc-calculator/index.html', 'contact/index.html', 'privacy/index.html', 'terms/index.html',
        'guides/condensation-mould-guide/index.html', 'guides/heat-pump-noise/index.html',
        'guides/how-to-improve-epc-rating/index.html', 'guides/planning-permission-heat-pump/index.html',
        'guides/radiator-sizing-heat-pump/index.html', 'guides/warm-homes-plan-2026/index.html')]
    bad = [f for f in touched if 'Updated March 2026' in contents[f] or 'Last checked March 2026' in contents[f]]
    check('no "Updated March 2026" on touched pages', not bad, str(bad))
    bad = [f for f in touched if 'guides/' in f and f != 'guides/index.html'
           and not re.search(r'"dateModified": ?"2026-09-06"', contents[f])]
    check('touched guides carry dateModified 2026-09-06', not bad, str(bad))

# --- stage d checks ---
if ORDER[STAGE] >= 3:
    g = contents['guides/heat-pump-cost-4-bed-house/index.html']
    body = re.search(r'<main.*?</main>', g, re.S).group(0)
    words = len(visible_text(body).split())
    links = len(re.findall(r'href="/[^"]*"', body))
    check('4-bed guide >= 2000 visible words (got %d)' % words, words >= 2000)
    check('4-bed guide >= 15 internal links in main (got %d)' % links, links >= 15)
    check('4-bed guide has 6 FAQ questions in schema',
          len(re.findall(r'"@type":"Question"', g)) == 6)

print()
print('ALL PASS' if not failures else 'FAILED: ' + ', '.join(failures))
sys.exit(1 if failures else 0)
