#!/usr/bin/env python3
"""Give every page a <main> landmark.

Lighthouse flags "Document does not have a main landmark" on the home page, and 15 pages
have none. A screen reader user has no way to skip the header and navigation without one,
which also makes the skip link added in the accessibility pass land nowhere useful.

Wraps the existing content container rather than inventing a new element, so nothing moves
visually. Idempotent.
"""
import io, re, glob, sys

# the element that already holds the page body on each template, in order of preference
# gi-content is a PER SECTION container on the guides hub, so choosing it wrapped only the
# first of six sections and left 23 of 47 guide items outside the landmark. Only match
# containers that hold the whole page body.
WRAPPERS = ['page-content', 'content-section', 'container']

def patch(path):
    s = io.open(path, encoding='utf-8').read()
    if re.search(r'<main\b', s):
        return None
    m = re.search(r'</(?:nav|header)>\s*', s)
    if not m:
        return None
    # find the first content wrapper after the header, and the matching close before the footer
    foot = re.search(r'<footer\b', s)
    end = foot.start() if foot else len(s)
    body = s[m.end():end]
    opened = None
    for w in WRAPPERS:
        mm = re.search(r'<(div|section|article)\b[^>]*class="[^"]*\b' + w + r'\b[^"]*"[^>]*>', body)
        if mm:
            opened = mm
            break
    if opened:
        start_abs = m.end() + opened.start()
    else:
        start_abs = m.end()
    new = s[:start_abs] + '<main id="main" tabindex="-1">\n' + s[start_abs:end] + '</main>\n' + s[end:]
    io.open(path, 'w', encoding='utf-8').write(new)
    return True

if __name__ == '__main__':
    pages = sorted(set(glob.glob('index.html') + glob.glob('*/index.html')
                       + glob.glob('guides/*/index.html') + glob.glob('embed/*/index.html')))
    done = [p for p in pages if patch(p)]
    print(f"added a main landmark to {len(done)} pages")
    for d in done:
        print(f"   {d}")
