# RetrofitPlanner "Fix and Freshen" September 2026 update: design

Date: 2026-09-06
Status: approved in conversation, awaiting written-spec review
Repo: ~/Desktop/Projects/retrofit-planner (main tracks origin, Netlify auto-deploys main)
Branch for this work: fix-and-freshen-2026-09 (merge to main and push at the end)

## 1. Background and goals

Google Search Console, 4 June to 3 September 2026 (web search only):

| Metric | Early June week | Late August week |
|---|---|---|
| Clicks | 25 | 89 |
| Impressions | 3,085 | 11,267 |
| Average position | 16.2 | 12.3 |

Three pages carry about 81% of clicks: /epc-calculator/ (281), /guides/heat-pump-cost-4-bed-house/ (238, position 3.4, only 854 words) and /guides/heat-pump-cost-by-house-type/ (171). 21 of the 48 sitemap URLs had zero impressions.

Nothing has been committed since 17 March 2026. Every page still cites Ofgem Q1 2026 prices and says "Updated March 2026".

Goals of this round:

1. Fix what is broken: 5 dead footer links on 11 pages, 2 legacy 404 URLs, 53 em dashes against site rule 1, wrong Boiler Upgrade Scheme facts, a stray empty directory.
2. Make prices and dates current across the site using the Ofgem cap for 1 October to 31 December 2026.
3. Expand the thin top-ranking 4-bed guide to 2,000 to 2,400 words.

Non-goals (flagged for a later round): rewrite of the tariffs guide, a running-costs-by-EPC-band page, repositioning the solar calculator around "cost calculator" queries, installer lead generation, removing the personal access token from the git remote URL, hyphenated ranges in EPC calculator copy, sitemap lastmod.

## 2. Ground truth (verified 5 and 6 September 2026)

### 2.1 Energy prices

| Input | Old (site) | New | Source |
|---|---|---|---|
| Electricity unit rate | 24.5p/kWh | 26.32p/kWh | Ofgem cap, 1 Oct to 31 Dec 2026, Direct Debit, GB average, no VAT on electricity from 1 Oct 2026 |
| Electricity standing charge | 61.64p/day | 54.83p/day | same |
| Gas unit rate | 6.76p/kWh | 7.97p/kWh | same, includes 5% VAT |
| Gas standing charge | 31.65p/day | 29.68p/day | same |
| Typical dual-fuel annual bill | £1,738 | £1,723 | Ofgem press release 26 Aug 2026, up 4% from £1,663 |
| Heating oil | 6.8p/kWh | 9.0p/kWh | September 2026 kerosene about 93p/litre inc VAT, 10.35 kWh/litre |
| LPG | 9.5p/kWh | 9.5p/kWh | no reliable bulk figure found, keep and label "typical bulk contract" |
| Heat pump tariff effective rate | 16p/kWh | 18p/kWh | Octopus Cosy 13p in 04-07, 13-16, 22-00 windows; about 60% of heat pump use shifted; OVO Heat Pump Plus (15p) closed 1 Feb 2026 |
| Gas boiler efficiency | 90% | 90% | unchanged |
| Air source COP | 2.9 (3.2 flats and well insulated) | unchanged | |
| Ground source COP | 3.7 | unchanged | |
| Economy 7 night rate (storage heater pages) | ~14p | unchanged | not cap-set, not verified, leave |

For reference, the cap in force until 30 September 2026 is 26.11p / 57.19p electricity and 7.33p / 29.04p gas. The site uses the October figures because they stay correct for four months.

Derived headline: heat from gas costs 7.97 / 0.90 = 8.86p per kWh. Heat from an air source heat pump on a standard tariff costs 26.32 / 2.9 = 9.08p per kWh. Near parity. On an 18p heat pump tariff it is 6.21p. Disconnecting a gas supply also saves the gas standing charge, 29.68p x 365 = £108 a year.

### 2.2 Scheme facts

| Item | Site says | Correct |
|---|---|---|
| Boiler Upgrade Scheme end | April 2028 (3 pages, 6 lines) | Runs to 2030 (extended 28 April 2026, Warm Homes Plan) |
| BUS ground source grant | £6,000 (heat-pump-calculator, grants) | £7,500 |
| BUS air-to-air | not mentioned | £2,500, mention only where BUS amounts are listed |
| BUS for oil or LPG homes | not mentioned; grants page implies less | £9,000 from July 2026 |
| BUS 2026-27 budget | not mentioned | £400 million, optional colour |
| ECO4 end | 31 December 2026 | Correct, extended from March 2026, no change |
| GBIS | closed 31 January 2026 | Correct |
| 0% VAT on installs | until March 2027 | Correct |

### 2.3 Heat pump installation prices (MCS data, England and Wales, 2026 Q2, BUS-funded installs, prices actually paid)

Median air source install £12,908. Lower quartile £11,128. Upper quartile £15,627. Median net of £7,500 grant about £5,400.

### 2.4 Models suitable for a 4-bed house (for the guide's model table)

| Model | Outputs for a 4-bed | Refrigerant | Max flow temp | Why pick it |
|---|---|---|---|---|
| Vaillant aroTHERM plus | 10 kW, 12 kW | R290 | 75C | High flow temperature keeps more existing radiators, very quiet mode |
| Mitsubishi Ecodan | 11.2 kW, 14 kW | R32 or R290 by model | 60 to 70C | Largest UK installer base, Zubadan models hold output to -25C |
| Daikin Altherma 3 H HT | 14 kW, 16 kW, 18 kW | R32 | 70C | Widest cold-weather range, long track record |
| Samsung EHS Mono HT Quiet | 12 kW, 14 kW | R32 | 70C | Value option, high temperature |

## 3. Work items

### 3.1 Dead links, footer, redirects, 404 page, stray directory

Canonical footer Guides column, byte-identical on all 48 pages (replaces the whole `<div class="footer-col"><h4>Guides</h4>...</div>` block):

```html
<div class="footer-col"><h4>Guides</h4><a href="/guides/heat-pump-cost-4-bed-house/">Heat Pump Cost: 4-Bed House</a><a href="/guides/heat-pump-cost-by-house-type/">Costs by House Type</a><a href="/guides/heat-pump-running-costs/">Heat Pump Running Costs</a><a href="/guides/best-heat-pump-tariffs/">Best Heat Pump Tariffs</a><a href="/guides/boiler-upgrade-scheme-guide/">BUS Grant Guide</a><a href="/guides/how-epc-points-are-calculated/">How EPC Points Are Calculated</a></div>
```

The 11 pages currently linking to the 5 unbuilt guides: index.html, about, boiler-vs-heat-pump, contact, epc-calculator, grants, insulation-calculator, methodology, privacy, solar-calculator, terms. heat-pump-calculator has a third variant, guides a fourth. All become the canonical block.

New file `_redirects` at repo root (Netlify reads it from the publish root):

```
/guides/heat-pump-guide/         /guides/heat-pump-cost-by-house-type/    301
/guides/insulation-guide/        /guides/is-loft-insulation-worth-it/     301
/guides/epc-explained/           /guides/how-epc-points-are-calculated/   301
/guides/boiler-upgrade-scheme/   /guides/boiler-upgrade-scheme-guide/     301
/guides/average-energy-bills/    /guides/average-energy-bills-uk/         301
/epc-calculator/epc-calculator/  /epc-calculator/                         301
/guides/heat-pump-running-costs-uk-electricity-vs-gas-compared  /guides/heat-pump-running-costs/  301
/CONTEXT.md                      /404.html                                404!
/docs/*                          /404.html                                404!
```

The last two rules stop Netlify serving the planning brief and this spec, which are committed to the repo and therefore public today (CONTEXT.md returns 200 live).

New file `404.html` at repo root: minimal branded page using the shared nav, CSS, favicon block, `<meta name="robots" content="noindex">`, a one-line message, and links to the six calculators and the guides hub. Netlify uses a root 404.html automatically.

Remove the empty untracked directory `guides/{heat-pump-noise,is-loft-insulation-worth-it,heat-pump-vs-new-boiler,eco4-scheme-explained,best-heat-pump-tariffs,solar-panel-payback-uk}`.

### 3.2 Scheme facts (4 files)

- heat-pump-calculator/index.html line 204: "£6,000 for ground source. Available until March 2028." becomes "£7,500 for air source or ground source, £9,000 if you are replacing an oil or LPG boiler. The scheme runs to 2030."
- guides/heat-pump-old-house/index.html line 248: "The scheme runs until April 2028." becomes "The scheme runs to 2030."
- guides/boiler-upgrade-scheme-guide/index.html: FAQ schema answer (line 57), body lines 197 and 244: April 2028 becomes 2030 with the 28 April 2026 extension mentioned once; add one sentence in the grant-amount section on the £9,000 oil and LPG rate from July 2026 and £2,500 air-to-air.
- grants/index.html: "£7,500 towards an air source heat pump or £6,000 towards a ground source heat pump" becomes "£7,500 towards an air source or ground source heat pump, rising to £9,000 if you are replacing an oil or LPG boiler"; delete or invert "no existing oil or LPG boiler (for the full grant)"; FAQ schema answer updated to match; results-panel text for BUS updated to match.

The grants page eligibility JavaScript is not changed except any displayed amount strings.

### 3.3 Em dashes (9 files, 53 instances)

about (16), epc-calculator (15), insulation-calculator (4), grants (4), contact (4), solar-calculator (3), methodology (3), boiler-vs-heat-pump (3), privacy (1). Each instance is rewritten by hand with a comma, full stop, colon, or a rephrase. No automated replacement. Gate: zero U+2014 in any .html file.

### 3.4 Rate refresh: calculators (4 files with constants)

| File | Old | New |
|---|---|---|
| heat-pump-calculator line 302 | `energyPrices: { electricity: 0.245, gas: 0.0676, oil: 0.068, lpg: 0.095 }` | `energyPrices: { electricity: 0.2632, gas: 0.0797, oil: 0.090, lpg: 0.095 }` |
| heat-pump-calculator line 238 prose | 24.5p vs 6.76p, 8.2p vs 7.5p per kWh of heat | 26.32p vs 7.97p; at COP 3.0 8.8p vs 8.9p for gas at 90%: "now roughly level" |
| boiler-vs-heat-pump line 230 | `gasRate: 0.0676, elecRate: 0.245` | `gasRate: 0.0797, elecRate: 0.2632` |
| boiler-vs-heat-pump line 166 prose | 7.35p gas, 7p to 9.8p heat pump | 8.9p gas at 92%, 7.5p to 10.5p heat pump at COP 2.5 to 3.5 |
| insulation-calculator line 387 | `fuelPrices: { gas: 0.0676, oil: 0.068, lpg: 0.095, electricity: 0.245 }` | `fuelPrices: { gas: 0.0797, oil: 0.090, lpg: 0.095, electricity: 0.2632 }` |
| solar-calculator line 273 | `electricityRate: 0.245, // Ofgem Q1 2026` | `electricityRate: 0.2632, // Ofgem Oct to Dec 2026` |

Any standing charge constants found by grepping 0.6164, 0.3165, 61.64, 31.65 become 0.5483 and 0.2968. epc-calculator and grants have no rate constants.

If a calculator page also has a heat pump tariff constant (grep 0.16, 16p), it becomes 0.18 and the label "well-scheduled heat pump tariff such as Octopus Cosy".

### 3.5 Rate refresh: recompute guides (site-formula pages)

Pages whose tables are produced by the site's own stated model. Expected list, implementation may move a page between 3.5 and 3.6 after reading it:

average-energy-bills-uk, energy-bills-by-household-size, heat-pump-running-costs, heat-pump-vs-new-boiler, electric-boiler-vs-heat-pump, storage-heaters-vs-heat-pump, heat-pump-cost-by-house-type, heat-pump-cost-4-bed-house (rewritten, section 3.8), heat-pump-old-house, boiler-upgrade-scheme-guide, heat-pump-flat, are-solar-panels-worth-it-uk, solar-panel-payback-uk, solar-battery-storage-uk, best-heat-pump-tariffs (standard-variable baseline rows only).

Model, confirmed to reproduce the current tables exactly:

- Gas boiler annual cost = heat demand / 0.90 x gas rate
- Oil boiler = heat demand / stated efficiency (0.85 default) x oil rate
- Heat pump standard = heat demand / COP x electricity rate
- Heat pump tariff = heat demand / COP x 0.18
- Electric boiler or direct electric = heat demand x electricity rate
- Bills = consumption kWh x unit rate + 365 x standing charge
- Solar = generation x self-use share x electricity rate + generation x export share x 8p, degradation 0.5% a year, existing payback and 25-year logic unchanged

Procedure (Python script, kept in the repo under docs/superpowers/tools/, not deployed because /docs/* is 404-ed):

1. Parse each target table and the assumption note under it.
2. Read the inputs from the page where stated (heat demand, consumption, COP, efficiency). Where a table states only outputs (household-size bills), back-solve the input from the old figure and old rates.
3. Guard: recompute at the OLD rates and compare with the figure on the page. Any cell more than £2 off is listed for a hand check and left untouched by the script.
4. Write the new figures at the NEW rates, rounded the same way the page rounds (nearest pound, or nearest £10 where the page uses round numbers).
5. Update every sentence in the same page that quotes a recomputed figure (the script reports old figures that still appear in prose after the table pass; those are fixed by hand).
6. Replace the assumption note with the new rates and the 18p tariff assumption.

Prose consequences to rewrite by hand on these pages: any sentence saying a heat pump on a standard tariff costs "more" or "slightly more" than gas is re-expressed as "about the same" with the two per-kWh-of-heat figures; oil comparisons now favour heat pumps by a wide margin.

The tariffs guide additionally gets "OVO Heat Pump Plus" marked "closed to new customers since February 2026" in its table and text. No other tariff rows are touched.

### 3.6 Rate refresh: annotate guides (EST or supplier-sourced figures)

Expected list: diy-loft-insulation, draught-proofing-guide, eco4-scheme-explained, epc-rating-landlords, free-loft-insulation-uk, great-british-insulation-scheme, home-upgrade-grant, how-epc-points-are-calculated, how-long-loft-insulation-lasts, is-cavity-wall-insulation-worth-it, is-loft-insulation-worth-it, solid-wall-insulation-cost, underfloor-insulation-cost, warm-home-discount.

Figures stay. Each note or sentence that currently says "at Ofgem Q1 2026 rates" (with or without the 6.76p or 24.5p figure) becomes one of:

- Gas-based savings: "Savings were calculated at the January to March 2026 gas price of 6.76p per kWh. From 1 October 2026 the Ofgem cap puts gas at 7.97p per kWh, so expect savings around 18% higher than shown."
- Electricity-based figures: "Figures use the January to March 2026 electricity price of 24.5p per kWh. The Ofgem cap from 1 October 2026 is 26.32p per kWh, so electricity-based savings are around 7% higher than shown."

The "Data sources" line "Energy prices from Ofgem Q1 2026 price cap" becomes "Energy prices from the Ofgem price cap" with the same link.

### 3.7 Labels and dates

Touched pages (everything in 3.2, 3.4, 3.5, 3.6, plus index.html, about, methodology, guides/index.html):

- "Ofgem Q1 2026 price cap" and "Ofgem Q1 2026" in labels become "Ofgem price cap, October to December 2026" (sentence-cased to fit). No "Q1 2026" string remains anywhere except inside the annotation sentences of 3.6, which spell it out as "January to March 2026" instead, so the gate is literally zero "Q1 2026".
- "Updated March 2026" in any of its four variants becomes "Updated September 2026" (same variant shape).
- Article schema `dateModified` becomes "2026-09-06". `datePublished` unchanged.
- index.html: "Currently using Q1 2026 rates." becomes "Currently using Ofgem rates for October to December 2026."
- guides/index.html: the "Ofgem Q1 2026 data" label becomes "Ofgem October to December 2026 data".
- methodology: rates paragraph lists the four October figures and the oil, LPG and 18p assumptions; "We update our calculators within one week of each new price cap taking effect (January, April, July, October)" becomes "We update our calculators when Ofgem announces each new cap (usually late February, May, August and November)".

Untouched pages keep their March 2026 dates: condensation-mould-guide, heat-pump-noise, how-to-improve-epc-rating, planning-permission-heat-pump, radiator-sizing-heat-pump, warm-homes-plan-2026, privacy, terms. (epc-calculator and contact receive only the footer and em-dash edits and also keep their dates.) Grants receives scheme-fact changes and is bumped.

### 3.8 The 4-bed guide rewrite (guides/heat-pump-cost-4-bed-house/index.html)

Keep: URL, title tag, H1, breadcrumb, Article schema (dateModified bumped), the Amazon paragraph, the four related-link cards, the insulate-first callout, nav and footer.

Meta description: "A heat pump for a 4-bed house costs £11,000 to £16,000 installed, £3,500 to £8,500 after the £7,500 grant. Real 2026 prices, sizing, models and running costs."

Structure (add `.toc` inline CSS from CONTEXT.md; each H2 gets an id):

1. Lead paragraph: answer first with `key-number` £11,000 to £16,000; MCS median for all air source installs £12,908; net £3,500 to £8,500; £9,000 grant for oil or LPG homes; running cost £1,117 a year on a heat pump tariff, £477 less than gas.
2. Table of contents.
3. What a 4-bed heat pump really costs in 2026: MCS 2026 Q2 table (lower quartile £11,128, median £12,908, upper quartile £15,627, net of grant column) and why 4-beds sit in the upper half (12 to 14 kW units, more radiators, larger cylinder).
4. Complete cost breakdown: existing table, note gains "£9,000 grant if replacing oil or LPG".
5. 4-bed semi versus 4-bed detached: new table. Semi 13,000 to 15,000 kWh, 8 to 10 kW, £10,000 to £13,000, net £2,500 to £5,500. Detached 16,000 to 20,000 kWh, 10 to 14 kW, £11,000 to £16,000, net £3,500 to £8,500.
6. What size heat pump for a 4-bed house: existing insulation table plus three sentences on the MCS heat-loss survey, the 40 to 60 W per m2 rule of thumb, and why oversizing hurts efficiency.
7. Which heat pumps suit a 4-bed house: table from section 2.4 and a paragraph saying installer design quality and a flow temperature of 50C or below matter more than brand.
8. Radiators, cylinder and pipework: 10 to 14 radiators typical, 4 to 7 upsized, 250 to 300 litre cylinder, microbore pipework as the common budget breaker.
9. Running costs, 4-bed detached, October to December 2026 rates, 18,000 kWh demand: gas boiler £1,594; heat pump standard £1,634; heat pump tariff £1,117 (saving £477); oil boiler £1,900 to £2,300; LPG £1,900; electric boiler £4,738. Note lists the assumptions. Second small table for a well-insulated 15,000 kWh home: gas £1,328, heat pump standard £1,361, heat pump tariff £931. Mention the £108 gas standing charge saved on disconnection.
10. The Boiler Upgrade Scheme for a 4-bed: £7,500, £9,000 for oil or LPG, installer applies, MCS required, runs to 2030, 0% VAT until March 2027.
11. Is a heat pump worth it for a 4-bed: extra cost over a new boiler £3,000 to £12,000; payback 6 to 25 years against gas, 4 to 15 against oil; 20-year tariff saving £9,540; link to the boiler-vs-heat-pump comparison.
12. Ground source versus air source: existing table recomputed (ground source £876 a year on a heat pump tariff at COP 3.7, £1,280 standard).
13. Getting quotes: three MCS quotes, heat-loss calculation, design flow temperature, SCOP figure, MCS 020 noise assessment, warranty, link to the MCS installer finder.
14. Related links (existing four cards).
15. FAQs, six, mirrored in FAQPage schema: cost for a 4-bed; size; running cost; which heat pump is best for a 4-bed detached; is it worth it; how long does installation take (2 to 4 days, up to a week with radiator upgrades).
16. Data sources: MCS Data Dashboard, Ofgem cap October to December 2026, GOV.UK BUS, Energy Saving Trust.

Targets: 2,000 to 2,400 words of visible text, at least 15 internal links, 3 to 4 external links, no em dashes, no ampersands in copy, no emoji.

### 3.9 Repo and delivery

1. Branch `fix-and-freshen-2026-09` from main.
2. Commit A: this spec. The recompute tool lands with commit C.
3. Commit B "Fix dead links, footer, redirects, 404 page, BUS facts, em dashes".
4. Commit C "Refresh prices and dates to Ofgem October to December 2026".
5. Commit D "Expand 4-bed heat pump cost guide".
6. Gates pass, calculators tested in the browser, then merge to main (fast-forward) and push. Netlify deploys.
7. Post-deploy checks (section 4.3).

Commit messages end with the Co-Authored-By line.

## 4. Verification

### 4.1 Static gates (script, run before each commit, all must pass)

- Zero U+2014 characters in any .html.
- Zero emoji in any .html.
- Zero occurrences of "24.5p", "6.76p", "61.64p", "31.65p", "Q1 2026", "0.245,", "0.0676".
- Zero occurrences of "2028" in BUS contexts.
- Every `href="/..."` internal link resolves to an existing local index.html or file.
- Every `<script type="application/ld+json">` block parses as JSON.
- The footer Guides block is byte-identical across all 48 pages.
- `_redirects` has 9 rules, `404.html` exists.
- heat-pump-cost-4-bed-house visible word count is at least 2,000 and internal links at least 15.
- No "Updated March 2026" remains on any page touched by 3.2, 3.4, 3.5, 3.6.

### 4.2 Calculator checks (browser pane against `python3 -m http.server` in the repo root)

For each of heat-pump-calculator, boiler-vs-heat-pump, insulation-calculator, solar-calculator: load the page, run one calculation with default inputs, confirm results render, the console has no errors, and one displayed figure matches a hand calculation with the new constants.

### 4.3 Post-deploy checks

- The 7 redirect URLs return 301 to the intended targets; /CONTEXT.md and /docs/superpowers/specs/ return 404.
- /, /epc-calculator/, /guides/heat-pump-cost-4-bed-house/ and /guides/heat-pump-cost-by-house-type/ return 200 and contain "26.32p".
- /guides/heat-pump-cost-4-bed-house/ contains the six FAQ questions.

## 5. Follow-ups after this round

1. Tariffs guide rewrite with September 2026 tariffs (6,374 impressions at position 17.8).
2. Running costs by EPC band page ("epc rating D monthly cost calculator" cluster, about 460 impressions at position 7.5, zero clicks).
3. Solar calculator retitle and copy around "solar panel cost calculator" (9,000 impressions at position 20.7).
4. Move the GitHub token out of the git remote URL into a credential helper.
5. Consider a shared /js/rates.js so the next cap change is a one-file edit for the calculators.
