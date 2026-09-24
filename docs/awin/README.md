# Awin applications

Publisher: Minnis and Company, ID 3103652. Promotional type: Editorial Content.

## Already applied (pending)

| ID | Merchant | Covers |
|----|----------|--------|
| 13574 | BOXT | boilers, heat pumps, solar, battery, EV |
| 25022 | EPCs, Gas Safety and Electrical Check | the EPC slot |
| 54765 | E.ON Next | the tariff slot |

## To apply (message file per merchant in this folder)

| ID | Merchant | Published rate | Covers |
|----|----------|----------------|--------|
| 73922 | Glow Green | £300 solar, £250 heat pump, £100 boiler, £50 battery, £25 AC, £10 EV. Per sale. | four of six tools |
| 122556 | OVO Solar and Heating | £35 CPL per validated lead | solar, heat pumps |
| 129571 | EDF Zero Carbon Homes | not published | solar, battery, heat pumps, EV |
| 118321 | Project Solar | not published | solar, battery |
| 18758 | Heatable | "negotiable, on request" | boilers, heat pumps, solar |

All five confirmed OPEN by following the bare awinmid redirect and landing on the
merchant's own site rather than Awin's closedMerchant.html. Cookie length is 30 days
on all five. Rates read from the public profile at ui.awin.com/merchant-profile/<id>,
which needs no login but renders the commission table in JavaScript, so curl misses it.

## Dead, do not look for it

5342 British Gas Boilers CPL. Its redirect serves closedMerchant.html. The Link Builder
still mints links for it because the advertiser record exists, which proves nothing about
whether the programme takes publishers.

## Figures used in the messages, all from the GSC export dated 20 Sep 2026

- 413 clicks, 52,068 impressions, 28 days to 20 Sep
- 39 clicks March, 331 August
- heat pump and boiler: 94,563 impressions, 777 clicks, nine pages
- /solar-calculator/: 13,191 impressions, 32 clicks, position 22.7
- /boiler-vs-heat-pump/: 11,929 impressions, position 11.2

The nine-page count folds GSC's anchor rows back into their parent page and drops
malformed and one-impression URLs. An earlier draft said 21 pages, which counted
those rows separately and would not have survived anyone checking.

## Paused on 24 September 2026

All affiliate activity was taken off the site on 24 September 2026: the Amazon tagged links
(unwrapped by docs/superpowers/tools/strip_affiliates.py), the per page commission notes, the
footer Amazon line, the privacy and About page sections, and the Awin machinery in
js/partners.js (publisher ID, the awin() link builder, the paid flags, rel="sponsored" and the
visible disclosure that appeared above paid links).

To bring Awin back after an approval, restore js/partners.js from commit 3be5248
(git show 3be5248:js/partners.js) and re-add the disclosure wording to privacy/ and about/.
The visible disclosure must sit above the paid link, before the reader clicks.

