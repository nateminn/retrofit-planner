#!/usr/bin/env python3
"""Open a photo's source page in a headless browser and print title plus licence-related text. usage: photo_page.py <url>"""
import sys, re
from playwright.sync_api import sync_playwright
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"
url = sys.argv[1]
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(user_agent=UA)
    r = pg.goto(url, wait_until='domcontentloaded', timeout=45000); pg.wait_for_timeout(2000)
    print('status', r.status); print('title', pg.title())
    text = pg.evaluate('document.body.innerText')
    for m in re.finditer(r'[^\n]*(licen[cs]e|CC0|CC BY|Creative Commons|Public domain|free to use|Photo by|Photographer|Author|Attribution)[^\n]*', text, re.I):
        print('  ', m.group(0).strip()[:160])
    hits = pg.evaluate("""() => [...document.querySelectorAll('a[href*="/@"], a[href*="/users/"], a[rel="author"], [data-testid*="author"], [class*="author"], [class*="Author"]')].slice(0,5).map(a => a.textContent.trim().slice(0,60))""")
    print('author-ish', hits)
    b.close()
