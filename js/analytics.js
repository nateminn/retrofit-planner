/* Google Analytics 4 for Retrofit Planner, in one place.

   WHY COOKIES AND NO BANNER. Since 5 February 2026 the Data (Use and Access) Act lets a site use
   cookies without consent when their only purpose is statistics about how the site is used, to
   improve it, provided visitors are told clearly and can object simply and for free (ICO guidance
   on storage and access technologies, "statistical purposes" exception, 29 April 2026). A third
   party tool qualifies only as a processor that uses the data for nothing else, so the Google
   Analytics property has every data sharing setting off, Google signals off and no Google Ads
   link, and this file keeps advertising storage denied and signals off in the page too.

   From 23 to 26 September 2026 analytics ran cookieless (consent denied), which kept GA4 from
   recording visits in its reports. Do not go back to that without a way to measure.

   WHAT IT SENDS. Page views with the address only: the path, plus any utm_ campaign tags. A
   shared result link carries calculator answers in its query string, and those never leave the
   page. The calculators add a "calculate" event naming the calculator (never the answers), and
   the thank-you pages add generate_lead and sign_up.

   OPTING OUT. The button on /privacy/ calls rpAnalytics.optOut(), which remembers the choice in
   this browser, deletes the Google Analytics cookies and stops Google Analytics loading at all. */
(function () {
    'use strict';

    var ID = 'G-4QMWG6G2WL';
    var KEY = 'rp-analytics-optout';
    var TAGS = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'];

    var out = false;
    try { out = window.localStorage.getItem(KEY) === '1'; } catch (e) { out = false; }

    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    if (out) { window['ga-disable-' + ID] = true; }

    /* The page address without calculator answers: keep the path and campaign tags only. */
    function pageLocation() {
        var kept = [];
        try {
            var q = new URLSearchParams(window.location.search);
            TAGS.forEach(function (t) { if (q.get(t)) { kept.push(t + '=' + encodeURIComponent(q.get(t))); } });
        } catch (e) { kept = []; }
        return window.location.origin + window.location.pathname + (kept.length ? '?' + kept.join('&') : '');
    }

    window.gtag('consent', 'default', {
        ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied',
        analytics_storage: out ? 'denied' : 'granted'
    });
    window.gtag('js', new Date());
    window.gtag('config', ID, {
        page_location: pageLocation(),
        allow_google_signals: false,
        allow_ad_personalization_signals: false
    });

    /* Loaded after the page, so it never slows the page down. */
    function load() {
        var s = document.createElement('script');
        s.async = true;
        s.src = 'https://www.googletagmanager.com/gtag/js?id=' + ID;
        document.head.appendChild(s);
    }
    if (!out) {
        if (document.readyState === 'complete') { load(); } else { window.addEventListener('load', load); }
    }

    function clearCookies() {
        var host = window.location.hostname;
        var domains = ['', host, '.' + host, '.' + host.replace(/^www\./, '')];
        document.cookie.split(';').forEach(function (c) {
            var name = c.split('=')[0].trim();
            if (name === '_ga' || name.indexOf('_ga_') === 0) {
                domains.forEach(function (d) {
                    document.cookie = name + '=; Max-Age=0; path=/' + (d ? '; domain=' + d : '');
                });
            }
        });
    }

    window.rpAnalytics = {
        optedOut: function () { return out; },
        optOut: function () {
            try { window.localStorage.setItem(KEY, '1'); } catch (e) { /* the page still stops for this visit */ }
            out = true;
            window['ga-disable-' + ID] = true;
            window.gtag('consent', 'update', { analytics_storage: 'denied' });
            clearCookies();
        },
        optIn: function () {
            try { window.localStorage.removeItem(KEY); } catch (e) { /* nothing stored */ }
            out = false;
            window['ga-disable-' + ID] = false;
        }
    };

    /* The opt-out control on /privacy/: a button and a status line. */
    function wire() {
        var btn = document.getElementById('analyticsOptOut');
        var status = document.getElementById('analyticsStatus');
        if (!btn || !status) { return; }
        function show() {
            status.textContent = out
                ? 'Analytics is off in this browser. We will not measure your visits here.'
                : 'Analytics is on in this browser.';
            btn.textContent = out ? 'Turn analytics back on' : 'Turn off analytics';
        }
        btn.addEventListener('click', function () {
            if (out) { window.rpAnalytics.optIn(); } else { window.rpAnalytics.optOut(); }
            show();
        });
        show();
    }
    if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', wire); } else { wire(); }
})();
