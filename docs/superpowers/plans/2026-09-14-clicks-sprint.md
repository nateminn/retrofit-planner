# Clicks and impressions sprint, 14 September 2026

Approved scope (Nathan, 14 Sep): all five items below, run unattended, deployed in stages as each part passes the checks.

Baseline (Search Console, 12 months to 14 Sep): 1.15K clicks, 137K impressions, 0.8% CTR, position 11.8. Three pages carry about 81% of clicks. Positions 1 to 6 convert at 1.7% against a normal 8 to 15%.

## Order of work

1. **Title and description sweep** (all guides and calculators). Answer-first, the figure in the title on cost pages, title 60 chars or fewer, description 155 or fewer. Do not touch pages already at position 3 or better for their main query unless the title is generic. Expected effect: clicks, within 2 to 4 weeks.
2. **Internal linking sweep.** Every guide with fewer than 4 editorial inbound links gets links from its topic siblings and, where relevant, from the three traffic pages (EPC calculator, 4-bed guide, cost-by-house-type guide). Expected effect: crawl and impressions on the 21 zero-impression pages.
3. **Five property-type guides** in the 3-bed semi pattern (3,000 words, models table, running costs, BUS section, 6 FAQs, charts, photo): 2-bed terrace, bungalow, flat (heat pump cost for a flat, distinct from the existing "can you get a heat pump in a flat" guide), 1930s semi, Victorian terrace. One builder agent and one fact-checker per guide, then a manual batch review. Expected effect: impressions, 2 to 3 months.
4. **Tariffs guide rewrite** with September 2026 tariffs from a researched source list. Targets about 1,100 impressions at positions 18 to 25.
5. **Solar calculator reframed as a cost calculator.** Title, hero and a cost table by system size above the estimate. Targets up to 2,000 impressions at positions 33 to 50.

## Rules that apply to every change

- Site rules in CONTEXT.md: no em dashes, no emojis, no ampersands in copy, www canonical with trailing slash, shared stylesheet, Fraunces plus Plus Jakarta Sans.
- Prices at the Ofgem cap for 1 October to 31 December 2026: electricity 26.32p/kWh, gas 7.97p/kWh, standing charges 54.83p and 29.68p per day. Heat pump tariff assumption 18p. BUS grant 7,500 pounds (9,000 for oil and LPG homes) to 2030.
- Every new guide: 15 or more internal links, FAQPage schema with 4 to 6 questions, Article schema with datePublished, hub entry, sitemap entry, hero photo with licence credit.
- Gates: docs/superpowers/tools/gates.py --stage d, photos_check.py, plus a Playwright render sweep at 375 and 1100 wide. Push only after all pass.

## Deployment

Branch clicks-sprint-2026-09-14, fast-forward merged to main after each stage. Push with the gh credential helper recipe in the project memory. Verify live before starting the next stage.
