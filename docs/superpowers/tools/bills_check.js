#!/usr/bin/env node
/* Every whole-bill figure the site states must equal js/bills.js.

   js/bills.js adds the electricity a home uses for lighting, appliances and cooking (the
   NEED median by bedrooms) to the heat model's heating cost. The energy bill calculator
   computes live, but its tables are static, the bill checker on the average bills guide
   inlines its own copy of the electricity figures, and the five energy-bills-N pages are
   generated. This loads the real scripts and compares each of those with them.

   Usage: node docs/superpowers/tools/bills_check.js   (exit code 1 on any mismatch) */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const ROOT = path.resolve(__dirname, '../../..');
const ctx = { window: {} };
vm.createContext(ctx);
for (const f of ['js/heat-model.js', 'js/bills.js']) vm.runInContext(fs.readFileSync(path.join(ROOT, f), 'utf8'), ctx);
const B = ctx.window.RP_BILLS;
const gbp = v => '£' + Math.round(v).toLocaleString('en-GB');
const bad = [];
let n = 0;
const read = p => fs.readFileSync(path.join(ROOT, p), 'utf8');
const text = s => s.replace(/<[^>]+>/g, '').replace(/&pound;/g, '£').trim();
function rows(html, from) {
    const s = html.slice(html.indexOf(from));
    const t = s.slice(0, s.indexOf('</table>'));
    return [...t.matchAll(/<tr>(.*?)<\/tr>/gs)].map(m => [...m[1].matchAll(/<t[hd][^>]*>(.*?)<\/t[hd]>/gs)].map(c => text(c[1])));
}
function expect(where, got, want) {
    n++;
    if (got !== want) bad.push(`${where}: page says ${got}, js/bills.js gives ${want}`);
}

/* 1. The energy bill calculator's three tables */
const calc = read('energy-bill-calculator/index.html');
const HOMES = { '1 bed flat': ['flat', 1], '2 bed flat': ['flat', 2], '2 bed mid-terrace': ['mid-terrace', 2],
    '2 bed bungalow': ['bungalow', 2], '3 bed mid-terrace': ['mid-terrace', 3], '3 bed semi-detached': ['semi', 3],
    '3 bed detached': ['detached', 3], '4 bed detached': ['detached', 4], '5 bed detached': ['detached', 5] };
for (const r of rows(calc, 'id="typical-bills"').slice(1)) {
    const h = HOMES[r[0]];
    if (!h) { bad.push('energy-bill-calculator: unknown row ' + r[0]); continue; }
    const b = B.bill(h[0], h[1], 'average', 'gas');
    expect('energy-bill-calculator ' + r[0], r.slice(1).join(' '), [gbp(b.total), gbp(b.total / 12), gbp(b.heating), gbp(b.electricity)].join(' '));
}
const FUELS = { 'Mains gas boiler': 'gas', 'Oil boiler': 'oil', 'LPG boiler': 'lpg', 'Electric heating, standard rate': 'electric',
    'Heat pump, standard tariff': 'heatpump', 'Heat pump, heat pump tariff': 'heatpump-tariff' };
for (const r of rows(calc, 'id="fuel"').slice(1)) expect('energy-bill-calculator fuel ' + r[0], r[1], gbp(B.bill('semi', 3, 'average', FUELS[r[0]]).total));
const ins = calc.match(/poor (£[\d,]+) a year, average (£[\d,]+), good (£[\d,]+) and excellent (£[\d,]+)/);
if (!ins) bad.push('energy-bill-calculator: insulation sentence not found');
else ['poor', 'average', 'good', 'excellent'].forEach((i, k) => expect('energy-bill-calculator insulation ' + i, ins[k + 1], gbp(B.bill('semi', 3, i, 'gas').total)));

/* 2. The bill checker's inline electricity figures on the average bills guide */
const avg = read('guides/average-energy-bills-uk/index.html');
const D = JSON.parse(avg.match(/var D=(\{.*?\});/s)[1]);
const BEDS = { flat1: 1, flat2: 2, terrace2: 2, semi3: 3, det3: 3, det4: 4, det5: 5 };
for (const k in BEDS) {
    const want = B.bill('semi', BEDS[k], 'average', 'gas').electricity;
    n++;
    if (!D[k] || Math.abs(D[k].e - want) > 0.01) bad.push(`average-energy-bills-uk bill checker ${k}: e is ${D[k] && D[k].e}, js/bills.js gives ${want.toFixed(2)}`);
}

/* 3. The generated energy-bills-N pages: every home row and the fuel table */
const PAGES = { 'energy-bills-1-bed-flat': [1, { '1 bed flat': 'flat' }], 'energy-bills-2-bed-house': [2, { '2 bed terrace': 'mid-terrace', '2 bed flat': 'flat' }],
    'energy-bills-3-bed-house': [3, { '3 bed semi': 'semi', '3 bed detached': 'detached' }], 'energy-bills-4-bed-house': [4, { '4 bed detached': 'detached' }],
    'energy-bills-5-bed-house': [5, { '5 bed detached': 'detached' }] };
const PFUEL = { 'Mains gas boiler': 'gas', 'Oil boiler': 'oil', 'LPG boiler': 'lpg', 'Electric heating, standard rate': 'electric', 'Heat pump, standard rate': 'heatpump' };
for (const [slug, [beds, homes]] of Object.entries(PAGES)) {
    const html = read('guides/' + slug + '/index.html');
    const main = Object.entries(homes)[0];
    for (const r of rows(html, 'id="by-type"').slice(1)) {
        const t = homes[r[0]];
        if (!t) continue;
        const b = B.bill(t, beds, 'average', 'gas');
        expect(slug + ' ' + r[0], r.slice(1).join(' '), [gbp(b.total), gbp(b.total / 12), gbp(b.heating), gbp(b.electricity)].join(' '));
    }
    for (const r of rows(html, 'id="fuel"').slice(1)) {
        const f = PFUEL[r[0]] || (/heat pump tariff/.test(r[0]) ? 'heatpump-tariff' : null);
        if (f) expect(slug + ' fuel ' + r[0], r[1], gbp(B.bill(main[1], beds, 'average', f).total));
    }
}

for (const b of bad) console.log('  ' + b);
console.log(`${bad.length ? 'FAIL' : 'PASS'}: ${n} bill figures checked against js/bills.js`);
process.exit(bad.length ? 1 : 0);
