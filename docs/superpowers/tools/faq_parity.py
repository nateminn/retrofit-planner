#!/usr/bin/env python3
"""Every FAQPage question and answer in a page's JSON-LD must appear, word for word, in the
page's visible text. Google treats FAQ markup that says something the page does not as
misleading, and a figure fixed in one place but not the other is how pages drift.

Usage: python3 docs/superpowers/tools/faq_parity.py   (exit code 1 on any mismatch)
"""
import html, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]


def norm(x):
    x = html.unescape(re.sub(r'<[^>]+>', ' ', x))
    x = x.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    x = re.sub(r'\s+', ' ', x)
    return re.sub(r'\s+([.,;:!?)])', r'\1', x.replace('( ', '(')).strip()


def main():
    bad, pages, pairs = [], 0, 0
    for f in sorted(ROOT.rglob('*.html')):
        r = f.relative_to(ROOT)
        if r.parts[0] in ('docs', 'node_modules'):
            continue
        s = f.read_text()
        faqs = []
        for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
            try:
                j = json.loads(block)
            except ValueError:
                continue
            for item in (j if isinstance(j, list) else [j]):
                if isinstance(item, dict) and item.get('@type') == 'FAQPage':
                    faqs += item.get('mainEntity', [])
        if not faqs:
            continue
        pages += 1
        body = s[s.find('<body'):]
        body = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', body, flags=re.S)
        visible = norm(body)
        for q in faqs:
            pairs += 1
            name = norm(q.get('name', ''))
            ans = norm(q.get('acceptedAnswer', {}).get('text', ''))
            if name not in visible:
                bad.append((str(r), 'question not on page', name[:90]))
            if ans not in visible:
                # find where it first diverges from the closest visible passage, for the report
                head = ans[:40]
                i = visible.find(head)
                if i < 0:
                    bad.append((str(r), 'answer not on page', ans[:90]))
                else:
                    seg = visible[i:i + len(ans) + 40]
                    k = next((n for n, (a, b) in enumerate(zip(ans, seg)) if a != b), min(len(ans), len(seg)))
                    bad.append((str(r), 'answer differs', 'schema "...%s" / page "...%s"' % (ans[max(0, k - 30):k + 40], seg[max(0, k - 30):k + 40])))
    for p, what, detail in bad[:40]:
        print('  %-52s %-20s %s' % (p[:52], what, detail[:200]))
    print('%s: %d FAQ answers on %d pages checked, %d problems' % ('FAIL' if bad else 'PASS', pairs, pages, len(bad)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
