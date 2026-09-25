/* The EPC points model and upgrade plan, as a pure function.

   Used by the landlord EPC calculator. The EPC calculator (epc-calculator/index.html) and its
   embeddable widget carry the same tables and plan logic inline; docs/superpowers/tools/
   epc_parity.js runs all three over every input combination and fails if this file gives a
   different band, points, cost or list of measures. Change all three together.

   Rough points model, NOT SAP: see the EPC calculator for what each table means and where
   the costs come from. */
(function () {
    'use strict';

    var BANDS = { G: 10, F: 30, E: 47, D: 62, C: 75, B: 86, A: 96 };
    var BAND_MIN = { A: 92, B: 81, C: 69, D: 55, E: 39, F: 21, G: 1 };
    var BAND_ORDER = ['G', 'F', 'E', 'D', 'C', 'B', 'A'];
    var EST = {
        base: 20,
        age: { pre1919: 8, '1919': 10, '1945': 13, '1965': 15, '1981': 17, '1991': 19, '2003': 21, '2012': 24 },
        type: { flat: 6, 'mid-terrace': 4, 'end-terrace': 2, semi: 1, detached: 0, bungalow: -1 },
        wall: { 'cavity-yes': 12, 'cavity-no': 4, 'solid-yes': 10, 'solid-no': 0 },
        loft: { none: 0, good: 7, na: 6 },
        glazing: { single: 0, partial: 3, double: 6, triple: 8 },
        heating: { 'old-gas': 6, 'new-gas': 14, oil: 8, lpg: 7, electric: -2, 'heat-pump': 18 },
        solar: { no: 0, yes: 8 },
        lighting: { old: 0, mixed: 1, led: 3 }
    };
    var MEASURES = [
        { id: 'loft', name: 'Loft insulation (270mm)', points: 7, cost: 750, requires: 'loft-none', grantEligible: true, link: '/insulation-calculator/' },
        { id: 'cavity', name: 'Cavity wall insulation', points: 8, cost: 2700, requires: 'wall-cavity-no', grantEligible: true, link: '/insulation-calculator/' },
        { id: 'led', name: 'LED lighting throughout', points: 3, cost: 200, requires: null, grantEligible: false, link: null },
        { id: 'controls', name: 'Smart heating controls', points: 3, cost: 275, requires: null, grantEligible: false, link: null },
        { id: 'glazing', name: 'Double glazing', points: 6, cost: 4800, requires: 'glazing-single', grantEligible: false, link: null },
        { id: 'glazing-partial', name: 'Replace remaining single glazing', points: 3, cost: 2400, requires: 'glazing-partial', grantEligible: false, link: null },
        { id: 'boiler', group: 'heating', name: 'New condensing gas boiler', points: 8, cost: 3500, requires: 'heating-old-gas', grantEligible: false, link: '/boiler-vs-heat-pump/' },
        { id: 'heatpump', group: 'heating', name: 'Air source heat pump', points: 12, cost: 12700, requires: 'heating-notHP', grantEligible: false, grantValue: 7500, link: '/heat-pump-calculator/' },
        { id: 'solar', name: 'Solar PV panels (4kW)', points: 8, cost: 6000, requires: 'solar-no', grantEligible: false, link: '/solar-calculator/' },
        { id: 'solidwall', name: 'Solid wall insulation (internal)', points: 10, cost: 12000, requires: 'wall-solid-no', grantEligible: true, link: '/insulation-calculator/' }
    ];
    var HP_COST = { flat: 11800, 'mid-terrace': 12400, 'end-terrace': 12600, semi: 12700, detached: 13000, bungalow: 13000 };

    function hpGrant(heating) { return (heating === 'oil' || heating === 'lpg') ? 9000 : 7500; }
    function bandOf(score) { return score >= 92 ? 'A' : score >= 81 ? 'B' : score >= 69 ? 'C' : score >= 55 ? 'D' : score >= 39 ? 'E' : score >= 21 ? 'F' : 'G'; }
    function atLeast(band, target) { return BAND_ORDER.indexOf(band) >= BAND_ORDER.indexOf(target); }
    function estimateScore(h) {
        var t = EST.base + EST.age[h.propAge] + EST.type[h.propType] + EST.wall[h.wall] + EST.loft[h.loft]
            + EST.glazing[h.glazing] + EST.heating[h.heating] + EST.solar[h.solar] + EST.lighting[h.lighting];
        return Math.max(1, Math.min(100, t));
    }

    /* h: { currentBand: 'A'..'G' | 'estimate', propType, propAge, wall, loft, glazing, heating, solar, lighting }
       Returns the cheapest-per-point plan that reaches target, exactly as the EPC calculator builds it. */
    function plan(h, targetBand) {
        var estimated = h.currentBand === 'estimate';
        var currentScore = estimated ? estimateScore(h) : BANDS[h.currentBand];
        var currentBand = estimated ? bandOf(currentScore) : h.currentBand;
        var pointsNeeded = BAND_MIN[targetBand] - currentScore;
        var out = { currentBand: currentBand, currentScore: currentScore, estimated: estimated, target: targetBand, measures: [], points: 0, cost: 0 };
        if (pointsNeeded <= 0) {
            out.met = true; out.newScore = currentScore; out.newBand = currentBand; out.reachesTarget = true;
            return out;
        }
        function estPoints(m) {
            switch (m.id) {
                case 'loft':            return EST.loft.good - EST.loft[h.loft];
                case 'cavity':          return EST.wall['cavity-yes'] - EST.wall[h.wall];
                case 'solidwall':       return EST.wall['solid-yes'] - EST.wall[h.wall];
                case 'glazing':         return EST.glazing.double - EST.glazing[h.glazing];
                case 'glazing-partial': return EST.glazing.double - EST.glazing[h.glazing];
                case 'boiler':          return EST.heating['new-gas'] - EST.heating[h.heating];
                case 'heatpump':        return EST.heating['heat-pump'] - EST.heating[h.heating];
                case 'solar':           return EST.solar.yes - EST.solar[h.solar];
                case 'led':             return EST.lighting.led - EST.lighting[h.lighting];
                default:                return m.points;
            }
        }
        var available = MEASURES.filter(function (m) {
            if (m.requires === 'loft-none' && h.loft !== 'none') { return false; }
            if (m.requires === 'wall-cavity-no' && h.wall !== 'cavity-no') { return false; }
            if (m.requires === 'wall-solid-no' && h.wall !== 'solid-no') { return false; }
            if (m.requires === 'glazing-single' && h.glazing !== 'single') { return false; }
            if (m.requires === 'glazing-partial' && h.glazing !== 'partial') { return false; }
            if (m.requires === 'heating-old-gas' && h.heating !== 'old-gas') { return false; }
            if (m.requires === 'heating-notHP' && h.heating === 'heat-pump') { return false; }
            if (m.requires === 'solar-no' && h.solar !== 'no') { return false; }
            return true;
        }).map(function (m) {
            var c = Object.assign({}, m, { points: Math.max(0, estPoints(m)) });
            if (c.id === 'heatpump') { c.cost = HP_COST[h.propType] || c.cost; c.grantValue = hpGrant(h.heating); }
            return c;
        }).filter(function (m) { return m.points > 0; });
        function netOf(m) { return Math.max(0, m.cost - (m.grantValue || 0)); }
        available.sort(function (a, b) { return (netOf(a) / a.points) - (netOf(b) / b.points); });
        var used = [], run = currentScore;
        for (var i = 0; i < available.length; i++) {
            var m = available[i];
            if (out.points >= pointsNeeded) { break; }
            if (m.group) { if (used.indexOf(m.group) !== -1) { continue; } used.push(m.group); }
            var net = Math.round(netOf(m));
            out.points += m.points; out.cost += net; run += m.points;
            out.measures.push(Object.assign({}, m, { netCost: net, runScore: Math.min(run, 100), runBand: bandOf(run) }));
        }
        out.newScore = Math.min(currentScore + out.points, 100);
        out.newBand = bandOf(out.newScore);
        out.reachesTarget = atLeast(out.newBand, targetBand);
        return out;
    }

    window.RP_EPC = { plan: plan, bandOf: bandOf, atLeast: atLeast, estimateScore: estimateScore, BAND_MIN: BAND_MIN, BAND_ORDER: BAND_ORDER };
})();
