#!/usr/bin/env python3
"""Add FAQPage JSON-LD to guides that have a visible FAQ section but no schema for it.
The schema is generated from the visible h3/p pairs so the two can never disagree.
usage: faq_schema.py [slug ...]   (default: every guide missing it)"""
import os, re, sys, json, html

def strip(x):
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', x))).strip()

def has_faq_schema(s):
    for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        try: j = json.loads(b)
        except Exception: continue
        for x in (j if isinstance(j, list) else [j]):
            if x.get('@type') == 'FAQPage': return True
    return False

slugs = sys.argv[1:] or sorted(d for d in os.listdir('guides') if os.path.isdir(os.path.join('guides', d)))
added = 0
for slug in slugs:
    p = os.path.join('guides', slug, 'index.html')
    if not os.path.isfile(p): continue
    s = open(p, encoding='utf-8').read()
    if has_faq_schema(s): continue
    m = re.search(r'<h2[^>]*>\s*Frequently asked questions\s*</h2>(.*?)(?=<h2|</main>)', s, re.S)
    if not m: continue
    pairs = re.findall(r'<h3>(.*?)</h3>\s*<p>(.*?)</p>', m.group(1), re.S)
    if not pairs: print('  %s: FAQ section but no h3/p pairs' % slug); continue
    faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": strip(q), "acceptedAnswer": {"@type": "Answer", "text": strip(a)}} for q, a in pairs]}
    tag = '<script type="application/ld+json">%s</script>\n' % json.dumps(faq, ensure_ascii=False, separators=(',', ':'))
    assert '</head>' in s, slug
    open(p, 'w', encoding='utf-8').write(s.replace('</head>', tag + '</head>', 1))
    added += 1
    print('  %-40s FAQPage added with %d questions' % (slug, len(pairs)))
print('pages updated:', added)
