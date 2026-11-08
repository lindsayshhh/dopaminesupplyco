#!/usr/bin/env python3
"""Build the Home decor section of Dopamine Supply Co. Safe to run any number of times.

Usage: python3 tools/build_decor.py

Reads tools/home-decor.json (room shelves, each a list of product ids) and catalog.js, then:
  - home-decor.html: the room chip bar, every room shelf of cards, and the pick count.
    If the page doesn't exist yet it is created from the dopamine-decor.html page shell.
  - index.html: the "Home decor" room tiles on the homepage (between <!--decor-home--> markers).
  - every page: the "Home decor" link in the main header menu.

tools/add_finds.py runs this before tools/seo_pass.py, and puts a new find on a shelf when its JSON
has a "room" field (one of the room slugs in home-decor.json). Run seo_pass.py after running this
script by hand, so the page's structured data matches the cards.
"""
import datetime, html, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
TAG = 'dopaminesupplyco-20'
PAGE = ROOT / 'home-decor.html'
DATA = ROOT / 'tools' / 'home-decor.json'
NAV_LINK = '<a class="nav-discover" href="home-decor.html">Home decor</a>'

TITLE = 'Funny Home Decor Ideas for Every Room | Dopamine Supply Co.'
DESC = ('Funny home decor and colorful dopamine decor ideas, shopped by room: weird wall art, neon signs, '
        'food-shaped pillows, kitchen towels, shower curtains and quirky vases.')
H1 = 'Funny Home Decor for Every Room'
RX_LINE = 'Rx: One weird little thing per room. Repeat as needed.'
INTRO = ("Your home should make you smile when you walk in. These are the bright, weird and slightly ridiculous "
         "finds I'd put in every room, from a raw chicken vase to a shower curtain with a plot twist. "
         "Pick a room or scroll the whole house.")


def esc(s):
    return html.escape(s, quote=True).replace('&#x27;', '&#39;')


def load():
    c = (ROOT / 'catalog.js').read_text()
    i = c.index('window.PRODUCTS = ') + len('window.PRODUCTS = ')
    products, _ = json.JSONDecoder().raw_decode(c, i)
    by_id = {p['id']: p for p in products if p.get('active') is not False}
    data = json.loads(DATA.read_text())
    rooms = []
    for r in data['rooms']:
        ids = [i for i in r['ids'] if i in by_id]
        rooms.append({**r, 'products': [by_id[i] for i in ids]})
    return rooms


def card(p):
    n, i = esc(p['name']), p['id']
    return (f'<article class="card" id="{i}"><div class="card-image"><button data-detail="{i}" aria-label="View {n}">'
            f'<img loading="lazy" decoding="async" src="{p["image"]}" alt="{n} by {esc(p["brand"])}" width="400" height="400"></button>'
            f'<button class="save-button" data-save="{i}" aria-label="Save {n} to my list" aria-pressed="false">♡</button></div>'
            f'<div class="card-body"><h3><button class="title-button" data-detail="{i}">{n}</button></h3><p>{esc(p["caption"])}</p>'
            f'<a class="amazon-link" href="{p["affiliateUrl"]}?tag={TAG}" target="_blank" rel="sponsored noopener noreferrer" '
            f'aria-label="View {n} on Amazon (opens a new tab)">View on Amazon <span aria-hidden="true">↗</span></a></div></article>')


def guide_name(slug):
    m = re.search(r'<h1>(.*?)</h1>', (ROOT / f'{slug}.html').read_text(), re.S)
    return html.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip() if m else slug


def room_nav(rooms, total):
    chips = [f'<a class="chip room-chip active" href="#picks" data-room="all" aria-current="true">All rooms <span>{total}</span></a>']
    for r in rooms:
        chips.append(f'<a class="chip room-chip" href="#room-{r["slug"]}" data-room="{r["slug"]}">'
                     f'{esc(r["title"])} <span>{len(r["products"])}</span></a>')
    return ('<!--decor-nav--><nav class="room-nav" aria-label="Shop by room"><div class="wrap room-nav-inner">'
            + ''.join(chips) + '</div></nav><!--/decor-nav-->')


def picks(rooms):
    out = ['<section class="collection wrap" id="picks">']
    for r in rooms:
        if not r['products']:
            continue
        more = ''
        if r.get('related') and (ROOT / f'{r["related"]}.html').exists():
            more = (f'<a class="room-more" href="{r["related"]}.html">See the {esc(guide_name(r["related"]).lower())} guide '
                    f'<span aria-hidden="true">→</span></a>')
        out.append(f'<div class="room {r["tile"]}" id="room-{r["slug"]}" data-room="{r["slug"]}">'
                   f'<div class="room-head"><div><span class="room-rx">Rx: {esc(r["rx"])}</span>'
                   f'<h2>{esc(r["title"])}</h2><p>{esc(r["blurb"])}</p></div>{more}</div>'
                   f'<div class="grid guide-grid">{"".join(card(p) for p in r["products"])}</div></div>')
    out.append('</section>')
    return ''.join(out)


def home_tiles(rooms, total):
    tiles = []
    for r in rooms:
        if not r['products']:
            continue
        thumbs = ''.join(f'<img loading="lazy" decoding="async" src="{p["image"]}" alt="" width="160" height="160">'
                         for p in r['products'][:3])
        tiles.append(f'<a class="room-tile {r["tile"]}" href="home-decor.html#room-{r["slug"]}">'
                     f'<div class="room-thumbs" aria-hidden="true">{thumbs}</div>'
                     f'<div class="room-tile-text"><h3>{esc(r["title"])}</h3><span class="room-count">{len(r["products"])} picks</span></div></a>')
    return ('<!--decor-home--><section class="rooms-home wrap" id="home-decor"><div class="section-heading"><div>'
            '<span class="maker-eyebrow"><span class="mini-capsule" aria-hidden="true"></span>New · Home decor</span>'
            '<h2>Home decor, by room.</h2><p class="affiliate-note">Weird wall art, funny pillows and bathroom upgrades. '
            'One little dose of happy for every room.</p></div>'
            f'<a class="solid rooms-all" href="home-decor.html">Shop all {total} <span aria-hidden="true">→</span></a></div>'
            f'<div class="room-tiles">{"".join(tiles)}</div></section><!--/decor-home-->')


def bootstrap():
    """Create home-decor.html from the dopamine-decor.html page shell."""
    s = (ROOT / 'dopamine-decor.html').read_text()
    head_end = s.index('</head>')
    head = s[:head_end]
    head = re.sub(r'<script type="application/ld\+json">.*?</script>', '', head, flags=re.S)
    head = re.sub(r'<title>.*?</title>', f'<title>{esc(TITLE)}</title>', head, count=1, flags=re.S)
    head = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{esc(DESC)}">', head, count=1)
    head = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{esc(H1)}">', head, count=1)
    head = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{esc(DESC)}">', head, count=1)
    head = head.replace('dopamine-decor.html"', 'home-decor.html"').replace('assets/og/dopamine-decor.jpg', 'assets/og/home-decor.jpg')
    head = head.replace('<link rel="stylesheet" href="shop.css">', '<link rel="stylesheet" href="shop.css"><link rel="stylesheet" href="decor.css">')
    head = head.replace('<script src="app.js" defer></script>', '<script src="app.js" defer></script><script src="decor.js" defer></script>')
    body_start = s[head_end:s.index('<main>')]
    tail = s[s.index('</section>\n<section class="rx-promo'):]  # rx promo, more guides, footer, dialogs
    tail = tail[len('</section>'):]
    month = datetime.date.today().strftime('%B %Y')
    main = ('<main>\n<div class="wrap"><p class="crumbs"><a href="index.html">Home</a> / <a href="home-decor.html">Home decor</a></p></div>\n'
            '<header class="guide-hero wrap">\n'
            '<img class="mascot hero-mascot" src="assets/mascot/point.webp" alt="" aria-hidden="true" width="300" height="400" decoding="async">\n'
            f'<p class="eyebrow"><span class="mini-capsule" aria-hidden="true"></span>Home decor · 0 picks · Updated {month}</p>\n'
            f'<h1>{esc(H1)}</h1>\n<p class="rx-line">{esc(RX_LINE)}</p>\n<p class="collection-intro">{esc(INTRO)}</p>\n'
            '<p class="affiliate-note">Links go to Amazon. If you buy something, I earn a small commission at no extra cost to you. '
            'Prices change often, so check Amazon for the current price.</p>\n</header>\n'
            '<!--decor-nav--><!--/decor-nav-->\n<section class="collection wrap" id="picks"></section>')
    PAGE.write_text(head + body_start + main + tail)


def main():
    rooms = load()
    total = sum(len(r['products']) for r in rooms)
    if not PAGE.exists():
        bootstrap()

    g = PAGE.read_text()
    g = re.sub(r'<!--decor-nav-->.*?<!--/decor-nav-->', lambda m: room_nav(rooms, total), g, count=1, flags=re.S)
    a = g.index('<section class="collection wrap" id="picks">')
    b = g.index('</section>', a) + len('</section>')
    g = g[:a] + picks(rooms) + g[b:]
    g = re.sub(r'(Home decor · )\d+( picks)', rf'\g<1>{total}\g<2>', g, count=1)
    PAGE.write_text(g)

    idx = ROOT / 'index.html'
    s = idx.read_text()
    block = home_tiles(rooms, total)
    if '<!--decor-home-->' in s:
        s = re.sub(r'<!--decor-home-->.*?<!--/decor-home-->', lambda m: block, s, count=1, flags=re.S)
    else:
        s = s.replace('<section class="maker wrap" id="shop">', block + '<section class="maker wrap" id="shop">', 1)
    if 'href="decor.css"' not in s:
        s = s.replace('<link rel="stylesheet" href="shop.css">', '<link rel="stylesheet" href="shop.css"><link rel="stylesheet" href="decor.css">', 1)
    idx.write_text(s)

    # "Home decor" in the main header menu, right after "Gift guides"
    for h in ROOT.glob('*.html'):
        t = h.read_text()
        if 'aria-label="Main navigation"' not in t or NAV_LINK in t:
            continue
        t2 = re.sub(r'(<nav aria-label="Main navigation">.*?<a class="nav-discover" href="index\.html#guides">Gift guides</a>)',
                    rf'\g<1>{NAV_LINK}', t, count=1, flags=re.S)
        if t2 != t:
            h.write_text(t2)

    # Keep the pin plan's pick count current
    ppath = ROOT / 'pinkit' / 'plan.json'
    if ppath.exists():
        plan = json.loads(ppath.read_text())
        for gd in plan.get('guides', []):
            if gd.get('slug') == 'home-decor' and gd.get('picks') != total:
                gd['picks'] = total
                ppath.write_text(json.dumps(plan, indent=1, ensure_ascii=False))

    print(f'Home decor: {total} picks across {sum(1 for r in rooms if r["products"])} rooms.')


if __name__ == '__main__':
    main()
