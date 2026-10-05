// The gift prescription quiz. Uses window.PRODUCTS (catalog.js), window.SHOP_CONFIG
// (config.js) and window.RX_DATA (rx-data.js, made by build.mjs).
(() => {
'use strict';
const $ = id => document.getElementById(id);
const root = $('rx');
if (!root || !window.RX_DATA) return;
const D = window.RX_DATA;
const config = window.SHOP_CONFIG || {};
const live = window.PRODUCTS.filter(p => p.active !== false && D.labels[p.id]);
const byId = Object.fromEntries(live.map(p => [p.id, p]));
const esc = v => String(v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const QUESTIONS = [
  { key: 'who', q: "Who's it for?", opts: [
    { id: 'coworker', t: 'A coworker', s: 'Desk buddy or Secret Santa match', c: ['#4754cf', '#fff9ee'] },
    { id: 'bestie', t: 'My best friend', s: 'Knows all my secrets', c: ['#ff8ebd', '#ffd84d'] },
    { id: 'partner', t: 'My partner', s: 'Already has everything', c: ['#f46b45', '#ff8ebd'] },
    { id: 'family', t: 'Family', s: 'Parents, siblings, the cool aunt', c: ['#d8e897', '#eea038'] },
    { id: 'me', t: 'Me, obviously', s: 'Treat yourself', c: ['#ffd84d', '#4754cf'] }
  ] },
  { key: 'vibe', q: "What's their vibe lately?", opts: [
    { id: 'fumes', t: 'Running on fumes', s: 'Needs a nap and a snack', c: ['#ffd84d', '#fff9ee'] },
    { id: 'main', t: 'Main character', s: 'Loud, sparkly, iconic', c: ['#ff8ebd', '#f46b45'] },
    { id: 'cozy', t: 'Cozy goblin', s: 'Blankets, tea, zero plans', c: ['#d8e897', '#eea038'] },
    { id: 'chaos', t: 'Chaos agent', s: 'Will laugh at anything', c: ['#4754cf', '#ff8ebd'] }
  ] },
  { key: 'occ', q: "What's the occasion?", opts: [
    { id: 'halloween', t: 'Spooky season', s: 'Halloween, or every day', c: ['#f46b45', '#26251e'] },
    { id: 'holidays', t: 'The holidays', s: 'Stockings and gift piles', c: ['#d8e897', '#ff8ebd'] },
    { id: 'swap', t: 'A gift swap', s: 'White elephant or Secret Santa', c: ['#ffd84d', '#4754cf'] },
    { id: 'birthday', t: 'Birthday', s: 'Another trip around the sun', c: ['#ff8ebd', '#fff9ee'] },
    { id: 'just', t: 'Just because', s: 'No reason needed', c: ['#eea038', '#d8e897'] }
  ] },
  { key: 'weird', q: 'How weird can they handle?', opts: [
    { id: 'cute', t: 'Cute weird', s: 'Charming, never awkward', c: ['#ff8ebd', '#fff9ee'] },
    { id: 'medium', t: 'Medium weird', s: 'A good laugh, nothing wild', c: ['#ffd84d', '#ff8ebd'] },
    { id: 'full', t: 'Fully unhinged', s: 'The weirder the better', c: ['#4754cf', '#f46b45'] }
  ] }
];

// How each answer nudges the picks: g = gift guides, m = moods, spicy = the cheekier items.
const WEIGHTS = {
  who: {
    coworker: { g: { 'desk-gifts-for-coworkers': 3, 'funny-white-elephant-gifts': 1 }, spicy: -2 },
    bestie: { g: { 'funny-white-elephant-gifts': 1, 'weird-stocking-stuffers': 1, 'dopamine-decor': 1 }, m: { Weird: 1 } },
    partner: { g: { 'funny-throw-pillows': 2, 'dopamine-decor': 1, 'gifts-for-tea-lovers': 1 }, m: { Cozy: 1 } },
    family: { g: { 'weird-kitchen-gadgets': 3, 'gifts-for-tea-lovers': 1 }, spicy: -6 },
    me: { g: { 'dopamine-decor': 2, 'funny-throw-pillows': 1 }, m: { Colorful: 1 } }
  },
  vibe: {
    fumes: { m: { Cozy: 2 }, g: { 'gifts-for-tea-lovers': 2, 'funny-throw-pillows': 1, 'desk-gifts-for-coworkers': 1 } },
    main: { m: { Colorful: 2 }, g: { 'dopamine-decor': 2 } },
    cozy: { m: { Cozy: 3 }, g: { 'funny-throw-pillows': 2, 'gifts-for-tea-lovers': 2 } },
    chaos: { m: { Weird: 3, Unnecessary: 1 }, g: { 'funny-white-elephant-gifts': 2 } }
  },
  occ: {
    halloween: { g: { 'spooky-cute-halloween-gifts': 5 } },
    holidays: { g: { 'weird-stocking-stuffers': 3 } },
    swap: { g: { 'funny-white-elephant-gifts': 3, 'desk-gifts-for-coworkers': 1 } },
    birthday: { g: { 'dopamine-decor': 1, 'funny-throw-pillows': 1, 'weird-stocking-stuffers': 1 } },
    just: { m: { Unnecessary: 1 } }
  },
  weird: {
    cute: { m: { Cozy: 1 }, spicy: -10 },
    medium: { spicy: -3 },
    full: { m: { Weird: 2 }, spicy: 3 }
  }
};
const OCCASION = { halloween: 'Spooky season', holidays: 'The holidays', swap: 'Gift swap', birthday: 'Birthday', just: 'Just because' };
const DIRECTIONS = {
  halloween: 'Take one before October 31. Boo responsibly.',
  holidays: 'Wrap loosely. Open before breakfast.',
  swap: 'Bring to the swap. Expect it to get stolen.',
  birthday: 'Take one with cake. Repeat yearly.',
  just: 'Take one before Monday. Repeat as needed.'
};
const WHO = { coworker: 'coworker', bestie: 'best friend', partner: 'partner', family: 'family member' };
const VIBE_THEM = { fumes: 'running on fumes', main: 'who is the main character', cozy: 'who is a cozy goblin', chaos: 'who is a chaos agent' };
const VIBE_ME = { fumes: 'You, running on fumes', main: 'You, the main character', cozy: 'You, a cozy goblin', chaos: 'You, a chaos agent' };

function patient(a) {
  if (a.who === 'me') return VIBE_ME[a.vibe] || 'You, obviously';
  const noun = WHO[a.who] || 'person';
  return a.vibe ? `The ${noun} ${VIBE_THEM[a.vibe]}` : `Your favorite ${noun}`;
}
const inGuide = (slug, id) => (D.guides[slug] || []).includes(id);
function score(p, a) {
  let s = Math.random() * 1.5;
  for (const [key, val] of Object.entries(a)) {
    const w = WEIGHTS[key] && WEIGHTS[key][val];
    if (!w) continue;
    for (const [slug, n] of Object.entries(w.g || {})) if (inGuide(slug, p.id)) s += n;
    for (const [mood, n] of Object.entries(w.m || {})) if (p.moods.includes(mood)) s += n;
    if (w.spicy && D.spicy.includes(p.id)) s += w.spicy;
  }
  return s;
}
// Last word of the name ("infuser", "pillow") keeps three tea infusers from showing up together.
const kind = p => p.name.toLowerCase().split(/\s+/).pop();
function choose(a, exclude) {
  const ranked = live.filter(p => !exclude.has(p.id)).map(p => [score(p, a), p]).sort((x, y) => y[0] - x[0]);
  const picks = [], kinds = new Set();
  for (const [, p] of ranked) {
    if (kinds.has(kind(p))) continue;
    picks.push(p); kinds.add(kind(p));
    if (picks.length === 3) break;
  }
  return picks;
}
function amazonUrl(p) {
  if (!p.affiliateUrl) return p.source;
  const url = new URL(p.affiliateUrl);
  if (config.amazonTag) url.searchParams.set('tag', config.amazonTag);
  return url.href;
}
function savedIds() {
  try { const v = JSON.parse(localStorage.getItem('dopamine-favorites') || '[]'); return new Set(Array.isArray(v) ? v : []); } catch { return new Set(); }
}
const newRxNo = () => String(Math.floor(1000 + Math.random() * 9000));

let step = 0, answers = {}, picks = [], shown = new Set(), rxNo = newRxNo(), shared = false;
const screens = { start: $('rx-start'), quiz: $('rx-quiz'), result: $('rx-result') };
function show(name) {
  for (const [k, el] of Object.entries(screens)) el.hidden = k !== name;
  window.scrollTo({ top: root.offsetTop - 10, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
}

function renderQuestion() {
  const Q = QUESTIONS[step];
  $('rx-step').textContent = `Question ${step + 1} of ${QUESTIONS.length}`;
  $('rx-dots').innerHTML = QUESTIONS.map((_, i) => `<span class="rx-dot${i <= step ? ' on' : ''}"></span>`).join('');
  $('rx-chips').innerHTML = QUESTIONS.slice(0, step).filter(q => answers[q.key]).map(q => {
    const o = q.opts.find(o => o.id === answers[q.key]);
    return `<span class="rx-chip">${esc(o.t)}</span>`;
  }).join('');
  $('rx-question').textContent = Q.q;
  $('rx-options').innerHTML = Q.opts.map(o => `<button type="button" class="rx-opt" data-opt="${o.id}" aria-pressed="${answers[Q.key] === o.id}"><span class="rx-capsule" aria-hidden="true"><span style="background:${o.c[0]}"></span><span style="background:${o.c[1]}"></span></span><span class="rx-opt-text"><b>${esc(o.t)}</b><small>${esc(o.s)}</small></span><svg class="rx-check" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg></button>`).join('');
  $('rx-next').disabled = !answers[Q.key];
  $('rx-next-label').textContent = step === QUESTIONS.length - 1 ? 'Fill my prescription' : 'Next';
}

function renderResult() {
  const a = answers;
  $('rx-no').textContent = rxNo;
  $('rx-no-band').textContent = rxNo;
  $('rx-title').innerHTML = shared ? 'Someone filled a prescription <span class="rx-joy">for you.</span>' : 'Your prescription is <span class="rx-joy">ready.</span>';
  $('rx-patient').textContent = patient(a);
  $('rx-occasion').textContent = OCCASION[a.occ] || 'Any day ending in Y';
  $('rx-directions').textContent = DIRECTIONS[a.occ] || DIRECTIONS.just;
  const saved = savedIds();
  $('rx-picks').innerHTML = picks.map((p, i) => {
    const [dosage, effects] = D.labels[p.id];
    const on = saved.has(p.id);
    return `<article class="rx-pick">
<div class="rx-pick-img"><button type="button" data-detail="${p.id}" aria-label="View ${esc(p.name)}"><img src="${esc(p.image)}" alt="${esc(p.name)} by ${esc(p.brand)}" loading="lazy" width="400" height="400"></button><span class="pick-no">No. ${i + 1}</span><button class="save-button${on ? ' saved' : ''}" data-save="${p.id}" aria-label="${on ? 'Remove' : 'Save'} ${esc(p.name)} ${on ? 'from' : 'to'} my list" aria-pressed="${on}">${on ? '♥' : '♡'}</button></div>
<div class="rx-pick-body"><h3><button type="button" class="title-button" data-detail="${p.id}">${esc(p.name)}</button></h3><p class="rx-caption">${esc(p.caption)}</p><p><b>Dosage:</b> ${esc(dosage)}</p><p><b>Side effects:</b> ${esc(effects)}</p><a class="rx-buy" href="${esc(amazonUrl(p))}" target="_blank" rel="sponsored noopener noreferrer" aria-label="View ${esc(p.name)} on Amazon (opens a new tab)">View on Amazon <span aria-hidden="true">↗</span></a></div>
</article>`;
  }).join('');
  $('rx-own').hidden = !shared;
  $('rx-refill').hidden = shared;
  $('rx-share-label').textContent = 'Share prescription';
  $('rx-copy').hidden = true;
  updateSaveAll();
}
function updateSaveAll() {
  const saved = savedIds();
  const all = picks.length && picks.every(p => saved.has(p.id));
  $('rx-save-all-label').textContent = all ? 'All 3 saved to my list' : 'Save all 3 to my list';
  $('rx-save-all').classList.toggle('on', !!all);
}
function shareUrl() {
  const a = answers;
  const url = new URL(location.href);
  url.hash = ['rx', a.who || '-', a.vibe || '-', a.occ || '-', a.weird || '-', rxNo, picks.map(p => p.id).join(',')].join('/');
  return url.href;
}
function dispense() {
  picks = choose(answers, shown);
  if (picks.length < 3) { shown = new Set(); picks = choose(answers, shown); }
  picks.forEach(p => shown.add(p.id));
  renderResult();
  show('result');
}
function readShared() {
  const parts = location.hash.replace(/^#/, '').split('/');
  if (parts[0] !== 'rx' || parts.length < 7) return false;
  const ids = parts[6].split(',').filter(id => byId[id]).slice(0, 3);
  if (!ids.length) return false;
  const clean = v => (v && v !== '-' ? v : undefined);
  answers = { who: clean(parts[1]), vibe: clean(parts[2]), occ: clean(parts[3]), weird: clean(parts[4]) };
  rxNo = /^\d{4}$/.test(parts[5]) ? parts[5] : newRxNo();
  picks = ids.map(id => byId[id]);
  picks.forEach(p => shown.add(p.id));
  shared = true;
  renderResult();
  show('result');
  return true;
}
function restart() {
  step = 0; answers = {}; shown = new Set(); shared = false; rxNo = newRxNo();
  history.replaceState(null, '', location.pathname + location.search);
  renderQuestion();
  show('quiz');
}

$('rx-begin').addEventListener('click', () => { step = 0; renderQuestion(); show('quiz'); });
$('rx-options').addEventListener('click', e => {
  const b = e.target.closest('[data-opt]');
  if (!b) return;
  answers[QUESTIONS[step].key] = b.dataset.opt;
  renderQuestion();
  $('rx-next').focus({ preventScroll: true });
});
$('rx-next').addEventListener('click', () => {
  if (!answers[QUESTIONS[step].key]) return;
  if (step < QUESTIONS.length - 1) { step++; renderQuestion(); } else dispense();
});
$('rx-skip').addEventListener('click', () => {
  delete answers[QUESTIONS[step].key];
  if (step < QUESTIONS.length - 1) { step++; renderQuestion(); } else dispense();
});
$('rx-back').addEventListener('click', () => {
  if (step === 0) show('start'); else { step--; renderQuestion(); }
});
$('rx-refill').addEventListener('click', () => { rxNo = newRxNo(); dispense(); });
$('rx-restart').addEventListener('click', restart);
$('rx-own').addEventListener('click', restart);
$('rx-save-all').addEventListener('click', () => {
  const saved = savedIds();
  const all = picks.every(p => saved.has(p.id));
  // Clicking each heart lets the site's own saving code keep the Saved list in sync.
  for (const p of picks) {
    if (saved.has(p.id) === all) root.querySelector(`#rx-picks [data-save="${p.id}"]`)?.click();
  }
  setTimeout(updateSaveAll, 0);
});
$('rx-picks').addEventListener('click', e => { if (e.target.closest('[data-save]')) setTimeout(updateSaveAll, 0); });
$('rx-share').addEventListener('click', async () => {
  const url = shareUrl();
  if (navigator.share) {
    try { await navigator.share({ title: 'My gift prescription · Dopamine Supply Co.', text: `Rx for ${patient(answers).toLowerCase()}: 3 little treats.`, url }); return; }
    catch (err) { if (err.name === 'AbortError') return; }
  }
  try { await navigator.clipboard.writeText(url); $('rx-share-label').textContent = 'Link copied'; }
  catch { $('rx-copy-url').value = url; $('rx-copy').hidden = false; $('rx-copy-url').select(); }
});
$('rx-copy-select').addEventListener('click', () => { $('rx-copy-url').focus(); $('rx-copy-url').select(); });
window.addEventListener('hashchange', () => { if (location.hash.startsWith('#rx/')) readShared(); });

root.classList.add('rx-ready');
readShared();
})();
