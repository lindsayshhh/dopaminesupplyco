#!/usr/bin/env python3
"""Build supply-shop.html, the page where Lindsay sells products directly (dropshipped).

Reads tools/supply-shop.json. Each item shows a "Coming soon" button until it has a
checkoutUrl (a Stripe Payment Link, Shopify Buy link, etc.), then it shows "Buy now".
Header, footer and dialogs are copied from home-decor.html so the page matches the site.

Usage: python3 tools/build_supply_shop.py

Paused 2026-11-19: the page and its "Shop" nav links were removed. To bring it back, run this
script, then re-add <a class="nav-discover" href="supply-shop.html">Shop</a> to the nav, the
quick-nav link, and the sitemap entry.
"""
import html, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
data = json.loads((ROOT / 'tools' / 'supply-shop.json').read_text())
items = data['items']
tpl = (ROOT / 'home-decor.html').read_text()
body_start = tpl[tpl.index('<body>'):tpl.index('<main>')]
body_end = tpl[tpl.index('</main>'):]
e = html.escape


def money(v):
    return f'${v:,.2f}'


def card(i, n):
    buy = (f'<a class="supply-buy" href="{e(i["checkoutUrl"])}" rel="noopener" '
           f'aria-label="Buy {e(i["name"])}, {money(i["price"])}">Buy now <span aria-hidden="true">↗</span></a>'
           if i.get('checkoutUrl') else
           '<span class="supply-soon" aria-disabled="true">Coming soon</span>')
    return (f'<article class="supply-card" id="{e(i["id"])}">'
            f'<div class="supply-photo"><img loading="{"eager" if n < 2 else "lazy"}" decoding="async" '
            f'src="assets/supply/{e(i["id"])}.webp" alt="{e(i["alt"])}" width="640" height="640">'
            f'<span class="supply-tag">Sold here</span></div>'
            f'<div class="supply-body"><span class="supply-kind">{e(i["kind"])}</span>'
            f'<h3>{e(i["name"])}</h3><p>{e(i["caption"])}</p>'
            f'<div class="rx-mini"><div class="rx-mini-band">Label</div><dl>'
            f'<dt>Dosage</dt><dd>{e(i["dosage"])}</dd><dt>Side effects</dt><dd>{e(i["sideEffects"])}</dd>'
            f'</dl></div><div class="supply-buyrow"><span class="supply-price">{money(i["price"])}</span>{buy}</div></div></article>')


live = any(i.get('checkoutUrl') for i in items)
status = 'Now open' if live else 'Opening soon'
title = 'The Supply Shop: Weird Little Finds, Sold Here | Dopamine Supply Co.'
desc = ('Weird little finds you can buy right here: happy pill message capsules, pocket pep talk '
        'crochet pals, glowing dumpling night lights and more from Dopamine Supply Co.')
cards = ''.join(card(i, n) for n, i in enumerate(items))
soon_tile = ('' if live else
             '<div class="supply-card supply-note-card"><span class="supply-pills" aria-hidden="true">'
             '<span class="rx-capsule"><span style="background:#ff8ebd"></span><span style="background:#ffd84d"></span></span>'
             '<span class="rx-capsule"><span style="background:#d8e897"></span><span style="background:#fff9ee"></span></span>'
             '<span class="rx-capsule"><span style="background:#ffd84d"></span><span style="background:#f46b45"></span></span></span>'
             '<h3>Checkout is almost ready.</h3><p>The shelves are stocked and the register is warming up. '
             'Save this page and check back soon.</p>'
             '<a class="supply-buy alt" href="index.html#guides">Browse gift guides <span aria-hidden="true">→</span></a></div>')

page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#fff9ee"><title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta property="og:title" content="The Supply Shop by Dopamine Supply Co."><meta property="og:description" content="{e(desc)}">
<link rel="canonical" href="https://dopaminesupplyco.com/supply-shop.html"><meta property="og:url" content="https://dopaminesupplyco.com/supply-shop.html"><meta property="og:type" content="website"><meta property="og:site_name" content="Dopamine Supply Co."><meta property="og:image" content="https://dopaminesupplyco.com/assets/og/home.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image"><link rel="icon" href="assets/dopamine-logo-transparent.png" type="image/png"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,700;9..40,800&amp;family=Space+Grotesk:wght@500;700&amp;display=swap"><link rel="stylesheet" href="style.css"><link rel="stylesheet" href="capsule.css"><link rel="stylesheet" href="guides.css"><link rel="stylesheet" href="rx.css"><link rel="stylesheet" href="shop.css"><link rel="stylesheet" href="supply.css">
<script src="config.js" defer></script><script src="catalog.js" defer></script><script src="app.js" defer></script>
</head>
{body_start}<main>
<div class="wrap"><p class="crumbs"><a href="index.html">Home</a> / The Supply Shop</p></div>
<header class="guide-hero wrap">
<img class="mascot hero-mascot" src="assets/mascot/point.webp" alt="" aria-hidden="true" width="300" height="400" decoding="async">
<p class="eyebrow"><span class="mini-capsule" aria-hidden="true"></span>The Supply Shop · {status}</p>
<h1>Weird little finds, sold right here.</h1>
<p class="rx-line">Rx: Tiny joys, delivered to your door</p>
<p class="collection-intro">These are a few of my favorite small, silly, happy things, and you can get them straight from me instead of hunting for them somewhere else. Each one earned its spot by making me laugh out loud.</p>
<p class="affiliate-note">{"Checkout is opening soon, so these can't be ordered quite yet. " if not live else ""}Orders ship from my supply partner, so please allow 1 to 3 weeks for delivery.</p>
</header>
<section class="supply wrap" id="products"><div class="supply-grid">{cards}{soon_tile}</div></section>
{body_end}'''

(ROOT / 'supply-shop.html').write_text(page)
print(f'wrote supply-shop.html with {len(items)} items ({"live" if live else "coming soon"})')
