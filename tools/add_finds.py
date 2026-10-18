#!/usr/bin/env python3
"""Add new Amazon finds to Dopamine Supply Co.

Usage: python3 tools/add_finds.py tools/new-finds-<date>.json [--date YYYY-MM-DD]

The JSON file is a list of finds:
  {"asin", "id", "name", "brand", "caption", "moods": [...], "spicy": bool (optional),
   "label": [dosage, side effects], "good": "Good for sentence",
   "guides": [guide slugs], "img": "https://m.media-amazon.com/..." (main product photo)}

It updates catalog.js, rx-data.js, index.html (static grid, JSON-LD, count),
each guide page (card, JSON-LD, count), the guide tile counts on every page,
and pinkit/plan.json. Product photos are downloaded and converted to
assets/<id>.webp by the "Fetch product images" GitHub Action after the push
(the cloud sandbox can't reach Amazon's image CDN).
"""
import json, re, sys, datetime, pathlib, html

ROOT = pathlib.Path(__file__).resolve().parent.parent
TAG = 'dopaminesupplyco-20'


def esc(s):
    return html.escape(s, quote=True).replace('&#x27;', '&#39;')


def ld_split(page):
    m = re.search(r'(<script type="application/ld\+json">)(.*?)(</script>)', page, re.S)
    return m, json.loads(m.group(2))


def ld_put(page, m, data):
    return page[:m.start(2)] + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + page[m.end(2):]


def amazon_link(p):
    return (f'<a class="amazon-link" href="{p["affiliateUrl"]}?tag={TAG}" target="_blank" rel="sponsored noopener noreferrer" '
            f'aria-label="View {esc(p["name"])} on Amazon (opens a new tab)">View on Amazon <span aria-hidden="true">↗</span></a>')


def card(p, pick_no=None, label=None, good=None):
    n, i = esc(p['name']), p['id']
    pick = f'<span class="pick-no">No. {pick_no}</span>' if pick_no else ''
    rx = ''
    if label:
        rx = (f'<div class="rx-mini"><div class="rx-mini-band">Label</div><dl><dt>Dosage</dt><dd>{esc(label[0])}</dd>'
              f'<dt>Side effects</dt><dd>{esc(label[1])}</dd><dt>Good for</dt><dd>{esc(good)}</dd></dl></div>')
    return (f'<article class="card" id="{i}"><div class="card-image"><button data-detail="{i}" aria-label="View {n}">'
            f'<img loading="lazy" decoding="async" src="{p["image"]}" alt="{n} by {esc(p["brand"])}" width="400" height="400"></button>'
            f'<button class="save-button" data-save="{i}" aria-label="Save {n} to my list" aria-pressed="false">♡</button>{pick}</div>'
            f'<div class="card-body"><h3><button class="title-button" data-detail="{i}">{n}</button></h3><p>{esc(p["caption"])}</p>'
            f'{rx}{amazon_link(p)}</div></article>')


def main():
    src = pathlib.Path(sys.argv[1])
    date = sys.argv[sys.argv.index('--date') + 1] if '--date' in sys.argv else datetime.date.today().isoformat()
    finds = json.loads(src.read_text())

    # catalog.js
    cpath = ROOT / 'catalog.js'
    c = cpath.read_text()
    a = c.index('['); b = c.index('];\n', a)
    products = json.loads(c[a:b + 1])
    have_ids = {p['id'] for p in products}
    have_asins = {m.group(1) for p in products for m in [re.search(r'/dp/([A-Z0-9]{10})', p.get('affiliateUrl') or p.get('source') or '')] if m}
    added = []
    for f in finds:
        if f['asin'] in have_asins:
            print('skip (already listed):', f['asin'], f['name']); continue
        if f['id'] in have_ids:
            raise SystemExit(f'id already used: {f["id"]}')
        p = {'id': f['id'], 'name': f['name'], 'caption': f['caption'], 'brand': f['brand'], 'moods': f['moods'],
             'referencePrice': None, 'source': f'https://www.amazon.com/dp/{f["asin"]}', 'sourceType': 'amazon',
             'image': f'assets/{f["id"]}.webp', 'imageSource': f.get('img', ''),
             'affiliateUrl': f'https://www.amazon.com/dp/{f["asin"]}', 'amazonVerified': date, 'active': True}
        products.append(p); have_ids.add(p['id']); have_asins.add(f['asin'])
        added.append((p, f))
    if not added:
        print('Nothing new.'); return
    cpath.write_text(c[:a] + json.dumps(products, indent=1, ensure_ascii=False) + c[b + 1:])

    # rx-data.js
    rpath = ROOT / 'rx-data.js'
    r = rpath.read_text()
    k = r.index('{'); e = r.rindex('}')
    rx = json.loads(r[k:e + 1])
    for p, f in added:
        rx['labels'][p['id']] = f['label']
        for g in f['guides']:
            rx['guides'].setdefault(g, []).append(p['id'])
        if f.get('spicy'):
            rx['spicy'].append(p['id'])
    rpath.write_text(r[:k] + json.dumps(rx, ensure_ascii=False, separators=(',', ':')) + r[e + 1:])

    # index.html
    ipath = ROOT / 'index.html'
    s = ipath.read_text()
    marker = '</div><div class="empty" id="empty"'
    assert s.count(marker) == 1
    s = s.replace(marker, ''.join(card(p) for p, _ in added) + marker)
    m, ld = ld_split(s)
    for p, _ in added:
        ld['itemListElement'].append({'@type': 'ListItem', 'position': len(ld['itemListElement']) + 1, 'name': p['name'], 'description': p['caption']})
    s = ld_put(s, m, ld)
    total = s.count('<article class="card"')
    s = re.sub(r'(<span id="results" role="status">)\d+ finds', rf'\g<1>{total} finds', s)
    ipath.write_text(s)

    # guide pages
    counts = {}
    for slug, ids in rx['guides'].items():
        gpath = ROOT / f'{slug}.html'
        if not gpath.exists():
            continue
        new_here = [(p, f) for p, f in added if slug in f['guides']]
        g = gpath.read_text()
        if new_here:
            start = g.index('id="picks"')
            end_marker = '</article></div></section>'
            pos = g.index(end_marker, start) + len('</article>')
            n0 = g[start:pos].count('<article class="card"')
            cards = ''.join(card(p, n0 + i + 1, f['label'], f['good']) for i, (p, f) in enumerate(new_here))
            g = g[:pos] + cards + g[pos:]
            m, ld = ld_split(g)
            for p, _ in new_here:
                ld['itemListElement'].append({'@type': 'ListItem', 'position': len(ld['itemListElement']) + 1, 'name': p['name'], 'description': p['caption']})
            g = ld_put(g, m, ld)
        start = g.index('id="picks"')
        n = g[start:g.index('</section>', start)].count('<article class="card"')
        g = re.sub(r'(Gift guide · )\d+( picks)', rf'\g<1>{n}\g<2>', g, count=1)
        counts[slug] = n
        gpath.write_text(g)

    # guide tile counts on every page
    for h in ROOT.glob('*.html'):
        t = h.read_text(); t0 = t
        for slug, n in counts.items():
            t = re.sub(rf'(href="{slug}\.html"><span class="guide-rx"><span class="mini-capsule" aria-hidden="true"></span>)\d+( picks)', rf'\g<1>{n}\g<2>', t)
        if t != t0:
            h.write_text(t)

    # pinkit/plan.json
    ppath = ROOT / 'pinkit' / 'plan.json'
    plan = json.loads(ppath.read_text())
    for gd in plan['guides']:
        if gd['slug'] in counts:
            gd['picks'] = counts[gd['slug']]
    ppath.write_text(json.dumps(plan, indent=1, ensure_ascii=False))

    print(f'Added {len(added)} finds. Catalog now {len(products)}. Guide counts: {counts}')


if __name__ == '__main__':
    main()
