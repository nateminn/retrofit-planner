/* One place that holds every "next step" link the calculators offer.

   Each destination is named once here, so a change of address is a one line edit. The
   calculators pick which box to show from their own result: where a heat pump would cost
   more to run, the page says so and offers the tariff route instead of quotes. A site
   people trust for a five figure decision is the entire asset, and it survives exactly as
   long as the numbers are allowed to lead. */
(function () {
    'use strict';

    /* Awin publisher ID for Minnis and Company. This is NOT a secret: it appears in every
       tracking link. The Awin API token IS a secret and must never appear in this file or
       anywhere in the repo, because everything here ships to the browser. */
    var AWIN_ID = '3103652';

    /* An Awin deep link, in the format Awin's Link Builder produces. */
    function awin(merchantId, destination) {
        return 'https://www.awin1.com/cread.php?awinmid=' + merchantId
             + '&awinaffid=' + AWIN_ID
             + '&ued=' + encodeURIComponent(destination)
             + '&platform=pl';
    }

    /* paid: true marks a link that can earn us a commission. The box then carries
       rel="sponsored" and a disclosure ABOVE the link, before the reader clicks.
       Programme 25022 (Energy Performance Certificates) approved 26 September 2026.
       If it is ever suspended, set paid to false and href back to the government register. */
    var NEXT = {
        epc: {
            href: awin('25022', 'https://energyperformancecertificates.co.uk/domestic-epc'),
            paid: true,
            cta: 'Book an EPC online',
            note: 'An accredited assessor visits, lodges the certificate on the national register and it lasts ten years.',
            alt: { href: 'https://www.gov.uk/get-new-energy-certificate', text: 'find any accredited assessor on the government register' }
        },
        heatpump: {
            href: 'https://mcscertified.com/find-an-installer/',
            cta: 'Get heat pump quotes',
            note: 'Only MCS certified installers can claim the Boiler Upgrade Scheme grant on your behalf.'
        },
        solar: {
            href: 'https://mcscertified.com/find-an-installer/',
            cta: 'Get solar quotes',
            note: 'MCS certification is also what makes you eligible for Smart Export Guarantee payments.'
        },
        tariff: {
            href: '/guides/best-heat-pump-tariffs/',
            cta: 'Compare heat pump tariffs',
            note: 'The tariff changes running costs more than almost anything else you can do.'
        },
        insulation: {
            href: 'https://www.trustmark.org.uk/find-a-tradesperson',
            cta: 'Find an insulation installer',
            note: 'TrustMark registration is required for most grant funded insulation work.'
        },
        grants: {
            href: '/grants/',
            cta: 'Check which grants you qualify for',
            note: ''
        }
    };

    function get(key) {
        var p = NEXT[key];
        return p ? { href: p.href, cta: p.cta, note: p.note, paid: !!p.paid, alt: p.alt || null } : null;
    }

    /* Builds a next step box. `key` picks the destination, `heading` and `body` carry the
       honest framing for the result that produced it. */
    window.rpPartnerBox = function (key, heading, body) {
        var p = get(key);
        if (!p) { return ''; }
        var external = p.href.charAt(0) !== '/';
        var html = '<div class="cta-box">';
        html += '<h3>' + heading + '</h3>';
        html += '<p>' + body + (p.note ? ' ' + p.note : '') + '</p>';
        /* Above the link, not below it: a disclosure met after the click is not a disclosure. */
        if (p.paid) {
            html += '<p class="cta-disclosure">This is a paid link: we may earn a commission if you order through it. '
                  + 'It costs you nothing and does not change any figure above.</p>';
        }
        var rel = external ? (p.paid ? ' target="_blank" rel="sponsored noopener"' : ' target="_blank" rel="noopener"') : '';
        html += '<a href="' + p.href + '"' + rel + '>' + p.cta + '</a>';
        if (p.alt) {
            html += '<p class="cta-alt">Or <a href="' + p.alt.href + '" target="_blank" rel="noopener">' + p.alt.text + '</a>.</p>';
        }
        html += '</div>';
        return html;
    };

    window.rpPartner = get;
})();
