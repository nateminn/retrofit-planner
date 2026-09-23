#!/usr/bin/env python3
"""Stop the Google Fonts stylesheet blocking first paint.

PageSpeed puts render-blocking requests at 900ms on mobile for this site, and the font
stylesheet is a cross origin round trip that has to resolve before anything draws. The URL
already carries display=swap, so text renders in the fallback and swaps regardless; making
the request non-blocking just means that first render does not wait for it.

The media="print" trick loads the stylesheet at low priority and promotes it on load, with
a noscript fallback for anyone without JavaScript. Idempotent.
"""
import io, re, glob

BLOCKING = re.compile(
    r'<link href="(https://fonts\.googleapis\.com/css2\?[^"]+)" rel="stylesheet">')

def patch(path):
    s = io.open(path, encoding='utf-8').read()
    if 'this.media=' in s:
        return None
    m = BLOCKING.search(s)
    if not m:
        return None
    url = m.group(1)
    new = ('<link rel="stylesheet" href="' + url + '" media="print" '
           'onload="this.media=\'all\';this.onload=null">'
           '<noscript><link rel="stylesheet" href="' + url + '"></noscript>')
    io.open(path, 'w', encoding='utf-8').write(s[:m.start()] + new + s[m.end():])
    return True

if __name__ == '__main__':
    pages = sorted(set(glob.glob('index.html') + glob.glob('*/index.html')
                       + glob.glob('guides/*/index.html') + glob.glob('embed/*/index.html')))
    done = [p for p in pages if patch(p)]
    print(f"made the font stylesheet non-blocking on {len(done)} pages")
