#!/usr/bin/env python3
"""Every page's elements must open and close in order.

Folding sections behind toggles moves closing tags around; a section whose heading sits
inside a box would take half the box with it. Browsers repair broken nesting silently, so
the page still looks fine until it does not. This parses each page and reports any end tag
that does not match the element it should close.

Usage: python3 docs/superpowers/tools/html_nesting.py   (exit code 1 on any problem)
"""
import pathlib, sys
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parents[3]
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr',
        'path', 'circle', 'rect', 'line', 'polyline', 'polygon', 'ellipse', 'stop', 'use'}
OPTIONAL_END = {'p', 'li', 'option', 'tr', 'td', 'th', 'thead', 'tbody'}


class Check(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.errors = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()
            return
        # implied closes of optional-end elements are legal
        while self.stack and self.stack[-1][0] in OPTIONAL_END and self.stack[-1][0] != tag:
            self.stack.pop()
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()
        else:
            self.errors.append('line %d: </%s> but the open element is <%s> from line %s'
                               % (self.getpos()[0], tag, self.stack[-1][0] if self.stack else 'none',
                                  self.stack[-1][1] if self.stack else '-'))


def check(text):
    c = Check()
    c.feed(text)
    return c.errors


def main():
    bad = 0
    for f in sorted(ROOT.rglob('*.html')):
        if f.relative_to(ROOT).parts[0] in ('docs', 'node_modules'):
            continue
        errs = check(f.read_text())
        if errs:
            bad += 1
            print('  %s: %s%s' % (f.relative_to(ROOT), errs[0], ' (and %d more)' % (len(errs) - 1) if len(errs) > 1 else ''))
    print('%s: %d pages with broken nesting' % ('FAIL' if bad else 'PASS', bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
