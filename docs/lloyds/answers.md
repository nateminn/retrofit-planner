# Lloyds Launch 2026 application, Homes challenge

Sub challenge: help customers manage, improve, protect and maximise the value of their homes.

Every figure below was verified in the repository or in a Google Search Console export on 24 September 2026. Search figures run from launch on 8 March to 22 September 2026, the latest day Google reports.

---

## Identity fields

- **Company name:** `Retrofit Planner`
- **Registered company name:** `Not yet registered. Trading as Retrofit Planner, with plans to register in Q4 2026`
- **Company registration number:** `Not yet registered, plans to register in Q4 2026`. If the field rejects text, leave it blank and tell Tom on the same thread. Do not enter digits: there is no number and any digits would be false.
- **Year founded:** `2026`
- **Locations of operation:** `United Kingdom`
- **Number of employees:** `1`
- **Which Launch focus area:** Homes
- **How did you hear about Launch:** Approached by Tom Hoskin at GrowthBuilders

## Short traction fields

- **Are you generating revenue?** `No`
- **Have you fundraised to date?** `N/A`
- **When are you next aiming to fundraise?** `No current plans` (your call, change it if that is not right)
- **Have you previously been in contact with Lloyds?** `NA`

---

## What do you do?

RetrofitPlanner.co.uk is a free UK home energy site I build and run on my own. Six calculators and 46 guides answer one question for one house: what does the work cost, what does it save, and what comes first.

Behind them is a heat demand model built from DESNZ National Energy Efficiency Data-Framework 2026 microdata, 39,502 gas heated records in England and Wales. It needs four fields: property type, floor area or bedrooms, fabric condition, heating fuel. No smart meter, no survey, no account. The method is published at /methodology/ and the model table is readable at /js/heat-model.js.

## Why did you develop this proposition? What problem are you solving?

Most retrofit figures a household can find come from the firm selling the work, with no method stated and no way to check them. Increasingly the other source is an AI answer, which can walk someone through it but rarely shows exactly where a number came from.

A heat pump or solid wall insulation often costs five figures, and a household lives with the choice for 15 years or more. A decision that size deserves a visible method. So I publish the process: public government data, a clear and simple model, and enough explanation for anyone to critique and judge the number before acting on it.

## What are the key features and benefits?

Six free tools: heat pump cost, insulation savings, an EPC planner, solar cost, a 15 year boiler versus heat pump comparison, and a grant checker. 46 guides across 60 pages. A bill checker inside one guide takes four inputs and tells a household how far their bill sits from typical for their house.

Every figure traces to one model. Two automated checks enforce that before anything publishes: one reads 18 guides for the model's demand figure, the other reads 148 cells across 8 property tables and works backwards from the costs. A wrong number fails the same check as a typo.

## What is your Unique Selling Point?

Kamma Climate and Cotality already model retrofit at property level and sell it to lenders. I am not claiming nobody else can do this. The difference is the output and who receives it: they return a risk score to the lender, this returns a payback figure and an ordered sequence of works to the customer, from a method anyone can read.

It also withholds the sale. The boiler tool hides both the quote prompt and the lead form when the old boiler is cheaper: at a £900 gas bill that is 42 of the tool's 120 input combinations. The solar tool tells 282 of 6,048 modelled cases it never pays back.

## Who is your target audience?

UK homeowners facing one decision, usually a boiler replacement forced by a breakdown, loft or wall insulation, or solar. They search by naming their own house: 3 bed semi, 4 bed detached, Victorian terrace, bungalow. They want a figure for that house, not a national average, and those are the searches the site ranks best for.

Inside Lloyds the same people are the 39 per cent of the mortgage book at EPC band D and the 17 per cent at E to G. The model is calibrated for gas heated homes in England and Wales, so Scotland and off gas properties would need separate work before any rollout.

## What specific impact do you think your solution will have?

Testable, not aspirational. A 12 week pilot on Lloyds mortgage customers at EPC band D or E, where the model is calibrated, each shown a payback figure and a ranked list for their own home, against a matched holdout.

Eco Home Reward claims ran to just over 3,000 in 2025 on a book of millions, a base rate near 0.1 per cent. Detecting a doubling needs roughly 30,000 per arm, which sets cohort size. Primary measure is green additional borrowing drawn, and accuracy is checked against the customer's own annual kWh. Failure is defined up front: no difference at 6 months means it does not work.

## How big is the market?

Lloyds puts UK home retrofit investment need at around £250 billion by 2050, yet just over 3,000 customers claimed its Eco Home Reward in 2025. In its own book, 39 per cent of residential mortgages with a known EPC are band D and 17 per cent are E to G.

The gap is not money, it is decisions. Doubling those claims is 3,000 more homes acting. At £9,000 to £16,000 for a heat pump installed, 3 bed semi to 4 bed detached, that is £27m to £48m of work. Every UK lender holds the same four fields and faces the same problem, so the same licence fits any of them.

## Does your proposition use artificial intelligence?

No. For a decision this size, a household should see the method and the data behind a number, not just a confident answer. Every output is arithmetic over a published table built from public government data, so anyone can check it, critique it or rebuild it by hand, your model risk team included. This is not anti AI. It is the right tool for a choice people live with for 15 years.

## Accessibility: WCAG 2.2 AA

Working towards, not conformant, and no formal audit has been done.

Measured this week: 100 of 100 images carry alt text, 151 label bindings, errors named per field, bound with aria-invalid and aria-describedby and announced through a live region with focus moved to them. Skip link on 62 of 64 pages. prefers-reduced-motion honoured. Last Lighthouse score 98.

On privacy: the site sets zero cookies and uses no client storage, analytics runs with consent mode denied, and fonts are self hosted. One third party request remains, Google Analytics. Calculator inputs never leave the browser.

## What stage of development are you?

Live and in public use since March 2026, built and run by one person. Not yet registered, with plans to register in Q4 2026.

Google search since launch: 39 clicks in March and 331 in August, with impressions up from 11,801 to 34,478. 22 days into September it has 346 clicks and 45,321 impressions, already past the whole of August and on pace for about 470 and 62,000.

It ranks best where people name their own house. The 4 bed heat pump cost guide averages position 3.6 on Google across 20,382 impressions, and the site averages position 6.3 for "epc points calculator".

## Who are your key customers?

No institutional customers yet. Users are UK homeowners arriving from Google: 1,325 clicks from 158,907 impressions since launch, 93 per cent of the clicks from the UK.

Two limitations I would rather state than have found. The site stores nothing on the device, so I have search data but no count of calculator uses, no completion rates and no user feedback. And no model output has yet been checked against a real house's quote or metered consumption. Establishing that accuracy is the first thing I would want the pilot to do.

## Who are your competitors?

The Energy Saving Trust Home Energy Efficiency Tool, which Lloyds already white labels, as do Nationwide and Barclays. By both banks' own descriptions it returns current and improved bills, EPC before and after, measure costs and CO2. Neither mentions payback, and no method is published. It covers all of Great Britain and gives EPC and CO2 figures, which I do not.

Snugg, free and distributed by TSB. Kamma Climate and Cotality sell property level modelling to lenders, but the output goes to the lender. Installer funnels and paid surveys answer only after the customer has committed.

## What are you hoping to achieve, and how can Lloyds help?

A 12 week pilot. Lloyds licences the model, IP stays with me: a four figure pilot fee then a five figure annual licence. No revenue share, no referral links on Lloyds pages.

It is a lookup table plus arithmetic, no dependencies and no network calls, so it can be audited in an afternoon or rebuilt from a spec. No customer data moves.

The Consumer Duty harm is a household spending five figures on a wrong payback. Outputs are guidance, not advice, and every figure carries its assumptions.
