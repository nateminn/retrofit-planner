#!/usr/bin/env python3
"""Stamp the shared page components onto every page: one footer with the newsletter
sign-up, and the right quote request form for the page's subject.

Why a generator: the site had 20 different footers and the quote form was pasted by hand
into 23 pages. Every component now lives here once, is wrapped in markers, and re-running
this script replaces it in place. Change the wording here, run it, and every page agrees.

Consent is the point of the forms. Each quote form has an unticked, required box whose
wording names who receives the details and says installers may pay us for the
introduction. The same wording travels with the submission in hidden fields
(consent_text, consent_version, source), so every lead in Netlify carries proof of what
the person agreed to, on which page, and when (Netlify stamps the time).

Usage: python3 docs/superpowers/tools/site_components.py [--apply]
"""
import re
import sys
import html
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
APPLY = '--apply' in sys.argv

CONTACT = 'hello@retrofitplanner.co.uk'
CONSENT_VERSION = 'intro-v2-2026-09-24'
NEWS_VERSION = 'newsletter-v2-2026-09-24'

TICK = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        '<polyline points="20 6 9 17 4 12"/></svg>')

PROPERTY = ('property', 'Property type', ['Flat', 'Terraced house', 'Semi-detached house', 'Detached house', 'Bungalow'])
HEATING = ('heating', 'Current heating', ['Gas boiler', 'Oil boiler', 'LPG boiler', 'Electric or storage heaters', 'Other or none'])
TIMING = ('timing', 'When are you looking to start?', ['Within 3 months', '3 to 6 months', '6 to 12 months', 'Just researching'])

KINDS = {
    'heat-pump': dict(
        form='heat-pump-quote', action='/quote-thanks/',
        h2='Get heat pump quotes for your home',
        who='MCS-certified heat pump installers',
        points=['MCS-certified installers only', '£7,500 grant, or £9,000 replacing oil or LPG', 'Free, with no obligation'],
        extra=[HEATING],
        timing=('timing', 'When are you looking to install?', TIMING[2])),
    'solar': dict(
        form='solar-quote', action='/quote-thanks/solar/',
        h2='Get solar panel quotes for your home',
        who='MCS-certified solar installers',
        points=['MCS-certified installers only', 'Needed for Smart Export Guarantee payments', 'Free, with no obligation'],
        extra=[('roof', 'Which way does your main roof face?', ['South', 'East or west', 'North', 'Not sure']),
               ('battery', 'Interested in a battery?', ['Yes', 'No', 'Not sure'])],
        timing=('timing', 'When are you looking to install?', TIMING[2])),
    'insulation': dict(
        form='insulation-quote', action='/quote-thanks/insulation/',
        h2='Get insulation quotes for your home',
        who='TrustMark-registered insulation installers',
        points=['TrustMark-registered installers only', 'Loft, cavity, solid wall and floor', 'Free, with no obligation'],
        extra=[('work', 'What do you want insulated?', ['Loft', 'Cavity walls', 'Solid walls', 'Floor', 'Draught-proofing', 'Not sure'])],
        timing=TIMING),
    'epc': dict(
        form='epc-quote', action='/quote-thanks/epc/',
        h2='Get quotes for a new EPC',
        who='accredited domestic energy assessors',
        points=['Accredited assessors only', 'Lodged on the national register', 'Free to ask, with no obligation'],
        extra=[('reason', 'Why do you need an EPC?', ['Selling', 'Letting', 'Improving my home', 'Applying for a grant', 'Other'])],
        timing=('timing', 'When do you need it?', ['Within 2 weeks', 'Within a month', '1 to 3 months', 'Just researching'])),
    'home': dict(
        form='home-upgrade-quote', action='/quote-thanks/home/',
        h2='Get quotes to upgrade your home',
        who='certified installers for the work I choose (MCS for heat pumps and solar, TrustMark for insulation)',
        sub_who='certified installers for the work you choose',
        points=['Certified installers only', 'Heat pumps, solar and insulation', 'Free, with no obligation'],
        extra=[('work', 'What do you want quotes for?', ['Heat pump', 'Solar panels', 'Insulation', 'Several of these', 'Not sure yet']), HEATING],
        timing=TIMING),
}

# Which form each page carries. Pages not listed carry none: legal and utility pages,
# the methodology (kept clean for anyone auditing it), thank-you pages and embeds.
HEAT_PUMP = ['heat-pump-calculator', 'boiler-vs-heat-pump'] + ['guides/' + g for g in [
    'heat-pump-cost-by-house-type', 'heat-pump-cost-3-bed-semi', 'heat-pump-cost-2-bed-terrace',
    'heat-pump-cost-4-bed-house', 'heat-pump-victorian-terrace', 'heat-pump-cost-3-bed-detached',
    'heat-pump-cost-end-terrace', 'heat-pump-cost-5-bed-house', 'heat-pump-1960s-house',
    'heat-pump-cost-2-bed-bungalow', 'heat-pump-cost-bungalow', 'heat-pump-flat', 'heat-pump-old-house',
    'heat-pump-running-costs', 'heat-pump-vs-new-boiler', 'storage-heaters-vs-heat-pump',
    'electric-boiler-vs-heat-pump', 'boiler-upgrade-scheme-guide', 'heat-pump-noise',
    'radiator-sizing-heat-pump', 'planning-permission-heat-pump', 'best-heat-pump-tariffs',
    'what-size-heat-pump', 'heat-pump-cost-3-bed-mid-terrace', 'heat-pump-1930s-semi']]
SOLAR = ['solar-calculator'] + ['guides/' + g for g in ['are-solar-panels-worth-it-uk', 'solar-battery-storage-uk', 'solar-panel-payback-uk']]
INSULATION = ['insulation-calculator'] + ['guides/' + g for g in [
    'diy-loft-insulation', 'draught-proofing-guide', 'free-loft-insulation-uk', 'how-long-loft-insulation-lasts',
    'is-cavity-wall-insulation-worth-it', 'is-loft-insulation-worth-it', 'solid-wall-insulation-cost',
    'underfloor-insulation-cost', 'condensation-mould-guide', 'great-british-insulation-scheme', 'eco4-scheme-explained']]
EPC = ['guides/epc-cost', 'guides/epc-rating-landlords']
HOME = ['', 'guides', 'grants', 'epc-calculator', 'about', 'retrofit-plan'] + ['guides/' + g for g in [
    'energy-bills-3-bed-house', 'energy-bills-4-bed-house', 'energy-bills-1-bed-flat', 'energy-bills-2-bed-house', 'energy-bills-5-bed-house',
    'how-epc-points-are-calculated', 'how-to-improve-epc-rating', 'energy-bills-by-epc-rating',
    'average-energy-bills-uk', 'energy-bills-by-household-size', 'home-upgrade-grant',
    'warm-homes-plan-2026', 'warm-home-discount']]
PAGE_KIND = {}
for kind, pages in (('heat-pump', HEAT_PUMP), ('solar', SOLAR), ('insulation', INSULATION), ('epc', EPC), ('home', HOME)):
    for p in pages:
        assert p not in PAGE_KIND, p
        PAGE_KIND[p] = kind

# Calculators show their form in a band that stays hidden until a result earns it.
BANDED = {'heat-pump-calculator', 'boiler-vs-heat-pump', 'solar-calculator', 'insulation-calculator', 'epc-calculator', 'retrofit-plan'}


def esc(s):
    return html.escape(s, quote=True)


def consent_text(k):
    return ('I agree that Retrofit Planner may pass my details to up to three %s covering my postcode, '
            'who may contact me by email or phone about a quote. Installers may pay Retrofit Planner a fee '
            'for the introduction. I can withdraw my consent at any time by emailing %s.' % (k['who'], CONTACT))


def select(field, label, options, fid):
    opts = '<option value="">Select</option>' + ''.join('<option>%s</option>' % o for o in options)
    return ('<div class="form-group"><label for="%s">%s</label><select id="%s" name="%s" required>%s</select></div>'
            % (fid, label, fid, field, opts))


def sub_who(k):
    return k.get('sub_who', k['who'])


def lead_form(kind, source):
    k = KINDS[kind]
    points = ''.join('<li>%s %s</li>' % (TICK, p) for p in k['points'])
    fields = ['<div class="form-group"><label for="qf-postcode">Postcode</label><input type="text" id="qf-postcode" '
              'name="postcode" required autocomplete="postal-code" placeholder="e.g. SW1A 1AA" '
              'pattern="^[A-Za-z]{1,2}[0-9][A-Za-z0-9]? ?[0-9][A-Za-z]{2}$" title="A UK postcode, for example SW1A 1AA"></div>',
              select(PROPERTY[0], PROPERTY[1], PROPERTY[2], 'qf-property')]
    for i, (field, label, options) in enumerate(k['extra']):
        fields.append(select(field, label, options, 'qf-' + field))
    t = k['timing']
    fields.append(select(t[0], t[1], t[2], 'qf-when'))
    fields += ['<div class="form-group"><label for="qf-name">Name</label><input type="text" id="qf-name" name="name" required autocomplete="name"></div>',
               '<div class="form-group"><label for="qf-email">Email</label><input type="email" id="qf-email" name="email" required autocomplete="email"></div>',
               '<div class="form-group"><label for="qf-phone">Phone (optional)</label><input type="tel" id="qf-phone" name="phone" autocomplete="tel"></div>']
    ct = consent_text(k)
    return (
        '<!-- lead-form:%s -->\n<section class="quote-form" id="quote">\n'
        '<h2>%s</h2>\n'
        '<p class="qf-sub">Tell us about your property and we will pass your request to up to three %s covering your postcode. It is free and there is no obligation to go ahead.</p>\n'
        '<ul class="qf-points">%s</ul>\n'
        '<form name="%s" method="POST" action="%s" data-netlify="true" netlify-honeypot="bot-field">\n'
        '<input type="hidden" name="form-name" value="%s">\n'
        '<input type="hidden" name="source" value="%s">\n'
        '<input type="hidden" name="consent_version" value="%s">\n'
        '<input type="hidden" name="consent_text" value="%s">\n'
        '<p class="qf-hp" hidden><label>Do not fill this in: <input name="bot-field"></label></p>\n'
        '<div class="qf-grid">\n%s\n</div>\n'
        '<label class="qf-consent"><input type="checkbox" name="share_ok" value="yes" required> %s</label>\n'
        '<button type="submit" class="btn-calculate">Request my free quotes</button>\n'
        '<p class="qf-small">It costs you nothing and never changes any figure on this site. We keep your request and the wording you agreed to as a record of your consent, and delete both after 12 months. See our <a href="/privacy/#quotes">privacy policy</a>.</p>\n'
        '</form>\n</section>\n<!-- /lead-form -->'
        % (kind, k['h2'], sub_who(k), points, k['form'], k['action'], k['form'], esc(source),
           CONSENT_VERSION, esc(ct), '\n'.join(fields), ct))


NEWS_TEXT = 'I would like email updates about changes to UK home energy rules, grants and prices. I can unsubscribe at any time.'

FOOTER_COLS = '''<div class="footer-inner"><div><div class="footer-brand">Retrofit Planner</div><p class="footer-about">Free tools to help UK homeowners plan energy-efficient home improvements.</p></div><div class="footer-col"><h3>Calculators</h3><a href="/retrofit-plan/">Retrofit Plan</a><a href="/heat-pump-calculator/">Heat Pump Cost Calculator</a><a href="/insulation-calculator/">Insulation Savings Calculator</a><a href="/epc-calculator/">EPC Improvement Planner</a><a href="/solar-calculator/">Solar Panel Cost Calculator</a><a href="/boiler-vs-heat-pump/">Boiler vs Heat Pump</a><a href="/grants/">Grant Eligibility Checker</a></div><div class="footer-col"><h3>Guides</h3><a href="/guides/heat-pump-cost-4-bed-house/">Heat Pump Cost: 4-Bed House</a><a href="/guides/heat-pump-cost-by-house-type/">Costs by House Type</a><a href="/guides/heat-pump-running-costs/">Heat Pump Running Costs</a><a href="/guides/best-heat-pump-tariffs/">Best Heat Pump Tariffs</a><a href="/guides/boiler-upgrade-scheme-guide/">BUS Grant Guide</a><a href="/guides/how-epc-points-are-calculated/">How EPC Points Are Calculated</a></div><div class="footer-col"><h3>Company</h3><a href="/about/">About Us</a><a href="/methodology/">Our Methodology</a><a href="/accuracy/">How Accurate We Are</a><a href="/privacy/">Privacy Policy</a><a href="/terms/">Terms of Use</a><a href="/embed/">Embed Our Calculators</a><a href="/contact/">Contact</a></div></div>'''

DEFAULT_ATTRIBUTION = ('Data from <a href="https://www.ofgem.gov.uk/check-if-energy-price-cap-affects-you" target="_blank" rel="noopener">Ofgem</a>, '
                       '<a href="https://energysavingtrust.org.uk/" target="_blank" rel="noopener">Energy Saving Trust</a>, and '
                       '<a href="https://www.gov.uk/" target="_blank" rel="noopener">GOV.UK</a>.')


def footer(source, attribution):
    news = (
        '<section class="footer-news" id="newsletter" aria-labelledby="fn-title">'
        '<div class="fn-copy"><h2 id="fn-title">Keep up to date with UK home energy rules</h2>'
        '<p>Grants, the energy price cap and the rules for UK homes change often. Get a short email when something changes that affects your home.</p></div>'
        '<form name="newsletter" method="POST" action="/newsletter-thanks/" data-netlify="true" netlify-honeypot="bot-field" class="fn-form">'
        '<input type="hidden" name="form-name" value="newsletter">'
        '<input type="hidden" name="source" value="%s">'
        '<input type="hidden" name="consent_version" value="%s">'
        '<input type="hidden" name="consent_text" value="%s">'
        '<p class="qf-hp" hidden><label>Do not fill this in: <input name="bot-field"></label></p>'
        '<label for="fn-email">Email address</label>'
        '<div class="fn-row"><input type="email" id="fn-email" name="email" required autocomplete="email" placeholder="you@example.com">'
        '<button type="submit">Keep me updated</button></div>'
        '<p class="fn-small">Unsubscribe any time. We use your email only for these updates and never share it. <a href="/privacy/#email-updates">Privacy policy</a></p>'
        '</form></section>' % (esc(source), NEWS_VERSION, esc(NEWS_TEXT)))
    return ('<!-- site-footer -->\n<footer class="footer">%s%s<div class="attribution">%s</div></footer>\n<!-- /site-footer -->'
            % (news, FOOTER_COLS, attribution))


CSS_MARK = '/* ===== FOOTER NEWSLETTER (site_components.py) ===== */'
CSS = CSS_MARK + '''
.footer-news{max-width:1080px;margin:0 auto 40px;padding:24px 28px;background:var(--color-bg,#fafaf7);border:1px solid var(--color-border);border-radius:var(--radius-lg);display:grid;grid-template-columns:1.1fr 1fr;gap:18px 36px;align-items:center}
.footer-news h2{font-family:var(--font-display);font-size:1.2rem;font-weight:700;margin:0 0 6px;color:var(--color-text)}
.footer-news .fn-copy p{font-size:.9rem;color:var(--color-text-secondary);line-height:1.55;margin:0}
.fn-form label{display:block;font-weight:600;font-size:.85rem;margin-bottom:6px;color:var(--color-text)}
.fn-row{display:flex;gap:8px}
.fn-row input{flex:1;min-width:0;padding:10px 12px;border:1px solid var(--color-border);border-radius:var(--radius-sm);font-size:.95rem;font-family:inherit;background:#fff;color:var(--color-text)}
.fn-row input:focus{outline:2px solid var(--color-accent);outline-offset:1px;border-color:var(--color-accent)}
.fn-row button{padding:10px 18px;background:var(--color-accent);color:#fff;border:0;border-radius:var(--radius-sm);font-size:.9rem;font-weight:600;font-family:inherit;cursor:pointer;white-space:nowrap}
.fn-row button:hover{opacity:.92}
.fn-small{font-size:.76rem;color:var(--color-text-tertiary);margin:8px 0 0;line-height:1.5}
.fn-small a{color:inherit}
@media (max-width:720px){.footer-news{grid-template-columns:1fr;padding:20px}.fn-row{flex-direction:column}.fn-row button{width:100%}}
'''

LEAD_RE = re.compile(r'<!-- lead-form:[a-z-]+ -->.*?<!-- /lead-form -->', re.S)
OLD_LEAD_RE = re.compile(r'<section class="quote-form" id="quote">.*?</form>\s*</section>', re.S)
FOOTER_RE = re.compile(r'(?:<!-- site-footer -->\s*)?<footer class="footer">.*?</footer>(?:\s*<!-- /site-footer -->)?', re.S)
ATTR_RE = re.compile(r'<div class="attribution">(.*?)</div>\s*</footer>', re.S)


def page_key(f):
    rel = f.relative_to(ROOT).as_posix()
    return rel[:-len('/index.html')] if rel.endswith('/index.html') else ('' if rel == 'index.html' else rel)


def insert_point(t):
    """Before the FAQ heading, else before the data sources heading, else end of main."""
    for label in ('Frequently asked questions', 'Data sources'):
        m = re.search(r'<h2[^>]*>\s*%s\s*</h2>' % label, t)
        if m:
            return m.start()
    return t.index('</main>')


def process(f):
    t0 = t = f.read_text()
    key = page_key(f)
    source = '/' + key + ('/' if key and not key.endswith('.html') else '')
    if key == '':
        source = '/'
    notes = []

    # Footer on every page, keeping the page's own data attribution.
    m = FOOTER_RE.search(t)
    if m:
        a = ATTR_RE.search(m.group(0))
        t = t[:m.start()] + footer(source, a.group(1).strip() if a else DEFAULT_ATTRIBUTION) + t[m.end():]
        notes.append('footer')

    kind = PAGE_KIND.get(key)
    if kind:
        block = lead_form(kind, source)
        if LEAD_RE.search(t):
            t = LEAD_RE.sub(lambda _: block, t, count=1); notes.append('form refreshed')
        elif OLD_LEAD_RE.search(t):
            t = OLD_LEAD_RE.sub(lambda _: block, t, count=1); notes.append('form upgraded')
        elif key in BANDED:
            i = t.index('</main>') + len('</main>')
            t = t[:i] + '\n<section class="quote-band" id="quoteBand" hidden>' + block + '</section>' + t[i:]
            notes.append('banded form added')
        else:
            i = insert_point(t)
            t = t[:i] + block + '\n' + t[i:]
            notes.append('form added')
    return t0, t, notes


THANKS = {
    '': ('heat-pump', 'heat pump', 'https://mcscertified.com/find-an-installer/', 'Find MCS-certified installers yourself',
         ['Will you do a room-by-room heat loss survey before quoting, and can I see it?',
          'What design flow temperature is the system sized for, and which radiators change?',
          'Is the £7,500 Boiler Upgrade Scheme grant deducted on the invoice, and who applies for it?',
          'What seasonal efficiency do you expect, and will you show me a running cost estimate?',
          'Who services it, what does that cost, and what does the warranty cover?'],
         [('/guides/heat-pump-cost-by-house-type/', 'Compare costs by house type'), ('/guides/boiler-upgrade-scheme-guide/', 'Read the grant guide')]),
    'solar': ('solar', 'solar panel', 'https://mcscertified.com/find-an-installer/', 'Find MCS-certified installers yourself',
              ['What will the system generate a year on my roof, and how did you work it out?',
               'Which panels and inverter are you quoting, and what warranties come with each?',
               'Is scaffolding included, and are there any extra costs for my roof?',
               'Will you register the system with MCS so I can claim Smart Export Guarantee payments?',
               'Would a battery pay for itself on my usage, and what would it add to the price?'],
              [('/solar-calculator/', 'Check the payback on your roof'), ('/guides/solar-panel-payback-uk/', 'Read the payback guide')]),
    'insulation': ('insulation', 'insulation', 'https://www.trustmark.org.uk/find-a-tradesperson', 'Find TrustMark-registered installers yourself',
                   ['Will you survey the property before quoting, including for damp and ventilation?',
                    'Which material and thickness are you quoting, and why that one for my home?',
                    'Is the work covered by a guarantee, and who provides it?',
                    'Could any of the cost be covered by a grant, and will you help apply?',
                    'How long will the work take, and what do I need to do beforehand?'],
                   [('/insulation-calculator/', 'Check what insulation saves you'), ('/guides/is-cavity-wall-insulation-worth-it/', 'Read the cavity wall guide')]),
    'epc': ('epc', 'EPC assessment', 'https://www.gov.uk/get-new-energy-certificate', 'Find an accredited assessor yourself',
            ['What is the total price, including lodging the certificate on the register?',
             'How long will the visit take, and what will you need to see?',
             'Can you tell me which recommendations would lift my rating the most?',
             'When will the certificate be lodged after the visit?',
             'Are you accredited, and which accreditation scheme are you with?'],
            [('/epc-calculator/', 'Plan your EPC improvements'), ('/guides/epc-cost/', 'Read what an EPC costs')]),
    'home': ('home', 'home upgrade', 'https://mcscertified.com/find-an-installer/', 'Find MCS-certified installers yourself',
             ['Will you survey the property before giving a fixed price?',
              'Which products are you quoting, and what warranties come with them?',
              'Which grants could reduce the cost, and will you handle the application?',
              'How long will the work take, and what disruption should I expect?',
              'Can you show me a running cost estimate for my home after the work?'],
             [('/grants/', 'Check which grants you qualify for'), ('/epc-calculator/', 'See which upgrades come first')]),
}


def thanks_page(template, slug, spec):
    kind, noun, finder, finder_label, questions, links = spec
    k = KINDS[kind]
    who = sub_who(k)
    t = re.sub(r'<title>[^<]*</title>', '<title>Request received | Retrofit Planner</title>', template)
    t = re.sub(r'gtag\("event","generate_lead",\{form:"[^"]*"\}\)', 'gtag("event","generate_lead",{form:"%s"})' % k['form'], t)
    qs = ''.join('<li>%s</li>' % q for q in questions)
    ls = ' or '.join('<a href="%s">%s</a>' % (h, l.lower() if i else l) for i, (h, l) in enumerate(links))
    main = ('<main id="main" class="thanks">\n'
            '<h1>Request received</h1>\n'
            '<p class="thanks-lead">Thank you. We will pass your %s request to up to three %s covering your postcode, usually within two working days, and they will contact you directly with a quote. If we cannot find anyone covering your area, we will email you to say so.</p>\n'
            '<p>You can also look for %s yourself.</p>\n'
            '<a class="thanks-cta" href="%s" target="_blank" rel="noopener">%s</a>\n'
            '<div class="thanks-questions"><h2>Five questions worth asking every installer</h2><ol>%s</ol></div>\n'
            '<p class="thanks-next">While you wait: %s.</p>\n'
            '<p class="thanks-small">Changed your mind? Email <a href="mailto:%s">%s</a> and we will not pass your details on, or will ask anyone we have passed them to to delete them.</p>\n'
            '</main>') % (noun, who, who, finder, finder_label, qs, ls, CONTACT, CONTACT)
    t = re.sub(r'<main id="main".*?</main>', lambda _: main, t, count=1, flags=re.S)
    return t


def newsletter_thanks(template):
    t = re.sub(r'<title>[^<]*</title>', '<title>You are signed up | Retrofit Planner</title>', template)
    t = re.sub(r'gtag\("event","generate_lead",\{form:"[^"]*"\}\)', 'gtag("event","sign_up",{method:"newsletter"})', t)
    main = ('<main id="main" class="thanks">\n<h1>You are signed up</h1>\n'
            '<p class="thanks-lead">Thank you. We will email you when something changes that affects UK homes: the energy price cap, grant rules and deadlines, and the standards homes are held to. Every email has an unsubscribe link.</p>\n'
            '<p class="thanks-next">In the meantime, <a href="/grants/">check which grants you qualify for</a> or <a href="/epc-calculator/">see which upgrades come first for your home</a>.</p>\n'
            '</main>')
    return re.sub(r'<main id="main".*?</main>', lambda _: main, t, count=1, flags=re.S)


THANKS_CSS_MARK = '/* ===== THANK YOU PAGES (site_components.py) ===== */'
THANKS_CSS = THANKS_CSS_MARK + '''
.thanks{max-width:640px;margin:0 auto;padding:72px 24px 56px}
.thanks h1{font-family:var(--font-display);font-size:2rem;font-weight:700;margin:0 0 16px}
.thanks p{color:var(--color-text-secondary);line-height:1.65;margin:0 0 16px}
.thanks .thanks-lead{font-size:1.08rem;color:var(--color-text)}
.thanks-cta{display:inline-block;padding:12px 22px;background:var(--color-accent);color:#fff;border-radius:var(--radius-sm);text-decoration:none;font-weight:600;margin:4px 0 8px}
.thanks-questions{margin:32px 0 8px}
.thanks-questions h2{font-family:var(--font-display);font-size:1.3rem;margin:0 0 10px}
.thanks-questions ol{color:var(--color-text-secondary);line-height:1.7;padding-left:22px;margin:0}
.thanks .thanks-small{font-size:.85rem}
'''


def main():
    changed = []
    css_path = ROOT / 'css' / 'style.css'
    css = css_path.read_text()
    for mark, block in ((CSS_MARK, CSS), (THANKS_CSS_MARK, THANKS_CSS)):
        if mark in css:
            css = re.sub(re.escape(mark) + r'.*?(?=\n/\* =====|\Z)', lambda _: block.rstrip('\n'), css, flags=re.S)
        else:
            css = css.rstrip('\n') + '\n\n' + block
    if APPLY:
        css_path.write_text(css)

    # Thank-you pages first, so the footer pass below stamps them too.
    template = (ROOT / 'quote-thanks' / 'index.html').read_text()
    for slug, spec in THANKS.items():
        out = ROOT / 'quote-thanks' / slug / 'index.html' if slug else ROOT / 'quote-thanks' / 'index.html'
        if APPLY:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(thanks_page(template, slug, spec))
        changed.append(str(out.relative_to(ROOT)) + ' (thanks page)')
    nt = ROOT / 'newsletter-thanks' / 'index.html'
    if APPLY:
        nt.parent.mkdir(exist_ok=True)
        nt.write_text(newsletter_thanks(template))
    changed.append('newsletter-thanks/index.html (thanks page)')

    seen = set()
    for f in sorted(ROOT.rglob('*.html')):
        parts = f.relative_to(ROOT).parts
        # The embed widgets are framed on other sites and carry no footer; the /embed/ page itself does.
        if parts[0] in ('docs', 'node_modules') or (parts[0] == 'embed' and len(parts) > 2):
            continue
        t0, t, notes = process(f)
        seen.add(page_key(f))
        if t != t0:
            changed.append('%s: %s' % (f.relative_to(ROOT), ', '.join(notes)))
            if APPLY:
                f.write_text(t)
    missing = sorted(k for k in PAGE_KIND if k not in seen)
    for c in changed:
        print(c)
    print('pages changed:', len(changed))
    if missing:
        print('MAPPED BUT NOT FOUND:', missing)
    print('APPLIED' if APPLY else 'dry run, pass --apply to write')


if __name__ == '__main__':
    main()
