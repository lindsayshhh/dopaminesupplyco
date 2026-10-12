// Renders one pin: node render.mjs specs/<name>.json ../pins/<name>.jpg
// Needs: npm install (in this folder). Uses the preinstalled Chromium.
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const [specFile, outFile] = process.argv.slice(2);
if (!specFile || !outFile) { console.error('Usage: node render.mjs <spec.json> <out.jpg>'); process.exit(1); }
const spec = JSON.parse(fs.readFileSync(specFile, 'utf8'));
const nm = path.join(here, 'node_modules');
const fonts = `
@font-face{font-family:'DM Sans';font-weight:100 1000;src:url(file://${nm}/@fontsource-variable/dm-sans/files/dm-sans-latin-wght-normal.woff2) format('woff2')}
@font-face{font-family:'Space Grotesk';font-weight:500;src:url(file://${nm}/@fontsource/space-grotesk/files/space-grotesk-latin-500-normal.woff2) format('woff2')}
@font-face{font-family:'Space Grotesk';font-weight:700;src:url(file://${nm}/@fontsource/space-grotesk/files/space-grotesk-latin-700-normal.woff2) format('woff2')}`;
const exe = ['/opt/pw-browsers/chromium'].find(p => fs.existsSync(p));
const browser = await chromium.launch({ executablePath: exe, args: ['--allow-file-access-from-files'] });
const page = await browser.newPage({ viewport: { width: 1000, height: 1500 } });
const errors = [];
page.on('pageerror', e => errors.push(e.message));
await page.addInitScript(s => { window.SPEC = s; }, spec);
await page.goto('file://' + path.join(here, 'pin.html'));
await page.addStyleTag({ content: fonts });
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(300);
const fit = await page.evaluate(() => window.fitPin());
const loaded = await page.evaluate(() => [...document.images].every(i => i.complete && i.naturalWidth > 0));
await page.screenshot({ path: outFile, type: 'jpeg', quality: 92, clip: { x: 0, y: 0, width: 1000, height: 1500 } });
await browser.close();
console.log(JSON.stringify({ out: outFile, ...fit, imagesLoaded: loaded, errors }));
if (errors.length || !loaded || fit.overflow) process.exitCode = 2;
