#!/usr/bin/env python3
"""Put the ECO4 closure on every page that invites action on it.

ECO4 ends on 31 December 2026 and the work must be COMPLETE by then, not merely applied
for. 24 pages were telling people they could get measures free through ECO4 without
saying that. Rather than 24 bespoke rewrites, this inserts one dated notice after the
first substantive mention, so the wording stays identical everywhere and can be swapped
or removed in a single pass on 1 January.

Run with --remove after the scheme closes.
"""
import io, re, sys, glob

MARK = 'data-scheme-note="eco4"'

NOTICE = (
    '<aside class="scheme-note" ' + MARK + '>'
    '<p><strong>ECO4 closes on 31 December 2026.</strong> The work has to be finished by then, '
    'not just applied for, and installers fill up as the date gets closer. Government has confirmed '
    'there will be no successor supplier obligation: from 2027 the money moves to council run schemes '
    'under the Warm Homes Plan, which you apply for through your local authority rather than your '
    'energy supplier. If you think you qualify, start now. '
    '<a href="/grants/">Check what you qualify for</a>.</p>'
    '</aside>'
)

# a mention that invites action, as opposed to a nav link or a card description
SUBSTANTIVE = re.compile(
    r'(free|fund|funds|funded|funding|covers?|cover|pay for|pays for|qualify|eligible|grant)'
    r'[^<]{0,80}\bECO4\b|\bECO4\b[^<]{0,80}'
    r'(free|fund|funds|funded|funding|covers?|cover|pay for|pays for|qualify|eligible)', re.I)

def target_paragraph(html):
    """The first <p> inside main that makes a substantive ECO4 claim."""
    m = re.search(r'<main\b[^>]*>', html)
    start = m.end() if m else 0
    for p in re.finditer(r'<p\b[^>]*>.*?</p>', html[start:], re.S):
        text = re.sub(r'<[^>]+>', ' ', p.group(0))
        if 'ECO4' in text and SUBSTANTIVE.search(text):
            return start + p.end()
    return None

def apply(path, remove=False):
    s = io.open(path, encoding='utf-8').read()
    if remove:
        new = re.sub(r'<aside class="scheme-note" ' + MARK + r'>.*?</aside>', '', s, flags=re.S)
        if new != s:
            io.open(path, 'w', encoding='utf-8').write(new)
            return 'removed'
        return None
    if MARK in s:
        return None
    if 'ECO4' not in s:
        return None
    # Pages that already explain the closure in their own words do not need a standing
    # notice repeating it. That includes the dedicated ECO4 guide and the grants checker.
    body = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', s, flags=re.S)
    if re.search(r'31 December 2026', body) or re.search(r'closes? (on |in )?(31 )?Dec', body, re.I):
        return None
    at = target_paragraph(s)
    if at is None:
        return None
    io.open(path, 'w', encoding='utf-8').write(s[:at] + '\n' + NOTICE + s[at:])
    return 'added'

if __name__ == '__main__':
    remove = '--remove' in sys.argv
    pages = sorted(set(glob.glob('index.html') + glob.glob('*/index.html')
                       + glob.glob('guides/*/index.html'))
                   - {'quote-thanks/index.html'})
    done = []
    for p in pages:
        r = apply(p, remove)
        if r:
            done.append(p)
    print(f"{'removed from' if remove else 'added to'} {len(done)} pages")
    for d in done:
        print(f"   {d}")
