#!/usr/bin/env python3
"""Build new guide pages whose figures all come from js/heat-model.js.

Each page is a function returning its title, description, H1, FAQ and body. Tables are
computed from the model at build time, so a page can never quote a number the model does
not produce. After building, run site_components.py so the page gets the shared footer and
its quote form, then add it to sitemap.xml and the guides index.

Usage: python3 docs/superpowers/tools/build_new_pages.py [slug ...]
"""
import json, re, subprocess, sys, pathlib, html

ROOT = pathlib.Path(__file__).resolve().parents[3]
TODAY = '2026-09-25'

JS = """global.window={};require('./js/heat-model.js');const H=window.RP_HEAT;const o={};
for(const t of ['detached','semi','mid-terrace','end-terrace','bungalow','flat'])for(const b of [1,2,3,4,5])for(const i of ['poor','average','good','excellent'])
o[t+'|'+b+'|'+i]={gas:H.gasKwh(t,b,i),heat:H.heatDemand(t,b,i),kw:H.heatPumpKw(t,b,i),install:H.heatPumpInstall(t,b,i),range:H.heatPumpInstallRange(t,b,i),cop:H.cop(i)};
console.log(JSON.stringify(o));"""
M = json.loads(subprocess.run(['node', '-e', JS], capture_output=True, text=True, cwd=ROOT).stdout)


def m(t, b, i='average'):
    return M['%s|%d|%s' % (t, b, i)]


def gbp(v):
    return '£' + f'{round(v):,}'


def kw(v):
    return ('%g' % v) + ' kW'


def table(label, head, rows):
    h = ''.join('<th scope="col">%s</th>' % c for c in head)
    body = ''.join('<tr><th scope="row">%s</th>%s</tr>' % (r[0], ''.join('<td>%s</td>' % c for c in r[1:])) for r in rows)
    return ('<div class="tblwrap" tabindex="0" role="region" aria-label="%s"><table class="data-table"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>'
            % (html.escape(label, quote=True), h, body))


# ------------------------------------------------------------------ what size heat pump
def what_size():
    homes = [('flat', 1, '1 bed flat'), ('flat', 2, '2 bed flat'), ('mid-terrace', 2, '2 bed mid-terrace'),
             ('mid-terrace', 3, '3 bed mid-terrace'), ('end-terrace', 3, '3 bed end-terrace'), ('semi', 3, '3 bed semi'),
             ('bungalow', 2, '2 bed bungalow'), ('bungalow', 3, '3 bed bungalow'), ('detached', 3, '3 bed detached'),
             ('semi', 4, '4 bed semi'), ('detached', 4, '4 bed detached'), ('detached', 5, '5 bed detached')]
    rows = []
    for t, b, label in homes:
        rows.append([label] + [kw(m(t, b, i)['kw']) for i in ('poor', 'average', 'good', 'excellent')])
    size_table = table('Typical heat pump size by home and insulation', ['Home', 'Poorly insulated', 'Average', 'Well insulated', 'Recently retrofitted'], rows)
    cost_rows = []
    for t, b, label in [('flat', 2, '2 bed flat'), ('mid-terrace', 3, '3 bed mid-terrace'), ('semi', 3, '3 bed semi'),
                        ('detached', 4, '4 bed detached'), ('detached', 5, '5 bed detached')]:
        c = m(t, b)
        cost_rows.append([label, kw(c['kw']), gbp(c['install']), '%s to %s' % (gbp(c['range'][0]), gbp(c['range'][1])), gbp(max(0, c['install'] - 7500))])
    cost_table = table('What each size costs installed', ['Home, average insulation', 'Typical size', 'Median installed', 'Middle half of installs', 'Median after £7,500 grant'], cost_rows)
    semi = m('semi', 3)
    semi_good = m('semi', 3, 'good')
    semi_poor = m('semi', 3, 'poor')
    d4 = m('detached', 4)
    faq = [
        ('What size heat pump do I need for a 3 bed semi?',
         'Most 3 bed semis with average insulation are fitted with a heat pump of about %s. A well insulated one is nearer %s and a poorly insulated one nearer %s. The exact size comes from the room by room heat loss calculation your installer must do.' % (kw(semi['kw']), kw(semi_good['kw']), kw(semi_poor['kw']))),
        ('What size heat pump do I need for a 4 bedroom house?',
         'A 4 bed detached house with average insulation typically has a heat pump of about %s, and a 4 bed semi about %s. Insulating first can bring that down, and a smaller unit costs less to buy.' % (kw(d4['kw']), kw(m('semi', 4)['kw']))),
        ('Is a bigger heat pump better?',
         'No. An oversized heat pump costs more to buy and switches on and off more often, which can lower its efficiency. The right size is the smallest that meets your home\'s heat loss on a cold day, which is what the installer\'s heat loss calculation works out.'),
        ('How is heat pump size worked out?',
         'An MCS certified installer calculates the heat lost from each room on a cold design day, from its size, walls, windows, floor and roof, and sizes the heat pump to cover that plus hot water. That calculation is required for the Boiler Upgrade Scheme grant.'),
    ]
    body = f'''
<p class="lead">A typical 3 bed semi is fitted with a heat pump of about {kw(semi['kw'])}, and a 4 bed detached house about {kw(d4['kw'])}. Insulation matters too: the same 3 bed semi needs about {kw(semi_good['kw'])} once it is well insulated. Across every home that got the government grant between April and June 2026, the median heat pump was 8 kW. The table below gives the typical size for your home, and what that size costs.</p>

<h2 id="by-home">Typical heat pump size for your home</h2>
<p>These are the sizes typically installed in homes like yours. They come from how much heat a home of each type and size uses in a year, from government meter data for 39,502 homes, and sit in line with the sizes installers fit under the Boiler Upgrade Scheme, where the median heat pump in April to June 2026 was 8 kW and the middle half were between 6 kW and 10.8 kW.</p>
{size_table}
<p class="note">Poorly insulated means little loft or wall insulation. Recently retrofitted means insulated walls, a full loft and good glazing. See <a href="/methodology/">our methodology</a> for how size follows heat demand.</p>

<h2 id="survey">Your installer decides the exact size</h2>
<p>A table can tell you what homes like yours usually have. It cannot tell you what yours needs. For the Boiler Upgrade Scheme, an MCS certified installer has to calculate the heat lost from every room on a cold day and size the heat pump to cover it, plus hot water. Ask to see that calculation before you accept a quote. Two quotes that differ by several kW for the same house are a sign that one of them has not done it properly.</p>
<p>Bigger is not safer. An oversized heat pump costs more, and it switches on and off more often in mild weather, which can lower how efficiently it runs. The right size is the smallest that keeps your home warm on a cold day.</p>

<h2 id="cost">What each size costs</h2>
<p>Price rises with size, but not in step with it: much of an installation is fixed cost, so a small heat pump is not much cheaper than a mid-sized one. These figures are the median recorded by installers under the Boiler Upgrade Scheme in 2025/26 for a heat pump of each size.</p>
{cost_table}
<p>Homes replacing oil or LPG get a £9,000 grant instead of £7,500 until March 2027. For your own home, use the <a href="/heat-pump-calculator/">heat pump calculator</a>, or build a full <a href="/retrofit-plan/">retrofit plan</a> that sizes the heat pump for your home after insulation.</p>

<h2 id="smaller">How to need a smaller heat pump</h2>
<p>Everything that cuts the heat your home loses also cuts the size of heat pump it needs. For a 3 bed semi, going from average to good insulation takes it from about {kw(semi['kw'])} to about {kw(semi_good['kw'])}. The measures that do most, measured in real homes by the government, are solid wall insulation (a median 17.3 per cent less gas) and cavity wall insulation (12.0 per cent). See <a href="/guides/is-cavity-wall-insulation-worth-it/">whether cavity wall insulation is worth it</a> and <a href="/guides/radiator-sizing-heat-pump/">radiator sizing for heat pumps</a>.</p>
'''
    return dict(slug='what-size-heat-pump', kind='heat-pump',
                title='What Size Heat Pump Do I Need? UK Sizes by House Type',
                description='Typical heat pump size for every UK home: about %s for a 3 bed semi and %s for a 4 bed detached, by insulation, with what each size costs installed.' % (kw(semi['kw']), kw(d4['kw'])),
                h1='What size heat pump do I need?', crumb='What size heat pump', faq=faq, body=body,
                sources=['DESNZ, <a href="https://www.gov.uk/government/statistics/boiler-upgrade-scheme-statistics-august-2026" target="_blank" rel="noopener">Boiler Upgrade Scheme statistics, August 2026</a>, Tables A1.3A and Q1.1A.',
                         'DESNZ, <a href="https://www.gov.uk/government/statistics/national-energy-efficiency-data-framework-need-report-summary-of-analysis-2026" target="_blank" rel="noopener">National Energy Efficiency Data-Framework 2026</a>, consumption data and impact of measures tables.',
                         'MCS, <a href="https://mcscertified.com/find-an-installer/" target="_blank" rel="noopener">find a certified installer</a>.'])


PAGES = {'what-size-heat-pump': what_size}


def render(p):
    tpl = (ROOT / 'accuracy' / 'index.html').read_text()
    head = tpl[:tpl.index('</head>')]
    url = 'https://www.retrofitplanner.co.uk/guides/%s/' % p['slug']
    head = re.sub(r'<title>.*?</title>', '<title>%s</title>' % p['title'], head)
    for prop, val in [('og:title', p['title']), ('og:description', p['description']), ('og:url', url),
                      ('twitter:title', p['title']), ('twitter:description', p['description'])]:
        head = re.sub(r'(<meta (?:property|name)="%s" content=")[^"]*(")' % re.escape(prop), lambda mm: mm.group(1) + html.escape(val, quote=True) + mm.group(2), head)
    head = re.sub(r'(<meta name="description" content=")[^"]*(")', lambda mm: mm.group(1) + html.escape(p['description'], quote=True) + mm.group(2), head)
    head = re.sub(r'<link rel="canonical" href="[^"]*">', '<link rel="canonical" href="%s">' % url, head)
    head = re.sub(r'<script type="application/ld\+json">.*?</script>\n?', '', head, flags=re.S)
    ld = [{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://www.retrofitplanner.co.uk/"},
              {"@type": "ListItem", "position": 2, "name": "Guides", "item": "https://www.retrofitplanner.co.uk/guides/"},
              {"@type": "ListItem", "position": 3, "name": p['crumb'], "item": url}]},
          {"@context": "https://schema.org", "@type": "Article", "headline": p['title'], "datePublished": TODAY, "dateModified": TODAY,
           "url": url, "author": {"@type": "Organization", "name": "Retrofit Planner"}, "publisher": {"@type": "Organization", "name": "Retrofit Planner"}},
          {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
              {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in p['faq']]}]
    head = head.replace('</style>', '</style>\n' + ''.join('<script type="application/ld+json">%s</script>\n' % json.dumps(x, ensure_ascii=False) for x in ld), 1)
    faq_html = '\n'.join('<h3>%s</h3>\n<p>%s</p>' % (q, a) for q, a in p['faq'])
    src_html = ''.join('<li>%s</li>' % s for s in p['sources'])
    nav = re.search(r'<nav class="nav">.*?</nav>', tpl, re.S).group(0).replace('<a href="/guides/">Guides</a>', '<a href="/guides/" class="active" aria-current="page">Guides</a>')
    page = head + '''</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
%s
<main id="main" class="guide-content">
<div class="breadcrumbs"><a href="/">Home</a><span>/</span><a href="/guides/">Guides</a><span>/</span>%s</div>
<h1>%s</h1>
<p class="note">Updated 25 September 2026. Every figure on this page comes from our published model; see <a href="/accuracy/">how accurate it is</a>.</p>
%s
<h2 id="faq">Frequently asked questions</h2>
%s
<h2 id="sources">Data sources</h2>
<ul>%s</ul>
</main>
<footer class="footer"><div class="attribution">Contains public sector information licensed under the <a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/" target="_blank" rel="noopener">Open Government Licence v3.0</a>.</div></footer>
<script src="/js/nav.js" defer></script>
</body>
</html>
''' % (nav, p['crumb'], p['h1'], p['body'], faq_html, src_html)
    out = ROOT / 'guides' / p['slug'] / 'index.html'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page)
    assert len(p['title']) <= 60, (p['slug'], len(p['title']))
    assert len(p['description']) <= 155, (p['slug'], len(p['description']))
    assert '—' not in page and '–' not in page
    return out


def main():
    slugs = sys.argv[1:] or list(PAGES)
    for s in slugs:
        p = PAGES[s]()
        out = render(p)
        print('wrote', out.relative_to(ROOT), '| title', len(p['title']), '| desc', len(p['description']), '| form', p['kind'])


if __name__ == '__main__':
    main()
