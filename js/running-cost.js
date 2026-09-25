/* What a heat pump would cost to run in a home, against the heating it has now.

   Drives /heat-pump-running-cost-calculator/. Heat demand, efficiency and prices all come
   from js/heat-model.js, and without the visitor's own usage the current heating cost is
   RP_BILLS.heatingCost, so this page, the energy bill calculator and the running cost
   guides give the same figure for the same home. Load heat-model.js and bills.js first.

   Running costs cover heating and hot water, before standing charges.

   USAGE. A visitor's own yearly figure replaces the model's median: gas, LPG and electric
   in kWh, oil in litres at 10.294 kWh a litre (DESNZ greenhouse gas conversion factors
   2026, gross calorific value). Heat delivered is usage times the system's efficiency:
   gas 90%, oil and LPG 85%, electric 100% (RP_HEAT.boilerEfficiency). */
(function () {
    'use strict';

    var OIL_KWH_PER_LITRE = 10.294;

    /* o: { type, beds, insulation, fuel: 'gas'|'oil'|'lpg'|'electric',
            tariff: 'hp'|'standard'|'custom', rate (pounds per kWh, custom only),
            usage (optional), efficiency (optional, else the measured value for the insulation) } */
    function cost(o) {
        var H = window.RP_HEAT, P = H.prices;
        var eff = H.boilerEfficiency(o.fuel);
        var price = { gas: P.gas, oil: P.oil, lpg: P.lpg, electric: P.electricity }[o.fuel];
        var heat, nowCost;
        if (o.usage) {
            var kwh = o.fuel === 'oil' ? o.usage * OIL_KWH_PER_LITRE : o.usage;
            heat = kwh * eff;
            nowCost = kwh * price;
        } else {
            heat = H.heatDemand(o.type, o.beds, o.insulation, 'gas');
            nowCost = window.RP_BILLS.heatingCost(o.type, o.beds, o.insulation, o.fuel);
        }
        var cop = o.efficiency || H.cop(o.insulation);
        var rate = o.tariff === 'custom' ? o.rate : o.tariff === 'standard' ? P.electricity : P.hpTariff;
        var hpKwh = heat / cop;
        return {
            heat: heat, cop: cop, rate: rate, hpKwh: hpKwh, hpCost: hpKwh * rate, nowCost: nowCost,
            hpPerHeat: rate / cop, nowPerHeat: price / eff, breakEven: price / eff * cop
        };
    }

    window.RP_RUNNING = { cost: cost, oilKwhPerLitre: OIL_KWH_PER_LITRE };
})();
