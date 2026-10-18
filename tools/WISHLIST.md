# Weekly wish list import: playbook

Reference notes for the weekly task that adds new finds from Lindsay's Amazon wish list "Dopamine"
(https://www.amazon.com/hz/wishlist/ls/2IR35EI732PXF, a public share link, so no sign-in is needed).
The scheduled task's own prompt holds the rules. This file holds the how-to details.

## Files
- `tools/add_finds.py`: adds finds from a JSON file to catalog.js, rx-data.js, index.html, the guide pages,
  guide tile counts and pinkit/plan.json. Skips any ASIN already in the catalog.
- `tools/new-finds-<date>.json`: one file per import (see the 2026-10-18 file for the format).
- `tools/wishlist-skipped.json`: wish list ASINs reviewed and not added, with the reason. Add every
  ASIN you skip. Reasons starting with "recheck" were good fits that failed the Amazon check: try them again.
- `tools/fetch_images.py` + `.github/workflows/fetch-images.yml`: after a push that changes catalog.js,
  a GitHub Action downloads each new product photo (imageSource) into assets/<id>.webp. The cloud sandbox
  can't reach Amazon's image CDN, so never try to download images yourself.

## 1. Read the wish list (built-in browser pane, any amazon.com tab)
Open https://www.amazon.com/hz/wishlist/ls/2IR35EI732PXF and run:

```js
const items=new Map();
const grab=(doc)=>{doc.querySelectorAll('li[data-itemid]').forEach(li=>{const a=li.querySelector('a[id^="itemName_"]');const href=a?.getAttribute('href')||'';const asin=(href.match(/\/dp\/([A-Z0-9]{10})/)||[])[1]||(li.getAttribute('data-reposition-action-params')||'').match(/ASIN:([A-Z0-9]{10})/)?.[1];items.set(li.getAttribute('data-itemid'),{asin,name:(a?.title||a?.textContent||'').trim().slice(0,120)})})};
grab(document);
let next=document.querySelector('input[name="showMoreUrl"]')?.value, n=0;
while(next && n<40){const h=await (await fetch(next,{credentials:'include'})).text();const d=new DOMParser().parseFromString(h,'text/html');grab(d);next=d.querySelector('input[name="showMoreUrl"]')?.value;n++;if(d.querySelector('#endOfListMarker'))break;}
window.__wl=[...items.values()]; window.__wl.length
```

Then filter out ASINs already in catalog.js (from affiliateUrl/source) and in wishlist-skipped.json
(except "recheck" ones): pass that list into the page as a JS array and keep `window.__new`.

## 2. Check each candidate on Amazon (same tab)

```js
const chk=async a=>{const h=await (await fetch('/dp/'+a,{credentials:'include'})).text();const d=new DOMParser().parseFromString(h,'text/html');const li=d.querySelector('#landingImage, #imgBlkFront, #ebooksImgBlkFront, #main-image');
return {img:li?.getAttribute('data-old-hires')||Object.keys(JSON.parse(li?.getAttribute('data-a-dynamic-image')||'{}')).pop()||li?.src,
 cart:!!d.querySelector('#add-to-cart-button, #buy-now-button'),
 avail:(d.querySelector('#availability')?.textContent||'').replace(/\s+/g,' ').trim().slice(0,50),
 brand:(d.querySelector('#bylineInfo')?.textContent||'').replace(/\s+/g,' ').trim().replace(/^(Visit the |Brand: )/,'').replace(/ Store$/,'').slice(0,40),
 title:(d.querySelector('#productTitle')?.textContent||'').trim().slice(0,200),
 bullets:[...d.querySelectorAll('#feature-bullets li span')].map(s=>s.textContent.trim()).filter(Boolean).slice(0,3).join(' / ').slice(0,400)}};
```
Run it a few ASINs at a time with Promise.all. Skip (as "recheck") anything without `cart`, without `img`,
or with 5 or fewer left in stock.

To look at photos, replace the page body with a grid of `<img>` tags (use the `._AC_SL300_.` size) and take
one screenshot. Look before writing a caption: titles are often vague.

## 3. Curate (what fits the site)
Add: playful, giftable, colorful or weird things in the spirit of the site (funny decor, food-shaped
pillows, kitchen gags, desk toys, cheeky candles, quirky wall art). Mildly cheeky is fine and goes in `spicy`.
Skip: plain household staples, generic jewelry/socks/frames, bulk fidget packs, kids-only items, medical or
therapy tools, knockoffs of licensed characters, cannabis or alcohol-concealment products, anything
crude or sexual beyond a wink, and near-duplicates of items already on the site.

## 4. Write the JSON and run the script
Each find: asin, id (kebab-case, unique), name (short, sentence case), brand, caption (one or two playful
sentences naming what it really is), moods (from Weird, Unnecessary, Colorful, Cozy), spicy (optional),
label [dosage, side effects] in pharmacy-label voice, good (one "Good for" sentence), guides (slugs from
pinkit/plan.json; the Halloween guide only Sept and Oct), img (the m.media-amazon.com URL).
No em dashes anywhere. No prices.

`python3 tools/add_finds.py tools/new-finds-<date>.json --date <date>`, then smoke-test index.html and one
guide page in Playwright (Chromium at /opt/pw-browsers/chromium) for JS errors and card counts.
