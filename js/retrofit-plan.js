/* Retrofit plan: from four facts about a home to an ordered list of works, each with a
   cost, a yearly saving and a payback, and a total for the whole plan.

   One file drives both /retrofit-plan/ and /embed/retrofit-plan/, so the two can never
   disagree. It reads heat demand, heat pump size, installed cost, efficiency and the
   grant from /js/heat-model.js, which must load first.

   SAVINGS ARE MEASURED, NOT MODELLED. Each insulation saving is the median fall in gas
   use that the government measured in real homes after that measure was fitted: NEED
   Impact of Measures 2026, Table 1 (DESNZ, 11 June 2026; installs mid-May 2023 to
   mid-May 2024). Measured savings are lower than the modelled figures most tools quote,
   because many homes were under-heated before and take part of the gain as warmth.

   COSTS. Insulation: Energy Saving Trust 2026 figures for a typical home (loft updated
   8 May 2026, cavity 10 February 2026, solid wall 18 June 2026). Heat pump: the median
   recorded under the Boiler Upgrade Scheme for a heat pump of the home's size, from the
   shared model.

   ORDER. Fabric first, cheapest payback first, then the heat pump sized for the home
   after insulation. Measures combine multiplicatively, so two 10 per cent savings make
   19, not 20. */
(function () {
    'use strict';

    var PRICE = { gas: 0.0797, oil: 0.113, lpg: 0.095, electric: 0.2632 };   // pounds per kWh, as RP_HEAT.prices
    var HP_TARIFF = 0.198;                                                     // pounds per kWh on a heat pump tariff
    var FUEL_NAME = { gas: 'mains gas', oil: 'heating oil', lpg: 'LPG', electric: 'electric heating' };

    var MEASURES = {
        loftBare: { name: 'Loft insulation to 270mm', cost: 750, saving: 0.0321, n: 1486,
            note: 'The measured figure covers top-ups as well as bare lofts. A loft with no insulation at all usually saves more than this.' },
        loftTopUp: { name: 'Loft insulation top-up to 270mm', cost: 600, saving: 0.0321, n: 1486,
            note: 'Measured average saving after loft insulation, top-ups and bare lofts together.' },
        cavity: { name: 'Cavity wall insulation', cost: 2700, saving: 0.1198, n: 2191,
            note: 'Energy Saving Trust puts a typical home at about £2,700. It is often free through a grant.' },
        solidInternal: { name: 'Solid wall insulation (internal)', cost: 12000, saving: 0.1728, n: 2411,
            note: 'About £12,000 for a typical 3 bed semi. External insulation costs about £15,000 and avoids losing room space.' }
    };

    function round(v, to) { return Math.round(v / to) * to; }
    function gbp(v) { return '£' + Math.round(v).toLocaleString('en-GB'); }

    /* inputs: { type, beds, insulation, fuel, loft, walls }
       loft: 'none' | 'some' | 'full' | 'unknown'; walls: 'cavity-empty' | 'cavity-filled' |
       'solid' | 'solid-insulated' | 'unknown' */
    function plan(inp) {
        var H = window.RP_HEAT;
        var fuel = inp.fuel;
        var heat = H.heatDemand(inp.type, inp.beds, inp.insulation, 'gas');
        var eff = H.boilerEfficiency(fuel === 'electric' ? 'electricity' : fuel);
        var fuelKwh = fuel === 'gas' ? H.gasKwh(inp.type, inp.beds, inp.insulation) : heat / eff;
        var baseCost = fuelKwh * PRICE[fuel];

        var candidates = [];
        var top = inp.type !== 'flat';   // lofts belong to houses, bungalows and top floor flats
        if (inp.loft === 'none' || (inp.loft === 'unknown' && inp.insulation === 'poor')) {
            if (top) { candidates.push({ key: 'loftBare', unsure: inp.loft === 'unknown' }); }
        } else if (inp.loft === 'some' || inp.loft === 'unknown') {
            if (top) { candidates.push({ key: 'loftTopUp', unsure: inp.loft === 'unknown' }); }
        }
        if (inp.walls === 'cavity-empty' || (inp.walls === 'unknown' && inp.insulation !== 'excellent' && inp.insulation !== 'good')) {
            candidates.push({ key: 'cavity', unsure: inp.walls === 'unknown' });
        }
        if (inp.walls === 'solid') {
            candidates.push({ key: 'solidInternal', unsure: false });
        }

        /* Rank fabric by payback on today's bill, then apply in that order so each saving
           is taken from what is left after the ones before it. */
        candidates.forEach(function (c) {
            var m = MEASURES[c.key];
            c.name = m.name; c.cost = m.cost; c.note = m.note; c.n = m.n; c.pct = m.saving;
            c.rank = m.cost / (baseCost * m.saving);
        });
        candidates.sort(function (a, b) { return a.rank - b.rank; });

        var remaining = 1, steps = [];
        candidates.forEach(function (c) {
            var saving = baseCost * remaining * c.pct;
            remaining *= (1 - c.pct);
            steps.push({ kind: 'fabric', key: c.key, name: c.name, cost: c.cost, costNote: 'Typical cost, before any grant',
                saving: saving, payback: c.cost / saving, note: c.note, unsure: c.unsure,
                measured: (c.pct * 100).toFixed(1) + '% measured median saving, ' + c.n.toLocaleString('en-GB') + ' homes' });
        });

        /* Heat pump for the home as it will be after the insulation above. */
        var heatAfter = heat * remaining;
        var fuelCostAfter = baseCost * remaining;
        var cop = H.cop(inp.insulation);
        var hpStandard = heatAfter / cop * PRICE.electric;
        var hpTariff = heatAfter / cop * HP_TARIFF;
        // Sized and costed for the home after the insulation above, not before it.
        var kw = H.kwForHeat(heatAfter);
        var install = H.heatPumpInstallForKw(kw);
        var range = H.rangeForCost(install);
        var grant = H.busGrant(fuel);
        var net = Math.max(0, install - grant);
        var saveTariff = fuelCostAfter - hpTariff;
        var saveStandard = fuelCostAfter - hpStandard;
        var hp = {
            kind: 'heatpump', name: 'Air source heat pump', kw: kw,
            cost: net, install: install, range: range, grant: grant,
            costNote: 'After the £' + grant.toLocaleString('en-GB') + ' Boiler Upgrade Scheme grant',
            saving: saveTariff, savingStandard: saveStandard,
            payback: saveTariff > 0 ? net / saveTariff : null,
            hpTariff: hpTariff, hpStandard: hpStandard, fuelCostAfter: fuelCostAfter, cop: cop
        };
        steps.push(hp);

        var fabricCost = 0, fabricSaving = 0;
        steps.forEach(function (s) { if (s.kind === 'fabric') { fabricCost += s.cost; fabricSaving += s.saving; } });
        return {
            inputs: inp, fuelName: FUEL_NAME[fuel], baseCost: baseCost, fuelKwh: fuelKwh, heat: heat,
            steps: steps, fabricCost: fabricCost, fabricSaving: fabricSaving,
            // The whole-plan figures count the heat pump only where it lowers the bill.
            totalCost: fabricCost + (saveTariff > 0 ? net : 0), totalSaving: fabricSaving + (saveTariff > 0 ? saveTariff : 0),
            heatPumpPays: saveTariff > 0
        };
    }

    function paybackLabel(p) {
        if (p === null || !isFinite(p) || p <= 0) { return 'No payback'; }
        if (p < 1) { return 'Under a year'; }
        if (p >= 50) { return 'Over 50 years'; }
        return Math.round(p) + ' years';
    }

    function render(el, r) {
        var h = '';
        h += '<p class="rp-lead">Your home uses about <strong>' + round(r.fuelKwh, 100).toLocaleString('en-GB') + ' kWh</strong> of '
            + r.fuelName + ' a year, costing about <strong>' + gbp(r.baseCost) + '</strong> for the energy alone. Here is the order we would do the work in.</p>';
        h += '<ol class="rp-steps">';
        r.steps.forEach(function (s, i) {
            h += '<li class="rp-step' + (s.kind === 'heatpump' ? ' rp-hp' : '') + '">';
            h += '<div class="rp-step-head"><span class="rp-num">' + (i + 1) + '</span><h3>' + s.name + (s.unsure ? ' <span class="rp-if">if your home needs it</span>' : '') + '</h3></div>';
            h += '<div class="rp-figs">';
            h += '<div><span class="rp-l">Cost</span><span class="rp-v">' + gbp(s.cost) + '</span><span class="rp-d">' + s.costNote + '</span></div>';
            if (s.kind === 'heatpump') {
                h += '<div><span class="rp-l">Yearly saving</span><span class="rp-v">' + (s.saving > 0 ? gbp(s.saving) : 'None') + '</span><span class="rp-d">On a 19.8p heat pump tariff. '
                    + (s.savingStandard > 0 ? gbp(s.savingStandard) + ' on a standard tariff' : gbp(-s.savingStandard) + ' a year more on a standard tariff') + '</span></div>';
            } else {
                h += '<div><span class="rp-l">Yearly saving</span><span class="rp-v">' + gbp(s.saving) + '</span><span class="rp-d">' + s.measured + '</span></div>';
            }
            h += '<div><span class="rp-l">Payback</span><span class="rp-v">' + paybackLabel(s.payback) + '</span><span class="rp-d">' + (s.kind === 'heatpump' ? 'After the grant, on a heat pump tariff' : s.key === 'loftBare' ? 'On the measured average; likely shorter for a bare loft' : 'At full price') + '</span></div>';
            h += '</div>';
            if (s.kind === 'heatpump') {
                h += '<p class="rp-note">' + (/^(8|11|18)(\.|$)/.test(String(s.kw)) ? 'An ' : 'A ') + s.kw + ' kW heat pump, typically ' + gbp(s.range[0]) + ' to ' + gbp(s.range[1]) + ' installed (median ' + gbp(s.install)
                    + ') before the grant, for a home like yours after the insulation above. Running cost ' + gbp(s.hpTariff) + ' a year on a heat pump tariff, against '
                    + gbp(s.fuelCostAfter) + ' for your current heating after insulation. Only an MCS certified installer can claim the grant.</p>';
            } else {
                h += '<p class="rp-note">' + s.note + '</p>';
            }
            h += '</li>';
        });
        h += '</ol>';
        h += '<div class="rp-total"><div><span class="rp-l">Whole plan</span><span class="rp-v">' + gbp(r.totalCost) + '</span><span class="rp-d">' + (r.heatPumpPays ? 'After the heat pump grant, before any insulation grant' : 'Insulation only, before any grant') + '</span></div>'
            + '<div><span class="rp-l">Saving a year</span><span class="rp-v">' + gbp(r.totalSaving) + '</span><span class="rp-d">' + (r.heatPumpPays ? 'With a heat pump tariff' : 'Insulation only; the heat pump would not lower your bill') + '</span></div>'
            + '<div><span class="rp-l">Payback</span><span class="rp-v">' + paybackLabel(r.totalSaving > 0 ? r.totalCost / r.totalSaving : null) + '</span><span class="rp-d">Simple payback at today\'s prices</span></div></div>';
        var fabricSteps = r.steps.filter(function (s) { return s.kind === 'fabric'; }).length;
        h += '<p class="rp-small">Savings are what homes like yours measurably saved, not the most you could save. '
            + (fabricSteps > 1 ? 'Where the plan has more than one insulation measure, each saving is taken from what is left after the one before; homes that had two measures at once measured less than that, so treat the combined figure as an upper guide. ' : '')
            + 'Costs are typical figures, and grants can cover some or all of the insulation. '
            + (r.inputs.fuel === 'oil'
                ? 'Prices: electricity at the Ofgem cap for October to December 2026; heating oil at 11.3p per kWh, the UK average on 25 September 2026. Oil prices move, so your own bill may differ. '
                : r.inputs.fuel === 'lpg'
                ? 'Prices: electricity at the Ofgem cap for October to December 2026; LPG at 9.5p per kWh, which varies by supplier and contract. '
                : 'Prices: Ofgem cap for October to December 2026, energy only' + (r.inputs.fuel === 'gas' ? '; gas also carries a £108 a year standing charge, which you save if you cap the supply after switching. ' : '. '))
            + (r.inputs.fuel === 'electric' ? 'Electric heating is priced at the standard rate; storage heaters on Economy 7 cost less to run, so your current bill and the heat pump saving will both be lower. ' : '')
            + '<a href="/accuracy/">How accurate are these figures?</a></p>';
        el.innerHTML = h;
    }

    window.RP_PLAN = { plan: plan, render: render, measures: MEASURES, price: PRICE };
})();
