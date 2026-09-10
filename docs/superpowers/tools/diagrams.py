#!/usr/bin/env python3
"""Insert explanatory inline-SVG diagrams into guide and calculator pages. Idempotent by figure id."""
import re, sys, html

INK = 'var(--color-text)'; INK2 = 'var(--color-text-secondary)'; LINE = '#6B6960'
C1 = 'var(--chart-1)'; C2 = 'var(--chart-2)'; C3 = 'var(--chart-3)'; SURF = 'var(--color-surface)'; ALT = 'var(--color-surface-alt)'
T = 'font-size="12" fill="%s"' % INK2
TB = 'font-size="12" font-weight="700" fill="%s"' % INK

def arrow(x1, y1, x2, y2, color=LINE, w=2):
    import math
    a = math.atan2(y2 - y1, x2 - x1); L = 8
    p1 = (x2 - L * math.cos(a - 0.45), y2 - L * math.sin(a - 0.45)); p2 = (x2 - L * math.cos(a + 0.45), y2 - L * math.sin(a + 0.45))
    return ('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%d" stroke-linecap="round"/>'
            '<polyline points="%.1f,%.1f %.1f,%.1f %.1f,%.1f" fill="none" stroke="%s" stroke-width="%d" stroke-linecap="round" stroke-linejoin="round"/>'
            % (x1, y1, x2, y2, color, w, p1[0], p1[1], x2, y2, p2[0], p2[1], color, w))

def fig(fid, label, svg, caption):
    return '<figure class="diagram-fig" id="%s"><div class="chart-scroll"><svg viewBox="0 0 720 %d" role="img" aria-label="%s" xmlns="http://www.w3.org/2000/svg">%s</svg></div><figcaption>%s</figcaption></figure>\n' % (fid, svg[0], html.escape(label, quote=True), svg[1], html.escape(caption, quote=True))

def d_heat_pump():
    s = []
    # outdoor unit
    s.append('<rect x="34" y="84" width="112" height="124" rx="10" fill="%s" stroke="%s" stroke-width="2"/>' % (ALT, LINE))
    s.append('<circle cx="90" cy="146" r="34" fill="none" stroke="%s" stroke-width="2"/>' % LINE)
    for ang in (0, 60, 120):
        s.append('<line x1="90" y1="146" x2="90" y2="116" stroke="%s" stroke-width="2" stroke-linecap="round" transform="rotate(%d 90 146)"/>' % (LINE, ang))
        s.append('<line x1="90" y1="146" x2="90" y2="176" stroke="%s" stroke-width="2" stroke-linecap="round" transform="rotate(%d 90 146)"/>' % (LINE, ang))
    for y in (118, 146, 174):
        s.append(arrow(2, y, 26, y, C1))
    s.append('<text x="90" y="232" text-anchor="middle" %s>Outdoor unit</text>' % TB)
    s.append('<text x="90" y="248" text-anchor="middle" %s>takes heat from the air,</text>' % T)
    s.append('<text x="90" y="262" text-anchor="middle" %s>even at minus 5C</text>' % T)
    # pipes to house
    s.append(arrow(146, 130, 266, 130, C3, 3))
    s.append('<line x1="266" y1="162" x2="146" y2="162" stroke="%s" stroke-width="3" stroke-linecap="round"/>' % C1)
    s.append('<text x="206" y="120" text-anchor="middle" %s>40 to 50C flow</text>' % T)
    s.append('<text x="206" y="182" text-anchor="middle" %s>cooler return</text>' % T)
    # house
    s.append('<polygon points="262,110 416,28 570,110" fill="none" stroke="%s" stroke-width="2" stroke-linejoin="round"/>' % LINE)
    s.append('<rect x="266" y="110" width="300" height="122" fill="%s" stroke="%s" stroke-width="2"/>' % (SURF, LINE))
    # cylinder
    s.append('<rect x="290" y="126" width="46" height="92" rx="14" fill="%s" stroke="%s" stroke-width="2"/>' % (ALT, LINE))
    s.append('<text x="313" y="248" text-anchor="middle" %s>Hot water cylinder</text>' % TB)
    s.append('<text x="313" y="262" text-anchor="middle" %s>170 to 300 litres</text>' % T)
    # radiators
    for x in (386, 462):
        s.append('<rect x="%d" y="180" width="60" height="30" rx="4" fill="%s" stroke="%s" stroke-width="2"/>' % (x, ALT, LINE))
        for k in range(1, 6):
            s.append('<line x1="%d" y1="184" x2="%d" y2="206" stroke="%s" stroke-width="1.5"/>' % (x + k * 10, x + k * 10, LINE))
    s.append('<line x1="336" y1="150" x2="522" y2="150" stroke="%s" stroke-width="2"/>' % C3)
    s.append('<line x1="416" y1="150" x2="416" y2="180" stroke="%s" stroke-width="2"/><line x1="492" y1="150" x2="492" y2="180" stroke="%s" stroke-width="2"/>' % (C3, C3))
    s.append('<text x="454" y="248" text-anchor="middle" %s>Larger radiators</text>' % TB)
    s.append('<text x="454" y="262" text-anchor="middle" %s>or underfloor heating</text>' % T)
    # efficiency callout
    s.append('<rect x="590" y="96" width="122" height="96" rx="10" fill="%s" stroke="%s" stroke-width="1.5"/>' % ('var(--color-accent-bg)', 'var(--color-accent-border)'))
    s.append('<text x="651" y="124" text-anchor="middle" %s>1 kWh of</text>' % T)
    s.append('<text x="651" y="140" text-anchor="middle" %s>electricity in</text>' % T)
    s.append('<text x="651" y="163" text-anchor="middle" font-size="13" font-weight="700" fill="var(--color-accent)">2.5 to 3.5 kWh</text>')
    s.append('<text x="651" y="180" text-anchor="middle" %s>of heat out</text>' % T)
    return (272, ''.join(s))

def d_heat_loss():
    s = []
    s.append('<polygon points="236,150 360,52 484,150" fill="%s" stroke="%s" stroke-width="2" stroke-linejoin="round"/>' % (ALT, LINE))
    s.append('<rect x="252" y="150" width="216" height="132" fill="%s" stroke="%s" stroke-width="2"/>' % (SURF, LINE))
    s.append('<rect x="284" y="180" width="44" height="40" fill="%s" stroke="%s" stroke-width="2"/>' % (ALT, LINE))
    s.append('<rect x="392" y="180" width="44" height="40" fill="%s" stroke="%s" stroke-width="2"/>' % (ALT, LINE))
    s.append('<rect x="342" y="222" width="36" height="60" fill="%s" stroke="%s" stroke-width="2"/>' % (ALT, LINE))
    # roof arrows
    for x in (300, 360, 420):
        s.append(arrow(x, 96 + (abs(x - 360) // 3), x, 30 + (abs(x - 360) // 3), C1))
    s.append('<text x="360" y="18" text-anchor="middle" %s>Roof 26%%</text>' % TB)
    # wall arrows
    s.append(arrow(252, 200, 196, 200, C1)); s.append(arrow(252, 250, 196, 250, C1))
    s.append('<text x="186" y="196" text-anchor="end" %s>Walls 33%%</text>' % TB)
    s.append(arrow(468, 250, 524, 250, C1))
    s.append('<text x="534" y="254" text-anchor="start" %s>Walls 33%%</text>' % TB)
    # window arrows
    s.append(arrow(436, 200, 524, 200, C1))
    s.append('<text x="534" y="196" text-anchor="start" %s>Windows and doors 18%%</text>' % TB)
    # draughts
    s.append(arrow(378, 268, 524, 296, C1))
    s.append('<text x="534" y="300" text-anchor="start" %s>Draughts 15%%</text>' % TB)
    # floor
    s.append(arrow(300, 282, 300, 322, C1)); s.append(arrow(420, 282, 420, 322, C1))
    s.append('<text x="360" y="342" text-anchor="middle" %s>Floor 8%%</text>' % TB)
    return (352, ''.join(s))

def d_epc_bands():
    bands = [('A', '92 to 100', 9, '#008054', '#FFFFFF'), ('B', '81 to 91', 11, '#19B459', '#FFFFFF'), ('C', '69 to 80', 12, '#8DCE46', '#1A1A17'),
             ('D', '55 to 68', 14, '#FFD500', '#1A1A17'), ('E', '39 to 54', 16, '#FCAA65', '#1A1A17'), ('F', '21 to 38', 18, '#EF8023', '#1A1A17'), ('G', '1 to 20', 20, '#E9153B', '#FFFFFF')]
    s = []; x = 30; total = sum(b[2] for b in bands); scale = 660 / total; centres = {}; top = 88; bh = 56
    for letter, pts, w, col, ink in bands:
        bw = w * scale
        s.append('<rect x="%.1f" y="%d" width="%.1f" height="%d" rx="6" fill="%s"/>' % (x, top, bw - 3, bh, col))
        s.append('<text x="%.1f" y="%d" text-anchor="middle" font-size="20" font-weight="700" fill="%s">%s</text>' % (x + bw / 2 - 1.5, top + 25, ink, letter))
        s.append('<text x="%.1f" y="%d" text-anchor="middle" font-size="11" fill="%s">%s</text>' % (x + bw / 2 - 1.5, top + 45, ink, pts))
        centres[letter] = x + bw / 2 - 1.5; x += bw
    for letter, label, y in (('E', 'Rented homes today: minimum band E', 16), ('C', 'Rented homes from 2030: band C', 42)):
        cx = centres[letter]
        s.append(arrow(cx, y + 6, cx, top - 4, LINE))
        s.append('<text x="%.1f" y="%d" text-anchor="middle" %s>%s</text>' % (cx, y, TB, label))
    cx = centres['D']
    s.append(arrow(cx, top + bh + 36, cx, top + bh + 6, LINE))
    s.append('<text x="%.1f" y="%d" text-anchor="middle" %s>Most common band in England and Wales</text>' % (cx, top + bh + 54, TB))
    return (top + bh + 62, ''.join(s))

def d_sizing():
    homes = [('Flat', '4 to 6 kW', '£7,000 to £10,000', 62, 60), ('Terrace', '5 to 7 kW', '£8,000 to £11,000', 74, 82), ('Semi-detached', '8 to 10 kW', '£9,000 to £12,000', 92, 98), ('Detached', '10 to 14 kW', '£11,000 to £16,000', 114, 116)]
    s = []; slots = [110, 280, 450, 620]; base = 150
    for (name, kw, cost, w, h), cx in zip(homes, slots):
        s.append('<polygon points="%.1f,%d %.1f,%d %.1f,%d" fill="%s" stroke="%s" stroke-width="2" stroke-linejoin="round"/>' % (cx - w / 2 - 6, base - h * 0.55, cx, base - h - 6, cx + w / 2 + 6, base - h * 0.55, ALT, LINE))
        s.append('<rect x="%.1f" y="%.1f" width="%d" height="%.1f" fill="%s" stroke="%s" stroke-width="2"/>' % (cx - w / 2, base - h * 0.55, w, h * 0.55, SURF, LINE))
        s.append('<rect x="%.1f" y="%.1f" width="12" height="16" fill="%s" stroke="%s" stroke-width="1.5"/>' % (cx - 6, base - 16, ALT, LINE))
        s.append('<text x="%d" y="%d" text-anchor="middle" %s>%s</text>' % (cx, base + 22, TB, name))
        s.append('<text x="%d" y="%d" text-anchor="middle" font-size="13" font-weight="700" fill="var(--color-accent)">%s</text>' % (cx, base + 42, kw))
        s.append('<text x="%d" y="%d" text-anchor="middle" %s>%s</text>' % (cx, base + 60, T, cost))
    s.append('<line x1="30" y1="%d" x2="690" y2="%d" stroke="%s" stroke-width="1.5"/>' % (base, base, LINE))
    return (228, ''.join(s))

def d_solar():
    s = []
    s.append('<circle cx="80" cy="60" r="22" fill="%s" stroke="%s" stroke-width="2"/>' % ('var(--color-highlight-bg)', C3))
    for ang in range(0, 360, 45):
        s.append('<line x1="80" y1="30" x2="80" y2="20" stroke="%s" stroke-width="2" stroke-linecap="round" transform="rotate(%d 80 60)"/>' % (C3, ang))
    s.append('<polygon points="150,100 260,40 370,100" fill="none" stroke="%s" stroke-width="2" stroke-linejoin="round"/>' % LINE)
    for i in range(3):
        s.append('<polygon points="%d,%d %d,%d %d,%d %d,%d" fill="%s" stroke="%s" stroke-width="1.5"/>' % (176 + i * 40, 92 - i * 14, 208 + i * 40, 76 - i * 14, 222 + i * 40, 90 - i * 14, 190 + i * 40, 106 - i * 14, C1, SURF))
    s.append('<text x="260" y="124" text-anchor="middle" %s>4 kW system, about 3,800 kWh a year</text>' % T)
    def bar(y, label, self_pct):
        x0, w = 30, 660
        s.append('<text x="%d" y="%d" %s>%s</text>' % (x0, y - 8, TB, label))
        sw = w * self_pct / 100
        s.append('<rect x="%d" y="%d" width="%.1f" height="26" rx="4" fill="%s"/>' % (x0, y, sw - 2, C2))
        s.append('<rect x="%.1f" y="%d" width="%.1f" height="26" rx="4" fill="%s"/>' % (x0 + sw, y, w - sw, C1))
        s.append('<text x="%.1f" y="%d" text-anchor="middle" font-size="12" font-weight="700" fill="#FFFFFF">%d%% used at home</text>' % (x0 + sw / 2, y + 17, self_pct))
        s.append('<text x="%.1f" y="%d" text-anchor="middle" font-size="12" font-weight="700" fill="#FFFFFF">%d%% exported</text>' % (x0 + sw + (w - sw) / 2, y + 17, 100 - self_pct))
    bar(160, 'Without a battery', 45)
    bar(216, 'With a battery', 80)
    s.append('<text x="30" y="266" %s>Electricity used at home saves the full 26.32p per kWh.</text>' % T)
    s.append('<text x="30" y="284" %s>Exported electricity earns about 8p per kWh under the Smart Export Guarantee.</text>' % T)
    return (298, ''.join(s))

DIAGRAMS = {
 'heat-pump': dict(build=d_heat_pump, label='How an air source heat pump heats a home', caption='An air source heat pump moves heat from outdoor air into a refrigerant loop, delivers it to the house at 40 to 50C, stores hot water in a cylinder and feeds larger radiators or underfloor heating. Every unit of electricity produces 2.5 to 3.5 units of heat.'),
 'heat-loss': dict(build=d_heat_loss, label='Where an uninsulated house loses heat', caption='Typical shares of heat loss for an uninsulated house, based on Energy Saving Trust estimates. Walls and roof account for about six tenths, which is why loft and wall insulation come first.'),
 'epc-bands': dict(build=d_epc_bands, label='EPC bands A to G and their SAP points', caption='The seven EPC bands with the SAP points each covers. Band widths are proportional to the points they span, so the lower bands cover more ground.'),
 'sizing': dict(build=d_sizing, label='Heat pump size and installed cost by house type', caption='Typical air source heat pump size and installed cost before the grant for each house type. A room-by-room heat loss survey sets the exact size.'),
 'solar': dict(build=d_solar, label='Where solar electricity goes with and without a battery', caption='Without a battery a household uses about 45% of its solar generation and exports the rest. A battery lifts self-use to about 80%.'),
}

PLACEMENTS = [
 ('heat-pump', 'guides/heat-pump-running-costs/index.html', 'first-h2'),
 ('heat-pump', 'guides/heat-pump-cost-4-bed-house/index.html', '<h2 id="size">'),
 ('heat-pump', 'guides/heat-pump-cost-3-bed-semi/index.html', '<h2 id="size">'),
 ('heat-pump', 'heat-pump-calculator/index.html', 'first-h2'),
 ('sizing', 'guides/heat-pump-cost-by-house-type/index.html', 'first-h2'),
 ('sizing', 'guides/heat-pump-flat/index.html', 'first-h2'),
 ('heat-loss', 'guides/is-loft-insulation-worth-it/index.html', 'first-h2'),
 ('heat-loss', 'guides/is-cavity-wall-insulation-worth-it/index.html', 'first-h2'),
 ('heat-loss', 'guides/solid-wall-insulation-cost/index.html', 'first-h2'),
 ('heat-loss', 'guides/draught-proofing-guide/index.html', 'first-h2'),
 ('heat-loss', 'guides/how-to-improve-epc-rating/index.html', 'first-h2'),
 ('heat-loss', 'insulation-calculator/index.html', 'first-h2'),
 ('epc-bands', 'guides/energy-bills-by-epc-rating/index.html', '<h2 id="table">'),
 ('epc-bands', 'guides/how-epc-points-are-calculated/index.html', 'first-h2'),
 ('epc-bands', 'epc-calculator/index.html', 'first-h2'),
 ('epc-bands', 'guides/epc-rating-landlords/index.html', 'first-h2'),
 ('solar', 'guides/are-solar-panels-worth-it-uk/index.html', 'first-h2'),
 ('solar', 'guides/solar-panel-payback-uk/index.html', 'first-h2'),
 ('solar', 'solar-calculator/index.html', 'first-h2'),
]

if __name__ == '__main__':
    dry = '--dry' in sys.argv; replace = '--replace' in sys.argv
    touched = set()
    for key, path, anchor in PLACEMENTS:
        page = open(path, encoding='utf-8').read()
        fid = 'diagram-' + key
        if replace and not dry:
            page, n = re.subn(r'<figure class="diagram-fig" id="%s">.*?</figure>\n' % fid, '', page, flags=re.S)
            assert n <= 1, (path, n)
        if 'id="%s"' % fid in page:
            print('skip (exists)', path, key); continue
        d = DIAGRAMS[key]; h, body = d['build']()
        figure = fig(fid, d['label'], (h, body), d['caption'])
        if anchor == 'first-h2':
            start = page.find('<h1')
            pos = page.find('<h2', start)
        else:
            pos = page.find(anchor)
        assert pos > 0, (path, anchor)
        if dry:
            print('%-58s %-10s at char %d: %s' % (path, key, pos, page[pos:pos + 40].replace('\n', ' '))); continue
        page = page[:pos] + figure + page[pos:]
        open(path, 'w', encoding='utf-8').write(page); touched.add(path)
        print('inserted', key, 'in', path)
    print('pages touched:', len(touched))
