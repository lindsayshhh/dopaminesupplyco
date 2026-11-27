// Name That Side Effect: match a product's Rx "side effects" line to its photo.
// Uses window.PRODUCTS (catalog.js), window.SHOP_CONFIG (config.js) and
// window.RX_DATA (rx-data.js). New products join the game once they have a label.
(() => {
'use strict';
const $ = id => document.getElementById(id);
const root = $('se');
if (!root || !window.RX_DATA || !window.PRODUCTS) return;
const D = window.RX_DATA;
const config = window.SHOP_CONFIG || {};
const live = window.PRODUCTS.filter(p => p.active !== false && D.labels[p.id]);
const esc = v => String(v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const ROUNDS = 10;
const effect = p => D.labels[p.id][1];
const dosage = p => D.labels[p.id][0];
// Last word of the name ("infuser", "pillow") keeps look-alikes out of the same round.
const kind = p => p.name.toLowerCase().split(/\s+/).pop();
const shuffle = list => { const a = [...list]; for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
// Only products whose side effect is unique can be the answer, so every question is fair.
const effectCount = live.reduce((m, p) => m.set(effect(p), (m.get(effect(p)) || 0) + 1), new Map());
const askable = live.filter(p => effectCount.get(effect(p)) === 1);

function amazonUrl(p) {
  if (!p.affiliateUrl) return p.source;
  const url = new URL(p.affiliateUrl);
  if (config.amazonTag) url.searchParams.set('tag', config.amazonTag);
  return url.href;
}
const buyLink = (p, cls) => `<a class="${cls}" href="${esc(amazonUrl(p))}" target="_blank" rel="${p.affiliateUrl ? 'sponsored ' : ''}noopener noreferrer" aria-label="View ${esc(p.name)} ${p.affiliateUrl ? 'on Amazon' : 'at ' + esc(p.brand)} (opens a new tab)">${p.affiliateUrl ? 'View on Amazon' : 'View at ' + esc(p.brand)} <span aria-hidden="true">↗</span></a>`;
function savedIds() {
  try { const v = JSON.parse(localStorage.getItem('dopamine-favorites') || '[]'); return new Set(Array.isArray(v) ? v : []); } catch { return new Set(); }
}
// The site's app.js listens for clicks on [data-save] and keeps hearts and the Saved list in sync.
const heart = (p, cls = 'save-button') => { const on = savedIds().has(p.id); return `<button type="button" class="${cls}${on ? ' saved' : ''}" data-save="${p.id}" aria-label="${on ? 'Remove' : 'Save'} ${esc(p.name)} ${on ? 'from' : 'to'} my list" aria-pressed="${on}">${on ? '♥' : '♡'}</button>`; };
const getBest = () => { try { return Number(localStorage.getItem('dopamine-side-effects-best')) || 0; } catch { return 0; } };
const setBest = n => { try { localStorage.setItem('dopamine-side-effects-best', String(n)); } catch {} };

const DIAGNOSES = [
  { min: 10, title: 'Licensed dopamine pharmacist.', note: 'Perfect score. You know these weird little things better than we do.', mascot: 'thumbs-up' },
  { min: 8, title: 'Dangerously high dopamine.', note: 'Side effects include knowing far too much about novelty gifts.', mascot: 'thumbs-up' },
  { min: 6, title: 'Healthy levels of whimsy.', note: 'Your joy is within the normal range. Keep taking it daily.', mascot: 'wave' },
  { min: 4, title: 'Mild whimsy deficiency.', note: 'Nothing serious. We recommend a long browse and a giant dumpling pillow.', mascot: 'wave' },
  { min: 0, title: 'Severe joy deficiency.', note: 'Refill immediately. Directions: play again, then browse the finds.', mascot: 'wave' }
];
const diagnose = n => DIAGNOSES.find(d => n >= d.min);
const CHEERS = ['Correct.', 'Nailed it.', 'Exactly right.', 'Yes, that one.', 'Correct diagnosis.'];
const OOPS = ['Not quite.', 'Close, but no.', 'Wrong bottle.', 'Misdiagnosis.'];
const pickOne = list => list[Math.floor(Math.random() * list.length)];

let rounds = [], round = 0, score = 0, streak = 0, results = [], hinted = false, hints = 0, answered = false, rxNo = '';
const screens = { start: $('se-start'), play: $('se-play'), end: $('se-end') };
function show(name) {
  for (const [k, el] of Object.entries(screens)) el.hidden = k !== name;
  window.scrollTo({ top: root.offsetTop - 10, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
}

function buildRounds() {
  const answers = [], usedKinds = new Set();
  for (const p of shuffle(askable)) {
    if (usedKinds.has(kind(p))) continue;
    answers.push(p); usedKinds.add(kind(p));
    if (answers.length === ROUNDS) break;
  }
  return answers.map(answer => {
    const kinds = new Set([kind(answer)]), options = [answer];
    for (const p of shuffle(live)) {
      if (p.id === answer.id || kinds.has(kind(p)) || effect(p) === effect(answer)) continue;
      options.push(p); kinds.add(kind(p));
      if (options.length === 4) break;
    }
    return { answer, options: shuffle(options) };
  });
}

function renderDots() {
  $('se-dots').innerHTML = rounds.map((_, i) => {
    const r = results[i];
    const cls = r === undefined ? (i === round ? ' now' : '') : r ? ' hit' : ' miss';
    return `<span class="se-dot${cls}"></span>`;
  }).join('');
}
function renderRound() {
  const r = rounds[round];
  answered = false; hinted = false;
  $('se-round').textContent = `Round ${round + 1} of ${ROUNDS}`;
  $('se-score').textContent = score;
  $('se-streak').textContent = streak >= 2 ? `${streak} in a row` : '';
  $('se-rxno').textContent = `Rx No. ${rxNo}-${String(round + 1).padStart(2, '0')}`;
  $('se-effect').textContent = effect(r.answer);
  $('se-dosage').textContent = dosage(r.answer);
  $('se-dosage-row').hidden = true;
  $('se-hint').hidden = false;
  $('se-reveal').hidden = true;
  $('se-reveal').innerHTML = '';
  $('se-options').innerHTML = r.options.map((p, i) => `<button type="button" class="se-opt" data-pick="${p.id}"><span class="se-opt-img"><img src="${esc(p.image)}" alt="" width="400" height="400" decoding="async"><span class="se-key" aria-hidden="true">${i + 1}</span><span class="se-mark" aria-hidden="true"></span></span><span class="se-opt-name">${esc(p.name)}</span></button>`).join('');
  renderDots();
  $('se-status').textContent = '';
  // Warm the next round's photos so they appear instantly.
  rounds[round + 1]?.options.forEach(p => { const img = new Image(); img.src = p.image; });
}

function answer(id) {
  if (answered) return;
  answered = true;
  const r = rounds[round], right = id === r.answer.id;
  results[round] = right;
  if (right) { score++; streak++; } else streak = 0;
  root.querySelectorAll('.se-opt').forEach(b => {
    b.disabled = true;
    if (b.dataset.pick === r.answer.id) b.classList.add('right');
    else if (b.dataset.pick === id) b.classList.add('wrong');
    else b.classList.add('dim');
  });
  $('se-hint').hidden = true;
  $('se-dosage-row').hidden = false;
  $('se-score').textContent = score;
  $('se-streak').textContent = streak >= 2 ? `${streak} in a row` : '';
  renderDots();
  const p = r.answer, last = round === ROUNDS - 1;
  const verdict = right ? pickOne(CHEERS) : pickOne(OOPS);
  $('se-reveal').innerHTML = `<p class="se-verdict ${right ? 'yes' : 'no'}">${verdict}</p>
<div class="se-found"><img src="${esc(p.image)}" alt="${esc(p.name)} by ${esc(p.brand)}" width="400" height="400"><div><h3>It's the ${esc(p.name)}.</h3><p>${esc(p.caption)}</p><div class="se-found-actions">${buyLink(p, 'se-buy')}${heart(p, 'se-heart')}</div></div></div>
<button type="button" class="rx-btn dark se-next" id="se-next">${last ? 'See my diagnosis' : 'Next round'} <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14"/><path d="m13 6 6 6-6 6"/></svg></button>`;
  $('se-reveal').hidden = false;
  $('se-status').textContent = `${verdict} It's the ${p.name}. Score ${score} of ${round + 1}.`;
  $('se-next').focus({ preventScroll: true });
  $('se-reveal').scrollIntoView({ block: 'nearest', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
}

function next() {
  if (round < ROUNDS - 1) { round++; renderRound(); $('se-effect').focus({ preventScroll: true }); }
  else finish();
}

function finish() {
  const d = diagnose(score), best = getBest(), newBest = score > best;
  if (newBest) setBest(score);
  $('se-final').textContent = `${score}/${ROUNDS}`;
  $('se-diagnosis').textContent = d.title;
  $('se-note').textContent = d.note;
  $('se-mascot').src = `assets/mascot/${d.mascot}.webp`;
  $('se-best').textContent = newBest && best ? `New personal best! (Old best: ${best}/${ROUNDS})` : newBest ? 'Your first score. The bar is set.' : `Your best: ${Math.max(best, score)}/${ROUNDS}`;
  $('se-hints-used').textContent = hints ? `Read the directions ${hints} ${hints === 1 ? 'time' : 'times'}.` : 'No directions needed.';
  $('se-share-label').textContent = 'Share my score';
  $('se-copy').hidden = true;
  $('se-dispensed').innerHTML = rounds.map((r, i) => {
    const p = r.answer;
    return `<article class="se-mini"><div class="se-mini-img"><button type="button" data-detail="${p.id}" aria-label="View ${esc(p.name)}"><img src="${esc(p.image)}" alt="${esc(p.name)} by ${esc(p.brand)}" loading="lazy" width="400" height="400"></button>${heart(p)}<span class="se-mini-mark ${results[i] ? 'yes' : 'no'}" aria-label="${results[i] ? 'You got this one' : 'You missed this one'}">${results[i] ? '✓' : '✗'}</span></div><h3><button type="button" class="title-button" data-detail="${p.id}">${esc(p.name)}</button></h3><p>${esc(effect(p))}</p>${buyLink(p, 'amazon-link')}</article>`;
  }).join('');
  show('end');
}

function start() {
  rounds = buildRounds(); round = 0; score = 0; streak = 0; results = []; hints = 0;
  rxNo = String(Math.floor(1000 + Math.random() * 9000));
  renderRound();
  show('play');
  $('se-effect').focus({ preventScroll: true });
}

$('se-begin').addEventListener('click', start);
$('se-again').addEventListener('click', start);
$('se-options').addEventListener('click', e => { const b = e.target.closest('[data-pick]'); if (b) answer(b.dataset.pick); });
$('se-reveal').addEventListener('click', e => { if (e.target.closest('#se-next')) next(); });
$('se-hint').addEventListener('click', () => {
  if (answered || hinted) return;
  hinted = true; hints++;
  $('se-dosage-row').hidden = false;
  $('se-hint').hidden = true;
  $('se-status').textContent = `Directions: ${dosage(rounds[round].answer)}`;
});
document.addEventListener('keydown', e => {
  if (screens.play.hidden || e.metaKey || e.ctrlKey || e.altKey || document.querySelector('dialog[open]')) return;
  if (!answered && /^[1-4]$/.test(e.key)) { const b = root.querySelectorAll('.se-opt')[Number(e.key) - 1]; if (b) { e.preventDefault(); answer(b.dataset.pick); } }
});
$('se-share').addEventListener('click', async () => {
  const d = diagnose(score);
  const grid = results.map(r => (r ? '🟢' : '⚪️')).join('');
  const url = location.origin + location.pathname;
  const text = `I got ${score}/${ROUNDS} on Name That Side Effect 💊\nDiagnosis: ${d.title}\n${grid}`;
  if (navigator.share) {
    try { await navigator.share({ title: 'Name That Side Effect · Dopamine Supply Co.', text, url }); return; }
    catch (err) { if (err.name === 'AbortError') return; }
  }
  try { await navigator.clipboard.writeText(`${text}\n${url}`); $('se-share-label').textContent = 'Score copied'; }
  catch { $('se-copy-text').value = `${text}\n${url}`; $('se-copy').hidden = false; $('se-copy-text').select(); }
});

const best = getBest();
if (best) { $('se-start-best').textContent = `Your best so far: ${best}/${ROUNDS}`; $('se-start-best').hidden = false; }
if (askable.length < ROUNDS) return;
root.classList.add('se-ready');
})();
