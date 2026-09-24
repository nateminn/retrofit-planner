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

RetrofitPlanner.co.uk is a free UK home energy site I build and run on my own. Seven tools and 51 guides answer one question for one house: what does the work cost, what does it save, and what comes first. The retrofit plan puts that in order from four fields: property type, bedrooms, fabric condition and heating fuel.

It runs on published government data: meter readings for 39,502 homes, installed costs from 30,590 grant funded heat pumps, and savings measured in real homes. The method is public at /methodology/ and the model at /js/heat-model.js.

## Why did you develop this proposition? What problem are you solving?

Most retrofit figures available to households come from the company selling the work. They rarely show how the number was reached, so it cannot be checked. Increasingly the other source is an AI answer, which can walk someone through the options but rarely shows where a number came from.

A heat pump or solid wall insulation often costs five figures, and a household lives with it for 15 years or more. A decision that size deserves a visible method. I publish the process: public government data, a clear and simple model, and enough explanation for anyone to question the number before acting.

## What are the key features and benefits?

Seven free tools: a retrofit plan that orders the works for one home, heat pump cost, insulation savings, an EPC planner, solar, a 15 year boiler versus heat pump comparison and a grant checker. The plan also runs as an embeddable widget, built for a partner's own site.

Every figure traces to one model. Checks compare 18 guides and 148 table cells against it before anything publishes, and /accuracy/ shows the model tested against measured data, before and after.

## What is your Unique Selling Point?

Kamma Climate and Cotality already model retrofit at property level and sell it to lenders. I am not claiming nobody else can do this. The difference is the output and who receives it: they return a risk score to the lender, this returns a payback figure and an ordered sequence of works to the customer, from a method anyone can read.

It also withholds the sale. The boiler comparison hides the quote prompt and form wherever a new boiler stays cheaper over 15 years even on a heat pump tariff: 35 of its 120 combinations at a £900 gas bill.

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

No. For a decision this size, a household should be able to see the method and the data behind a number, not just a confident answer. Every output is arithmetic over a published table built from public government data, so anyone can check it or work it through by hand. This is not an anti AI position. It is the right tool for a choice people live with for 15 years.

## Accessibility: WCAG 2.2 AA

Working towards, not claiming conformance, because no formal manual audit has been done.

Automated testing finds no errors on any page: axe-core 4.13 against the WCAG 2.2 A and AA rules, at desktop and phone widths, including every calculator after it shows a result. Forms name each error, bind it to its field and announce it. Tables and charts that scroll can be reached by keyboard. Reduced motion is honoured.

On privacy: the site sets no cookies, analytics runs with consent mode denied, and calculator inputs never leave the browser.

## What stage of development are you?

Live and in public use since March 2026, built and run by one person. Not yet registered, with plans to register in Q4 2026. Every tool works today and is ready to test, including an embeddable retrofit plan.

On 24 September 2026 I tested the model against measured data and corrected it where it was off: installed costs, heat pump efficiency and insulation savings. The results are published at /accuracy/.

Clicks from Google search have risen every month since launch, and September passed the whole of August with eight days to spare.

## Who are your key customers?

No institutional customers yet. Users are homeowners who find the site through Google search, 93 per cent of them in the UK. Since September they can ask for installer quotes, with recorded consent, and the first requests have arrived.

The calculators store and send nothing, so I have no count of calculator uses. The model is tested against measured data from thousands of real installations, but not yet against individual homes' own bills. That is the first thing I would want the pilot to do.

## Who are your competitors?

The Energy Saving Trust Home Energy Efficiency Tool, which Lloyds already white labels, as do Nationwide and Barclays. By the banks' descriptions it returns current and improved bills, EPC before and after, measure costs and CO2. None mentions payback, and no method is published. It covers all of Great Britain and gives EPC and CO2 figures; my EPC planner is only a rough estimate.

Snugg, a free home energy planner TSB offers its customers. Kamma Climate and Cotality sell modelling to lenders, not advice to customers. Installer funnels answer only after the customer has committed.

## What are you hoping to achieve, and how can Lloyds help?

I am not asking for investment. I would like a 12 week pilot that tests two things: whether a published payback figure moves Lloyds customers to act, and whether the model's figures match real homes. If it works, we agree terms for wider use. If it does not, Lloyds has a clear answer at low cost.

The model is a lookup table plus arithmetic, so no customer data needs to move. Outputs are guidance, not advice, and every figure shows its assumptions.

---

## If they ask (interview prep, not for the form)

**Why publish the method at all?**
- A household spending five figures deserves to see how the number was reached.
- Publishing invites correction. Errors get found and fixed rather than hidden.
- For a bank under Consumer Duty, a published method is evidence the guidance is fair and explainable.
- It is the only way to be credibly independent of the firms selling the work.

**Where is the value if you collect no data?**
- The value is the decision it helps someone make, not data taken from them. The calculators store and send nothing.
- Four dropdowns carry little learning value. What would improve the model is outcomes: real bills and real quotes. That is exactly what a pilot measures.
- Inside Lloyds, measurement comes from Lloyds' own records of who went on to act. Nothing needs to leave the bank.
- The model itself needs no personal data, so running it inside Lloyds needs no data sharing agreement.

**Why would Lloyds pay for this?**
- Not yet, and I am not asking them to. The pilot exists to find out whether it is worth paying for.
- If it moves customers to act and the figures hold up against real homes, that result is the case for a licence.

**What if the model is wrong?**
- It has not yet been checked against real homes, and I say so in the application.
- It is built from government microdata and checked for internal consistency on every change. Testing it against real outcomes is the first job of the pilot.
