/* What insulation costs to install, by type of home. One table for the insulation
   calculator, the retrofit plan and the insulation cost guides
   (docs/superpowers/tools/build_new_pages.py reads this file), so they cannot disagree.

   SOURCE. Energy Saving Trust advice pages, Great Britain figures, typical professional
   installation, unsubsidised, read from their published tables on 25 September 2026:
   - Cavity wall insulation, page updated 8 May 2026: detached house £3,900, semi-detached
     £2,200, mid-terrace £1,100, detached bungalow £1,700, mid-floor flat £950; "typical
     installation costs in Great Britain are around £2,200". (Earlier pages on this site
     used £2,700, the figure on the version updated 10 February 2026.)
   - Loft insulation, page updated 8 May 2026: 0 to 270mm detached £1,100, semi £750,
     mid-terrace £650, detached bungalow £1,200; top-up from 120mm to 270mm detached £800,
     semi £600, mid-terrace £500, detached bungalow £800.
   - Solid wall insulation, page updated 18 June 2026: around £12,000 internal and £15,000
     external for a typical install; the Trust does not split it by home.
   - Floor insulation, page updated 19 May 2026: a suspended timber floor £1,400 to £2,500
     depending on house type; solid floors considerably more.

   WHERE THE TRUST PUBLISHES NOTHING we borrow the nearest home and say so on the page:
   an end-terrace takes the semi-detached figures (one party wall, similar size), and a
   top-floor flat's loft takes the mid-terrace figures (the smallest roof the Trust prices).
   Bungalow figures are the Trust's detached bungalow. */
(function () {
    'use strict';

    var COSTS = {
        loftBare:   { detached: 1100, semi: 750, 'end-terrace': 750, 'mid-terrace': 650, bungalow: 1200, flat: 650 },
        loftTopUp:  { detached: 800, semi: 600, 'end-terrace': 600, 'mid-terrace': 500, bungalow: 800, flat: 500 },
        cavity:     { detached: 3900, semi: 2200, 'end-terrace': 2200, 'mid-terrace': 1100, bungalow: 1700, flat: 950 },
        solidInternal: 12000,
        solidExternal: 15000,
        floorRange: [1400, 2500],
        // homes the Trust prices directly; the others borrow, as above
        published: {
            loftBare: ['detached', 'semi', 'mid-terrace', 'bungalow'],
            loftTopUp: ['detached', 'semi', 'mid-terrace', 'bungalow'],
            cavity: ['detached', 'semi', 'mid-terrace', 'bungalow', 'flat']
        },
        typical: { loftBare: 750, loftTopUp: 600, cavity: 2200 }
    };

    function cost(measure, type) {
        var t = COSTS[measure];
        if (typeof t === 'number') { return t; }
        return (t && t[type]) || COSTS.typical[measure];
    }

    window.RP_INS = { costs: COSTS, cost: cost };
})();
