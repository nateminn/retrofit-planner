/* One heat demand model, shared by every page that compares heating costs.

   Two pages used to disagree by a factor of 2.4 on the same house: the heat pump
   calculator put a 5-bed mid-terrace at 16,000 kWh of heat demand while the boiler
   comparison put it at 6,600 kWh. Both tables were unsourced. This one is not.

   SOURCE. DESNZ National Energy Efficiency Data-Framework (NEED) 2026, covering 2024
   consumption in England and Wales.
   - The shape of the table comes from the 50,000 row anonymised sample: 39,502 records
     whose main heating fuel is gas and which recorded 2024 gas consumption. Median
     consumption was taken for every property type and floor area band with at least 50
     records, then fitted against floor area for each type.
   - The bedroom scale was calibrated so the population weighted result reproduces NEED's
     own published median gas consumption by bedroom count (Table 3c: 5,215 / 7,954 /
     10,540 / 13,787 / 19,339 kWh for 1 to 5 or more bedrooms). It lands within 0.3% for
     2 to 5 bedrooms and 3.3% for 1 bedroom. The implied floor areas are 40, 70, 101, 139, 205 square
     metres for 1 to 5 or more bedrooms.
   - The insulation adjustment is measured the same way, comparing EPC bands WITHIN each
     property type and floor area cell so that size is not counted twice. Across 17 such
     cells the medians relative to band D are: A/B 0.62, C 0.85, D 1.00, E 1.11.
     That is a much narrower spread than the 1.0 to 1.5 range this site used to assume,
     and it is what the data supports.

     WHY THERE IS NO BAND F OR G TIER, checked against the 2026 sample on 24 September
     2026 rather than assumed. NEED reports F and G as one band, and the 50,000 row sample
     holds 635 such records, 312 of them gas heated with 2024 consumption. Measured the
     same way as the tiers above, within property type and floor area cells, F/G comes out
     at 1.04, which is BELOW band E at 1.11. Three cells clear 30 records and all three
     agree: mid terrace 1.04, semi 1.03 and 1.06. Loosening the threshold to 10 records
     gives 1.06 across 11 cells. In every cell with enough data, F/G households buy 3 to 5
     per cent LESS gas than band E households in the same size and type of house.
     That is almost certainly under-heating rather than efficiency: the worst bands
     correlate with fuel poverty, and metered consumption measures what people buy, not
     what the building needs. Two consequences. A tier at 1.04 would have the site tell
     the owner of a solid wall Victorian house that it uses less than a band E one, which
     is true of the meter and useless as advice. And demand for any home in these bands is
     understated for heat pump sizing, because a heat pump will heat the house properly
     where the old system did not.
     Beware the naive version of this calculation: pooling all records regardless of
     property size gives F/G 1.23, because the worst bands skew towards larger older
     houses. That confounds band with size, which is what the within cell method exists
     to avoid.

   Figures are median ANNUAL GAS CONSUMPTION in kWh for a gas heated home at EPC band D,
   which includes hot water and any gas cooking. Multiply by boiler efficiency for the
   heat actually delivered. */
(function () {
    'use strict';

    var MODEL = {
        // Median annual gas consumption, kWh, at EPC band D.
        gas: {
            'detached': { 1: 7100, 2: 9400, 3: 11700, 4: 14600, 5: 19500 },
            'semi': { 1: 4100, 2: 7500, 3: 11000, 4: 15300, 5: 22800 },
            'end-terrace': { 1: 6600, 2: 8400, 3: 10300, 4: 12600, 5: 16500 },
            'mid-terrace': { 1: 4300, 2: 7000, 3: 9800, 4: 13200, 5: 19100 },
            'bungalow': { 1: 7000, 2: 9200, 3: 11500, 4: 14300, 5: 19100 },
            'flat': { 1: 5600, 2: 7100, 3: 8700, 4: 10700, 5: 14100 },
        },
        // Relative to EPC band D, measured within property type and floor area cells.
        insulation: { excellent: 0.62, good: 0.85, average: 1.00, poor: 1.11 },
        // Seasonal performance of a well specified air source heat pump, by how well the
        // fabric lets it run at a low flow temperature.
        cop: { excellent: 3.4, good: 3.2, average: 2.9, poor: 2.6 },
        // Real world seasonal efficiency, below the lab figure on the badge.
        boilerEfficiency: { gas: 0.90, oil: 0.85, lpg: 0.85, electric: 1.0 },
        // Installed cost before any grant, for a typical 3-bed of that type.
        heatPumpBase: { detached: 11000, semi: 10000, 'mid-terrace': 9000,
                        'end-terrace': 9500, bungalow: 10000, flat: 8000 },
        // A new condensing gas boiler, across the £1,500 to £3,500 range the site quotes.
        boilerBase: 2500
    };

    function clampBeds(b) {
        b = parseInt(b, 10);
        if (!b || b < 1) { return 1; }
        return b > 5 ? 5 : b;
    }

    window.RP_HEAT = {
        model: MODEL,
        /* Annual gas consumption in kWh for this home, before any change of heating. */
        gasKwh: function (type, beds, insulation) {
            var row = MODEL.gas[type];
            if (!row) { return null; }
            var base = row[clampBeds(beds)];
            var f = MODEL.insulation[insulation];
            return Math.round(base * (f === undefined ? 1 : f));
        },
        /* Heat actually delivered into the home each year, in kWh. */
        heatDemand: function (type, beds, insulation, fuel) {
            var gas = this.gasKwh(type, beds, insulation);
            if (gas === null) { return null; }
            var eff = MODEL.boilerEfficiency[fuel || 'gas'];
            return Math.round(gas * (eff === undefined ? 0.90 : eff));
        },
        cop: function (insulation) {
            var c = MODEL.cop[insulation];
            return c === undefined ? MODEL.cop.average : c;
        },
        boilerEfficiency: function (fuel) {
            var e = MODEL.boilerEfficiency[fuel];
            return e === undefined ? 0.90 : e;
        },
        /* Both install costs scale with the same size factor, so a 1-bed flat and a
           5-bed detached no longer get quoted the identical figure. */
        sizeFactor: function (beds) { return 1 + (clampBeds(beds) - 3) * 0.08; },
        heatPumpInstall: function (type, beds, insulation) {
            var base = MODEL.heatPumpBase[type];
            if (!base) { return null; }
            // A leakier home needs more emitters and a bigger unit for the same comfort.
            var fabric = insulation === 'poor' ? 1.15 : insulation === 'average' ? 1.05 : 1.0;
            var c = Math.round(base * this.sizeFactor(beds) * fabric / 100) * 100;
            return Math.max(7000, Math.min(c, 15000));
        },
        boilerInstall: function (beds) {
            var c = Math.round(MODEL.boilerBase * this.sizeFactor(beds) / 50) * 50;
            return Math.max(1500, Math.min(c, 3500));
        }
    };
})();
