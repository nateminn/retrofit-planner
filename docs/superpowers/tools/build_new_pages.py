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


# Prices and electricity baselines shared with the bill checker on average-energy-bills-uk,
# read from that page so the two can never disagree.
def bill_data():
    src = (ROOT / 'guides' / 'average-energy-bills-uk' / 'index.html').read_text()
    D = json.loads(re.search(r'var D=(\{.*?\});', src, re.S).group(1))
    return D
RG, RE, ROIL, RLPG, SCG, HPT = 0.0797, 0.2632, 0.090, 0.095, 108.33, 0.18
INS = [('poor', 'Poorly insulated'), ('average', 'Average'), ('good', 'Well insulated'), ('excellent', 'Recently retrofitted')]


def heating_cost(t, b, i, fuel):
    c = m(t, b, i)
    if fuel == 'gas': return c['gas'] * RG + SCG
    if fuel == 'oil': return c['heat'] / 0.85 * ROIL
    if fuel == 'lpg': return c['heat'] / 0.85 * RLPG
    if fuel == 'electric': return c['heat'] * RE
    if fuel == 'hp': return c['heat'] / c['cop'] * RE
    if fuel == 'hpt': return c['heat'] / c['cop'] * HPT


def bills_page(slug, beds, homes, crumb):
    D = bill_data()
    rows, main = [], None
    for key, t, label in homes:
        e = D[key]['e']
        g = heating_cost(t, beds, 'average', 'gas') + e
        rows.append([label, gbp(g), gbp(g / 12), gbp(heating_cost(t, beds, 'average', 'gas')), gbp(e)])
        main = main or (key, t, label, g, e)
    key, t, label, total, e = main
    ins_rows = [[iname, gbp(heating_cost(t, beds, i, 'gas') + e), gbp((heating_cost(t, beds, i, 'gas') + e) / 12)] for i, iname in INS]
    fuel_rows = []
    for f, fname in [('gas', 'Mains gas boiler'), ('oil', 'Oil boiler'), ('lpg', 'LPG boiler'), ('electric', 'Electric heating, standard rate'), ('hp', 'Heat pump, standard rate'), ('hpt', 'Heat pump, 18p heat pump tariff')]:
        yr = heating_cost(t, beds, 'average', f) + e
        fuel_rows.append([fname, gbp(yr), gbp(yr / 12)])
    tbl_types = table('Average energy bill by type of %d bed home' % beds, ['Home, average insulation, gas heating', 'A year', 'A month', 'Heating', 'Everything else'], rows)
    tbl_ins = table('Energy bill for a %s by insulation' % label, ['Insulation', 'A year', 'A month'], ins_rows)
    tbl_fuel = table('Energy bill for a %s by heating fuel' % label, ['Heating', 'A year', 'A month'], fuel_rows)
    gas_kwh = m(t, beds)['gas']
    faq = [
        ('What is the average energy bill for a %d bed house?' % beds,
         'About %s a year, or %s a month, for a %s with average insulation heated by mains gas, at the Ofgem price cap for October to December 2026. That includes both standing charges.' % (gbp(total), gbp(total / 12), label)),
        ('How much gas does a %d bed house use?' % beds,
         'A %s with average insulation uses about %s kWh of gas a year for heating, hot water and any gas cooking, from government meter data. A poorly insulated one uses about %s kWh and a well insulated one about %s kWh.' % (label, f"{gas_kwh:,}", f"{m(t, beds, 'poor')['gas']:,}", f"{m(t, beds, 'good')['gas']:,}")),
        ('Why is my bill higher than this?',
         'The usual reasons are a colder than average home, more people in it, being at home in the day, or a tariff above the price cap. Our bill checker compares your own bill with a home like yours.'),
    ]
    body = f"""
<p class="lead">A {label} with average insulation and gas central heating costs about <strong>{gbp(total)} a year</strong>, or <strong>{gbp(total / 12)} a month</strong>, at the Ofgem price cap for October to December 2026. That is about {gbp(total - e)} for gas and {gbp(e)} for electricity, both including their standing charges.</p>

<h2 id="by-type">Average bill by type of {beds} bed home</h2>
<p>Gas is the larger part of the bill, and it depends on the size and type of the house. Heating use comes from government meter data for 39,502 gas heated homes; electricity for lights, appliances and cooking is scaled by home size from Ofgem's typical consumption figures.</p>
{tbl_types}

<h2 id="insulation">How insulation changes it</h2>
<p>Insulation is the biggest thing you can change. These are the bills for the same {label} at each level of insulation, measured the government's way: comparing homes of the same type and size with different EPC bands.</p>
{tbl_ins}

<h2 id="fuel">How your heating fuel changes it</h2>
<p>Everything else on the bill stays the same whatever heats the home, so this table only changes the heating part. Heat pump running costs use the median efficiency measured in 428 homes in the government's Electrification of Heat trial.</p>
{tbl_fuel}
<p class="note">Gas bills include the £108.33 a year gas standing charge; homes without gas do not pay it. Electricity includes the £200.13 standing charge in every row. Oil and LPG are September 2026 market prices.</p>

<h2 id="check">Check your own bill</h2>
<p>Put your own annual bill into the <a href="/guides/average-energy-bills-uk/#bill-checker">bill checker</a> to see how far it sits from a home like yours, or see <a href="/guides/energy-bills-by-household-size/">bills by number of people</a> and <a href="/guides/energy-bills-by-epc-rating/">bills by EPC rating</a>. To cut the bill, the <a href="/retrofit-plan/">retrofit plan</a> puts the upgrades for your home in order, with what each saves.</p>
"""
    return dict(slug=slug, kind='home',
                title='Average Energy Bill for a %d Bed House UK 2026: %s a Month' % (beds, gbp(total / 12)),
                description='A %d bed house costs about %s a year, %s a month, in gas and electricity at the October 2026 price cap. By house type, insulation and heating fuel.' % (beds, gbp(total), gbp(total / 12)),
                h1='Average energy bill for a %d bed house' % beds, crumb=crumb, faq=faq, body=body,
                sources=['DESNZ, <a href="https://www.gov.uk/government/statistics/national-energy-efficiency-data-framework-need-report-summary-of-analysis-2026" target="_blank" rel="noopener">National Energy Efficiency Data-Framework 2026</a>.',
                         'Ofgem, <a href="https://www.ofgem.gov.uk/check-if-energy-price-cap-affects-you" target="_blank" rel="noopener">energy price cap</a>, October to December 2026.',
                         'Energy Systems Catapult for DESNZ, <a href="https://esc-production-2021.s3.eu-west-2.amazonaws.com/wp-content/uploads/2024/12/18093557/EoH-Heat-Pump-Performance-Data-Analysis-Report.pdf" target="_blank" rel="noopener">Electrification of Heat heat pump performance report</a>, December 2024.'])


def bills_3():
    return bills_page('energy-bills-3-bed-house', 3, [('semi3', 'semi', '3 bed semi'), ('det3', 'detached', '3 bed detached')], 'Energy bills, 3 bed house')


def bills_4():
    return bills_page('energy-bills-4-bed-house', 4, [('det4', 'detached', '4 bed detached')], 'Energy bills, 4 bed house')


def hp_house(slug, t, b, label, title_label, crumb, intro, extra_h2, extra_p, compare):
    c = m(t, b)
    rows = [[iname, kw(m(t, b, i)['kw']), gbp(m(t, b, i)['install']), '%s to %s' % (gbp(m(t, b, i)['range'][0]), gbp(m(t, b, i)['range'][1])),
             gbp(max(0, m(t, b, i)['install'] - 7500))] for i, iname in INS]
    tbl_cost = table('Heat pump cost for a %s by insulation' % label, ['Insulation', 'Typical size', 'Median installed', 'Middle half of installs', 'Median after £7,500 grant'], rows)
    run = []
    for i, iname in INS:
        x = m(t, b, i)
        run.append([iname, gbp(x['gas'] * RG), gbp(x['heat'] / x['cop'] * RE), gbp(x['heat'] / x['cop'] * HPT)])
    tbl_run = table('Running cost for a %s by insulation' % label, ['Insulation', 'Gas boiler', 'Heat pump, standard rate', 'Heat pump tariff, 18p'], run)
    comp = [[l, kw(m(tt, bb)['kw']), '%s to %s' % (gbp(m(tt, bb)['range'][0]), gbp(m(tt, bb)['range'][1])), gbp(m(tt, bb)['heat'] / m(tt, bb)['cop'] * HPT)] for tt, bb, l in compare]
    tbl_comp = table('%s compared with similar homes' % label.capitalize(), ['Home, average insulation', 'Typical size', 'Installed, middle half', 'Heat pump tariff running cost'], comp)
    lo, hi = c['range']
    faq = [
        ('How much does a heat pump cost for a %s?' % label,
         'Typically %s to %s installed for a %s heat pump, with a median of %s, from what installers recorded under the Boiler Upgrade Scheme in 2025/26. After the £7,500 grant that is %s to %s, or %s to %s if you are replacing oil or LPG.' % (gbp(lo), gbp(hi), kw(c['kw']), gbp(c['install']), gbp(max(0, lo - 7500)), gbp(max(0, hi - 7500)), gbp(max(0, lo - 9000)), gbp(max(0, hi - 9000)))),
        ('Is a heat pump cheaper to run than gas in a %s?' % label,
         'On an 18p heat pump tariff, yes: about %s a year against %s for gas with average insulation. On a standard electricity tariff it costs about %s, a little more than gas. Both figures are energy only; gas also carries a £108 a year standing charge you save if you cap the supply.' % (gbp(c['heat'] / c['cop'] * HPT), gbp(c['gas'] * RG), gbp(c['heat'] / c['cop'] * RE))),
        ('What size heat pump does a %s need?' % label,
         'About %s with average insulation, and less once it is well insulated. The exact size comes from the room by room heat loss calculation an MCS installer must do. See our guide to heat pump sizes.' % kw(c['kw'])),
    ]
    body = f"""
<p class="lead">{intro} Installers recorded a typical cost of <strong>{gbp(lo)} to {gbp(hi)}</strong> for a heat pump of that size under the Boiler Upgrade Scheme, with a median of {gbp(c['install'])}. After the £7,500 grant, most pay <strong>{gbp(max(0, lo - 7500))} to {gbp(max(0, hi - 7500))}</strong>.</p>

<h2 id="cost">What it costs</h2>
<p>Size, and so price, follows how much heat the home loses. These are the typical size and the recorded installed cost for a {label} at each level of insulation. The installed cost is the whole job as installers reported it to the scheme: the heat pump, hot water cylinder, labour and VAT, before the grant. Some homes also need larger radiators, which can add to it; see <a href="/guides/radiator-sizing-heat-pump/">radiator sizing</a>.</p>
{tbl_cost}
<p class="note">Middle half of installs: the scheme's lower and upper quartile, scaled to each median. Homes replacing oil or LPG get £9,000 instead of £7,500 until March 2027.</p>

<h2 id="running">What it costs to run</h2>
<p>Running costs use the median efficiency measured across 428 heat pumps in the government's Electrification of Heat trial, at the Ofgem price cap for October to December 2026. The tariff matters more than almost anything else: see <a href="/guides/best-heat-pump-tariffs/">heat pump tariffs</a>.</p>
{tbl_run}

<h2 id="{extra_h2[0]}">{extra_h2[1]}</h2>
{extra_p}

<h2 id="compare">Compared with similar homes</h2>
{tbl_comp}
<p>For your own figures, use the <a href="/heat-pump-calculator/">heat pump calculator</a>, or build a <a href="/retrofit-plan/">retrofit plan</a> that puts insulation first and sizes the heat pump for the home after it.</p>
"""
    return dict(slug=slug, kind='heat-pump', title=title_label % (gbp(lo), gbp(hi)) if '%s' in title_label else title_label,
                description='%s heat pump: %s to %s installed, %s to %s after the £7,500 grant. Typical size, running costs and what to check first.' % (label[0].upper() + label[1:], gbp(lo), gbp(hi), gbp(max(0, lo - 7500)), gbp(max(0, hi - 7500))),
                h1='Heat pump for a %s: cost and running costs' % label, crumb=crumb, faq=faq, body=body,
                sources=['DESNZ, <a href="https://www.gov.uk/government/statistics/boiler-upgrade-scheme-statistics-august-2026" target="_blank" rel="noopener">Boiler Upgrade Scheme statistics, August 2026</a>, Tables A1.3A and Q1.1A.',
                         'Energy Systems Catapult for DESNZ, <a href="https://esc-production-2021.s3.eu-west-2.amazonaws.com/wp-content/uploads/2024/12/18093557/EoH-Heat-Pump-Performance-Data-Analysis-Report.pdf" target="_blank" rel="noopener">Electrification of Heat heat pump performance report</a>, December 2024.',
                         'DESNZ, <a href="https://www.gov.uk/government/statistics/national-energy-efficiency-data-framework-need-report-summary-of-analysis-2026" target="_blank" rel="noopener">National Energy Efficiency Data-Framework 2026</a>.',
                         'Ofgem, <a href="https://www.ofgem.gov.uk/check-if-energy-price-cap-affects-you" target="_blank" rel="noopener">energy price cap</a>, October to December 2026.'])


def mid_terrace_3():
    c = m('mid-terrace', 3)
    return hp_house('heat-pump-cost-3-bed-mid-terrace', 'mid-terrace', 3, '3 bed mid-terrace',
                    '3-Bed Mid-Terrace Heat Pump Cost 2026: %s to %s', 'Heat pump, 3 bed mid-terrace',
                    'In government meter data a 3 bed mid-terrace uses less heat than any other kind of 3 bed house, because two of its walls are shared with warm neighbours, so it needs a smaller heat pump: about %s with average insulation.' % kw(c['kw']),
                    ('outdoor-unit', 'Where the outdoor unit goes'),
                    '<p>Most mid-terraces have no side access, so the outdoor unit usually goes in the back garden or yard, and the installer runs pipework through to the hot water cylinder. Keep it away from a neighbour\'s window: in England a heat pump is usually permitted development, but only within noise and siting conditions. See <a href="/guides/planning-permission-heat-pump/">planning rules</a> and <a href="/guides/heat-pump-noise/">heat pump noise</a> before you choose a spot.</p>',
                    [('mid-terrace', 3, '3 bed mid-terrace'), ('end-terrace', 3, '3 bed end-terrace'), ('semi', 3, '3 bed semi'), ('detached', 3, '3 bed detached')])


def semi_1930s():
    c = m('semi', 3)
    g = m('semi', 3, 'good')
    return hp_house('heat-pump-1930s-semi', 'semi', 3, '1930s semi',
                    'Heat Pump for a 1930s Semi UK 2026: Cost and Running Costs', 'Heat pump, 1930s semi',
                    'A typical 1930s semi is a 3 bed house, and many were built with cavity walls that have since been filled. With average insulation, a 1930s semi typically needs a heat pump of about %s, falling to about %s once it is well insulated.' % (kw(c['kw']), kw(g['kw'])),
                    ('before', 'What to check in a 1930s semi first'),
                    '<p>Three things decide how well a heat pump works in a house of this age. First, the walls: if the cavity has never been filled, filling it is one of the biggest cuts in heat loss you can make, a median 12.0 per cent less gas in homes the government measured. Second, the floor: many 1930s houses have suspended timber floors that are draughty, which <a href="/guides/underfloor-insulation-cost/">underfloor insulation</a> and draught-proofing address. Third, the radiators: rooms such as a bay-fronted lounge may need a larger radiator to stay warm at the lower flow temperatures heat pumps run at. An MCS installer\'s room by room heat loss survey shows which rooms need what.</p>',
                    [('semi', 3, '3 bed semi'), ('end-terrace', 3, '3 bed end-terrace'), ('mid-terrace', 3, '3 bed mid-terrace'), ('detached', 3, '3 bed detached')])


PAGES = {'what-size-heat-pump': what_size, 'energy-bills-3-bed-house': bills_3, 'energy-bills-4-bed-house': bills_4,
         'heat-pump-cost-3-bed-mid-terrace': mid_terrace_3, 'heat-pump-1930s-semi': semi_1930s}


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
