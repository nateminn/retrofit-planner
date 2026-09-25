/* A home's yearly energy bill: heating from the shared heat model, plus the electricity
   every home uses for lighting, appliances and cooking, plus standing charges.

   One file drives the energy bill calculator, the bill checker on the average bills
   guide and the bill figures the guides quote (docs/superpowers/tools/build_new_pages.py
   reads it), so they can never disagree. Load /js/heat-model.js first.

   ELECTRICITY. The median yearly electricity use for homes with that many bedrooms in
   England and Wales in 2024: DESNZ National Energy Efficiency Data-Framework, consumption
   headline tables 2026, Table 4c. It is a median across all homes, including the few
   heated by electricity, so it is a little above what lights and appliances alone use.

   STANDING CHARGES. Ofgem price cap, 1 October to 31 December 2026, direct debit:
   electricity 54.83p a day (£200.13 a year), gas 29.68p a day (£108.33 a year). Only a
   home on mains gas pays the gas one. */
(function () {
    'use strict';

    var ELEC_KWH = { 1: 1666, 2: 2137, 3: 2659, 4: 3371, 5: 4581 };   // 5 means 5 or more
    var STANDING = { electricity: 200.13, gas: 108.33 };
    var EFF = { oil: 0.85, lpg: 0.85 };

    function beds(b) { return Math.max(1, Math.min(5, parseInt(b, 10) || 3)); }

    function electricityKwh(b) { return ELEC_KWH[beds(b)]; }

    /* fuel: 'gas' | 'oil' | 'lpg' | 'electric' | 'heatpump' | 'heatpump-tariff' */
    function heatingCost(type, b, insulation, fuel) {
        var H = window.RP_HEAT, P = H.prices;
        var heat = H.heatDemand(type, beds(b), insulation, 'gas');
        if (fuel === 'gas') { return H.gasKwh(type, beds(b), insulation) * P.gas; }
        if (fuel === 'oil') { return heat / EFF.oil * P.oil; }
        if (fuel === 'lpg') { return heat / EFF.lpg * P.lpg; }
        if (fuel === 'electric') { return heat * P.electricity; }
        if (fuel === 'heatpump-tariff') { return heat / H.cop(insulation) * P.hpTariff; }
        return heat / H.cop(insulation) * P.electricity;   // heat pump on a standard tariff
    }

    /* The whole year's bill, split the way people see it. */
    function bill(type, b, insulation, fuel) {
        var P = window.RP_HEAT.prices;
        var heating = heatingCost(type, b, insulation, fuel);
        var electricity = electricityKwh(b) * P.electricity + STANDING.electricity;
        var gasStanding = fuel === 'gas' ? STANDING.gas : 0;
        return { heating: heating + gasStanding, electricity: electricity, total: heating + gasStanding + electricity,
                 electricityKwh: electricityKwh(b), gasStanding: gasStanding };
    }

    window.RP_BILLS = { bill: bill, heatingCost: heatingCost, electricityKwh: electricityKwh,
                        standing: STANDING, elecKwhByBeds: ELEC_KWH };
})();
