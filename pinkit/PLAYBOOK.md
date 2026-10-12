# Daily Pinterest pin: playbook

Reference notes for the daily pin task on Lindsay's Dopamine Supply Co. Pinterest account.
The scheduled task's own prompt holds the rules. This file holds the how-to details.

## Files
- `plan.json`: guides, boards, Etsy shop, rotation and rules.
- `log.json`: every pin posted (newest last). Append one entry per pin.
- `pin.html` + `render.mjs`: the pin designer. Run `npm install` here once per session, then
  `node render.mjs specs/<date>-<slug>.json ../pins/<date>-<slug>.jpg`.
  It prints JSON. `overflow:false`, `imagesLoaded:true` and no errors means the pin is good.
- `specs/examples/`: one spec per layout (label, list, bottle, photo). Copy one and edit.
- `photos/`: Lindsay's own design photos (for the photo layout only).

## Site data (in the repo root)
- `catalog.js`: `window.PRODUCTS`, each with id, name, caption, brand, moods. Only `active` ones are live.
- `rx-data.js`: `window.RX_DATA` with `labels[id] = [dosage, side effects]` and `guides[slug] = [product ids]`.
- Each product card on a page has `id="<product id>"`, so `<guide>.html#<id>` links straight to it.

## Picking today's pin
1. Read the last entry type in `log.json` and take the next type from `plan.rotation`.
2. guide: choose a guide that is in season (see `season`), weighting in-season favorites,
   and whose link was not posted in the last 7 days. Pick a layout and angle different from the
   last pin for that guide (check the log). Headline ideas: a specific person ("for the friend who..."),
   a number ("21 weird little..."), a moment ("Secret Santa under $25" only if true), or a joke.
3. product: choose an active product from an in-season guide that has never been pinned (check
   `subject` in the log). Link STRAIGHT TO AMAZON: `https://www.amazon.com/dp/<ASIN>?tag=dopaminesupplyco-20`
   (ASIN from the product's affiliateUrl in catalog.js; never shorten or cloak the link). Board = that guide's
   board. Use the label layout (text only, never Amazon photos): Patient = who it's for, Prescribed = 1 <product>,
   Dosage and Side effects from RX_DATA. The description MUST end with the disclosure line
   "#affiliate · As an Amazon Associate I earn from qualifying purchases." before the hashtags.
4. etsy: open the Etsy shop in the browser pane and list active listings. Pick one whose listing
   was not pinned in the last `repeat_after_days` days. If none qualifies, do a guide pin instead.
   For a new listing photo, open the image URL (i.etsystatic.com, il_794xN size) in the pane, read it
   as base64 with fetch + FileReader, save it into `photos/<listing-slug>.jpg`. Use the photo layout,
   `site` = "Designed by Lindsay · on Etsy", link = the Etsy listing URL.

## Writing
- Title: up to 100 characters, keyword first (what people search), then the hook.
- Description: 2 to 3 sentences that name real items from the guide, then 4 to 5 hashtags.
- Alt text: one plain sentence describing the image.
- No em dashes anywhere. No claims about prices or sales that aren't on the site.
- Amazon pins: put the affiliate disclosure in the description, keep the title free of prices, and never use the words "Amazon's choice" or "best seller".

## Publishing the image
1. Commit the spec and the jpg, push to main. GitHub Pages serves it at
   `https://dopaminesupplyco.com/pins/<file>.jpg` within a minute or two.
2. In the Pinterest tab (browser pane), load it into the upload box with this script,
   retrying every 30 seconds for up to 5 minutes until the image loads. If it still fails, use
   `https://raw.githubusercontent.com/lindsayshhh/dopaminesupplyco/main/pins/<file>.jpg`.

```js
const img=new Image(); img.crossOrigin='anonymous'; img.src=URL+'?x='+Date.now();
await new Promise((r,j)=>{img.onload=r;img.onerror=j});
const c=document.createElement('canvas'); c.width=img.naturalWidth; c.height=img.naturalHeight;
c.getContext('2d').drawImage(img,0,0);
const b=await new Promise(r=>c.toBlob(r,'image/jpeg',0.95));
const inp=document.querySelector('input[type=file]'); const dt=new DataTransfer();
dt.items.add(new File([b],'pin.jpg',{type:'image/jpeg'})); inp.files=dt.files;
inp.dispatchEvent(new Event('change',{bubbles:true}));
```
(Pinterest blocks fetch() to other sites, which is why this uses an image + canvas.)

## Pinterest pin builder (https://www.pinterest.com/pin-creation-tool/)
Pinterest is a high-risk site in the browser pane: each page load needs Lindsay's tap
(`request_access` url https://pinterest.com). Load the page ONCE and do everything on it.
Screenshots there can be stale; trust `find`, `read_page` and javascript checks.
1. Close the "Pin drafts" panel if open. Run the upload script. Wait 3 seconds.
2. Title: `find` "Tell everyone what your Pin is about", click it, type.
3. Description: `find` "Describe your Pin" (the combobox), click, type, then press Escape.
4. Link: `find` "Add a link", click, type.
5. Board: `find` the board name currently shown under Board and click it. Wait 1 second,
   then `find` the board you want and click it. For a new board: `find` "Create board",
   scroll_to and click it, `find` the name box ("Places to Go"), type the name, keep
   "Make this board private" unticked, click "Create".
6. Alt text: `find` "More options", scroll_to and click it, then `find` "Describe your Pin's
   visual details", click, type.
7. Verify with javascript: `#storyboard-selector-title` value, `#storyboardAltText` value,
   `input[type=url]` value, and the text after "Board" in document.body.innerText.
8. `find` "Publish" (the plain one, not "Publish at a later date"), click it, wait 4 seconds.
   Success: the title field is empty again and "Upload your media" shows.
Leave "Show similar products" and "Mark as AI-Modified" as they are.
