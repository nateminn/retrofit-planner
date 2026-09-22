#!/usr/bin/env python3
"""Wire the six calculators into js/a11y.js.

Replaces the generic alert() validation with named field errors, and replaces the
silent results reveal with one that announces and moves focus. Idempotent.
"""
import io, re, sys, glob

CALCS = ['epc-calculator', 'solar-calculator', 'heat-pump-calculator',
         'insulation-calculator', 'boiler-vs-heat-pump', 'grants']

# (pattern, replacement) for the validation guards, per page where they differ
GUARDS = [
    # the EPC guard puts alert() and return on the same line inside a multi-line block
    (re.compile(r"if \(![^)]*?currentBand[^)]*?\) \{\s*\n\s*alert\('Please fill in all fields\.'\); return;\s*\n\s*\}", re.S),
     "if (!rpRequire(['propAge'])) { return; }"),
    (re.compile(r"if \(![^)]*?\) \{ alert\('Please fill in all (?:required )?fields\.'\); return; \}"),
     "if (!rpRequire()) { return; }"),
    (re.compile(r"if \(![^)]*?\) \{\s*\n\s*alert\('Please fill in all fields\.'\);\s*\n\s*return;\s*\n\s*\}", re.S),
     "if (!rpRequire()) { return; }"),
    (re.compile(r"if \(![^)]*?\) \{\s*\n\s*alert\('Please answer all eight questions\.'\); return;\s*\n\s*\}", re.S),
     "if (!rpRequire()) { return; }"),
]

REVEAL = re.compile(
    r"document\.getElementById\('results'\)\.classList\.add\('visible'\);\s*\n"
    r"\s*document\.getElementById\('results'\)\.scrollIntoView\(\{[^}]*\}\);")

def patch(slug):
    p = f'{slug}/index.html'
    s = io.open(p, encoding='utf-8').read()
    before = s
    notes = []

    # 1. load the helper
    if '/js/a11y.js' not in s:
        s = s.replace('</body>', '<script src="/js/a11y.js" defer></script>\n</body>', 1)
        notes.append('script')

    # 2. skip link, first focusable element on the page
    if 'skip-link' not in s:
        m = re.search(r'<body[^>]*>', s)
        s = s[:m.end()] + '\n<a class="skip-link" href="#main">Skip to content</a>' + s[m.end():]
        notes.append('skip-link')
    if re.search(r'<main\b(?![^>]*\bid=)', s):
        s = re.sub(r'<main\b(?![^>]*\bid=)', '<main id="main"', s, count=1)
        notes.append('main-id')

    # 3. named validation
    for pat, rep in GUARDS:
        new, n = pat.subn(rep, s, count=1)
        if n:
            s = new; notes.append('validate'); break

    # 4. the conditional EPC age check
    s2 = s.replace(
        "if (!propAge) { alert('Please choose when the property was built so we can estimate the rating.'); return; }",
        "if (!rpRequireOne('propAge', 'Choose when it was built so we can estimate the rating.')) { return; }")
    if s2 != s:
        s = s2; notes.append('validate-age')

    # 5. announce results and move focus
    s, n = REVEAL.subn("rpReveal('results');", s)
    if n:
        notes.append(f'reveal x{n}')

    if s != before:
        io.open(p, 'w', encoding='utf-8').write(s)
    print(f"  {slug:24} {', '.join(notes) if notes else 'no change'}")
    return 'validate' in notes or 'validate-age' in notes, n

if __name__ == '__main__':
    print('wiring calculators into js/a11y.js')
    for c in CALCS:
        patch(c)
    leftover = []
    for c in CALCS:
        s = io.open(f'{c}/index.html', encoding='utf-8').read()
        if re.search(r"alert\('Please", s):
            leftover.append(c)
    print('\nremaining alert() validation:', leftover if leftover else 'none')
