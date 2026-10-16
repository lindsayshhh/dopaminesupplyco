# Daily Pinterest pin: playbook

Reference notes for the daily pin task on Lindsay's Dopamine Supply Co. Pinterest account.
The scheduled task's own prompt holds the rules. This file holds the how-to details.

## Files
- `plan.json`: guides, boards, Etsy shop, rotation and rules.
- `log.json`: every pin posted (newest last). Append one entry per pin.
- `pin.html` + `render.mjs`: the pin designer (for guide and Etsy pins). Run `npm install` here once per
  session, then `node render.mjs specs/<date>-<slug>.json ../pins/<date>-<slug>.jpg`.
  It prints JSON. `overflow:false`, `imagesLoaded:true` and no errors means the pin is good.
- `specs/examples/`: one spec per layout (label, list, bottle, photo). Copy one and edit.
- `photos/`: Lindsay's own design photos (for the photo layout only).

## Site data (in the repo root)
- `catalog.js`: `window.PRODUCTS`, each with id, name, caption, brand, moods, affiliateUrl. Only `active` ones are live.
- `rx-data.js`: `window.RX_DATA` with `labels[id] = [dosage, side effects]` and `guides[slug] = [product ids]`.
- `notes.json` (in the source folder, if present) or the product caption gives description material.

## Picking today's pin
1. Read the last entry type in `log.json` and take the next type from `plan.rotation`.
2. guide: choose a guide that is in season (see `season`), weighting in-season favorites,
   and whose link was not posted in the last 7 days. Render a new design with a layout and angle
   different from the last pin for that guide (check the log). Headline ideas: a specific person
   ("for the friend who..."), a number ("21 weird little..."), a moment, or a joke.
3. product: choose an active product from an in-season guide that has never been pinned (check
   `subject` in the log). Link STRAIGHT TO AMAZON: `https://www.amazon.com/dp/<ASIN>?tag=dopaminesupplyco-20`
   (ASIN from the product's affiliateUrl; never shorten or cloak the link). Board = that guide's board.
   No design to render: the pin uses Amazon's own main product photo (see "Amazon product check").
   The description MUST include "#affiliate · As an Amazon Associate I earn from qualifying purchases."
   before the hashtags.
4. etsy: list the shop's active listings (https://www.etsy.com/shop/DopamineSupplyCo2026). Pick one
   not pinned in the last `repeat_after_days` days. If none qualifies, do a guide pin instead.
   Use the photo layout with the listing photo saved in `photos/`, `site` = "Designed by Lindsay · on Etsy",
   link = the Etsy listing URL.

## Writing
- Title: up to 100 characters, keyword first (what people search), then the hook.
- Description: 2 to 3 sentences naming real items, then 4 to 5 hashtags.
- Alt text: one plain sentence describing the image.
- No em dashes anywhere. No claims about prices or sales that aren't on the site.
- Amazon pins: affiliate disclosure in the description, no prices in the title, never "Amazon's choice" or "best seller".

## Amazon product check (product pins)
Open one browser pane tab on any amazon.com product page, then in that tab run:

```js
const a='<ASIN>';
const h=await (await fetch('/dp/'+a,{credentials:'include'})).text();
const d=new DOMParser().parseFromString(h,'text/html');
const li=d.querySelector('#landingImage, #imgBlkFront, #ebooksImgBlkFront');
({img:li?.getAttribute('data-old-hires')||Object.keys(JSON.parse(li?.getAttribute('data-a-dynamic-image')||'{}')).pop(),
  cart:!!d.querySelector('#add-to-cart-button, #buy-now-button'),
  avail:(d.querySelector('#availability')?.textContent||'').replace(/\s+/g,' ').trim().slice(0,40)})
```
Skip the product if `cart` is false, there is no image, or availability says only a few are left.
`img` is an m.media-amazon.com URL: use it as the pin image. Close the Amazon tab when done.

## Publishing (all pin types)
Guide and Etsy pin images: commit and push the jpg first. GitHub Pages serves it at
`https://dopaminesupplyco.com/pins/<file>.jpg` within a minute or two (check it loads with an Image() in the page).

Pinterest is a high-risk site in the browser pane: each page load needs Lindsay's tap
(`request_access` url https://pinterest.com). Load https://www.pinterest.com/DopamineSupplyCo/_created/
ONCE and do everything there with javascript (always pass that tab's tabId):

```js
const H={'X-Requested-With':'XMLHttpRequest','Accept':'application/json, text/javascript, */*, q=0.01'};
window.__recent=async()=>{const d=encodeURIComponent(JSON.stringify({options:{username:'DopamineSupplyCo',page_size:25},context:{}}));
  const r=await fetch('/resource/UserPinsResource/get/?source_url=%2FDopamineSupplyCo%2F_created%2F&data='+d,{headers:{...H,'X-Pinterest-PWS-Handler':'www/[username]/_created.js'}});
  return (await r.json()).resource_response.data};
window.__create=async(o)=>{const csrf=document.cookie.match(/csrftoken=([^;]+)/)?.[1];
  const opts={board_id:o.board_id,image_url:o.img,link:o.link,description:o.desc,title:o.title,alt_text:o.alt,method:'button',scrape_metric:{source:'www_url_scrape'}};
  const body=new URLSearchParams({source_url:'/pin/create/button/',data:JSON.stringify({options:opts,context:{}})});
  const r=await fetch('/resource/PinResource/create/',{method:'POST',headers:{...H,'X-CSRFToken':csrf,'Content-Type':'application/x-www-form-urlencoded'},body});
  const j=await r.json();const p=j.resource_response?.data;return {ok:j.resource_response?.status,id:p?.id,board:p?.board?.name,link:p?.link,err:j.resource_response?.error?.message}};
```

Board ids (from `__recent()` pins' `board.id`, or this list):
Gift Ideas 723390827587190977 · Halloween Gift Ideas 723390827587190975 · Stocking Stuffer Ideas 723390827587190978 ·
White Elephant Gift Ideas 723390827587191404 · Dopamine Home 723390827587188684 · Dopamine Kitchen 723390827587188683 ·
True Crime Gifts 723390827587190969 · Dopamine Halloween 723390827587190654

Call `await window.__create({...})` ONCE per pin. Then check `__recent()`: the newest pin must have the
right title, board and link, and the description must contain the disclosure for Amazon pins.
If create returns an error, do not retry blindly: report what it said.

Notes learned:
- Pinterest's "Save from URL" errors on Amazon pages; the create call above (what Amazon's Share button does) works.
- A pin's destination link can't be edited after a share-button save, so get the link right the first time.
- Keep each javascript call under about 40 seconds; for several pins, check results in a separate call.
