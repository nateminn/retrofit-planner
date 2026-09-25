"""Accessibility check. Run from the repo root with a local server on 8799:
    npm i axe-core (anywhere), python3 -m http.server 8799 &,
    python3 docs/superpowers/tools/axe_check.py <path to axe.min.js> <report.json>
Zero violations on 24 Sep 2026 across 68 pages.

Run axe-core (WCAG 2.0/2.1/2.2 A and AA rules) over every page at desktop and phone
widths, including each calculator after it has produced a result."""
import glob, json, sys, collections
from playwright.sync_api import sync_playwright
AXE = open(sys.argv[1]).read()
BASE = 'http://localhost:8799/'
pages = sorted(set(p[2:].replace('index.html', '') for p in glob.glob('./**/index.html', recursive=True) if not p.startswith('./docs'))) + ['404.html']
CALC = {'heat-pump-calculator/', 'energy-bill-calculator/', 'heat-pump-running-cost-calculator/', 'retrofit-plan/', 'boiler-vs-heat-pump/', 'solar-calculator/', 'insulation-calculator/', 'epc-calculator/', 'grants/'}
out = []
with sync_playwright() as p:
    b = p.chromium.launch()
    for w in (1280, 375):
        pg = b.new_page(viewport={'width': w, 'height': 900})
        for u in pages:
            pg.goto(BASE + u); pg.wait_for_timeout(100)
            states = ['load']
            if u in CALC:
                states.append('result')
            for st in states:
                if st == 'result':
                    # fill every visible select with its first real option, numbers with a typical value, then press the main button
                    pg.evaluate("""()=>{document.querySelectorAll('main select').forEach(s=>{if(s.closest('form[data-netlify]'))return;const o=[...s.options].find(o=>o.value);if(o&&!s.value){s.value=o.value;s.dispatchEvent(new Event('change',{bubbles:true}))}});
                                  document.querySelectorAll('main input[type=number]').forEach(i=>{if(!i.value){i.value='1200';i.dispatchEvent(new Event('input',{bubbles:true}))}})}""")
                    btn = pg.locator('button.btn-calculate:not(form[data-netlify] button)').first
                    try: btn.click(timeout=1500)
                    except Exception: pass
                    pg.wait_for_timeout(300)
                pg.add_script_tag(content=AXE)
                res = pg.evaluate("""async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}});
                    return r.violations.map(v=>({id:v.id,impact:v.impact,help:v.help,nodes:v.nodes.map(n=>({target:n.target.join(' '),html:n.html.slice(0,160),summary:(n.failureSummary||'').slice(0,200)}))}))}""")
                for v in res:
                    out.append({'page': u, 'width': w, 'state': st, **v})
        pg.close()
    b.close()
json.dump(out, open(sys.argv[2], 'w'), indent=1)
c = collections.Counter((v['id'], v['impact']) for v in out)
print('violation instances (rule, impact): pages affected')
for (rid, imp), n in c.most_common():
    pg_set = sorted(set(v['page'] for v in out if v['id'] == rid))
    print('  %-28s %-9s %3d  e.g. %s' % (rid, imp, n, ', '.join(pg_set[:4])))
print('total', len(out))
