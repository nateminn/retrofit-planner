/* One place that holds every commercial link on the site.

   WHY IT EXISTS. Partner programmes get approved, change rate, and close. Before this, the
   money links were hard coded into 19 pages pointing at MCS and TrustMark, which earn nothing
   and send people to a competitor's installer finder. Now each destination is named once here.
   When an Awin programme is approved, paste the tracking URL into `url` and the whole site
   switches. Until then `url` stays empty and every call falls back to the useful non earning
   link, so nothing is ever broken or dead.

   HOW TO ACTIVATE ONE. Set url to the Awin deeplink, set `paid` to true, and that is all.
   Leave `fallback` alone: it is what runs if the programme is later suspended.

   THE RULE THIS FILE ENFORCES. A partner link is only ever offered as the genuine next step
   for the answer the visitor just got. The calculators pick which partner to show from their
   own result, not from which one pays most. Where a result says a heat pump will cost more to
   run, the page says so and offers the tariff route instead of pushing quotes anyway. That is
   not squeamishness: a site people trust for a five figure decision is the entire asset, and
   it survives exactly as long as the numbers are allowed to lead. */
(function () {
    'use strict';

    /* Awin publisher ID for Minnis and Company. This is NOT a secret: it appears in every
       tracking link on every affiliate site in the world. The API token is a secret and must
       never appear in this file or anywhere else in the repo, because everything here ships
       to the browser. */
    var AWIN_ID = '3103652';

    /* Builds an Awin tracking link. Once a programme is approved, all a partner entry below
       needs is `awinmid` plus the destination it should land on. */
    function awin(merchantId, destination) {
        // Format taken from Awin's own Link Builder API response, including platform=pl.
        //
        // OPEN programmes, each confirmed by following its bare awinmid redirect and landing
        // on the merchant's own site:
        //   25022 EPC and Gas Safety, 13574 BOXT, 54765 E.ON Next,
        //   118321 Project Solar, 18758 Heatable.
        // CLOSED, do not use: 5342 British Gas Boilers CPL. Its redirect serves Awin's
        // closedMerchant.html, so the programme no longer accepts publishers. The Link
        // Builder still mints links for it because the advertiser record exists. That is
        // the trap: a link generating successfully proves the id is known, nothing more.
        //
        // Approval is a separate thing again. An unapproved link still redirects but pays
        // nothing, which is why none of these are switched on below.
        return 'https://www.awin1.com/cread.php?awinmid=' + merchantId
             + '&awinaffid=' + AWIN_ID
             + '&ued=' + encodeURIComponent(destination)
             + '&platform=pl';
    }

    var PARTNERS = {
        epc: {
            // When programme 25022 is approved: paid: true, url: awin('25022', '<their landing page>')
            paid: false, url: '',
            fallback: 'https://www.gov.uk/get-new-energy-certificate',
            cta: 'Book an accredited EPC assessment',
            note: 'An assessor visits, lodges the certificate on the national register and it lasts ten years.'
        },
        heatpump: {
            // On approval of 13574 BOXT:   paid: true, url: awin('13574', 'https://www.boxt.co.uk/heat-pumps')
            // or 18758 Heatable:           paid: true, url: awin('18758', 'https://heatable.co.uk/heat-pumps')
            paid: false, url: '',
            fallback: 'https://mcscertified.com/find-an-installer/',
            cta: 'Get heat pump quotes',
            note: 'Only MCS certified installers can claim the Boiler Upgrade Scheme grant on your behalf.'
        },
        solar: {
            // On approval of 118321 Project Solar: paid: true, url: awin('118321', 'https://www.projectsolaruk.com/')
            // or 18758 Heatable:                   paid: true, url: awin('18758', 'https://heatable.co.uk/solar')
            paid: false, url: '',
            fallback: 'https://mcscertified.com/find-an-installer/',
            cta: 'Get solar quotes',
            note: 'MCS certification is also what makes you eligible for Smart Export Guarantee payments.'
        },
        tariff: {
            // On approval of 54765 E.ON Next: paid: true, url: awin('54765', 'https://www.eonnext.com/')
            paid: false, url: '',
            fallback: '/guides/best-heat-pump-tariffs/',
            cta: 'Compare heat pump tariffs',
            note: 'The tariff changes running costs more than almost anything else you can do.'
        },
        insulation: {
            // No open Awin programme fits this slot. Insulation is mostly grant funded or
            // local trade, and the search demand here is small. The TrustMark fallback is
            // the right answer, not a placeholder waiting to be monetised.
            paid: false, url: '',
            fallback: 'https://www.trustmark.org.uk/find-a-tradesperson',
            cta: 'Find an insulation installer',
            note: 'TrustMark registration is required for most grant funded insulation work.'
        },
        grants: {
            // Deliberately never commercial. Grants are public money and the honest answer
            // is the government route, whatever a partner would pay to sit here.
            paid: false, url: '', fallback: '/grants/',
            cta: 'Check which grants you qualify for',
            note: ''
        }
    };

    function get(key) {
        var p = PARTNERS[key];
        if (!p) { return null; }
        return {
            href: p.url || p.fallback,
            paid: !!(p.url && p.paid),
            cta: p.cta,
            note: p.note
        };
    }

    /* Builds a next step box. `key` picks the partner, `heading` and `body` carry the honest
       framing for the result that produced it. Adds rel="sponsored" and a disclosure line only
       when the link actually earns, because claiming a commercial relationship that does not
       exist is its own kind of dishonesty. */
    window.rpPartnerBox = function (key, heading, body) {
        var p = get(key);
        if (!p) { return ''; }
        var external = p.href.charAt(0) !== '/';
        var rel = external ? (p.paid ? ' target="_blank" rel="sponsored noopener"' : ' target="_blank" rel="noopener"') : '';
        var html = '<div class="cta-box">';
        html += '<h4>' + heading + '</h4>';
        html += '<p>' + body + (p.note ? ' ' + p.note : '') + '</p>';
        html += '<a href="' + p.href + '"' + rel + '>' + p.cta + '</a>';
        if (p.paid) {
            html += '<p class="cta-disclosure">We may be paid a commission if you go on to buy '
                  + 'through this link. It costs you nothing and it does not change the figures '
                  + 'above, which come from the same model whatever you decide.</p>';
        }
        html += '</div>';
        return html;
    };

    window.rpPartner = get;
})();
