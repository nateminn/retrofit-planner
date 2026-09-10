#!/usr/bin/env python3
"""Generate inline SVG charts from a page's own data tables and insert them above the table.
Usage: python3 docs/superpowers/tools/charts.py --dry   (parse and describe only)
       python3 docs/superpowers/tools/charts.py          (insert figures, add js include)
Idempotent: a page that already contains a figure with the same id is skipped."""
import re, html, sys, math

C1, C2, C3 = 'var(--chart-1)', 'var(--chart-2)', 'var(--chart-3)'
W = 720

def text(s):
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s))).strip()

def parse_tables(page):
    out = []
    for m in re.finditer(r'<table class="data-table">(.*?)</table>', page, re.S):
        rows = []
        for tr in re.findall(r'<tr>(.*?)</tr>', m.group(1), re.S):
            rows.append([text(c) for c in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', tr, re.S)])
        out.append({'start': m.start(), 'rows': rows})
    return out

NUM = re.compile(r'-?£?\s?([\d,]+(?:\.\d+)?)')
def num(cell):
    """Return (low, high) in plain numbers, or None. Handles '£1,594', '£469 to £552', '10.5p', '9.7 years', '-£40 (about level)'."""
    c = cell.replace(' ', ' ')
    if c.lower().startswith(('n/a', 'baseline', 'free', 'immediate')):
        return None
    neg = c.strip().startswith('-')
    parts = re.split(r'\s+to\s+', c)
    vals = []
    for p in parts[:2]:
        mm = NUM.search(p)
        if not mm:
            return None
        v = float(mm.group(1).replace(',', ''))
        vals.append(-v if neg else v)
    if len(vals) == 1:
        vals = [vals[0], vals[0]]
    return tuple(vals)

def fmt(v, unit):
    if unit == '£':
        return '£' + format(int(round(v)), ',')
    if unit == 'p':
        return ('%.1f' % v).rstrip('0').rstrip('.') + 'p'
    if unit == 'yr':
        return ('%.1f' % v).rstrip('0').rstrip('.') + ' years'
    return format(int(round(v)), ',')

def nice_ticks(vmax, n=4):
    if vmax <= 0:
        return [0, 1]
    raw = vmax / n
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        step = m * mag
        if vmax / step <= n + 0.5:
            break
    top = step * math.ceil(vmax / step)
    return [step * i for i in range(int(top / step) + 1)]

def rrect_top(x, y, w, h, r=4):
    """Column with rounded top corners, square baseline."""
    if h <= r:
        return '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="2"/>' % (x, y, w, h)
    return ('<path d="M%.1f,%.1f v%.1f a%d,%d 0 0 1 %d,-%d h%.1f a%d,%d 0 0 1 %d,%d v%.1f z"/>'
            % (x, y + h, -(h - r), r, r, r, r, w - 2 * r, r, r, r, r, h - r))

def rrect_right(x, y, w, h, r=4):
    """Horizontal bar with rounded right end, square left end."""
    if w <= r:
        return '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="2"/>' % (x, y, w, h)
    return ('<path d="M%.1f,%.1f h%.1f a%d,%d 0 0 1 %d,%d v%.1f a%d,%d 0 0 1 %d,%d h%.1f z"/>'
            % (x, y, w - r, r, r, r, r, h - 2 * r, r, r, -r, r, -(w - r)))

def esc(s):
    return html.escape(s, quote=True)

def legend(series, colors):
    return '<div class="chart-legend">' + ''.join('<span><i style="background:%s"></i>%s</span>' % (c, esc(n)) for n, c in zip(series, colors)) + '</div>'

def figure(fid, title, caption, svg, series=None, colors=None):
    head = '<div class="chart-head"><div class="chart-title">%s</div>%s</div>' % (esc(title), legend(series, colors) if series and len(series) > 1 else '')
    return '<figure class="chart-fig" id="%s">%s<div class="chart-scroll">%s</div><figcaption>%s</figcaption></figure>\n' % (fid, head, svg, esc(caption))

# ---------- forms ----------
def grouped_columns(cats, series, unit, title, label_series=None):
    """series: list of (name, [ (lo,hi) or None ... ])"""
    n = len(cats); k = len(series)
    colors = [C1, C2, C3][:k]
    L, R, T, B = 52, 12, 14, 44
    plot_w = W - L - R
    vmax = max(v[1] for _, vals in series for v in vals if v) * 1.08
    ticks = nice_ticks(vmax)
    top = ticks[-1]
    plot_h = 220
    H = T + plot_h + B
    slot = plot_w / n
    bw = min(24, (slot * 0.7) / k - 2)
    group_w = k * bw + (k - 1) * 2
    def y(v): return T + plot_h * (1 - v / top)
    parts = ['<svg class="chart-svg" viewBox="0 0 %d %d" role="img" aria-label="%s">' % (W, H, esc(title))]
    for t in ticks:
        parts.append('<line class="grid" x1="%d" x2="%d" y1="%.1f" y2="%.1f"/>' % (L, W - R, y(t), y(t)))
        parts.append('<text class="tick" x="%d" y="%.1f" text-anchor="end" dominant-baseline="middle">%s</text>' % (L - 6, y(t), esc(fmt(t, unit) if unit != '£' else '£' + format(int(t), ','))))
    parts.append('<line class="axis" x1="%d" x2="%d" y1="%.1f" y2="%.1f"/>' % (L, W - R, y(0), y(0)))
    for i, cat in enumerate(cats):
        cx = L + slot * i + slot / 2
        parts.append(wrap_label(cat, cx, H - B + 16, slot - 6))
        x0 = cx - group_w / 2
        for j, (name, vals) in enumerate(series):
            v = vals[i]
            if not v:
                continue
            lo, hi = v
            x = x0 + j * (bw + 2)
            if lo != hi:
                ytop, ybot = y(hi), y(lo)
                shape = '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="4"/>' % (x, ytop, bw, ybot - ytop)
                val = '%s to %s' % (fmt(lo, unit), fmt(hi, unit))
            else:
                ytop = y(hi)
                shape = rrect_top(x, ytop, bw, y(0) - ytop)
                val = fmt(hi, unit)
            parts.append('<g class="bar" tabindex="0" fill="%s" data-val="%s" data-tip="%s">%s<rect class="hit" x="%.1f" y="%d" width="%.1f" height="%d"/></g>'
                         % (colors[j], esc(val), esc('%s, %s' % (cat, name)), shape, x - 3, T, bw + 6, plot_h))
            if label_series is not None and j == label_series and lo == hi:
                parts.append('<text class="val" x="%.1f" y="%.1f" text-anchor="middle">%s</text>' % (x + bw / 2, ytop - 5, esc(fmt(hi, unit))))
    parts.append('</svg>')
    return ''.join(parts), [s[0] for s in series], colors

def wrap_label(label, cx, y, maxw):
    words = label.split(); lines = []; cur = ''
    for w in words:
        if len(cur + ' ' + w) * 6.2 > maxw and cur:
            lines.append(cur); cur = w
        else:
            cur = (cur + ' ' + w).strip()
    lines.append(cur)
    lines = lines[:3]
    return '<text class="cat" text-anchor="middle">' + ''.join('<tspan x="%.1f" y="%.1f">%s</tspan>' % (cx, y + 13 * i, esc(l)) for i, l in enumerate(lines)) + '</text>'

def stacked_columns(cats, series, unit, title):
    n = len(cats); k = len(series)
    colors = [C1, C2, C3][:k]
    L, R, T, B = 52, 12, 22, 44
    plot_w = W - L - R
    totals = [sum(series[j][1][i][1] for j in range(k) if series[j][1][i]) for i in range(n)]
    ticks = nice_ticks(max(totals) * 1.08); top = ticks[-1]
    plot_h = 220; H = T + plot_h + B
    slot = plot_w / n; bw = min(28, slot * 0.6)
    def y(v): return T + plot_h * (1 - v / top)
    parts = ['<svg class="chart-svg" viewBox="0 0 %d %d" role="img" aria-label="%s">' % (W, H, esc(title))]
    for t in ticks:
        parts.append('<line class="grid" x1="%d" x2="%d" y1="%.1f" y2="%.1f"/><text class="tick" x="%d" y="%.1f" text-anchor="end" dominant-baseline="middle">%s</text>' % (L, W - R, y(t), y(t), L - 6, y(t), esc('£' + format(int(t), ','))))
    parts.append('<line class="axis" x1="%d" x2="%d" y1="%.1f" y2="%.1f"/>' % (L, W - R, y(0), y(0)))
    for i, cat in enumerate(cats):
        cx = L + slot * i + slot / 2; x = cx - bw / 2
        parts.append(wrap_label(cat, cx, H - B + 16, slot - 6))
        base = 0
        for j, (name, vals) in enumerate(series):
            v = vals[i]
            if not v:
                continue
            h = v[1]
            ytop, ybot = y(base + h), y(base)
            gap = 2 if j < k - 1 else 0
            shape = rrect_top(x, ytop, bw, ybot - ytop - gap) if j == k - 1 else '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>' % (x, ytop, bw, max(0, ybot - ytop - gap))
            parts.append('<g class="bar" tabindex="0" fill="%s" data-val="%s" data-tip="%s">%s<rect class="hit" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/></g>'
                         % (colors[j], esc(fmt(h, unit)), esc('%s, %s' % (cat, name)), shape, x - 3, ytop, bw + 6, ybot - ytop))
            base += h
        parts.append('<text class="val" x="%.1f" y="%.1f" text-anchor="middle">%s</text>' % (cx, y(base) - 5, esc(fmt(base, unit))))
    parts.append('</svg>')
    return ''.join(parts), [s[0] for s in series], colors

def hbars(cats, vals, unit, title, color=C2, highlight=None, label_all=False):
    """Single series horizontal bars; vals are (lo,hi); ranges drawn as floating bars."""
    n = len(cats)
    L, R, T, B = 190, 70, 10, 30
    plot_w = W - L - R
    vmax = max(v[1] for v in vals if v) * 1.05
    ticks = nice_ticks(vmax); top = ticks[-1]
    def wrap2(label, limit=27):
        if len(label) <= limit:
            return [label]
        words = label.split(); lines = []; cur = ''
        for w in words:
            if len(cur + ' ' + w) > limit and cur:
                lines.append(cur); cur = w
            else:
                cur = (cur + ' ' + w).strip()
        lines.append(cur)
        if len(lines) > 2:
            lines = [lines[0], ' '.join(lines[1:])]
            if len(lines[1]) > limit + 4:
                lines[1] = lines[1][:limit + 3] + '…'
        return lines
    wrapped = [wrap2(c) for c in cats]
    row_h = 34 if any(len(w) > 1 for w in wrapped) else 30
    plot_h = row_h * n; H = T + plot_h + B
    def x(v): return L + plot_w * v / top
    parts = ['<svg class="chart-svg" viewBox="0 0 %d %d" role="img" aria-label="%s">' % (W, H, esc(title))]
    for t in ticks:
        parts.append('<line class="grid" x1="%.1f" x2="%.1f" y1="%d" y2="%d"/><text class="tick" x="%.1f" y="%d" text-anchor="middle">%s</text>' % (x(t), x(t), T, T + plot_h, x(t), H - 8, esc(fmt(t, unit) if unit != '£' else '£' + format(int(t), ','))))
    parts.append('<line class="axis" x1="%d" x2="%d" y1="%d" y2="%d"/>' % (L, L, T, T + plot_h))
    extremes = set()
    if not label_all:
        vs = [(v[1], i) for i, v in enumerate(vals) if v]
        extremes = {max(vs)[1], min(vs)[1]}
        if highlight is not None:
            extremes.add(highlight)
    for i, (cat, v) in enumerate(zip(cats, vals)):
        cy = T + row_h * i + row_h / 2
        lines = wrapped[i]
        if len(lines) == 1:
            parts.append('<text class="cat" x="%d" y="%.1f" text-anchor="end" dominant-baseline="middle">%s</text>' % (L - 8, cy, esc(lines[0])))
        else:
            parts.append('<text class="cat" text-anchor="end"><tspan x="%d" y="%.1f">%s</tspan><tspan x="%d" y="%.1f">%s</tspan></text>' % (L - 8, cy - 2, esc(lines[0]), L - 8, cy + 11, esc(lines[1])))
        if not v:
            continue
        lo, hi = v; bh = 18; by = cy - bh / 2
        col = C3 if highlight == i else color
        if lo != hi:
            shape = '<rect x="%.1f" y="%.1f" width="%.1f" height="%d" rx="4"/>' % (x(lo), by, x(hi) - x(lo), bh)
            val = '%s to %s' % (fmt(lo, unit), fmt(hi, unit))
        else:
            shape = rrect_right(L, by, x(hi) - L, bh)
            val = fmt(hi, unit)
        parts.append('<g class="bar" tabindex="0" fill="%s" data-val="%s" data-tip="%s">%s<rect class="hit" x="%d" y="%.1f" width="%.1f" height="%d"/></g>' % (col, esc(val), esc(cat), shape, L, by - 4, plot_w, bh + 8))
        if label_all or i in extremes:
            tw = len(val) * 6.6
            if x(hi) + 6 + tw <= W - 4:
                parts.append('<text class="val" x="%.1f" y="%.1f" dominant-baseline="middle">%s</text>' % (x(hi) + 6, cy, esc(val)))
            elif lo != hi and x(lo) - 6 - tw >= L + 2:
                parts.append('<text class="val" x="%.1f" y="%.1f" text-anchor="end" dominant-baseline="middle">%s</text>' % (x(lo) - 6, cy, esc(val)))
            else:
                parts.append('<text class="val val-in" x="%.1f" y="%.1f" text-anchor="end" dominant-baseline="middle">%s</text>' % (x(hi) - 6, cy, esc(val)))
    parts.append('</svg>')
    return ''.join(parts), None, [color]

# ---------- specs ----------
SPECS = [
 dict(page='guides/energy-bills-by-epc-rating/index.html', table=0, fid='chart-bills-by-band', form='stacked', cat=0, cols=[(4, 'Gas'), (5, 'Electricity')], unit='£', drop=['All homes'],
      title='Typical annual energy bill by EPC band', caption='Median metered consumption per band (DESNZ NEED 2026, 2024 data) priced at the Ofgem cap for October to December 2026, including standing charges. Gas in blue, electricity in green.'),
 dict(page='guides/energy-bills-by-epc-rating/index.html', table=1, fid='chart-modelled-vs-actual', form='grouped', cat=0, cols=[(1, 'Modelled cost (EPC method)'), (2, 'Actual metered bill')], unit='£', label=1,
      title='What the certificate says versus what homes actually pay', caption='Modelled required fuel cost by band from the 2026 fuel poverty statistics against the median metered bill at October 2026 prices. The gap widens as the band gets worse.'),
 dict(page='guides/heat-pump-running-costs/index.html', table=0, fid='chart-running-costs-by-property', form='grouped', cat=0, cols=[(2, 'Gas boiler'), (3, 'Heat pump, standard tariff'), (4, 'Heat pump, heat pump tariff')], unit='£', label=2,
      title='Annual heating cost by property type', caption='Gas boiler at 90% efficiency and a heat pump with COP 2.9 at the Ofgem cap for October to December 2026. The heat pump tariff bar shows the 17p to 20p effective-rate range.'),
 dict(page='guides/heat-pump-running-costs/index.html', table=1, fid='chart-cost-per-kwh-by-cop', form='grouped', cat=0, cols=[(1, 'Standard tariff'), (2, 'Heat pump tariff')], unit='p', label=1,
      title='Cost per kWh of heat at each efficiency level', caption='Pence per kWh of delivered heat at 26.32p/kWh on a standard tariff and 18p/kWh on a heat pump tariff. Gas at 90% boiler efficiency costs 8.9p per kWh for comparison.'),
 dict(page='guides/heat-pump-running-costs/index.html', table=2, fid='chart-cost-per-kwh-by-fuel', form='hbars', cat=0, cols=[(2, 'Cost per kWh of heat')], unit='p', highlight_last=True,
      title='Cost per kWh of heat by fuel', caption='Fuel price divided by system efficiency. Heat pump rows use COP 2.9; oil and LPG boilers 85%, gas 90%. October to December 2026 prices, oil at September 2026 market rate.'),
 dict(page='guides/heat-pump-vs-new-boiler/index.html', table=0, fid='chart-15-year-total', form='row_hbars', row='15-year total cost', cats=['New gas boiler', 'Heat pump, standard tariff', 'Heat pump, heat pump tariff'], cols=[1, 2, 3], unit='£', highlight=2,
      title='15-year total cost of ownership, 3-bed semi', caption='Upfront cost after the £7,500 grant, radiator and cylinder work, running costs and maintenance over 15 years. Ranges reflect the spread of installation and radiator costs.'),
 dict(page='guides/heat-pump-vs-new-boiler/index.html', table=1, fid='chart-running-cost-comparison', form='grouped', cat=0, cols=[(1, 'Gas boiler'), (2, 'Heat pump, standard tariff'), (3, 'Heat pump, heat pump tariff')], unit='£', label=2,
      title='Annual heating cost by property type', caption='Ofgem cap for October to December 2026, gas at 90% boiler efficiency, heat pump COP 2.9 on a standard tariff or an 18p effective heat pump tariff.'),
 dict(page='guides/electric-boiler-vs-heat-pump/index.html', table=0, fid='chart-electric-vs-heat-pump', form='grouped', cat=0, cols=[(1, 'Electric boiler'), (2, 'Heat pump, standard tariff'), (3, 'Heat pump, heat pump tariff')], unit='£', label=2,
      title='Annual heating cost: electric boiler versus heat pump', caption='Electric boiler at 100% efficiency and a heat pump with COP 2.9, both at 26.32p/kWh, or 18p/kWh on a heat pump tariff. Heat demand from 8,000 kWh (2-bed terrace) to 18,000 kWh (4-bed detached).'),
 dict(page='guides/storage-heaters-vs-heat-pump/index.html', table=0, fid='chart-storage-vs-heat-pump', form='grouped', cat=0, cols=[(1, 'Storage heaters'), (2, 'Heat pump, standard tariff'), (3, 'Heat pump, heat pump tariff')], unit='£', label=2,
      title='Annual heating cost: storage heaters versus heat pump', caption='Storage heaters on Economy 7 with daytime top-up; heat pump COP 2.9 at the Ofgem cap for October to December 2026, standard or heat pump tariff.'),
 dict(page='guides/heat-pump-cost-by-house-type/index.html', table=0, fid='chart-installed-cost-by-type', form='hbars', cat=0, cols=[(2, 'Installed cost')], unit='£',
      title='Installed cost before the grant, by property type', caption='Air source heat pump including unit, labour, commissioning and MCS certificate. Deduct £7,500 (or £9,000 for oil and LPG homes) for the Boiler Upgrade Scheme grant.'),
 dict(page='guides/heat-pump-cost-by-house-type/index.html', table=5, fid='chart-running-cost-by-type', form='grouped', cat=0, cols=[(1, 'Gas boiler'), (2, 'Heat pump, standard tariff'), (3, 'Heat pump, heat pump tariff')], unit='£', label=2,
      title='Annual heating cost by house type', caption='Gas at 7.97p/kWh and 90% boiler efficiency; heat pump COP 2.9 at 26.32p/kWh or 18p/kWh effective on a heat pump tariff. Well-insulated properties.'),
 dict(page='guides/heat-pump-cost-4-bed-house/index.html', table=1, fid='chart-4bed-breakdown', form='hbars', cat=0, cols=[(1, 'Range')], unit='£', drop=['BUS grant', 'Net heat pump cost'], highlight_label='Total out of pocket',
      title='Where the money goes on a 4-bed installation', caption='Cost ranges for each element after the £7,500 Boiler Upgrade Scheme grant is deducted from the heat pump line. The total is what a typical 4-bed pays out of pocket.'),
 dict(page='guides/heat-pump-cost-4-bed-house/index.html', table=5, fid='chart-4bed-running', form='hbars', cat=0, cols=[(1, 'Annual cost')], unit='£', highlight_label='Heat pump (heat pump tariff)',
      title='Annual heating cost, 4-bed detached, 18,000 kWh', caption='Ofgem cap for October to December 2026. The heat pump on a heat pump tariff is the gold bar; oil and LPG use September 2026 market prices.'),
 dict(page='guides/heat-pump-cost-3-bed-semi/index.html', table=1, fid='chart-3bed-breakdown', form='hbars', cat=0, cols=[(1, 'Range')], unit='£', drop=['BUS grant', 'Net heat pump cost'], highlight_label='Total out of pocket',
      title='Where the money goes on a 3-bed semi installation', caption='Cost ranges for each element after the £7,500 grant is deducted from the heat pump line. Many 1950s to 1980s semis need fewer radiator changes and land near the bottom of the total.'),
 dict(page='guides/heat-pump-cost-3-bed-semi/index.html', table=4, fid='chart-3bed-running', form='hbars', cat=0, cols=[(1, 'Annual cost')], unit='£', highlight_label='Heat pump (heat pump tariff)',
      title='Annual heating cost, 3-bed semi, 12,000 kWh', caption='Ofgem cap for October to December 2026. The heat pump on a heat pump tariff is the gold bar; oil and LPG use September 2026 market prices.'),
 dict(page='guides/average-energy-bills-uk/index.html', table=0, fid='chart-bills-by-property', form='stacked', cat=0, cols=[(1, 'Gas'), (2, 'Electricity')], unit='£',
      title='Annual energy bill by property type', caption='Gas and electricity at the Ofgem cap for October to December 2026, including standing charges. Consumption by property type from Energy Saving Trust and Ofgem data.'),
 dict(page='guides/energy-bills-by-household-size/index.html', table=0, fid='chart-bills-by-occupants', form='stacked', cat=0, cols=[(1, 'Gas'), (2, 'Electricity')], unit='£',
      title='Annual energy bill by number of occupants', caption='Dual fuel, direct debit, at the Ofgem cap for October to December 2026. Heating costs are largely fixed by the property, so the per-person cost falls as households grow.'),
 dict(page='guides/solar-panel-payback-uk/index.html', table=0, fid='chart-solar-payback', form='hbars', cat=0, cols=[(3, 'Payback')], unit='yr',
      title='Solar payback period by scenario', caption='System cost divided by annual benefit (bill savings plus export income) at 26.32p/kWh electricity and 8p/kWh export. Larger systems and southern roofs pay back fastest.'),
 dict(page='guides/are-solar-panels-worth-it-uk/index.html', table=1, fid='chart-solar-benefit', form='stacked', cat=0, cols=[(2, 'Bill saving'), (3, 'Export income')], unit='£',
      title='Annual benefit from solar panels by system', caption='Bill savings from self-used electricity at 26.32p/kWh plus Smart Export Guarantee income at 8p/kWh. A battery lifts self-use from 45% to 80%.'),
 dict(page='guides/best-heat-pump-tariffs/index.html', table=1, fid='chart-tariff-costs', form='hbars', cat=0, cols=[(1, 'Annual heating cost')], unit='£', highlight_label='Standard variable (26.32p flat)',
      title='Annual heating cost by tariff, 3-bed semi', caption='12,000 kWh heat demand, COP 2.9, 60% of heating shifted to off-peak windows where the tariff has them. The standard variable rate is the gold bar for comparison.'),
 dict(page='guides/boiler-upgrade-scheme-guide/index.html', table=2, fid='chart-bus-running', form='hbars', cat=0, cols=[(1, 'Annual cost')], unit='£', highlight_label='Heat pump (heat pump tariff, ~18p/kWh)',
      title='Annual heating cost after switching, 3-bed semi', caption='15,000 kWh heat demand at the Ofgem cap for October to December 2026.'),
 dict(page='guides/heat-pump-old-house/index.html', table=2, fid='chart-old-house-running', form='hbars', cat=0, cols=[(1, 'Annual heating cost')], unit='£', highlight_label='Heat pump (COP 2.9, heat pump tariff)',
      title='Annual heating cost in an insulated old house, 15,000 kWh', caption='Ofgem cap for October to December 2026. The heat pump tariff bar shows the 17p to 20p effective-rate range.'),
 dict(page='guides/solar-battery-storage-uk/index.html', table=0, fid='chart-battery-savings', form='hbars', cat=0, cols=[(3, 'Annual saving')], unit='£',
      title='Annual saving by battery size, with a 4 kW solar system', caption='Stored solar used in the evening instead of bought at 26.32p/kWh. Time-of-use tariffs add £100 to £200 a year on top.'),
 dict(page='guides/heat-pump-flat/index.html', table=0, fid='chart-flat-costs', form='hbars', cat=0, cols=[(2, 'Install cost')], unit='£',
      title='Installed cost by flat type, before the grant', caption='Small 4 to 8 kW systems. After the £7,500 grant most flats pay £0 to £2,500 for the heat pump itself.'),
]

def build(spec, page):
    tables = parse_tables(page)
    t = tables[spec['table']]
    rows = [r for r in t['rows'][1:] if r]
    if spec['form'] == 'row_hbars':
        row = next(r for r in rows if r[0].startswith(spec['row']))
        vals = [num(row[c]) for c in spec['cols']]
        svg, series, colors = hbars(spec['cats'], vals, spec['unit'], spec['title'], highlight=spec.get('highlight'), label_all=True)
        return svg, series, colors, list(zip(spec['cats'], vals))
    drop = set(spec.get('drop', []))
    rows = [r for r in rows if r[spec['cat']] not in drop and not r[spec['cat']].startswith('Total') or r[spec['cat']].startswith('Total out')]
    cats = [r[spec['cat']] for r in rows]
    series = [(name, [num(r[c]) if c < len(r) else None for r in rows]) for c, name in spec['cols']]
    if spec['form'] == 'grouped':
        svg, s, colors = grouped_columns(cats, series, spec['unit'], spec['title'], label_series=spec.get('label'))
    elif spec['form'] == 'stacked':
        svg, s, colors = stacked_columns(cats, series, spec['unit'], spec['title'])
    elif spec['form'] == 'hbars':
        vals = series[0][1]
        hl = None
        if spec.get('highlight_label'):
            hl = next((i for i, c in enumerate(cats) if c.startswith(spec['highlight_label'])), None)
        if spec.get('highlight_last'):
            hl = len(cats) - 1
        svg, s, colors = hbars(cats, vals, spec['unit'], spec['title'], highlight=hl)
    return svg, s, colors, list(zip(cats, [[v for _, vs in series for v in [vs[i]]] for i in range(len(cats))]))

def insert(page, spec, fig):
    tables = list(re.finditer(r'<table class="data-table">', page))
    pos = tables[spec['table']].start()
    wrap = page.rfind('<div class="tblwrap">', 0, pos)
    if wrap != -1 and page[wrap:pos].strip() == '<div class="tblwrap">':
        pos = wrap
    return page[:pos] + fig + page[pos:]

if __name__ == '__main__':
    dry = '--dry' in sys.argv; replace = '--replace' in sys.argv
    touched = set()
    for spec in SPECS:
        page = open(spec['page'], encoding='utf-8').read()
        if replace and not dry:
            page, k = re.subn(r'<figure class="chart-fig" id="%s">.*?</figure>\n' % spec['fid'], '', page, flags=re.S)
            assert k <= 1, (spec['fid'], k)
        svg, series, colors, data = build(spec, page)
        if dry:
            print('%-52s %-28s %s' % (spec['page'].replace('guides/', '').replace('/index.html', ''), spec['fid'], data[:4]))
            continue
        if 'id="%s"' % spec['fid'] in page:
            print('skip (exists)', spec['fid']); continue
        fig = figure(spec['fid'], spec['title'], spec['caption'], svg, series, colors)
        page = insert(page, spec, fig)
        if '/js/charts.js' not in page:
            page = page.replace('</body>', '<script src="/js/charts.js" defer></script>\n</body>')
        open(spec['page'], 'w', encoding='utf-8').write(page)
        touched.add(spec['page']); print('inserted', spec['fid'])
    if not dry:
        print('pages touched:', len(touched))
