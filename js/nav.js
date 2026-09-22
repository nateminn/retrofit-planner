/* Brings the current page's nav link into view on the mobile strip. Without this the
   marker sits off screen on pages late in the nav order, so the strip looks like it is
   showing someone else's position. */
(function () {
    'use strict';
    function reveal() {
        var strip = document.querySelector('.nav-links');
        if (!strip || strip.scrollWidth <= strip.clientWidth) { return; }
        var active = strip.querySelector('a.active, a[aria-current="page"]');
        if (!active) { return; }
        var want = active.offsetLeft - (strip.clientWidth - active.offsetWidth) / 2;
        strip.scrollLeft = Math.max(0, want);
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', reveal);
    } else { reveal(); }
})();
