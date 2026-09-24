// Parity test: run the EPC calculator logic from both pages on every input combination
// with a stub DOM, and compare band, points, total cost and the list of measures.
// The /embed/ page promises the widget matches the full calculator; this keeps it true.
// Usage: node docs/superpowers/tools/epc_parity.js   (exit code 1 on any mismatch)
const fs = require('fs'), vm = require('vm');
const ROOT = require('path').resolve(__dirname, '../../..') + '/';
function scriptOf(path, marker) {
  const s = fs.readFileSync(ROOT + path, 'utf8');
  const blocks = [...s.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
  return blocks.find(b => b.includes(marker));
}
function makeCtx(code) {
  const els = {};
  function el(id) {
    if (!els[id]) { els[id] = { id, value: '', textContent: '', _h: '', hidden: true, style: {},
      children: [], classList: { add() {}, remove() {}, contains() { return false; } },
      appendChild(c) { this.children.push(c); }, setAttribute() {}, querySelector() { return null; } };
      Object.defineProperty(els[id], 'innerHTML', { get() { return this._h; }, set(v) { this._h = v; if (v === '') this.children = []; } }); }
    return els[id];
  }
  const document = { getElementById: el, createElement: () => ({ textContent: '', className: '', style: {}, children: [], appendChild(c) { this.children.push(c); } }),
    documentElement: { scrollHeight: 0 }, body: {} };
  const ctx = { document, window: { parent: null, addEventListener() {} }, console,
    rpRequire: () => true, rpRequireOne: () => true, rpReveal: () => {}, rpPartnerBox: () => '' };
  ctx.window.parent = ctx.window;
  vm.createContext(ctx);
  vm.runInContext(code.replace(/^\s*const /gm, 'var ').replace(/^\s*let /gm, 'var '), ctx);
  return { ctx, els, el };
}
const main = makeCtx(scriptOf('epc-calculator/index.html', 'function calculate()'));
const emb = makeCtx(scriptOf('embed/epc-calculator/index.html', 'function calc()'));
const V = {
  currentBand: ['estimate', 'G', 'F', 'E', 'D', 'C', 'B'], targetBand: ['C', 'B', 'A'],
  propType: ['detached', 'semi', 'mid-terrace', 'end-terrace', 'bungalow', 'flat'],
  propAge: ['pre1919', '1919', '1945', '1965', '1981', '1991', '2003', '2012'],
  hasWall: ['cavity-no', 'cavity-yes', 'solid-no', 'solid-yes'], hasLoft: ['none', 'good', 'na'],
  hasDoubleGlazing: ['single', 'partial', 'double', 'triple'],
  heating: ['old-gas', 'new-gas', 'oil', 'lpg', 'electric', 'heat-pump'], hasSolar: ['no', 'yes'],
  lighting: ['old', 'mixed', 'led'] };
const keys = Object.keys(V);
let n = 0, bad = 0, examples = [], alreadyMet = 0;
function readMain() {
  const h = main.el('resultsContent').innerHTML;
  if (h.includes('You already meet your target')) return { met: true, band: (h.match(/Band ([A-G]),/) || [])[1] };
  const vals = [...h.matchAll(/<div class="value">([^<]*)<\/div>/g)].map(m => m[1]);
  const names = [...h.matchAll(/font-size: 0.95rem;">(?:<a[^>]*>)?([^<]+)/g)].map(m => m[1]);
  const pts = [...h.matchAll(/margin-top: 2px;">\+(\d+) points: /g)].map(m => +m[1]);
  return { now: vals[0], band: vals[1], pts: vals[2], cost: vals[3], names: names.join('|'), each: pts.join(',') };
}
function readEmb() {
  const g = id => emb.el(id).textContent;
  if (g('newPts') === 'already at or above target') return { met: true, band: g('nowBand').replace('Band ', '') };
  const rows = emb.el('planBody').children.map(tr => tr.children.map(td => td.textContent));
  return { now: g('nowBand'), band: g('newBand'), pts: '+' + rows.reduce((a, r) => a + (+r[1].slice(1)), 0),
    cost: g('cost'), names: rows.map(r => r[0].replace(/ \(after the .*\)$/, '').replace('Loft insulation to 270mm', 'Loft insulation (270mm)')).join('|'), each: rows.map(r => r[1].slice(1)).join(',') };
}
function rec(i, cur) {
  if (i === keys.length) {
    for (const k of keys) { main.el(k).value = cur[k]; emb.el(k).value = cur[k]; }
    main.el('tenure').value = 'owner';
    main.ctx.calculate(); emb.ctx.calc();
    const a = readMain(), b = readEmb(); n++;
    let same;
    if (a.met || b.met) { same = a.met && b.met; if (same) alreadyMet++; }
    else same = a.now === b.now && a.band === b.band && a.pts === b.pts && a.cost === b.cost && a.names === b.names && a.each === b.each;
    if (!same) { bad++; if (examples.length < 5) examples.push({ cur: { ...cur }, a, b }); }
    return;
  }
  const vals = (keys[i] === 'propAge' && cur.currentBand !== 'estimate') ? ['1965'] : V[keys[i]];
  for (const v of vals) { cur[keys[i]] = v; rec(i + 1, cur); }
}
rec(0, {});
console.log(JSON.stringify({ combinations: n, mismatches: bad, alreadyMeetTarget: alreadyMet }));
for (const e of examples) console.log(JSON.stringify(e));
console.log((bad ? 'FAIL' : 'PASS') + ': EPC widget and EPC calculator agree on ' + (n - bad).toLocaleString('en-GB') + ' of ' + n.toLocaleString('en-GB') + ' combinations');
process.exitCode = bad ? 1 : 0;
