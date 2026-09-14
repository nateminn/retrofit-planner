# Advertising setup for retrofitplanner.co.uk

Shipped 14 September 2026: honest privacy policy (analytics, newsletter, advertising partner, consent, retention, UK GDPR rights), a comment-only ads.txt, methodology wording aligned.

## Decision: Journey by Mediavine first, AdSense only as a fallback

Journey needs 1,000 sessions in 30 days (GA4 shows about 1,200 to 1,400), a site at least four months old (launched March 2026), original content, and the Grow by Mediavine script running on the site for 30 days before evaluation. It pays a 70 percent revenue share, net 65 days, and reported RPMs average about 11 dollars per thousand pageviews, two to three times AdSense. At current traffic expect roughly 10 to 25 pounds a month, rising with pageviews.

## Steps

1. Nathan: create a free Grow account at grow.me, add retrofitplanner.co.uk as a non-WordPress site, and copy the Grow script tag from the dashboard. Share GA4 access with Mediavine when the dashboard asks; that is how they verify sessions.
2. Add the Grow script to every page just before `</head>` (a one-line site-wide edit with docs/superpowers/tools/apply_edits.py). Commit, push, confirm it fires in the Grow dashboard. This starts the 30-day clock.
3. After 30 days, apply to Journey inside the Grow dashboard. When approved, Mediavine supplies its ad script (which includes its consent banner for UK and EEA visitors) and its ads.txt lines. Add the script site-wide, paste the lines into ads.txt, and add a footer link "Cookie settings" that reopens the Mediavine consent dialog.
4. Two placements only: an in-article unit after the first h2 section on guides and a sidebar unit on calculators. Journey controls placement automatically but allows density limits; set the lowest density.
5. Verify: gates.py, the Playwright render sweep at 375 and 1100 wide, and Cumulative Layout Shift under 0.1 in PageSpeed Insights.

## If AdSense instead

Apply at adsense.google.com, then: ads.txt line `google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0`; Google's own consent message under Privacy and messaging; Consent Mode defaults (`gtag('consent','default',{ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied',analytics_storage:'denied',wait_for_update:500})`) before the existing Google tag; the adsbygoogle.js script with the client ID; the same two placements with fixed-height containers. Expect GA4 reported users to fall once consent defaults to denied.

## Larger earner
The quote form on the heat pump cost pages is worth ten to twenty times the ads at today's traffic (about 800 visits a month to those pages, 2 percent enquiry rate, 25 to 60 pounds per accepted lead).
