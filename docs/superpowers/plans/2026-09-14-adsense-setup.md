# AdSense setup for retrofitplanner.co.uk

Prerequisites shipped 14 September 2026: honest privacy policy (analytics, newsletter, advertising cookies, consent, rights), a comment-only ads.txt at the domain root, methodology wording aligned.

## When the publisher ID (pub-XXXXXXXXXXXXXXXX) arrives

1. **ads.txt**: replace the commented line with `google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0` and commit. Check https://www.retrofitplanner.co.uk/ads.txt returns it as text/plain.
2. **Consent banner**: in AdSense open Privacy and messaging, create a GDPR message for the UK and EEA (standard consent, not consent or pay), choose the site, and publish. It is delivered through the AdSense script, so nothing else is needed on the site. Add a footer link "Cookie settings" on every page that calls `googlefc.callbackQueue.push({CONSENT_DATA_READY: () => googlefc.showRevocationMessage()})` so visitors can reopen the banner, which the privacy policy promises.
3. **Head snippet on every page**, placed before the existing Google tag so Consent Mode defaults apply first:
   ```html
   <script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}
   gtag('consent','default',{ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied',analytics_storage:'denied',wait_for_update:500});</script>
   <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX" crossorigin="anonymous"></script>
   ```
   Expect GA4 reported users to fall once consent defaults to denied; Google fills part of the gap with modelled data. This is the price of a compliant banner.
4. **Two ad units only**: an in-article display unit inserted after the first h2 section on every guide, and a 300 by 250 unit in the calculator sidebar below the results card. Wrap each in a container with a fixed min-height (280px in-article, 250px sidebar) so the page does not jump, and load them lazily below the first screen.
5. **Verify**: pages still pass gates.py and the Playwright render sweep at 375 and 1100 wide, Cumulative Layout Shift stays under 0.1 in PageSpeed Insights, and the AdSense site status shows ads.txt authorised.

## Decision recorded
Journey by Mediavine pays two to three times AdSense per view and the site already clears its 1,000 sessions in 30 days threshold (GA4 snapshot 14 September 2026: about 1,200 to 1,400 sessions a month). Apply to Journey first; use AdSense only if Journey declines. Either way, the quote form on the heat pump cost pages is the larger earner.
