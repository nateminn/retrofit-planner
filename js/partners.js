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
        /* paid and href are decided by the SAME condition on purpose. An earlier version
           had href fall back with `p.url || p.fallback` while paid required both flags,
           so a slot holding a tracking url with paid still false would serve the money
           link while every other part of this file treated it as unpaid: no sponsored
           rel, no disclosure. That is the one state this file exists to make impossible. */
        var live = !!(p.url && p.paid);
        return {
            href: live ? p.url : p.fallback,
            paid: live,
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
        /* Above the link, not below it. A disclosure the reader meets after they have
           already clicked is not a disclosure. */
        if (p.paid) {
            html += '<p class="cta-disclosure">We may be paid a commission if you go on to buy '
                  + 'through this link. It costs you nothing and it does not change the figures '
                  + 'above, which come from the same model whatever you decide.</p>';
        }
        html += '<a href="' + p.href + '"' + rel + '>' + p.cta + '</a>';
        html += '</div>';
        return html;
    };

    window.rpPartner = get;

    /* The calculators write their partner box long after DOMContentLoaded, so the
       page level check has already run and found nothing. They call this once the
       box is in the DOM. It is idempotent and does nothing when no link earns. */
    window.rpDisclose = function () { showDisclosure(); };

    /* VISIBLE DISCLOSURE.

       rel="sponsored" tells a search engine a link is paid. It tells the reader nothing.
       The CMA guidance on hidden advertising and the ASA rules both ask for something
       stronger: the reader has to be able to tell a link is paid BEFORE they click it,
       without hunting for it. A line in the privacy policy does not meet that, and nor
       does an attribute they cannot see.

       So: if a page contains any link that actually earns, put one plain sentence at the
       top of the content saying so. Once per page, above the article, in the reader's
       path rather than beside it. Pages with no paid links get nothing, because a
       disclosure on a page that earns nothing is just noise that trains people to skip
       the real ones. */
    function paidLinkCount() {
        var n = 0, i, a;
        var rels = document.querySelectorAll('a[rel~="sponsored"]');
        for (i = 0; i < rels.length; i++) { if (rels[i].href) { n++; } }
        var slots = document.querySelectorAll('[data-partner]');
        for (i = 0; i < slots.length; i++) {
            a = get(slots[i].getAttribute('data-partner'));
            if (a && a.paid) { n++; }
        }
        return n;
    }

    function showDisclosure() {
        if (document.querySelector('.affiliate-note')) { return; }
        var main = document.querySelector('main');
        if (!main || !paidLinkCount()) { return; }
        var note = document.createElement('p');
        note.className = 'affiliate-note';
        note.setAttribute('role', 'note');
        note.textContent = 'Some links on this page earn us a commission if you buy. '
            + 'It costs you nothing, and it never changes the numbers or which option '
            + 'this page recommends.';
        // After the h1 where there is one, so the reader has the subject before the caveat.
        var h1 = main.querySelector('h1');
        if (h1 && h1.parentNode) { h1.parentNode.insertBefore(note, h1.nextSibling); }
        else { main.insertBefore(note, main.firstChild); }
    }

    /* Upgrades any anchor carrying data-partner to the paid destination once that
       programme is switched on above. Until then the anchor keeps the href already in
       the HTML, so the link works with JavaScript off and works if a programme is later
       suspended. Nothing here ever downgrades a link that is already correct. */
    function upgradeLinks() {
        var slots = document.querySelectorAll('a[data-partner]');
        for (var i = 0; i < slots.length; i++) {
            var el = slots[i];
            var p = get(el.getAttribute('data-partner'));
            if (!p || !p.paid || !p.href) { continue; }
            el.href = p.href;
            var rel = (el.getAttribute('rel') || '').split(/\s+/);
            if (rel.indexOf('sponsored') === -1) { rel.push('sponsored'); }
            if (rel.indexOf('noopener') === -1) { rel.push('noopener'); }
            el.setAttribute('rel', rel.join(' ').trim());
        }
    }

    function init() { upgradeLinks(); showDisclosure(); }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else { init(); }
})();
