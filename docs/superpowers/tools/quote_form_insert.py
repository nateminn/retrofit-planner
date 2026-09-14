#!/usr/bin/env python3
"""Insert the heat pump quote form on the pages listed in PAGES. Idempotent."""
import re, sys, os
TICK = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>'
def form(source):
    return ('<section class="quote-form" id="quote">\n'
    '<h2>Get heat pump quotes for your home</h2>\n'
    '<p class="qf-sub">Tell us about your property and we will email you a shortlist of MCS-certified installers covering your postcode, with the questions worth asking each one. Free, no obligation, no sales calls unless you ask for them.</p>\n'
    '<ul class="qf-points"><li>%s MCS-certified installers only</li><li>%s Grant of £7,500 handled by the installer</li><li>%s Reply within two working days</li></ul>\n'
    '<form name="heat-pump-quote" method="POST" action="/quote-thanks/" data-netlify="true" netlify-honeypot="bot-field">\n'
    '<input type="hidden" name="form-name" value="heat-pump-quote">\n'
    '<input type="hidden" name="source" value="%s">\n'
    '<p style="display:none"><label>Do not fill this in: <input name="bot-field"></label></p>\n'
    '<div class="qf-grid">\n'
    '<div class="form-group"><label for="qf-postcode">Postcode</label><input type="text" id="qf-postcode" name="postcode" required autocomplete="postal-code" placeholder="e.g. SW1A 1AA" pattern="^[A-Za-z]{1,2}[0-9][A-Za-z0-9]? ?[0-9][A-Za-z]{2}$" title="A UK postcode, for example SW1A 1AA"></div>\n'
    '<div class="form-group"><label for="qf-property">Property type</label><select id="qf-property" name="property" required><option value="">Select</option><option>Flat</option><option>Terraced house</option><option>Semi-detached house</option><option>Detached house</option><option>Bungalow</option></select></div>\n'
    '<div class="form-group"><label for="qf-heating">Current heating</label><select id="qf-heating" name="heating" required><option value="">Select</option><option>Gas boiler</option><option>Oil boiler</option><option>LPG boiler</option><option>Electric or storage heaters</option><option>Other or none</option></select></div>\n'
    '<div class="form-group"><label for="qf-when">When are you looking to install?</label><select id="qf-when" name="timing" required><option value="">Select</option><option>Within 3 months</option><option>3 to 6 months</option><option>6 to 12 months</option><option>Just researching</option></select></div>\n'
    '<div class="form-group"><label for="qf-name">Name</label><input type="text" id="qf-name" name="name" required autocomplete="name"></div>\n'
    '<div class="form-group"><label for="qf-email">Email</label><input type="email" id="qf-email" name="email" required autocomplete="email"></div>\n'
    '<div class="form-group"><label for="qf-phone">Phone (optional)</label><input type="tel" id="qf-phone" name="phone" autocomplete="tel"></div>\n'
    '</div>\n'
    '<label class="qf-consent"><input type="checkbox" name="share_ok" value="yes"> You may pass my details to up to three MCS-certified installers so they can contact me directly with a quote.</label>\n'
    '<button type="submit" class="btn-calculate">Send my request</button>\n'
    '<p class="qf-small">We use your details only to answer this request, and share them with installers only if you tick the box. If an installer we introduce wins your job they may pay us an introduction fee; that never changes the price you pay. See our <a href="/privacy/">privacy policy</a>.</p>\n'
    '</form>\n</section>\n') % (TICK, TICK, TICK, source)

PAGES = {
 'guides/heat-pump-cost-4-bed-house/index.html': 'after-breakdown',
 'guides/heat-pump-cost-3-bed-semi/index.html': 'after-breakdown',
 'guides/heat-pump-cost-2-bed-terrace/index.html': 'after-breakdown',
 'guides/heat-pump-cost-3-bed-detached/index.html': 'after-breakdown',
 'guides/heat-pump-cost-5-bed-house/index.html': 'after-breakdown',
 'guides/heat-pump-cost-bungalow/index.html': 'after-breakdown',
 'guides/heat-pump-victorian-terrace/index.html': 'after-breakdown',
 'guides/heat-pump-cost-by-house-type/index.html': 'before-second-h2',
 'heat-pump-calculator/index.html': 'after-main',
 'boiler-vs-heat-pump/index.html': 'after-main',
}
dry = '--dry' in sys.argv; n = 0
for path, where in PAGES.items():
    s = open(path, encoding='utf-8').read()
    if 'name="heat-pump-quote"' in s: print('skip (present)', path); continue
    src = '/' + path.replace('index.html', '')
    if where == 'after-breakdown':
        i = s.index('<h2 id="breakdown"'); j = s.index('<h2', i + 5)
        s = s[:j] + form(src) + s[j:]
    elif where == 'before-second-h2':
        h1 = s.index('<h1'); first = s.index('<h2', h1); second = s.index('<h2', first + 5)
        s = s[:second] + form(src) + s[second:]
    else:
        i = s.index('</main>') + len('</main>')
        s = s[:i] + '\n<section class="quote-band">' + form(src).rstrip('\n') + '</section>\n' + s[i:]
    assert '—' not in s
    if not dry: open(path, 'w', encoding='utf-8').write(s)
    n += 1; print('inserted', path, where)
print('pages with the form:', n, '(dry run)' if dry else '')
