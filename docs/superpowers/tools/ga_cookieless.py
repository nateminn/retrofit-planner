#!/usr/bin/env python3
"""RETIRED 26 September 2026: analytics now runs from js/analytics.js with cookies, under the
UK statistical purposes exception, and no page carries an inline GA snippet any more.

Run Google Analytics 4 without setting any cookies.

WHY. GA4's default config writes _ga and _ga_<id> on arrival. Those are analytics
cookies, not strictly necessary ones, so PECR reg 6 wants consent before they are set.
This site has no consent banner and does not want one, so the answer is to stop setting
the cookies rather than to ask about them.

HOW, AND WHAT DOES NOT WORK. The obvious candidate, client_storage: 'none' on the
config call, is a Universal Analytics option. GA4 ignores it. Measured on this site:
with client_storage: 'none' set, _ga and _ga_4QMWG6G2WL were still written on a cleared
browser. Do not reach for it again.

What does work is Consent Mode. gtag('consent', 'default', {analytics_storage: 'denied'})
issued BEFORE the js and config calls stops GA4 writing anything. Measured: zero cookies,
zero localStorage, zero sessionStorage, and the /g/collect request still fires with
gcs=G100, so pageviews are still delivered. Order matters: the consent call has to come
first or the config runs under the default granted state and sets the cookies anyway.

WHAT YOU GIVE UP. Without a stored client id GA4 cannot recognise a returning visitor,
so Users and Sessions lose their meaning and engagement metrics with them. Pageviews by
page, and trends over time, are unaffected, which is what this site is measured on.

ad_storage, ad_user_data and ad_personalization are denied too. The site shows no
advertising, so there is no reason for any of it to reach Google's ad products.

Handles both snippet spellings on the site and keeps each page's own whitespace.
Idempotent.
"""
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]

CONSENT_SPACED = (
    "gtag('consent', 'default', { ad_storage: 'denied', ad_user_data: 'denied', "
    "ad_personalization: 'denied', analytics_storage: 'denied' });\n    "
)
CONSENT_TIGHT = (
    "gtag('consent','default',{ad_storage:'denied',ad_user_data:'denied',"
    "ad_personalization:'denied',analytics_storage:'denied'});"
)

PAIRS = [
    ("gtag('js', new Date());", CONSENT_SPACED + "gtag('js', new Date());"),
    ("gtag('js',new Date());",  CONSENT_TIGHT + "gtag('js',new Date());"),
]

def main():
    done, already, untouched = [], [], []
    for f in sorted(ROOT.rglob('*.html')):
        if '.git' in f.parts:
            continue
        html = f.read_text()
        if 'googletagmanager' not in html:
            continue
        rel = f.relative_to(ROOT)
        if "'consent'" in html or '"consent"' in html:
            already.append(rel); continue
        new = html
        for old, repl in PAIRS:
            new = new.replace(old, repl, 1)
        if new == html:
            untouched.append(rel); continue
        f.write_text(new)
        done.append(rel)
    print(f"consent default applied to {len(done)} pages; {len(already)} already had it")
    for r in untouched:
        print(f"  GA TAG PRESENT BUT gtag('js') NOT MATCHED: {r}")
    return 1 if untouched else 0

if __name__ == '__main__':
    sys.exit(main())
