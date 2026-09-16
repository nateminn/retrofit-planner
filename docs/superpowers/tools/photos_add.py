#!/usr/bin/env python3
"""Add a hero photo to guides that have none. Driven by docs/superpowers/tools/photos_add.json.
  photos_add.py search [slug ...]   search candidates, build contact sheets in $SHEETS
  photos_add.py place  [slug ...]   fetch the pick, write images, insert the figure, og tags and hub thumb
json: {slug: {"query":..., "alt":..., "caption":..., "pick": n, "focus": "50% 60%", "precrop": [l,t,r,b]}}"""
import os, sys, json, re, subprocess, hashlib, html
from PIL import Image, ImageOps, ImageDraw

ROOT = os.getcwd()
TOOLS = os.path.join(ROOT, 'docs', 'superpowers', 'tools')
SITE = 'https://www.retrofitplanner.co.uk'
CACHE = os.path.join(ROOT, '.photo-src'); os.makedirs(os.path.join(CACHE, 'cand'), exist_ok=True)
SHEETS = os.environ.get('SHEETS', os.path.join(CACHE, 'sheets')); os.makedirs(SHEETS, exist_ok=True)
spec = json.load(open(os.path.join(TOOLS, 'photos_add.json'), encoding='utf-8'))
mode = sys.argv[1]; slugs = sys.argv[2:] or list(spec)

def thumb_url(c):
    u = c['download_url']
    return re.sub(r'w=\d+', 'w=420', u) if 'images.pexels.com' in u else u

def get(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 8000: return True
    return subprocess.run(['python3', os.path.join(TOOLS, 'photo_get.py'), url, path], capture_output=True, text=True).returncode == 0

if mode == 'search':
    for slug in slugs:
        s = spec[slug]; cp = os.path.join(CACHE, 'cand', slug + '.json')
        if not os.path.exists(cp):
            r = subprocess.run(['python3', os.path.join(TOOLS, 'photo_search.py'), s['query'], '--sources', s.get('sources', 'pexels,pixabay'), '--limit', '8'], capture_output=True, text=True)
            try: cands = json.loads(r.stdout)
            except Exception: print(slug, 'search failed', r.stdout[:80]); continue
            json.dump(cands, open(cp, 'w'), indent=1)
        cands = json.load(open(cp))[:8]; cells = []
        for i, c in enumerate(cands):
            tp = os.path.join(CACHE, 'cand', '%s-%d.jpg' % (slug, i))
            try: im = ImageOps.fit(ImageOps.exif_transpose(Image.open(tp)).convert('RGB'), (300, 200), Image.LANCZOS) if get(thumb_url(c), tp) else Image.new('RGB', (300, 200), (200, 200, 200))
            except Exception: im = Image.new('RGB', (300, 200), (200, 200, 200))
            d = ImageDraw.Draw(im); d.rectangle([0, 0, 34, 24], fill=(0, 0, 0)); d.text((8, 5), str(i), fill=(255, 255, 255)); cells.append(im)
        sheet = Image.new('RGB', (1200, 400), (255, 255, 255))
        for i, im in enumerate(cells): sheet.paste(im, ((i % 4) * 300, (i // 4) * 200))
        sheet.save(os.path.join(SHEETS, slug + '.png'))
        print('%-34s %s' % (slug, ' | '.join('%d %s' % (i, (c.get('title') or '')[:34]) for i, c in enumerate(cands))))

elif mode == 'place':
    credits = []
    hub_path = os.path.join(ROOT, 'guides', 'index.html'); hub = open(hub_path, encoding='utf-8').read()
    for slug in slugs:
        s = spec[slug]
        if 'pick' not in s: print('no pick for', slug); continue
        c = json.load(open(os.path.join(CACHE, 'cand', slug + '.json')))[s['pick']]
        src = os.path.join(CACHE, '%s-%s.jpg' % (slug, hashlib.md5(c['download_url'].encode()).hexdigest()[:12]))
        assert get(c['download_url'], src), ('download failed', slug)
        im = ImageOps.exif_transpose(Image.open(src)).convert('RGB')
        if s.get('precrop'):
            l, t, r, b = s['precrop']; W, H = im.size; im = im.crop((int(W*l), int(H*t), int(W*r), int(H*b)))
        hub_linked = ('href="/guides/%s/"' % slug) in hub
        variants = [('1200', (1200, 800), 'webp'), ('960', (960, 640), 'webp'), ('640', (640, 427), 'webp'), ('og', (1200, 800), 'jpg')]
        if hub_linked: variants.insert(3, ('240', (240, 240), 'webp'))
        for name, (w, h), kind in variants:
            fn = os.path.join(ROOT, 'images', '%s-%s.%s' % (slug, name, kind))
            img = ImageOps.fit(im, (w, h), Image.LANCZOS, centering=(0.5, 0.5))
            if kind == 'webp': img.save(fn, 'WEBP', quality=74, method=6)
            else: img.save(fn, 'JPEG', quality=82, optimize=True, progressive=True)
        who = (c.get('photographer') or '').strip()
        srcname = {'pexels': 'Pexels', 'pixabay': 'Pixabay', 'commons': 'Wikimedia Commons', 'openverse': 'Openverse'}.get(c['source'], c['source'])
        lic = (c.get('license') or '').strip()
        m = re.match(r'(CC BY(?:-SA)?(?:-NC)?)\s*([0-9]\.[0-9])', lic, re.I)
        licpart = ''
        if m:
            url = 'https://creativecommons.org/licenses/%s/%s/' % (m.group(1)[3:].lower(), m.group(2))
            licpart = '<a href="%s" rel="license noopener" target="_blank">%s %s</a>, ' % (url, m.group(1).upper(), m.group(2))
        credit = 'Photo: %s%s<a href="%s" rel="nofollow noopener" target="_blank">%s</a>.' % (
            (html.escape(who) + ', ') if who else '', licpart + ('via ' if licpart or who else ''),
            html.escape(c['page_url'], quote=True), srcname)
        style = ' style="--photo-focus:%s"' % s['focus'] if s.get('focus') else ''
        alt = html.escape(s['alt'], quote=True)
        fig = ('<figure class="photo-fig" id="photo-%s"%s><img src="/images/%s-960.webp" srcset="/images/%s-640.webp 640w, /images/%s-960.webp 960w, /images/%s-1200.webp 1200w" '
               'sizes="(max-width: 768px) calc(100vw - 48px), 720px" width="1200" height="800" alt="%s" fetchpriority="high" decoding="async"><figcaption>%s %s</figcaption></figure>'
               ) % (slug, style, slug, slug, slug, slug, alt, html.escape(s['caption']), credit)
        p = os.path.join(ROOT, 'guides', slug, 'index.html'); page = open(p, encoding='utf-8').read()
        page = re.sub(r'\n?<figure class="photo-fig" id="photo-%s".*?</figure>\n?' % re.escape(slug), '\n', page, flags=re.S)
        page = page.replace('</h1>\n', '</h1>\n\n' + fig + '\n', 1)
        if 'og:image' not in page:
            og = ('<meta property="og:image" content="%s/images/%s-og.jpg">\n<meta property="og:image:width" content="1200">\n'
                  '<meta property="og:image:height" content="800">\n<meta property="og:image:alt" content="%s">\n') % (SITE, slug, alt)
            page = re.sub(r'(<meta property="og:type"[^>]*>\n?)', lambda m: m.group(1) + og, page, count=1)
        open(p, 'w', encoding='utf-8').write(page)
        if hub_linked and ('images/%s-240.webp' % slug) not in hub:
            thumb = '<img class="gi-thumb" src="/images/%s-240.webp" width="240" height="240" alt="" loading="lazy" decoding="async">' % slug
            hub = re.sub(r'(<a href="/guides/%s/" class="guide-item">\s*)' % re.escape(slug), lambda m: m.group(1) + thumb, hub, count=1)
        credits.append('- %s: %s, %s, %s' % (slug, (c.get('title') or c['id'])[:80], c['license'], c['page_url']))
        print('placed', slug, c['source'], c['id'], '(hub thumb)' if hub_linked else '')
    open(hub_path, 'w', encoding='utf-8').write(hub)
    cf = os.path.join(ROOT, 'images', 'CREDITS.md')
    old = open(cf).read() if os.path.exists(cf) else '# Image credits\n\n'
    open(cf, 'w').write(old + '\n'.join(l for l in credits if l.split(':')[0] not in old) + '\n')
