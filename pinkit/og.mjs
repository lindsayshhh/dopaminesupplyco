// Renders social share images (1200x630): node og.mjs <specs.json>
// specs.json is a list of { out, chip, head, accent, images, mascot, logo } written by tools/seo_pass.py --og.
// Needs: npm install (in this folder). Uses the preinstalled Chromium.
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const specs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const nm = path.join(here, 'node_modules');
const fonts = `
@font-face{font-family:'DM Sans';font-weight:100 1000;src:url(file://${nm}/@fontsource-variable/dm-sans/files/dm-sans-latin-wght-normal.woff2) format('woff2')}
@font-face{font-family:'Space Grotesk';font-weight:700;src:url(file://${nm}/@fontsource/space-grotesk/files/space-grotesk-latin-700-normal.woff2) format('woff2')}`;
const exe = ['/opt/pw-browsers/chromium'].find(p => fs.existsSync(p));
const browser = await chromium.launch({ executablePath: exe, args: ['--allow-file-access-from-files'] });
const page = await browser.newPage({ viewport: { width: 1200, height: 630 } });
const errors = [];
page.on('pageerror', e => errors.push(e.message));
await page.goto('file://' + path.join(here, 'og.html'));
await page.addStyleTag({ content: fonts });
let failed = 0;
for (const s of specs) {
  await page.evaluate(spec => window.applySpec(spec), s);
  await page.evaluate(() => document.fonts.ready);
  await page.waitForFunction(() => [...document.images].filter(i => i.src && i.style.display !== 'none').every(i => i.complete));
  const fit = await page.evaluate(() => window.fit());
  const loaded = await page.evaluate(() => [...document.images].filter(i => i.src && i.style.display !== 'none').every(i => i.naturalWidth > 0));
  await page.screenshot({ path: s.out, type: 'jpeg', quality: 88, clip: { x: 0, y: 0, width: 1200, height: 630 } });
  console.log(JSON.stringify({ out: path.basename(s.out), ...fit, imagesLoaded: loaded }));
  if (fit.overflow || !loaded) failed++;
}
await browser.close();
if (errors.length) console.log(JSON.stringify({ errors }));
if (failed || errors.length) process.exitCode = 2;
