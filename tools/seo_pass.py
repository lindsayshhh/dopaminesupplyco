#!/usr/bin/env python3
"""SEO pass for Dopamine Supply Co. Safe to run any number of times.

Usage: python3 tools/seo_pass.py [--og]

Every run:
  - guide pages: social share tags (og:image -> assets/og/<slug>.jpg, twitter card), an ItemList
    rebuilt from the cards on the page (name, description, image, link to the card), a
    BreadcrumbList, and a "related guides" line under the intro
  - homepage: keyword title and description, Organization + WebSite structured data, share tags
  - quiz page: share tags
  - sitemap.xml with lastmod dates (today for files with uncommitted changes, else last commit date)

--og also renders the 1200x630 share images into assets/og/ (needs `npm install` in pinkit/).
Guide share images use the first four picks on each guide, so they only need re-rendering when
a guide's top picks change or a new guide is added.

tools/add_finds.py runs this (without --og) at the end of every import.
"""
import datetime, html, json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = 'https://dopaminesupplyco.com'
TODAY = datetime.date.today().isoformat()

# Anchor text used when linking to a guide from another guide.
ANCHOR = {
    'advent-calendars': 'fun advent calendars',
    'spooky-cute-halloween-gifts': 'spooky-cute Halloween gifts',
    'weird-stocking-stuffers': 'weird stocking stuffers',
    'funny-white-elephant-gifts': 'funny white elephant gifts',
    'weird-kitchen-gadgets': 'weird kitchen gadgets',
    'funny-throw-pillows': 'funny throw pillows',
    'gifts-for-tea-lovers': 'gifts for tea lovers',
    'desk-gifts-for-coworkers': 'desk gifts for coworkers',
    'dopamine-decor': 'dopamine decor',
    'home-decor': 'funny home decor by room',
    'gifts-under-15': 'gifts under $15',
    'gifts-under-25': 'gifts under $25',
    'gifts-under-50': 'gifts under $50',
    'gifts-for-best-friend': 'gifts for your best friend',
    'gifts-for-mom': 'quirky gifts for mom',
    'gifts-for-him': 'funny gifts for him',
    'gifts-for-person-who-has-everything': 'gifts for the person who has everything',
}
# Three related guides for each guide. Add a row here when you add a guide.
RELATED = {
    'advent-calendars': ['weird-stocking-stuffers', 'gifts-under-50', 'gifts-for-person-who-has-everything'],
    'spooky-cute-halloween-gifts': ['weird-kitchen-gadgets', 'gifts-for-tea-lovers', 'gifts-under-25'],
    'weird-stocking-stuffers': ['gifts-under-15', 'funny-white-elephant-gifts', 'advent-calendars'],
    'funny-white-elephant-gifts': ['gifts-under-25', 'desk-gifts-for-coworkers', 'weird-stocking-stuffers'],
    'weird-kitchen-gadgets': ['gifts-for-mom', 'gifts-for-tea-lovers', 'gifts-under-25'],
    'funny-throw-pillows': ['home-decor', 'dopamine-decor', 'gifts-for-best-friend'],
    'gifts-for-tea-lovers': ['weird-kitchen-gadgets', 'gifts-for-mom', 'gifts-under-15'],
    'desk-gifts-for-coworkers': ['funny-white-elephant-gifts', 'gifts-under-25', 'gifts-under-15'],
    'dopamine-decor': ['home-decor', 'funny-throw-pillows', 'gifts-for-person-who-has-everything'],
    'home-decor': ['dopamine-decor', 'funny-throw-pillows', 'weird-kitchen-gadgets'],
    'gifts-under-15': ['weird-stocking-stuffers', 'gifts-under-25', 'desk-gifts-for-coworkers'],
    'gifts-under-25': ['gifts-under-15', 'gifts-under-50', 'funny-white-elephant-gifts'],
    'gifts-under-50': ['gifts-under-25', 'dopamine-decor', 'gifts-for-person-who-has-everything'],
    'gifts-for-best-friend': ['gifts-under-25', 'funny-throw-pillows', 'gifts-for-person-who-has-everything'],
    'gifts-for-mom': ['weird-kitchen-gadgets', 'gifts-for-tea-lovers', 'dopamine-decor'],
    'gifts-for-him': ['desk-gifts-for-coworkers', 'weird-kitchen-gadgets', 'gifts-under-50'],
    'gifts-for-person-who-has-everything': ['gifts-for-best-friend', 'dopamine-decor', 'gifts-under-50'],
}

# Gift guide tiles. The tile blocks on the homepage, the quiz page and every guide's "More gift guides"
# section are rebuilt from this, with pick counts read from each guide page. Add a row when you add a guide.
TILES = {
    'spooky-cute-halloween-gifts': ('t-orange', 'Spooky-cute gifts', 'For people who decorate in September.'),
    'advent-calendars': ('t-green', 'Advent calendars', 'One tiny surprise a day until Christmas.'),
    'weird-stocking-stuffers': ('t-pink', 'Stocking stuffers', 'Small enough to fit. Weird enough to remember.'),
    'funny-white-elephant-gifts': ('t-yellow', 'White elephant gifts', 'The gift that gets stolen twice.'),
    'gifts-for-best-friend': ('t-pink', 'For your best friend', 'For the one who gets the joke.'),
    'gifts-for-mom': ('t-lavender', 'For mom', 'Cheerful, cozy and actually useful.'),
    'gifts-for-him': ('t-blue', 'For him', 'Desk toys, kitchen gear and a goose.'),
    'gifts-for-person-who-has-everything': ('t-orange', 'Has everything', "They definitely don't have a raw chicken vase."),
    'desk-gifts-for-coworkers': ('t-lavender', 'Coworker gifts', 'For the eight hours you spend there.'),
    'gifts-for-tea-lovers': ('t-blue', 'Gifts for tea lovers', 'Tiny friends who live in your mug.'),
    'gifts-under-15': ('t-yellow', 'Under $15', 'Big laugh. Tiny receipt.'),
    'gifts-under-25': ('t-green', 'Under $25', 'The Secret Santa sweet spot.'),
    'gifts-under-50': ('t-mint', 'Under $50', "For when they're worth a little more."),
    'weird-kitchen-gadgets': ('t-green', 'Weird kitchen gadgets', 'Funny tools that still do the job.'),
    'dopamine-decor': ('t-amber', 'Dopamine decor', 'Bright, loud and a little ridiculous.'),
    'funny-throw-pillows': ('t-mint', 'Funny pillows', 'Soft, squishy and a little absurd.'),
}
TILE_GROUPS = [
    ('For the holidays', ['spooky-cute-halloween-gifts', 'advent-calendars', 'weird-stocking-stuffers', 'funny-white-elephant-gifts']),
    ('By person', ['gifts-for-best-friend', 'gifts-for-mom', 'gifts-for-him', 'gifts-for-person-who-has-everything',
                   'desk-gifts-for-coworkers', 'gifts-for-tea-lovers']),
    ('By budget', ['gifts-under-15', 'gifts-under-25', 'gifts-under-50']),
    ('By vibe', ['weird-kitchen-gadgets', 'dopamine-decor', 'funny-throw-pillows']),
]
# Seasonal guides only get a tile in these months (the pages themselves stay live and in the sitemap).
TILE_MONTHS = {'spooky-cute-halloween-gifts': {9, 10}}
HOME_GUIDES_NOTE = 'Shop by holiday, person, budget or vibe.'
HOME_GRID_LIMIT = 24  # cards in the homepage's static grid; app.js shows the rest with "Show more"

QUICK_NAV = ('<nav class="quick-nav" aria-label="Quick links"><a href="index.html#guides">Gift guides</a>'
             '<a href="home-decor.html">Home decor</a><a href="prescription.html">Gift quiz</a>'
             '<a href="index.html#shop">My designs</a><a href="index.html#collection">Browse</a></nav>')

# Hub pages that use the guide layout but aren't gift guides: their own breadcrumb trail and share-image chip.
HUBS = {'home-decor': ('Home decor', 'home-decor.html')}

HOME_TITLE ='Weird Gifts and Funny Gift Ideas | Dopamine Supply Co.'
HOME_DESC = ('Weird gifts and funny gift ideas for your very specific people. Browse playful finds, '
             'gift guides by budget and recipient, and a gift prescription quiz.')
HOME_OG_TITLE = 'Dopamine Supply Co.: weird gifts and funny gift ideas'
HOME_INTRO_OLD = 'A curated collection of playful finds for your daily dose of dopamine.'
HOME_INTRO_NEW = 'Weird gifts, funny gift ideas and playful finds for your daily dose of dopamine.'
SAME_AS = ['https://dopaminesupplyco2026.etsy.com']


def esc(s):
    return html.escape(s, quote=True).replace('&#x27;', '&#39;')


def unesc(s):
    return html.unescape(re.sub(r'<[^>]+>', '', s)).strip()


def ld_tag(data):
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + '</script>'


def ld_blocks(page):
    """(match, parsed json) for every JSON-LD block on the page."""
    out = []
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', page, re.S):
        out.append((m, json.loads(m.group(1))))
    return out


def set_ld(page, typ, data, after_pattern=None):
    """Replace the JSON-LD block of this @type, or insert it after the last JSON-LD block."""
    for m, d in ld_blocks(page):
        if d.get('@type') == typ:
            return page[:m.start()] + ld_tag(data) + page[m.end():]
    blocks = ld_blocks(page)
    pos = blocks[-1][0].end() if blocks else page.index('</head>')
    return page[:pos] + ld_tag(data) + page[pos:]


def drop_ld(page, typ):
    for m, d in ld_blocks(page):
        if d.get('@type') == typ:
            return page[:m.start()] + page[m.end():]
    return page


def set_share_tags(page, image, alt, og_type):
    """Rewrite og:image (+ size and alt), og:type, og:site_name and the twitter card. Idempotent."""
    page = re.sub(r'<meta (?:property="og:(?:image(?::[a-z]+)?|type|site_name)"|name="twitter:[a-z]+") content="[^"]*">', '', page)
    tags = (f'<meta property="og:type" content="{og_type}"><meta property="og:site_name" content="Dopamine Supply Co.">'
            f'<meta property="og:image" content="{SITE}/{image}"><meta property="og:image:width" content="1200">'
            f'<meta property="og:image:height" content="630"><meta property="og:image:alt" content="{esc(alt)}">'
            f'<meta name="twitter:card" content="summary_large_image">')
    m = re.search(r'<meta property="og:url" content="[^"]*">', page)
    return page[:m.end()] + tags + page[m.end():]


def guide_pages():
    return sorted(p for p in ROOT.glob('*.html') if 'id="picks"' in p.read_text())


def guide_names():
    """Short guide names from the tile list, e.g. 'Under $25'."""
    return {slug: t[1] for slug, t in TILES.items()}


def pick_count(slug):
    m = re.search(r'Gift guide · (\d+) picks', (ROOT / f'{slug}.html').read_text())
    return int(m.group(1)) if m else 0


def tile_groups_html(exclude=None, countdown=False):
    month = datetime.date.today().month
    out = []
    for title, slugs in TILE_GROUPS:
        tiles = []
        for slug in slugs:
            if slug == exclude or not (ROOT / f'{slug}.html').exists():
                continue
            if slug in TILE_MONTHS and month not in TILE_MONTHS[slug]:
                continue
            color, name, blurb = TILES[slug]
            tiles.append(f'<a class="guide-tile {color}" href="{slug}.html"><span class="guide-rx"><span class="mini-capsule" '
                         f'aria-hidden="true"></span>{pick_count(slug)} picks</span><h3>{esc(name)}</h3><p>{esc(blurb)}</p>'
                         f'<span class="go">Open the guide <span aria-hidden="true">→</span></span></a>')
        if not tiles:
            continue
        extra = ' <span class="countdown" data-countdown hidden></span>' if countdown and title == 'For the holidays' else ''
        out.append(f'<div class="guide-group"><h3 class="guide-group-title">{title}{extra}</h3>'
                   f'<div class="guide-tiles">{"".join(tiles)}</div></div>')
    return ''.join(out)


def set_tiles(page, exclude=None, countdown=False):
    """Replace the guide groups in the page's tile section (homepage #guides or a 'more-guides' section)."""
    i = page.find('class="guide-tile')
    if i < 0:
        return page
    sec = page.rfind('<section', 0, i)
    start = page.index('<div class="guide-group">', sec)
    end = page.index('</section>', start)
    return page[:start] + tile_groups_html(exclude, countdown) + page[end:]


def set_quick_nav(page):
    page = re.sub(r'<nav class="quick-nav".*?</nav>', '', page, flags=re.S)
    return page.replace('</header>', '</header>' + QUICK_NAV, 1) if '</header>' in page else page


def active_products():
    s = (ROOT / 'catalog.js').read_text()
    i = s.index('window.PRODUCTS = ') + len('window.PRODUCTS = ')
    products, _ = json.JSONDecoder().raw_decode(s, i)
    return sum(1 for p in products if p.get('active') is not False)


def trim_home_grid(s):
    """Keep the first HOME_GRID_LIMIT cards in the static grid and add the Show more button."""
    a = s.index('<div class="grid" id="grid">') + len('<div class="grid" id="grid">')
    b = s.index('</div><div class="empty" id="empty"', a)
    grid_cards = re.findall(r'<article class="card".*?</article>', s[a:b], re.S)
    s = s[:a] + ''.join(grid_cards[:HOME_GRID_LIMIT]) + s[b:]
    n = active_products()
    s = re.sub(r'(<span id="results" role="status">)\d+ finds', rf'\g<1>{n} finds', s)
    s = re.sub(r'<div class="more-line">.*?</div>', '', s, flags=re.S)
    more = '<div class="more-line"><button class="solid" id="show-more" type="button" hidden>Show more finds</button></div>'
    c = s.index('id="collection"')
    p = s.index('<p class="price-note">', c)
    return s[:p] + more + s[p:]


def cards(page):
    """Cards in the picks section, in page order: id, name, caption, image."""
    start = page.index('id="picks"')
    sec = page[start:page.index('</section>', start)]
    out = []
    for m in re.finditer(r'<article class="card" id="([^"]+)">(.*?)</article>', sec, re.S):
        body = m.group(2)
        name = unesc(re.search(r'<h3>(.*?)</h3>', body, re.S).group(1))
        cap = re.search(r'<div class="card-body"><h3>.*?</h3><p>(.*?)</p>', body, re.S)
        img = re.search(r'<img[^>]*src="(assets/[^"]+)"', body)
        out.append({'id': m.group(1), 'name': name, 'caption': unesc(cap.group(1)) if cap else '',
                    'image': img.group(1) if img else None})
    return out


def do_guide(path, names):
    slug = path.stem
    g = path.read_text()
    h1 = unesc(re.search(r'<h1>(.*?)</h1>', g, re.S).group(1))
    url = f'{SITE}/{path.name}'

    # Share tags
    kind = 'home decor guide' if slug in HUBS else 'gift guide'
    g = set_share_tags(g, f'assets/og/{slug}.jpg', f'{h1}, a Dopamine Supply Co. {kind}', 'article')

    # ItemList rebuilt from the cards
    items = []
    for i, c in enumerate(cards(g), 1):
        it = {'@type': 'ListItem', 'position': i, 'name': c['name'], 'url': f'{url}#{c["id"]}'}
        if c['image']:
            it['image'] = f'{SITE}/{c["image"]}'
        if c['caption']:
            it['description'] = c['caption']
        items.append(it)
    g = set_ld(g, 'ItemList', {'@context': 'https://schema.org', '@type': 'ItemList', 'name': h1,
                               'numberOfItems': len(items), 'itemListElement': items})

    # Breadcrumbs, matching the visible "Home / Gift guides" trail
    if slug in HUBS:
        trail = [{'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': f'{SITE}/'},
                 {'@type': 'ListItem', 'position': 2, 'name': HUBS[slug][0], 'item': url}]
    else:
        trail = [{'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': f'{SITE}/'},
                 {'@type': 'ListItem', 'position': 2, 'name': 'Gift guides', 'item': f'{SITE}/index.html#guides'},
                 {'@type': 'ListItem', 'position': 3, 'name': names.get(slug, h1), 'item': url}]
    g = set_ld(g, 'BreadcrumbList', {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': trail})

    # Related guides line under the intro
    g = re.sub(r'\n*<p class="related-guides">.*?</p>', '', g, flags=re.S)
    rel = [r for r in RELATED.get(slug, []) if (ROOT / f'{r}.html').exists()]
    if rel:
        links = [f'<a href="{r}.html">{esc(ANCHOR[r])}</a>' for r in rel]
        line = ', '.join(links[:-1]) + (' and ' if len(links) > 1 else '') + links[-1]
        note = re.search(r'<p class="affiliate-note">.*?</p>', g[g.index('class="guide-hero'):], re.S)
        pos = g.index('class="guide-hero') + note.end()
        g = g[:pos] + f'\n<p class="related-guides">Also worth a look: {line}.</p>' + g[pos:]

    g = set_tiles(g, exclude=slug)
    g = set_quick_nav(g)
    path.write_text(g)
    return slug, h1, cards(g)


def do_home():
    p = ROOT / 'index.html'
    s = p.read_text()
    s = re.sub(r'<title>.*?</title>', f'<title>{esc(HOME_TITLE)}</title>', s, count=1, flags=re.S)
    s = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{esc(HOME_DESC)}">', s, count=1)
    s = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{esc(HOME_OG_TITLE)}">', s, count=1)
    s = s.replace(f'<p class="collection-intro">{HOME_INTRO_OLD}</p>', f'<p class="collection-intro">{HOME_INTRO_NEW}</p>')
    s = set_share_tags(s, 'assets/og/home.jpg', 'Dopamine Supply Co. weird gifts and funny gift ideas', 'website')
    # The 270-item product list gave search engines nothing to link to; describe the site instead.
    s = drop_ld(s, 'ItemList')
    s = set_ld(s, 'Organization', {'@context': 'https://schema.org', '@type': 'Organization', '@id': f'{SITE}/#org',
                                   'name': 'Dopamine Supply Co.', 'url': f'{SITE}/',
                                   'logo': f'{SITE}/assets/dopamine-logo-transparent.png', 'sameAs': SAME_AS})
    s = set_ld(s, 'WebSite', {'@context': 'https://schema.org', '@type': 'WebSite', '@id': f'{SITE}/#website',
                              'name': 'Dopamine Supply Co.', 'url': f'{SITE}/', 'publisher': {'@id': f'{SITE}/#org'}})
    s = re.sub(r'(<section class="guides-home wrap" id="guides"><div class="section-heading"><div><h2>Gift guides\.</h2>'
               r'<p class="affiliate-note">)[^<]*(</p>)', rf'\g<1>{esc(HOME_GUIDES_NOTE)}\g<2>', s, count=1)
    s = set_tiles(s, countdown=True)
    s = set_quick_nav(s)
    s = trim_home_grid(s)
    p.write_text(s)


def do_quiz():
    p = ROOT / 'prescription.html'
    s = p.read_text()
    s = set_share_tags(s, 'assets/og/prescription.jpg', 'Gift prescription quiz from Dopamine Supply Co.', 'website')
    s = set_tiles(s)
    s = set_quick_nav(s)
    p.write_text(s)


def do_404():
    p = ROOT / '404.html'
    if p.exists():
        p.write_text(set_quick_nav(p.read_text()))


def lastmod(path):
    rel = str(path.relative_to(ROOT))
    if subprocess.run(['git', 'status', '--porcelain', '--', rel], cwd=ROOT, capture_output=True, text=True).stdout.strip():
        return TODAY
    d = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', rel], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return d or TODAY


def do_sitemap(guides):
    pages = [ROOT / 'index.html', ROOT / 'prescription.html'] + guides
    rows = []
    for p in pages:
        loc = f'{SITE}/' if p.name == 'index.html' else f'{SITE}/{p.name}'
        rows.append(f'<url><loc>{loc}</loc><lastmod>{lastmod(p)}</lastmod></url>')
    (ROOT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                                      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                      + '\n'.join(rows) + '\n</urlset>\n')


def render_og(guides_info, names):
    out = ROOT / 'assets' / 'og'
    out.mkdir(exist_ok=True)
    base = f'file://{ROOT}'
    specs = []

    def imgs(cs):
        return [f'{base}/{c["image"]}' for c in cs if c['image'] and (ROOT / c['image']).exists()][:4]

    for slug, h1, cs in guides_info:
        g = (ROOT / f'{slug}.html').read_text()
        n = len(cs)
        mascot = re.search(r'hero-mascot" src="([^"]+)"', g)
        words = h1.split()
        two = len(words) > 3 and words[-2].lower() not in {'and', 'for', 'the', 'of', 'to', 'a', 'who', 'that'}
        chip = f'{HUBS[slug][0]} · {n} picks' if slug in HUBS else f'Gift guide · {n} picks'
        if slug in HUBS:  # one photo from each of the first rooms, so the image isn't all one kind of thing
            firsts = {}
            for m in re.finditer(r'<div class="room[^"]*" id="room-([^"]+)".*?<img[^>]*src="(assets/[^"]+)"', g, re.S):
                firsts.setdefault(m.group(1), m.group(2))
            pick = [{'image': i} for r, i in firsts.items() if r in ('lights', 'cozy', 'plants', 'bathroom')]
            cs = pick + cs
        specs.append({'out': str(out / f'{slug}.jpg'), 'chip': chip, 'head': h1,
                      'accent': ' '.join(words[-2:]) if two else words[-1],
                      'images': imgs(cs), 'mascot': f'{base}/{mascot.group(1)}' if mascot else '',
                      'logo': f'{base}/assets/dopamine-logo-transparent.png'})
    home_cards = cards((ROOT / 'index.html').read_text().replace('id="collection"', 'id="picks"', 1))
    specs.append({'out': str(out / 'home.jpg'), 'chip': 'Weird gifts · funny finds', 'head': 'Weird little finds. Big little joy.',
                  'accent': 'Big little joy.', 'images': imgs(home_cards), 'mascot': f'{base}/assets/mascot/wave.webp',
                  'logo': f'{base}/assets/dopamine-logo-transparent.png'})
    specs.append({'out': str(out / 'prescription.jpg'), 'chip': 'Gift quiz · 4 questions', 'head': 'Get a gift prescription.',
                  'accent': 'prescription.', 'images': imgs(home_cards[4:]), 'mascot': f'{base}/assets/mascot/thumbs-up.webp',
                  'logo': f'{base}/assets/dopamine-logo-transparent.png'})
    spec_file = ROOT / 'pinkit' / 'og-specs.json'
    spec_file.write_text(json.dumps(specs, indent=1))
    try:
        r = subprocess.run(['node', str(ROOT / 'pinkit' / 'og.mjs'), str(spec_file)], cwd=ROOT / 'pinkit')
    finally:
        spec_file.unlink()
    if r.returncode:
        raise SystemExit('Share image render had problems (see above).')


def main():
    names = guide_names()
    guides = guide_pages()
    info = [do_guide(p, names) for p in guides]
    do_home()
    do_quiz()
    do_404()
    if '--og' in sys.argv:
        render_og(info, names)
    do_sitemap(guides)
    print(f'SEO pass done: {len(guides)} guides, homepage, quiz page, sitemap.')


if __name__ == '__main__':
    main()
