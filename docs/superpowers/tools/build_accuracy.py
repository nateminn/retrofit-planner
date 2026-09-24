#!/usr/bin/env python3
"""Build /accuracy/: the model tested against measured data, before and after.

Every figure in the tables is computed here, from the old model (docs/model-v1.js, the
heat model as it stood before 24 September 2026), the current js/heat-model.js, and the
published source values written below with their table references. Re-run after any
model change; the page must never be edited by hand.

Usage: python3 docs/superpowers/tools/build_accuracy.py
"""
import json, re, subprocess, pathlib, html

ROOT = pathlib.Path(__file__).resolve().parents[3]
GAS_P, ELEC_P, HPT_P = 0.0797, 0.2632, 0.18

# Boiler Upgrade Scheme statistics, August 2026 release, Table A1.3A: 2025/26 median
# installed cost of air source heat pumps by capacity band, with the number of installs.
BUS = [('4 to 6 kW', 11494, 4206), ('6 to 8 kW', 12164, 8054), ('8 to 10 kW', 12686, 8526),
       ('10 to 12 kW', 13943, 3994), ('12 to 14 kW', 15365, 2824), ('14 to 16 kW', 15496, 1245),
       ('16 to 18 kW', 14817, 956)]
BUS_ALL = (13021, 30590)
# Electrification of Heat final report, Table 1.2, 428 air source heat pumps, SPFH4.
EOH = {'q1': 2.55, 'median': 2.78, 'q3': 3.05, 'n': 428, 'spfh2': 2.93}
# NEED Impact of Measures 2026, Table 1, median measured gas saving.
NEED = [('Cavity wall insulation', 0.1198, 2191, 'cavity'), ('Solid wall insulation', 0.1728, 2411, 'solid'),
        ('Loft insulation (mostly top-ups)', 0.0321, 1486, 'loft')]
# The insulation calculator's figures before the change, for a 3 bed semi on gas.
INSULATION_BEFORE = {'cavity': 215, 'solid': 340, 'loft': 120}

JS = """global.window={};require(%r);const H=window.RP_HEAT;const o={};
for(const [t,b] of %s){o[t+'|'+b]={heat:H.heatDemand(t,b,'average'),gas:H.gasKwh(t,b,'average'),install:H.heatPumpInstall(t,b,'average'),
kw:H.heatPumpKw?H.heatPumpKw(t,b,'average'):null,range:H.heatPumpInstallRange?H.heatPumpInstallRange(t,b,'average'):null,
cop:{poor:H.cop('poor'),average:H.cop('average'),good:H.cop('good'),excellent:H.cop('excellent')}};}
console.log(JSON.stringify(o));"""
HOMES = [('flat', 2, '2 bed flat'), ('mid-terrace', 2, '2 bed mid-terrace'), ('end-terrace', 3, '3 bed end-terrace'),
         ('semi', 3, '3 bed semi'), ('detached', 3, '3 bed detached'), ('detached', 4, '4 bed detached'),
         ('detached', 5, '5 bed detached')]


def model(path):
    out = subprocess.run(['node', '-e', JS % (str(path), json.dumps([[t, b] for t, b, _ in HOMES]))],
                         capture_output=True, text=True, cwd=ROOT)
    if out.returncode:
        raise SystemExit(out.stderr)
    return json.loads(out.stdout)


def gbp(v):
    return '£' + f'{round(v):,}'


def band_median(kw):
    lo = int(kw // 2 * 2) if kw >= 4 else 4
    for label, med, n in BUS:
        a, b = [int(x) for x in label.replace(' kW', '').split(' to ')]
        if a <= kw < b:
            return label, med, n
    return BUS[-1]


def main():
    old = model(ROOT / 'docs' / 'model-v1.js')
    new = model(ROOT / 'js' / 'heat-model.js')
    semi_old, semi_new = old['semi|3'], new['semi|3']

    # Efficiency table
    eff_rows = ''
    labels = [('poor', 'Poor', 'lower quartile, %.2f' % EOH['q1']), ('average', 'Average', 'median, %.2f' % EOH['median']),
              ('good', 'Good', 'upper quartile, %.2f' % EOH['q3']), ('excellent', 'Excellent', 'about the 90th percentile')]
    for key, name, measured in labels:
        eff_rows += '<tr><th scope="row">%s</th><td>%s</td><td>%s</td><td>%s</td></tr>' % (
            name, '%.1f' % semi_old['cop'][key], '%.2f' % semi_new['cop'][key], measured)
    hp_before = semi_old['heat'] / semi_old['cop']['average']
    hp_after = semi_new['heat'] / semi_new['cop']['average']

    # Installed cost table
    cost_rows = ''
    gaps = []
    for t, b, label in HOMES:
        o, n = old['%s|%d' % (t, b)], new['%s|%d' % (t, b)]
        band, med, cnt = band_median(n['kw'])
        gaps.append(n['install'] - o['install'])
        cost_rows += '<tr><th scope="row">%s</th><td>%g kW</td><td>%s</td><td>%s (%s, %s homes)</td><td>%s</td><td>%s to %s</td></tr>' % (
            label, n['kw'], gbp(o['install']), gbp(med), band, f'{cnt:,}', gbp(n['install']), gbp(n['range'][0]), gbp(n['range'][1]))

    # Insulation table, 3 bed semi on gas at average insulation
    gas = semi_new['gas']
    ins_rows = ''
    for name, pct, n, key in NEED:
        measured = gas * pct * GAS_P
        ins_rows += '<tr><th scope="row">%s</th><td>%s a year</td><td>%s a year (%.1f%%, %s homes)</td></tr>' % (
            name, gbp(INSULATION_BEFORE[key]), gbp(measured), pct * 100, f'{n:,}')

    # The counts in the checks section come from the checks themselves, not from memory.
    mc = (ROOT / 'docs/superpowers/tools/model_check.py').read_text()
    mc_basis = mc[mc.index('BASIS = {'):]
    mc_guides = len(re.findall(r"^\s*'[a-z0-9-]+':", mc_basis[:mc_basis.index('\n}\n')], re.M))
    tc_out = subprocess.run(['python3', 'docs/superpowers/tools/table_check.py'], cwd=ROOT, capture_output=True, text=True).stdout
    tc_cells = int(re.search(r'(\d+) table cells checked', tc_out).group(1))
    tc_src = (ROOT / 'docs/superpowers/tools/table_check.py').read_text()
    tc_tables = len(re.findall(r'dict\(page=', tc_src[tc_src.index('SPECS = ['):tc_src.index('INLINE = [')]))
    page = TEMPLATE.format(
        mc_guides=mc_guides, tc_cells=tc_cells, tc_tables=tc_tables,
        eff_rows=eff_rows, cost_rows=cost_rows, ins_rows=ins_rows,
        hp_before=gbp(hp_before * ELEC_P), hp_after=gbp(hp_after * ELEC_P),
        hpt_before=gbp(hp_before * HPT_P), hpt_after=gbp(hp_after * HPT_P),
        gap_lo=gbp(min(gaps)), gap_hi=gbp(max(gaps)),
        semi_old_install=gbp(semi_old['install']), semi_new_install=gbp(semi_new['install']),
        semi_old_after=gbp(max(0, semi_old['install'] - 7500)), semi_new_after=gbp(max(0, semi_new['install'] - 7500)),
        bus_all=gbp(BUS_ALL[0]), bus_n=f'{BUS_ALL[1]:,}', eoh_n=EOH['n'], eoh_median='%.2f' % EOH['median'],
        eoh_q1='%.2f' % EOH['q1'], eoh_q3='%.2f' % EOH['q3'], eoh_spfh2='%.2f' % EOH['spfh2'],
        old_avg='%.1f' % semi_old['cop']['average'],
        pct_eff=round((semi_old['cop']['average'] / EOH['median'] - 1) * 100),
    )
    head = HEAD
    out = ROOT / 'accuracy' / 'index.html'
    out.parent.mkdir(exist_ok=True)
    out.write_text(head + page)
    print('wrote', out.relative_to(ROOT))


HEAD = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>How Accurate Are Our Figures? Tested Against Real Homes</title>
<meta name="description" content="We tested our heat pump costs, running costs and insulation savings against government data from real installations. What matched, what did not, what changed.">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://www.retrofitplanner.co.uk/accuracy/">
<meta property="og:title" content="How Accurate Are Our Figures? Tested Against Real Homes">
<meta property="og:description" content="We tested our heat pump costs, running costs and insulation savings against government data from real installations. What matched, what did not, what changed.">
<meta property="og:url" content="https://www.retrofitplanner.co.uk/accuracy/">
<meta property="og:type" content="article">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="How Accurate Are Our Figures? Tested Against Real Homes">
<meta name="twitter:description" content="We tested our heat pump costs, running costs and insulation savings against government data from real installations. What matched, what did not, what changed.">
<meta property="og:site_name" content="Retrofit Planner">
<link rel="icon" type="image/x-icon" href="/favicon.ico"><link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png"><link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png"><link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png"><link rel="manifest" href="/site.webmanifest">
<link rel="stylesheet" href="/css/style.css">
<style>
.guide-content{max-width:760px;margin:0 auto;padding:0 24px 60px}.guide-content h1{font-family:var(--font-display);font-size:2rem;font-weight:700;letter-spacing:-0.03em;line-height:1.2;margin-bottom:16px}.guide-content h2{font-family:var(--font-display);font-size:1.4rem;font-weight:700;margin:40px 0 12px}.guide-content h3{font-size:1.05rem;font-weight:600;margin:24px 0 8px}.guide-content p,.guide-content li{line-height:1.7;color:var(--color-text-secondary)}.guide-content p{margin:0 0 16px}.guide-content ul{padding-left:22px;margin:0 0 16px}
.lead{font-size:1.1rem;color:var(--color-text)!important}
.data-table{width:100%;border-collapse:collapse;margin:16px 0 8px;font-size:.9rem}.data-table th,.data-table td{text-align:left;padding:10px 12px;border-bottom:1px solid var(--color-border);vertical-align:top}.data-table thead th{background:var(--color-surface-alt);font-weight:600;font-size:.8rem;text-transform:uppercase;letter-spacing:.03em;border-bottom:2px solid var(--color-border)}
.tblwrap{overflow-x:auto;-webkit-overflow-scrolling:touch}
.verdict{background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-md);padding:20px 24px;margin:24px 0}.verdict h2{margin-top:0!important;font-size:1.15rem!important}.verdict li{margin-bottom:6px}
.note{font-size:.85rem;color:var(--color-text-tertiary)!important}
</style>
<script type="application/ld+json">{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://www.retrofitplanner.co.uk/"}, {"@type": "ListItem", "position": 2, "name": "How accurate are our figures?", "item": "https://www.retrofitplanner.co.uk/accuracy/"}]}</script>
<script type="application/ld+json">{"@context": "https://schema.org", "@type": "Article", "headline": "How Accurate Are Our Figures? Tested Against Real Homes", "datePublished": "2026-09-25", "dateModified": "2026-09-25", "url": "https://www.retrofitplanner.co.uk/accuracy/", "author": {"@type": "Organization", "name": "Retrofit Planner"}, "publisher": {"@type": "Organization", "name": "Retrofit Planner"}}</script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-4QMWG6G2WL"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('consent','default',{ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied',analytics_storage:'denied'});gtag('js',new Date());gtag('config','G-4QMWG6G2WL');</script>
<link rel="preload" href="/fonts/fraunces-normal-2.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/plus-jakarta-sans-normal-4.woff2" as="font" type="font/woff2" crossorigin>
</head>
'''

TEMPLATE = '''<body>
<a class="skip-link" href="#main">Skip to content</a>
<nav class="nav"><div class="nav-inner"><a href="/" class="nav-logo">Retrofit Planner</a><ul class="nav-links"><li><a href="/heat-pump-calculator/">Heat Pump</a></li><li><a href="/insulation-calculator/">Insulation</a></li><li><a href="/epc-calculator/">EPC Rating</a></li><li><a href="/solar-calculator/">Solar Panels</a></li><li><a href="/grants/">Grants</a></li><li><a href="/guides/">Guides</a></li></ul></div></nav>
<main id="main" class="guide-content">
<div class="breadcrumbs"><a href="/">Home</a><span>/</span>How accurate are our figures?</div>
<h1>How accurate are our figures?</h1>
<p class="lead">Every figure on this site comes from one published model. On 24 September 2026 we tested that model against the largest sets of measured data available for UK homes. Two parts of it were wrong, and a third, our insulation savings, was far more optimistic than what homes actually saw. We changed all three. This page shows what we tested, what we found and what we changed.</p>

<div class="verdict">
<h2>The short version</h2>
<ul>
<li><strong>How much heat a home uses:</strong> built from and checked against government meter data for 39,502 gas heated homes. Within 0.3 per cent of the published medians for 2 to 5 bedroom homes.</li>
<li><strong>Heat pump efficiency:</strong> our average of {old_avg} was {pct_eff} per cent above the {eoh_median} measured across {eoh_n} real heat pumps. Now matched to the measurements.</li>
<li><strong>Heat pump installed cost:</strong> {gap_lo} to {gap_hi} below what installers recorded for the same size of heat pump across {bus_n} grant funded installations. Now matched by size.</li>
<li><strong>Insulation savings:</strong> our insulation calculator showed two to four times what homes measurably saved. It now shows the measured savings.</li>
<li><strong>Not yet tested:</strong> whether our figure for one particular home matches that home's own bills and quotes. That needs metered data from real households, and we say so wherever it matters.</li>
</ul>
</div>

<h2 id="demand">How much heat a home uses</h2>
<p>The model starts from how much gas a home burns in a year. That comes from the government's National Energy Efficiency Data-Framework (NEED), which links meter readings to property records: 39,502 gas heated homes with 2024 consumption, fitted by property type and floor area. We then checked the result against NEED's own published median gas use by number of bedrooms. It lands within 0.3 per cent for 2 to 5 bedrooms and 3.3 per cent for 1 bedroom.</p>
<p>An honest caveat: this is a calibration, not an independent test, because the checking figures come from the same data. It shows the model reproduces what the typical home of each kind uses. It does not show how close it gets for one particular home, which varies a great deal with how people heat.</p>

<h2 id="efficiency">Heat pump efficiency</h2>
<p>A heat pump's running cost depends on its seasonal efficiency: how many units of heat it delivers for each unit of electricity over a year. We had assumed 2.6 to 3.4 depending on how well the home is insulated. The government funded Electrification of Heat trial measured {eoh_n} air source heat pumps in real homes over a full year. Measured across the whole system, including the immersion heater, backup heater and pumps, which is what a household pays for, the median was {eoh_median}, and the middle half of homes sat between {eoh_q1} and {eoh_q3}.</p>
<div class="tblwrap" tabindex="0" role="region" aria-label="Heat pump efficiency, before and after"><table class="data-table"><thead><tr><th scope="col">Insulation</th><th scope="col">We used</th><th scope="col">We now use</th><th scope="col">Measured position</th></tr></thead><tbody>{eff_rows}</tbody></table></div>
<p>For a 3 bed semi with average insulation, that moves the yearly heat pump running cost from {hp_before} to {hp_after} on a standard tariff, and from {hpt_before} to {hpt_after} on an 18p heat pump tariff. An independent analysis of Ofgem's heat pump data, cited in the same report, found a median of 2.74 on the same measure for heat pumps installed from 2022 onwards.</p>

<h2 id="cost">Heat pump installed cost</h2>
<p>Every grant funded heat pump in England and Wales is recorded with the price the installer charged. The government publishes the median by size of heat pump: {bus_all} across {bus_n} air source heat pumps in 2025/26, including the system, labour and VAT, before the grant. We compared our figure for each home with the median for a heat pump of the size our model gives it.</p>
<div class="tblwrap" tabindex="0" role="region" aria-label="Heat pump installed cost, before and after"><table class="data-table"><thead><tr><th scope="col">Home</th><th scope="col">Size</th><th scope="col">We used</th><th scope="col">Recorded median, nearest size band</th><th scope="col">We now use</th><th scope="col">Middle half of installs</th></tr></thead><tbody>{cost_rows}</tbody></table></div>
<p class="note">We read between the size bands rather than rounding to one, so a 6 kW heat pump sits between the 4 to 6 kW and 6 to 8 kW medians. The 16 to 18 kW band has a lower median than the 14 to 16 kW band, on a smaller sample of 956 homes, so we read past it to keep cost rising with size. The middle half of installs is the scheme's own lower and upper quartile, scaled to each median.</p>
<p>Our figures were too low across the board, by the most for small homes, because much of the cost of an install is fixed and does not shrink with the house. For a 3 bed semi the calculator's figure moves from {semi_old_install} to {semi_new_install}, and the cost after the £7,500 grant from {semi_old_after} to {semi_new_after}. Homes replacing oil or LPG now get the £9,000 grant available to them until March 2027.</p>

<h2 id="insulation">Insulation savings</h2>
<p>NEED also measures what homes saved after insulation, by comparing their gas use before and after against similar homes that had nothing done. Those measured savings are much lower than the modelled figures most calculators use, including ours, because many homes were under-heated before and take part of the gain as warmth rather than a lower bill.</p>
<div class="tblwrap" tabindex="0" role="region" aria-label="Insulation savings for a 3 bed semi on gas, before and after"><table class="data-table"><thead><tr><th scope="col">Measure, 3 bed semi on gas</th><th scope="col">We showed</th><th scope="col">Measured median saving</th></tr></thead><tbody>{ins_rows}</tbody></table></div>
<p>The insulation calculator now shows what homes like yours typically saved, and says plainly that a home heated the same way before and after can save more. Its installation costs now follow the Energy Saving Trust's 2026 figures, which were well above ours.</p>

<h2 id="untested">What we have not tested yet</h2>
<ul>
<li><strong>Your home against your bills.</strong> Every figure here describes the typical home of its kind. How close it gets for a particular house depends on how that household heats it, and testing that needs metered data from real homes, shared with consent.</li>
<li><strong>The EPC estimator.</strong> It is a simple points model, not an assessment, and we have not compared it with lodged certificates.</li>
<li><strong>Solar generation.</strong> We use the European Commission's PVGIS model for generation. NEED measured a median 12.2 per cent fall in electricity bought after solar was fitted, which we have not yet reconciled with our figures.</li>
</ul>

<h2 id="checks">How we keep the site in line with the model</h2>
<p>The model is one readable file, <a href="/js/heat-model.js">heat-model.js</a>, and the <a href="/methodology/">methodology</a> explains each step. Before any change goes live, automated checks read the heat demand stated on {mc_guides} guides and {tc_cells} cells in {tc_tables} property tables and compare each one with the model. A page that disagrees fails the same check as a broken link.</p>

<h2 id="sources">Sources</h2>
<ul>
<li>Department for Energy Security and Net Zero, <a href="https://www.gov.uk/government/statistics/boiler-upgrade-scheme-statistics-august-2026" target="_blank" rel="noopener">Boiler Upgrade Scheme statistics, August 2026</a>, Tables A1.3A and Q1.1A, published 24 September 2026.</li>
<li>Energy Systems Catapult for the Department for Energy Security and Net Zero, <a href="https://esc-production-2021.s3.eu-west-2.amazonaws.com/wp-content/uploads/2024/12/18093557/EoH-Heat-Pump-Performance-Data-Analysis-Report.pdf" target="_blank" rel="noopener">Electrification of Heat Demonstration Project: Heat Pump Performance Data Analysis Report</a>, December 2024, Tables 1.2 and 8.1.</li>
<li>Department for Energy Security and Net Zero, <a href="https://www.gov.uk/government/statistics/national-energy-efficiency-data-framework-need-impact-of-measures-data-tables-2026" target="_blank" rel="noopener">NEED impact of measures data tables 2026</a>, Table 1, published 11 June 2026, and the <a href="https://www.gov.uk/government/statistics/national-energy-efficiency-data-framework-need-report-summary-of-analysis-2026" target="_blank" rel="noopener">NEED 2026 consumption data</a>.</li>
<li>GOV.UK, <a href="https://www.gov.uk/apply-boiler-upgrade-scheme" target="_blank" rel="noopener">Apply for the Boiler Upgrade Scheme</a>, and <a href="https://www.gov.uk/government/news/record-number-of-heating-oil-households-apply-for-a-heat-pump" target="_blank" rel="noopener">the £9,000 grant for oil and LPG homes</a>, 27 August 2026.</li>
<li>Energy Saving Trust, <a href="https://energysavingtrust.org.uk/advice/cavity-wall-insulation/" target="_blank" rel="noopener">cavity wall</a>, <a href="https://energysavingtrust.org.uk/advice/solid-wall-insulation/" target="_blank" rel="noopener">solid wall</a> and <a href="https://energysavingtrust.org.uk/advice/roof-and-loft-insulation/" target="_blank" rel="noopener">loft insulation</a> advice pages, updated 10 February, 18 June and 8 May 2026.</li>
</ul>
<p class="note">Tested 24 September 2026. When a source updates, we re-run the comparison and this page changes with it.</p>
</main>
<footer class="footer"><div class="attribution">Contains public sector information licensed under the <a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/" target="_blank" rel="noopener">Open Government Licence v3.0</a>.</div></footer>
<script src="/js/nav.js" defer></script>
</body>
</html>
'''

if __name__ == '__main__':
    main()
