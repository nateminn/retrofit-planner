#!/usr/bin/env python3
"""Add scope attributes to table headers.

Without scope, a screen reader cannot reliably say which column a cell belongs to, and this
site is 40+ data tables of numbers where that association is the whole point. Headers inside
thead become scope="col"; a th that opens a tbody row becomes scope="row". Idempotent.
"""
import io, re, glob, sys

TH = re.compile(r'<th(?![^>]*\bscope=)([^>]*)>')

def patch(html):
    out, n = [], 0
    pos = 0
    # walk thead and tbody blocks separately so row headers are not mislabelled as columns
    for m in re.finditer(r'<(thead|tbody)\b[^>]*>.*?</\1>', html, re.S):
        out.append(html[pos:m.start()])
        block, kind = m.group(0), m.group(1)
        if kind == 'thead':
            block, k = TH.subn(r'<th scope="col"\1>', block)
            n += k
        else:
            rows = []
            last = 0
            for r in re.finditer(r'<tr\b[^>]*>.*?</tr>', block, re.S):
                rows.append(block[last:r.start()])
                row = r.group(0)
                m2 = TH.search(row)
                if m2:
                    # an existing th that opens a body row is a row header
                    row = row[:m2.start()] + f'<th scope="row"{m2.group(1)}>' + row[m2.end():]
                    n += 1
                else:
                    # promote the opening td to a row header, but only when it is a text
                    # label rather than a number, so numeric first columns are left alone
                    m3 = re.match(r'(\s*<tr\b[^>]*>\s*)<td([^>]*)>(.*?)</td>', row, re.S)
                    if m3:
                        text = re.sub(r'<[^>]+>', '', m3.group(3)).strip()
                        if text and not re.match(r'^[£\d]', text):
                            row = (m3.group(1) + f'<th scope="row"{m3.group(2)}>' + m3.group(3)
                                   + '</th>' + row[m3.end():])
                            n += 1
                rows.append(row)
                last = r.end()
            rows.append(block[last:])
            block = ''.join(rows)
        out.append(block)
        pos = m.end()
    out.append(html[pos:])
    return ''.join(out), n

if __name__ == '__main__':
    pages = sorted(set(glob.glob('index.html') + glob.glob('*/index.html')
                       + glob.glob('guides/*/index.html') + glob.glob('embed/*/index.html')))
    total, touched = 0, 0
    for p in pages:
        s = io.open(p, encoding='utf-8').read()
        new, n = patch(s)
        if n:
            io.open(p, 'w', encoding='utf-8').write(new)
            total += n; touched += 1
    print(f"added scope to {total} headers across {touched} pages")
