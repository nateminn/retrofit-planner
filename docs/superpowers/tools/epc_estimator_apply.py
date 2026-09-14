#!/usr/bin/env python3
"""Add the EPC rating estimator to epc-calculator/index.html. Idempotent (skips if the estimate option exists)."""
import re, json, sys
p='epc-calculator/index.html'; s=open(p,encoding='utf-8').read()
if 'value="estimate"' in s: print('already applied'); sys.exit(0)
def rep(old,new,count=1):
    global s
    assert s.count(old)>=1, 'NOT FOUND: '+old[:80]; s=s.replace(old,new,count)
rep('<option value="">Select your current EPC band</option>\n                    <option value="G">G (1-20 points)</option>',
    '<option value="">Select your current EPC band</option>\n                    <option value="estimate">Not sure, estimate it for me</option>\n                    <option value="G">G (1-20 points)</option>')
m=re.search(r'(<div class="form-group">\s*<label for="propType">.*?</div>\s*)', s, re.S); assert m
new_inputs='''            <div class="form-group">
                <label for="propAge">When was it built?</label>
                <select id="propAge">
                    <option value="">Select (needed for an estimate)</option>
                    <option value="pre1919">Before 1919</option>
                    <option value="1919">1919 to 1944</option>
                    <option value="1945">1945 to 1964</option>
                    <option value="1965">1965 to 1980</option>
                    <option value="1981">1981 to 1990</option>
                    <option value="1991">1991 to 2002</option>
                    <option value="2003">2003 to 2011</option>
                    <option value="2012">2012 or later</option>
                </select>
                <p class="helper">Age sets the starting point of the estimate. Older homes lose more heat through walls and floors even when insulated.</p>
            </div>
            <div class="form-group">
                <label for="lighting">Lighting</label>
                <select id="lighting">
                    <option value="mixed">Mix of LED and older bulbs</option>
                    <option value="led">Mostly LED</option>
                    <option value="old">Mostly halogen or old bulbs</option>
                </select>
            </div>
'''
s=s[:m.end()]+new_inputs+s[m.end():]
rep('<p class="helper">Check your EPC at <a href="https://www.gov.uk/find-energy-certificate" target="_blank" rel',
    '<p class="helper">Choose "estimate it for me" if you do not know your band. Check for an existing certificate at <a href="https://www.gov.uk/find-energy-certificate" target="_blank" rel')
rep('<h2>Your current EPC details</h2>','<h2>Estimate your rating, or enter your band</h2>')
rep("Tell us about your property and current EPC, and we'll show you the most cost-effective improvements.","Tell us about your home. If you do not know your EPC band we estimate it from the age, insulation and heating, then rank every improvement by cost per point.")
rep('<button class="btn-calculate" onclick="calculate()">Show my improvement plan</button>','<button class="btn-calculate" onclick="calculate()">Estimate my rating and show the plan</button>')
rep('Updated March 2026</div>','Updated September 2026</div>')
rep('<h1>EPC Improvement Calculator</h1>','<h1>EPC Calculator: Your Rating and the Cheapest Upgrades</h1>')
rep('<p>Find the cheapest way to improve your EPC rating. We rank every improvement by cost-effectiveness so you know what to do first.',
    '<p>Not sure of your EPC rating? Estimate it from your home\'s age, insulation and heating, then see every improvement ranked by cost per point so you know what to do first.')
old_d=re.search(r'<meta name="description" content="([^"]*)"',s).group(1)
new_d='Free EPC calculator: estimate your rating from your home\'s age, insulation and heating, then see which upgrades add the most points for the least money.'
assert len(new_d)<=155; s=s.replace(old_d,new_d)
rep("    const BANDS = { G: 10, F: 30, E: 47, D: 62, C: 75, B: 86, A: 96 };",
"""    const BANDS = { G: 10, F: 30, E: 47, D: 62, C: 75, B: 86, A: 96 };
    // Estimate of the current SAP score. Base and age steps are calibrated to English Housing Survey
    // averages (mean 67 across England in 2023; 86% of post-1990 homes in bands A to C against 23% of
    // pre-1919 homes); the adjustments use the same point ranges as the improvement table on this page.
    const EST = {
        base: 20,
        age: { pre1919: 8, '1919': 10, '1945': 13, '1965': 15, '1981': 17, '1991': 19, '2003': 21, '2012': 24 },
        type: { flat: 6, 'mid-terrace': 4, 'end-terrace': 2, semi: 1, detached: 0, bungalow: -1 },
        wall: { 'cavity-yes': 12, 'cavity-no': 4, 'solid-yes': 10, 'solid-no': 0 },
        loft: { none: 0, good: 7, na: 6 },
        glazing: { single: 0, partial: 3, double: 6, triple: 8 },
        heating: { 'old-gas': 6, 'new-gas': 14, oil: 8, electric: -2, 'heat-pump': 18 },
        solar: { no: 0, yes: 8 },
        lighting: { old: 0, mixed: 1, led: 3 }
    };
    function bandOf(score) { return score >= 92 ? 'A' : score >= 81 ? 'B' : score >= 69 ? 'C' : score >= 55 ? 'D' : score >= 39 ? 'E' : score >= 21 ? 'F' : 'G'; }
    function estimateScore(age, type, wall, loft, glazing, heating, solar, lighting) {
        const total = EST.base + EST.age[age] + EST.type[type] + EST.wall[wall] + EST.loft[loft] + EST.glazing[glazing] + EST.heating[heating] + EST.solar[solar] + EST.lighting[lighting];
        return Math.max(1, Math.min(100, total));
    }""")
rep("""        const currentBand = document.getElementById('currentBand').value;
        const targetBand = document.getElementById('targetBand').value;""",
"""        let currentBand = document.getElementById('currentBand').value;
        const targetBand = document.getElementById('targetBand').value;
        const propType = document.getElementById('propType').value;
        const propAge = document.getElementById('propAge').value;
        const lighting = document.getElementById('lighting').value;""")
rep("""        if (!currentBand || !targetBand || !loft || !wall || !glazing || !heating || !solar || !tenure) {
            alert('Please fill in all fields.'); return;
        }

        const currentScore = BANDS[currentBand];""",
"""        if (!currentBand || !targetBand || !propType || !loft || !wall || !glazing || !heating || !solar || !tenure) {
            alert('Please fill in all fields.'); return;
        }
        let estimated = false, currentScore;
        if (currentBand === 'estimate') {
            if (!propAge) { alert('Please choose when the property was built so we can estimate the rating.'); return; }
            currentScore = estimateScore(propAge, propType, wall, loft, glazing, heating, solar, lighting);
            currentBand = bandOf(currentScore); estimated = true;
        } else {
            currentScore = BANDS[currentBand];
        }
        const estimateNote = estimated ? '<div class="result-full" style="background: var(--color-accent-bg); border: 1px solid var(--color-accent-border); margin-bottom: 16px;"><div style="font-weight: 600;">Estimated current rating: Band ' + currentBand + ', about ' + currentScore + ' points</div><div style="font-size: 0.88rem; color: var(--color-text-secondary); margin-top: 4px;">Likely range ' + Math.max(1, currentScore - 6) + ' to ' + Math.min(100, currentScore + 6) + ' (Band ' + bandOf(Math.max(1, currentScore - 6)) + ' to ' + bandOf(Math.min(100, currentScore + 6)) + '). This is an estimate from the age, insulation and heating you entered, not an EPC. Most homes already have one: <a href="https://www.gov.uk/find-energy-certificate" target="_blank" rel="noopener">check the register</a>. <a href="/guides/how-epc-points-are-calculated/">How the points work</a>.</div></div>' : '';""")
rep("""        if (pointsNeeded <= 0) {
            document.getElementById('resultsContent').innerHTML = '<div class="result-full\"""",
"""        if (pointsNeeded <= 0) {
            document.getElementById('resultsContent').innerHTML = estimateNote + '<div class="result-full\"""")
rep("""        // Summary
        html += '<div class="result-grid">';
        html += '<div class="result-item"><div class="label">Current rating</div><div class="value">Band ' + currentBand + '</div><div class="detail">~' + currentScore + ' points</div></div>';""",
"""        // Summary
        html += estimateNote;
        html += '<div class="result-grid">';
        html += '<div class="result-item"><div class="label">' + (estimated ? 'Estimated current rating' : 'Current rating') + '</div><div class="value">Band ' + currentBand + '</div><div class="detail">~' + currentScore + ' points</div></div>';""")
sec='''<section class="intro-band" id="how-estimate">
<h2>How the EPC estimate works</h2>
<p>An EPC score runs from 1 to 100 and is calculated from the modelled cost of heating, hot water and lighting per square metre. Our estimate starts from the average score for homes of your property's age in the English Housing Survey, where the mean across England was 67 in 2023 and 86% of homes built after 1990 sit in bands A to C against 23% of homes built before 1919. It then adds or subtracts points for your walls, loft, glazing, heating, solar panels and lighting using the same point ranges as the improvement table below. Expect it to land within about 6 points of an assessor's figure. It is not an EPC: a certificate needs a domestic energy assessor, costs about £60 to £120 and lasts ten years. Read <a href="/guides/how-epc-points-are-calculated/">how EPC points are calculated</a> or see <a href="/guides/energy-bills-by-epc-rating/">what each band pays in bills</a>.</p>
</section>
'''
rep('<h2>How to improve your EPC rating in 2026</h2>', sec+'<h2>How to improve your EPC rating in 2026</h2>')
faq_h2=s.index('<h2>Frequently asked questions</h2>'); first_h3=s.index('<h3>', faq_h2); end_first=s.index('</p>', first_h3)+4
new_faq='\n<h3>How accurate is the EPC estimate?</h3>\n<p>Usually within 6 points of an assessor\'s figure, which is enough to tell you the band you are likely in and how far you are from the next one. The estimate uses the average score for homes of your age from the English Housing Survey and adjusts it for your insulation, heating and glazing. Only a domestic energy assessor can issue an EPC.</p>'
s=s[:end_first]+new_faq+s[end_first:]
blocks=list(re.finditer(r'<script type="application/ld\+json">(.*?)</script>', s, re.S))
fb=[b for b in blocks if 'FAQPage' in b.group(1)]; assert len(fb)==1
j=json.loads(fb[0].group(1)); j['mainEntity'].insert(1, {"@type":"Question","name":"How accurate is the EPC estimate?","acceptedAnswer":{"@type":"Answer","text":"Usually within 6 points of an assessor's figure, which is enough to tell you the band you are likely in and how far you are from the next one. The estimate uses the average score for homes of your age from the English Housing Survey and adjusts it for your insulation, heating and glazing. Only a domestic energy assessor can issue an EPC."}})
s=s[:fb[0].start()]+'<script type="application/ld+json">'+json.dumps(j,ensure_ascii=False)+'</script>'+s[fb[0].end():]
s=re.sub(r'("@type":"WebApplication","name":"[^"]*","description":")[^"]*(")', r'\1Estimate your EPC rating from your home\'s age, insulation and heating, then see every improvement ranked by cost per point, with 2026 costs and grants.\2', s)
assert '—' not in s
open(p,'w',encoding='utf-8').write(s); print('estimator written')
