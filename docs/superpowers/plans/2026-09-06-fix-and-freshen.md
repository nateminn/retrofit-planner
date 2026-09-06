# RetrofitPlanner Fix and Freshen (September 2026) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the site's dead links, wrong grant facts and style-rule breaches, refresh every price and date to the Ofgem cap for 1 October to 31 December 2026, and expand the 4-bed heat pump guide to 2,000+ words, then deploy via a single push to main.

**Architecture:** The site is static HTML with no build step (repo root is the Netlify publish root). All changes are exact-string edits to committed HTML, applied by small Python scripts that assert each old string occurs the expected number of times before replacing it, so nothing is silently skipped or double-applied. A gates script enforces the site rules and the spec's verification list before every commit. Work happens on branch `fix-and-freshen-2026-09`, merged fast-forward to `main` at the end.

**Tech Stack:** HTML, CSS, vanilla JS, Python 3 (standard library only), git, Netlify `_redirects`, the Browser pane for calculator checks.

**Spec:** `docs/superpowers/specs/2026-09-06-fix-and-freshen-design.md` (read it first; section 2 holds the verified constants).

**Repo:** `/Users/nathan/Desktop/Projects/retrofit-planner`. Every command below runs from that directory. Use `/usr/bin/grep` (BSD grep); the shell's `grep` is ugrep and rejects long regexes.

**Site rules that every edit must respect:** no em dash character (U+2014) anywhere, no emoji, no "&" in visible copy (write "and"), internal links use a leading and trailing slash, canonical URLs use `www.`.

---

## File map

| Path | Change |
|---|---|
| `docs/superpowers/tools/gates.py` | Create. Static checks from spec section 4.1. |
| `docs/superpowers/tools/footer.py` | Create. Rewrites the footer Guides column on all 48 pages plus 404.html. |
| `docs/superpowers/tools/emdash.py` | Create. Applies the 53 hand-written em dash rewrites. |
| `docs/superpowers/tools/verify_model.py` | Create. Guard: reproduces the current tables from the site's stated model at the old rates, prints the new values. |
| `docs/superpowers/tools/apply_edits.py` | Create. Generic runner: applies `(old, new, count)` edits per page with assertions. |
| `docs/superpowers/tools/edits_*.py` | Create, one per task. Edit lists consumed by `apply_edits.py`. |
| `_redirects` | Create. 9 rules. |
| `404.html` | Create. Branded not-found page. |
| 48 existing `index.html` files | Footer column; prices, labels, dates as listed per task. |
| `guides/heat-pump-cost-4-bed-house/index.html` | Rewrite in full. |
| `CONTEXT.md` | Data section updated to the new constants. |
| `guides/{...}` stray empty directory | Delete. |

Commits: A (spec, already done) → B "Fix dead links, footer, redirects, 404 page, BUS facts, em dashes" → C "Refresh prices and dates to Ofgem October to December 2026" → D "Expand 4-bed heat pump cost guide" → merge to main → push.

---

## Constants used throughout (from spec section 2)

| Name | Old | New |
|---|---|---|
| Electricity unit rate | 0.245 (24.5p) | 0.2632 (26.32p) |
| Gas unit rate | 0.0676 (6.76p) | 0.0797 (7.97p) |
| Electricity standing charge | 61.64p/day (£225/yr) | 54.83p/day (£200/yr) |
| Gas standing charge | 31.65p/day (£115.52/yr) | 29.68p/day (£108.33/yr) |
| Heating oil | 0.068 (6.8p) | 0.090 (9.0p) |
| LPG | 0.095 | 0.095 |
| Heat pump tariff effective | 16p (ranges 16 to 20p) | 18p (ranges 17 to 20p) |
| Gas boiler efficiency | 0.90 | 0.90 |
| Air source COP | 2.9 (3.2 flats) | unchanged |
| Ground source COP | 3.7 | unchanged |
| Ofgem typical consumption | 2,700 kWh elec, 11,500 kWh gas | 2,500 kWh elec, 9,500 kWh gas (from 1 July 2026) |
| Ofgem typical annual bill | £1,738 | £1,723 |

Model: gas = demand / 0.90 × gas rate; heat pump standard = demand / COP × electricity rate; heat pump tariff = demand / COP × 0.18; electric boiler = demand × electricity rate; bill = kWh × rate + 365 × standing charge.

Recomputed core figures (demand in kWh):

| Demand | Gas | HP standard | HP tariff 18p | HP 17p | HP 20p | Electric boiler |
|---|---|---|---|---|---|---|
| 8,000 | £708 | £726 | £497 | £469 | £552 | £2,106 |
| 12,000 | £1,063 | £1,089 | £745 | £703 | £828 | £3,158 |
| 15,000 | £1,328 | £1,361 | £931 | £879 | £1,034 | £3,948 |
| 18,000 | £1,594 | £1,634 | £1,117 | £1,055 | £1,241 | £4,738 |
| 22,000 | £1,948 | £1,997 | £1,366 | £1,290 | £1,517 | n/a |

Old figures these replace: gas £601/£901/£1,127/£1,352/£1,653; HP standard £676/£1,014/£1,267/£1,521/£1,859; HP tariff £441/£662/£828/£993/£1,214; electric boiler £1,960/£2,940/£3,675/£4,410.

---

### Task 0: Preflight and gates script

**Files:**
- Create: `docs/superpowers/tools/gates.py`

- [ ] **Step 1: Confirm branch and clean tree**

Run: `git status -sb | head -3`
Expected: first line `## fix-and-freshen-2026-09`, nothing else listed (the spec is already committed as 3b85e1b).

- [ ] **Step 2: Write the gates script**

Create `docs/superpowers/tools/gates.py`:

```python
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

PAGES = sorted(set(glob.glob('index.html') + glob.glob('*/index.html') + glob.glob('guides/*/index.html')))
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
    for f, s in contents.items():
        hits = sorted(set(stale.findall(s)))
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
```

- [ ] **Step 3: Run the gates to record the baseline**

Run: `python3 docs/superpowers/tools/gates.py --stage b`
Expected: FAIL for "no em dashes", "no BUS 2028 claims", "all internal links resolve", "footer Guides block identical", "_redirects has 9 rules", "404.html exists", "no stray brace directory". PASS for "no emoji" and "all JSON-LD parses". Exit code 1. This is the starting state, not a problem.

---

### Task 1: Footer Guides column on every page

**Files:**
- Create: `docs/superpowers/tools/footer.py`
- Modify: all 48 `index.html` files

- [ ] **Step 1: Write the footer script**

Create `docs/superpowers/tools/footer.py`:

```python
#!/usr/bin/env python3
"""Replace the footer Guides column on every page with the canonical block."""
import glob, re

CANON = ('<div class="footer-col"><h4>Guides</h4>'
         '<a href="/guides/heat-pump-cost-4-bed-house/">Heat Pump Cost: 4-Bed House</a>'
         '<a href="/guides/heat-pump-cost-by-house-type/">Costs by House Type</a>'
         '<a href="/guides/heat-pump-running-costs/">Heat Pump Running Costs</a>'
         '<a href="/guides/best-heat-pump-tariffs/">Best Heat Pump Tariffs</a>'
         '<a href="/guides/boiler-upgrade-scheme-guide/">BUS Grant Guide</a>'
         '<a href="/guides/how-epc-points-are-calculated/">How EPC Points Are Calculated</a>'
         '</div>')
PATTERN = re.compile(r'<div class="footer-col">\s*<h4>Guides</h4>.*?</div>', re.S)

pages = sorted(set(glob.glob('index.html') + glob.glob('*/index.html') + glob.glob('guides/*/index.html')))
if glob.glob('404.html'):
    pages.append('404.html')
changed = 0
for f in pages:
    s = open(f, encoding='utf-8').read()
    n = len(PATTERN.findall(s))
    assert n == 1, '%s: expected 1 Guides block, found %d' % (f, n)
    new = PATTERN.sub(lambda m: CANON, s)
    if new != s:
        open(f, 'w', encoding='utf-8').write(new)
        changed += 1
print('pages scanned %d, rewritten %d' % (len(pages), changed))
```

- [ ] **Step 2: Run it**

Run: `python3 docs/superpowers/tools/footer.py`
Expected: `pages scanned 48, rewritten 48` (every page had a different or dead list).

- [ ] **Step 3: Verify**

Run: `/usr/bin/grep -rl 'guides/epc-explained/\|guides/heat-pump-guide/\|guides/insulation-guide/\|guides/boiler-upgrade-scheme/"\|guides/average-energy-bills/"' --include='*.html' . | wc -l`
Expected: `0`

Run: `python3 docs/superpowers/tools/gates.py --stage b 2>&1 | /usr/bin/grep -E 'footer|internal links'`
Expected: `PASS footer Guides block identical on all pages` and `PASS all internal links resolve`.

---

### Task 2: Redirects, 404 page, stray directory

**Files:**
- Create: `_redirects`
- Create: `404.html`
- Delete: `guides/{heat-pump-noise,is-loft-insulation-worth-it,heat-pump-vs-new-boiler,eco4-scheme-explained,best-heat-pump-tariffs,solar-panel-payback-uk}`

- [ ] **Step 1: Create `_redirects`** (exact content, whitespace-separated columns)

```
/guides/heat-pump-guide/          /guides/heat-pump-cost-by-house-type/    301
/guides/insulation-guide/         /guides/is-loft-insulation-worth-it/     301
/guides/epc-explained/            /guides/how-epc-points-are-calculated/   301
/guides/boiler-upgrade-scheme/    /guides/boiler-upgrade-scheme-guide/     301
/guides/average-energy-bills/     /guides/average-energy-bills-uk/         301
/epc-calculator/epc-calculator/   /epc-calculator/                         301
/guides/heat-pump-running-costs-uk-electricity-vs-gas-compared   /guides/heat-pump-running-costs/   301
/CONTEXT.md                       /404.html                                404
/docs/*                           /404.html                                404
```

- [ ] **Step 2: Create `404.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Page Not Found | Retrofit Planner</title>
<meta name="robots" content="noindex, follow">
<link rel="icon" type="image/x-icon" href="/favicon.ico"><link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png"><link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png"><link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png"><link rel="manifest" href="/site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;0,9..144,700;1,9..144,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/style.css">
<style>
.nf{max-width:720px;margin:0 auto;padding:64px 24px 80px;text-align:center}
.nf h1{font-family:var(--font-display);font-size:2.2rem;font-weight:700;letter-spacing:-0.03em;margin-bottom:12px}
.nf p{color:var(--color-text-secondary);line-height:1.6;margin-bottom:28px}
.nf ul{list-style:none;padding:0;margin:0 auto;max-width:420px;display:grid;gap:10px;text-align:left}
.nf li a{display:block;padding:12px 16px;border:1px solid var(--color-border);border-radius:var(--radius-md);background:var(--color-surface);color:var(--color-accent);font-weight:600;text-decoration:none}
.nf li a:hover{border-color:var(--color-accent-border);background:var(--color-accent-bg)}
</style>
</head>
<body>
<nav class="nav"><div class="nav-inner"><a href="/" class="nav-logo">Retrofit Planner</a><ul class="nav-links"><li><a href="/heat-pump-calculator/">Heat Pump</a></li><li><a href="/insulation-calculator/">Insulation</a></li><li><a href="/epc-calculator/">EPC Rating</a></li><li><a href="/solar-calculator/">Solar Panels</a></li><li><a href="/grants/">Grants</a></li><li><a href="/guides/">Guides</a></li></ul></div></nav>
<main class="nf">
<h1>Page not found</h1>
<p>That page has moved or never existed. The calculators and guides below cover everything on the site.</p>
<ul>
<li><a href="/heat-pump-calculator/">Heat Pump Cost Calculator</a></li>
<li><a href="/insulation-calculator/">Insulation Savings Calculator</a></li>
<li><a href="/epc-calculator/">EPC Improvement Planner</a></li>
<li><a href="/solar-calculator/">Solar Panel Calculator</a></li>
<li><a href="/boiler-vs-heat-pump/">Boiler vs Heat Pump</a></li>
<li><a href="/grants/">Grant Eligibility Checker</a></li>
<li><a href="/guides/">All guides</a></li>
</ul>
</main>
<footer class="footer"><div class="footer-inner"><div><div class="footer-brand">Retrofit Planner</div><p class="footer-about">Free tools to help UK homeowners plan energy-efficient home improvements.</p></div><div class="footer-col"><h4>Calculators</h4><a href="/heat-pump-calculator/">Heat Pump Cost Calculator</a><a href="/insulation-calculator/">Insulation Savings Calculator</a><a href="/epc-calculator/">EPC Improvement Planner</a><a href="/solar-calculator/">Solar Panel ROI Calculator</a><a href="/boiler-vs-heat-pump/">Boiler vs Heat Pump</a><a href="/grants/">Grant Eligibility Checker</a></div><div class="footer-col"><h4>Guides</h4><a href="/guides/heat-pump-cost-4-bed-house/">Heat Pump Cost: 4-Bed House</a><a href="/guides/heat-pump-cost-by-house-type/">Costs by House Type</a><a href="/guides/heat-pump-running-costs/">Heat Pump Running Costs</a><a href="/guides/best-heat-pump-tariffs/">Best Heat Pump Tariffs</a><a href="/guides/boiler-upgrade-scheme-guide/">BUS Grant Guide</a><a href="/guides/how-epc-points-are-calculated/">How EPC Points Are Calculated</a></div><div class="footer-col"><h4>Company</h4><a href="/about/">About Us</a><a href="/methodology/">Our Methodology</a><a href="/privacy/">Privacy Policy</a><a href="/terms/">Terms of Use</a><a href="/contact/">Contact</a></div></div><div class="attribution">Data from <a href="https://www.ofgem.gov.uk/check-if-energy-price-cap-affects-you" target="_blank" rel="noopener">Ofgem</a>, <a href="https://energysavingtrust.org.uk/" target="_blank" rel="noopener">Energy Saving Trust</a>, and <a href="https://www.gov.uk/" target="_blank" rel="noopener">GOV.UK</a>.</div></footer>
</body>
</html>
```

- [ ] **Step 3: Remove the stray directory**

Run: `rmdir "guides/{heat-pump-noise,is-loft-insulation-worth-it,heat-pump-vs-new-boiler,eco4-scheme-explained,best-heat-pump-tariffs,solar-panel-payback-uk}" && ls guides | /usr/bin/grep -c '{'`
Expected: `0`

- [ ] **Step 4: Verify**

Run: `python3 docs/superpowers/tools/gates.py --stage b 2>&1 | /usr/bin/grep -E 'redirects|404|stray|footer'`
Expected: all four lines PASS (404.html is picked up by the footer identity check too).

---

### Task 3: Boiler Upgrade Scheme facts (4 files)

**Files:**
- Create: `docs/superpowers/tools/apply_edits.py` (generic runner, reused by every later task)
- Create: `docs/superpowers/tools/edits_bus.py`
- Modify: `heat-pump-calculator/index.html`, `guides/heat-pump-old-house/index.html`, `guides/boiler-upgrade-scheme-guide/index.html`, `grants/index.html`

- [ ] **Step 1: Write the generic edit runner**

Create `docs/superpowers/tools/apply_edits.py`:

```python
#!/usr/bin/env python3
"""Apply exact-string edits with assertions.
Usage: python3 docs/superpowers/tools/apply_edits.py edits_bus [--check]
The module must define EDITS = {path: [(old, new) | (old, new, count), ...]}.
Every old string must occur exactly `count` times (default 1) in the file, or the
file is left untouched and the script exits 1. --check only verifies presence."""
import importlib, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
mod = importlib.import_module(sys.argv[1])
check_only = '--check' in sys.argv
problems = []
for path, edits in mod.EDITS.items():
    s = open(path, encoding='utf-8').read()
    for e in edits:
        old, new = e[0], e[1]
        count = e[2] if len(e) > 2 else 1
        n = s.count(old)
        if n != count:
            problems.append('%s: expected %d, found %d: %r' % (path, count, n, old[:90]))
            continue
        if '—' in new:
            problems.append('%s: replacement contains an em dash: %r' % (path, new[:90]))
            continue
        s = s.replace(old, new)
    if not problems and not check_only:
        open(path, 'w', encoding='utf-8').write(s)
if problems:
    print('\n'.join(problems))
    sys.exit(1)
print(('checked' if check_only else 'applied') + ' %d files, %d edits' %
      (len(mod.EDITS), sum(len(v) for v in mod.EDITS.values())))
```

- [ ] **Step 2: Write the BUS edit list**

Create `docs/superpowers/tools/edits_bus.py`:

```python
EDITS = {
 'heat-pump-calculator/index.html': [
  ('covers air source heat pumps. £6,000 for ground source. Available until March 2028. Applied automatically by your installer.',
   'covers air source and ground source heat pumps, with £9,000 if you are replacing an oil or LPG boiler. The scheme runs to 2030. Applied automatically by your installer.'),
  ('The Boiler Upgrade Scheme provides £7,500 towards an air source heat pump and £6,000 towards a ground source heat pump.',
   'The Boiler Upgrade Scheme provides £7,500 towards an air source or ground source heat pump, and £9,000 if you are replacing an oil or LPG boiler.'),
  ('provides £7,500 for an air source heat pump and £6,000 for a ground source heat pump.',
   'provides £7,500 for an air source or ground source heat pump, rising to £9,000 if you are replacing an oil or LPG boiler.'),
 ],
 'guides/heat-pump-old-house/index.html': [
  ('The scheme runs until April 2028.</p>', 'The scheme runs to 2030.</p>'),
 ],
 'guides/boiler-upgrade-scheme-guide/index.html': [
  ('"text":"The scheme runs until April 2028. The government has extended it from its original March 2025 end date and increased funding. Apply well before the deadline, as installer availability tightens closer to scheme closures."',
   '"text":"The scheme now runs to 2030. It was extended on 28 April 2026 under the Warm Homes Plan, with a £400 million budget for 2026 to 2027. Apply well before the end date, as installer availability tightens closer to scheme closures."'),
  ('The scheme runs until April 2028 and is available to all homeowners',
   'The scheme runs to 2030 and is available to all homeowners'),
  ('<p>The BUS has been extended and expanded. The current funding runs until April 2028. If demand exceeds supply, the scheme may close early or be replaced. Applying sooner reduces this risk.</p>',
   '<p>The BUS has been extended and expanded. On 28 April 2026 the government extended it to 2030 under the Warm Homes Plan and set a £400 million budget for 2026 to 2027. If demand exceeds supply in any year, applications can pause, so applying sooner reduces this risk.</p>'),
  ('<p>April 2028. Apply well before the deadline.', '<p>2030, following the April 2026 extension. Apply well before the end date.'),
  ('<tr><td>Ground source heat pump</td><td class="highlight-cell">£7,500</td><td>£15,000 to £35,000</td><td>£7,500 to £27,500</td></tr></tbody></table>',
   '<tr><td>Ground source heat pump</td><td class="highlight-cell">£7,500</td><td>£15,000 to £35,000</td><td>£7,500 to £27,500</td></tr>\n<tr><td>Air or ground source, replacing oil or LPG</td><td class="highlight-cell">£9,000</td><td>£9,000 to £13,000</td><td>£0 to £4,000</td></tr>\n<tr><td>Air-to-air heat pump</td><td class="highlight-cell">£2,500</td><td>£3,000 to £8,000</td><td>£500 to £5,500</td></tr></tbody></table>'),
  ('<p>£7,500 for both air source and ground source heat pumps. It is deducted',
   '<p>£7,500 for both air source and ground source heat pumps, or £9,000 if you are replacing an oil or LPG boiler. Air-to-air systems get £2,500. It is deducted'),
  ('"text":"The grant is £7,500 for an air source heat pump and £7,500 for a ground source heat pump. It is deducted',
   '"text":"The grant is £7,500 for an air source or ground source heat pump, £9,000 if you are replacing an oil or LPG boiler, and £2,500 for an air-to-air system. It is deducted'),
 ],
 'grants/index.html': [
  ('Provides £7,500 towards an air source heat pump or £6,000 towards a ground source heat pump.',
   'Provides £7,500 towards an air source or ground source heat pump, rising to £9,000 if you are replacing an oil or LPG boiler.'),
  (' and no existing oil or LPG boiler (for the full grant)', ''),
  ('Towards an air source heat pump. Applied by your MCS-certified installer.',
   'Towards an air source or ground source heat pump, or £9,000 if you are replacing oil or LPG. Applied by your MCS-certified installer.'),
  ("desc: 'Towards an air source heat pump installation. Your MCS-certified installer applies on your behalf.'",
   "desc: 'Towards an air source or ground source heat pump, or £9,000 if you are replacing an oil or LPG boiler. Your MCS-certified installer applies on your behalf.'"),
 ],
}
```

- [ ] **Step 3: Check presence, then apply**

Run: `python3 docs/superpowers/tools/apply_edits.py edits_bus --check`
Expected: `checked 4 files, 16 edits`. If any line prints `expected 1, found 0`, open that file, locate the sentence with `/usr/bin/grep -n`, and correct the `old` string to match byte-for-byte (do not loosen the assertion).

Run: `python3 docs/superpowers/tools/apply_edits.py edits_bus`
Expected: `applied 4 files, 16 edits`

- [ ] **Step 4: Verify**

Run: `/usr/bin/grep -rn '2028' --include='*.html' . | /usr/bin/grep -v 'docs/' | wc -l`
Expected: `0`

Run: `/usr/bin/grep -rn '£6,000 towards a ground\|£6,000 for a ground\|£6,000 for ground' --include='*.html' . | wc -l`
Expected: `0`

---

### Task 4: Em dashes (53 instances in 9 files)

**Files:**
- Create: `docs/superpowers/tools/emdash.py`
- Modify: `about/index.html`, `epc-calculator/index.html`, `insulation-calculator/index.html`, `grants/index.html`, `contact/index.html`, `solar-calculator/index.html`, `methodology/index.html`, `boiler-vs-heat-pump/index.html`, `privacy/index.html`

- [ ] **Step 1: Write the em dash edit list** (the `—` in the old strings is the em dash character itself)

Create `docs/superpowers/tools/emdash.py`:

```python
EDITS = {
 'about/index.html': [
  ('No sales pitch, no hidden agenda — just clear data and honest calculations.',
   'No sales pitch, no hidden agenda, just clear data and honest calculations.'),
  ('Heat pumps, insulation, solar panels, EPC improvements — there', 'Heat pumps, insulation, solar panels, EPC improvements: there'),
  ('<strong>Ofgem</strong> — energy prices', '<strong>Ofgem</strong>: energy prices'),
  ('<strong>Energy Saving Trust (EST)</strong> — installation costs', '<strong>Energy Saving Trust (EST)</strong>: installation costs'),
  ('<strong>BEIS / DESNZ</strong> — government', '<strong>BEIS / DESNZ</strong>: government'),
  ('<strong>BRE (Building Research Establishment)</strong> — the Standard', '<strong>BRE (Building Research Establishment)</strong>: the Standard'),
  ('<strong>GOV.UK</strong> — grant scheme', '<strong>GOV.UK</strong>: grant scheme'),
  ('<strong>Installer referrals</strong> — when you click', '<strong>Installer referrals</strong>: when you click'),
  ('<strong>Product recommendations</strong> — some pages', '<strong>Product recommendations</strong>: some pages'),
  ('run entirely in your browser — we don', 'run entirely in your browser. We don'),
  ('</a> — ', '</a>: ', 6),
  (' (coming soon)', '', 4),
 ],
 'epc-calculator/index.html': [
  ('should start there — it', 'should start there. It'),
  ('</strong> — £', '</strong>: £', 9),
  ('Landlords should plan ahead — the most', 'Landlords should plan ahead. The most'),
  ('Consider further improvements for lower bills — try our', 'Consider further improvements for lower bills. Try our'),
  ("' — target reached'", "', target reached'"),
  ("' points — '", "' points: '"),
  ("' — reaches Band '", "', reaches Band '"),
 ],
 'insulation-calculator/index.html': [
  ('alternating long and short bricks — that indicates', 'alternating long and short bricks, which indicates'),
  ('after cavity fill — get a survey', 'after cavity fill, so get a survey'),
  ("' — costs £'", "', costs £'"),
  ("' — payback in '", "', payback in '"),
  ("' — <strong style", "', <strong style"),
 ],
 'grants/index.html': [
  ('local authority schemes — all in one place.', 'local authority schemes, all in one place.'),
  ('applies on your behalf — the grant is deducted', 'applies on your behalf, and the grant is deducted'),
  ('Eligibility criteria may change — always verify', 'Eligibility criteria may change, so always verify'),
  ('by your installer — no application needed.', 'by your installer, no application needed.'),
 ],
 'contact/index.html': [
  ('</strong> — ', '</strong>: ', 4),
 ],
 'solar-calculator/index.html': [
  ('per year — roughly equivalent', 'per year, roughly equivalent'),
  ('supplies your electricity — shop around', 'supplies your electricity, so shop around'),
  ('per year — equivalent to driving', 'per year, equivalent to driving'),
 ],
 'methodology/index.html': [
  ('vary by property — our estimates', 'vary by property, so our estimates'),
  ('change frequently — we review', 'change frequently, so we review'),
  ('run in your browser — we do not', 'run in your browser. We do not'),
 ],
 'boiler-vs-heat-pump/index.html': [
  ('</a> — we recommend insulating', '</a>. We recommend insulating'),
  ('MCS-certified installer — no separate application needed.', 'MCS-certified installer, with no separate application needed.'),
  ('phased out — a heat pump future-proofs', 'phased out, and a heat pump future-proofs'),
 ],
 'privacy/index.html': [
  ('aggregated and anonymous — we cannot', 'aggregated and anonymous, so we cannot'),
 ],
}
```

- [ ] **Step 2: Check, apply, verify zero remain**

Run: `python3 docs/superpowers/tools/apply_edits.py emdash --check && python3 docs/superpowers/tools/apply_edits.py emdash`
Expected: `checked 9 files, 39 edits` then `applied 9 files, 39 edits`.

Run: `/usr/bin/grep -rl '—' --include='*.html' . | /usr/bin/grep -v docs/ | wc -l`
Expected: `0`. If a file remains, print its line with `/usr/bin/grep -n '—' FILE`, add a tuple for it to `emdash.py`, and rerun; do not use a blanket regex replacement.

- [ ] **Step 3: Full stage-b gate**

Run: `python3 docs/superpowers/tools/gates.py --stage b`
Expected: every line PASS, final line `ALL PASS`, exit 0.

---

### Task 5: Commit B

- [ ] **Step 1: Review the diff summary**

Run: `git status --short | wc -l && git diff --stat | tail -1`
Expected: about 52 changed files plus `_redirects`, `404.html` and the tools. The stat line ends with insertions and deletions of a few hundred lines each.

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "Fix dead links, footer, redirects, 404 page, BUS facts, em dashes

Harmonise the footer Guides column on all 48 pages (5 links pointed at
guides that were never built), add Netlify redirects for the 7 dead URLs
and a branded 404 page, correct Boiler Upgrade Scheme facts (runs to 2030,
ground source 7,500, 9,000 for oil and LPG homes, 2,500 air-to-air),
remove the 53 em dashes that broke site rule 1, and delete a stray empty
directory.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

Expected: one commit on `fix-and-freshen-2026-09`; `git status` clean.

---

### Task 6: Model guard (prove the recompute is safe)

**Files:**
- Create: `docs/superpowers/tools/verify_model.py`

- [ ] **Step 1: Write the guard**

Create `docs/superpowers/tools/verify_model.py`:

```python
#!/usr/bin/env python3
"""Guard for the price refresh. Reproduces the figures currently on the pages from the
site's stated model at the OLD rates (tolerance 2 pounds), then prints the NEW figures."""
import sys
OLD = dict(E=0.245, G=0.0676, SCE=0.6164, SCG=0.3165, HP=0.16)
NEW = dict(E=0.2632, G=0.0797, SCE=0.5483, SCG=0.2968, HP=0.18)
def gas(d, r): return round(d / 0.9 * r['G'])
def hpstd(d, r, cop=2.9): return round(d / cop * r['E'])
def hptar(d, r, rate=None): return round(d / 2.9 * (rate or r['HP']))
def eboil(d, r): return round(d * r['E'])
def bill_gas(k, r): return round(k * r['G'] + 365 * r['SCG'])
def bill_elec(k, r): return round(k * r['E'] + 365 * r['SCE'])
D5 = (8000, 12000, 15000, 18000, 22000)
D4 = (8000, 12000, 15000, 18000)
checks = [
 ('running-costs gas', [gas(d, OLD) for d in D5], [601, 901, 1127, 1352, 1653]),
 ('running-costs hp standard', [hpstd(d, OLD) for d in D5], [676, 1014, 1267, 1521, 1859]),
 ('running-costs hp tariff 16p', [hptar(d, OLD) for d in D5], [441, 662, 828, 993, 1214]),
 ('running-costs hp tariff 20p upper', [hptar(d, OLD, 0.20) for d in D5], [529, 794, 993, 1192, 1457]),
 ('electric boiler', [eboil(d, OLD) for d in D4], [1960, 2940, 3675, 4410]),
 ('vs-boiler 15yr running totals', [(901 + 100) * 15, (1014 + 65) * 15, (662 + 65) * 15], [15015, 16185, 10905]),
 ('avg-bills gas by kWh', [bill_gas(k, OLD) for k in (5500, 8500, 14000)], [487, 690, 1062]),
 ('avg-bills elec by kWh', [bill_elec(k, OLD) for k in (1800, 2300, 2700, 3500)], [666, 789, 887, 1083]),
 ('solar 45% self-use', [round(g * 0.45 * OLD['E']) for g in (2850, 3800, 3320, 5700)], [314, 419, 366, 628]),
 ('solar 80% self-use with battery', [round(3800 * 0.8 * OLD['E'])], [745]),
 ('solar export 55% at 8p', [round(g * 0.55 * 0.08) for g in (2850, 3800, 3320, 5700)], [125, 167, 146, 250]),
 ('ground source 4-bed COP 3.7 at 16p', [round(18000 / 3.7 * 0.16)], [778]),
]
ok = True
for name, got, exp in checks:
    good = all(abs(a - b) <= 2 for a, b in zip(got, exp)) and len(got) == len(exp)
    ok &= good
    print(('PASS ' if good else 'FAIL ') + name + ('' if good else '  got %s expected %s' % (got, exp)))
# Known arithmetic errors on the current average-energy-bills page (the kWh column is authoritative):
known = [(11500, 905), (18000, 1347), (24000, 1856)]
print('KNOWN avg-bills gas rows that do not reproduce (recompute from the stated kWh):',
      [(k, bill_gas(k, OLD), page) for k, page in known])
print()
print('NEW gas 8k..22k        ', [gas(d, NEW) for d in D5])
print('NEW hp standard        ', [hpstd(d, NEW) for d in D5])
print('NEW hp tariff 18p      ', [hptar(d, NEW) for d in D5])
print('NEW hp tariff 17p      ', [hptar(d, NEW, 0.17) for d in D5])
print('NEW hp tariff 20p      ', [hptar(d, NEW, 0.20) for d in D5])
print('NEW electric boiler    ', [eboil(d, NEW) for d in D4])
print('NEW avg-bills gas      ', [bill_gas(k, NEW) for k in (5500, 8500, 11500, 14000, 18000, 24000)])
print('NEW avg-bills elec     ', [bill_elec(k, NEW) for k in (1800, 2300, 2700, 3500)])
print('NEW ofgem typical 2500/9500', bill_elec(2500, NEW) + bill_gas(9500, NEW))
print('NEW solar 45%          ', [round(g * 0.45 * NEW['E']) for g in (2850, 3800, 3320, 5700)], 'battery 80%:', round(3800 * 0.8 * NEW['E']))
print('NEW 4-bed: gas %d, hp std %d, hp tariff %d, elec boiler %d, gshp %d, semi14k gas %d hp %d tariff %d' % (
    gas(18000, NEW), hpstd(18000, NEW), hptar(18000, NEW), eboil(18000, NEW), round(18000 / 3.7 * 0.18),
    gas(14000, NEW), hpstd(14000, NEW), hptar(14000, NEW)))
sys.exit(0 if ok else 1)
```

- [ ] **Step 2: Run it**

Run: `python3 docs/superpowers/tools/verify_model.py`
Expected: every check PASS, then the KNOWN line showing `(11500, 893, 905), (18000, 1332, 1347), (24000, 1738, 1856)`, then exactly these NEW lines:

```
NEW gas 8k..22k         [708, 1063, 1328, 1594, 1948]
NEW hp standard         [726, 1089, 1361, 1634, 1997]
NEW hp tariff 18p       [497, 745, 931, 1117, 1366]
NEW hp tariff 17p       [469, 703, 879, 1055, 1290]
NEW hp tariff 20p       [552, 828, 1034, 1241, 1517]
NEW electric boiler     [2106, 3158, 3948, 4738]
NEW avg-bills gas       [547, 786, 1025, 1224, 1543, 2021]
NEW avg-bills elec      [674, 805, 911, 1121]
NEW ofgem typical 2500/9500 1723
NEW solar 45%           [338, 450, 393, 675] battery 80%: 800
NEW 4-bed: gas 1594, hp std 1634, hp tariff 1117, elec boiler 4738, gshp 876, semi14k gas 1240 hp 1271 tariff 869
```

If any NEW line differs from the above, stop: the constants in the script disagree with the spec, and every number in Tasks 9 to 21 was derived from these. Fix the script or the spec before continuing.

---

### Task 7: Calculators (constants, prose, labels, dates)

**Files:**
- Create: `docs/superpowers/tools/edits_calc.py`
- Modify: `heat-pump-calculator/index.html`, `boiler-vs-heat-pump/index.html`, `insulation-calculator/index.html`, `solar-calculator/index.html`, `grants/index.html`

- [ ] **Step 1: Write the edit list**

Create `docs/superpowers/tools/edits_calc.py`:

```python
EDITS = {
 'heat-pump-calculator/index.html': [
  ('energyPrices: { electricity: 0.245, gas: 0.0676, oil: 0.068, lpg: 0.095 },',
   'energyPrices: { electricity: 0.2632, gas: 0.0797, oil: 0.090, lpg: 0.095 }, // Ofgem cap Oct to Dec 2026; oil Sept 2026 market'),
  ('However, electricity costs more per unit than gas. At current Ofgem rates (24.5p/kWh electricity vs 6.76p/kWh gas as of Q1 2026), a heat pump with a COP of 3.0 costs roughly 8.2p per kWh of heat, compared to around 7.5p per kWh from a gas boiler operating at 90% efficiency. The savings are modest for gas users but substantial for anyone on oil, LPG, or electric heating.',
   'However, electricity costs more per unit than gas. At the Ofgem price cap for October to December 2026 (26.32p/kWh electricity vs 7.97p/kWh gas), a heat pump with a COP of 3.0 costs roughly 8.8p per kWh of heat, compared to around 8.9p per kWh from a gas boiler operating at 90% efficiency. On a standard tariff the two are level. The savings are real for gas users who switch to a heat pump tariff, and substantial for anyone on oil, LPG, or electric heating.'),
  ('At current Ofgem rates, a heat pump with a COP of 3.2 costs about 7.7p per kWh of heat versus 7.4p for gas.',
   'At the Ofgem price cap for October to December 2026, a heat pump with a COP of 3.2 costs about 8.2p per kWh of heat versus 8.9p for gas at 90% boiler efficiency.'),
  ('Updated March 2026 with latest Ofgem rates', 'Updated September 2026 with Ofgem October to December 2026 rates'),
  ('Energy prices from Ofgem (Q1 2026 price cap).', 'Energy prices from Ofgem (October to December 2026 price cap).'),
 ],
 'boiler-vs-heat-pump/index.html': [
  ('gasRate: 0.0676, elecRate: 0.245,', 'gasRate: 0.0797, elecRate: 0.2632,'),
  ('// Ofgem Q1 2026 rates, EST cost data', '// Ofgem cap Oct to Dec 2026 rates, EST cost data'),
  ('<p>Gas costs 6.76p per kWh (Ofgem Q1 2026) and a modern condensing boiler is around 92% efficient. Electricity costs 24.5p per kWh, but a heat pump delivers 2.5 to 3.5 kWh of heat per kWh of electricity (its coefficient of performance or COP). This means the effective cost per kWh of heat is roughly 7.35p for gas and 7p to 9.8p for a heat pump, depending on efficiency. In a well-insulated home with a properly sized heat pump, running costs are comparable or lower than gas.</p>',
   '<p>Gas costs 7.97p per kWh (Ofgem price cap, October to December 2026) and a modern condensing boiler is around 92% efficient. Electricity costs 26.32p per kWh, but a heat pump delivers 2.5 to 3.5 kWh of heat per kWh of electricity (its coefficient of performance or COP). This means the effective cost per kWh of heat is roughly 8.7p for gas and 7.5p to 10.5p for a heat pump, depending on efficiency. In a well-insulated home with a properly sized heat pump, running costs are level with or lower than gas.</p>'),
  ('Updated March 2026 with Ofgem Q1 rates', 'Updated September 2026 with Ofgem October to December 2026 rates'),
  ('Ofgem</a> Q1 2026 price cap. Calculator results are estimates.',
   'Ofgem</a> price cap, October to December 2026. Calculator results are estimates.'),
 ],
 'insulation-calculator/index.html': [
  ('fuelPrices: { gas: 0.0676, oil: 0.068, lpg: 0.095, electricity: 0.245 },',
   'fuelPrices: { gas: 0.0797, oil: 0.090, lpg: 0.095, electricity: 0.2632 },'),
  ('>Ofgem</a> Q1 2026 price cap', '>Ofgem</a> price cap, October to December 2026; oil at September 2026 market rate'),
  ('Updated March 2026 with latest Ofgem rates', 'Updated September 2026 with Ofgem October to December 2026 rates'),
  ('Energy prices from Ofgem (Q1 2026 price cap).', 'Energy prices from Ofgem (October to December 2026 price cap).'),
 ],
 'solar-calculator/index.html': [
  ('electricityRate: 0.245, // Ofgem Q1 2026', 'electricityRate: 0.2632, // Ofgem cap Oct to Dec 2026'),
  ('// Sources: PVGIS (EU JRC), Energy Saving Trust, Ofgem Q1 2026', '// Sources: PVGIS (EU JRC), Energy Saving Trust, Ofgem cap Oct to Dec 2026'),
  ('Updated March 2026 with latest electricity rates', 'Updated September 2026 with October to December 2026 electricity rates'),
  ('Electricity prices from Ofgem (Q1 2026 price cap).', 'Electricity prices from Ofgem (October to December 2026 price cap).'),
 ],
 'grants/index.html': [
  ('Updated March 2026', 'Updated September 2026'),
  ('Last checked March 2026', 'Last checked September 2026'),
  ('published scheme rules as of March 2026', 'published scheme rules as of September 2026'),
 ],
}
```

- [ ] **Step 2: Check, apply, verify**

Run: `python3 docs/superpowers/tools/apply_edits.py edits_calc --check && python3 docs/superpowers/tools/apply_edits.py edits_calc`
Expected: `checked 5 files, 21 edits` then `applied 5 files, 21 edits`.

Run: `/usr/bin/grep -n '0\.245\|0\.0676\|Q1 2026\|March 2026' heat-pump-calculator/index.html boiler-vs-heat-pump/index.html insulation-calculator/index.html solar-calculator/index.html grants/index.html | wc -l`
Expected: `0`

Run: `python3 -c "import re;s=open('heat-pump-calculator/index.html').read();print(re.search(r'energyPrices: \{[^}]*\}',s).group(0))"`
Expected: `energyPrices: { electricity: 0.2632, gas: 0.0797, oil: 0.090, lpg: 0.095 }`

---

### Task 8: Homepage, about, methodology, guides hub, CONTEXT.md

**Files:**
- Create: `docs/superpowers/tools/edits_core.py`
- Modify: `index.html`, `about/index.html`, `methodology/index.html`, `guides/index.html`, `CONTEXT.md`

- [ ] **Step 1: Write the edit list**

Create `docs/superpowers/tools/edits_core.py`:

```python
EDITS = {
 'index.html': [
  ('Updated March 2026 with latest Ofgem rates', 'Updated September 2026 with Ofgem October to December 2026 rates'),
  ('Updated quarterly with each new price cap. Currently using Q1 2026 rates.',
   'Updated with each new price cap. Currently using Ofgem rates for October to December 2026.'),
  ('Energy prices from Ofgem (Q1 2026 price cap).', 'Energy prices from Ofgem (October to December 2026 price cap).'),
 ],
 'about/index.html': [
  ('Energy prices from Ofgem (Q1 2026 price cap).', 'Energy prices from Ofgem (October to December 2026 price cap).'),
  ('We update our calculators within days of each new price cap taking effect.',
   'We update our calculators when Ofgem announces each new price cap.'),
 ],
 'methodology/index.html': [
  ('Our current rates are from the Q1 2026 price cap:',
   'Our current rates are from the price cap for 1 October to 31 December 2026, announced on 26 August 2026:'),
  ('<li>Electricity: 24.5p per kWh</li>', '<li>Electricity: 26.32p per kWh, standing charge 54.83p per day</li>'),
  ('<li>Gas: 6.76p per kWh</li>',
   '<li>Gas: 7.97p per kWh, standing charge 29.68p per day</li>\n            <li>Heating oil: 9.0p per kWh (September 2026 kerosene market price)</li>\n            <li>LPG: 9.5p per kWh (typical bulk contract)</li>\n            <li>Heat pump tariff: 18p per kWh effective, assuming a well-scheduled time-of-use tariff such as Octopus Cosy with around 60% of heating shifted into the cheap windows</li>'),
  ('We update our calculators within one week of each new price cap taking effect (January, April, July, October).',
   'We update our calculators when Ofgem announces each new price cap (usually late February, May, August and November), so the figures cover the coming quarter.'),
 ],
 'guides/index.html': [
  ('What UK households actually pay for gas and electricity. Ofgem Q1 2026 data',
   'What UK households actually pay for gas and electricity. Ofgem October to December 2026 data'),
  ('Council Tax A to D. Closes 31 March 2026', 'Council Tax A to D. Closed 31 March 2026'),
 ],
 'CONTEXT.md': [
  ('### Energy Prices (Ofgem Q1 2026 Price Cap)', '### Energy Prices (Ofgem Price Cap, 1 October to 31 December 2026, announced 26 August 2026)'),
  ('- Electricity: 24.5p per kWh', '- Electricity: 26.32p per kWh'),
  ('- Gas: 6.76p per kWh', '- Gas: 7.97p per kWh'),
  ('- Electricity standing charge: 61.64p per day', '- Electricity standing charge: 54.83p per day'),
  ('- Gas standing charge: 31.65p per day',
   '- Gas standing charge: 29.68p per day\n- Ofgem typical consumption from 1 July 2026: 2,500 kWh electricity, 9,500 kWh gas (typical dual-fuel bill £1,723)\n- Heat pump tariff effective rate used in all tables: 18p per kWh (well-scheduled Octopus Cosy). OVO Heat Pump Plus closed to new customers February 2026.\n- Refresh recipe: run docs/superpowers/tools/verify_model.py, then update the constants in the four calculators and the tables listed in docs/superpowers/plans/2026-09-06-fix-and-freshen.md'),
  ('- Heating oil (kerosene): 6.8p per kWh', '- Heating oil (kerosene): 9.0p per kWh (September 2026, about 93p per litre including VAT)'),
  ('- BUS runs until April 2028', '- BUS runs to 2030 (extended 28 April 2026). £9,000 for homes replacing oil or LPG (from July 2026). £2,500 for air-to-air.'),
  ('- BUS: £7,500 air source, £6,000 ground source. Until April 2028.',
   '- BUS: £7,500 air source or ground source, £9,000 if replacing oil or LPG, £2,500 air-to-air. Runs to 2030.'),
 ],
}
```

- [ ] **Step 2: Check, apply, verify**

Run: `python3 docs/superpowers/tools/apply_edits.py edits_core --check && python3 docs/superpowers/tools/apply_edits.py edits_core`
Expected: `checked 5 files, 19 edits` then `applied 5 files, 19 edits`.

Run: `/usr/bin/grep -n 'Q1 2026\|24\.5p\|6\.76p\|2028' index.html about/index.html methodology/index.html guides/index.html CONTEXT.md | wc -l`
Expected: `0`

Run: `/usr/bin/grep -c 'closes 31 March 2026' index.html guides/index.html`
Expected: both `0` (if the homepage still says "closes", add the tuple `('closes 31 March 2026', 'closed 31 March 2026')` for `index.html` to `edits_core.py` and rerun; the hub has a capitalised variant already handled).

---

## Recompute pages (Tasks 9 to 18)

Every task below follows the same shape: write an edit module with exact `(old, new)` strings taken from the current file, run `apply_edits.py MODULE --check`, then apply, then confirm no stale token remains in that file. Full-row replacements are used for table rows so the assertion is unambiguous. Where the same substring legitimately occurs twice, the tuple carries a count.

### Task 9: heat-pump-running-costs

**Files:**
- Create: `docs/superpowers/tools/edits_running.py`
- Modify: `guides/heat-pump-running-costs/index.html`

- [ ] **Step 1: Write the edit list**

```python
EDITS = {'guides/heat-pump-running-costs/index.html': [
 ('<tr><td>Mid-terrace (2 bed)</td><td>8,000</td><td>£601</td><td>£676</td><td class="highlight-cell">£441 to £529</td></tr>',
  '<tr><td>Mid-terrace (2 bed)</td><td>8,000</td><td>£708</td><td>£726</td><td class="highlight-cell">£469 to £552</td></tr>'),
 ('<tr><td>Semi-detached (3 bed)</td><td>12,000</td><td>£901</td><td>£1,014</td><td class="highlight-cell">£662 to £794</td></tr>',
  '<tr><td>Semi-detached (3 bed)</td><td>12,000</td><td>£1,063</td><td>£1,089</td><td class="highlight-cell">£703 to £828</td></tr>'),
 ('<tr><td>Semi-detached (3 bed, old)</td><td>15,000</td><td>£1,127</td><td>£1,267</td><td class="highlight-cell">£828 to £993</td></tr>',
  '<tr><td>Semi-detached (3 bed, old)</td><td>15,000</td><td>£1,328</td><td>£1,361</td><td class="highlight-cell">£879 to £1,034</td></tr>'),
 ('<tr><td>Detached (4 bed)</td><td>18,000</td><td>£1,352</td><td>£1,521</td><td class="highlight-cell">£993 to £1,192</td></tr>',
  '<tr><td>Detached (4 bed)</td><td>18,000</td><td>£1,594</td><td>£1,634</td><td class="highlight-cell">£1,055 to £1,241</td></tr>'),
 ('<tr><td>Detached (4 bed, old)</td><td>22,000</td><td>£1,653</td><td>£1,859</td><td class="highlight-cell">£1,214 to £1,457</td></tr>',
  '<tr><td>Detached (4 bed, old)</td><td>22,000</td><td>£1,948</td><td>£1,997</td><td class="highlight-cell">£1,290 to £1,517</td></tr>'),
 ('Gas boiler assumes 90% efficiency at 6.76p/kWh. Heat pump assumes COP 2.9. Standard tariff: 24.5p/kWh. Heat pump tariff: 15 to 18p/kWh effective rate. Based on Ofgem Q1 2026 price cap.',
  'Gas boiler assumes 90% efficiency at 7.97p/kWh. Heat pump assumes COP 2.9. Standard tariff: 26.32p/kWh. Heat pump tariff: 17 to 20p/kWh effective rate. Based on the Ofgem price cap for October to December 2026.'),
 ('<th>Cost per kWh of heat (HP tariff, 16p)</th>', '<th>Cost per kWh of heat (HP tariff, 18p)</th>'),
 ('<tr><td>2.5 (poor installation)</td><td>9.8p</td><td>6.4p</td></tr>', '<tr><td>2.5 (poor installation)</td><td>10.5p</td><td>7.2p</td></tr>'),
 ('<tr><td>2.8 (average)</td><td>8.8p</td><td>5.7p</td></tr>', '<tr><td>2.8 (average)</td><td>9.4p</td><td>6.4p</td></tr>'),
 ('<tr><td>3.0 (good)</td><td>8.2p</td><td class="highlight-cell">5.3p</td></tr>', '<tr><td>3.0 (good)</td><td>8.8p</td><td class="highlight-cell">6.0p</td></tr>'),
 ('<tr><td>3.2 (excellent)</td><td>7.7p</td><td class="highlight-cell">5.0p</td></tr>', '<tr><td>3.2 (excellent)</td><td>8.2p</td><td class="highlight-cell">5.6p</td></tr>'),
 ('<tr><td>4.0 (ground source)</td><td>6.1p</td><td class="highlight-cell">4.0p</td></tr>', '<tr><td>4.0 (ground source)</td><td>6.6p</td><td class="highlight-cell">4.5p</td></tr>'),
 ('For reference: gas boiler at 90% efficiency costs 7.5p per kWh of heat at 6.76p/kWh gas price.',
  'For reference: gas boiler at 90% efficiency costs 8.9p per kWh of heat at 7.97p/kWh gas price.'),
 ('<tr><td>Gas (mains)</td><td>6.76p</td><td>7.5p</td></tr>', '<tr><td>Gas (mains)</td><td>7.97p</td><td>8.9p</td></tr>'),
 ('<tr><td>Oil (kerosene)</td><td>6.8p</td><td>8.0p</td></tr>', '<tr><td>Oil (kerosene)</td><td>9.0p</td><td>10.6p</td></tr>'),
 ('<tr><td>Direct electric</td><td>24.5p</td><td>24.5p</td></tr>', '<tr><td>Direct electric</td><td>26.32p</td><td>26.32p</td></tr>'),
 ('<tr><td>Heat pump (standard tariff, COP 2.9)</td><td>24.5p</td><td class="highlight-cell">8.4p</td></tr>',
  '<tr><td>Heat pump (standard tariff, COP 2.9)</td><td>26.32p</td><td class="highlight-cell">9.1p</td></tr>'),
 ('<tr><td>Heat pump (HP tariff, COP 2.9)</td><td>~16p</td><td class="highlight-cell">5.5p</td></tr>',
  '<tr><td>Heat pump (HP tariff, COP 2.9)</td><td>~18p</td><td class="highlight-cell">6.2p</td></tr>'),
 ('Oil and LPG prices fluctuate significantly. Figures based on March 2026 market rates.',
  'Oil and LPG prices fluctuate significantly. Figures based on September 2026 market rates.'),
 ('On a standard electricity tariff, a heat pump costs slightly more to run than a gas boiler. On a dedicated heat pump tariff, it costs <span class="key-number">£200 to £400 less</span> per year.',
  'On a standard electricity tariff, a heat pump now costs about the same to run as a gas boiler. On a dedicated heat pump tariff, it costs <span class="key-number">£200 to £500 less</span> per year.'),
 ('<p>At the Q1 2026 Ofgem price cap, electricity costs 24.5p/kWh and gas costs 6.76p/kWh. Electricity is 3.6 times more expensive than gas. But a heat pump with a COP of 2.9 produces 2.9 kWh of heat for every 1 kWh of electricity. So the effective cost of heat from a heat pump is 24.5p divided by 2.9, which equals 8.4p per kWh of heat. Compare that to gas at 6.76p per kWh (assuming 90% boiler efficiency, the real cost is 7.5p per kWh of heat).</p>',
  '<p>At the Ofgem price cap for October to December 2026, electricity costs 26.32p/kWh and gas costs 7.97p/kWh. Electricity is 3.3 times more expensive than gas. But a heat pump with a COP of 2.9 produces 2.9 kWh of heat for every 1 kWh of electricity. So the effective cost of heat from a heat pump is 26.32p divided by 2.9, which equals 9.1p per kWh of heat. Compare that to gas at 7.97p per kWh (assuming 90% boiler efficiency, the real cost is 8.9p per kWh of heat).</p>'),
 ('<p>On a standard tariff, heat pump heating costs 8.4p per kWh versus gas at 7.5p per kWh. Gas wins by a narrow margin. On a heat pump tariff at an effective rate of 16p/kWh, heat pump heating costs 5.5p per kWh, beating gas comfortably.</p>',
  '<p>On a standard tariff, heat pump heating costs 9.1p per kWh versus gas at 8.9p per kWh. That is level, within the margin of any real installation. On a heat pump tariff at an effective rate of 18p/kWh, heat pump heating costs 6.2p per kWh, beating gas comfortably.</p>'),
 ('Effective rates of 15 to 18p/kWh are achievable.', 'Effective rates of 17 to 20p/kWh are achievable.'),
 ('<p>A 3-bed semi costs £1,267 on a standard tariff or £828 to £1,034 on a heat pump tariff.',
  '<p>A 3-bed semi costs £1,361 on a standard tariff or £879 to £1,034 on a heat pump tariff.'),
 ('On a standard electricity tariff, heat pumps cost slightly more to run than a gas boiler in most UK homes. On a dedicated heat pump tariff with cheaper off-peak rates, heat pumps are cheaper. For a 3-bed semi, annual heating costs are approximately £1,127 for gas, £1,267 for a heat pump on standard tariff, and £828 to £1,034 for a heat pump on a heat pump tariff.',
  'On a standard electricity tariff, heat pumps now cost about the same to run as a gas boiler in most UK homes. On a dedicated heat pump tariff with cheaper off-peak rates, heat pumps are cheaper. For a 3-bed semi, annual heating costs are approximately £1,328 for gas, £1,361 for a heat pump on standard tariff, and £879 to £1,034 for a heat pump on a heat pump tariff.'),
 ('A well-insulated 3-bed semi with a COP 2.9 heat pump costs £1,267 per year on a standard tariff or £828 to £1,034 on a heat pump tariff.',
  'A well-insulated 3-bed semi with a COP 2.9 heat pump costs £1,361 per year on a standard tariff or £879 to £1,034 on a heat pump tariff.'),
 ('This can reduce your effective electricity rate from 24.5p/kWh to around 15 to 18p/kWh for heating.',
  'This can reduce your effective electricity rate from 26.32p/kWh to around 17 to 20p/kWh for heating.'),
]}
```

- [ ] **Step 2: Check, apply, verify**

Run: `python3 docs/superpowers/tools/apply_edits.py edits_running --check && python3 docs/superpowers/tools/apply_edits.py edits_running`
Expected: `checked 1 files, 27 edits` then `applied 1 files, 27 edits`.

Run: `/usr/bin/grep -c '24\.5p\|6\.76p\|15 to 18p\|~16p\|16p/kWh\|£1,267\|£828 to £993' guides/heat-pump-running-costs/index.html`
Expected: `0` (the sources line still says "Q1 2026"; Task 20 sweeps that).

---

### Task 10: heat-pump-vs-new-boiler

**Files:**
- Create: `docs/superpowers/tools/edits_vsboiler.py`
- Modify: `guides/heat-pump-vs-new-boiler/index.html`

- [ ] **Step 1: Write the edit list**

```python
EDITS = {'guides/heat-pump-vs-new-boiler/index.html': [
 ('<tr><td>Annual heating cost</td><td>£901</td><td>£1,014</td><td>£662</td></tr>',
  '<tr><td>Annual heating cost</td><td>£1,063</td><td>£1,089</td><td>£745</td></tr>'),
 ('<tr><td>15-year running total</td><td>£15,015</td><td>£16,185</td><td>£10,905</td></tr>',
  '<tr><td>15-year running total</td><td>£17,445</td><td>£17,310</td><td>£12,150</td></tr>'),
 ('<td><strong>£17,515 to £18,515</strong></td><td><strong>£20,485 to £26,185</strong></td><td class="highlight-cell"><strong>£15,205 to £20,905</strong></td>',
  '<td><strong>£19,945 to £20,945</strong></td><td><strong>£21,610 to £27,310</strong></td><td class="highlight-cell"><strong>£16,450 to £22,150</strong></td>'),
 ('Gas boiler assumes 90% efficiency, 6.76p/kWh, annual service £100. Heat pump assumes COP 2.9, standard tariff 24.5p/kWh or HP tariff ~16p/kWh, service every 2 years at £150. 12,000 kWh annual heat demand. BUS grant of £7,500 applied. Ofgem Q1 2026 rates.',
  'Gas boiler assumes 90% efficiency, 7.97p/kWh, annual service £100. Heat pump assumes COP 2.9, standard tariff 26.32p/kWh or HP tariff ~18p/kWh, service every 2 years at £150. 12,000 kWh annual heat demand. BUS grant of £7,500 applied. Ofgem price cap, October to December 2026.'),
 ('<tr><td>2-bed terrace</td><td>£601</td><td>£676</td><td>£441</td><td class="highlight-cell">£160</td></tr>',
  '<tr><td>2-bed terrace</td><td>£708</td><td>£726</td><td>£497</td><td class="highlight-cell">£211</td></tr>'),
 ('<tr><td>3-bed semi</td><td>£901</td><td>£1,014</td><td>£662</td><td class="highlight-cell">£239</td></tr>',
  '<tr><td>3-bed semi</td><td>£1,063</td><td>£1,089</td><td>£745</td><td class="highlight-cell">£318</td></tr>'),
 ('<tr><td>3-bed detached</td><td>£1,127</td><td>£1,267</td><td>£828</td><td class="highlight-cell">£299</td></tr>',
  '<tr><td>3-bed detached</td><td>£1,328</td><td>£1,361</td><td>£931</td><td class="highlight-cell">£397</td></tr>'),
 ('<tr><td>4-bed detached</td><td>£1,352</td><td>£1,521</td><td>£993</td><td class="highlight-cell">£359</td></tr>',
  '<tr><td>4-bed detached</td><td>£1,594</td><td>£1,634</td><td>£1,117</td><td class="highlight-cell">£477</td></tr>'),
 ('Based on Ofgem Q1 2026 rates. Gas 6.76p/kWh at 90% efficiency. HP COP 2.9. Standard tariff 24.5p/kWh. HP tariff ~16p/kWh effective. Well-insulated properties.',
  'Based on the Ofgem price cap for October to December 2026. Gas 7.97p/kWh at 90% efficiency. HP COP 2.9. Standard tariff 26.32p/kWh. HP tariff ~18p/kWh effective. Well-insulated properties.'),
 ('Over 15 years, a heat pump on a dedicated tariff costs <span class="key-number">£2,000 to £5,000 less</span> than a new gas boiler for a typical 3-bed semi. On a standard electricity tariff, the boiler wins by a narrow margin.',
  'Over 15 years, a heat pump on a dedicated tariff costs <span class="key-number">around £1,000 less</span> than a new gas boiler for a typical 3-bed semi at the midpoint of each cost range, and up to £4,500 less if your radiators need little work. On a standard electricity tariff, the boiler wins by around £4,000.'),
 ("This single decision swings the comparison by £5,000 to £8,000 over the system's lifetime.",
  'This single decision swings the comparison by around £5,000 over 15 years.'),
 ('<p>On a heat pump tariff, a 3-bed semi saves £239 per year versus gas. Over 15 years that is £3,585 in running cost savings alone. A 4-bed detached saves £5,385 over 15 years.',
  '<p>On a heat pump tariff, a 3-bed semi saves £318 per year versus gas. Over 15 years that is £4,770 in running cost savings alone. A 4-bed detached saves £7,155 over 15 years.'),
 ('On standard electricity at 24.5p/kWh, a heat pump costs more to run than gas. If you cannot or will not switch tariff, the running cost disadvantage wipes out the upfront grant benefit.',
  'On standard electricity at 26.32p/kWh, a heat pump costs about the same to run as gas. If you cannot or will not switch tariff, there is no running cost saving to offset the higher upfront cost.'),
 ('Oil and LPG users save £300 to £600 per year by switching.',
  'Oil and LPG users save £120 to £270 per year on a standard tariff and £350 to £800 on a heat pump tariff.'),
 ('heat pump tariff</a>, yes, by £2,000 to £5,000. On a standard tariff, the boiler is slightly cheaper.',
  'heat pump tariff</a>, yes, by around £1,000 at the midpoint and up to £4,500 if your radiators need little work. On a standard tariff, the boiler is about £4,000 cheaper over 15 years.'),
 ('On a heat pump tariff, yes. For a 3-bed semi, the 15-year total cost of a heat pump (after the £7,500 grant) is £14,430 to £19,470, compared to £16,905 to £19,525 for a new gas boiler. On a standard electricity tariff, the heat pump is slightly more expensive over 15 years.',
  'On a heat pump tariff, yes at the midpoint. For a 3-bed semi, the 15-year total cost of a heat pump (after the £7,500 grant) is £16,450 to £22,150, compared to £19,945 to £20,945 for a new gas boiler. On a standard electricity tariff, the heat pump is about £4,000 more expensive over 15 years.'),
]}
```

- [ ] **Step 2: Check, apply, verify**

Run: `python3 docs/superpowers/tools/apply_edits.py edits_vsboiler --check && python3 docs/superpowers/tools/apply_edits.py edits_vsboiler`
Expected: `checked 1 files, 16 edits` then `applied 1 files, 16 edits`.

Run: `/usr/bin/grep -c '24\.5p\|6\.76p\|~16p\|£15,015\|£239\|£14,430' guides/heat-pump-vs-new-boiler/index.html`
Expected: `0`

---

### Task 11: electric-boiler-vs-heat-pump

**Files:**
- Create: `docs/superpowers/tools/edits_eboiler.py`
- Modify: `guides/electric-boiler-vs-heat-pump/index.html`

- [ ] **Step 1: Write the edit list**

```python
EDITS = {'guides/electric-boiler-vs-heat-pump/index.html': [
 ('<tr><td>2-bed terrace</td><td>£1,960</td><td>£676</td><td>£441</td><td class="highlight-cell">£1,519</td></tr>',
  '<tr><td>2-bed terrace</td><td>£2,106</td><td>£726</td><td>£497</td><td class="highlight-cell">£1,609</td></tr>'),
 ('<tr><td>3-bed semi</td><td>£2,940</td><td>£1,014</td><td>£662</td><td class="highlight-cell">£2,278</td></tr>',
  '<tr><td>3-bed semi</td><td>£3,158</td><td>£1,089</td><td>£745</td><td class="highlight-cell">£2,413</td></tr>'),
 ('<tr><td>3-bed detached</td><td>£3,675</td><td>£1,267</td><td>£828</td><td class="highlight-cell">£2,847</td></tr>',
  '<tr><td>3-bed detached</td><td>£3,948</td><td>£1,361</td><td>£931</td><td class="highlight-cell">£3,017</td></tr>'),
 ('<tr><td>4-bed detached</td><td>£4,410</td><td>£1,521</td><td>£993</td><td class="highlight-cell">£3,417</td></tr>',
  '<tr><td>4-bed detached</td><td>£4,738</td><td>£1,634</td><td>£1,117</td><td class="highlight-cell">£3,621</td></tr>'),
 ('Electric boiler assumes 100% efficiency at 24.5p/kWh. Heat pump COP 2.9. Standard tariff 24.5p/kWh. HP tariff ~16p/kWh. Ofgem Q1 2026 rates.',
  'Electric boiler assumes 100% efficiency at 26.32p/kWh. Heat pump COP 2.9. Standard tariff 26.32p/kWh. HP tariff ~18p/kWh. Ofgem price cap, October to December 2026.'),
 ('that is the difference between £2,940 per year (electric boiler) and £662 per year (heat pump on a heat pump tariff).',
  'that is the difference between £3,158 per year (electric boiler) and £745 per year (heat pump on a heat pump tariff).'),
 ('Every unit of heat costs you the full electricity price: 24.5p at Ofgem Q1 2026 rates.',
  'Every unit of heat costs you the full electricity price: 26.32p at the Ofgem price cap for October to December 2026.'),
 ('the heat pump saves £1,284 to £2,889 per year compared to an electric boiler.',
  'the heat pump saves £1,380 to £3,104 per year compared to an electric boiler.'),
 ('with £2,278 per year in running cost savings (3-bed semi on HP tariff)',
  'with £2,413 per year in running cost savings (3-bed semi on HP tariff)'),
 ('Gas boiler homes save £239/yr by switching. Electric boiler homes save £2,278/yr.',
  'Gas boiler homes save £318/yr by switching. Electric boiler homes save £2,413/yr.'),
 ('may cost only £735 on an electric boiler. The saving from a heat pump (£490 on HP tariff) would be £245 per year, making the payback much longer.',
  'may cost only £790 on an electric boiler. A heat pump on a heat pump tariff would cost around £186, a saving of about £600 per year, so the payback stretches to 6 to 14 years rather than 1 to 3.'),
 ('A 3-bed semi saves £2,278/yr on a', 'A 3-bed semi saves £2,413/yr on a'),
 ('<p>£2,000 to £4,400 depending on property size. It is the most expensive common heating system because electricity costs 3.6 times more per kWh than gas.</p>',
  '<p>£2,100 to £4,700 depending on property size. It is the most expensive common heating system because electricity costs 3.3 times more per kWh than gas.</p>'),
 ('For a 3-bed semi, an electric boiler costs around £2,940 per year to run. A heat pump on a standard tariff costs £1,014. On a heat pump tariff, it costs £662.',
  'For a 3-bed semi, an electric boiler costs around £3,158 per year to run. A heat pump on a standard tariff costs £1,089. On a heat pump tariff, it costs £745.'),
 ('An electric boiler costs £2,000 to £3,500 per year to run for a typical UK home, depending on property size and insulation level. This is based on electricity at 24.5p/kWh and a boiler efficiency of 99 to 100%. Electric boilers are the most expensive common heating system to run because electricity costs 3.6 times more per kWh than gas.',
  'An electric boiler costs £2,100 to £4,700 per year to run for a typical UK home, depending on property size and insulation level. This is based on electricity at 26.32p/kWh and a boiler efficiency of 99 to 100%. Electric boilers are the most expensive common heating system to run because electricity costs 3.3 times more per kWh than gas.'),
 ('The running cost saving is £1,500 to £2,300 per year for a typical home.',
  'The running cost saving is £1,600 to £3,000 per year for a typical home.'),
 ('saves £1,500 to £2,300 per year, giving a payback', 'saves £1,600 to £3,000 per year, giving a payback'),
]}
```

- [ ] **Step 2: Check, apply, verify**

Run: `python3 docs/superpowers/tools/apply_edits.py edits_eboiler --check && python3 docs/superpowers/tools/apply_edits.py edits_eboiler`
Expected: `checked 1 files, 17 edits` then `applied 1 files, 17 edits`.

Run: `/usr/bin/grep -c '24\.5p\|~16p\|£2,278\|£2,940\|3\.6 times' guides/electric-boiler-vs-heat-pump/index.html`
Expected: `0`

---

### Task 12: storage-heaters-vs-heat-pump

**Files:**
- Create: `docs/superpowers/tools/edits_storage.py`
- Modify: `guides/storage-heaters-vs-heat-pump/index.html`

- [ ] **Step 1: Write the edit list**

```python
EDITS = {'guides/storage-heaters-vs-heat-pump/index.html': [
 ('<tr><td>2-bed flat</td><td>£1,700</td><td>£676</td><td>£441</td><td class="highlight-cell">£1,259</td></tr>',
  '<tr><td>2-bed flat</td><td>£1,700</td><td>£726</td><td>£497</td><td class="highlight-cell">£1,203</td></tr>'),
 ('<tr><td>2-bed terrace</td><td>£2,000</td><td>£676</td><td>£441</td><td class="highlight-cell">£1,559</td></tr>',
  '<tr><td>2-bed terrace</td><td>£2,000</td><td>£726</td><td>£497</td><td class="highlight-cell">£1,503</td></tr>'),
 ('<tr><td>3-bed semi</td><td>£2,600</td><td>£1,014</td><td>£662</td><td class="highlight-cell">£1,938</td></tr>',
  '<tr><td>3-bed semi</td><td>£2,600</td><td>£1,089</td><td>£745</td><td class="highlight-cell">£1,855</td></tr>'),
 ('<tr><td>4-bed detached</td><td>£3,800</td><td>£1,521</td><td>£993</td><td class="highlight-cell">£2,807</td></tr>',
  '<tr><td>4-bed detached</td><td>£3,800</td><td>£1,634</td><td>£1,117</td><td class="highlight-cell">£2,683</td></tr>'),
 ('Storage heaters on Economy 7 (night rate ~14p/kWh plus day boost at 24.5p/kWh). Heat pump COP 2.9. HP tariff ~16p/kWh. Well-insulated properties. Ofgem Q1 2026.',
  'Storage heaters on Economy 7 (night rate ~14p/kWh plus daytime boost at the standard rate). Storage heater figures are unchanged from March 2026 because Economy 7 rates are set by suppliers, not the price cap. Heat pump COP 2.9 at 26.32p/kWh standard or ~18p/kWh on a heat pump tariff, Ofgem price cap for October to December 2026. Well-insulated properties.'),
 ('Save £1,500 to £2,300/Year UK 2026', 'Save £1,200 to £2,700/Year UK 2026'),
 ('Replacing storage heaters with a heat pump saves £1,500 to £2,300 per year.', 'Replacing storage heaters with a heat pump saves £1,200 to £2,700 per year.', 2),
 ('saves <span class="key-number">£1,500 to £2,300 per year</span>', 'saves <span class="key-number">£1,200 to £2,700 per year</span>'),
 ('(24.5p/kWh or higher on Economy 7)', '(26.32p/kWh or higher on Economy 7)'),
 ('<p>At £1,938 annual saving (3-bed semi on HP tariff), payback is 3 to 7 years. After that, you save nearly £2,000 every year',
  '<p>At £1,855 annual saving (3-bed semi on HP tariff), payback is 3 to 8 years. After that, you save around £1,900 every year'),
 ('<p>£1,500 to £2,800 per year depending on property size and tariff. Payback is 3 to 7 years.',
  '<p>£1,200 to £2,700 per year depending on property size and tariff. Payback is 3 to 8 years.'),
]}
```

- [ ] **Step 2: Check, apply, verify**

Run: `python3 docs/superpowers/tools/apply_edits.py edits_storage --check && python3 docs/superpowers/tools/apply_edits.py edits_storage`
Expected: `checked 1 files, 11 edits` then `applied 1 files, 11 edits`.

Run: `/usr/bin/grep -c '24\.5p\|~16p\|£1,500 to £2,300\|£1,938' guides/storage-heaters-vs-heat-pump/index.html`
Expected: `0`. If `og:title` still carries the old range, add `('Save £1,500 to £2,300/Year', 'Save £1,200 to £2,700/Year')` and rerun.

---

### Task 13: heat-pump-cost-by-house-type

**Files:**
- Create: `docs/superpowers/tools/edits_bytype.py`
- Modify: `guides/heat-pump-cost-by-house-type/index.html`

- [ ] **Step 1: Write the edit list**

```python
EDITS = {'guides/heat-pump-cost-by-house-type/index.html': [
 ('<td>£440 to £580</td></tr>', '<td>£500 to £650</td></tr>'),
 ('<td>£520 to £680</td></tr>', '<td>£590 to £770</td></tr>'),
 ('<td>£620 to £820</td></tr>', '<td>£700 to £920</td></tr>'),
 ('<td>£660 to £900</td></tr>', '<td>£740 to £1,010</td></tr>'),
 ('<td>£760 to £1,040</td></tr>', '<td>£860 to £1,170</td></tr>'),
 ('<td>£900 to £1,260</td></tr>', '<td>£1,010 to £1,420</td></tr>'),
 ('<td>£1,100 to £1,520</td></tr>', '<td>£1,240 to £1,710</td></tr>'),
 ('Running costs assume COP 2.9, heat pump tariff at ~16p/kWh. Based on well-insulated properties.',
  'Running costs assume COP 2.9, heat pump tariff at ~18p/kWh (Ofgem price cap, October to December 2026). Based on well-insulated properties.'),
 ('<tr><td>2-bed terrace</td><td>£601</td><td>£676</td><td class="highlight-cell">£441</td></tr>',
  '<tr><td>2-bed terrace</td><td>£708</td><td>£726</td><td class="highlight-cell">£497</td></tr>'),
 ('<tr><td>3-bed semi</td><td>£901</td><td>£1,014</td><td class="highlight-cell">£662</td></tr>',
  '<tr><td>3-bed semi</td><td>£1,063</td><td>£1,089</td><td class="highlight-cell">£745</td></tr>'),
 ('<tr><td>3-bed detached</td><td>£1,127</td><td>£1,267</td><td class="highlight-cell">£828</td></tr>',
  '<tr><td>3-bed detached</td><td>£1,328</td><td>£1,361</td><td class="highlight-cell">£931</td></tr>'),
 ('<tr><td>4-bed detached</td><td>£1,352</td><td>£1,521</td><td class="highlight-cell">£993</td></tr>',
  '<tr><td>4-bed detached</td><td>£1,594</td><td>£1,634</td><td class="highlight-cell">£1,117</td></tr>'),
 ('Gas at 6.76p/kWh (90% efficiency). HP standard tariff at 24.5p/kWh (COP 2.9). HP tariff at ~16p/kWh effective. Ofgem Q1 2026 rates. Well-insulated properties.',
  'Gas at 7.97p/kWh (90% efficiency). HP standard tariff at 26.32p/kWh (COP 2.9). HP tariff at ~18p/kWh effective. Ofgem price cap, October to December 2026. Well-insulated properties.'),
 ('are typically £440 to £580 per year.', 'are typically £500 to £650 per year.'),
 ('<p>Annual running costs on a heat pump tariff run £660 to £900, compared to £900 to £1,130 for gas.',
  '<p>Annual running costs on a heat pump tariff run £740 to £1,010, compared to £1,060 to £1,330 for gas.'),
]}
```

- [ ] **Step 2: Check, apply, verify**

Run: `python3 docs/superpowers/tools/apply_edits.py edits_bytype --check && python3 docs/superpowers/tools/apply_edits.py edits_bytype`
Expected: `checked 1 files, 15 edits` then `applied 1 files, 15 edits`.

Run: `/usr/bin/grep -c '24\.5p\|6\.76p\|~16p\|£440 to £580\|£660 to £900' guides/heat-pump-cost-by-house-type/index.html`
Expected: `0`

---

### Task 14: heat-pump-old-house, boiler-upgrade-scheme-guide running costs, heat-pump-flat

**Files:**
- Create: `docs/superpowers/tools/edits_misc3.py`
- Modify: `guides/heat-pump-old-house/index.html`, `guides/boiler-upgrade-scheme-guide/index.html`, `guides/heat-pump-flat/index.html`

- [ ] **Step 1: Write the edit list**

```python
EDITS = {
 'guides/heat-pump-old-house/index.html': [
  ('<tr><td>Gas boiler (90% efficiency)</td><td>£1,127</td></tr>', '<tr><td>Gas boiler (90% efficiency)</td><td>£1,328</td></tr>'),
  ('<tr><td>Heat pump (COP 2.9, standard tariff)</td><td>£1,267</td></tr>', '<tr><td>Heat pump (COP 2.9, standard tariff)</td><td>£1,361</td></tr>'),
  ('<tr><td>Heat pump (COP 2.9, heat pump tariff)</td><td class="highlight-cell">£862 to £1,034</td></tr>',
   '<tr><td>Heat pump (COP 2.9, heat pump tariff)</td><td class="highlight-cell">£879 to £1,034</td></tr>'),
  ('<p>At the Q1 2026 Ofgem price cap, electricity costs 24.5p/kWh and gas costs 6.76p/kWh. A heat pump with a COP of 2.9 delivers heat at an effective cost of 8.4p/kWh, which is higher than gas at 6.76p per kWh. The gap narrows significantly if you switch to a heat pump tariff.</p>',
   '<p>At the Ofgem price cap for October to December 2026, electricity costs 26.32p/kWh and gas costs 7.97p/kWh. A heat pump with a COP of 2.9 delivers heat at an effective cost of 9.1p/kWh, against 8.9p per kWh for gas once boiler efficiency is included. The two are close to level, and a heat pump tariff puts the heat pump clearly ahead.</p>'),
  ('reduce your effective electricity cost to around 15 to 18p/kWh, bringing your heating cost per kWh closer to 5 to 6p.',
   'reduce your effective electricity cost to around 17 to 20p/kWh, bringing your heating cost per kWh down to 6 to 7p.'),
  ('Based on Ofgem Q1 2026 price cap rates. Standing charges excluded. Heat pump tariff assumes 15 to 18p/kWh effective rate.',
   'Based on the Ofgem price cap for October to December 2026. Standing charges excluded. Heat pump tariff assumes 17 to 20p/kWh effective rate.'),
 ],
 'guides/boiler-upgrade-scheme-guide/index.html': [
  ('<tr><td>Gas boiler (90% efficiency)</td><td>£1,127</td></tr>', '<tr><td>Gas boiler (90% efficiency)</td><td>£1,328</td></tr>'),
  ('<tr><td>Heat pump (standard tariff, 24.5p/kWh)</td><td>£1,267</td></tr>', '<tr><td>Heat pump (standard tariff, 26.32p/kWh)</td><td>£1,361</td></tr>'),
  ('<tr><td>Heat pump (heat pump tariff, ~16p/kWh)</td><td class="highlight-cell">£828</td></tr>',
   '<tr><td>Heat pump (heat pump tariff, ~18p/kWh)</td><td class="highlight-cell">£931</td></tr>'),
  ('<p>At the Q1 2026 Ofgem price cap, a heat pump with a COP of 2.9 on a standard tariff costs slightly more to run than a gas boiler. On a dedicated heat pump tariff, it costs less.',
   '<p>At the Ofgem price cap for October to December 2026, a heat pump with a COP of 2.9 on a standard tariff costs about the same to run as a gas boiler. On a dedicated heat pump tariff, it costs less.'),
  ('Based on Ofgem Q1 2026 rates. Heat pump tariff assumes Octopus Cosy or equivalent.',
   'Based on the Ofgem price cap for October to December 2026. Heat pump tariff assumes Octopus Cosy or equivalent at ~18p/kWh effective.'),
 ],
 'guides/heat-pump-flat/index.html': [
  ('<td>£400 to £500</td></tr>', '<td>£430 to £540</td></tr>'),
  ('<td>£450 to £600</td></tr>', '<td>£480 to £640</td></tr>'),
  ('<td>£500 to £700</td></tr>', '<td>£540 to £750</td></tr>'),
  ('Q1 2026 rates (24.5p/kWh), assuming good insulation and COP 3.2.',
   'price cap rates for October to December 2026 (26.32p/kWh), assuming good insulation and COP 3.2.'),
  ('Running costs £400 to £600 per year.', 'Running costs £430 to £640 per year.'),
  ('Running costs are £400 to £600 per year.', 'Running costs are £430 to £640 per year.'),
 ],
}
```

- [ ] **Step 2: Check, apply, verify**

Run: `python3 docs/superpowers/tools/apply_edits.py edits_misc3 --check && python3 docs/superpowers/tools/apply_edits.py edits_misc3`
Expected: `checked 3 files, 17 edits` then `applied 3 files, 17 edits`.

Run: `/usr/bin/grep -c '24\.5p\|6\.76p\|~16p\|15 to 18p\|£1,267' guides/heat-pump-old-house/index.html guides/boiler-upgrade-scheme-guide/index.html guides/heat-pump-flat/index.html`
Expected: `0` for each file.

---

### Task 15: best-heat-pump-tariffs (baseline row, savings column, OVO closure)

**Files:**
- Create: `docs/superpowers/tools/edits_tariffs.py`
- Modify: `guides/best-heat-pump-tariffs/index.html`

- [ ] **Step 1: Write the edit list**

```python
EDITS = {'guides/best-heat-pump-tariffs/index.html': [
 ('<td>24.5p/kWh flat</td>', '<td>26.32p/kWh flat</td>'),
 ('<tr><td>OVO Heat Pump Plus</td><td>11 to 14p</td>', '<tr><td>OVO Heat Pump Plus (closed to new customers, February 2026)</td><td>11 to 14p</td>'),
 ('<p>If you prefer simplicity, <strong>OVO Heat Pump Plus</strong> provides a straightforward overnight rate without half-hourly price changes. It is less aggressive on savings than Cosy or Agile but requires no smart scheduling.</p>',
  '<p><strong>OVO Heat Pump Plus</strong> offered a straightforward overnight rate without half-hourly price changes, but it closed to new customers in February 2026. Existing customers keep their rate. If you want simplicity without smart scheduling, Economy 7 or a fixed-window tariff such as Cosy is now the nearest equivalent.</p>'),
 ('<tr><td>Standard variable (24.5p flat)</td><td>£1,014</td><td>Baseline</td></tr>', '<tr><td>Standard variable (26.32p flat)</td><td>£1,089</td><td>Baseline</td></tr>'),
 ('<td class="highlight-cell">£352 (35%)</td>', '<td class="highlight-cell">£427 (39%)</td>'),
 ('<td class="highlight-cell">£434 (43%)</td>', '<td class="highlight-cell">£509 (47%)</td>'),
 ('<tr><td>OVO Heat Pump Plus</td><td>£745</td><td>£269 (27%)</td></tr>', '<tr><td>OVO Heat Pump Plus (closed to new customers)</td><td>£745</td><td>£344 (32%)</td></tr>'),
 ('<tr><td>Economy 7</td><td>£828</td><td>£186 (18%)</td></tr>', '<tr><td>Economy 7</td><td>£828</td><td>£261 (24%)</td></tr>'),
 ('<tr><td>Octopus Go</td><td>£690</td><td>£324 (32%)</td></tr>', '<tr><td>Octopus Go</td><td>£690</td><td>£399 (37%)</td></tr>'),
 ('The difference between the worst option (standard variable at £1,014) and the best (Agile at £580) is £434 per year.',
  'The difference between the worst option (standard variable at £1,089) and the best (Agile at £580) is £509 per year.'),
 ('that is nearly £9,000.', 'that is more than £10,000.'),
 ('verified March 2026. Standard variable rates from', 'verified March 2026 and rechecked for availability in September 2026. Standard variable rates from'),
 ('annual heating costs of £662 to £828 on a heat pump tariff versus £1,267 on standard rates.',
  'annual heating costs of £745 to £931 on a heat pump tariff versus £1,089 to £1,361 on standard rates.'),
]}
```

- [ ] **Step 2: Check, apply, verify**

Run: `python3 docs/superpowers/tools/apply_edits.py edits_tariffs --check && python3 docs/superpowers/tools/apply_edits.py edits_tariffs`
Expected: `checked 1 files, 13 edits` then `applied 1 files, 13 edits`.

Run: `/usr/bin/grep -c '24\.5p\|£1,014\|£434 per year' guides/best-heat-pump-tariffs/index.html`
Expected: `0`

---

### Task 16: average-energy-bills-uk

**Files:**
- Create: `docs/superpowers/tools/edits_avgbills.py`
- Modify: `guides/average-energy-bills-uk/index.html`

Basis: table 1 cells are back-solved from the old figures at the old rates and recomputed at the new ones (rounded to £10 except the 3-bed average row); tables 2 and 3 are recomputed from the kWh shown; the three table 2 rows that never reproduced (11,500, 18,000, 24,000) are corrected from their stated kWh, as recorded by `verify_model.py`.

- [ ] **Step 1: Write the edit list**

```python
EDITS = {'guides/average-energy-bills-uk/index.html': [
 ('Using Ofgem Q1 2026 price cap data.', 'Using Ofgem October to December 2026 price cap data.'),
 ('Ofgem</a> Q1 2026 price cap rates. Consumption data', 'Ofgem</a> price cap rates for October to December 2026. Consumption data'),
 ('<p class="lead">The average UK household pays approximately <span class="key-number">£1,738 per year</span> for gas and electricity combined at Q1 2026 rates. But averages hide huge variation. A well-insulated 2 bed flat might pay £1,200 while a poorly insulated 5 bed detached house pays over £2,800.',
  '<p class="lead">The average UK household pays approximately <span class="key-number">£1,723 per year</span> for gas and electricity combined at the Ofgem price cap for October to December 2026. But averages hide huge variation. A well-insulated 2 bed flat might pay £1,420 while a poorly insulated 5 bed detached house pays over £3,200.'),
 ('<h2>Current energy prices (Q1 2026)</h2>', '<h2>Current energy prices (October to December 2026)</h2>'),
 ('rates for Q1 2026 (January to March). The price cap changes quarterly.</p>',
  'rates for 1 October to 31 December 2026, announced on 26 August 2026. The price cap changes quarterly.</p>'),
 ('<p>Electricity: <span class="key-number">24.5p per kWh</span> with a daily standing charge of 61.64p. Gas: <span class="key-number">6.76p per kWh</span> with a daily standing charge of 31.65p.</p>',
  '<p>Electricity: <span class="key-number">26.32p per kWh</span> with a daily standing charge of 54.83p. Gas: <span class="key-number">7.97p per kWh</span> with a daily standing charge of 29.68p. Ofgem also lowered its typical consumption values on 1 July 2026 to 2,500 kWh of electricity and 9,500 kWh of gas a year (from 2,700 and 11,500), which is why the headline £1,723 is not directly comparable with earlier typical bills.</p>'),
 ('<tr><td>1 bed flat</td><td>£500</td><td>£700</td><td class="highlight-cell">£1,200</td><td>£100</td></tr>',
  '<tr><td>1 bed flat</td><td>£560</td><td>£710</td><td class="highlight-cell">£1,270</td><td>£106</td></tr>'),
 ('<tr><td>2 bed flat</td><td>£600</td><td>£730</td><td class="highlight-cell">£1,330</td><td>£111</td></tr>',
  '<tr><td>2 bed flat</td><td>£680</td><td>£740</td><td class="highlight-cell">£1,420</td><td>£118</td></tr>'),
 ('<tr><td>2 bed terrace</td><td>£700</td><td>£760</td><td class="highlight-cell">£1,460</td><td>£122</td></tr>',
  '<tr><td>2 bed terrace</td><td>£800</td><td>£770</td><td class="highlight-cell">£1,570</td><td>£131</td></tr>'),
 ('<tr><td>3 bed semi (average insulation)</td><td>£905</td><td>£833</td><td class="highlight-cell">£1,738</td><td>£145</td></tr>',
  '<tr><td>3 bed semi (average insulation)</td><td>£1,025</td><td>£853</td><td class="highlight-cell">£1,878</td><td>£157</td></tr>'),
 ('<tr><td>3 bed semi (good insulation)</td><td>£720</td><td>£790</td><td class="highlight-cell">£1,510</td><td>£126</td></tr>',
  '<tr><td>3 bed semi (good insulation)</td><td>£820</td><td>£810</td><td class="highlight-cell">£1,630</td><td>£136</td></tr>'),
 ('<tr><td>3 bed detached</td><td>£1,100</td><td>£870</td><td class="highlight-cell">£1,970</td><td>£164</td></tr>',
  '<tr><td>3 bed detached</td><td>£1,270</td><td>£890</td><td class="highlight-cell">£2,160</td><td>£180</td></tr>'),
 ('<tr><td>4 bed detached</td><td>£1,400</td><td>£920</td><td class="highlight-cell">£2,320</td><td>£193</td></tr>',
  '<tr><td>4 bed detached</td><td>£1,620</td><td>£950</td><td class="highlight-cell">£2,570</td><td>£214</td></tr>'),
 ('<tr><td>5 bed detached</td><td>£1,900</td><td>£980</td><td class="highlight-cell">£2,880</td><td>£240</td></tr>',
  '<tr><td>5 bed detached</td><td>£2,210</td><td>£1,010</td><td class="highlight-cell">£3,220</td><td>£268</td></tr>'),
 ('Based on Ofgem Q1 2026 price cap rates. Gas bills calculated from', 'Based on the Ofgem price cap for October to December 2026. Gas bills calculated from'),
 ('heat demand data by property type at 92% boiler efficiency. Electricity bills', 'consumption data by property type. Electricity bills'),
 ('That is the difference between a £720 and a £1,100 gas bill.', 'That is the difference between an £820 and a £1,270 gas bill.'),
 ('<td>5,500</td><td>Average</td><td>£487</td></tr>', '<td>5,500</td><td>Average</td><td>£547</td></tr>'),
 ('<td>8,500</td><td>Average</td><td>£690</td></tr>', '<td>8,500</td><td>Average</td><td>£786</td></tr>'),
 ('<td>11,500</td><td>Average</td><td>£905</td></tr>', '<td>11,500</td><td>Average</td><td>£1,025</td></tr>'),
 ('<td>8,500</td><td>Good</td><td>£690</td></tr>', '<td>8,500</td><td>Good</td><td>£786</td></tr>'),
 ('<td>14,000</td><td>Average</td><td>£1,062</td></tr>', '<td>14,000</td><td>Average</td><td>£1,224</td></tr>'),
 ('<td>18,000</td><td>Average</td><td>£1,347</td></tr>', '<td>18,000</td><td>Average</td><td>£1,543</td></tr>'),
 ('<td>24,000</td><td>Average</td><td>£1,856</td></tr>', '<td>24,000</td><td>Average</td><td>£2,021</td></tr>'),
 ('<p class="data-table note">Gas costs = (consumption / 0.92 boiler efficiency) x 6.76p + standing charge.',
  '<p class="data-table note">Gas costs = consumption x 7.97p + standing charge (29.68p/day = £108/yr).'),
 ('<td>1,800</td><td>£666</td></tr>', '<td>1,800</td><td>£674</td></tr>'),
 ('<td>2,300</td><td>£789</td></tr>', '<td>2,300</td><td>£805</td></tr>'),
 ('<td>2,700</td><td>£887</td></tr>', '<td>2,700</td><td>£911</td></tr>'),
 ('<td>3,500</td><td>£1,083</td></tr>', '<td>3,500</td><td>£1,121</td></tr>'),
 ('<td>+2,500</td><td>+£613</td></tr>', '<td>+2,500</td><td>+£658</td></tr>'),
 ('<td>+2,500 to 4,500</td><td>+£613 to £1,103</td></tr>', '<td>+2,500 to 4,500</td><td>+£658 to £1,184</td></tr>'),
 ('Electricity costs = consumption x 24.5p + standing charge (61.64p/day = £225/yr).',
  'Electricity costs = consumption x 26.32p + standing charge (54.83p/day = £200/yr).'),
 ('can reduce electricity bills by £400 to £700 per year.', 'can reduce electricity bills by £450 to £750 per year.'),
 ('<p>Approximately £1,738 per year for gas and electricity combined, based on',
  '<p>Approximately £1,723 per year for gas and electricity combined at the October to December 2026 cap, based on'),
 ('typical consumption values. Actual bills range from £1,200 for a 1 bed flat to over £2,800 for a 5 bed detached house.</p>',
  'typical consumption values of 2,500 kWh of electricity and 9,500 kWh of gas. Actual bills range from £1,270 for a 1 bed flat to over £3,200 for a 5 bed detached house.</p>'),
 ('<p>Approximately £905 per year based on typical consumption of 11,500 kWh. Gas costs 6.76p per kWh at the Q1 2026 price cap, plus a 31.65p daily standing charge.</p>',
  '<p>Approximately £865 per year based on Ofgem typical consumption of 9,500 kWh. Gas costs 7.97p per kWh at the October to December 2026 price cap, plus a 29.68p daily standing charge.</p>'),
 ('<p>Approximately £833 per year based on typical consumption of 2,700 kWh. Electricity costs 24.5p per kWh at the Q1 2026 price cap, plus a 61.64p daily standing charge.',
  '<p>Approximately £858 per year based on Ofgem typical consumption of 2,500 kWh. Electricity costs 26.32p per kWh at the October to December 2026 price cap, plus a 54.83p daily standing charge.'),
 ('<p>A 3 bed semi costs approximately £1,600 to £2,000 per year for gas and electricity.',
  '<p>A 3 bed semi costs approximately £1,600 to £2,100 per year for gas and electricity.'),
 ("The average UK household energy bill is approximately £1,738 per year as of Q1 2026, based on Ofgem's typical domestic consumption values of 11,500 kWh of gas and 2,700 kWh of electricity. Actual bills vary significantly by property type, from around £1,200 for a 1 bed flat to over £2,800 for a 5 bed detached house.",
  "The average UK household energy bill is approximately £1,723 per year at the October to December 2026 price cap, based on Ofgem's typical domestic consumption values of 9,500 kWh of gas and 2,500 kWh of electricity. Actual bills vary significantly by property type, from around £1,270 for a 1 bed flat to over £3,200 for a 5 bed detached house."),
 ("The average gas bill is approximately £905 per year based on Ofgem's typical consumption of 11,500 kWh at the Q1 2026 price cap rate of 6.76p per kWh plus a daily standing charge of 31.65p. Actual gas bills range from £500 for a small flat to £1,900 for a large detached house.",
  "The average gas bill is approximately £865 per year based on Ofgem's typical consumption of 9,500 kWh at the October to December 2026 price cap rate of 7.97p per kWh plus a daily standing charge of 29.68p. Actual gas bills range from £560 for a small flat to £2,210 for a large detached house."),
 ("The average electricity bill is approximately £833 per year based on Ofgem's typical consumption of 2,700 kWh at the Q1 2026 price cap rate of 24.5p per kWh plus a daily standing charge of 61.64p.",
  "The average electricity bill is approximately £858 per year based on Ofgem's typical consumption of 2,500 kWh at the October to December 2026 price cap rate of 26.32p per kWh plus a daily standing charge of 54.83p."),
 ('A 3 bed semi-detached house costs approximately £1,600 to £2,000 per year for gas and electricity combined. A well-insulated 3 bed semi costs closer to £1,600, while a poorly insulated one can reach £2,200 or more. These figures are at Ofgem Q1 2026 price cap rates.',
  'A 3 bed semi-detached house costs approximately £1,600 to £2,100 per year for gas and electricity combined. A well-insulated 3 bed semi costs closer to £1,630, while a poorly insulated one can reach £2,400 or more. These figures are at the Ofgem price cap for October to December 2026.'),
]}
```

- [ ] **Step 2: Check, apply, verify**

Run: `python3 docs/superpowers/tools/apply_edits.py edits_avgbills --check && python3 docs/superpowers/tools/apply_edits.py edits_avgbills`
Expected: `checked 1 files, 42 edits` then `applied 1 files, 42 edits`.

Run: `/usr/bin/grep -c '24\.5p\|6\.76p\|61\.64p\|31\.65p\|£1,738\|£905\|£833' guides/average-energy-bills-uk/index.html`
Expected: `0`

---

### Task 17: energy-bills-by-household-size

**Files:**
- Create: `docs/superpowers/tools/edits_household.py`
- Modify: `guides/energy-bills-by-household-size/index.html`

Basis: every bill cell is back-solved from the old figure at the old rates (kWh = (bill minus annual standing charge) / unit rate) and recomputed at the new rates, rounded to £10; totals and per-person figures follow.

- [ ] **Step 1: Write the edit list**

```python
EDITS = {'guides/energy-bills-by-household-size/index.html': [
 ('A 1-person home pays £1,170/yr. A 4-person home pays £1,890/yr.', 'A 1-person home pays £1,250/yr. A 4-person home pays £2,090/yr.'),
 ('pays around <span class="key-number">£1,170 per year</span> for gas and electricity. A 4-person household pays around £1,890.',
  'pays around <span class="key-number">£1,250 per year</span> for gas and electricity. A 4-person household pays around £2,090.'),
 ('<tr><td>1 person</td><td>£620</td><td>£550</td><td>£1,170</td><td class="highlight-cell">£1,170</td></tr>',
  '<tr><td>1 person</td><td>£700</td><td>£550</td><td>£1,250</td><td class="highlight-cell">£1,250</td></tr>'),
 ('<tr><td>2 people</td><td>£810</td><td>£610</td><td>£1,420</td><td>£710</td></tr>',
  '<tr><td>2 people</td><td>£930</td><td>£610</td><td>£1,540</td><td>£770</td></tr>'),
 ('<tr><td>3 people</td><td>£980</td><td>£660</td><td>£1,640</td><td>£547</td></tr>',
  '<tr><td>3 people</td><td>£1,130</td><td>£670</td><td>£1,800</td><td>£600</td></tr>'),
 ('<tr><td>4 people</td><td>£1,200</td><td>£690</td><td class="highlight-cell">£1,890</td><td>£473</td></tr>',
  '<tr><td>4 people</td><td>£1,390</td><td>£700</td><td class="highlight-cell">£2,090</td><td>£523</td></tr>'),
 ('<tr><td>5+ people</td><td>£1,400</td><td>£750</td><td>£2,150</td><td>£430 or less</td></tr>',
  '<tr><td>5+ people</td><td>£1,620</td><td>£760</td><td>£2,380</td><td>£476 or less</td></tr>'),
 ('Based on Ofgem Q1 2026 price cap rates: gas 6.76p/kWh, electricity 24.5p/kWh.',
  'Based on the Ofgem price cap for October to December 2026: gas 7.97p/kWh plus 29.68p/day, electricity 26.32p/kWh plus 54.83p/day.'),
 ('A single person pays £1,170 per person per year. In a 4-person household, the per-person cost drops to £473',
  'A single person pays £1,250 per person per year. In a 4-person household, the per-person cost drops to £523'),
 ('<tr><td>1-bed flat</td><td>£400</td><td>£500</td><td>£900</td></tr>', '<tr><td>1-bed flat</td><td>£440</td><td>£500</td><td>£940</td></tr>'),
 ('<tr><td>2-bed terrace</td><td>£700</td><td>£580</td><td>£1,280</td></tr>', '<tr><td>2-bed terrace</td><td>£800</td><td>£580</td><td>£1,380</td></tr>'),
 ('<tr><td>3-bed semi (average)</td><td>£1,050</td><td>£640</td><td class="highlight-cell">£1,690</td></tr>',
  '<tr><td>3-bed semi (average)</td><td>£1,210</td><td>£650</td><td class="highlight-cell">£1,860</td></tr>'),
 ('<tr><td>3-bed detached</td><td>£1,300</td><td>£680</td><td>£1,980</td></tr>', '<tr><td>3-bed detached</td><td>£1,500</td><td>£690</td><td>£2,190</td></tr>'),
 ('<tr><td>4-bed detached</td><td>£1,560</td><td>£740</td><td>£2,300</td></tr>', '<tr><td>4-bed detached</td><td>£1,810</td><td>£750</td><td>£2,560</td></tr>'),
 ('<tr><td>5-bed detached</td><td>£1,850</td><td>£800</td><td>£2,650</td></tr>', '<tr><td>5-bed detached</td><td>£2,150</td><td>£820</td><td>£2,970</td></tr>'),
 ('at 90% efficiency. Ofgem Q1 2026 rates. Well-insulated properties.', 'at 90% efficiency. Ofgem price cap, October to December 2026. Well-insulated properties.'),
 ('household figure of £1,738 per year is based on a medium-consumption home.',
  'household figure of £1,723 per year is based on a medium-consumption home using 2,500 kWh of electricity and 9,500 kWh of gas.'),
 ('<td>£240 to £600 (if you have a HP)</td>', '<td>£230 to £520 (if you have a HP)</td>'),
 ('reduce a typical 3-bed semi bill from £1,690 to £1,000 to £1,200.', 'reduce a typical 3-bed semi bill from £1,860 to £1,100 to £1,300.'),
 ('saves £239/yr for a 3-bed semi. If you are on oil, LPG, or electric heating, the savings are £500 to £2,800/yr.',
  'saves £318/yr for a 3-bed semi. If you are on oil, LPG, or electric heating, the savings are £650 to £3,600/yr.'),
 ('<p>Approximately £1,890 per year (gas and electricity combined) at Ofgem Q1 2026 rates.',
  '<p>Approximately £2,090 per year (gas and electricity combined) at the Ofgem price cap for October to December 2026.'),
 ('<p>Approximately £1,170 per year. Single-person homes', '<p>Approximately £1,250 per year. Single-person homes'),
 ('<p>Roughly £150 to £250 per year per additional person', '<p>Roughly £250 to £300 per year per additional person'),
 ('pays approximately 1,890 pounds per year for gas and electricity combined in 2026, based on the Ofgem price cap. This breaks down to roughly 1,200 for gas and 690 for electricity.',
  'pays approximately 2,090 pounds per year for gas and electricity combined at the October to December 2026 Ofgem price cap. This breaks down to roughly 1,390 for gas and 700 for electricity.'),
 ('A 1-person household pays approximately 1,170 pounds per year', 'A 1-person household pays approximately 1,250 pounds per year'),
 ('adds roughly 150 to 250 pounds per year', 'adds roughly 250 to 300 pounds per year'),
]}
```

- [ ] **Step 2: Check, apply, verify**

Run: `python3 docs/superpowers/tools/apply_edits.py edits_household --check && python3 docs/superpowers/tools/apply_edits.py edits_household`
Expected: `checked 1 files, 26 edits` then `applied 1 files, 26 edits`.

Run: `/usr/bin/grep -c '24\.5p\|6\.76p\|£1,170\|£1,890\|1,170 pounds\|£1,738' guides/energy-bills-by-household-size/index.html`
Expected: `0`

---

### Task 18: The three solar pages

**Files:**
- Create: `docs/superpowers/tools/edits_solar.py`
- Modify: `guides/are-solar-panels-worth-it-uk/index.html`, `guides/solar-panel-payback-uk/index.html`, `guides/solar-battery-storage-uk/index.html`

Basis: bill saving = generation × self-use share × 26.32p (export income unchanged at 8p); payback = cost / annual benefit; battery-page savings scale by 26.32 / 24.5 and round to £10; 25-year totals use a 0.94 average degradation factor.

- [ ] **Step 1: Write the edit list**

```python
EDITS = {
 'guides/are-solar-panels-worth-it-uk/index.html': [
  ('Updated March 2026. Calculations use Ofgem Q1 2026 electricity rate of 24.5p/kWh.',
   'Updated September 2026. Calculations use the Ofgem October to December 2026 electricity rate of 26.32p/kWh.'),
  ('saves £400 to £700 per year, and pays for itself in 8 to 12 years.', 'saves £450 to £750 per year, and pays for itself in 8 to 11 years.', 2),
  ('A 4 kW system saves £400 to £700 per year and pays for itself in 8 to 12 years.', 'A 4 kW system saves £450 to £750 per year and pays for itself in 8 to 11 years.'),
  ('<td>£314</td><td>£125</td><td class="highlight-cell">£439</td>', '<td>£338</td><td>£125</td><td class="highlight-cell">£463</td>'),
  ('<td>£419</td><td>£167</td><td class="highlight-cell">£586</td>', '<td>£450</td><td>£167</td><td class="highlight-cell">£617</td>'),
  ('<td>£745</td><td>£61</td><td class="highlight-cell">£806</td>', '<td>£800</td><td>£61</td><td class="highlight-cell">£861</td>'),
  ('<td>£366</td><td>£146</td><td class="highlight-cell">£512</td>', '<td>£393</td><td>£146</td><td class="highlight-cell">£539</td>'),
  ('<td>£628</td><td>£250</td><td class="highlight-cell">£878</td>', '<td>£675</td><td>£250</td><td class="highlight-cell">£925</td>'),
  ('Electricity at 24.5p/kWh (Ofgem Q1 2026).', 'Electricity at 26.32p/kWh (Ofgem, October to December 2026).'),
  ('you use 80% yourself at the full 24.5p/kWh rate.', 'you use 80% yourself at the full 26.32p/kWh rate.'),
  ('net profit of approximately <span class="key-number">£7,000 to £9,000</span>', 'net profit of approximately <span class="key-number">£7,500 to £9,500</span>'),
  ('you buy grid electricity at 24.5p/kWh in the evening.', 'you buy grid electricity at 26.32p/kWh in the evening.'),
  ('Electricity rates from Ofgem Q1 2026.', 'Electricity rates from Ofgem, October to December 2026.', 2),
 ],
 'guides/solar-panel-payback-uk/index.html': [
  ('Electricity at 24.5p/kWh (', 'Electricity at 26.32p/kWh ('),
  ('Ofgem</a> Q1 2026).</p>', 'Ofgem</a>, October to December 2026).</p>'),
  ('<td>£6,000</td><td>£586</td><td class="highlight-cell">10.2 years</td>', '<td>£6,000</td><td>£617</td><td class="highlight-cell">9.7 years</td>'),
  ('<td>£9,750</td><td>£806</td><td>12.1 years</td>', '<td>£9,750</td><td>£861</td><td>11.3 years</td>'),
  ('<td>£6,000</td><td>£557</td><td>10.8 years</td>', '<td>£6,000</td><td>£587</td><td>10.2 years</td>'),
  ('<td>£6,000</td><td>£512</td><td>11.7 years</td>', '<td>£6,000</td><td>£539</td><td>11.1 years</td>'),
  ('<td>£6,000</td><td>£480</td><td>12.5 years</td>', '<td>£6,000</td><td>£505</td><td>11.9 years</td>'),
  ('<td>£4,750</td><td>£439</td><td class="highlight-cell">10.8 years</td>', '<td>£4,750</td><td>£463</td><td class="highlight-cell">10.3 years</td>'),
  ('<td>£8,000</td><td>£878</td><td class="highlight-cell">9.1 years</td>', '<td>£8,000</td><td>£925</td><td class="highlight-cell">8.6 years</td>'),
  ('(45% self-use at 24.5p/kWh)', '(45% self-use at 26.32p/kWh)'),
  ('(valued at 24.5p/kWh)', '(valued at 26.32p/kWh)'),
  ('delivers approximately <span class="key-number">£8,500 net profit</span> (total benefits of £14,500 minus £6,000 cost). With a battery, net profit is approximately £8,000 (total benefits of £17,750 minus £9,750 cost).',
   'delivers approximately <span class="key-number">£8,500 net profit</span> (total benefits of £14,500 minus £6,000 cost, allowing for panel degradation). With a battery, net profit is approximately £10,500 (total benefits of £20,200 minus £9,750 cost).'),
  ('at the full 24.5p rate.', 'at the full 26.32p rate.'),
  ('adds roughly £35 per year to your savings from a 4 kW system.', 'adds roughly £17 per year to your savings from a 4 kW system without a battery, or £30 with one.'),
  ('instead of using it at 24.5p.', 'instead of using it at 26.32p.'),
  ('Cost £5,000 to £7,000, annual benefit £500 to £700. Net profit over 25 years approximately £7,000 to £10,000.</p>',
   'Cost £5,000 to £7,000, annual benefit £550 to £750. Net profit over 25 years approximately £7,500 to £10,000.</p>'),
  ('saves £500 to £700 per year (bill savings plus Smart Export Guarantee income). Payback is 8 to 12 years without a battery. Over 25 years, net profit is approximately £7,000 to £10,000.',
   'saves £550 to £750 per year (bill savings plus Smart Export Guarantee income). Payback is 8 to 11 years without a battery. Over 25 years, net profit is approximately £7,500 to £10,000.'),
  ('Ofgem</a> Q1 2026. SEG rates from', 'Ofgem</a>, October to December 2026. SEG rates from'),
 ],
 'guides/solar-battery-storage-uk/index.html': [
  ('<td>£150 to £250</td></tr>', '<td>£160 to £270</td></tr>'),
  ('<td class="highlight-cell">£200 to £350</td></tr>', '<td class="highlight-cell">£210 to £380</td></tr>'),
  ('<td>£300 to £450</td></tr>', '<td>£320 to £480</td></tr>'),
  ('<td>£350 to £550</td></tr>', '<td>£380 to £590</td></tr>'),
  ('standard electricity at 24.5p/kWh.', 'standard electricity at 26.32p/kWh.'),
  ('saves £200 to £550 per year depending on your usage pattern and tariff.', 'saves £210 to £590 per year depending on your usage pattern and tariff.'),
  ('buy from the grid at 24.5p/kWh.', 'buy from the grid at 26.32p/kWh.'),
  ('that is roughly 10 to 20p per kWh stored. A 5 kWh battery cycling once per day saves 50p to £1 per day, or £180 to £365 per year.',
   'that is roughly 11 to 22p per kWh stored. A 5 kWh battery cycling once per day saves 55p to £1.10 per day, or £200 to £400 per year.'),
  ('<td>£400 to £550</td>', '<td>£430 to £590</td>'),
  ('<td>£600 to £900</td>', '<td>£640 to £970</td>'),
  ('<td class="highlight-cell">£700 to £1,050</td>', '<td class="highlight-cell">£750 to £1,130</td>'),
  ('<p>£200 to £350 from shifted self-consumption. £400 to £550 with a', '<p>£210 to £380 from shifted self-consumption. £430 to £600 with a'),
  ('saves approximately £200 to £350 per year by shifting', 'saves approximately £210 to £380 per year by shifting'),
  ('savings can reach £400 to £550 per year', 'savings can reach £430 to £600 per year'),
 ],
}
```

- [ ] **Step 2: Check, apply, verify**

Run: `python3 docs/superpowers/tools/apply_edits.py edits_solar --check && python3 docs/superpowers/tools/apply_edits.py edits_solar`
Expected: `checked 3 files, 45 edits` then `applied 3 files, 45 edits`.

Run: `/usr/bin/grep -c '24\.5p\|Q1 2026' guides/are-solar-panels-worth-it-uk/index.html guides/solar-panel-payback-uk/index.html guides/solar-battery-storage-uk/index.html`
Expected: `0` for the first two files; the battery page still shows `1` (its sources line, swept in Task 20).

---

### Task 19: Annotate the EST-sourced pages

**Files:**
- Create: `docs/superpowers/tools/edits_annotate.py`
- Modify: 13 guides listed in the module (the Home Upgrade Grant page is Task 19b)

- [ ] **Step 1: Write the edit list**

```python
GAS = ('Savings were calculated at the January to March 2026 gas price of 6.76p per kWh. '
       'From 1 October 2026 the Ofgem cap puts gas at 7.97p per kWh, so expect savings around 18% higher than shown.')
EDITS = {
 'guides/diy-loft-insulation/index.html': [
  ('Savings based on gas heating at Ofgem Q1 2026 rates. DIY payback assumes', GAS + ' DIY payback assumes')],
 'guides/draught-proofing-guide/index.html': [
  ('Gas heating at Ofgem Q1 2026 rates. Savings assume', GAS + ' Savings assume')],
 'guides/eco4-scheme-explained/index.html': [
  ('Based on gas heating at Ofgem Q1 2026 rates. Savings for a 3-bed semi.', GAS + ' Savings for a 3-bed semi.')],
 'guides/free-loft-insulation-uk/index.html': [
  ('Upgrading from 0 to 270mm mineral wool. Gas at Ofgem Q1 2026 rates.</p>', 'Upgrading from 0 to 270mm mineral wool with gas heating. ' + GAS + '</p>')],
 'guides/great-british-insulation-scheme/index.html': [
  ('Gas heating at Ofgem Q1 2026 rates.</p>', GAS + '</p>')],
 'guides/how-epc-points-are-calculated/index.html': [
  ('Energy costs are illustrative based on a 3-bed semi at Ofgem Q1 2026 rates.',
   'Energy costs are illustrative for a 3-bed semi at January to March 2026 prices. The Ofgem cap from 1 October 2026 raises gas by 18% and electricity by 7%, so read them as relative, not exact.')],
 'guides/how-long-loft-insulation-lasts/index.html': [
  ('based on upgrading from no insulation to 270mm mineral wool. Gas heating at Ofgem Q1 2026 rates.</p>',
   'based on upgrading from no insulation to 270mm mineral wool with gas heating. ' + GAS + '</p>')],
 'guides/is-cavity-wall-insulation-worth-it/index.html': [
  ('Gas heating at Ofgem Q1 2026 rates (6.76p/kWh). Costs include', GAS + ' Costs include')],
 'guides/is-loft-insulation-worth-it/index.html': [
  ('Savings based on upgrading from 0 to 270mm mineral wool, gas heating at Ofgem Q1 2026 rates (6.76p/kWh). DIY costs',
   'Savings based on upgrading from 0 to 270mm mineral wool with gas heating. ' + GAS + ' DIY costs')],
 'guides/solid-wall-insulation-cost/index.html': [
  ('Based on gas heating at Ofgem Q1 2026 price cap rates (6.76p/kWh).</p>', GAS + '</p>')],
 'guides/underfloor-insulation-cost/index.html': [
  ('Savings for a 3-bed semi on gas at Ofgem Q1 2026 rates. Professional costs', 'Savings for a 3-bed semi with gas heating. ' + GAS + ' Professional costs'),
  ('Gas heating at Ofgem Q1 2026 rates. Detached homes', GAS + ' Detached homes')],
}
```

(epc-rating-landlords and warm-home-discount only carry the sources line, which Task 20 sweeps.)

- [ ] **Step 2: Check, apply, verify**

Run: `python3 docs/superpowers/tools/apply_edits.py edits_annotate --check && python3 docs/superpowers/tools/apply_edits.py edits_annotate`
Expected: `checked 11 files, 12 edits` then `applied 11 files, 12 edits`.

Run: `/usr/bin/grep -l 'Q1 2026 rates\|Q1 2026 price cap rates' guides/*/index.html | wc -l`
Expected: `0` (only `Ofgem Q1 2026 price cap</a>` anchor texts remain, for the sweep).

---

### Task 19b: Home Upgrade Grant page running-cost note

**Files:**
- Modify: `guides/home-upgrade-grant/index.html` (see the rows printed in the "HUG rows" section appended after this plan's self-review; the edit module is `edits_hug.py`)

- [ ] **Step 1: Write and apply the edit list** as specified in the appendix "Task 19b detail" at the end of this plan, then verify with:

Run: `/usr/bin/grep -c '24\.5p\|~16p\|Q1 2026' guides/home-upgrade-grant/index.html`
Expected: `1` before Task 20 (the sources anchor), `0` after.

---

### Task 20: Dates and labels sweep, stage-c gate, commit C

**Files:**
- Create: `docs/superpowers/tools/sweep.py`
- Modify: every touched page (dates, dateModified, remaining Ofgem anchor texts)

- [ ] **Step 1: Write the sweep**

Create `docs/superpowers/tools/sweep.py`:

```python
#!/usr/bin/env python3
"""Sitewide label and date sweep for touched pages only."""
import glob, re

UNTOUCHED = {
 'epc-calculator/index.html', 'contact/index.html', 'privacy/index.html', 'terms/index.html',
 'guides/condensation-mould-guide/index.html', 'guides/heat-pump-noise/index.html',
 'guides/how-to-improve-epc-rating/index.html', 'guides/planning-permission-heat-pump/index.html',
 'guides/radiator-sizing-heat-pump/index.html', 'guides/warm-homes-plan-2026/index.html',
}
LABELS = [
 ('>Ofgem Q1 2026 price cap</a>', '>Ofgem price cap, October to December 2026</a>'),
 ('>Ofgem Q1 2026</a>', '>Ofgem price cap, October to December 2026</a>'),
 ('Ofgem</a> Q1 2026 price cap', 'Ofgem</a> price cap, October to December 2026'),
 ('Ofgem</a> Q1 2026', 'Ofgem</a> price cap, October to December 2026'),
 ('Updated March 2026', 'Updated September 2026'),
]
pages = sorted(set(glob.glob('index.html') + glob.glob('*/index.html') + glob.glob('guides/*/index.html')))
report = {}
for f in pages:
    if f in UNTOUCHED:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    for old, new in LABELS:
        s = s.replace(old, new)
    if f.startswith('guides/') and f != 'guides/index.html':
        s, n = re.subn(r'"dateModified": ?"2026-03-\d\d"', '"dateModified":"2026-09-06"', s)
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        report[f] = True
    left = re.findall(r'.{0,50}Q1 2026.{0,30}', s)
    if left:
        print('LEFTOVER', f, left)
print('rewritten %d pages' % len(report))
```

- [ ] **Step 2: Run it**

Run: `python3 docs/superpowers/tools/sweep.py`
Expected: `rewritten 38 pages` (give or take two) and no `LEFTOVER` lines. If a LEFTOVER prints, add a tuple for that exact context to the relevant `edits_*.py` module (or to LABELS if it is an anchor variant) and rerun. Never edit an untouched page.

- [ ] **Step 3: Stage-c gate**

Run: `python3 docs/superpowers/tools/gates.py --stage c`
Expected: `ALL PASS`. The two most likely failures and their fixes: a stale token left in prose (grep for it with `/usr/bin/grep -rn TOKEN --include='*.html' .` and add an exact tuple to the page's module), or a touched guide whose `dateModified` uses an unexpected format (open the file and set it to `2026-09-06` by hand).

- [ ] **Step 4: Spot-read three pages**

Run: `for f in guides/heat-pump-running-costs guides/average-energy-bills-uk guides/heat-pump-vs-new-boiler; do echo "== $f"; sed -e 's/<[^>]*>/ /g' $f/index.html | tr -s ' \n' ' ' | /usr/bin/grep -o '[^.]*\(26\.32p\|7\.97p\|£1,723\|£1,063\)[^.]*\.' | head -4; done`
Expected: sentences that read naturally with the new figures and no doubled words. Fix any awkward sentence by adding a tuple to that page's module and re-running only that module (the runner refuses to double-apply, so a second run of an already-applied module reports `expected 1, found 0` for its earlier tuples: put the new tuple in a fresh module such as `edits_fixups.py` instead).

- [ ] **Step 5: Commit C**

```bash
git add -A
git commit -m "Refresh prices and dates to Ofgem October to December 2026

Electricity 26.32p, gas 7.97p, standing charges 54.83p and 29.68p, oil 9.0p,
heat pump tariff assumption 18p. Recomputed every table on the 15 pages that
use the site's own model, annotated the EST-sourced insulation pages with the
price change, updated the four calculators' constants, and moved dates to
September 2026 on every touched page. Ofgem typical consumption values updated
to 2,500 kWh electricity and 9,500 kWh gas.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

Expected: clean tree after commit.

---

### Task 21: Rewrite the 4-bed heat pump guide

**Files:**
- Rewrite: `guides/heat-pump-cost-4-bed-house/index.html` (replace the whole file with the content below)

- [ ] **Step 1: Write the file**

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Heat Pump Cost for a 4-Bed House UK 2026: Full Price Breakdown</title>
<meta name="description" content="A heat pump for a 4-bed house costs £11,000 to £16,000 installed, £3,500 to £8,500 after the £7,500 grant. Real 2026 prices, sizing, models and running costs.">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://www.retrofitplanner.co.uk/guides/heat-pump-cost-4-bed-house/">
<meta property="og:title" content="Heat Pump Cost for a 4-Bed House UK 2026: Full Price Breakdown">
<meta property="og:description" content="A heat pump for a 4-bed house costs £11,000 to £16,000 installed, £3,500 to £8,500 after the £7,500 grant. Real 2026 prices, sizing, models and running costs.">
<meta property="og:url" content="https://www.retrofitplanner.co.uk/guides/heat-pump-cost-4-bed-house/">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Retrofit Planner">
<link rel="icon" type="image/x-icon" href="/favicon.ico"><link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png"><link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png"><link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png"><link rel="manifest" href="/site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;0,9..144,700;1,9..144,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/style.css">
<style>
.guide-content{max-width:760px;margin:0 auto;padding:0 24px 60px}.guide-content h1{font-family:var(--font-display);font-size:2rem;font-weight:700;letter-spacing:-0.03em;line-height:1.2;margin-bottom:16px}.guide-content h2{font-family:var(--font-display);font-size:1.4rem;font-weight:600;margin-top:40px;margin-bottom:12px}.guide-content h3{font-family:var(--font-display);font-size:1.1rem;font-weight:600;margin-top:28px;margin-bottom:8px}.guide-content p{line-height:1.7;margin-bottom:16px}.guide-content ul{margin:0 0 16px 20px;line-height:1.7}.guide-content li{margin-bottom:8px}
.data-table{width:100%;border-collapse:collapse;margin:24px 0;font-size:.9rem}.data-table th{background:var(--color-surface-alt);font-weight:600;text-align:left;padding:12px 16px;border-bottom:2px solid var(--color-border);font-size:.82rem;text-transform:uppercase;letter-spacing:.04em;color:var(--color-text-secondary)}.data-table td{padding:12px 16px;border-bottom:1px solid var(--color-surface-alt)}.data-table tr:last-child td{border-bottom:none}.data-table .highlight-cell{color:var(--color-accent);font-weight:600}.note{font-size:.78rem;color:var(--color-text-tertiary);margin-top:-12px;margin-bottom:24px}.callout{background:var(--color-accent-bg);border:1px solid var(--color-accent-border);border-radius:var(--radius-md);padding:20px 24px;margin:28px 0}.callout h4{font-family:var(--font-display);font-size:1rem;font-weight:600;color:var(--color-accent);margin-bottom:8px}.callout p{font-size:.9rem;color:var(--color-text-secondary);margin:0}.callout a{color:var(--color-accent);font-weight:600}.key-number{display:inline-block;font-family:var(--font-display);font-weight:700;font-size:1.1rem;color:var(--color-accent)}.article-meta{font-size:.85rem;color:var(--color-text-tertiary);margin-bottom:24px}
.toc{background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-md);padding:24px;margin:24px 0}.toc h4{font-family:var(--font-display);font-size:1rem;font-weight:600;margin-bottom:12px}.toc a{display:block;font-size:.88rem;color:var(--color-text-secondary);text-decoration:none;padding:6px 0;border-bottom:1px solid var(--color-surface-alt)}.toc a:last-child{border-bottom:none}.toc a:hover{color:var(--color-accent)}
</style>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Home","item":"https://www.retrofitplanner.co.uk/"},{"@type":"ListItem","position":2,"name":"Guides","item":"https://www.retrofitplanner.co.uk/guides/"},{"@type":"ListItem","position":3,"name":"Heat Pump Cost 4-Bed House"}]}</script>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Article","headline":"Heat Pump Cost for a 4-Bed House UK 2026","datePublished":"2026-03-17","dateModified":"2026-09-06","author":{"@type":"Organization","name":"Retrofit Planner"},"publisher":{"@type":"Organization","name":"Retrofit Planner"}}</script>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":"How much does a heat pump cost for a 4-bedroom house?","acceptedAnswer":{"@type":"Answer","text":"An air source heat pump for a 4-bed house costs £11,000 to £16,000 installed. The MCS median for all air source installations in 2026 is £12,908. After the £7,500 Boiler Upgrade Scheme grant you pay £3,500 to £8,500, or £6,500 to £14,500 including radiator upgrades and a hot water cylinder."}},{"@type":"Question","name":"What size heat pump does a 4-bed house need?","acceptedAnswer":{"@type":"Answer","text":"A 4-bed detached house typically needs a 10 to 14 kW air source heat pump. A 4-bed semi needs 8 to 10 kW. The installer's room-by-room heat loss calculation decides the exact size, and insulating first brings both the size and the cost down."}},{"@type":"Question","name":"How much does it cost to run a heat pump in a 4-bed house?","acceptedAnswer":{"@type":"Answer","text":"At the Ofgem price cap for October to December 2026, a 4-bed detached house with 18,000 kWh of heat demand costs £1,117 a year on a heat pump tariff or £1,634 on standard electricity, compared with £1,594 for a gas boiler."}},{"@type":"Question","name":"Which heat pump is best for a 4-bed detached house?","acceptedAnswer":{"@type":"Answer","text":"Any 10 to 14 kW air source unit from Vaillant, Mitsubishi, Daikin or Samsung will heat a 4-bed detached house well. Choose on the installer's design, a flow temperature of 50C or lower and the seasonal efficiency quoted, rather than on brand."}},{"@type":"Question","name":"Is a heat pump worth it for a 4-bedroom house?","acceptedAnswer":{"@type":"Answer","text":"Yes on a heat pump tariff or off the gas grid. A 4-bed detached saves £477 a year against gas on a heat pump tariff and around £800 against oil, and the unit lasts 20 to 25 years. Against a cheap boiler replacement on a standard electricity tariff the case is weaker."}},{"@type":"Question","name":"How long does a 4-bed heat pump installation take?","acceptedAnswer":{"@type":"Answer","text":"Two to four days for the heat pump, cylinder and controls, and up to a week when most radiators are replaced. The installer applies for the Boiler Upgrade Scheme grant and deducts it from the invoice."}}]}</script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-4QMWG6G2WL"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-4QMWG6G2WL');</script>
</head>
<body>
<nav class="nav"><div class="nav-inner"><a href="/" class="nav-logo">Retrofit Planner</a><ul class="nav-links"><li><a href="/heat-pump-calculator/">Heat Pump</a></li><li><a href="/insulation-calculator/">Insulation</a></li><li><a href="/epc-calculator/">EPC Rating</a></li><li><a href="/solar-calculator/">Solar Panels</a></li><li><a href="/grants/">Grants</a></li><li><a href="/guides/" class="active">Guides</a></li></ul></div></nav>
<main class="guide-content">
<div class="breadcrumbs"><a href="/">Home</a><span>/</span><a href="/guides/">Guides</a><span>/</span>Heat Pump Cost 4-Bed House</div>
<p class="article-meta">Updated September 2026. Installed prices from <a href="https://mcscertified.com/low-carbon-landscapes/mcs-data-dashboard/" target="_blank" rel="noopener">MCS installation data</a> for April to June 2026. Energy prices from the <a href="https://www.ofgem.gov.uk/check-if-energy-price-cap-affects-you" target="_blank" rel="noopener">Ofgem</a> price cap for October to December 2026.</p>
<h1>Heat Pump Cost for a 4-Bedroom House: Full 2026 Breakdown</h1>
<p class="lead">An air source heat pump for a 4-bed house costs <span class="key-number">£11,000 to £16,000</span> installed. The <a href="/guides/boiler-upgrade-scheme-guide/">£7,500 Boiler Upgrade Scheme grant</a> brings that down to £3,500 to £8,500, and homes replacing an oil or LPG boiler now get £9,000. Add radiator upgrades and a hot water cylinder and the realistic total is £6,500 to £14,500 after the grant. At the Ofgem price cap for October to December 2026, running costs are £1,117 a year on a <a href="/guides/best-heat-pump-tariffs/">heat pump tariff</a>, £477 less than gas. This guide covers every cost that is specific to a 4-bed home: the prices people actually paid in 2026, sizing, the models installers fit, radiators and cylinders, running costs, and what to check in a quote.</p>
<div class="toc"><h4>In this guide</h4>
<a href="#real-prices">What a 4-bed heat pump really costs in 2026</a>
<a href="#breakdown">Complete cost breakdown</a>
<a href="#semi-vs-detached">4-bed semi versus 4-bed detached</a>
<a href="#size">What size heat pump for a 4-bed house</a>
<a href="#models">Which heat pumps suit a 4-bed house</a>
<a href="#radiators">Radiators, cylinder and pipework</a>
<a href="#running-costs">Running costs: 4-bed detached</a>
<a href="#grant">The Boiler Upgrade Scheme for a 4-bed</a>
<a href="#worth-it">Is a heat pump worth it for a 4-bed house</a>
<a href="#ground-source">Ground source vs air source</a>
<a href="#quotes">Getting quotes: what to check</a>
<a href="#faq">Frequently asked questions</a>
</div>
<h2 id="real-prices">What a 4-bed heat pump really costs in 2026</h2>
<p>The most reliable price data comes from installations paid for through the Boiler Upgrade Scheme, which the Microgeneration Certification Scheme (MCS) publishes every quarter. For England and Wales in April to June 2026, the median air source heat pump installation cost <span class="key-number">£12,908</span>. A quarter of installations came in under £11,128 and a quarter cost more than £15,627. These are prices actually paid on the invoice, not quotes.</p>
<table class="data-table"><thead><tr><th>Position</th><th>Installed cost</th><th>After £7,500 grant</th><th>After £9,000 oil or LPG grant</th></tr></thead><tbody>
<tr><td>Lower quartile</td><td>£11,128</td><td class="highlight-cell">£3,628</td><td>£2,128</td></tr>
<tr><td>Median</td><td>£12,908</td><td class="highlight-cell">£5,408</td><td>£3,908</td></tr>
<tr><td>Upper quartile</td><td>£15,627</td><td class="highlight-cell">£8,127</td><td>£6,627</td></tr>
</tbody></table>
<p class="note">MCS Data Dashboard, BUS-funded air source installations, England and Wales, April to June 2026. Excludes radiator and cylinder work invoiced separately.</p>
<p>A 4-bed house normally sits in the upper half of that range. It needs a 10 to 14 kW unit rather than the 5 to 8 kW that suits a terrace, it has more radiators to check and replace, and it usually needs a 250 to 300 litre hot water cylinder. Installers also spend longer on the design, because a larger house has more rooms to survey and more pipework to trace. That is why the realistic range for a 4-bed is £11,000 to £16,000 before the grant, with well-insulated 1990s and newer homes at the bottom and older, larger or poorly insulated ones at the top. Use our <a href="/heat-pump-calculator/">heat pump calculator</a> for an estimate that reflects your own insulation level and heating fuel.</p>
<h2 id="breakdown">Complete cost breakdown</h2>
<table class="data-table"><thead><tr><th>Cost element</th><th>Range</th><th>Notes</th></tr></thead><tbody>
<tr><td>Heat pump unit and installation</td><td>£11,000 to £16,000</td><td>10 to 14 kW air source. Includes unit, pipework, controls, MCS certificate</td></tr>
<tr><td>BUS grant</td><td class="highlight-cell">-£7,500</td><td>Deducted from the installer invoice. £9,000 if you are replacing an oil or LPG boiler</td></tr>
<tr><td>Net heat pump cost</td><td class="highlight-cell">£3,500 to £8,500</td><td>What you actually pay for the heat pump</td></tr>
<tr><td>Radiator upgrades</td><td>£3,000 to £5,500</td><td>4 to 7 radiators typically need upsizing. See <a href="/guides/radiator-sizing-heat-pump/">radiator sizing guide</a></td></tr>
<tr><td>Hot water cylinder</td><td>£800 to £1,500</td><td>Required if replacing a combi boiler, 250 to 300 litres for a 4-bed</td></tr>
<tr><td>Pipework modifications</td><td>£0 to £1,500</td><td>If existing pipework is microbore or undersized</td></tr>
<tr><td>Concrete plinth</td><td>£200 to £500</td><td>Base for the outdoor unit</td></tr>
<tr><td><strong>Total out of pocket</strong></td><td><strong>£6,500 to £14,500</strong></td><td>After the BUS grant, including all ancillary costs</td></tr>
</tbody></table>
<p class="note">0% VAT applies until March 2027. Costs from MCS installation data and <a href="https://energysavingtrust.org.uk/" target="_blank" rel="noopener">Energy Saving Trust</a>.</p>
<p>The heat pump itself is only part of the bill. On a 4-bed retrofit the radiator work, cylinder and pipework together add £4,000 to £8,500, so a quote that covers the heat pump alone is not the number to budget from. Ask every installer for an itemised quote that lists each radiator they intend to change.</p>
<h2 id="semi-vs-detached">4-bed semi versus 4-bed detached</h2>
<p>Not every 4-bed house is detached. A 4-bed semi shares one wall, so it loses less heat, needs a smaller unit and costs less to run. The difference is worth £1,000 to £3,000 on installation and around £250 a year on running costs.</p>
<table class="data-table"><thead><tr><th>Property</th><th>Typical heat demand</th><th>Heat pump size</th><th>Installed cost</th><th>After £7,500 grant</th></tr></thead><tbody>
<tr><td>4-bed semi-detached</td><td>13,000 to 15,000 kWh</td><td>8 to 10 kW</td><td>£10,000 to £13,000</td><td class="highlight-cell">£2,500 to £5,500</td></tr>
<tr><td>4-bed detached</td><td>16,000 to 20,000 kWh</td><td>10 to 14 kW</td><td>£11,000 to £16,000</td><td class="highlight-cell">£3,500 to £8,500</td></tr>
</tbody></table>
<p class="note">Heat demand assumes loft insulation, double glazing and filled cavity walls where present.</p>
<p>At 14,000 kWh of heat demand, a 4-bed semi costs £1,240 a year on gas, £1,271 on a heat pump with a standard tariff, and £869 on a heat pump tariff at the October to December 2026 price cap. The detached figures are in the running costs section below.</p>
<h2 id="size">What size heat pump for a 4-bed house</h2>
<p>A 4-bed detached house typically needs a 10 to 14 kW air source heat pump. The exact size depends on your insulation level.</p>
<table class="data-table"><thead><tr><th>Insulation level</th><th>Heat demand (kWh)</th><th>HP size</th><th>Installed cost</th></tr></thead><tbody>
<tr><td>Well insulated (270mm loft, filled cavity, double glazed)</td><td>14,000 to 16,000</td><td>10 to 12 kW</td><td class="highlight-cell">£11,000 to £13,000</td></tr>
<tr><td>Partially insulated</td><td>17,000 to 20,000</td><td>12 to 14 kW</td><td>£13,000 to £15,000</td></tr>
<tr><td>Poorly insulated</td><td>22,000 to 28,000</td><td>14 to 18 kW</td><td>£15,000 to £19,000</td></tr>
</tbody></table>
<p class="note">Insulating first reduces heat pump size and cost. See our <a href="/guides/is-loft-insulation-worth-it/">loft insulation</a> and <a href="/guides/is-cavity-wall-insulation-worth-it/">cavity wall insulation</a> guides.</p>
<p>Your MCS installer must carry out a room-by-room heat loss calculation before quoting. It works out how much heat each room loses on the coldest design day, usually around minus 3C in southern England and lower further north, and sizes the unit to cover the total with a small margin. As a rule of thumb, a reasonably insulated 4-bed needs 40 to 60 watts per square metre of floor area, so a 140 square metre house has 6 to 9 kW of heat loss and needs a 10 to 12 kW unit once hot water is included. Oversizing is not a safe default. A unit that is too big cycles on and off, wears faster and runs less efficiently than one sized to the house, so treat a quote with no heat loss calculation behind it as a warning sign.</p>
<div class="callout"><h4>Insulate first to save £2,000 to £4,000</h4><p><a href="/guides/is-loft-insulation-worth-it/">Loft insulation</a> (£300 to £600) and <a href="/guides/is-cavity-wall-insulation-worth-it/">cavity wall insulation</a> (£400 to £1,500) reduce your heat pump cost and running costs permanently. If you qualify for <a href="/guides/eco4-scheme-explained/">ECO4</a>, get free insulation first.</p></div>
<h2 id="models">Which heat pumps suit a 4-bed house</h2>
<p>Installers fit the 10 to 14 kW class from four manufacturers more than any other. The table shows the models you are most likely to be quoted for a 4-bed house.</p>
<table class="data-table"><thead><tr><th>Model</th><th>Outputs for a 4-bed</th><th>Refrigerant</th><th>Max flow temp</th><th>Why pick it</th></tr></thead><tbody>
<tr><td>Vaillant aroTHERM plus</td><td>10 kW, 12 kW</td><td>R290</td><td>75C</td><td>High flow temperature keeps more existing radiators, very quiet mode</td></tr>
<tr><td>Mitsubishi Ecodan</td><td>11.2 kW, 14 kW</td><td>R32 or R290 by model</td><td>60 to 70C</td><td>Largest UK installer base, Zubadan models hold output to minus 25C</td></tr>
<tr><td>Daikin Altherma 3 H HT</td><td>14 kW, 16 kW, 18 kW</td><td>R32</td><td>70C</td><td>Widest cold-weather range, long track record</td></tr>
<tr><td>Samsung EHS Mono HT Quiet</td><td>12 kW, 14 kW</td><td>R32</td><td>70C</td><td>Value option with high temperature output</td></tr>
</tbody></table>
<p class="note">Outputs are the nominal ratings in each range that cover a 4-bed house. Your heat loss calculation decides which one you need.</p>
<p>Brand matters less than design. Ask for a design flow temperature of 50C or lower, a seasonal coefficient of performance (SCOP) above 3.5 in the quote, and an MCS 020 noise assessment for the outdoor unit position. R290 units such as the aroTHERM plus can run hotter, which sometimes means fewer radiator changes in an older house, while the Ecodan and Altherma ranges have the largest installed base and the widest parts availability. A well-designed system from any of these manufacturers will outperform a poorly designed one from the best of them. Our <a href="/guides/heat-pump-noise/">heat pump noise guide</a> explains what the noise limits mean for where the outdoor unit can go.</p>
<h2 id="radiators">Radiators, cylinder and pipework</h2>
<p>A heat pump runs at a lower flow temperature than a gas boiler, so each radiator has to be larger to deliver the same heat. A 4-bed house typically has 10 to 14 radiators, and 4 to 7 of them need upsizing. Budget £3,000 to £5,500 for that work. Our <a href="/guides/radiator-sizing-heat-pump/">radiator sizing guide</a> explains how installers decide which ones to change.</p>
<p>You also need a hot water cylinder, normally 250 to 300 litres for a family of four or five. If you currently have a combi boiler there is no cylinder, so allow £800 to £1,500 for one plus a cupboard or loft space to put it in. If you already have a system boiler with a cylinder, it will usually need replacing anyway, because heat pump cylinders have a larger coil to work at lower temperatures.</p>
<p>The common budget breaker is microbore pipework, the 8 mm or 10 mm pipes fitted in many homes from the 1970s onwards. It restricts flow at heat pump temperatures and often needs replacing with 15 mm or 22 mm pipe at £1,000 to £1,500. Ask the installer to check the pipe sizes during the survey rather than discovering the problem on installation day.</p>
<h2 id="running-costs">Running costs: 4-bed detached</h2>
<p>These figures use the Ofgem price cap for 1 October to 31 December 2026: electricity 26.32p per kWh and gas 7.97p per kWh. Gas rose 9% at this cap change while electricity barely moved, which is why a heat pump on a standard tariff now costs about the same to run as a gas boiler.</p>
<table class="data-table"><thead><tr><th>Heating system</th><th>Annual cost</th><th>Saving vs gas</th></tr></thead><tbody>
<tr><td>Gas boiler</td><td>£1,594</td><td>Baseline</td></tr>
<tr><td>Heat pump (standard tariff)</td><td>£1,634</td><td>-£40 (about level)</td></tr>
<tr><td class="highlight-cell">Heat pump (heat pump tariff)</td><td class="highlight-cell">£1,117</td><td class="highlight-cell">£477 saving</td></tr>
<tr><td>Oil boiler</td><td>£1,900 to £2,300</td><td>n/a</td></tr>
<tr><td>LPG boiler</td><td>£1,900</td><td>n/a</td></tr>
<tr><td>Electric boiler</td><td>£4,738</td><td>n/a</td></tr>
</tbody></table>
<p class="note">18,000 kWh heat demand. Gas at 7.97p/kWh and 90% boiler efficiency. Heat pump COP 2.9 at 26.32p/kWh, or 18p/kWh effective on a well-scheduled heat pump tariff such as Octopus Cosy. Oil at 9.0p/kWh (September 2026 kerosene prices), LPG at 9.5p/kWh. Standing charges excluded.</p>
<p>The tariff makes or breaks the economics. On a heat pump tariff you save £477 a year against gas, which is £9,540 over 20 years. Disconnecting your gas supply saves a further £108 a year in gas standing charge. Read our <a href="/guides/heat-pump-running-costs/">running costs guide</a> for the full comparison, our <a href="/guides/best-heat-pump-tariffs/">tariff guide</a> for how to get an effective rate near 18p, and our <a href="/guides/electric-boiler-vs-heat-pump/">electric boiler vs heat pump guide</a> if you heat with electricity today.</p>
<p>Insulation moves these numbers more than any tariff. A well-insulated 4-bed detached with 15,000 kWh of heat demand costs £1,328 a year on gas, £1,361 on a heat pump with a standard tariff and £931 on a heat pump tariff, so the saving stays near £400 a year while every bill is £250 to £300 lower.</p>
<h2 id="grant">The Boiler Upgrade Scheme for a 4-bed</h2>
<p>The Boiler Upgrade Scheme pays £7,500 towards an air source or ground source heat pump in England and Wales. Since July 2026, homes replacing an oil or LPG boiler get £9,000. Your MCS-certified installer applies for the grant and it comes off the invoice, so you never handle the money. The scheme was extended to 2030 in April 2026 with a £400 million budget for the current year, and installations carry 0% VAT until March 2027. There is no upper limit on the value of the house or the size of the system, so a 4-bed detached qualifies exactly as a flat does, provided the property has a valid EPC and the heat pump replaces a fossil fuel system. Read our <a href="/guides/boiler-upgrade-scheme-guide/">BUS grant guide</a> for the full eligibility rules and our <a href="/grants/">grant checker</a> for everything else you might qualify for.</p>
<h2 id="worth-it">Is a heat pump worth it for a 4-bed house</h2>
<p>Against a new gas boiler at £2,500 to £3,500, a heat pump costs £3,000 to £12,000 more once radiators and the cylinder are included. At £477 a year saving on a heat pump tariff, that is a payback of 6 to 25 years, so the case rests on landing at the low end of the cost range or on being off the gas grid. Against an oil boiler the saving is around £800 a year and the payback drops to 4 to 15 years, before counting the £9,000 grant and the oil tank you no longer need. A heat pump also lasts 20 to 25 years compared with 12 to 15 for a boiler, so over its life it replaces one and a half boilers. Run the numbers for your own house with our <a href="/boiler-vs-heat-pump/">boiler vs heat pump comparison</a>, and read <a href="/guides/heat-pump-vs-new-boiler/">heat pump vs new boiler</a> for the 15-year view.</p>
<h2 id="ground-source">Ground source vs air source for a 4-bed</h2>
<table class="data-table"><thead><tr><th>System</th><th>Installed cost</th><th>After grant</th><th>Annual running cost</th></tr></thead><tbody>
<tr><td>Air source</td><td>£11,000 to £16,000</td><td class="highlight-cell">£3,500 to £8,500</td><td>£1,117 (HP tariff)</td></tr>
<tr><td>Ground source</td><td>£22,000 to £35,000</td><td>£14,500 to £27,500</td><td class="highlight-cell">£876 (HP tariff)</td></tr>
</tbody></table>
<p class="note">Ground source COP 3.7, needs a 100m+ borehole or 200+ sqm of garden. Both qualify for the £7,500 BUS grant.</p>
<p>For most 4-bed homes air source is the practical choice. Ground source saves roughly £240 a year on a heat pump tariff but costs £10,000 or more extra upfront and needs a drilling rig or a large trench in the garden. It makes sense for a detached house with plenty of land and a long ownership horizon. Read our <a href="/guides/heat-pump-cost-by-house-type/">costs by house type guide</a> for the full comparison across property types.</p>
<h2 id="quotes">Getting quotes: what to check</h2>
<p>Get three quotes from MCS-certified installers, and compare them on the design rather than the headline price. Each quote should include:</p>
<ul>
<li>A room-by-room heat loss calculation with the design outdoor temperature stated.</li>
<li>The design flow temperature, ideally 50C or lower, and the SCOP the installer expects at that temperature.</li>
<li>A radiator schedule listing every emitter, which ones change, and their new sizes.</li>
<li>The cylinder size and where it will go.</li>
<li>An MCS 020 noise assessment for the outdoor unit position, showing it meets the 42 dB limit at the nearest neighbour's window.</li>
<li>The warranty on the unit, usually 5 to 7 years, the warranty on the installation, and who you call when something fails.</li>
<li>Confirmation that the installer will apply for the Boiler Upgrade Scheme and deduct it from the invoice.</li>
</ul>
<p>Installation takes 2 to 4 days for the heat pump and cylinder, and up to a week if most radiators are being swapped. Check the <a href="/guides/planning-permission-heat-pump/">planning permission rules</a> before you sign. Most 4-bed houses in England are covered by permitted development, but listed buildings and conservation areas are not. Find installers through the <a href="https://mcscertified.com/find-an-installer/" target="_blank" rel="noopener">MCS installer search</a>.</p>
<p>Reduce noise with <a href="https://www.amazon.co.uk/Anti-Vibration-Pads-Washing-Machine/dp/B0CN19ZGMN?linkCode=ll2&tag=minnisandcomp-21&linkId=ffd22b56b4cb72eaea60811486115867&ref_=as_li_ss_tl" target="_blank" rel="noopener sponsored">anti-vibration pads</a>. Manage your system with a <a href="https://www.amazon.co.uk/Drayton-Wiser-Multi-Zone-Thermostat-Radiator/dp/B075GSQDZF?linkCode=ll2&tag=minnisandcomp-21&linkId=239b41c78ed1daccb461674b20104df6&ref_=as_li_ss_tl" target="_blank" rel="noopener sponsored">smart thermostat</a>. Track costs with an <a href="https://www.amazon.co.uk/Efergy-Technologies-ELITE-CLASSIC-4-0/dp/B001Q1G4WK?linkCode=ll2&tag=minnisandcomp-21&linkId=8851dc3cbe4a8278697f2ed210c97971&ref_=as_li_ss_tl" target="_blank" rel="noopener sponsored">energy monitor</a>.</p>
<div class="related-links">
<a href="/heat-pump-calculator/" class="related-link-card"><div class="rl-icon"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="8" y1="6" x2="16" y2="6"/></svg></div><div class="rl-text"><div class="rl-name">Heat Pump Calculator</div><div class="rl-desc">Personalised cost estimate</div></div></a>
<a href="/guides/heat-pump-cost-by-house-type/" class="related-link-card"><div class="rl-icon"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg></div><div class="rl-text"><div class="rl-name">Costs by House Type</div><div class="rl-desc">Compare all property types</div></div></a>
<a href="/guides/radiator-sizing-heat-pump/" class="related-link-card"><div class="rl-icon"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/></svg></div><div class="rl-text"><div class="rl-name">Radiator Sizing Guide</div><div class="rl-desc">Which radiators need upgrading</div></div></a>
<a href="/guides/boiler-upgrade-scheme-guide/" class="related-link-card"><div class="rl-icon"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg></div><div class="rl-text"><div class="rl-name">BUS Grant Guide</div><div class="rl-desc">How to claim £7,500</div></div></a>
</div>
<h2 id="faq">Frequently asked questions</h2>
<h3>How much does a heat pump cost for a 4-bedroom house?</h3>
<p>£11,000 to £16,000 installed. The MCS median for all air source installations in 2026 is £12,908. After the <a href="/guides/boiler-upgrade-scheme-guide/">£7,500 BUS grant</a> you pay £3,500 to £8,500, or £6,500 to £14,500 with radiators and a cylinder.</p>
<h3>What size heat pump does a 4-bed house need?</h3>
<p>10 to 14 kW for a detached house, 8 to 10 kW for a semi. The installer's heat loss calculation decides. <a href="/guides/is-loft-insulation-worth-it/">Insulate first</a> to bring the size and cost down.</p>
<h3>How much does it cost to run a heat pump in a 4-bed house?</h3>
<p>£1,117 a year on a <a href="/guides/best-heat-pump-tariffs/">heat pump tariff</a>, £1,634 on standard electricity, against £1,594 for gas at the October to December 2026 price cap. See our <a href="/guides/heat-pump-running-costs/">running costs guide</a>.</p>
<h3>Which heat pump is best for a 4-bed detached house?</h3>
<p>Any 10 to 14 kW unit from Vaillant, Mitsubishi, Daikin or Samsung will heat a 4-bed detached house well. Choose on the installer's design, a flow temperature of 50C or lower and the SCOP in the quote, not on brand. Our <a href="/guides/heat-pump-noise/">heat pump noise guide</a> covers the outdoor unit.</p>
<h3>Is a heat pump worth it for a 4-bedroom house?</h3>
<p>Yes on a heat pump tariff or off the gas grid. You save £477 a year against gas and around £800 against oil, and the unit lasts 20 to 25 years. Against a cheap boiler replacement on a standard tariff the case is weaker. Compare with our <a href="/boiler-vs-heat-pump/">boiler vs heat pump tool</a>.</p>
<h3>How long does a 4-bed heat pump installation take?</h3>
<p>2 to 4 days for the heat pump, cylinder and controls, and up to a week when most radiators are replaced. The <a href="/guides/boiler-upgrade-scheme-guide/">BUS grant</a> is applied by the installer, so there is no waiting on your side.</p>
<h2>Data sources</h2>
<p>Installed prices from the <a href="https://mcscertified.com/low-carbon-landscapes/mcs-data-dashboard/" target="_blank" rel="noopener">MCS Data Dashboard</a> (BUS-funded installations, England and Wales, April to June 2026). Energy prices from the <a href="https://www.ofgem.gov.uk/check-if-energy-price-cap-affects-you" target="_blank" rel="noopener">Ofgem price cap</a> for October to December 2026. Grant rules from <a href="https://www.gov.uk/apply-boiler-upgrade-scheme" target="_blank" rel="noopener">GOV.UK</a>. Cost ranges from <a href="https://energysavingtrust.org.uk/" target="_blank" rel="noopener">Energy Saving Trust</a> and installer market data.</p>
</main>
<section class="newsletter-signup"><div class="newsletter-inner"><h3>Get UK Energy Policy Updates</h3><p>Grant deadlines, tariff changes, and money-saving tips for homeowners.<br>No spam. Unsubscribe anytime.</p><form name="newsletter" method="POST" action="/thank-you/" data-netlify="true" netlify-honeypot="bot-field" class="newsletter-form"><p style="display:none"><label>Do not fill this in: <input name="bot-field"></label></p><input type="email" name="email" placeholder="Your email address" required><button type="submit">Subscribe</button></form></div></section>
<style>.newsletter-signup{background:var(--color-surface-alt,#f5f7f5);border-top:2px solid var(--color-accent-bg,#e8f5e9);padding:40px 24px;text-align:center}.newsletter-inner{max-width:520px;margin:0 auto}.newsletter-signup h3{font-family:var(--font-display);font-size:1.2rem;font-weight:600;margin-bottom:8px}.newsletter-signup p{font-size:.88rem;color:var(--color-text-secondary,#555);margin-bottom:16px;line-height:1.5}.newsletter-form{display:flex;gap:8px;max-width:420px;margin:0 auto}.newsletter-form input[type="email"]{flex:1;padding:10px 14px;border:1px solid var(--color-border,#ddd);border-radius:var(--radius-sm,6px);font-size:.9rem}.newsletter-form button{padding:10px 20px;background:var(--color-accent,#1b6b4a);color:#fff;border:none;border-radius:var(--radius-sm,6px);font-size:.9rem;font-weight:600;cursor:pointer}@media(max-width:500px){.newsletter-form{flex-direction:column}.newsletter-form button{width:100%}}</style>
<footer class="footer"><div class="footer-inner"><div><div class="footer-brand">Retrofit Planner</div><p class="footer-about">Free tools to help UK homeowners plan energy-efficient home improvements.</p></div><div class="footer-col"><h4>Calculators</h4><a href="/heat-pump-calculator/">Heat Pump Cost Calculator</a><a href="/insulation-calculator/">Insulation Savings Calculator</a><a href="/epc-calculator/">EPC Improvement Planner</a><a href="/solar-calculator/">Solar Panel ROI Calculator</a><a href="/boiler-vs-heat-pump/">Boiler vs Heat Pump</a><a href="/grants/">Grant Eligibility Checker</a></div><div class="footer-col"><h4>Guides</h4><a href="/guides/heat-pump-cost-4-bed-house/">Heat Pump Cost: 4-Bed House</a><a href="/guides/heat-pump-cost-by-house-type/">Costs by House Type</a><a href="/guides/heat-pump-running-costs/">Heat Pump Running Costs</a><a href="/guides/best-heat-pump-tariffs/">Best Heat Pump Tariffs</a><a href="/guides/boiler-upgrade-scheme-guide/">BUS Grant Guide</a><a href="/guides/how-epc-points-are-calculated/">How EPC Points Are Calculated</a></div><div class="footer-col"><h4>Company</h4><a href="/about/">About Us</a><a href="/methodology/">Our Methodology</a><a href="/privacy/">Privacy Policy</a><a href="/terms/">Terms of Use</a><a href="/contact/">Contact</a></div></div><div class="attribution">Data from <a href="https://www.ofgem.gov.uk/check-if-energy-price-cap-affects-you" target="_blank" rel="noopener">Ofgem</a>, <a href="https://energysavingtrust.org.uk/" target="_blank" rel="noopener">Energy Saving Trust</a>, and <a href="https://www.gov.uk/" target="_blank" rel="noopener">GOV.UK</a>.</div></footer>
</body>
</html>
```

- [ ] **Step 2: Verify the page**

Run: `python3 docs/superpowers/tools/gates.py --stage d`
Expected: `ALL PASS`, including the three 4-bed lines (word count above 2,000, at least 15 internal links, 6 schema questions).

Run: `python3 -c "import re;s=open('guides/heat-pump-cost-4-bed-house/index.html').read();print('em dash' if chr(8212) in s else 'no em dash', '| visible ampersands:', len(re.findall(r'>[^<]*&(?!amp;|#)[^<]*<', re.sub(r'<script.*?</script>','',s,flags=re.S))))"`
Expected: `no em dash | visible ampersands: 0`

- [ ] **Step 3: Update the guides hub description**

The hub card for this guide reads "£11,000 to £16,000 installed. £3,500 to £8,500 after grant. Full breakdown for 4-bed homes". Replace it so the card reflects the new content:

```python
# python3 - <<'EOF'
p='guides/index.html'; s=open(p).read()
old='£11,000 to £16,000 installed. £3,500 to £8,500 after grant. Full breakdown for 4-bed homes'
new='£11,000 to £16,000 installed, £3,500 to £8,500 after the grant. Real 2026 prices, sizing, models and running costs'
assert s.count(old)==1; open(p,'w').write(s.replace(old,new)); print('hub updated')
# EOF
```

- [ ] **Step 4: Commit D**

```bash
git add -A
git commit -m "Expand 4-bed heat pump cost guide

Rewrite from 854 to about 2,300 words: MCS 2026 real-price quartiles, semi
versus detached, sizing and heat loss, model table, radiators and cylinder,
running costs at the October to December 2026 cap, BUS 2030 and 9,000 oil
and LPG rate, payback, ground source, quote checklist, six FAQs with schema,
table of contents and Open Graph tags.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 22: Calculator checks in the browser

**Files:** none modified.

- [ ] **Step 1: Serve the site locally**

Run in the background: `python3 -m http.server 8787 --bind 127.0.0.1`
Expected: `Serving HTTP on 127.0.0.1 port 8787`.

- [ ] **Step 2: Check each calculator**

For each of the four pages, using the Browser pane tools:

1. `navigate` to the URL.
2. `find` the button text, `left_click` it.
3. `javascript_tool` with the expression in the table; confirm the value.
4. `read_console_messages` with `onlyErrors: true`; expect an empty list.
5. `get_page_text` and confirm the results block contains a pound figure and does not contain "24.5".

| URL | Button text | Expression | Expected |
|---|---|---|---|
| http://127.0.0.1:8787/heat-pump-calculator/ | Calculate my heat pump costs | `JSON.stringify(DATA.energyPrices)` | `{"electricity":0.2632,"gas":0.0797,"oil":0.09,"lpg":0.095}` |
| http://127.0.0.1:8787/boiler-vs-heat-pump/ | Compare boiler vs heat pump | `[D.gasRate, D.elecRate].join(',')` | `0.0797,0.2632` |
| http://127.0.0.1:8787/insulation-calculator/ | Calculate my insulation savings | `JSON.stringify(DATA.fuelPrices)` | `{"gas":0.0797,"oil":0.09,"lpg":0.095,"electricity":0.2632}` |
| http://127.0.0.1:8787/solar-calculator/ | Calculate my solar savings | `SOLAR.electricityRate` | `0.2632` |

Also load http://127.0.0.1:8787/guides/heat-pump-cost-4-bed-house/ and take a screenshot to confirm the table of contents, the six tables and the FAQ render with the site styling and no horizontal overflow at the pane width.

- [ ] **Step 3: Stop the server**

Stop the background task started in Step 1.

---

### Task 23: Merge, push, verify live

- [ ] **Step 1: Final gate on the branch**

Run: `python3 docs/superpowers/tools/gates.py --stage d && git status --short | wc -l`
Expected: `ALL PASS` and `0`.

- [ ] **Step 2: Merge fast-forward and push** (the user approved pushing once checks pass)

```bash
git checkout main && git merge --ff-only fix-and-freshen-2026-09 && git push origin main && git log --oneline -5
```

Expected: `Updating <old>..<new>` with `Fast-forward`, then the push summary, then five commits with the four new ones on top of `562ffdf`.

- [ ] **Step 3: Wait for Netlify**

Poll `curl -s -o /dev/null -w '%{http_code}' https://www.retrofitplanner.co.uk/404.html` every 30 seconds until it returns `200` (a page that did not exist before the deploy). Allow up to 5 minutes.

- [ ] **Step 4: Post-deploy checks**

```bash
for u in /guides/heat-pump-guide/ /guides/insulation-guide/ /guides/epc-explained/ /guides/boiler-upgrade-scheme/ /guides/average-energy-bills/ /epc-calculator/epc-calculator/ /guides/heat-pump-running-costs-uk-electricity-vs-gas-compared; do printf "%-70s " "$u"; curl -s -o /dev/null -w '%{http_code} -> %{redirect_url}\n' "https://www.retrofitplanner.co.uk$u"; done
for u in /CONTEXT.md /docs/superpowers/specs/2026-09-06-fix-and-freshen-design.md; do printf "%-70s " "$u"; curl -s -o /dev/null -w '%{http_code}\n' "https://www.retrofitplanner.co.uk$u"; done
for u in / /epc-calculator/ /guides/heat-pump-cost-4-bed-house/ /guides/heat-pump-cost-by-house-type/ /heat-pump-calculator/; do printf "%-45s " "$u"; curl -s "https://www.retrofitplanner.co.uk$u" | /usr/bin/grep -c '26\.32p\|October to December 2026'; done
curl -s https://www.retrofitplanner.co.uk/guides/heat-pump-cost-4-bed-house/ | /usr/bin/grep -o '"@type":"Question"' | wc -l
```

Expected: the seven redirect lines show `301 -> https://www.retrofitplanner.co.uk/<target>/`; the two protected paths show `404`; each of the five pages shows a count of at least 1 (the EPC calculator only carries the footer change, so its count may be 0, which is acceptable); the last line prints `6`.

---

### Task 24: Record the outcome in memory

**Files:**
- Modify: `/Users/nathan/.claude/projects/-Users-nathan-Desktop/memory/project_retrofit_planner.md`

- [ ] **Step 1: Append the round's facts**

```python
# python3 - <<'EOF'
p='/Users/nathan/.claude/projects/-Users-nathan-Desktop/memory/project_retrofit_planner.md'
s=open(p).read()
add=('\n\n**September 2026 fix-and-freshen round (shipped 2026-09-06, branch fix-and-freshen-2026-09 merged to main):** '
     'prices now Ofgem cap 1 Oct to 31 Dec 2026 (elec 26.32p, gas 7.97p, SC 54.83p/29.68p), oil 9.0p, heat pump tariff assumption 18p, '
     'Ofgem TDCV 2,500/9,500 kWh, BUS runs to 2030 with £9,000 for oil/LPG homes. Footer harmonised, 7 redirects in _redirects, '
     '404.html added, /CONTEXT.md and /docs/* return 404 on the live site. Tools for the next refresh live in '
     'docs/superpowers/tools/ (gates.py, verify_model.py, apply_edits.py with edits_*.py); spec and plan in docs/superpowers/. '
     'Follow-ups not done: tariffs guide rewrite (OVO Heat Pump Plus closed Feb 2026), EPC-band running-cost page, '
     'solar calculator repositioning, GitHub token still embedded in the git remote URL.')
if 'September 2026 fix-and-freshen round' not in s:
    open(p,'w').write(s.rstrip('\n')+add+'\n'); print('memory updated')
# EOF
```

- [ ] **Step 2: Update the index line**

In `/Users/nathan/.claude/projects/-Users-nathan-Desktop/memory/MEMORY.md`, change the RetrofitPlanner line to:

`- [RetrofitPlanner (personal side project)](project_retrofit_planner.md) — Desktop/Projects/retrofit-planner is the live repo; Sept 2026 refresh shipped (Ofgem Q4 2026 rates, tools in docs/superpowers/tools/); follow-ups: tariffs rewrite, EPC-band page, solar retitle`

---

## Appendix: Task 19b detail (Home Upgrade Grant page)

Create `docs/superpowers/tools/edits_hug.py`:

```python
EDITS = {'guides/home-upgrade-grant/index.html': [
 ('<tr><td>Air source heat pump</td><td>£9,000 to £13,000</td><td>£300 to £600 vs oil</td></tr>',
  '<tr><td>Air source heat pump</td><td>£9,000 to £13,000</td><td>£750 to £1,350 vs oil</td></tr>'),
 ('<tr><td>Maximum value</td><td class="highlight-cell">Up to £25,000</td><td>Up to £10,000+</td><td>£7,500</td></tr>',
  '<tr><td>Maximum value</td><td class="highlight-cell">Up to £25,000</td><td>Up to £10,000+</td><td>£7,500 (£9,000 for oil or LPG homes)</td></tr>'),
 ('<tr><td>Oil boiler</td><td>£1,200 to £1,600</td><td>£662 (HP tariff)</td><td class="highlight-cell">£538 to £938</td></tr>',
  '<tr><td>Oil boiler</td><td>£1,500 to £2,100</td><td>£745 (HP tariff)</td><td class="highlight-cell">£755 to £1,355</td></tr>'),
 ('<tr><td>LPG boiler</td><td>£1,400 to £1,800</td><td>£662 (HP tariff)</td><td class="highlight-cell">£738 to £1,138</td></tr>',
  '<tr><td>LPG boiler</td><td>£1,600 to £2,000</td><td>£745 (HP tariff)</td><td class="highlight-cell">£855 to £1,255</td></tr>'),
 ('<tr><td>Electric storage heaters</td><td>£2,200 to £3,000</td><td>£662 (HP tariff)</td><td class="highlight-cell">£1,538 to £2,338</td></tr>',
  '<tr><td>Electric storage heaters</td><td>£2,400 to £3,200</td><td>£745 (HP tariff)</td><td class="highlight-cell">£1,655 to £2,455</td></tr>'),
 ('<tr><td>Electric boiler</td><td>£2,500 to £3,500</td><td>£662 (HP tariff)</td><td class="highlight-cell">£1,838 to £2,838</td></tr>',
  '<tr><td>Electric boiler</td><td>£2,700 to £3,800</td><td>£745 (HP tariff)</td><td class="highlight-cell">£1,955 to £3,055</td></tr>'),
 ('<p class="note">Oil at ~7p/kWh. LPG at ~8.5p/kWh. Electricity at 24.5p/kWh. Heat pump COP 2.9 on HP tariff ~16p/kWh. 12,000 kWh heat demand.</p>',
  '<p class="note">Oil at 9.0p/kWh (September 2026 kerosene price). LPG at 9.5p/kWh. Electricity at 26.32p/kWh (Ofgem price cap, October to December 2026). Heat pump COP 2.9 on HP tariff ~18p/kWh. 12,000 kWh heat demand. Fossil fuel and storage heater ranges scaled from the March 2026 figures by the change in each fuel price.</p>'),
]}
```

Basis: oil scaled by 9.0 / 7.0, LPG by 9.5 / 8.5, electric rows by 26.32 / 24.5, all rounded to £100; heat pump on tariff = 12,000 / 2.9 × 18p = £745; savings are the differences.

Run: `python3 docs/superpowers/tools/apply_edits.py edits_hug --check && python3 docs/superpowers/tools/apply_edits.py edits_hug`
Expected: `checked 1 files, 7 edits` then `applied 1 files, 7 edits`.
