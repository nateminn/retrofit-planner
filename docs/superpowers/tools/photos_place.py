#!/usr/bin/env python3
"""Process chosen photos into /images and place them on pages.
usage: photos_place.py <picks.json> <subjects.json> [--dry]
picks.json: [{slug, chosen:{file, source, id, title, photographer, page_url, license, license_url}, alt, caption}]
Idempotent: a page that already has id="photo-<slug>" is skipped; images are regenerated each run."""
import sys, json, re, os, html
from PIL import Image, ImageOps

SITE = 'https://www.retrofitplanner.co.uk'
CACHE = '.photo-src'
picks = json.load(open(sys.argv[1])); subjects = {s['slug']: s for s in json.load(open(sys.argv[2]))}
dry = '--dry' in sys.argv
os.makedirs('images', exist_ok=True)

def crop_resize(im, w, h):
    return ImageOps.fit(im, (w, h), Image.LANCZOS, centering=(0.5, 0.5))

HUB = open('guides/index.html', encoding='utf-8').read()

# Some originals put the subject off to one side, so a centre crop loses it.
# Fractions of the original frame (left, top, right, bottom) to keep before resizing.
PRECROP = {
    'boiler-vs-heat-pump': (0.40, 0.0, 1.0, 1.0),
}

def fetch(c, slug):
    """Always resolve the image from its source URL, keyed by that URL, so the file
    on disk can never drift from the credit metadata (agents reuse candidate filenames)."""
    import hashlib, subprocess
    os.makedirs(CACHE, exist_ok=True)
    key = hashlib.md5(c['download_url'].encode()).hexdigest()[:16]
    path = os.path.join(CACHE, '%s-%s.jpg' % (slug, key))
    if os.path.exists(path) and os.path.getsize(path) > 20000:
        return path
    r = subprocess.run(['python3', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'photo_get.py'), c['download_url'], path], capture_output=True, text=True)
    assert r.returncode == 0, ('download failed', slug, r.stdout.strip()[:120])
    return path

def process(slug, path, thumb=True):
    im = Image.open(path); im = ImageOps.exif_transpose(im).convert('RGB')
    if slug in PRECROP:
        l, t, r, bo = PRECROP[slug]; W, H = im.size
        im = im.crop((int(W * l), int(H * t), int(W * r), int(H * bo)))
    out = {}
    variants = [('1200', (1200, 800), 'webp'), ('960', (960, 640), 'webp'), ('640', (640, 427), 'webp'), ('og', (1200, 800), 'jpg')]
    if thumb: variants.insert(3, ('240', (240, 240), 'webp'))
    for name, (w, h), kind in variants:
        fn = 'images/%s-%s.%s' % (slug, name, kind)
        img = crop_resize(im, w, h)
        if kind == 'webp': img.save(fn, 'WEBP', quality=74, method=6)
        else: img.save(fn, 'JPEG', quality=82, optimize=True, progressive=True)
        out[name] = (fn, os.path.getsize(fn))
    return out

def clean_who(who):
    who = re.sub(r'\s*\([^)]*\)', '', who or '').strip(' ,.;')
    who = re.sub(r'\s+', ' ', who)
    return who[:60]

def clean_license(lic):
    l = lic or ''
    m = re.search(r'CC BY-SA[ -]?(\d\.\d)?', l, re.I)
    if m: return 'CC BY-SA ' + (m.group(1) or '4.0')
    m = re.search(r'CC BY[ -]?(\d\.\d)?', l, re.I)
    if m: return 'CC BY ' + (m.group(1) or '4.0')
    if re.search(r'CC0', l, re.I): return 'CC0 1.0'
    if re.search(r'public domain', l, re.I): return 'Public domain'
    return l[:40]

def credit_html(c):
    src = c['source'].split(':')[0]
    who = html.escape(clean_who(c.get('photographer')))
    if src == 'pexels':
        return 'Photo: %s via <a href="%s" rel="nofollow noopener" target="_blank">Pexels</a>.' % (who or 'Pexels contributor', html.escape(c['page_url']))
    if src == 'pixabay':
        return 'Photo: %svia <a href="%s" rel="nofollow noopener" target="_blank">Pixabay</a>.' % ((who + ' ') if who else '', html.escape(c['page_url']))
    lic = html.escape(clean_license(c.get('license'))); lu = c.get('license_url') or ''
    lic_html = '<a href="%s" rel="license noopener" target="_blank">%s</a>' % (html.escape(lu), lic) if lu else lic
    if src == 'commons':
        site = 'Wikimedia Commons'
    else:
        host = re.sub(r'^www\.', '', re.sub(r'^https?://([^/]+).*$', r'\1', c['page_url'] or ''))
        site = {'flickr.com': 'Flickr', 'commons.wikimedia.org': 'Wikimedia Commons'}.get(host, host or 'Openverse')
    return 'Photo: %s, %s, via <a href="%s" rel="nofollow noopener" target="_blank">%s</a>.' % (who or 'unknown author', lic_html, html.escape(c['page_url']), site)

def figure(slug, alt, caption, credit, banner=False, priority=True):
    attrs = 'fetchpriority="high"' if priority else 'loading="lazy"'
    return ('<figure class="photo-fig%s" id="photo-%s"><img src="/images/%s-960.webp" srcset="/images/%s-640.webp 640w, /images/%s-960.webp 960w, /images/%s-1200.webp 1200w" '
            'sizes="%s" width="1200" height="800" alt="%s" %s decoding="async"><figcaption>%s %s</figcaption></figure>\n') % (
            ' banner' if banner else '', slug, slug, slug, slug, slug, '(max-width: 1128px) calc(100vw - 48px), 1080px' if banner else '(max-width: 768px) calc(100vw - 48px), 720px',
            html.escape(alt, quote=True), attrs, html.escape(caption), credit)

def og_tags(slug, alt):
    return ('<meta property="og:image" content="%s/images/%s-og.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="800">'
            '<meta property="og:image:alt" content="%s"><meta name="twitter:card" content="summary_large_image">') % (SITE, slug, html.escape(alt, quote=True))

credits = ['# Image credits', '', 'Every photo on retrofitplanner.co.uk is used under a licence that allows commercial use. Files are resized crops of the originals linked below, and each one carries its credit in the caption on the page.', '',
           'Two images are licensed CC BY-SA, which means the cropped versions used here are offered under the same licence. If you reuse or edit those two files elsewhere, keep the credit and the CC BY-SA notice with them. Everything else is Pexels, Pixabay, CC0 or CC BY and carries no share-alike obligation.', '']
touched = set(); total_bytes = 0; placed = {}
for p in picks:
    slug = p['slug']; c = p['chosen']; s = subjects[slug]
    for ch in (p['alt'], p['caption']):
        assert '—' not in ch and '&' not in ch, (slug, 'em dash or ampersand in text')
    thumb = ('href="/guides/%s/" class="guide-item"' % slug) in HUB
    src = fetch(c, slug)
    sizes = process(slug, src, thumb); total_bytes += sum(v[1] for v in sizes.values())
    credits.append('- `%s`: [%s](%s) by %s. Licence: %s%s.' % (slug, c.get('title') or c['id'], c['page_url'], clean_who(c.get('photographer')) or 'unknown', clean_license(c.get('license')) if c['source'].split(':')[0] not in ('pexels', 'pixabay') else c.get('license'), (' (' + c['license_url'] + ')') if c.get('license_url') else ''))
    page = open(s['page'], encoding='utf-8').read()
    credit = credit_html(c)
    if 'id="photo-%s"' % slug in page:
        new_fig = figure(slug, p['alt'], p['caption'], credit, banner=not s['page'].startswith('guides/')).rstrip('\n')
        page, k = re.subn(r'<figure class="photo-fig[^"]*" id="photo-%s">.*?</figure>' % re.escape(slug), lambda m: new_fig, page, count=1, flags=re.S)
        assert k == 1, slug
        action = 'replaced'
    elif s['page'].startswith('guides/'):
        m = re.search(r'</h1>\s*\n?', page); assert m, slug
        fig = figure(slug, p['alt'], p['caption'], credit)
        page = page[:m.end()] + '\n' + fig + page[m.end():]
        action = 'placed'
    else:
        i = page.index('</header>') + len('</header>')
        fig = '<div class="photo-banner">' + figure(slug, p['alt'], p['caption'], credit, banner=True).rstrip('\n') + '</div>\n'
        page = page[:i] + '\n' + fig + page[i:]
        action = 'placed'
    if 'property="og:image"' not in page:
        m = re.search(r'<meta property="og:type"[^>]*>', page)
        if m:
            page = page[:m.end()] + og_tags(slug, p['alt']) + page[m.end():]
        else:
            t = re.search(r'<title>(.*?)</title>', page, re.S)
            d = re.search(r'<meta name="description" content="([^"]*)"[^>]*>', page)
            assert t and d, ('cannot build og tags for', s['page'])
            url = SITE + '/' + s['page'].replace('index.html', '')
            block = ('<meta property="og:title" content="%s"><meta property="og:description" content="%s">'
                     '<meta property="og:url" content="%s"><meta property="og:type" content="article">'
                     '<meta property="og:site_name" content="Retrofit Planner">') % (html.escape(t.group(1).strip(), quote=True), d.group(1), url)
            page = page[:d.end()] + block + og_tags(slug, p['alt']) + page[d.end():]
            print('  built og tags for', s['page'])
    if not dry: open(s['page'], 'w', encoding='utf-8').write(page)
    touched.add(s['page']); placed[slug] = sizes; print(action, slug, {k: v[1] // 1024 for k, v in sizes.items()}, 'KB')

# guides hub thumbnails
hub = open('guides/index.html', encoding='utf-8').read(); n = 0
for slug in placed:
    if not subjects[slug]['page'].startswith('guides/'): continue
    pat = re.compile(r'(<a href="/guides/%s/" class="guide-item">\s*)<div class="gi-(?:icon|thumb)">.*?</div>' % re.escape(slug), re.S)
    hub, k = pat.subn(r'\1<div class="gi-thumb"><img src="/images/%s-240.webp" width="240" height="240" alt="" loading="lazy" decoding="async"></div>' % slug, hub, count=1)
    n += k
if n and not dry: open('guides/index.html', 'w', encoding='utf-8').write(hub); touched.add('guides/index.html')
print('hub thumbnails', n)

# home tool cards
home = open('index.html', encoding='utf-8').read(); n = 0
for slug in placed:
    if subjects[slug]['page'].startswith('guides/'): continue
    pat = re.compile(r'(<a href="/%s/" class="tool-card[^"]*">\s*)(?:<div class="icon">.*?</div>|<img class="tc-img"[^>]*>)\s*' % re.escape(slug), re.S)
    home, k = pat.subn(r'\1<img class="tc-img" src="/images/%s-640.webp" width="640" height="427" alt="" loading="lazy" decoding="async">\n            ' % slug, home, count=1)
    n += k
if n and not dry: open('index.html', 'w', encoding='utf-8').write(home); touched.add('index.html')
print('home card images', n)
if not dry: open('images/CREDITS.md', 'w').write('\n'.join(credits) + '\n')
print('pages touched', len(touched), 'image bytes %.1f MB' % (total_bytes / 1e6))
