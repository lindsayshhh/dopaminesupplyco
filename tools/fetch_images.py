#!/usr/bin/env python3
"""Download missing product photos into assets/<id>.webp (900x900, white background).

Runs in the "Fetch product images" GitHub Action. Reads catalog.js and fetches
imageSource for every product whose image file doesn't exist yet.
"""
import io, json, pathlib, sys, time, urllib.request
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
c = (ROOT / 'catalog.js').read_text()
a = c.index('['); b = c.index('];\n', a)
products = json.loads(c[a:b + 1])
missing = [p for p in products if p.get('image', '').startswith('assets/') and not (ROOT / p['image']).exists() and p.get('imageSource')]
print(f'{len(missing)} images to fetch')
failed = []
for p in missing:
    url = p['imageSource']
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'})
        data = urllib.request.urlopen(req, timeout=30).read()
        im = Image.open(io.BytesIO(data)).convert('RGBA')
        im.thumbnail((900, 900), Image.LANCZOS)
        canvas = Image.new('RGB', (900, 900), (255, 255, 255))
        canvas.paste(im, ((900 - im.width) // 2, (900 - im.height) // 2), im)
        out = ROOT / p['image']
        out.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(out, 'WEBP', quality=82, method=6)
        print('ok  ', p['id'], out.stat().st_size)
    except Exception as e:
        failed.append(p['id']); print('FAIL', p['id'], url, e)
    time.sleep(0.5)
if failed:
    print('Failed:', ', '.join(failed)); sys.exit(1 if len(failed) == len(missing) else 0)
