#!/usr/bin/env python3
"""Download a candidate photo to a path and print its pixel size. usage: photo_get.py <url> <out.jpg>"""
import sys, subprocess
from PIL import Image
url, out = sys.argv[1], sys.argv[2]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"
r = subprocess.run(['curl', '-sL', '-A', UA, '-e', 'https://www.google.com/', '--max-time', '60', '-o', out, '-w', '%{http_code}', url], capture_output=True, text=True)
try:
    im = Image.open(out); im.load()
    print('http', r.stdout, 'size', im.size[0], 'x', im.size[1], 'mode', im.mode)
except Exception as e:
    print('http', r.stdout, 'FAILED', str(e)[:120]); sys.exit(1)
