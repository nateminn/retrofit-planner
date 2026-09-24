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
   heat actually delivered.

   CALIBRATED AGAINST MEASURED DATA, 24 September 2026. Two inputs were assumptions until
   then, and both were checked against what real installations recorded. Both moved.
   The full comparison, before and after, is published at /accuracy/.

   - Heat pump efficiency. Was 2.6 / 2.9 / 3.2 / 3.4 by fabric. Now the whole system
     seasonal performance (SPFH4: heat pump, immersion, backup heater and circulation
     pumps, which is what the household pays for) measured in 428 air source heat pumps
     by the Electrification of Heat trial (Energy Systems Catapult for DESNZ, final report
     December 2024, Table 1.2): median 2.78, quartiles 2.55 and 3.05. Poor fabric takes
     the lower quartile, average the median, good the upper quartile, and excellent 3.25,
     about the 90th percentile of that distribution. The old average of 2.9 was 4 per
     cent above the measured median, so every heat pump running cost was a little low.
   - Heat pump installed cost. Was a flat base per property type. Now the median cost
     installers reported for air source heat pumps paid under the Boiler Upgrade Scheme in
     2025/26, by capacity band (DESNZ BUS statistics, August 2026 release, Table A1.3A,
     30,590 installations), read at the size this model gives the home. Those costs include
     the system, labour and VAT, before the grant. The old figures matched the data for
     large homes but sat 2,000 to 4,000 pounds low for small ones, because an install has
     fixed costs that do not shrink with the house. The ranges quoted on the site are the
     scheme's Q2 2026 quartiles scaled to each median (Table Q1.1A).
   - Size. The kW a home needs is its annual heat demand over 1,100 full load hours,
     which reproduces the sizes the site's guides quote for each house type. */
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
        // Measured whole system seasonal performance (SPFH4), Electrification of Heat
        // trial, 428 air source heat pumps: lower quartile, median, upper quartile, ~P90.
        cop: { excellent: 3.25, good: 3.05, average: 2.78, poor: 2.55 },
        // Real world seasonal efficiency, below the lab figure on the badge. Electric
        // heating appears under both names because the pages use both; a missing key used
        // to fall back silently to 0.90 and price every electric home as 90% efficient.
        boilerEfficiency: { gas: 0.90, oil: 0.85, lpg: 0.85, electric: 1.0, electricity: 1.0 },
        // Median installed cost, pounds, of air source heat pumps paid under the Boiler
        // Upgrade Scheme in 2025/26, at each capacity band's midpoint in kW (Table A1.3A).
        // The 16 to 18 kW band (14,817) sits below 14 to 16 kW on a smaller sample, so it
        // is skipped to keep cost rising with size. Above 20 kW the scheme reports too few
        // homes of this kind to use.
        busCostByKw: [[5, 11494], [7, 12164], [9, 12686], [11, 13943], [13, 15365], [15, 15496], [19, 17878]],
        // Q2 2026 lower and upper quartile as a share of the median: 11,128 and 15,627
        // against 12,908 (Table Q1.1A).
        busSpread: [0.862, 1.211],
        // Hours a year at full output. Heat demand over this gives the kW the guides quote.
        fullLoadHours: 1100,
        // Boiler Upgrade Scheme grant: 7,500, or 9,000 replacing oil or LPG (gov.uk, raised
        // 2026, available until March 2027).
        busGrant: 7500, busGrantOilLpg: 9000,
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
        /* Boiler install cost scales with the home. */
        sizeFactor: function (beds) { return 1 + (clampBeds(beds) - 3) * 0.08; },
        /* Heat pump size in kW, to the nearest half kW. */
        heatPumpKw: function (type, beds, insulation) {
            var heat = this.heatDemand(type, beds, insulation, 'gas');
            if (heat === null) { return null; }
            var kw = Math.round(heat / MODEL.fullLoadHours * 2) / 2;
            return Math.max(4, Math.min(kw, 20));
        },
        /* Median installed cost for a heat pump of that size under the Boiler Upgrade
           Scheme, interpolated between capacity bands, to the nearest 100 pounds. A leakier
           home costs more because it needs a bigger unit, which the size already carries. */
        heatPumpInstall: function (type, beds, insulation) {
            var kw = this.heatPumpKw(type, beds, insulation);
            return kw === null ? null : this.heatPumpInstallForKw(kw);
        },
        /* The same median for a heat pump of a given size, for callers that size it
           themselves, such as the retrofit plan sizing for the home after insulation. */
        heatPumpInstallForKw: function (kw) {
            var t = MODEL.busCostByKw, c;
            if (kw <= t[0][0]) { c = t[0][1]; }
            else if (kw >= t[t.length - 1][0]) { c = t[t.length - 1][1]; }
            else {
                for (var i = 1; i < t.length; i++) {
                    if (kw <= t[i][0]) {
                        var f = (kw - t[i - 1][0]) / (t[i][0] - t[i - 1][0]);
                        c = t[i - 1][1] + f * (t[i][1] - t[i - 1][1]);
                        break;
                    }
                }
            }
            return Math.round(c / 100) * 100;
        },
        kwForHeat: function (heat) {
            return Math.max(4, Math.min(Math.round(heat / MODEL.fullLoadHours * 2) / 2, 20));
        },
        rangeForCost: function (c) {
            return [Math.round(c * MODEL.busSpread[0] / 500) * 500, Math.round(c * MODEL.busSpread[1] / 500) * 500];
        },
        /* The middle half of real installs around that median, to the nearest 500 pounds. */
        heatPumpInstallRange: function (type, beds, insulation) {
            var c = this.heatPumpInstall(type, beds, insulation);
            if (c === null) { return null; }
            return [Math.round(c * MODEL.busSpread[0] / 500) * 500, Math.round(c * MODEL.busSpread[1] / 500) * 500];
        },
        /* The grant for the fuel being replaced. */
        busGrant: function (fuel) {
            return (fuel === 'oil' || fuel === 'lpg' || fuel === 'oil-boiler' || fuel === 'lpg-boiler')
                ? MODEL.busGrantOilLpg : MODEL.busGrant;
        },
        boilerInstall: function (beds) {
            var c = Math.round(MODEL.boilerBase * this.sizeFactor(beds) / 50) * 50;
            return Math.max(1500, Math.min(c, 3500));
        }
    };
})();
