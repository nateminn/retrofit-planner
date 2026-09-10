#!/usr/bin/env python3
"""Search free-to-use photo sources without API keys. Prints JSON list of candidates.
usage: photo_search.py "<query>" [--sources pexels,pixabay,commons,openverse] [--limit 12]
Each candidate: {source, id, title, photographer, page_url, download_url, width, height, license}
Licences: pexels (Pexels License), pixabay (Pixabay Content License), commons/openverse carry the real CC tag."""
import sys, json, re, html, subprocess, urllib.parse

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"

def curl_json(url):
    out = subprocess.run(['curl', '-s', '-A', UA, '--max-time', '30', url], capture_output=True, text=True).stdout
    try:
        return json.loads(out)
    except Exception:
        return None

def pexels(q, limit):
    from playwright.sync_api import sync_playwright
    res = []
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(user_agent=UA)
        pg.goto('https://www.pexels.com/search/%s/' % urllib.parse.quote(q), wait_until='domcontentloaded', timeout=45000)
        pg.wait_for_timeout(2500)
        cards = pg.evaluate("""() => [...document.querySelectorAll('article')].map(a => {
            const ph = a.querySelector('a[href^="/photo/"]'); const img = a.querySelector('img'); const us = a.querySelector('a[href^="/@"]');
            return {href: ph && ph.getAttribute('href'), alt: img && img.getAttribute('alt'), src: img && (img.getAttribute('src')||''), user: us && us.textContent.trim()}; })""")
        b.close()
    seen = set()
    for c in cards:
        m = re.search(r'/photo/([a-z0-9-]+?)-(\d+)/?$', c.get('href') or '')
        if not m or m.group(2) in seen: continue
        seen.add(m.group(2)); pid = m.group(2)
        res.append(dict(source='pexels', id=pid, title=(c.get('alt') or m.group(1).replace('-', ' ')).strip(), photographer=c.get('user') or '',
                        page_url='https://www.pexels.com/photo/%s-%s/' % (m.group(1), pid),
                        download_url='https://images.pexels.com/photos/%s/pexels-photo-%s.jpeg?auto=compress&cs=tinysrgb&w=1600' % (pid, pid),
                        width=None, height=None, license='Pexels License (free for commercial use, no attribution required)'))
        if len(res) >= limit: break
    return res

def pixabay(q, limit):
    from playwright.sync_api import sync_playwright
    res = []
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(user_agent=UA)
        pg.goto('https://pixabay.com/images/search/%s/' % urllib.parse.quote(q), wait_until='domcontentloaded', timeout=45000)
        pg.wait_for_timeout(2500)
        cards = pg.evaluate("""() => [...document.querySelectorAll('a[href^="/photos/"]')].map(a => { const img = a.querySelector('img');
            return {href: a.getAttribute('href'), alt: img && img.getAttribute('alt'), srcset: img && (img.getAttribute('srcset') || img.getAttribute('data-lazy-srcset') || ''), src: img && (img.getAttribute('src') || img.getAttribute('data-lazy-src') || '')}; })""")
        b.close()
    seen = set()
    for c in cards:
        m = re.search(r'/photos/([a-z0-9-]+?)-(\d+)/?$', c.get('href') or '')
        if not m or m.group(2) in seen: continue
        cdn = re.search(r'(https://cdn\.pixabay\.com/photo/[^\s",]+?)_(?:\d+)\.(jpg|jpeg|png)', (c.get('srcset') or '') + ' ' + (c.get('src') or ''))
        if not cdn: continue
        seen.add(m.group(2))
        res.append(dict(source='pixabay', id=m.group(2), title=(c.get('alt') or m.group(1).replace('-', ' ')).strip(), photographer='',
                        page_url='https://pixabay.com' + m.group(0), download_url='%s_1280.%s' % (cdn.group(1), cdn.group(2)),
                        width=None, height=None, license='Pixabay Content License (free for commercial use, no attribution required)'))
        if len(res) >= limit: break
    return res

def commons(q, limit):
    url = ('https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch=%s&gsrnamespace=6&gsrlimit=%d'
           '&prop=imageinfo&iiprop=url|size|extmetadata&iiurlwidth=1600&format=json') % (urllib.parse.quote(q + ' filetype:bitmap'), limit)
    d = curl_json(url) or {}
    res = []
    for p in (d.get('query', {}).get('pages', {}) or {}).values():
        ii = (p.get('imageinfo') or [{}])[0]; em = ii.get('extmetadata', {})
        lic = em.get('LicenseShortName', {}).get('value', '')
        if not re.search(r'CC0|CC BY|Public domain|PD', lic, re.I): continue
        artist = re.sub(r'<[^>]+>', '', em.get('Artist', {}).get('value', '')).strip()
        res.append(dict(source='commons', id=p['title'], title=p['title'].replace('File:', '').rsplit('.', 1)[0], photographer=artist,
                        page_url=ii.get('descriptionurl'), download_url=ii.get('thumburl') or ii.get('url'), width=ii.get('width'), height=ii.get('height'), license=lic))
    return res

def openverse(q, limit):
    url = 'https://api.openverse.org/v1/images/?q=%s&license=cc0,pdm,by&category=photograph&page_size=%d' % (urllib.parse.quote(q), limit)
    d = curl_json(url) or {}
    res = []
    for r in d.get('results', []):
        res.append(dict(source='openverse:' + r.get('source', ''), id=r['id'], title=r.get('title') or '', photographer=r.get('creator') or '',
                        page_url=r.get('foreign_landing_url'), download_url=r.get('url'), width=r.get('width'), height=r.get('height'),
                        license='CC %s %s' % (r.get('license', '').upper(), r.get('license_version', ''))))
    return res

if __name__ == '__main__':
    q = sys.argv[1]; args = sys.argv[2:]
    sources = 'pexels,pixabay,commons,openverse'; limit = 12
    if '--sources' in args: sources = args[args.index('--sources') + 1]
    if '--limit' in args: limit = int(args[args.index('--limit') + 1])
    out = []
    for s in sources.split(','):
        try:
            out += globals()[s](q, limit)
        except Exception as e:
            print(json.dumps({'source': s, 'error': str(e)[:200]}), file=sys.stderr)
    print(json.dumps(out, indent=1))
