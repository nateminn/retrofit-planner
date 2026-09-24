/* One place that holds every "next step" link the calculators offer.

   Each destination is named once here, so a change of address is a one line edit. The
   calculators pick which box to show from their own result: where a heat pump would cost
   more to run, the page says so and offers the tariff route instead of quotes. A site
   people trust for a five figure decision is the entire asset, and it survives exactly as
   long as the numbers are allowed to lead. */
(function () {
    'use strict';

    var NEXT = {
        epc: {
            href: 'https://www.gov.uk/get-new-energy-certificate',
            cta: 'Book an accredited EPC assessment',
            note: 'An assessor visits, lodges the certificate on the national register and it lasts ten years.'
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
        return p ? { href: p.href, cta: p.cta, note: p.note } : null;
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
        html += '<a href="' + p.href + '"' + (external ? ' target="_blank" rel="noopener"' : '') + '>' + p.cta + '</a>';
        html += '</div>';
        return html;
    };

    window.rpPartner = get;
})();
