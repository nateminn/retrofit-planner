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


# Electricity for lighting, appliances and cooking: the 2024 NEED median by bedrooms, read
# from js/bills.js so the energy bill calculator and these pages share one table.
def elec_bill(beds):
    js = (ROOT / 'js' / 'bills.js').read_text()
    kwh = dict((int(k), int(v)) for k, v in re.findall(r'(\d): (\d{4})', re.search(r'var ELEC_KWH = \{([^}]*)\}', js).group(1)))
    return kwh[min(5, beds)] * RE + 200.13


def elec_kwh(beds):
    js = (ROOT / 'js' / 'bills.js').read_text()
    return int(re.search(r'%d: (\d{4})' % min(5, beds), re.search(r'var ELEC_KWH = \{([^}]*)\}', js).group(1)).group(1))
import sys as _sys, os as _os; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import prices as _prices
RG, RE, ROIL, RLPG, SCG, HPT = _prices.GAS, _prices.ELEC, _prices.OIL, _prices.LPG, 108.33, _prices.HPT
TP = ('%.1f' % (HPT * 100)).rstrip('0').rstrip('.') + 'p'   # the tariff as the pages write it, e.g. 19.8p
INS = [('poor', 'Poorly insulated'), ('average', 'Average'), ('good', 'Well insulated'), ('excellent', 'Recently retrofitted')]


def heating_cost(t, b, i, fuel):
    c = m(t, b, i)
    if fuel == 'gas': return c['gas'] * RG + SCG
    if fuel == 'oil': return c['heat'] / 0.85 * ROIL
    if fuel == 'lpg': return c['heat'] / 0.85 * RLPG
    if fuel == 'electric': return c['heat'] * RE
    if fuel == 'hp': return c['heat'] / c['cop'] * RE
    if fuel == 'hpt': return c['heat'] / c['cop'] * HPT


def bills_page(slug, beds, homes, crumb, noun='house'):
    D = bill_data()
    rows, main = [], None
    for key, t, label in homes:
        e = elec_bill(beds)
        g = heating_cost(t, beds, 'average', 'gas') + e
        rows.append([label, gbp(g), gbp(g / 12), gbp(heating_cost(t, beds, 'average', 'gas')), gbp(e)])
        main = main or (key, t, label, g, e)
    key, t, label, total, e = main
    ins_rows = [[iname, gbp(heating_cost(t, beds, i, 'gas') + e), gbp((heating_cost(t, beds, i, 'gas') + e) / 12)] for i, iname in INS]
    fuel_rows = []
    for f, fname in [('gas', 'Mains gas boiler'), ('oil', 'Oil boiler'), ('lpg', 'LPG boiler'), ('electric', 'Electric heating, standard rate'), ('hp', 'Heat pump, standard rate'), ('hpt', 'Heat pump, %s heat pump tariff' % TP)]:
        yr = heating_cost(t, beds, 'average', f) + e
        fuel_rows.append([fname, gbp(yr), gbp(yr / 12)])
    tbl_types = table('Average energy bill by type of %d bed home' % beds, ['Home, average insulation, gas heating', 'A year', 'A month', 'Heating', 'Everything else'], rows)
    tbl_ins = table('Energy bill for a %s by insulation' % label, ['Insulation', 'A year', 'A month'], ins_rows)
    tbl_fuel = table('Energy bill for a %s by heating fuel' % label, ['Heating', 'A year', 'A month'], fuel_rows)
    gas_kwh = m(t, beds)['gas']
    faq = [
        ('What is the average energy bill for a %d bed %s?' % (beds, noun),
         'About %s a year, or %s a month, for a %s with average insulation heated by mains gas, at the Ofgem price cap for October to December 2026. That includes both standing charges.' % (gbp(total), gbp(total / 12), label)),
        ('How much gas does a %d bed %s use?' % (beds, noun),
         'A %s with average insulation uses about %s kWh of gas a year for heating, hot water and any gas cooking, from government meter data. A poorly insulated one uses about %s kWh and a well insulated one about %s kWh.' % (label, f"{gas_kwh:,}", f"{m(t, beds, 'poor')['gas']:,}", f"{m(t, beds, 'good')['gas']:,}")),
        ('Why is my bill higher than this?',
         'The usual reasons are a colder than average home, more people in it, being at home in the day, or a tariff above the price cap. Our bill checker compares your own bill with a home like yours.'),
    ]
    body = f"""
<p class="lead">A {label} with average insulation and gas central heating costs about <strong>{gbp(total)} a year</strong>, or <strong>{gbp(total / 12)} a month</strong>, at the Ofgem price cap for October to December 2026. That is about {gbp(total - e)} for gas and {gbp(e)} for electricity, both including their standing charges.</p>

<h2 id="by-type">Average bill by type of {beds} bed home</h2>
<p>{'Gas is the larger part of the bill' if (total - e) > e else 'Electricity is the larger part of the bill in a home this size'}, and gas use depends on the size and type of the home. Heating use comes from government meter data for 39,502 gas heated homes; electricity for lights, appliances and cooking is the 2024 median for homes with {beds} bedroom{'s' if beds > 1 else ''}, {elec_kwh(beds):,} kWh a year, from the same government data.</p>
{tbl_types}

<h2 id="insulation">How insulation changes it</h2>
<p>Insulation changes the heating part of the bill. These are the bills for the same {label} at each level of insulation, measured the government's way: comparing homes of the same type and size with different EPC bands.</p>
{tbl_ins}

<h2 id="fuel">How your heating fuel changes it</h2>
<p>Everything else on the bill stays the same whatever heats the home, so this table only changes the heating part. Heat pump running costs use the median efficiency measured in 428 homes in the government's Electrification of Heat trial.</p>
{tbl_fuel}
<p class="note">Gas bills include the £108.33 a year gas standing charge; homes without gas do not pay it. Electricity includes the £200.13 standing charge in every row. Oil is {ROIL * 100:.1f}p per kWh, the BoilerJuice UK average of 116.20p a litre on 25 September 2026, and oil prices move; LPG is {RLPG * 100:.1f}p per kWh, our assumption for a typical bulk contract.</p>

<h2 id="check">Check your own bill</h2>
<p>Put your own annual bill into the <a href="/energy-bill-calculator/">energy bill calculator</a> to see how far it sits from a home like yours, or see <a href="/guides/energy-bills-by-household-size/">bills by number of people</a> and <a href="/guides/energy-bills-by-epc-rating/">bills by EPC rating</a>. To cut the bill, the <a href="/retrofit-plan/">retrofit plan</a> puts the upgrades for your home in order, with what each saves.</p>
"""
    return dict(slug=slug, kind='home',
                title='Average Energy Bill for a %d Bed %s UK 2026: %s a Month' % (beds, noun.capitalize(), gbp(total / 12)),
                description='A %d bed %s costs about %s a year, %s a month, in gas and electricity at the October 2026 price cap. By home type, insulation and heating fuel.' % (beds, noun, gbp(total), gbp(total / 12)),
                h1='Average energy bill for a %d bed %s' % (beds, noun), crumb=crumb, faq=faq, body=body,
                sources=['DESNZ, <a href="https://www.gov.uk/government/statistics/national-energy-efficiency-data-framework-need-report-summary-of-analysis-2026" target="_blank" rel="noopener">National Energy Efficiency Data-Framework 2026</a>.',
                         'Ofgem, <a href="https://www.ofgem.gov.uk/your-energy-supply/your-energy-bill/energy-price-cap-and-standing-charges-explained" target="_blank" rel="noopener">energy price cap</a>, October to December 2026.',
                         'Energy Systems Catapult for DESNZ, <a href="https://esc-production-2021.s3.eu-west-2.amazonaws.com/wp-content/uploads/2024/12/18093557/EoH-Heat-Pump-Performance-Data-Analysis-Report.pdf" target="_blank" rel="noopener">Electrification of Heat trial, heat pump performance report</a>, December 2024.'])


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
    tbl_run = table('Running cost for a %s by insulation' % label, ['Insulation', 'Gas boiler', 'Heat pump, standard rate', 'Heat pump tariff, %s' % TP], run)
    comp = [[l, kw(m(tt, bb)['kw']), '%s to %s' % (gbp(m(tt, bb)['range'][0]), gbp(m(tt, bb)['range'][1])), gbp(m(tt, bb)['heat'] / m(tt, bb)['cop'] * HPT)] for tt, bb, l in compare]
    tbl_comp = table('%s compared with similar homes' % label.capitalize(), ['Home, average insulation', 'Typical size', 'Installed, middle half', 'Heat pump tariff running cost'], comp)
    lo, hi = c['range']
    faq = [
        ('How much does a heat pump cost for a %s?' % label,
         'Typically %s to %s installed for a %s heat pump, with a median of %s, from what installers recorded under the Boiler Upgrade Scheme in 2025/26. After the £7,500 grant that is %s to %s, or %s to %s if you are replacing oil or LPG.' % (gbp(lo), gbp(hi), kw(c['kw']), gbp(c['install']), gbp(max(0, lo - 7500)), gbp(max(0, hi - 7500)), gbp(max(0, lo - 9000)), gbp(max(0, hi - 9000)))),
        ('Is a heat pump cheaper to run than gas in a %s?' % label,
         'On a ' + TP + ' heat pump tariff, yes: about %s a year against %s for gas with average insulation. On a standard electricity tariff it costs about %s, a little more than gas. Both figures are energy only; gas also carries a £108 a year standing charge you save if you cap the supply.' % (gbp(c['heat'] / c['cop'] * HPT), gbp(c['gas'] * RG), gbp(c['heat'] / c['cop'] * RE))),
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
                         'Energy Systems Catapult for DESNZ, <a href="https://esc-production-2021.s3.eu-west-2.amazonaws.com/wp-content/uploads/2024/12/18093557/EoH-Heat-Pump-Performance-Data-Analysis-Report.pdf" target="_blank" rel="noopener">Electrification of Heat trial, heat pump performance report</a>, December 2024.',
                         'DESNZ, <a href="https://www.gov.uk/government/statistics/national-energy-efficiency-data-framework-need-report-summary-of-analysis-2026" target="_blank" rel="noopener">National Energy Efficiency Data-Framework 2026</a>.',
                         'Ofgem, <a href="https://www.ofgem.gov.uk/your-energy-supply/your-energy-bill/energy-price-cap-and-standing-charges-explained" target="_blank" rel="noopener">energy price cap</a>, October to December 2026.'])


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
                    '<p>Three things decide how well a heat pump works in a house of this age. First, the walls: if the cavity has never been filled, filling it is one of the biggest cuts in heat loss you can make, a median 12.0 per cent less gas in homes the government measured. Second, the floor: many 1930s houses have suspended timber floors that are draughty, which <a href="/guides/underfloor-insulation-cost/">underfloor insulation</a> and draught-proofing address. Third, the radiators: rooms such as a bay-fronted lounge may need a larger radiator to stay warm at the lower flow temperatures heat pumps run at. An MCS installer\'s room by room heat loss survey shows which rooms need what.</p><p>See also <a href="/guides/epc-rating-1930s-house/">the EPC rating of a 1930s house</a>.</p>',
                    [('semi', 3, '3 bed semi'), ('end-terrace', 3, '3 bed end-terrace'), ('mid-terrace', 3, '3 bed mid-terrace'), ('detached', 3, '3 bed detached')])


def bills_1():
    return bills_page('energy-bills-1-bed-flat', 1, [('flat1', 'flat', '1 bed flat')], 'Energy bills, 1 bed flat', noun='flat')


def bills_2():
    return bills_page('energy-bills-2-bed-house', 2, [('terrace2', 'mid-terrace', '2 bed terrace'), ('flat2', 'flat', '2 bed flat')], 'Energy bills, 2 bed home')


def bills_5():
    return bills_page('energy-bills-5-bed-house', 5, [('det5', 'detached', '5 bed detached')], 'Energy bills, 5 bed house')



# ------------------------------------------------------------------ insulation cost by house type
# Costs: js/insulation-costs.js (Energy Saving Trust, May and June 2026). Savings: the median
# fall in gas use measured after each measure (NEED Impact of Measures 2026, Table 1), applied
# to the home's gas use from js/heat-model.js at the October 2026 cap, the same basis as the
# cavity, loft and solid wall guides. Floors have no measured figure, so they carry the
# Trust's own modelled saving, labelled as such.
_INS_JS = """global.window={};require('./js/insulation-costs.js');console.log(JSON.stringify(window.RP_INS.costs));"""
IC = json.loads(subprocess.run(['node', '-e', _INS_JS], capture_output=True, text=True, cwd=ROOT).stdout)
PCT = {'loft': 0.0321, 'cavity': 0.1198, 'solid': 0.1728, 'loft+cavity': 0.0838}
FLOOR_SAVING = {'detached': 85, 'semi': 55, 'mid-terrace': 40, 'bungalow': 100}   # Trust, GB, July 2026 prices
EST_NAME = {'detached': 'detached house', 'semi': 'semi-detached house', 'mid-terrace': 'mid-terrace house',
            'end-terrace': 'semi-detached house', 'bungalow': 'detached bungalow', 'flat': 'mid-floor flat'}


def ins_saving(t, b, key):
    return m(t, b)['gas'] * PCT[key] * RG


def payback(cost, saving):
    y = cost / saving
    return 'Over 50 years' if y >= 50 else '%d years' % round(y)


def ins_page(slug, t, beds, main_beds, label, plural, crumb, notes):
    c = lambda k: IC[k][t]
    main = '%d bed %s' % (main_beds, label)
    sv = {k: ins_saving(t, main_beds, k) for k in ('loft', 'cavity', 'solid', 'loft+cavity')}
    rows = []
    loft_label = 'Loft insulation, bare loft to 270mm' + (' (top floor flat)' if t == 'flat' else '')
    rows.append([loft_label, gbp(c('loftBare')), 'More than ' + gbp(sv['loft']), 'Under ' + payback(c('loftBare'), sv['loft']).lower()])
    rows.append(['Loft insulation, top-up from 120mm' + (' (top floor flat)' if t == 'flat' else ''), gbp(c('loftTopUp')), gbp(sv['loft']), payback(c('loftTopUp'), sv['loft'])])
    rows.append(['Cavity wall insulation', gbp(c('cavity')), gbp(sv['cavity']), payback(c('cavity'), sv['cavity'])])
    rows.append(['Solid wall insulation, internal', gbp(IC['solidInternal']), gbp(sv['solid']), payback(IC['solidInternal'], sv['solid'])])
    rows.append(['Solid wall insulation, external', gbp(IC['solidExternal']), gbp(sv['solid']), payback(IC['solidExternal'], sv['solid'])])
    fs = FLOOR_SAVING.get(t)
    rows.append(['Suspended timber floor' + (' (ground floor flat)' if t == 'flat' else ''), '£1,400 to £2,500',
                 ('About %s (Trust estimate)' % gbp(fs)) if fs else 'Not published', ('%d to %d years' % (round(1400 / fs), round(2500 / fs))) if fs else 'Not published'])
    tbl = table('Insulation cost and saving for a %s' % main, ['Measure', 'Typical cost', 'Saving a year', 'Payback'], rows)
    brow = [['%d bed %s' % (b, label), gbp(ins_saving(t, b, 'loft')), gbp(ins_saving(t, b, 'cavity')), gbp(ins_saving(t, b, 'solid'))] for b in beds]
    tbl_beds = table('Measured saving a year by size of %s' % label, ['Home, heated by gas', 'Loft', 'Cavity walls', 'Solid walls'], brow)
    k_avg, k_good = m(t, main_beds)['kw'], m(t, main_beds, 'good')['kw']
    both = c('loftBare') + c('cavity')
    note_costs = ('Costs: Energy Saving Trust, typical professional installation before any grant: loft and cavity figures for a %s (updated 8 May 2026), '
                  'solid wall figures for a typical home (18 June 2026), suspended floors £1,400 to £2,500 depending on the house (19 May 2026). %s'
                  'Savings: the median fall in gas use measured in real homes after each measure (DESNZ NEED Impact of Measures 2026, Table 1: loft 3.2%%, cavity wall 12.0%%, solid wall 17.3%%), '
                  'applied to a %s with average insulation at the October 2026 cap price of 7.97p per kWh. The loft figure is the median across all loft jobs, most of them top-ups, so insulating a bare loft saves more. Floor savings are the Trust\'s own estimates. Payback is cost divided by the yearly saving, at full price. '
                  'Homes heated by oil, LPG or electricity save more in pounds.' % (EST_NAME[t], notes, main))
    faq = [
        ('How much does it cost to insulate a %s?' % label,
         ('About %s for cavity wall insulation in a mid-floor flat, up to %s for internal solid wall insulation, at Energy Saving Trust prices before any grant. A top floor flat can top up its loft from about %s.'
          % (gbp(c('cavity')), gbp(IC['solidInternal']), gbp(c('loftTopUp')))) if t == 'flat' else
         ('From about %s to top up the loft to %s for internal solid wall insulation, at Energy Saving Trust prices before any grant. Cavity wall insulation costs about %s for a %s.'
          % (gbp(c('loftTopUp')), gbp(IC['solidInternal']), gbp(c('cavity')), EST_NAME[t]))),
        ('Is cavity wall insulation worth it for a %s?' % label,
         'Homes that had it fitted used a median 12.0%% less gas, about %s a year for a %s on gas, so at about %s it takes %s to pay back at full price. It can be free through ECO4 for households on qualifying benefits, and it adds about 8 EPC points in our model.'
         % (gbp(sv['cavity']), main, gbp(c('cavity')), payback(c('cavity'), sv['cavity']).lower())),
        ('Can I get insulation for my %s free?' % label,
         'Possibly. ECO4 funds insulation for households on qualifying benefits until 31 December 2026, in homes rated D to G if owned or E to G if privately rented, and in England a Warm Homes: Local Grant through the council can help households on lower incomes. Insulation carries 0% VAT until 31 March 2027.'),
    ]
    lead = (f"Insulating a flat costs about <strong>{gbp(c('cavity'))}</strong> for cavity walls, the Energy Saving Trust's figure for a mid-floor flat, up to <strong>{gbp(IC['solidInternal'])}</strong> or more for solid walls. A top floor flat can also insulate its loft from about {gbp(c('loftTopUp'))}, and homes that had cavity wall insulation fitted used a median 12.0% less gas."
            if t == 'flat' else
            f"Insulating a {label} costs from about <strong>{gbp(c('loftTopUp'))}</strong> to top up the loft to <strong>{gbp(IC['solidInternal'])}</strong> or more for solid walls. Cavity wall insulation costs about <strong>{gbp(c('cavity'))}</strong>, the Energy Saving Trust's figure for a {EST_NAME[t]}, and homes that had it fitted used a median 12.0% less gas afterwards.")
    body = f"""
<p class="lead">{lead}</p>

<h2 id="costs">What each measure costs</h2>
<p class="answer"><strong>Loft first, then the walls.</strong> For a {main} on gas, cavity wall insulation saves about {gbp(sv['cavity'])} a year and pays back in {payback(c('cavity'), sv['cavity']).lower()}; solid walls save more but cost far more.</p>
{tbl}
<p class="note">{note_costs}</p>

<h2 id="walls">Cavity or solid walls?</h2>
<p class="answer"><strong>Check before you price anything.</strong> Homes built from the 1930s usually have cavity walls, which are far cheaper to insulate; brickwork showing the short ends of some bricks means solid walls. Your EPC records the wall type.</p>
<p>Solid wall insulation costs about {gbp(IC['solidInternal'])} fitted inside or {gbp(IC['solidExternal'])} outside, and saves about {gbp(sv['solid'])} a year here, so at full price it only pays with a grant. Read <a href="/guides/is-cavity-wall-insulation-worth-it/">is cavity wall insulation worth it</a> and <a href="/guides/solid-wall-insulation-cost/">solid wall insulation cost</a>.</p>

<h2 id="together">Loft and cavity together{' (top floor flat)' if t == 'flat' else ''}</h2>
<p class="answer"><strong>About {gbp(both)} for both.</strong> Homes that had loft and cavity wall insulation fitted together used a median 8.4% less gas, about {gbp(sv['loft+cavity'])} a year here; that is a different group of homes from the single-measure figures, so the two cannot be compared directly.</p>
<p>In our EPC model the loft adds about 7 points and cavity walls about 8, often enough to lift a home a band. Insulating first also shrinks the heat pump a {main} needs, from {kw(k_avg)} at average insulation to {kw(k_good)} well insulated. Plan the whole job with the <a href="/retrofit-plan/">retrofit plan</a>, or check your own home in the <a href="/insulation-calculator/">insulation calculator</a>.</p>

<h2 id="by-size">Savings by size of {label}</h2>
<p class="answer"><strong>Bigger homes save more.</strong> These are the measured savings a year for homes heated by gas, with average insulation to start with.</p>
{tbl_beds}
<p>Compare other types of home in <a href="/guides/insulation-cost-by-house-type/">insulation cost by house type</a>.</p>

<h2 id="grants">Grants that can pay for it</h2>
<p class="answer"><strong>ECO4 until 31 December 2026, then council grants.</strong> ECO4 funds insulation for households on qualifying benefits, in homes rated D to G if owned or E to G if privately rented, and the work must be finished by then.</p>
<p>In England a <a href="/grants/">Warm Homes: Local Grant</a> through your council can help households on lower incomes, and insulation carries 0% VAT until 31 March 2027. Landlords can check the 2030 band C rules with the <a href="/landlord-epc-calculator/">landlord EPC calculator</a>.</p>
"""
    return dict(slug=slug, kind='insulation',
                title='Insulation Cost for %s UK 2026' % ('an ' + label.title() if label[0] in 'aeiou' else 'a ' + label.title()),
                description='Loft %s to %s, cavity walls %s, solid walls £12,000 to £15,000: insulation costs and measured savings for a %s.'
                            % (gbp(c('loftTopUp')), gbp(c('loftBare')), gbp(c('cavity')), label),
                h1='How much does it cost to insulate a %s?' % label, crumb=crumb, faq=faq, body=body,
                sources=['Energy Saving Trust, <a href="https://energysavingtrust.org.uk/advice/cavity-wall-insulation/" target="_blank" rel="noopener">cavity wall</a>, <a href="https://energysavingtrust.org.uk/advice/roof-and-loft-insulation/" target="_blank" rel="noopener">loft</a>, <a href="https://energysavingtrust.org.uk/advice/solid-wall-insulation/" target="_blank" rel="noopener">solid wall</a> and <a href="https://energysavingtrust.org.uk/advice/floor-insulation/" target="_blank" rel="noopener">floor insulation</a> advice, May and June 2026.',
                         'DESNZ, <a href="https://www.gov.uk/government/statistics/national-energy-efficiency-data-framework-need-impact-of-measures-data-tables-2026" target="_blank" rel="noopener">NEED Impact of Measures 2026</a>, 11 June 2026.',
                         'Ofgem, <a href="https://www.ofgem.gov.uk/your-energy-supply/your-energy-bill/energy-price-cap-and-standing-charges-explained" target="_blank" rel="noopener">energy price cap</a>, October to December 2026.'])


INS_TYPES = [('insulation-cost-detached-house', 'detached', 4, 'Detached house'), ('insulation-cost-semi-detached-house', 'semi', 3, 'Semi-detached house'),
             ('insulation-cost-terraced-house', 'mid-terrace', 3, 'Terraced house'), ('insulation-cost-bungalow', 'bungalow', 3, 'Bungalow'),
             ('insulation-cost-flat', 'flat', 2, 'Flat')]


def ins_hub():
    rows = []
    for slug, t, b, name in INS_TYPES:
        sv = ins_saving(t, b, 'cavity')
        rows.append(['<a href="/guides/%s/">%s</a>' % (slug, name), gbp(IC['loftTopUp'][t]) + ' to ' + gbp(IC['loftBare'][t]), gbp(IC['cavity'][t]), gbp(sv), payback(IC['cavity'][t], sv)])
    tbl = table('Insulation cost by house type', ['Home', 'Loft', 'Cavity walls', 'Cavity saving a year', 'Cavity payback'], rows)
    faq = [('How much does insulation cost for my type of house?',
            'Cavity wall insulation costs about £950 for a flat, £1,100 for a mid-terrace, £1,700 for a detached bungalow, £2,200 for a semi and £3,900 for a detached house, at Energy Saving Trust prices. Loft insulation costs £500 to £1,200 and solid walls about £12,000 inside or £15,000 outside.'),
           ('Which insulation pays back fastest?',
            'Cavity wall insulation in a smaller home: about 12 years in a 3 bed mid-terrace and 14 in a 2 bed flat, on the measured gas savings. Solid wall insulation takes over 50 years at full price, so it pays best with a grant.')]
    body = f"""
<p class="lead">What loft, cavity wall, solid wall and floor insulation cost for each type of home, at Energy Saving Trust prices, and what homes that had it fitted saved on gas. Cavity wall insulation runs from <strong>£950</strong> for a flat to <strong>£3,900</strong> for a detached house.</p>

<h2 id="compare">Insulation cost by house type</h2>
<p class="answer"><strong>Cavity walls pay back fastest in smaller homes.</strong> A mid-terrace pays about £1,100 and saves about £94 a year; a detached house pays £3,900 and saves about £139.</p>
{tbl}
<p class="note">Costs: Energy Saving Trust, typical professional installation before any grant, updated 8 May 2026; the loft range runs from a top-up from 120mm to a bare loft, and a flat's loft figure is borrowed from the mid-terrace. Savings: the median 12.0% fall in gas use measured after cavity wall insulation (DESNZ NEED Impact of Measures 2026), for a 4 bed detached house, 3 bed semi, 3 bed mid-terrace, 3 bed bungalow and 2 bed flat on gas at the October 2026 cap. Solid wall insulation costs about £12,000 inside or £15,000 outside for any home, and a suspended timber floor £1,400 to £2,500.</p>

<h2 id="choose">Your type of home</h2>
<p class="answer"><strong>Pick your home for every measure, with savings by size and the grants.</strong></p>
<ul>{''.join('<li><a href="/guides/%s/">Insulation cost for %s</a></li>' % (slug, ('an ' if n[0] in 'AEIOU' else 'a ') + n.lower()) for slug, t, b, n in INS_TYPES)}</ul>
<p>Or work it out for your own home, with the insulation you have now, in the <a href="/insulation-calculator/">insulation calculator</a>.</p>
"""
    return dict(slug='insulation-cost-by-house-type', kind='insulation',
                title='Insulation Cost by House Type UK 2026: Loft, Walls, Floor',
                description='Cavity wall insulation from £950 for a flat to £3,900 for a detached house, loft and solid walls too, with measured savings and payback.',
                h1='Insulation cost by house type', crumb='Insulation cost by house type', faq=faq, body=body,
                sources=['Energy Saving Trust, <a href="https://energysavingtrust.org.uk/advice/cavity-wall-insulation/" target="_blank" rel="noopener">cavity wall</a> and <a href="https://energysavingtrust.org.uk/advice/roof-and-loft-insulation/" target="_blank" rel="noopener">loft insulation</a> advice, updated 8 May 2026.',
                         'DESNZ, <a href="https://www.gov.uk/government/statistics/national-energy-efficiency-data-framework-need-impact-of-measures-data-tables-2026" target="_blank" rel="noopener">NEED Impact of Measures 2026</a>.'])


def ins_semi():
    return ins_page('insulation-cost-semi-detached-house', 'semi', [2, 3, 4], 3, 'semi-detached house', 'semis', 'Insulation cost, semi-detached house', '')


def ins_detached():
    return ins_page('insulation-cost-detached-house', 'detached', [3, 4, 5], 4, 'detached house', 'detached houses', 'Insulation cost, detached house', '')


def ins_terrace():
    return ins_page('insulation-cost-terraced-house', 'mid-terrace', [2, 3], 3, 'terraced house', 'terraces', 'Insulation cost, terraced house',
                    'An end-terrace, which the Trust does not price, is closer to a semi-detached house: see our semi page. ')


def ins_bungalow():
    return ins_page('insulation-cost-bungalow', 'bungalow', [2, 3], 3, 'bungalow', 'bungalows', 'Insulation cost, bungalow', '')


def ins_flat():
    return ins_page('insulation-cost-flat', 'flat', [1, 2], 2, 'flat', 'flats', 'Insulation cost, flat',
                    'The Trust prices no loft for a flat, so a top floor flat takes its mid-terrace loft figures. ')



# ------------------------------------------------------------------ solar payback by region
# Every figure is the solar calculator's own output, saved by solar_regions.py to
# docs/solar-regions.json (a gate re-runs the calculator and fails if they drift). The map is
# the ONS ITL1 boundaries, simplified in docs/maps/itl1-2025.json (Open Government Licence).
SOLAR_R = json.loads((ROOT / 'docs' / 'solar-regions.json').read_text())
MAP = json.loads((ROOT / 'docs' / 'maps' / 'itl1-2025.json').read_text())
REGION = {
    'south': dict(slug='solar-panel-payback-south-england', name='South and East England', short='southern England', kwp=945,
                  itl=['London', 'South East (England)', 'South West (England)', 'East (England)'],
                  areas='London, the South East, the South West and the East of England', cities=[('London', 987), ('Bristol', 992)],
                  title='Solar Panel Payback, South and East England: %s'),
    'midlands': dict(slug='solar-panel-payback-midlands', name='the Midlands', short='the Midlands', kwp=885,
                     itl=['East Midlands (England)', 'West Midlands (England)'], areas='the East and West Midlands', cities=[('Birmingham', 940)],
                     title='Solar Panel Payback in the Midlands 2026: %s'),
    'north': dict(slug='solar-panel-payback-north-england', name='North England', short='northern England', kwp=850,
                  itl=['North East (England)', 'North West (England)', 'Yorkshire and The Humber'],
                  areas='the North East, the North West and Yorkshire and the Humber', cities=[('Manchester', 861), ('Newcastle upon Tyne', 921)],
                  title='Solar Panel Payback in Northern England 2026: %s'),
    'wales': dict(slug='solar-panel-payback-wales', name='Wales', short='Wales', kwp=885, itl=['Wales'], areas='all of Wales', cities=[('Cardiff', 1009)],
                  title='Solar Panel Payback in Wales 2026: %s'),
    'scotland': dict(slug='solar-panel-payback-scotland', name='Scotland', short='Scotland', kwp=795, itl=['Scotland'], areas='all of Scotland',
                     cities=[('Edinburgh', 878)], title='Solar Panel Payback in Scotland 2026: %s'),
}
SIZE_COST = {'3': '£4,000 to £5,500', '4': '£5,000 to £7,000', '5': '£6,500 to £8,500', '6': '£8,500 to £10,000'}
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
ROOF_NAME = {'south-east': 'South-east', 'south-west': 'South-west', 'east': 'East', 'west': 'West', 'north': 'North'}


def rcap(k):
    n = REGION[k]['name']
    return n[0].upper() + n[1:]


def region_of(itl_name):
    return next((k for k, v in REGION.items() if itl_name in v['itl']), None)


def region_map(highlight=None, links=True):
    """The UK by ITL1 region, each coloured by our payback. Regions link to their page."""
    shades = {'south': '#2d6a4f', 'midlands': '#40916c', 'wales': '#52a37b', 'north': '#74b495', 'scotland': '#95c7ad'}
    out = []
    for itl, d in MAP['paths'].items():
        r = region_of(itl)
        if r is None:
            out.append('<path d="%s" class="rm-none"><title>Northern Ireland: not covered</title></path>' % d)
            continue
        fill = shades[r] if (highlight is None or highlight == r) else '#d7e3dc'
        cls = 'rm-r' + (' rm-on' if highlight == r else '')
        path = '<path d="%s" fill="%s" class="%s" data-region="%s"><title>%s: %s</title></path>' % (d, fill, cls, r, rcap(r), SOLAR_R[r]['sizes']['4']['payback'])
        if links and highlight != r:
            nm = rcap(r)
            path = '<a href="/guides/%s/" data-region="%s" aria-label="%s: solar payback %s">%s</a>' % (REGION[r]['slug'], r, nm, SOLAR_R[r]['sizes']['4']['payback'], path)
        out.append(path)
    # a map with links is a group of links, not an image: links inside role="img" are unreachable
    role = 'group' if links else 'img'
    return ('<svg class="region-map" viewBox="0 0 %d %d" role="%s" aria-label="Map of the UK by region, shaded by solar panel payback">%s</svg>'
            % (MAP['w'], MAP['h'], role, ''.join(out)))


def solar_region_page(key):
    R, D = REGION[key], SOLAR_R[key]
    s4 = D['sizes']['4']
    size_rows = [['%s kW' % k, SIZE_COST[k], f"{int(v['gen']):,} kWh", gbp(v['benefit']), v['payback'], gbp(v['net25'])] for k, v in D['sizes'].items()]
    tbl_size = table('Solar payback by system size in %s' % R['short'], ['System', 'Installed cost', 'Generation a year', 'Saving and export a year', 'Payback', '25 years, after costs'], size_rows)
    roof_rows = [['South', f"{int(s4['gen']):,} kWh", gbp(s4['benefit']), s4['payback']]] + [[ROOF_NAME[k], f"{int(v['gen']):,} kWh", gbp(v['benefit']), v['payback']] for k, v in D['roofs'].items()]
    tbl_roof = table('4 kW solar payback by roof direction in %s' % R['short'], ['Roof faces', 'Generation a year', 'Saving and export a year', 'Payback'], roof_rows)
    b = s4['battery']
    tbl_batt = table('4 kW solar with and without a battery in %s' % R['short'], ['Result', 'Panels only', 'With a 5 kWh battery'],
                     [['Upfront cost', '£6,000', gbp(b['cost'])], ['Used at home', '%d%% of output' % s4['self_pct'], '%d%% of output' % b['self_pct']],
                      ['Saving and export a year', gbp(s4['benefit']), gbp(b['benefit'])], ['Payback', s4['payback'], b['payback']],
                      ['25 years, after costs', gbp(s4['net25']), ('Loses ' + gbp(-b['net25'])) if b['net25'] < 0 else gbp(b['net25'])]])
    tbl_seg = table('4 kW solar payback by export tariff in %s' % R['short'], ['Export rate', 'Saving and export a year', 'Payback'],
                    [['4.1p flat SEG rate', gbp(s4['seg']['4.1p'][0]), s4['seg']['4.1p'][1]], ['12p, Outgoing Octopus', gbp(s4['benefit']), s4['payback']],
                     ['17.5p installer-linked rate', gbp(s4['seg']['17.5p'][0]), s4['seg']['17.5p'][1]]])
    mo = s4['months']
    tbl_month = table('Monthly output of a 4 kW system in %s' % R['short'], ['Month', 'kWh'], [[MONTHS[i], str(mo[i])] for i in range(12)])
    ratio = max(mo) / mo[11]
    others = [['<a href="/guides/%s/">%s</a>' % (REGION[k]['slug'], rcap(k)) if k != key else '<strong>%s</strong>' % rcap(k),
               f"{int(SOLAR_R[k]['sizes']['4']['gen']):,} kWh", gbp(SOLAR_R[k]['sizes']['4']['benefit']), SOLAR_R[k]['sizes']['4']['payback']] for k in REGION]
    tbl_others = table('4 kW solar payback in each region', ['Region', 'Generation a year', 'Saving and export a year', 'Payback'], others)
    name_cap = R['name'][0].upper() + R['name'][1:]
    faq = [('How long do solar panels take to pay back in %s?' % R['short'],
            'About %s for a typical 4 kW south facing system costing £6,000, at the October 2026 price cap and a 12p export rate. It earns about %s a year and leaves about %s over 25 years.'
            % (s4['payback'], gbp(s4['benefit']), gbp(s4['net25']))),
           ('Are solar panels worth it in %s?' % R['short'],
            'On a reasonable roof, yes: a 4 kW system pays for itself in about %s, well inside a 25 year panel life. An east or west roof takes about %s, and a battery stretches it to %s.'
            % (s4['payback'], D['roofs']['east']['payback'], b['payback'])),
           ('How much electricity does a 4 kW solar system make in %s?' % R['short'],
            'About %s kWh a year on a south facing roof, using %s kWh per kW: the PVGIS figure for homes across the region, less 7%% for shading and dirt. Enter your postcode in the solar calculator for your own area. %s makes about %s times as much as December.'
            % (f"{int(s4['gen']):,}", R['kwp'], MONTHS[mo.index(max(mo))], ('%.1f' % ratio)))]
    body = f"""
<div class="region-intro"><p class="lead">A typical 4 kW solar system in {R['short']} costs about £6,000, generates about <strong>{int(s4['gen']):,} kWh</strong> a year and brings in about <strong>{gbp(s4['benefit'])} a year</strong> in bill savings and export payments, so it pays for itself in about <strong>{s4['payback']}</strong>. These are the solar calculator's figures for {R['areas']}.</p>
<figure class="region-fig">{region_map(highlight=key)}<figcaption>{name_cap} is highlighted. <a href="/guides/solar-panel-payback-by-region/">Compare every region</a>.</figcaption></figure></div>

<h2 id="by-size">Payback by system size</h2>
<p class="answer"><strong>About {s4['payback']} for 4 kW.</strong> Systems above 4 kW earn more over 25 years but pay back more slowly, because more of their output is exported at 12p rather than used at 26.32p.</p>
{tbl_size}
<p class="note">South facing roof at a typical pitch, a household using 2,500 kWh a year (a bill of about £860) that is out for about half the day, no battery, 12p export on Outgoing Octopus. Payback uses the middle of each cost range; 0% VAT until 31 March 2027. The 25 year figure allows for the panels losing 0.5% of their output a year.</p>

<h2 id="roof">Roof direction</h2>
<p class="answer"><strong>South is best, but east or west still pays back in about {D['roofs']['east']['payback']}.</strong> A north facing roof makes much less and takes about {D['roofs']['north']['payback']}.</p>
{tbl_roof}

<h2 id="battery">With a battery</h2>
<p class="answer"><strong>A battery slows payback to {b['payback']} here.</strong> It adds about {gbp(b['benefit'] - s4['benefit'])} a year for £4,600, and a battery lasts 10 to 12 years, so it is bought twice over the life of the panels.</p>
{tbl_batt}

<h2 id="export">Export tariff</h2>
<p class="answer"><strong>The export rate moves payback more than where you live.</strong> The same system pays back in {s4['seg']['17.5p'][1]} at 17.5p and {s4['seg']['4.1p'][1]} at 4.1p.</p>
{tbl_seg}

<h2 id="months">Month by month</h2>
<p class="answer"><strong>{MONTHS[mo.index(max(mo))]} makes about {ratio:.1f} times as much as December.</strong> April to September carries most of the year's output, so no home battery covers a winter in {R['short']}.</p>
{tbl_month}

<h2 id="compare">Compared with other regions</h2>
<p class="answer"><strong>The whole of Great Britain pays back within about two years of each other.</strong> Roof direction and the export tariff matter more than the region.</p>
{tbl_others}
<p>Work out your own roof, system size and battery in the <a href="/solar-calculator/">solar panel calculator</a>, or read <a href="/guides/solar-panel-payback-uk/">solar panel payback in the UK</a>.</p>
"""
    return dict(slug=R['slug'], kind='solar', title=R['title'] % s4['payback'].replace('years', 'Years'),
                description=('A 4 kW solar system in %s costs about £6,000, earns about %s a year and pays back in about %s. By size, roof and battery.'
                             % (R['short'], gbp(s4['benefit']), s4['payback'])),
                h1='Solar panel payback in %s' % R['short'], crumb='Solar payback, %s' % R['short'], faq=faq, body=body,
                sources=['European Commission Joint Research Centre, <a href="https://re.jrc.ec.europa.eu/pvg_tools/en/" target="_blank" rel="noopener">PVGIS 5.3</a>: generation by region and month, queried September 2026.',
                         'MCS, <a href="https://mcscertified.com/" target="_blank" rel="noopener">MGD 003 Solar PV Self-Consumption</a>: the share of output used at home.',
                         'Ofgem price cap October to December 2026; export rates from the suppliers, 25 September 2026; costs checked against DESNZ solar PV cost data, May 2026.',
                         'Map: Office for National Statistics, ITL1 boundaries January 2025, Open Government Licence v3.0. Contains OS data &copy; Crown copyright and database right 2025.'])


def solar_hub():
    rows = [['<a href="/guides/%s/">%s</a>' % (REGION[k]['slug'], rcap(k)),
             f"{int(SOLAR_R[k]['sizes']['4']['gen']):,} kWh", gbp(SOLAR_R[k]['sizes']['4']['benefit']), SOLAR_R[k]['sizes']['4']['payback'], gbp(SOLAR_R[k]['sizes']['4']['net25'])] for k in REGION]
    tbl = table('4 kW solar payback by region', ['Region', 'Generation a year', 'Saving and export a year', 'Payback', '25 years, after costs'], rows)
    lo, hi = SOLAR_R['south']['sizes']['4']['payback'], SOLAR_R['scotland']['sizes']['4']['payback']
    faq = [('Where in the UK do solar panels pay back fastest?',
            'In South and East England, about %s for a typical 4 kW south facing system, against about %s in Scotland. Wales and the Midlands sit in between. Northern Ireland is not covered, as it has its own electricity prices and export payments.' % (lo, hi)),
           ('Is solar worth it in the north of the UK?',
            'Yes on a reasonable roof: a 4 kW system pays back in about %s in northern England and %s in Scotland, well inside a 25 year panel life. Long summer days in the north partly make up for darker winters.' % (SOLAR_R['north']['sizes']['4']['payback'], hi))]
    body = f"""
<p class="lead">A typical 4 kW solar system pays for itself in about <strong>{lo}</strong> in South and East England and about <strong>{hi}</strong> in Scotland. Choose your region on the map for its full figures.</p>
<div class="region-picker">
<figure class="region-fig">{region_map()}<figcaption>Darker green pays back faster. Northern Ireland is not covered. Tap or select a region to open its page.</figcaption></figure>
<div class="region-panel" id="regionPanel" aria-live="polite"><p class="rp-hint">Hover over or select a region to see its figures.</p></div>
</div>

<h2 id="compare">Payback by region</h2>
<p class="answer"><strong>About two years separate the sunniest and the dullest regions.</strong> The export tariff and roof direction matter more than where you live.</p>
{tbl}
<p class="note">The solar calculator's figures for a 4 kW south facing system costing £6,000, a household using 2,500 kWh a year that is out for about half the day, no battery, and 12p export on Outgoing Octopus. Each region uses a cautious generation figure below the PVGIS result for its sunniest city.</p>
<p>Work out your own roof in the <a href="/solar-calculator/">solar panel calculator</a>, or read <a href="/guides/solar-panel-payback-uk/">solar panel payback in the UK</a>.</p>
<script>
(function () {{
    var D = {json.dumps({k: {'name': rcap(k), 'url': '/guides/%s/' % REGION[k]['slug'], 'gen': int(SOLAR_R[k]['sizes']['4']['gen']), 'benefit': int(SOLAR_R[k]['sizes']['4']['benefit']), 'payback': SOLAR_R[k]['sizes']['4']['payback']} for k in REGION})};
    var panel = document.getElementById('regionPanel');
    function show(k) {{
        var d = D[k]; if (!d) {{ return; }}
        panel.innerHTML = '<h3>' + d.name + '</h3><p><strong>' + d.payback + '</strong> to pay back a 4 kW system, earning about £' + d.benefit.toLocaleString('en-GB') + ' a year from ' + d.gen.toLocaleString('en-GB') + ' kWh.</p><p><a href="' + d.url + '">Full figures for ' + d.name.replace(/^The /, 'the ') + '</a></p>';
    }}
    document.querySelectorAll('.region-map a[data-region]').forEach(function (a) {{
        a.addEventListener('mouseenter', function () {{ show(a.getAttribute('data-region')); }});
        a.addEventListener('focus', function () {{ show(a.getAttribute('data-region')); }});
    }});
}})();
</script>
"""
    return dict(slug='solar-panel-payback-by-region', kind='solar', title='Solar Panel Payback by Region UK 2026: %s to %s' % (lo.replace(' years', ''), hi.replace('years', 'Years')),
                description='How long solar panels take to pay back in each part of Great Britain, from %s in the south to %s in Scotland, with a map of every region.' % (lo, hi),
                h1='Solar panel payback by region', crumb='Solar payback by region', faq=faq, body=body,
                sources=['Our <a href="/solar-calculator/">solar panel calculator</a>, using PVGIS 5.3, MCS MGD 003, the Ofgem price cap for October to December 2026 and supplier export rates of 25 September 2026.',
                         'Map: Office for National Statistics, ITL1 boundaries January 2025, Open Government Licence v3.0. Contains OS data &copy; Crown copyright and database right 2025.'])



# ------------------------------------------------------------------ heat pumps by council
# docs/bus-councils.json and docs/maps/lad-2025-ew.json come from bus_councils.py: DESNZ
# Boiler Upgrade Scheme Table Q1.2, Census 2021 households (Nomis) and ONS May 2025 boundaries.
HP_BINS = [20, 35, 50, 75]
HP_COLS = ['#e8f1ec', '#b9d9c6', '#7fb897', '#4a936c', '#23603f']
HP_LABELS = ['Under 20', '20 to 35', '35 to 50', '50 to 75', '75 or more']


def hp_council_page():
    D = json.loads((ROOT / 'docs' / 'bus-councils.json').read_text())
    MP = json.loads((ROOT / 'docs' / 'maps' / 'lad-2025-ew.json').read_text())
    C = D['councils']
    col = lambda r: HP_COLS[sum(r >= b for b in HP_BINS)]
    order = sorted(C, key=lambda c: C[c]['rank'])
    n = len(order)
    fmt = lambda v: f'{v:,}'
    one = lambda v: ('%.1f' % v)

    def svg(mp, cls, label):
        paths = ''.join('<path d="%s" fill="%s" data-c="%s"><title>%s: %s per 10,000 households</title></path>'
                        % (d, col(C[c]['rate']), c, html.escape(C[c]['name']), one(C[c]['rate'])) for c, d in mp['paths'].items())
        return '<svg class="%s" viewBox="0 0 %d %d" role="img" aria-label="%s">%s</svg>' % (cls, mp['w'], mp['h'], label, paths)

    legend = '<ul class="hp-legend">%s</ul>' % ''.join('<li><span style="background:%s"></span>%s</li>' % (HP_COLS[i], HP_LABELS[i]) for i in range(5))
    pages = set(D.get('pages', []))
    cname = lambda c: ('<a href="/guides/%s/">%s</a>' % (council_slug(C[c]['name']), html.escape(council_name(C[c]['name'])))) if c in pages else html.escape(C[c]['name'])
    top = [[cname(c), C[c]['region'], fmt(C[c]['hp']), one(C[c]['rate'])] for c in order[:10]]
    bottom = [[cname(c), C[c]['region'], fmt(C[c]['hp']), one(C[c]['rate'])] for c in reversed(order[-10:])]
    head = ['Council', 'Region', 'Heat pumps', 'Per 10,000 households']
    regions = sorted(D['regions'].items(), key=lambda kv: -kv[1]['rate'])
    reg_rows = [[k, fmt(v['hp']), fmt(v['households']), one(v['rate'])] for k, v in regions]
    all_rows = [[str(C[c]['rank']), cname(c), C[c]['region'], fmt(C[c]['hp']), fmt(C[c]['households']), one(C[c]['rate'])] for c in order]
    most = max(C, key=lambda c: C[c]['hp'])
    from collections import Counter
    lead_reg, lead_n = Counter(C[c]['region'] for c in order[:10]).most_common(1)[0]
    top_where = ('mostly in %s' % REGION_THE.get(lead_reg, lead_reg)) if lead_n >= 5 else 'spread across England and Wales'
    first, last = C[order[0]], C[order[-1]]
    lowest5 = [C[c] for c in order if C[c]['rate'] < 5]
    data = {c: [v['name'], v['hp'], v['households'], v['rate'], v['rank'], v['region']] + (['/guides/%s/' % council_slug(v['name'])] if c in pages else []) for c, v in C.items()}
    names = ''.join('<option value="%s">' % html.escape(C[c]['name']) for c in sorted(C, key=lambda c: C[c]['name']))
    faq = [('Which council has the most heat pumps?',
            '%s has the most heat pump grants paid of any council in England and Wales, %s. Per household, %s leads with %s for every 10,000 households, more than four times the England and Wales figure of %s.'
            % (C[most]['name'], fmt(C[most]['hp']), first['name'], one(first['rate']), one(D['rate']))),
           ('How many heat pumps are there in my area?',
            'Search for your council above. The figures count heat pumps paid for with a Boiler Upgrade Scheme grant from May 2022 to June 2026, so they leave out heat pumps installed without the grant, for example in new build homes.'),
           ('Why are there so few heat pumps in London?',
            'London has %s heat pump grants for every 10,000 households, the lowest of any region. Much of the scheme has gone to rural homes and homes off the gas grid: in the same statistics, 48%% of the air to water heat pumps paid for were in rural homes and 37%% in homes off the gas grid.' % one(D['regions']['London']['rate']))]
    body = f"""
<p class="lead"><strong>{fmt(D['total'])}</strong> heat pumps have been installed with a Boiler Upgrade Scheme grant in England and Wales since the scheme opened in May 2022, about <strong>{one(D['rate'])}</strong> for every 10,000 households. {html.escape(first['name'])} leads with {one(first['rate'])}; parts of inner London have fewer than 5.</p>

<div class="hp-map-wrap">
<figure class="hp-map">{svg(MP['main'], 'hp-main', 'Map of England and Wales by council, shaded by heat pump grants per 10,000 households')}
<figcaption>Heat pumps per 10,000 households, by council.{legend}</figcaption></figure>
<div class="hp-side">
<label for="councilSearch">Find your council</label>
<input id="councilSearch" list="councilNames" autocomplete="off" placeholder="e.g. Leeds"><datalist id="councilNames">{names}</datalist>
<div class="hp-panel" id="councilPanel" aria-live="polite"><p class="rp-hint">Search for a council, or hover over the map.</p></div>
<figure class="hp-london">{svg(MP['london'], 'hp-ldn', 'London boroughs, shaded by heat pump grants per 10,000 households')}<figcaption>London, enlarged</figcaption></figure>
</div>
</div>

<h2 id="most">Where heat pumps are most common</h2>
<p class="answer"><strong>Rural councils, {top_where}, lead.</strong> The top ten all have more than twice the England and Wales figure of {one(D['rate'])} per 10,000 households.</p>
{table('Councils with the most heat pump grants per household', head, top)}

<h2 id="least">Where they are least common</h2>
<p class="answer"><strong>London boroughs and other urban areas.</strong> In the same statistics, 48% of the air to water heat pumps paid for went to rural homes and 37% to homes off the gas grid.</p>
{table('Councils with the fewest heat pump grants per household', head, bottom)}

<h2 id="regions">By region</h2>
<p class="answer"><strong>The South West has the most per household, London the fewest.</strong></p>
{table('Heat pump grants by region', ['Region', 'Heat pumps', 'Households', 'Per 10,000 households'], reg_rows)}

<h2 id="all">Every council</h2>
<p class="answer"><strong>All {n} councils in England and Wales, ranked.</strong></p>
<details class="more"><summary>Show every council</summary>
{table('Heat pump grants in every council, ranked', ['Rank', 'Council', 'Region', 'Heat pumps', 'Households', 'Per 10,000 households'], all_rows)}
</details>
<p class="note">Heat pumps are Boiler Upgrade Scheme grants paid from 23 May 2022 to 30 June 2026 (DESNZ, {html.escape(D['title'].split(' - ')[0])}, published {long_date_str(D['published'])}), counting air and ground source heat pumps. Households are the Census 2021 count for each council. The scheme covers England and Wales; Scotland and Northern Ireland have their own. Heat pumps installed without the grant, such as in most new build and social homes, are not counted.</p>

<h2 id="yours">Thinking about one?</h2>
<p class="answer"><strong>The grant is £7,500, or £9,000 replacing oil or LPG in a home with no mains gas, until 31 March 2027.</strong> See what one would cost and save in your home with the <a href="/heat-pump-calculator/">heat pump calculator</a>, or read the <a href="/guides/boiler-upgrade-scheme-guide/">Boiler Upgrade Scheme guide</a>.</p>
<script>
(function () {{
    var D = {json.dumps(data, ensure_ascii=False, separators=(',', ':'))};
    var byName = {{}}; Object.keys(D).forEach(function (c) {{ byName[D[c][0].toLowerCase()] = c; }});
    var panel = document.getElementById('councilPanel'), input = document.getElementById('councilSearch');
    var ew = {D['rate']}, n = {n};
    function show(c) {{
        var d = D[c]; if (!d) {{ return; }}
        var cmp = d[3] >= ew ? (d[3] / ew).toFixed(1) + ' times the England and Wales figure' : 'below the England and Wales figure of ' + ew.toFixed(1);
        panel.innerHTML = '<h3>' + d[0] + '</h3><p><strong>' + d[1].toLocaleString('en-GB') + '</strong> heat pumps with a grant, <strong>' + d[3].toFixed(1) + '</strong> for every 10,000 households, ' + cmp + '.</p><p>Ranked ' + d[4] + ' of ' + n + ' councils. ' + d[5] + '.</p>' + (d[6] ? '<p><a href="' + d[6] + '">More on heat pumps in ' + d[0].replace(/, City of$/, '') + '</a></p>' : '');
        document.querySelectorAll('.hp-map-wrap path.on').forEach(function (p) {{ p.classList.remove('on'); }});
        document.querySelectorAll('.hp-map-wrap path[data-c="' + c + '"]').forEach(function (p) {{ p.classList.add('on'); }});
    }}
    document.querySelectorAll('.hp-map-wrap svg').forEach(function (svg) {{
        svg.addEventListener('mouseover', function (e) {{ var c = e.target.getAttribute && e.target.getAttribute('data-c'); if (c) {{ show(c); }} }});
    }});
    function find() {{ var c = byName[input.value.trim().toLowerCase()]; if (c) {{ show(c); }} }}
    input.addEventListener('change', find); input.addEventListener('input', find);
}})();
</script>
"""
    return dict(slug='heat-pumps-by-council', kind='heat-pump', provenance='official statistics', title='Heat Pumps by Council: Grants in Every Area Mapped 2026',
                description='How many heat pump grants have been paid in every council area of England and Wales, per 10,000 households, on a map. Find your council.',
                h1='Heat pumps by council', crumb='Heat pumps by council', faq=faq, body=body,
                sources=['Department for Energy Security and Net Zero, <a href="https://www.gov.uk/government/statistics/boiler-upgrade-scheme-statistics-august-2026" target="_blank" rel="noopener">Boiler Upgrade Scheme statistics, August 2026</a>, Tables Q1.2, 1.5 and 1.6. Source: Ofgem.',
                         'Office for National Statistics, Census 2021, <a href="https://www.nomisweb.co.uk/datasets/c2021ts041" target="_blank" rel="noopener">TS041 number of households</a>, by local authority.',
                         'Map: Office for National Statistics, Local Authority Districts (May 2025) boundaries, Open Government Licence v3.0. Contains OS data &copy; Crown copyright and database right 2025.'])


REGION_THE = {'North East': 'the North East', 'North West': 'the North West', 'East Midlands': 'the East Midlands',
              'West Midlands': 'the West Midlands', 'East': 'the East of England', 'South East': 'the South East',
              'South West': 'the South West'}


def council_slug(name):
    return 'heat-pumps-in-' + re.sub(r'[^a-z0-9]+', '-', council_name(name).lower()).strip('-')


def council_name(name):
    # 'Bristol, City of' reads as 'Bristol'; 'Kingston upon Hull, City of' as 'Kingston upon Hull'
    return re.sub(r', (City|County) of$', '', name).strip()


def region_svg(D, MP, code):
    """The council's region from the main map, cropped to the region, with the council marked."""
    C = D['councils']
    region = C[code]['region']
    col = lambda r: HP_COLS[sum(r >= b for b in HP_BINS)]
    mine = {c: d for c, d in MP['main']['paths'].items() if C[c]['region'] == region}
    nums = [float(x) for d in mine.values() for x in re.findall(r'-?\d+\.?\d*', d)]
    xs, ys = nums[0::2], nums[1::2]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    pad = 4
    body = ''.join('<path d="%s" fill="%s"%s><title>%s: %s per 10,000 households</title></path>'
                   % (d, col(C[c]['rate']), ' class="on"' if c == code else '', html.escape(council_name(C[c]['name'])), '%.1f' % C[c]['rate'])
                   for c, d in sorted(mine.items(), key=lambda kv: kv[0] == code))
    return ('<svg class="hp-region" viewBox="%.1f %.1f %.1f %.1f" role="img" aria-label="%s, with %s outlined">%s</svg>'
            % (x0 - pad, y0 - pad, x1 - x0 + 2 * pad, y1 - y0 + 2 * pad, html.escape(region), html.escape(council_name(C[code]['name'])), body))


def hp_council_detail(code):
    D = json.loads((ROOT / 'docs' / 'bus-councils.json').read_text())
    MP = json.loads((ROOT / 'docs' / 'maps' / 'lad-2025-ew.json').read_text())
    C, v = D['councils'], D['councils'][code]
    name = council_name(v['name'])
    region = v['region']
    rthe = REGION_THE.get(region, region)
    R = D['regions'][region]
    n = len(C)
    fmt = lambda x: f'{x:,}'
    one = lambda x: '%.1f' % x
    ew = D['rate']
    times = v['rate'] / ew
    cmp = ('%.1f times the England and Wales figure of %s' % (times, one(ew))) if times >= 1.15 else \
          ('close to the England and Wales figure of %s' % one(ew)) if times > 0.87 else \
          ('below the England and Wales figure of %s' % one(ew))
    reg_list = sorted([c for c in C if C[c]['region'] == region], key=lambda c: C[c]['rank'])
    pos = reg_list.index(code)
    win = reg_list[max(0, pos - 4): pos + 5]
    pages = set(D['pages'])
    def cell_name(c):
        nm = html.escape(council_name(C[c]['name']))
        if c == code:
            return '<strong>%s</strong>' % nm
        return '<a href="/guides/%s/">%s</a>' % (council_slug(C[c]['name']), nm) if c in pages else nm
    near = table('%s councils around %s' % (region, name), ['Rank in region', 'Council', 'Heat pumps', 'Per 10,000 households'],
                 [[str(reg_list.index(c) + 1), cell_name(c), fmt(C[c]['hp']), one(C[c]['rate'])] for c in win])
    cmp_tbl = table('%s compared' % name, ['Area', 'Heat pumps', 'Per 10,000 households'],
                    [['<strong>%s</strong>' % html.escape(name), fmt(v['hp']), one(v['rate'])], [html.escape(region), fmt(R['hp']), one(R['rate'])],
                     ['England and Wales', fmt(D['total']), one(ew)]])
    yrs = v['years']
    year_rows = [[D['years'][i] + (' (from 23 May)' if i == 0 else ''), fmt(yrs[i]), fmt(D['ew_years'][i])] for i in range(len(yrs))]
    tbl_years = table('Heat pump grants a year in %s' % name, ['Financial year', name, 'England and Wales'], year_rows)
    growth = yrs[-1] / yrs[1] if yrs[1] else None
    ew_growth = D['ew_years'][-1] / D['ew_years'][1]
    if growth and yrs[1] >= 20:
        grow_txt = ('%s had %s grants paid in 2025/26 against %s in 2023/24, the first full year: %.1f times as many, against %.1f times across England and Wales.'
                    % (name, fmt(yrs[-1]), fmt(yrs[1]), growth, ew_growth))
    else:
        grow_txt = '%s had %s grants paid in 2025/26 against %s in 2023/24, the first full year.' % (name, fmt(yrs[-1]), fmt(yrs[1]))
    if yrs[-1] < yrs[-2]:
        grow_txt += ' That is down from %s in 2024/25.' % fmt(yrs[-2])
    energy = energy_section(code, name)
    welsh = code.startswith('W')
    local = ('Your council can refer low income households to ECO4 Flex until 31 December 2026. Wales has its own Warm Homes Nest scheme.' if welsh else
             'In England, ask your council whether it has Warm Homes: Local Grant funding, which can pay for insulation and a heat pump for households on lower incomes.')
    faq = [('How many heat pumps are there in %s?' % name,
            '%s heat pumps have been installed in %s with a Boiler Upgrade Scheme grant since the scheme opened in May 2022, to the end of June 2026. That is %s for every 10,000 households.'
            % (fmt(v['hp']), name, one(v['rate']))),
           ('How does %s compare with the rest of the country?' % name,
            '%s ranks %s of %d councils in England and Wales for heat pump grants per household, %s. Across %s the figure is %s.'
            % (name, ordinal(v['rank']), n, cmp, rthe, one(R['rate']))),
           ('Can I get a heat pump grant in %s?' % name,
            'Yes, if you own the home and are replacing fossil fuel or electric heating: the Boiler Upgrade Scheme gives £7,500 off a heat pump, or £9,000 replacing oil or LPG in a home with no mains gas, until 31 March 2027. Your MCS installer applies for it. ' + local)]
    body = f"""
<p class="lead"><strong>{fmt(v['hp'])}</strong> heat pumps have been installed in {html.escape(name)} with a Boiler Upgrade Scheme grant since May 2022, <strong>{one(v['rate'])}</strong> for every 10,000 households. That ranks {html.escape(name)} <strong>{ordinal(v['rank'])} of {n}</strong> councils in England and Wales, {cmp}.</p>

<h2 id="compare">How {html.escape(name)} compares</h2>
<div class="hp-council-cmp">
<div>
<p class="answer"><strong>{ordinal(pos + 1)} of {len(reg_list)} councils in {html.escape(rthe)}.</strong> The region as a whole has {one(R['rate'])} heat pumps for every 10,000 households.</p>
{cmp_tbl}
</div>
<figure class="hp-region-fig">{region_svg(D, MP, code)}<figcaption>{html.escape(region)}, {html.escape(name)} outlined. <a href="/guides/heat-pumps-by-council/">Every council on one map</a>.</figcaption></figure>
</div>

<h2 id="years">Year by year</h2>
<p class="answer"><strong>{fmt(yrs[-1])} grants in 2025/26.</strong> {grow_txt}</p>
{tbl_years}
<p class="note">Financial years run April to March. The first year starts on 23 May 2022, when the scheme opened, and April to June 2026 is in the total but not yet in a year, so the years add up to less than the total.</p>

<h2 id="nearby">Nearby in the rankings</h2>
<p class="answer"><strong>Where {html.escape(name)} sits among the councils in {html.escape(rthe)}.</strong></p>
{near}

{energy}
<h2 id="yours">Getting a heat pump in {html.escape(name)}</h2>
<p class="answer"><strong>£7,500 off, or £9,000 replacing oil or LPG in a home with no mains gas, until 31 March 2027.</strong> A typical 3 bed semi costs £11,000 to £15,500 installed before the grant.</p>
<p>{local} See what a heat pump would cost and save in your home with the <a href="/heat-pump-calculator/">heat pump calculator</a>, and what it costs to run with the <a href="/heat-pump-running-cost-calculator/">running cost calculator</a>.</p>
<p class="note">Heat pumps are Boiler Upgrade Scheme grants paid from 23 May 2022 to 30 June 2026 (DESNZ Boiler Upgrade Scheme statistics, August 2026, Tables Q1.2 and A1.7), counting air and ground source heat pumps. Heat pumps installed without the grant, such as in most new build and social homes, are not counted. Households are the Census 2021 count for {html.escape(name)}: {fmt(v['households'])}.</p>
"""
    title = 'Heat Pumps in %s: %s Grants Paid, 2026' % (name, fmt(v['hp']))
    if len(title) > 60:
        title = 'Heat Pumps in %s: %s Grants' % (name, fmt(v['hp']))
    if len(title) > 60:
        title = 'Heat Pumps in %s, 2026' % name
    desc = ('%s heat pumps installed in %s with a government grant, %s per 10,000 households: ranked %s of %d councils. By year and against %s.'
            % (fmt(v['hp']), name, one(v['rate']), ordinal(v['rank']), n, rthe))
    if len(desc) > 155:
        desc = '%s heat pumps installed in %s with a government grant, %s per 10,000 households, ranked %s of %d councils.' % (fmt(v['hp']), name, one(v['rate']), ordinal(v['rank']), n)
    return dict(slug=council_slug(v['name']), kind='heat-pump', provenance='official statistics', title=title, description=desc,
                h1='Heat pumps in %s' % name, crumb='Heat pumps in %s' % name, faq=faq, body=body,
                sources=['Department for Energy Security and Net Zero, <a href="https://www.gov.uk/government/statistics/boiler-upgrade-scheme-statistics-august-2026" target="_blank" rel="noopener">Boiler Upgrade Scheme statistics, August 2026</a>, Tables Q1.2 and A1.7. Source: Ofgem.',
                         'Office for National Statistics, Census 2021, <a href="https://www.nomisweb.co.uk/datasets/c2021ts041" target="_blank" rel="noopener">TS041 number of households</a>.',
                         'Department for Energy Security and Net Zero, <a href="https://www.gov.uk/government/statistics/national-energy-efficiency-data-framework-need-consumption-data-tables-2026" target="_blank" rel="noopener">NEED consumption data tables 2026</a>, local authority tables 2024.',
                         'Map: Office for National Statistics, Local Authority Districts (May 2025) boundaries, Open Government Licence v3.0. Contains OS data &copy; Crown copyright and database right 2025.'])


def energy_section(code, name):
    """'Energy use in <council>': median gas and electricity per home against England and Wales, by home type."""
    N = json.loads((ROOT / 'docs' / 'energy-councils.json').read_text())
    e, ew = N['councils'][code], N['ew']
    fmt = lambda x: f'{x:,}' if x else 'no data'
    nm = html.escape(name)
    def vs(a, b):
        d = (a - b) / b * 100
        return 'close to' if abs(d) < 3 else '%d%% %s' % (round(abs(d)), 'above' if d > 0 else 'below')
    if e['gas']:
        cost = gas_cost(e['gas']) + elec_cost(e['elec'])
        ans = ('<strong>%s kWh of gas and %s kWh of electricity a year</strong> for the median home, about %s at the October 2026 price cap. '
               'Gas use is %s the England and Wales median of %s kWh.' % (fmt(e['gas']), fmt(e['elec']), gbp(cost), vs(e['gas'], ew['gas']), fmt(ew['gas'])))
    else:
        ans = '<strong>%s kWh of electricity a year</strong> for the median home. There is no mains gas.' % fmt(e['elec'])
    rows = [['<strong>All homes</strong>', fmt(e['gas']), fmt(ew['gas']), fmt(e['elec']), fmt(ew['elec'])]]
    for t, lab in TYPE_LABEL.items():
        if e['gas_type'].get(t) or e['elec_type'].get(t):
            rows.append([lab, fmt(e['gas_type'].get(t)), fmt(ew['gas_type'][t]), fmt(e['elec_type'].get(t)), fmt(ew['elec_type'][t])])
    tbl = table('Median energy use per home a year in %s, kWh' % name, ['Home', 'Gas, ' + nm, 'Gas, England and Wales', 'Electricity, ' + nm, 'Electricity, England and Wales'], rows)
    return f"""<h2 id="energy">Energy use in {nm}</h2>
<p class="answer">{ans}</p>
{tbl}
<p class="note">Medians from 2024 meter readings (DESNZ NEED local authority tables 2024, LA1, LA2, LA5 and LA6). Gas covers homes with a gas meter. Costs use the Ofgem cap for October to December 2026, with standing charges. <a href="/guides/energy-use-by-council/">Energy use in every council on one map</a>.</p>
"""


def ordinal(k):
    return '%d%s' % (k, 'th' if 10 <= k % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(k % 10, 'th'))


def long_date_str(iso):
    import datetime
    d = datetime.date.fromisoformat(iso)
    return '%d %s %d' % (d.day, d.strftime('%B'), d.year)



# ------------------------------------------------------------------ EPC rating by house age
# docs/epc-by-age.json comes from epc_by_age.py (English Housing Survey 2024 live tables and NEED
# 2026). The routes to band C are js/epc-plan.js, the EPC calculator's own model, run in node.
AGE_ERAS = [
    dict(slug='epc-rating-victorian-house', tname='Victorian House', short='Victorian and Edwardian', period='before 1919', ehs=['pre-1919'], need=['Pre 1919'],
         examples=[('pre1919', 'mid-terrace', 'solid-no', 'a Victorian mid-terrace with solid walls')], target='C',
         links=[('/guides/heat-pump-victorian-terrace/', 'heat pumps in a Victorian terrace'), ('/guides/solid-wall-insulation-cost/', 'solid wall insulation cost'), ('/guides/heat-pump-old-house/', 'heat pumps in an old house')]),
    dict(slug='epc-rating-1930s-house', tname='1930s House', short='1920s and 1930s', period='between 1919 and 1944', ehs=['1919-44'], need=['1919 - 1944'],
         examples=[('1919', 'semi', 'cavity-no', 'a 1930s semi with unfilled cavity walls'), ('1919', 'semi', 'solid-no', 'a 1930s semi with solid walls')], target='C',
         links=[('/guides/heat-pump-1930s-semi/', 'heat pumps in a 1930s semi'), ('/guides/is-cavity-wall-insulation-worth-it/', 'is cavity wall insulation worth it'), ('/guides/solid-wall-insulation-cost/', 'solid wall insulation cost')]),
    dict(slug='epc-rating-1950s-house', tname='1950s House', short='1950s and early 1960s', period='between 1945 and 1964', ehs=['1945-64'], need=['1945 - 1964'],
         examples=[('1945', 'semi', 'cavity-no', 'a 1950s semi with unfilled cavity walls')], target='C',
         links=[('/guides/heat-pump-1960s-house/', 'heat pumps in a 1960s house'), ('/guides/is-cavity-wall-insulation-worth-it/', 'is cavity wall insulation worth it')]),
    dict(slug='epc-rating-1970s-house', tname='1970s House', short='late 1960s and 1970s', period='between 1965 and 1980', ehs=['1965-80'], need=['1965 - 1982'],
         examples=[('1965', 'semi', 'cavity-no', 'a 1970s semi with unfilled cavity walls')], target='C',
         links=[('/guides/heat-pump-1960s-house/', 'heat pumps in a 1960s house'), ('/guides/is-cavity-wall-insulation-worth-it/', 'is cavity wall insulation worth it')]),
    dict(slug='epc-rating-1980s-1990s-house', tname='1980s or 1990s House', short='1980s and 1990s', period='between 1981 and 2002', ehs=['1981-90', '1991-2002'], need=['1983 - 1992', '1993 - 1999'],
         examples=[('1981', 'semi', 'cavity-no', 'a 1980s semi with unfilled cavity walls'), ('1991', 'semi', 'cavity-no', 'a 1990s semi with unfilled cavity walls')], target='C',
         links=[('/guides/is-cavity-wall-insulation-worth-it/', 'is cavity wall insulation worth it'), ('/guides/how-to-improve-epc-rating/', 'how to improve an EPC rating')]),
    dict(slug='epc-rating-new-build-house', tname='New Build House', short='new build', period='since 2003', ehs=['2003-2013', 'post-2013'], need=['2000 - 2011', '2012 onwards'],
         examples=[('2003', 'semi', 'cavity-yes', 'a 2000s semi'), ('2012', 'semi', 'cavity-yes', 'a home built since 2012')], target='B',
         links=[('/guides/how-to-improve-epc-rating/', 'how to improve an EPC rating'), ('/solar-calculator/', 'the solar panel calculator')]),
]
AGE_LABEL = {'pre-1919': 'Before 1919', '1919-44': '1919 to 1944', '1945-64': '1945 to 1964', '1965-80': '1965 to 1980', '1981-90': '1981 to 1990',
             '1991-2002': '1991 to 2002', '2003-2013': '2003 to 2013', 'post-2013': 'After 2013', 'all dwellings': 'All homes'}
NEED_LABEL = {'Pre 1919': 'Before 1919', '1919 - 1944': '1919 to 1944', '1945 - 1964': '1945 to 1964', '1965 - 1982': '1965 to 1982',
              '1983 - 1992': '1983 to 1992', '1993 - 1999': '1993 to 1999', '2000 - 2011': '2000 to 2011', '2012 onwards': '2012 onwards', 'All dwellings': 'All homes'}


def epc_plans(cases):
    js = ('global.window={};require("./js/epc-plan.js");const E=window.RP_EPC;const out=[];'
          'for(const c of %s){const p=E.plan({currentBand:"estimate",propAge:c[0],propType:c[1],wall:c[2],loft:"good",glazing:"double",'
          'heating:"new-gas",solar:"no",lighting:"mixed"},c[3]);out.push(p);}console.log(JSON.stringify(out));' % json.dumps(cases))
    return json.loads(subprocess.run(['node', '-e', js], capture_output=True, text=True, cwd=ROOT).stdout)


def band_of(sap):
    return 'A' if sap >= 92 else 'B' if sap >= 81 else 'C' if sap >= 69 else 'D' if sap >= 55 else 'E' if sap >= 39 else 'F' if sap >= 21 else 'G'


def pct(v):
    if v is None:
        return 'too few to show'
    if v == 0:
        return '0%'
    return 'under 1%' if v < 1 else 'over 99%' if 99 < v < 100 else '%d%%' % round(v)


def need_period(k):
    lab = NEED_LABEL[k]
    if lab.startswith('Before'):
        return lab.lower()
    if lab.endswith('onwards'):
        return 'since ' + lab.split()[0]
    a, b = lab.split(' to ')
    return 'between %s and %s' % (a, b)


def epc_age_page(i):
    E = AGE_ERAS[i]
    A = json.loads((ROOT / 'docs' / 'epc-by-age.json').read_text())
    ages, allh = A['ages'], A['ages']['all dwellings']
    rows = E['ehs']
    homes = sum(ages[r]['homes_000'] for r in rows)
    abc = sum(ages[r]['bands']['A/B/C'] * ages[r]['homes_000'] for r in rows) / homes
    efg = sum(ages[r]['bands']['E/F/G'] * ages[r]['homes_000'] for r in rows) / homes
    sap = sum(ages[r]['bands']['SAP'] * ages[r]['homes_000'] for r in rows) / homes
    cols = rows + ['all dwellings']
    bshare = {b: sum((ages[r]['bands'][b] or 0) * ages[r]['homes_000'] for r in rows) / homes for b in ('A/B', 'C', 'D', 'E', 'F', 'G')}
    top_band = max(bshare, key=bshare.get)
    band_word = ('Mostly band %s' if bshare[top_band] > 50 else 'Most often band %s') % top_band + ', %s' % pct(bshare[top_band])
    bands_tbl = table('EPC bands of homes built %s' % E['period'], ['EPC band'] + [AGE_LABEL[c] for c in cols],
                      [[b] + [pct(ages[c]['bands'][b]) for c in cols] for b in ('A/B', 'C', 'D', 'E', 'F', 'G')]
                      + [['Average rating'] + ['%d (band %s)' % (round(ages[c]['bands']['SAP']), band_of(ages[c]['bands']['SAP'])) for c in cols]])
    w = lambda c: ages[c]['walls']
    feat = [['Solid walls, not insulated'] + [pct(w(c)['solid uninsulated']) for c in cols],
            ['Solid walls, insulated'] + [pct(w(c)['solid insulated']) for c in cols],
            ['Cavity walls, not insulated'] + [pct(w(c)['cavity uninsulated']) for c in cols],
            ['Cavity walls, insulated'] + [pct((w(c)['cavity insulated'] or 0) + (w(c)['cavity insulated as built'] or 0)) for c in cols],
            ['Loft insulation 150mm or more'] + [pct(ages[c]['loft']['150mm or more']) for c in cols],
            ['Loft insulation under 100mm, or none'] + [pct((ages[c]['loft']['under 100mm'] or 0) + (ages[c]['loft']['none'] or 0)) for c in cols],
            ['Double glazing throughout'] + [pct(ages[c]['glazing_all']) for c in cols],
            ['Gas heating'] + [pct(ages[c]['gas']) for c in cols],
            ['Heat pump'] + [pct(ages[c]['heat_pump']) for c in cols]]
    feat_tbl = table('What homes built %s are like' % E['period'], ['Feature'] + [AGE_LABEL[c] for c in cols], feat)
    wv = lambda r, k: ages[r]['walls'][k] or 0
    wshare = {k: sum(wv(r, k) * ages[r]['homes_000'] for r in rows) / homes for k in ('solid uninsulated', 'solid insulated', 'cavity uninsulated')}
    wshare['cavity insulated'] = sum((wv(r, 'cavity insulated') + wv(r, 'cavity insulated as built')) * ages[r]['homes_000'] for r in rows) / homes   # built insulated counts as filled
    top_wall = max(['solid uninsulated', 'solid insulated', 'cavity uninsulated', 'cavity insulated'], key=lambda k: wshare[k] or 0)
    share = wshare[top_wall] or 0
    lead_word = 'most have' if share >= 50 else 'the most common is'
    wall_txt = {'solid uninsulated': 'solid walls with no insulation', 'solid insulated': 'insulated solid walls',
                'cavity uninsulated': 'cavity walls that are still unfilled', 'cavity insulated': 'filled cavity walls'}[top_wall]
    wall_txt = '%s %s, %s' % (lead_word, wall_txt, pct(share)) if share < 50 else '%s %s (%s)' % (lead_word, wall_txt, pct(share))
    ng = A['need_gas_median']; nm = A['need_gas_per_m2_houses']
    gas_cols = E['need'] + ['All dwellings']
    gas_tbl = table('Gas use of homes built %s' % E['period'], ['Built'] + ['Median gas a year', 'Median gas per square metre (houses)'],
                    [[NEED_LABEL[k], f"{ng[k]:,} kWh", ('%d kWh' % nm[k]) if k in nm else 'not published for this band'] for k in gas_cols])
    plans = epc_plans([[a, t, wl, E['target']] for a, t, wl, _ in E['examples']])
    plan_html, plan_answer = '', ''
    for (age, t, wl, label), p in zip(E['examples'], plans):
        link = ('/epc-calculator/?currentBand=estimate&targetBand=%s&propType=%s&propAge=%s&lighting=mixed&hasLoft=good&hasWall=%s&hasDoubleGlazing=double&heating=new-gas&hasSolar=no&tenure=owner'
                % (E['target'], t, age, wl))
        if p.get('met'):
            txt = 'Our model puts %s at about %d points, band %s: already band %s or better.' % (label, p['currentScore'], p['currentBand'], E['target'])
            plan_html += '<p>%s <a href="%s">Check your own home</a>.</p>' % (txt[0].upper() + txt[1:], html.escape(link, quote=True))
            plan_answer = plan_answer or txt
            continue
        rows_ = [[m['name'], '+%d' % m['points'], gbp(m['netCost']), 'Band ' + m['runBand']] for m in p['measures']]
        plan_html += ('<h3>%s</h3><p>Our model starts it at about %d points, band %s. The cheapest route to band %s costs about %s:</p>%s<p><a href="%s">Check your own home in the EPC calculator</a>.</p>'
                      % (label[0].upper() + label[1:], p['currentScore'], p['currentBand'], E['target'], gbp(p['cost']),
                         table('Route to band %s for %s' % (E['target'], label), ['Upgrade, cheapest per point first', 'Points', 'Cost', 'Reaches'], rows_), html.escape(link, quote=True)))
        plan_answer = plan_answer or ('For %s, about %s in our model, starting from band %s.' % (label, gbp(p['cost']), p['currentBand']))
    starts = [p['currentScore'] for p in plans]
    calib = ('Our model starts %s at %d points' % (E['examples'][0][3], starts[0])) + (' and %s at %d' % (E['examples'][1][3], starts[1]) if len(starts) > 1 else '')
    period_cap = E['period'][0].upper() + E['period'][1:]
    faq = [('What EPC rating does a %s home usually have?' % E['short'],
            'Band %s on average: homes built %s average %d points in the English Housing Survey 2024, against %d for all homes. About %s are band C or better, and %s are band E or worse.'
            % (band_of(sap), E['period'], round(sap), round(allh['bands']['SAP']), pct(abc), pct(efg))),
           ('Can a %s home reach EPC band %s?' % (E['short'], E['target']),
            ('Yes: %s of homes built %s are already band %s or better. ' % (pct(abc if E['target'] == 'C' else bshare['A/B']), E['period'], E['target'])) + plan_answer),
           ('Why do older homes have lower EPC ratings?',
            'Walls are a big part of it. The rating models what a home costs to heat per square metre, and solid walls lose far more heat than filled cavity walls; %s of homes built before 1919 have solid walls with no insulation.' % pct(ages['pre-1919']['walls']['solid uninsulated']))]
    body = f"""
<p class="lead"><strong>{pct(abc)}</strong> of homes in England built {E['period']} are EPC band C or better, against {pct(allh['bands']['A/B/C'])} of all homes. Their average rating is <strong>{round(sap)} points, band {band_of(sap)}</strong>, and {pct(efg)} are band E or worse.</p>

<h2 id="bands">How {E['short']} homes rate</h2>
<p class="answer"><strong>{band_word}.</strong> There are about {homes / 1000:.1f} million of these homes in England; the table shows how their EPC bands compare with all homes.</p>
{bands_tbl}

<h2 id="features">What these homes are like</h2>
<p class="answer"><strong>Walls: {wall_txt}.</strong> Loft insulation and double glazing are common in homes of every age.</p>
{feat_tbl}

<h2 id="gas">How much gas they use</h2>
<p class="answer"><strong>A median {ng[E['need'][0]]:,} kWh of gas a year</strong> for homes built {need_period(E['need'][0])}, against {ng['All dwellings']:,} kWh for all homes, from meter readings.</p>
{gas_tbl}

<h2 id="route">Getting to band {E['target']}</h2>
<p class="answer"><strong>{plan_answer}</strong> {calib}; the survey average for these homes is {round(sap)}.</p>
{plan_html}

<h2 id="help">Rules and grants</h2>
<p class="answer"><strong>Landlords need band C by 1 October 2030.</strong> Check a rented home with the <a href="/landlord-epc-calculator/">landlord EPC calculator</a>.</p>
<p>ECO4 can fund insulation for households on qualifying benefits until 31 December 2026, and the Boiler Upgrade Scheme gives £7,500 off a heat pump. Read more about {', '.join('<a href="%s">%s</a>' % l for l in E['links'])}, or see <a href="/guides/epc-rating-by-house-age/">EPC ratings for every age of home</a>.</p>
<p class="note">EPC bands and home features: English Housing Survey 2024, live tables DA7101, DA6201 and DA6101 (MHCLG, updated {long_date_str(A['ehs_published'])}), England. Gas use: NEED consumption tables 2026 (DESNZ), 2024 meter readings, England and Wales, whose age bands differ slightly from the survey's. The routes to band {E['target']} are our simple EPC points model, the same as our EPC calculator, not the government's SAP software, for a home with loft insulation, double glazing and a gas boiler under 15 years old.</p>
"""
    title = 'EPC Rating for a %s: Band %s on Average' % (E['tname'], band_of(sap))
    if len(title) > 60:
        title = 'EPC Rating for a %s, 2026' % E['tname']
    return dict(slug=E['slug'], kind='home', provenance='official statistics and our published model', title=title,
                description=('%s of homes built %s are EPC band C or better; the average is band %s. What they are like, their gas use and %s band %s.'
                             % (pct(abc).capitalize(), E['period'], band_of(sap), 'how close they are to' if all(p.get('met') for p in plans) else 'the route to', E['target']))[:155],
                h1='EPC rating for a %s home' % E['short'], crumb='EPC rating, %s homes' % E['short'], faq=faq, body=body,
                sources=['Ministry of Housing, Communities and Local Government, <a href="https://www.gov.uk/government/statistical-data-sets/energy-performance" target="_blank" rel="noopener">English Housing Survey live tables on energy performance</a>, DA7101, DA6201 and DA6101, 2024.',
                         'Department for Energy Security and Net Zero, <a href="https://www.gov.uk/government/statistics/national-energy-efficiency-data-framework-need-consumption-data-tables-2026" target="_blank" rel="noopener">NEED consumption data tables 2026</a>, headline Table 7 and gas per square metre Table 4.2.',
                         'Our <a href="/epc-calculator/">EPC calculator</a> points model, <a href="/js/epc-plan.js">js/epc-plan.js</a>.'])


def epc_age_hub():
    A = json.loads((ROOT / 'docs' / 'epc-by-age.json').read_text())
    ages = A['ages']
    order = ['pre-1919', '1919-44', '1945-64', '1965-80', '1981-90', '1991-2002', '2003-2013', 'post-2013', 'all dwellings']
    page_for = {}
    for E in AGE_ERAS:
        for r in E['ehs']:
            page_for[r] = E['slug']
    name = lambda k: ('<a href="/guides/%s/">%s</a>' % (page_for[k], AGE_LABEL[k])) if k in page_for else AGE_LABEL[k]
    rows = [[name(k), '%.1f million' % (ages[k]['homes_000'] / 1000), pct(ages[k]['bands']['A/B/C']), pct(ages[k]['bands']['E/F/G']),
             '%d (band %s)' % (round(ages[k]['bands']['SAP']), band_of(ages[k]['bands']['SAP']))] for k in order]
    tbl = table('EPC rating by age of home', ['Built', 'Homes in England', 'Band C or better', 'Band E or worse', 'Average rating'], rows)
    bars = ''.join('<div class="age-bar"><span class="ab-l">%s</span><span class="ab-t"><span class="ab-f" style="width:%d%%"></span></span><span class="ab-v">%s</span></div>'
                   % (AGE_LABEL[k], round(ages[k]['bands']['A/B/C']), pct(ages[k]['bands']['A/B/C'])) for k in order[:-1])
    ng, nm = A['need_gas_median'], A['need_gas_per_m2_houses']
    solid = lambda k: (ages[k]['walls']['solid uninsulated'] or 0) + (ages[k]['walls']['solid insulated'] or 0)
    gas_tbl = table('Gas use by age of home', ['Built', 'Median gas a year', 'Median gas per square metre (houses)'],
                    [[NEED_LABEL[k], f"{ng[k]:,} kWh", ('%d kWh' % nm[k]) if k in nm else 'not published'] for k in ['Pre 1919', '1919 - 1944', '1945 - 1964', '1965 - 1982', '1983 - 1992', '1993 - 1999', '2000 - 2011', '2012 onwards', 'All dwellings']])
    faq = [('Do older houses have worse EPC ratings?',
            'Yes. In the English Housing Survey 2024, %s of homes built before 1919 are band C or better, against %s of homes built after 2013. The average rating rises from %d points for the oldest homes to %d for the newest.'
            % (pct(ages['pre-1919']['bands']['A/B/C']), pct(ages['post-2013']['bands']['A/B/C']), round(ages['pre-1919']['bands']['SAP']), round(ages['post-2013']['bands']['SAP']))),
           ('Which homes use the most gas?',
            'Homes built between 1919 and 1944, a median %s kWh a year and %d kWh per square metre in houses, slightly more than homes built before 1919 (%s kWh and %d kWh). Homes built since 2012 use a median %s kWh.'
            % (f"{ng['1919 - 1944']:,}", nm['1919 - 1944'], f"{ng['Pre 1919']:,}", nm['Pre 1919'], f"{ng['2012 onwards']:,}"))]
    body = f"""
<p class="lead">The older the home, the lower its EPC rating: <strong>{pct(ages['pre-1919']['bands']['A/B/C'])}</strong> of homes built before 1919 are band C or better, against <strong>{pct(ages['post-2013']['bands']['A/B/C'])}</strong> of homes built after 2013. Choose your home's age for what it is typically like and the route to band C.</p>
<div class="age-bars" aria-hidden="true"><p class="ab-h">Share of homes at band C or better</p>{bars}</div>

<h2 id="by-age">EPC rating by age of home</h2>
<p class="answer"><strong>Older homes are far more likely to have solid walls.</strong> {pct(solid('pre-1919'))} of homes built before 1919 have them and {pct(solid('1919-44'))} of those built 1919 to 1944; solid walls lose far more heat than filled cavity walls.</p>
{tbl}

<h2 id="gas">Gas use by age of home</h2>
<p class="answer"><strong>Homes built between the wars use the most.</strong> Per square metre, a house built before 1919 uses a median {nm['Pre 1919']} kWh of gas a year and one built since 2000 uses {nm['2000 onwards']}.</p>
{gas_tbl}

<h2 id="yours">Your home's age</h2>
<ul>{''.join('<li><a href="/guides/%s/">EPC rating for a %s home</a>, built %s</li>' % (E['slug'], E['short'], E['period']) for E in AGE_ERAS)}</ul>
<p>Or estimate your own home's rating and the cheapest route to band C in the <a href="/epc-calculator/">EPC calculator</a>.</p>
<p class="note">English Housing Survey 2024, live tables DA7101 (MHCLG, updated {long_date_str(A['ehs_published'])}), England. Gas use: NEED consumption tables 2026 (DESNZ), 2024 meter readings, England and Wales.</p>
"""
    return dict(slug='epc-rating-by-house-age', kind='home', provenance='official statistics and our published model', title='EPC Rating by House Age: Victorian to New Build, 2026',
                description='How EPC ratings change with the age of a home, from %s at band C or better before 1919 to %s after 2013, with gas use and the route to band C.'
                            % (pct(ages['pre-1919']['bands']['A/B/C']), pct(ages['post-2013']['bands']['A/B/C'])),
                h1='EPC rating by house age', crumb='EPC rating by house age', faq=faq, body=body,
                sources=['Ministry of Housing, Communities and Local Government, <a href="https://www.gov.uk/government/statistical-data-sets/energy-performance" target="_blank" rel="noopener">English Housing Survey live tables on energy performance</a>, DA7101, 2024.',
                         'Department for Energy Security and Net Zero, <a href="https://www.gov.uk/government/statistics/national-energy-efficiency-data-framework-need-consumption-data-tables-2026" target="_blank" rel="noopener">NEED consumption data tables 2026</a>.'])


# ------------------------------------------------------------------ energy use by council
# docs/energy-councils.json from need_councils.py: DESNZ NEED local authority tables 2024.
EN_BINS = {'gas': [8500, 9500, 10500, 11500], 'elec': [2300, 2500, 2700, 2900]}
EN_COLS = ['#fdf1dc', '#f5d49a', '#e6ad5c', '#c7852b', '#8f5710']
EN_LABELS = {'gas': ['Under 8,500 kWh', '8,500 to 9,500', '9,500 to 10,500', '10,500 to 11,500', '11,500 kWh or more'],
             'elec': ['Under 2,300 kWh', '2,300 to 2,500', '2,500 to 2,700', '2,700 to 2,900', '2,900 kWh or more']}
TYPE_LABEL = {'Detached': 'Detached house', 'Semi detached': 'Semi-detached house', 'Mid terrace': 'Mid-terrace house', 'End terrace': 'End-terrace house',
              'Bungalow': 'Bungalow', 'Converted flat': 'Converted flat', 'Purpose built flat': 'Purpose built flat'}


def en_bin(kind, v):
    return None if v is None else sum(v >= b for b in EN_BINS[kind])


def gas_cost(k):
    return k * RG + SCG


def elec_cost(k):
    return k * RE + 200.13


def energy_council_page():
    N = json.loads((ROOT / 'docs' / 'energy-councils.json').read_text())
    B = json.loads((ROOT / 'docs' / 'bus-councils.json').read_text())
    MP = json.loads((ROOT / 'docs' / 'maps' / 'lad-2025-ew.json').read_text())
    C, BC = N['councils'], B['councils']
    fmt = lambda x: f'{x:,}'
    nm = lambda c: council_name(BC[c]['name'])
    pages = set(B.get('pages', []))
    link = lambda c: ('<a href="/guides/%s/">%s</a>' % (council_slug(BC[c]['name']), html.escape(nm(c)))) if c in pages else html.escape(nm(c))

    def svg(mp, cls, label):
        out = []
        for c, d in mp['paths'].items():
            gb, eb = en_bin('gas', C[c]['gas']), en_bin('elec', C[c]['elec'])
            fill = EN_COLS[gb] if gb is not None else '#e4e2dc'
            out.append('<path d="%s" fill="%s" data-c="%s" data-g="%s" data-e="%s"><title>%s</title></path>'
                       % (d, fill, c, '' if gb is None else gb, '' if eb is None else eb, html.escape(nm(c))))
        return '<svg class="%s" viewBox="0 0 %d %d" role="img" aria-label="%s">%s</svg>' % (cls, mp['w'], mp['h'], label, ''.join(out))

    legend = lambda kind: '<ul class="hp-legend" data-kind="%s"%s>%s</ul>' % (kind, '' if kind == 'gas' else ' hidden', ''.join(
        '<li><span style="background:%s"></span>%s</li>' % (EN_COLS[i], EN_LABELS[kind][i]) for i in range(5)))
    gas_rank = sorted([c for c in C if C[c]['gas']], key=lambda c: -C[c]['gas'])
    el_rank = sorted([c for c in C if C[c]['elec']], key=lambda c: -C[c]['elec'])
    head = ['Council', 'Region', 'Median a year', 'Typical cost a year']
    row_g = lambda c: [link(c), BC[c]['region'], fmt(C[c]['gas']) + ' kWh', gbp(gas_cost(C[c]['gas']))]
    row_e = lambda c: [link(c), BC[c]['region'], fmt(C[c]['elec']) + ' kWh', gbp(elec_cost(C[c]['elec']))]
    regs = sorted(N['regions'].values(), key=lambda r: -r['gas'])
    reg_name = lambda n: {'East': 'East of England', 'Yorkshire and The Humber': 'Yorkshire and the Humber'}.get(n, n)
    reg_rows = [[reg_name(r['name']),
                 fmt(r['gas']) + ' kWh', fmt(r['elec']) + ' kWh', gbp(gas_cost(r['gas']) + elec_cost(r['elec']))] for r in regs]
    all_rows = [[link(c), BC[c]['region'], (fmt(C[c]['gas']) + ' kWh') if C[c]['gas'] else 'no mains gas', fmt(C[c]['elec']) + ' kWh'] for c in sorted(C, key=lambda c: nm(c))]
    ew = N['ew']
    data = {c: [nm(c), C[c]['gas'], C[c]['elec'], (gas_rank.index(c) + 1) if C[c]['gas'] else None, el_rank.index(c) + 1, BC[c]['region']]
            + (['/guides/%s/' % council_slug(BC[c]['name'])] if c in pages else []) for c in C}
    names = ''.join('<option value="%s">' % html.escape(nm(c)) for c in sorted(C, key=nm))
    ew_total = gas_cost(ew['gas']) + elec_cost(ew['elec'])
    faq = [('How much gas does a typical home use?',
            'A median %s kWh a year across England and Wales, among homes with a gas meter, and %s kWh of electricity, from 2024 meter readings. At the October to December 2026 price cap that is about %s for gas and %s for electricity, including standing charges.'
            % (fmt(ew['gas']), fmt(ew['elec']), gbp(gas_cost(ew['gas'])), gbp(elec_cost(ew['elec'])))),
           ('Which council uses the most gas?',
            '%s, where the median home with gas uses %s kWh a year, followed by %s and %s.'
            % (nm(gas_rank[0]), fmt(C[gas_rank[0]]['gas']), nm(gas_rank[1]), nm(gas_rank[2]))),
           ('Why is gas use low in Cornwall?',
            'Homes of every type in Cornwall use less gas than the England and Wales median: a semi-detached house %s kWh against %s. The figure covers only homes with a gas meter, and many Cornish homes are off the gas grid; Cornwall also has the %s highest rate of Boiler Upgrade Scheme heat pumps per household of any council.' % (fmt(C['E06000052']['gas_type']['Semi detached']), fmt(ew['gas_type']['Semi detached']), ordinal(BC['E06000052']['rank'])))]
    body = f"""
<p class="lead">A typical home in England and Wales uses <strong>{fmt(ew['gas'])} kWh</strong> of gas and <strong>{fmt(ew['elec'])} kWh</strong> of electricity a year, about <strong>{gbp(ew_total)}</strong> at the October 2026 price cap. Here is how much homes use in every council, from the government's 2024 meter readings.</p>

<div class="en-toggle" role="group" aria-label="Show on the map"><button type="button" data-kind="gas" aria-pressed="true">Gas</button><button type="button" data-kind="elec" aria-pressed="false">Electricity</button></div>
<div class="hp-map-wrap">
<figure class="hp-map">{svg(MP['main'], 'hp-main', 'Map of England and Wales by council, shaded by median energy use per home')}
<figcaption>Median use per home a year, by council.{legend('gas')}{legend('elec')}</figcaption></figure>
<div class="hp-side">
<label for="councilSearch">Find your council</label>
<input id="councilSearch" list="councilNames" autocomplete="off" placeholder="e.g. Leeds"><datalist id="councilNames">{names}</datalist>
<div class="hp-panel" id="councilPanel" aria-live="polite"><p class="rp-hint">Search for a council, or hover over the map.</p></div>
<figure class="hp-london">{svg(MP['london'], 'hp-ldn', 'London boroughs, shaded by median energy use per home')}<figcaption>London, enlarged</figcaption></figure>
</div>
</div>

<h2 id="gas-most">Where homes use the most gas</h2>
<p class="answer"><strong>Outer London and Surrey.</strong> The median home with gas in {html.escape(nm(gas_rank[0]))} uses {fmt(C[gas_rank[0]]['gas'])} kWh.</p>
{table('Councils where homes use the most gas', head, [row_g(c) for c in gas_rank[:10]])}

<h2 id="gas-least">Where homes use the least gas</h2>
<p class="answer"><strong>Inner London and the South West.</strong> Where many homes are off the gas grid, the figure covers only those on it.</p>
{table('Councils where homes use the least gas', head, [row_g(c) for c in reversed(gas_rank[-10:])])}

<h2 id="elec">Electricity</h2>
<p class="answer"><strong>Highest in Surrey and off-grid areas, lowest in inner London.</strong> The Isles of Scilly, with no mains gas, top the table at {fmt(C['E06000053']['elec'])} kWh.</p>
{table('Councils where homes use the most electricity', head, [row_e(c) for c in el_rank[:10]])}

<h2 id="regions">By region</h2>
<p class="answer"><strong>The South West uses the least gas, London the most.</strong></p>
{table('Median energy use by region', ['Region', 'Gas', 'Electricity', 'Typical cost of both a year'], reg_rows)}

<h2 id="all">Every council</h2>
<p class="answer"><strong>All {len(C)} councils in England and Wales.</strong></p>
<details class="more"><summary>Show every council</summary>
{table('Median energy use in every council', ['Council', 'Region', 'Gas', 'Electricity'], all_rows)}
</details>
<p class="note">Median gas and electricity per home from the NEED local authority tables 2024 (DESNZ, published {long_date_str(N['published'])}): the gas year runs mid-May 2024 to mid-May 2025 and covers homes with a gas meter; the electricity year runs February 2024 to January 2025. Typical costs are the medians priced at the Ofgem cap for October to December 2026, with standing charges. Compare your own bill with the <a href="/energy-bill-calculator/">energy bill calculator</a>.</p>
<script>
(function () {{
    var D = {json.dumps(data, ensure_ascii=False, separators=(',', ':'))};
    var COLS = {json.dumps(EN_COLS)}, kind = 'gas';
    var byName = {{}}; Object.keys(D).forEach(function (c) {{ byName[D[c][0].toLowerCase()] = c; }});
    var panel = document.getElementById('councilPanel'), input = document.getElementById('councilSearch');
    var gp = {RG}, gs = {SCG}, ep = {RE}, es = 200.13, ewg = {ew['gas']}, ewe = {ew['elec']};
    function money(v) {{ return '£' + Math.round(v).toLocaleString('en-GB'); }}
    function show(c) {{
        var d = D[c]; if (!d) {{ return; }}
        var g = d[1] ? '<p><strong>' + d[1].toLocaleString('en-GB') + ' kWh</strong> of gas, about ' + money(d[1] * gp + gs) + ' a year, ' + (d[1] > ewg ? 'above' : 'below') + ' the England and Wales median of ' + ewg.toLocaleString('en-GB') + '.</p>' : '<p>No mains gas.</p>';
        panel.innerHTML = '<h3>' + d[0] + '</h3>' + g + '<p><strong>' + d[2].toLocaleString('en-GB') + ' kWh</strong> of electricity, about ' + money(d[2] * ep + es) + ' a year.</p><p>' + d[5] + '.</p>'
            + (d[6] ? '<p><a href="' + d[6] + '">More on ' + d[0] + '</a></p>' : '');
        document.querySelectorAll('.hp-map-wrap path.on').forEach(function (p) {{ p.classList.remove('on'); }});
        document.querySelectorAll('.hp-map-wrap path[data-c="' + c + '"]').forEach(function (p) {{ p.classList.add('on'); }});
    }}
    function paint(k) {{
        kind = k;
        document.querySelectorAll('.hp-map-wrap path[data-c]').forEach(function (p) {{
            var b = p.getAttribute(k === 'gas' ? 'data-g' : 'data-e');
            p.setAttribute('fill', b === '' ? '#e4e2dc' : COLS[+b]);
        }});
        document.querySelectorAll('.hp-legend').forEach(function (l) {{ l.hidden = l.getAttribute('data-kind') !== k; }});
        document.querySelectorAll('.en-toggle button').forEach(function (b) {{ b.setAttribute('aria-pressed', b.getAttribute('data-kind') === k ? 'true' : 'false'); }});
    }}
    document.querySelectorAll('.en-toggle button').forEach(function (b) {{ b.addEventListener('click', function () {{ paint(b.getAttribute('data-kind')); }}); }});
    document.querySelectorAll('.hp-map-wrap svg').forEach(function (svg) {{
        svg.addEventListener('mouseover', function (e) {{ var c = e.target.getAttribute && e.target.getAttribute('data-c'); if (c) {{ show(c); }} }});
    }});
    function find() {{ var c = byName[input.value.trim().toLowerCase()]; if (c) {{ show(c); }} }}
    input.addEventListener('change', find); input.addEventListener('input', find);
}})();
</script>
"""
    return dict(slug='energy-use-by-council', kind='none', provenance='official statistics', title='Energy Use by Council: Gas and Electricity Mapped, 2026',
                description='How much gas and electricity a typical home uses in every council in England and Wales, and what it costs, on a map. Find your council.',
                h1='Energy use by council', crumb='Energy use by council', faq=faq, body=body,
                sources=['Department for Energy Security and Net Zero, <a href="https://www.gov.uk/government/statistics/national-energy-efficiency-data-framework-need-consumption-data-tables-2026" target="_blank" rel="noopener">NEED consumption data tables 2026</a>, local authority tables 2024, LA1 and LA2.',
                         'Ofgem energy price cap, October to December 2026.',
                         'Map: Office for National Statistics, Local Authority Districts (May 2025) boundaries, Open Government Licence v3.0. Contains OS data &copy; Crown copyright and database right 2025.'])


# ------------------------------------------------------------------ solar output by council
# docs/solar-councils.json from pvgis_councils.py: PVGIS output averaged over up to 8 places
# where people live in each council. The map is docs/maps/lad-2025-uk.json.
SO_BINS = [900, 950, 1000, 1050]
SO_COLS = ['#c3cedc', '#f6e3a1', '#f0c64f', '#e29a1f', '#b8650c']
SO_LABELS = ['Under 900 kWh', '900 to 950', '950 to 1,000', '1,000 to 1,050', '1,050 kWh or more']
CALC_REGION = {'London': 'south', 'South East': 'south', 'South West': 'south', 'East': 'south', 'East Midlands': 'midlands',
               'West Midlands': 'midlands', 'North East': 'north', 'North West': 'north', 'Yorkshire and the Humber': 'north',
               'Wales': 'wales', 'Scotland': 'scotland'}
REGION_NAME = {'East': 'East of England', 'Yorkshire and The Humber': 'Yorkshire and the Humber'}


def solar_council_page():
    D = json.loads((ROOT / 'docs' / 'solar-councils.json').read_text())
    MP = json.loads((ROOT / 'docs' / 'maps' / 'lad-2025-uk.json').read_text())
    C = D['councils']
    n, med = len(C), D['median']
    fmt = lambda x: f'{x:,}'
    rname = lambda r: REGION_NAME.get(r, r)
    order = sorted(C, key=lambda c: C[c]['rank'])
    top, bottom = order[0], order[-1]
    kbin = lambda v: sum(v >= b for b in SO_BINS)
    the = lambda c: ('the ' if C[c]['name'].endswith('Islands') else '') + C[c]['name']

    def svg(mp, cls, label, shetland=False):
        out = []
        for c, d in mp['paths'].items():
            out.append('<path d="%s" fill="%s" data-c="%s"><title>%s</title></path>' % (d, SO_COLS[kbin(C[c]['kwh'])], c, html.escape(C[c]['name'])))
        if shetland and mp.get('shetland_box'):
            x0, y0, x1, y1 = mp['shetland_box']
            out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="none" stroke="#8a8a80" stroke-width="0.8"/>' % (x0, y0, x1 - x0, y1 - y0))
        return '<svg class="%s" viewBox="0 0 %d %d" role="img" aria-label="%s">%s</svg>' % (cls, mp['w'], mp['h'], label, ''.join(out))

    legend = '<ul class="hp-legend">%s</ul>' % ''.join('<li><span style="background:%s"></span>%s</li>' % (SO_COLS[i], SO_LABELS[i]) for i in range(5))

    def row(c):
        return [html.escape(C[c]['name']), html.escape(rname(C[c]['region'])), fmt(C[c]['kwh']) + ' kWh', fmt(C[c]['kwh'] * 4) + ' kWh']
    head = ['Council', 'Region', 'Per kW of panels', 'A 4 kW system']
    regs = {}
    for c in C:
        regs.setdefault(C[c]['region'], []).append(C[c]['kwh'])
    reg_order = sorted(regs, key=lambda r: -sum(regs[r]) / len(regs[r]))
    reg_rows = []
    for r in reg_order:
        v = regs[r]
        cell = html.escape(rname(r))
        if r in CALC_REGION:
            cell = '<a href="/guides/%s/">%s</a>' % (REGION[CALC_REGION[r]]['slug'], cell)
        reg_rows.append([cell, fmt(round(sum(v) / len(v))) + ' kWh', '%s to %s kWh' % (fmt(min(v)), fmt(max(v)))])
    vals = sorted(C[c]['kwh'] for c in C)
    q1, q3 = vals[len(vals) // 4], vals[(3 * len(vals)) // 4]
    within = round(max(med - q1, q3 - med) / med * 100)
    scot = D['nations']['Scotland']['mean']
    scot_pct = round((1 - scot / med) * 100)
    data = {c: [C[c]['name'], C[c]['kwh'], C[c]['rank'], rname(C[c]['region'])]
            + (['/guides/%s/' % REGION[CALC_REGION[C[c]['region']]]['slug'], REGION[CALC_REGION[C[c]['region']]]['name']] if C[c]['region'] in CALC_REGION else [])
            for c in C}
    names = ''.join('<option value="%s">' % html.escape(C[c]['name']) for c in sorted(C, key=lambda c: C[c]['name']))
    all_rows = [[html.escape(C[c]['name']), html.escape(rname(C[c]['region'])), fmt(C[c]['kwh']) + ' kWh', str(C[c]['rank'])] for c in sorted(C, key=lambda c: C[c]['name'])]
    faq = [('Which part of the UK gets the most solar power?',
            'The south coast of England. %s tops the table at %s kWh a year for each kW of panels on a south facing roof, followed by %s and %s.'
            % (C[top]['name'], fmt(C[top]['kwh']), C[order[1]]['name'], C[order[2]]['name'])),
           ('Do solar panels work in Scotland?',
            'Yes. A south facing roof in the average Scottish council makes %s kWh a year for each kW of panels, about %d%% less than the UK median of %s kWh. Payback takes longer; see <a href="/guides/solar-panel-payback-scotland/">solar payback in Scotland</a>.'
            % (fmt(scot), scot_pct, fmt(med))),
           ('How are these figures worked out?',
            'We ran the European Commission\'s PVGIS model for up to %d places where people live in each council, and averaged them: 1 kW of panels facing due south at a 35 degree pitch with 14%% losses, on the SARAH3 sunshine record for 2005 to 2023.' % D['points_per_council'])]
    body = f"""
<p class="lead">In the median UK council, each kW of solar panels on a south facing roof makes <strong>{fmt(med)} kWh</strong> a year, about <strong>{fmt(med * 4)} kWh</strong> from a typical 4 kW system. That runs from {fmt(C[top]['kwh'])} kWh in {html.escape(the(top))} to {fmt(C[bottom]['kwh'])} kWh in {html.escape(the(bottom))}.</p>

<div class="hp-map-wrap">
<figure class="hp-map">{svg(MP['main'], 'hp-main', 'Map of the UK by council, shaded by solar output per kW of panels', True)}
<figcaption>Output a year for each kW of panels on a clean south facing roof, by council. Shetland is shown in the box.{legend}</figcaption></figure>
<div class="hp-side">
<label for="councilSearch">Find your council</label>
<input id="councilSearch" list="councilNames" autocomplete="off" placeholder="e.g. Bristol"><datalist id="councilNames">{names}</datalist>
<div class="hp-panel" id="councilPanel" aria-live="polite"><p class="rp-hint">Search for a council, or hover over the map.</p></div>
<figure class="hp-london">{svg(MP['london'], 'hp-ldn', 'London boroughs, shaded by solar output')}<figcaption>London, enlarged</figcaption></figure>
</div>
</div>

<h2 id="most">The sunniest councils</h2>
<p class="answer"><strong>The Sussex coast.</strong> {html.escape(C[top]['name'])} makes {fmt(C[top]['kwh'])} kWh a year for each kW of panels, {round((C[top]['kwh'] / med - 1) * 100)}% more than the UK median.</p>
{table('Councils with the most solar output', head, [row(c) for c in order[:10]])}

<h2 id="least">The least sunny councils</h2>
<p class="answer"><strong>The Scottish Highlands and islands.</strong> {html.escape(the(bottom)[0].upper() + the(bottom)[1:])} make{'' if the(bottom).startswith('the ') else 's'} {fmt(C[bottom]['kwh'])} kWh, {round((1 - C[bottom]['kwh'] / med) * 100)}% less than the median, but panels still work there.</p>
{table('Councils with the least solar output', head, [row(c) for c in order[-10:]])}

<h2 id="regions">By region</h2>
<p class="answer"><strong>{html.escape(rname(reg_order[0]))} leads and {html.escape(rname(reg_order[-1]))} trails.</strong> Each region links to what panels cost and save there.</p>
{table('Solar output by region, per kW of panels', ['Region', 'Average council', 'Range'], reg_rows)}

<h2 id="matter">How much does location matter?</h2>
<p class="answer"><strong>Less than your roof.</strong> Half of all councils are within {within}% of the median; turning panels from south to east or west costs about 20%.</p>
<p>Shading, roof direction and pitch usually matter more than which council you live in. The <a href="/solar-calculator/">solar calculator</a> takes your postcode, roof direction and pitch, and uses the PVGIS figure for your postcode district less 7% for shading and dirt on the panels.</p>

<h2 id="all">Every council</h2>
<p class="answer"><strong>All {n} councils in the UK, ranked.</strong></p>
<details class="more"><summary>Show every council</summary>
{table('Solar output in every council, per kW of panels', ['Council', 'Region', 'Per kW of panels', 'Rank'], all_rows)}
</details>
<p class="note">Modelled with PVGIS 5.3 (European Commission Joint Research Centre), PVGIS-SARAH3 database for 2005 to 2023: 1 kW of crystalline silicon panels, building mounted, facing due south at 35 degrees, 14% system losses, the same settings as the city table on our solar calculator. Each council's figure is the average over up to {D['points_per_council']} places where people live: ONS population weighted centres of MSOAs in England and Wales, Scottish Government Intermediate Zone centres in Scotland (weighted by households), and the largest town in each Northern Ireland council. Queried {long_date_str(D['queried'])}.</p>
<script>
(function () {{
    var D = {json.dumps(data, ensure_ascii=False, separators=(',', ':'))};
    var byName = {{}}; Object.keys(D).forEach(function (c) {{ byName[D[c][0].toLowerCase()] = c; }});
    var panel = document.getElementById('councilPanel'), input = document.getElementById('councilSearch'), med = {med}, n = {n};
    function f(v) {{ return v.toLocaleString('en-GB'); }}
    function show(c) {{
        var d = D[c]; if (!d) {{ return; }}
        var pct = Math.round((d[1] / med - 1) * 100);
        panel.innerHTML = '<h3>' + d[0] + '</h3><p><strong>' + f(d[1]) + ' kWh</strong> a year for each kW of panels, about ' + f(d[1] * 4) + ' kWh from a 4 kW system.</p>'
            + '<p>Ranked ' + d[2] + ' of ' + n + ', ' + (pct === 0 ? 'the same as' : Math.abs(pct) + '% ' + (pct > 0 ? 'above' : 'below')) + ' the UK median.</p>'
            + (d[4] ? '<p><a href="' + d[4] + '">What solar panels save in ' + d[5] + '</a></p>' : '<p><a href="/solar-calculator/">Try the solar calculator</a></p>');
        document.querySelectorAll('.hp-map-wrap path.on').forEach(function (p) {{ p.classList.remove('on'); }});
        document.querySelectorAll('.hp-map-wrap path[data-c="' + c + '"]').forEach(function (p) {{ p.classList.add('on'); }});
    }}
    document.querySelectorAll('.hp-map-wrap svg').forEach(function (svg) {{
        svg.addEventListener('mouseover', function (e) {{ var c = e.target.getAttribute && e.target.getAttribute('data-c'); if (c) {{ show(c); }} }});
    }});
    function find() {{ var c = byName[input.value.trim().toLowerCase()]; if (c) {{ show(c); }} }}
    input.addEventListener('change', find); input.addEventListener('input', find);
}})();
</script>
"""
    return dict(slug='solar-output-by-council', kind='none', provenance="the European Commission's PVGIS model and official statistics", title='Solar Panel Output by Council: UK Map, 2026',
                description='How much electricity solar panels make in every UK council, from the European Commission PVGIS model, on a map. Find your council.',
                h1='Solar panel output by council', crumb='Solar output by council', faq=faq, body=body,
                sources=['European Commission Joint Research Centre, <a href="https://re.jrc.ec.europa.eu/pvg_tools/en/" target="_blank" rel="noopener">PVGIS 5.3</a>, PVGIS-SARAH3 database.',
                         'Office for National Statistics, <a href="https://geoportal.statistics.gov.uk/" target="_blank" rel="noopener">MSOA (December 2021) population weighted centroids</a>, Open Government Licence v3.0.',
                         'Scottish Government, <a href="https://www.spatialdata.gov.scot/" target="_blank" rel="noopener">Intermediate Zone 2022 centroids</a>, Open Government Licence v3.0.',
                         'Map: Office for National Statistics, Local Authority Districts (May 2025) boundaries, Open Government Licence v3.0. Contains OS data &copy; Crown copyright and database right 2025.'])


_BUS = json.loads((ROOT / 'docs' / 'bus-councils.json').read_text())
PAGES = {'what-size-heat-pump': what_size, 'energy-bills-3-bed-house': bills_3, 'energy-bills-4-bed-house': bills_4,
         'energy-bills-1-bed-flat': bills_1, 'energy-bills-2-bed-house': bills_2, 'energy-bills-5-bed-house': bills_5,
         'heat-pump-cost-3-bed-mid-terrace': mid_terrace_3, 'heat-pump-1930s-semi': semi_1930s,
         'insulation-cost-semi-detached-house': ins_semi, 'insulation-cost-detached-house': ins_detached,
         'insulation-cost-terraced-house': ins_terrace, 'insulation-cost-bungalow': ins_bungalow, 'insulation-cost-flat': ins_flat,
         'insulation-cost-by-house-type': ins_hub, 'solar-panel-payback-by-region': solar_hub, 'heat-pumps-by-council': hp_council_page, 'energy-use-by-council': energy_council_page, 'solar-output-by-council': solar_council_page, 'epc-rating-by-house-age': epc_age_hub,
         **{AGE_ERAS[i]['slug']: (lambda i=i: epc_age_page(i)) for i in range(len(AGE_ERAS))},
         **{council_slug(_BUS['councils'][c]['name']): (lambda c=c: hp_council_detail(c)) for c in _BUS['pages']},
         **{REGION[k]['slug']: (lambda k=k: solar_region_page(k)) for k in REGION}}


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
    # questions open one at a time, as on the answer-first pages
    faq_html = '\n'.join('<details class="faq-item" data-af><summary><h3>%s</h3></summary><p>%s</p></details>' % (q, a) for q, a in p['faq'])
    src_html = ''.join('<li>%s</li>' % s for s in p['sources'])
    nav = re.search(r'<nav class="nav">.*?</nav>', tpl, re.S).group(0).replace('<a href="/guides/">Guides</a>', '<a href="/guides/" class="active" aria-current="page">Guides</a>')
    page = head + '''</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
%s
<main id="main" tabindex="-1" class="guide-content">
<div class="breadcrumbs"><a href="/">Home</a><span>/</span><a href="/guides/">Guides</a><span>/</span>%s</div>
<h1>%s</h1>
<p class="note">Updated 25 September 2026. Every figure on this page comes from %s; see <a href="/accuracy/">where our data comes from</a>.</p>
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
''' % (nav, p['crumb'], p['h1'], p.get('provenance', 'our published model'), p['body'], faq_html, src_html)
    out = ROOT / 'guides' / p['slug'] / 'index.html'
    out.parent.mkdir(parents=True, exist_ok=True)
    # 'a 8 kW' reads wrong; sizes that start with a vowel sound take 'an'
    page = re.sub(r'\ba ((?:8|11|18)(?:\.\d)? kW)', r'an \1', page)
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
