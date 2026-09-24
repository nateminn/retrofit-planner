# Quote leads: how they work, and what to do with each one

Written 25 September 2026. The forms, consent wording and privacy text went live on
24 September. This is the operating manual for everything after someone presses
"Request my free quotes".

## Before you pass on or charge for a single lead

1. **Register with the ICO and pay the data protection fee.** Passing people's details to
   installers is trading in personal information, which the ICO says is not exempt.
   Tier 1 (micro organisations: turnover up to £632,000 or up to 10 staff) is £52 a year.
   Do it at ico.org.uk/for-organisations/data-protection-fee. It takes ten minutes and
   the register is public, which a bank reviewing you will check.
2. **Name the controller on the privacy page.** UK GDPR needs the identity of whoever is
   responsible for the data. Today the page says "Retrofit Planner". Once registered,
   add your name or your company's name as it appears on the ICO register.
3. **Keep the live tracker out of this repository.** The GitHub repo is public until you
   make it private, and even then a lead list does not belong in version control. Keep
   the real tracker in ~/Documents/RetrofitPlanner-Leads/ (or a private spreadsheet),
   using lead-tracker-template.csv as its header row.

## What each submission already proves

Every quote request in Netlify carries:

| Field | What it proves |
|---|---|
| created_at (Netlify) | When they asked |
| source | The page they asked on |
| consent_text | The exact wording they ticked |
| consent_version | Which version of that wording and which form, for example intro-v2-2026-09-24-heat-pump or intro-v2-2026-09-24-solar |
| share_ok = yes | That they ticked it. The box is required, so every request since 24 September has it |

Requests made before 24 September used the older optional box. Only pass those on if
share_ok is yes, and treat them under the wording they saw: "You may pass my details to
up to three MCS-certified installers so they can contact me directly with a quote."

Form names in Netlify: heat-pump-quote, solar-quote, insulation-quote, epc-quote,
home-upgrade-quote, newsletter.

## The two working days rule

The confirmation page tells people we pass their request on "usually within two working
days" and that we will email them if nobody covers their area. Keep that promise.

For each request:

1. **Acknowledge** within one working day (template in homeowner-replies.md).
2. **Find installers** covering the postcode on the right register, and check each one is
   currently certified on the day you pass the lead:
   - Heat pumps and solar: MCS, mcscertified.com/find-an-installer
   - Insulation: TrustMark, trustmark.org.uk/find-a-tradesperson
   - EPC: the government register of assessors, gov.uk/get-new-energy-certificate
3. **Pass the minimum**: first name, postcode, property type, heating, timing, the work
   wanted, email, and phone only if given. Send each installer their own email; never a
   list of several people.
4. **Tell the homeowner** who you passed them to (template).
5. **Record it** in the tracker: who, when, and the consent version.
6. **Delete** the request and its tracker row 12 months after it arrived, or sooner if
   they ask. Netlify: Forms, open the form, open the submission, Delete.

If someone withdraws consent, stop, tell any installer you already passed them to that
they have withdrawn and ask them to delete the details, and confirm to the person.

## Charging installers

The consent wording and the privacy, terms and about pages already say installers may
pay a fee for each introduction, so charging needs no change to the site. What must stay
true:

- Only certified installers, checked on the day.
- No more than three per request.
- The fee never changes a calculator result or which installers a person is offered.
- Never sell or share a lead with anyone who is not quoting for that job.

Price the introduction however you and the installer agree (per lead, or per job won).
No figure is suggested here because none was researched; ask two or three installers
what they pay other lead sources before you name a number.

## The Lloyds point

The application says the calculators withhold the quote prompt when their own figures
say the work does not pay. That is still true: on the heat pump calculator, the boiler
comparison and the solar calculator the form only appears when the result supports
getting quotes. Guides show the form to anyone reading about the work, which is a
reader's choice, not a recommendation.
