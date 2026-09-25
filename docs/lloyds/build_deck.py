#!/usr/bin/env python3
"""Build the Lloyds Launch pitch deck as a PDF.

Six landscape slides, the site's own palette, and Georgia for display because that is
the fallback the site's CSS declares behind Fraunces. Nothing here is decoration for
its own sake: every number on every slide is one that model_check.py, table_check.py or
a GSC export can be pointed at. Search figures: GSC export to 22 Sep 2026.

Run: python3 docs/lloyds/build_deck.py
"""
import pathlib
from reportlab.lib.pagesizes import landscape, A4  # noqa: F401  (kept for reference)
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

OUT = pathlib.Path(__file__).parent / 'retrofit-planner-lloyds-launch.pdf'
# 16:9, which is what a deck is. A4 landscape is 1.41:1 and leaves a band of dead
# space under every slide.
W, H = 960, 540

BG      = colors.HexColor('#FAFAF7')
SURFACE = colors.HexColor('#FFFFFF')
TEXT    = colors.HexColor('#2B2A26')
MUTED   = colors.HexColor('#6B6960')
ACCENT  = colors.HexColor('#2D6A4F')
ACCBG   = colors.HexColor('#EDF6F0')
BORDER  = colors.HexColor('#E2DFD6')

for name, path in [('Disp', '/System/Library/Fonts/Supplemental/Georgia.ttf'),
                   ('DispB', '/System/Library/Fonts/Supplemental/Georgia Bold.ttf')]:
    pdfmetrics.registerFont(TTFont(name, path))
BODY, BOLD = 'Helvetica', 'Helvetica-Bold'

M = 17 * mm


def slide(c, kicker=None):
    c.setFillColor(BG)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    if kicker:
        c.setFillColor(ACCENT)
        c.setFont(BODY, 9.5)
        c.drawString(M, H - M + 3 * mm, kicker.upper())


def wrap(c, text, x, y, width, font, size, leading, fill=TEXT):
    """Draw wrapped text, return the y below it."""
    c.setFont(font, size)
    c.setFillColor(fill)
    words, line = text.split(), ''
    for w in words:
        trial = (line + ' ' + w).strip()
        if c.stringWidth(trial, font, size) <= width:
            line = trial
        else:
            c.drawString(x, y, line)
            y -= leading
            line = w
    if line:
        c.drawString(x, y, line)
        y -= leading
    return y


def bullet(c, head, body, x, y, width):
    c.setFillColor(ACCENT)
    c.circle(x + 1.8 * mm, y + 1.5 * mm, 1.6 * mm, stroke=0, fill=1)
    c.setFont(BOLD, 13)
    c.setFillColor(TEXT)
    c.drawString(x + 6.5 * mm, y, head)
    return wrap(c, body, x + 6.5 * mm, y - 7.2 * mm, width - 6.5 * mm, BODY, 11.5, 6.2 * mm, MUTED) - 11 * mm


def stat(c, x, y, w, big, label):
    c.setFillColor(SURFACE)
    c.setStrokeColor(BORDER)
    c.roundRect(x, y, w, 31 * mm, 3 * mm, stroke=1, fill=1)
    c.setFont('DispB', 25)
    c.setFillColor(ACCENT)
    c.drawString(x + 7 * mm, y + 17 * mm, big)
    c.setFont(BODY, 8)
    c.setFillColor(MUTED)
    wrap(c, label, x + 7 * mm, y + 11 * mm, w - 13 * mm, BODY, 9, 4.2 * mm, MUTED)


c = canvas.Canvas(str(OUT), pagesize=(W, H))

# 1 ------------------------------------------------------------------ title
slide(c)
c.setFillColor(ACCENT)
c.rect(M, H - M - 2 * mm, 26 * mm, 1.4 * mm, stroke=0, fill=1)
c.setFont('DispB', 40)
c.setFillColor(TEXT)
c.drawString(M, H - M - 24 * mm, 'Retrofit Planner')
y = wrap(c, 'Retrofit cost, saving and payback for one specific house, from four simple '
            'questions about it.', M, H - M - 38 * mm, W - 2 * M - 60 * mm,
         'Disp', 15, 8 * mm, MUTED)
c.setFont(BODY, 9.5)
c.setFillColor(MUTED)
c.drawString(M, M + 14 * mm, 'Lloyds Launch 2026   |   Homes   |   RetrofitPlanner.co.uk')
c.drawString(M, M + 8 * mm, 'Built and run by one person. Plans to register in Q4 2026.')
c.showPage()

# 2 ------------------------------------------------------------------ problem
slide(c, 'the problem')
c.setFont('DispB', 31)
c.setFillColor(TEXT)
c.drawString(M, H - M - 16 * mm, 'The incentive is funded. The decision is not.')
y = H - M - 34 * mm
y = bullet(c, '£250 billion of home retrofit needed by 2050',
           'Cited by Lloyds. By value, 39% of its residential mortgages with a known EPC are '
           'band D, 17% E to G.', M, y, 118 * mm)
y = bullet(c, 'Over 3,000 green home reward claims in 2025',
           'Against over £320bn of mortgages. Up to £2,000 is available and almost nobody takes it.',
           M, y, 118 * mm)
y = bullet(c, 'EPCs do not measure what a house actually uses',
           'Lloyds 2025 sustainability report: EPCs capture neither actual energy use nor recent '
           'retrofit work, and a 2.0% gap to the financed emissions pathway is attributed to '
           'EPC data limits.', M, y, 118 * mm)
c.setFillColor(ACCBG)
c.roundRect(W - M - 96 * mm, H - M - 98 * mm, 96 * mm, 66 * mm, 3 * mm, stroke=0, fill=1)
wrap(c, 'A household will not act on a cost and a saving. They act on how many years the '
        'money takes to come back, and which measure to do first. The bank tools\' own '
        'descriptions never mention it.', W - M - 88 * mm, H - M - 45 * mm, 80 * mm, 'Disp', 15, 8.4 * mm, TEXT)
c.showPage()

# 3 ------------------------------------------------------------------ model
slide(c, 'the model')
c.setFont('DispB', 31)
c.setFillColor(TEXT)
c.drawString(M, H - M - 16 * mm, 'Built from government microdata, published openly')
y = H - M - 32 * mm
y = wrap(c, 'DESNZ National Energy Efficiency Data-Framework 2026. 39,502 gas heated records '
            'with 2024 consumption, England and Wales. Median gas per property type and floor '
            'area band, calibrated to reproduce NEED published medians within 0.3% for 2 to 5 '
            'bedrooms and 3.3% for 1 bedroom.',
         M, y, W - 2 * M, BODY, 12, 6.4 * mm, MUTED)
y -= 6 * mm
c.setFont(BOLD, 11)
c.setFillColor(TEXT)
c.drawString(M, y, 'Four inputs. No smart meter, no survey, no account, no address.')
y -= 7 * mm
c.setFont(BODY, 10)
c.setFillColor(MUTED)
c.drawString(M, y, 'property type    |    bedrooms    |    insulation level    |    heating fuel')
gap = (W - 2 * M - 2 * 6 * mm) / 3
sy = y - 34 * mm
stat(c, M, sy, gap, '39,502', 'gas heated NEED records behind the table')
stat(c, M + gap + 6 * mm, sy, gap, '18 + 154', 'guides and table cells checked against the model automatically')
stat(c, M + 2 * (gap + 6 * mm), sy, gap, '0', 'cookies set, and no calculator asks for personal details')
c.setFont(BODY, 8.5)
c.setFillColor(MUTED)
c.drawString(M, sy - 10 * mm, 'Method at /methodology/. The model table itself is readable at /js/heat-model.js.')
c.showPage()

# 4 ------------------------------------------------------------------ different
slide(c, 'what is different')
c.setFont('DispB', 31)
c.setFillColor(TEXT)
c.drawString(M, H - M - 16 * mm, 'Everything about it is checkable')
y = H - M - 34 * mm
y = bullet(c, 'The method is published, and enforced',
           'Comparable tools return a score or an estimate without saying how it was produced. This '
           'one publishes the model table and the method behind it, and automated checks compare the '
           'heat demand and cost figures in 18 guides and 154 table cells against that table before '
           'anything goes live.',
           M, y, W - 2 * M)
y = bullet(c, 'No AI, by choice, not anti AI',
           'A heat pump often costs five figures and a household lives with it for 15 years, so the '
           'method and the data behind the number should be visible, not just a confident answer. '
           'Deterministic arithmetic over public data that anyone can check or work through by hand.',
           M, y, W - 2 * M)
y = bullet(c, 'It withholds the sale',
           'The boiler tool hides both the quote prompt and the quote form when a new boiler is cheaper '
           'over 15 years even on a heat pump tariff: at a £900 gas bill, 37 of its 120 input '
           'combinations. At a typical £860 bill the solar tool tells all 420 battery combinations to '
           'price the battery separately, and shows a 25 year loss in 213.', M, y, W - 2 * M)
c.showPage()

# 5 ------------------------------------------------------------------ honest
slide(c, 'where it stands')
c.setFont('DispB', 31)
c.setFillColor(TEXT)
c.drawString(M, H - M - 16 * mm, 'Small, growing fast, not yet tested house by house')

# Monthly Google search impressions in thousands, March launch month to September. September is drawn
# as what it has so far (22 days) plus a pale extension to its 30 day pace, so the
# projection is never mistaken for a result.
MONTHS = [('Mar', 11.8), ('Apr', 12.1), ('May', 11.4), ('Jun', 18.9), ('Jul', 24.9), ('Aug', 34.5), ('Sep', 45.3)]
SEP_PACE = 61.8
base, top = 205, 375
scale = (top - base) / SEP_PACE
bw, step = 44, 70
c.setFont(BOLD, 11)
c.setFillColor(TEXT)
c.drawString(M, 410, 'Monthly impressions on Google search')
for n, (mon, v) in enumerate(MONTHS):
    x = M + n * step
    if mon == 'Sep':
        c.setFillColor(ACCBG)
        c.setStrokeColor(ACCENT)
        c.setDash(3, 2)
        c.rect(x, base, bw, SEP_PACE * scale, stroke=1, fill=1)
        c.setDash()
        c.setFont(BOLD, 9.5)
        c.setFillColor(ACCENT)
        c.drawCentredString(x + bw / 2, base + SEP_PACE * scale + 5, 'on pace ~62k')
    c.setFillColor(ACCENT)
    c.rect(x, base, bw, v * scale, stroke=0, fill=1)
    c.setFont(BOLD, 9.5)
    if mon == 'Sep':
        c.setFillColor(SURFACE)
        c.drawCentredString(x + bw / 2, base + v * scale - 13, '%.1fk' % v)
    else:
        c.setFillColor(TEXT)
        c.drawCentredString(x + bw / 2, base + v * scale + 5, '%.1fk' % v)
    c.setFont(BODY, 9)
    c.setFillColor(MUTED)
    c.drawCentredString(x + bw / 2, base - 13, mon)
c.setStrokeColor(BORDER)
c.line(M - 4, base, M + 6 * step + bw + 4, base)
c.setFont(BODY, 8)
c.setFillColor(MUTED)
c.drawString(M + 6 * step + bw + 10, base + 4, 'Sep: 22 days')

sx, sw = W - M - 96 * mm, 96 * mm
stat(c, sx, 290, sw, '3.6', 'average Google position for the 4 bed heat pump cost guide')
stat(c, sx, 190, sw, 'Every month', 'clicks from Google have grown every month since launch. September passed all of August with eight days to spare.')

y = 150
c.setFont(BOLD, 11)
c.setFillColor(TEXT)
c.drawString(M, y, 'What I do not have, stated plainly')
y = wrap(c, 'The calculators store nothing and ask for no personal details, so there is no count of '
            'calculator uses, no completion rate and no user feedback. The model has been tested against '
            'measured data in aggregate, but no output has yet been checked against one house\'s quote or '
            'its metered consumption. Establishing that accuracy is the first '
            'thing a pilot should do.', M, y - 8 * mm, W - 2 * M, BODY, 11.5, 6.2 * mm, MUTED)
c.showPage()

# 6 ------------------------------------------------------------------ ask
slide(c, 'the pilot')
c.setFont('DispB', 31)
c.setFillColor(TEXT)
c.drawString(M, H - M - 16 * mm, '12 weeks, one cohort, a falsifiable result')
y = H - M - 34 * mm
y = bullet(c, 'Who', 'Mortgage customers at EPC band D or E, where the model is calibrated, '
                     'against a matched holdout. At a 0.1% yearly claim rate, a 6 month read '
                     'needs roughly 47,000 per arm.',
           M, y, 118 * mm)
y = bullet(c, 'What they see', 'A payback figure and a ranked list of measures for their own home, '
                               'inside a page Lloyds already runs.', M, y, 118 * mm)
y = bullet(c, 'Measured by', 'Green additional borrowing drawn, and model accuracy against the '
                             "customer's own annual kWh. No difference at 6 months means it did not work.",
           M, y, 118 * mm)
bx = W - M - 96 * mm
c.setFillColor(SURFACE)
c.setStrokeColor(BORDER)
c.roundRect(bx, H - M - 92 * mm, 96 * mm, 60 * mm, 3 * mm, stroke=1, fill=1)
c.setFont(BOLD, 10.5)
c.setFillColor(TEXT)
c.drawString(bx + 8 * mm, H - M - 42 * mm, 'Commercially')
wrap(c, 'Not seeking investment. A pilot first, to find out whether it works. If it does, we agree '
        'terms for wider use. No revenue share and no referral links on a Lloyds page. It is a lookup '
        'table plus arithmetic, so no customer data needs to move.',
     bx + 8 * mm, H - M - 52 * mm, 80 * mm, BODY, 11, 6 * mm, MUTED)
c.setFont(BODY, 9)
c.setFillColor(MUTED)
c.drawString(M, M + 8 * mm, 'RetrofitPlanner.co.uk')
c.showPage()

c.save()
print('wrote %s (%d KB)' % (OUT.name, OUT.stat().st_size // 1024))
