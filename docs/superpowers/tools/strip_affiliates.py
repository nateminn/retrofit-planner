#!/usr/bin/env python3
"""Remove every affiliate link and affiliate statement from the shipped site.

Run once on 24 Sep 2026 when the owner paused all affiliate activity. Amazon links are
unwrapped so the advice around them survives; sentences that only existed to point at a
product are removed; the per page commission note and the footer Amazon line go.
Usage: python3 docs/superpowers/tools/strip_affiliates.py [--apply]
"""
import re, sys, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parents[3]
APPLY = '--apply' in sys.argv

def flex(s):
    """Literal sentence to a regex that tolerates any whitespace between words."""
    return r'\s+'.join(re.escape(w) for w in s.split())

DELETE = [
    "See recommended loft insulation rolls for the right product at the right depth.",
    "See recommended loft insulation rolls for the right product.",
    "See recommended draught excluder strips for the best options.",
    "See recommended sash window draught-proofing kits.",
    "See recommended door bottom draught excluders.",
    "See recommended letterbox draught excluders.",
    "See recommended chimney balloons.",
    "See recommended draught excluder strips to get started.",
    "See recommended smart thermostats if you want to upgrade further.",
    "See recommended energy monitors to track the real impact of your upgrades on consumption.",
    "For optimal heat pump control, see recommended smart thermostats designed for heat pump systems.",
    "To optimise your running costs, see recommended smart thermostats for heat pump scheduling and recommended energy monitors to track your actual consumption.",
    "See recommended anti-vibration pads that sit between the unit and the plinth.",
    "See recommended anti-vibration pads for noise reduction that may help with planning concerns.",
    "See recommended anti-vibration pads.",
    "See recommended smart thermostats with scheduling features that optimise comfort and noise management.",
    "See recommended smart thermostats designed to optimise heat pump scheduling.",
    "See recommended smart thermostats with heat pump optimisation features.",
    "See recommended smart thermostats that can coordinate heat pump scheduling with battery charge levels.",
    "See recommended energy monitors that show real-time electricity usage.",
    "For efficient boiler or heat pump management, see recommended smart thermostats.",
    "If topping up, see recommended loft insulation rolls.",
    "See recommended borescope cameras if you want to check yourself.",
    "See recommended rigid PIR insulation boards for the best products for underfloor use.",
    "See recommended rigid insulation boards.",
    "For optimal heat pump and radiator control, see recommended smart thermostats with room-by-room scheduling and recommended smart TRVs that adjust individual radiator output based on room temperature.",
    "Monitor your system performance with recommended energy monitors that show solar generation, battery charge, and grid import/export in real time.",
    # Orphans: plugs whose links were removed earlier but whose text stayed behind.
    "See recommended loft insulation rolls for the standard 100mm top-up layer.",
    "See recommended loft insulation rolls.",
    "See recommended draught excluder strips.",
    "See recommended loft boarding kits designed to maintain insulation depth.",
    "See recommended loft boarding kits that maintain the correct insulation depth.",
    "See recommended loft boarding kits designed for this purpose.",
    "See recommended loft boarding kits.",
    "See recommended energy monitors to measure the impact of your insulation on actual consumption.",
    "See recommended energy monitors that tenants can use to track their consumption.",
    "See recommended energy monitors to track exactly where your energy is going.",
    "See recommended LED bulb packs.",
    "See recommended smart electric radiators for flats.",
    "See recommended infrared heating panels.",
    "See recommended smart thermostats for optimal heat pump control.",
    "See recommended smart thermostats for systems that tenants can manage easily.",
    "See recommended sound level meters to check your specific situation before installation.",
]
REWRITE = [
    (r'See\s+recommended\s+anti-vibration\s+pads\s+to\s+reduce\s+transmitted\s+vibration,\s+and\s+read\s+our\s+(<a\b[^>]*>[^<]*</a>)\.',
     r'Anti-vibration pads reduce transmitted vibration, and our \1 covers the rest.'),
    (flex("For noise reduction on the outdoor unit, see recommended anti-vibration pads."),
     "For noise reduction on the outdoor unit, fit anti-vibration pads."),
    (flex("If you still have draughts, see recommended draught excluder strips for an easy next step."),
     "If you still have draughts, draught excluder strips are an easy next step."),
    (flex("See recommended damp meters to check your walls yourself before calling an installer."),
     "A damp meter lets you check your walls yourself before calling an installer."),
    (flex("See recommended damp meters to check before you start."),
     "Check for damp with a damp meter before you start."),
    (flex("See recommended thermal imaging cameras to verify insulation coverage after installation."),
     "A thermal imaging camera can confirm insulation coverage after installation."),
    (flex("See recommended replacement air brick covers if yours are damaged."),
     "Replace any air brick covers that are damaged."),
    (r'\s*\(see\s+recommended\s+draught\s+excluder\s+strips\)', ''),
    (r'\s*\(see\s+recommended\s+pads\)', ''),
    (r'with\s+recommended\s+energy\s+monitors', 'with an energy monitor'),
    (r'with\s+a\s+recommended\s+energy\s+monitor', 'with an energy monitor'),
    (r'with\s+a\s+recommended\s+digital\s+hygrometer', 'with a digital hygrometer'),
    (r'Use\s+a\s+recommended\s+thermal\s+imaging\s+camera', 'Use a thermal imaging camera'),
    (flex("See recommended pipe insulation for exposed loft pipework."), "Insulate any exposed pipework in the loft."),
    (flex("See recommended pipe insulation for loft pipework."), "Insulate any exposed pipework in the loft."),
    (flex("See recommended draught excluder strips for an easy DIY fix."), "Draught excluder strips are an easy DIY fix."),
    (r'See\s+recommended\s+loft\s+insulation\s+rolls\s+and\s+use\s+our\s+(<a\b[^>]*>[^<]*</a>)\s+for\s+exact\s+savings\.', r'Use our \1 for exact savings.'),
    (flex("See recommended draught excluder strips for a DIY approach to the most common gaps."), "Draught excluder strips are a cheap DIY fix for the most common gaps."),
    (flex("See recommended draught excluder strips for a DIY approach."), "Draught excluder strips are a cheap DIY option."),
    (flex("See recommended draught excluder strips for an immediate improvement."), "Draught excluder strips give an immediate improvement."),
    (flex("See recommended anti-vibration pads to reduce noise transmission through the ground."), "Anti-vibration pads reduce noise transmitted through the ground."),
    (r'See\s+recommended\s+anti-vibration\s+pads\s+to\s+reduce\s+transmitted\s+noise\s+further,\s+and\s+read\s+our\s+(<a\b[^>]*>[^<]*</a>)\s+for\s+practical\s+reduction\s+tips\.', r'Anti-vibration pads reduce transmitted noise further, and our \1 has practical reduction tips.'),
    (flex("See recommended thermal imaging cameras to find areas where insulation has been displaced."), "A thermal imaging camera shows where insulation has been displaced."),
    (flex("See recommended damp meters to check your walls before committing."), "Check your walls with a damp meter before committing."),
    (flex("See recommended thermal imaging cameras to identify exactly where your walls are losing the most heat before you commit to insulating."), "A thermal imaging camera shows exactly where your walls lose the most heat before you commit to insulating."),
]
AMAZON = re.compile(r'<a\b[^>]*href="https://www\.amazon\.co\.uk[^"]*"[^>]*>(.*?)</a>', re.S)
NOTE = re.compile(r'[ \t]*<p class="affiliate-note"[^>]*>[^<]*</p>\n?')
FOOTER = re.compile(r'\s*As an Amazon Associate I earn from qualifying purchases\.')
EMPTY = re.compile(r'[ \t]*<(p|li)>\s*</\1>\n?')

stats = collections.Counter()
changed = []
for f in sorted(ROOT.rglob('*.html')):
    if 'docs' in f.relative_to(ROOT).parts:
        continue
    t0 = t = f.read_text()
    t, n = AMAZON.subn(r'\1', t); stats['amazon links unwrapped'] += n
    for s in DELETE:
        t, n = re.subn(r'\s*' + flex(s), '', t); stats['sentences deleted'] += n
    for pat, rep in REWRITE:
        t, n = re.subn(pat, rep, t); stats['sentences rewritten'] += n
    t, n = NOTE.subn('', t); stats['commission notes removed'] += n
    t, n = FOOTER.subn('', t); stats['footer Amazon lines removed'] += n
    t, n = EMPTY.subn('', t); stats['empty p/li removed'] += n
    if t != t0:
        changed.append(str(f.relative_to(ROOT)))
        if APPLY:
            f.write_text(t)

for k, v in stats.items():
    print('%-30s %d' % (k, v))
print('files changed:', len(changed))
print('APPLIED' if APPLY else 'dry run, pass --apply to write')
