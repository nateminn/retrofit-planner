#!/usr/bin/env python3
"""Answer first, detail on request.

Long pages read like a book. This keeps every word (search engines and anyone who wants it
still get it) but shows each section as its question, a one or two sentence answer, and
its main table or chart, with the rest folded into a "Read the detail" toggle that opens
in place. Method notes under tables fold into "The data behind this table", and FAQs
become a list of questions that open one at a time.

docs/answer-first.json maps a page to:
  {"sections": [{"h2": "exact heading text", "answer": "one or two sentences, **bold** allowed",
                 "title": "optional new heading text", "keep": true,  # keep the first table or chart visible
                 "summary": "optional toggle label"}],
   "notes":    [{"starts": "first words of a p.note", "summary": "The data behind this table"}],
   "faq":      true,
   "jump":     [["Label", "exact heading text or #id"], ...]}   # optional row of question buttons
Every £, p, % and kW figure in an answer must appear in the section it summarises.

Runs once per page: a page already carrying data-af is skipped. Undo with git.
Usage: python3 docs/superpowers/tools/answer_first.py [--apply]
"""
import html, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
APPLY = '--apply' in sys.argv
FIG_RE = re.compile(r'£[\d,]+(?:\.\d+)?|\b\d[\d,]*(?:\.\d+)?(?:p\b|%| kW\b)')


def visible(s):
    s = re.sub(r'<script.*?</script>|<style.*?</style>|<svg.*?</svg>', ' ', s, flags=re.S)
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s)))


def md(p):
    return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', p)


def element_end(s, start):
    """End index of the element opening at start, counting nested tags of the same name."""
    tag = re.match(r'<([a-z0-9]+)', s[start:]).group(1)
    depth, i = 0, start
    for m in re.finditer(r'<(/?)%s\b[^>]*>' % tag, s[start:]):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            return start + m.end()
    raise ValueError('unbalanced <%s> at %d' % (tag, start))


def slug(t):
    return re.sub(r'[^a-z0-9]+', '-', html.unescape(t).lower()).strip('-')[:48].rstrip('-')


def process(page, spec):
    f = ROOT / page / 'index.html'
    s = f.read_text()
    problems = []
    if 'data-af' in s:
        return s, ['%s: already answer-first, skipped' % page]
    a = s.index('<main')
    end = s.index('<footer', a)

    # 1. sections, last first so earlier offsets stay valid
    heads = [(m.start(), m.end(), re.sub(r'\s+', ' ', visible(m.group(2))).strip(), m.group(1))
             for m in re.finditer(r'<h2([^>]*)>(.*?)</h2>', s[:end]) if m.start() > a]
    for sec in reversed(spec.get('sections', [])):
        idx = next((k for k, h in enumerate(heads) if h[2] == sec['h2']), None)
        if idx is None:
            problems.append('%s: no heading "%s"' % (page, sec['h2']))
            continue
        h_start, h_end, text, attrs = heads[idx]
        stop = heads[idx + 1][0] if idx + 1 < len(heads) else end
        for marker in ('<div class="related-links">', '</article>', '<!-- lead-form'):
            k = s.find(marker, h_end, stop)
            if k != -1:
                stop = k
        body = s[h_end:stop]
        for fig in FIG_RE.findall(sec['answer'].replace('**', '')):
            if fig not in visible(body):
                problems.append('%s, "%s": %s is in the answer but not in the section' % (page, sec['h2'], fig))
        kept = ''
        if sec.get('keep', True):
            m = re.search(r'<div class="tblwrap"|<figure class="chart-fig"', body)
            if m:
                e = element_end(body, m.start())
                kept, body = body[m.start():e], body[:m.start()] + body[e:]
        if not re.search(r'\bid="', attrs):
            attrs = ' id="%s"' % slug(sec.get('title', text)) + attrs
        head = '<h2%s>%s</h2>' % (attrs, html.escape(sec.get('title', text), quote=False))
        rest = body.strip()
        block = ('\n            ' + head
                 + '\n            <p class="answer" data-af>' + md(sec['answer']) + '</p>'
                 + ('\n            ' + kept if kept else '')
                 + ('\n            <details class="more" data-af><summary>%s</summary>\n            %s\n            </details>'
                    % (sec.get('summary', 'Read the detail'), rest) if rest else '')
                 + '\n\n            ')
        s = s[:h_start] + block + s[stop:]

    # 2. method notes under tables
    for n in spec.get('notes', []):
        m = re.search(r'<p class="(?:data-table )?note">\s*' + re.escape(n['starts']) + r'.*?</p>', s, re.S)
        if not m:
            problems.append('%s: no note starting "%s"' % (page, n['starts']))
            continue
        s = s[:m.start()] + '<details class="more note-more" data-af><summary>%s</summary>%s</details>' % (
            n.get('summary', 'The data behind this table'), m.group(0)) + s[m.end():]

    # 3. FAQ: each question opens on its own
    if spec.get('faq'):
        m = re.search(r'<h2[^>]*>Frequently asked questions</h2>', s)
        if not m:
            problems.append('%s: no FAQ heading' % page)
        else:
            stop = re.search(r'<h2|</article>|<div class="related-links">', s[m.end():])
            stop = m.end() + (stop.start() if stop else 0)
            faq = s[m.end():stop]
            faq2, k = re.subn(r'<h3>(.*?)</h3>\s*((?:<p>.*?</p>\s*)+)',
                              lambda q: '<details class="faq-item" data-af><summary><h3>%s</h3></summary>%s</details>\n            '
                              % (q.group(1), q.group(2).strip()), faq, flags=re.S)
            if not k:
                problems.append('%s: no FAQ questions found' % page)
            head = m.group(0) if 'id="' in m.group(0) else m.group(0).replace('<h2', '<h2 id="faq"', 1)
            s = s[:m.start()] + head + faq2 + s[stop:]

    # 4. a row of question buttons at the top of the article
    if spec.get('jump'):
        ids = dict((re.sub(r'\s+', ' ', visible(m.group(2))).strip(), re.search(r'id="([^"]+)"', m.group(1)))
                   for m in re.finditer(r'<h2([^>]*)>(.*?)</h2>', s))
        links = []
        for label, target in spec['jump']:
            if target.startswith('#'):
                links.append((label, target))
            elif ids.get(target):
                links.append((label, '#' + ids[target].group(1)))
            else:
                problems.append('%s: jump target "%s" has no id' % (page, target))
        nav = ('<nav class="jump af-jump" aria-label="Jump to a question" data-af>%s</nav>\n'
               % ''.join('<a href="%s">%s</a>' % (h, html.escape(l)) for l, h in links))
        k = s.index('<article>', a) + len('<article>')
        s = s[:k] + '\n            ' + nav + s[k:]
    return s, problems


def main():
    data = json.loads((ROOT / 'docs' / 'answer-first.json').read_text())
    bad = []
    for page, spec in data.items():
        new, problems = process(page, spec)
        real = [p for p in problems if 'already answer-first' not in p]
        bad += real
        for p in problems:
            print('  ' + p)
        if APPLY and not real and new != (ROOT / page / 'index.html').read_text():
            (ROOT / page / 'index.html').write_text(new)
            print('  applied to ' + page)
    print('%s: %d pages' % ('FAIL' if bad else 'PASS', len(data)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
