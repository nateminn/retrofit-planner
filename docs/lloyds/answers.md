# Lloyds Launch 2026 application, Homes challenge

Sub challenge: help customers manage, improve, protect and maximise the value of their homes.

Every figure below was verified in the repository or in a GSC export on 24 September 2026.

---

## Identity fields

- **Registered company name:** `Retrofit Planner` (sole trader, not yet incorporated)
- **Company registration number:** `Not yet registered, incorporating Q4 2026`. If the field rejects text, leave it blank and tell Tom on the same thread. Do not enter digits: there is no number and any digits would be false.
- **Year founded:** `2026`
- **Number of employees:** `1`
- **Which Launch focus area:** Homes
- **How did you hear about Launch:** Approached by Tom Hoskin at GrowthBuilders

---

## What do you do?

RetrofitPlanner.co.uk is a free UK home energy site I build and run on my own. Six calculators and 46 guides answer one question for one house: what does the work cost, what does it save, and what comes first.

Behind them is a heat demand model built from DESNZ National Energy Efficiency Data-Framework 2026 microdata, 39,502 gas heated records in England and Wales. It needs four fields: property type, floor area or bedrooms, fabric condition, heating fuel. No smart meter, no survey, no account. The method is published at /methodology/ and the model table is readable at /js/heat-model.js.

## Why did you develop this proposition? What problem are you solving?

Most retrofit numbers a household can find come from the firm selling the work, with no method stated and no way to check them. The public data to answer it properly already exists, so I built the model instead of guessing.

The site is designed to be funded by referral, with five programmes applied for and none approved. That is why the method is published, the model table is open, and the tools withhold the quote prompt when their own figures say the work does not pay. Those rules were written before any of it earned anything, which is the only time you can write them honestly.

## What are the key features and benefits?

Six free tools: heat pump cost, insulation savings, an EPC planner, solar cost, a 15 year boiler versus heat pump comparison, and a grant checker. 46 guides across 60 pages. A bill checker inside one guide takes four inputs and tells a household how far their bill sits from typical for their house.

Every figure traces to one model. Two automated checks enforce that before anything publishes: one reads 18 guides for the model's demand figure, the other reads 148 cells across 8 property tables and works backwards from the costs. A wrong number fails the same check as a typo.

## What is your Unique Selling Point?

Kamma Climate and Cotality already model retrofit at property level and sell it to LBG's peers. I am not claiming nobody else can do this. The difference is the output and who receives it: they return a risk score to the lender, this returns a payback figure and an ordered sequence of works to the customer, from a method anyone can read.

It also withholds the sale. The boiler tool hides both the quote prompt and the lead form when the old boiler is cheaper: at a £900 gas bill that is 42 of the tool's 120 input combinations. The solar tool tells 282 of 6,048 modelled cases it never pays back.

## Who is your target audience?

UK homeowners facing one decision, usually a boiler replacement forced by a breakdown, loft or wall insulation, or solar. Search traffic skews to people naming their own house: 3 bed semi, Victorian terrace, 1960s house, bungalow. They want a figure for that house, not a national average.

Inside LBG the same people are the 39 per cent of the mortgage book at EPC band D and the 17 per cent at E to G. The model is calibrated for gas heated homes in England and Wales, so Scotland and off gas properties would need separate work before any rollout.

## What specific impact do you think your solution will have?

Testable, not aspirational. A 12 week pilot on LBG mortgage customers at EPC band D or E, where the model is calibrated, each shown a payback figure and a ranked list for their own home, against a matched holdout.

Eco Home Reward claims ran to just over 3,000 in 2025 on a book of millions, a base rate near 0.1 per cent. Detecting a doubling needs roughly 30,000 per arm, which sets cohort size. Primary measure is green additional borrowing drawn, and accuracy is checked against the customer's own annual kWh. Failure is defined up front: no difference at 6 months means it does not work.

## How big is the market?

LBG puts home retrofit investment need at around £250 billion by 2050. Inside their own book, 39 per cent of residential mortgages with a known EPC are band D and 17 per cent are E to G, and just over 3,000 customers claimed the Eco Home Reward in 2025.

Their 2025 sustainability report says EPCs capture neither actual energy use nor recent retrofit work, and attributes a 2.0 per cent gap against its financed emissions reference pathway to EPC data limits. Every UK mortgage lender holds the same four fields and faces the same measurement problem, so the same licence fits any of them.

## Does your proposition use artificial intelligence?

NA, and deliberately. Every output is arithmetic over a published table, so any figure can be reproduced by hand and audited by your model risk team. It also keeps the interface four dropdowns rather than a chat box. The worst stock is the oldest: 18 per cent of NEED's earliest age band sits at EPC E or below against 0.5 per cent of the newest. Those owners need a clear form, not a conversation.

## Accessibility: WCAG 2.2 AA

Working towards, not conformant, and no formal audit has been done.

Measured this week: 100 of 100 images carry alt text, 151 label bindings, errors named per field, bound with aria-invalid and aria-describedby and announced through a live region with focus moved to them. Skip link on 62 of 64 pages. prefers-reduced-motion honoured. Last Lighthouse score 98.

On privacy: the site sets zero cookies and uses no client storage, analytics runs with consent mode denied, and fonts are self hosted. One third party request remains, Google Analytics. Calculator inputs never leave the browser.

## What stage of development are you?

Live and in public use, run by one person as a sole trader, incorporating Q4 2026. On the key person risk: I would carry professional indemnity and cyber cover for a pilot, and offer source escrow plus a perpetual licence to the model table, so LBG keeps what it built on if I am not here.

Search Console to 20 September 2026: 413 clicks from 52,068 impressions in 28 days, against 39 in March, and average position 25.6 in June to 11.0. The EPC calculator earns a 2.14 per cent click through rate from position 10.6 against 0.79 sitewide, so people choose this result over those around it.

## Who are your key customers?

No institutional customers yet. Users are UK homeowners arriving from search: 413 clicks in the last 28 days, and 94,563 impressions with 777 clicks across nine heat pump and boiler pages over 12 months.

Two limitations I would rather state than have found. Because the site stores nothing on the device, I have search and click data but no completion rates, no repeat use and no user feedback. And no model output has yet been checked against a real house's quote or metered consumption. Establishing that accuracy is the first thing I would want the pilot to do.

## Who are your competitors?

The Energy Saving Trust Home Energy Efficiency Tool, which LBG already white labels, as do Nationwide and Barclays. By both banks' own descriptions it returns current and improved bills, EPC before and after, measure costs and CO2. Neither mentions payback, and no method is published. It covers all of Great Britain and gives EPC and CO2 figures, which I do not.

Snugg, free and distributed by TSB. Kamma Climate and Cotality sell property level modelling to lenders, but the output goes to the lender. Installer funnels and paid surveys answer only after the customer has committed.

## What are you hoping to achieve, and how can LBG help?

A 12 week pilot. LBG licences the model, IP stays with me: a four figure pilot fee then a five figure annual licence. No revenue share, no referral links on LBG pages.

It is a lookup table plus arithmetic, no dependencies and no network calls, so it can be audited in an afternoon or rebuilt from a spec. No customer data moves.

The Consumer Duty harm is a household spending five figures on a wrong payback. Outputs are guidance, not advice, and every figure carries its assumptions.
