(() => {
'use strict';
const products = window.PRODUCTS;
const config = window.SHOP_CONFIG;
const $ = id => document.getElementById(id);
const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const money = n => new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:2,minimumFractionDigits:0}).format(n);
const known = new Set(products.map(p => p.id));
let saved;
try { const parsed = JSON.parse(localStorage.getItem('dopamine-favorites') || '[]'); saved = new Set(Array.isArray(parsed) ? parsed.filter(id => known.has(id)) : []); } catch { saved = new Set(); }
let mood = 'All', budget = 0, query = '', featured = products[0], sharedIds = null, seen = new Set([featured.id]), toastTimer;
const matching = () => products.filter(p => p.active !== false && (mood === 'All' || p.moods.includes(mood)) && (!budget || (Number.isFinite(p.referencePrice) && p.referencePrice < budget)) && `${p.name} ${p.caption} ${p.brand} ${p.moods.join(' ')}`.toLowerCase().includes(query));
function amazonUrl(p) {
 if (!p.affiliateUrl) return p.source;
 const url = new URL(p.affiliateUrl);
 if (config.amazonTag) url.searchParams.set('tag',config.amazonTag);
 return url.href;
}
const amazon = (p,cls='amazon-link') => `<a class="${cls}" href="${escape(amazonUrl(p))}" target="_blank" rel="${p.affiliateUrl?'sponsored ':''}noopener noreferrer" aria-label="View ${escape(p.name)} ${p.affiliateUrl?'on Amazon':'at '+escape(p.brand)} (opens a new tab)">${p.affiliateUrl?'View on Amazon':'View at '+escape(p.brand)} <span aria-hidden="true">↗</span></a>`;
const heart = (p,cls='save-button') => `<button class="${cls}${saved.has(p.id)?' saved':''}" data-save="${p.id}" aria-label="${saved.has(p.id)?'Remove':'Save'} ${escape(p.name)}${saved.has(p.id)?' from':' to'} my list" aria-pressed="${saved.has(p.id)}">${saved.has(p.id)?'♥':'♡'}</button>`;
function showToast(message){$('toast').textContent=message;$('toast').classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').classList.remove('show'),2600);}
function renderFeature(animate=false){
 if(!$('featured'))return;
 const p=featured;
 $('featured').innerHTML=`<div class="featured-photo"><img src="${p.image}" alt="${escape(p.name)} by ${escape(p.brand)}" fetchpriority="high" data-detail="${p.id}" tabindex="0" role="button" aria-label="View ${escape(p.name)}">${heart(p)}</div><div class="featured-copy"><h2>${escape(p.name)}</h2><div class="feature-actions">${amazon(p)}</div></div>`;
 if(animate){$('featured').classList.remove('dispense');void $('featured').offsetWidth;$('featured').classList.add('dispense');}
}
function renderGrid(){
 if(!$('grid'))return;
 const list=matching();
 $('results').textContent=`${list.length} ${list.length===1?'find':'finds'}`;
 $('grid').innerHTML=list.map(p=>`<article class="card"><div class="card-image"><button data-detail="${p.id}" aria-label="View ${escape(p.name)}"><img loading="lazy" decoding="async" src="${p.image}" alt="${escape(p.name)} by ${escape(p.brand)}" width="400" height="400"></button>${heart(p)}</div><div class="card-body"><h3><button class="title-button" data-detail="${p.id}">${escape(p.name)}</button></h3><p>${escape(p.caption)}</p>${amazon(p)}</div></article>`).join('');
 $('empty').hidden=!!list.length;$('reset').hidden=mood==='All'&&!budget&&!query;
}
function updateHearts(){
 document.querySelectorAll('[data-save]').forEach(button=>{const p=products.find(p=>p.id===button.dataset.save);if(!p)return;const on=saved.has(p.id);button.classList.toggle('saved',on);button.setAttribute('aria-pressed',String(on));button.setAttribute('aria-label',`${on?'Remove':'Save'} ${p.name} ${on?'from':'to'} my list`);button.textContent=button.classList.contains('detail-save')?(on?'♥ Saved to my list':'♡ Save to my list'):(on?'♥':'♡');});
 $('saved-count').textContent=saved.size;
}
function saveProduct(id){
 const removing=saved.has(id);if(removing)saved.delete(id);else saved.add(id);
 try{localStorage.setItem('dopamine-favorites',JSON.stringify([...saved]));showToast(removing?'Removed from your little list':'A little joy, saved. ♥');}catch{showToast('Saved for this visit. Browser storage is unavailable.');}
 updateHearts();if($('saved').open)renderSaved();
}
function showDetail(id){const p=products.find(p=>p.id===id);if(!p)return;
 $('detail-content').innerHTML=`<div class="detail-layout"><img src="${p.image}" alt="${escape(p.name)} by ${escape(p.brand)}"><div class="detail-copy"><p class="eyebrow">${p.moods.join(' · ')} / ${escape(p.brand)}</p><h2>${escape(p.name)}</h2><p>${escape(p.caption)}</p>${amazon(p,'solid')}<button class="text-button detail-save" data-save="${p.id}" aria-pressed="${saved.has(p.id)}">${saved.has(p.id)?'♥ Saved to my list':'♡ Save to my list'}</button><small>${p.affiliateUrl ? "Check Amazon for current price and availability." : "This saved find is available through its maker’s page."}</small><small>As an Amazon Associate I earn from qualifying purchases.</small>${p.sourceType === "amazon" ? "" : `<a class="source-link" href="${p.source}" target="_blank" rel="noopener noreferrer">View the maker’s product details ↗</a>`}</div></div>`;$('detail').showModal();
}
function resetFilters(){mood='All';budget=0;query='';$('search').value='';document.querySelectorAll('[data-mood]').forEach(b=>{const active=b.dataset.mood==='All';b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active));});renderGrid();}
function renderSaved(){
 const ids=sharedIds??[...saved], list=ids.map(id=>products.find(p=>p.id===id)).filter(Boolean);
 $('list-title').textContent=sharedIds?'Shared finds.':'Saved finds.';
 $('list-note').textContent=sharedIds?'Save any favorites to your own list.':'Saved on this device.';
 $('saved-items').innerHTML=list.length?list.map(p=>`<article class="saved-row"><img src="${p.image}" alt="${escape(p.name)}"><div><h3>${escape(p.name)}</h3>${amazon(p)}</div>${sharedIds?`<button class="remove" data-save="${p.id}" aria-label="Save ${escape(p.name)} to my list" aria-pressed="${saved.has(p.id)}">${saved.has(p.id)?'♥':'♡'}</button>`:`<button class="remove" data-remove="${p.id}" aria-label="Remove ${escape(p.name)} from my list">×</button>`}</article>`).join(''):'<div class="list-empty">Tap a heart to save a find.</div>';
 $('share-list').disabled=!list.length;$('share-list').textContent='Share list ↗';$('own-list').hidden=!sharedIds;updateHearts();
}
function openSaved(){sharedIds=null;$('copy-fallback').hidden=true;renderSaved();$('saved').showModal();}
function readSharedList(){
 if(!location.hash.startsWith('#list='))return;
 const ids=location.hash.slice(6).split(',').filter(id=>known.has(id));sharedIds=[...new Set(ids)].slice(0,products.length);
 renderSaved();if(!$('saved').open)$('saved').showModal();
}
async function shareList(){
 const ids=sharedIds??[...saved];if(!ids.length)return;
 const url=new URL(location.href);url.hash='list='+ids.join(',');
 if(navigator.share){try{await navigator.share({title:'My little list · Dopamine Supply Co.',text:'A few very good hints.',url:url.href});return;}catch(e){if(e.name==='AbortError')return;}}
 try{await navigator.clipboard.writeText(url.href);showToast('Wish-list link copied. Drop a hint.');}catch{$('share-url').value=url.href;$('copy-fallback').hidden=false;$('share-url').focus();$('share-url').select();}
}
$('surprise')?.addEventListener('click',()=>{let pool=matching();if(!pool.length){showToast('No finds match. Try clearing your filters.');return;}if(pool.length===1&&pool[0].id===featured.id){showToast('Your one perfect match. Broaden the filters for more!');return;}let fresh=pool.filter(p=>!seen.has(p.id));if(!fresh.length){seen.clear();fresh=pool.filter(p=>p.id!==featured.id);if(!fresh.length)fresh=pool;}featured=fresh[Math.floor(Math.random()*fresh.length)];seen.add(featured.id);renderFeature(true);$('surprise-status').textContent=`Your surprise: ${featured.name}. ${featured.caption}`;});
document.addEventListener('click',e=>{const save=e.target.closest('[data-save]');if(save){saveProduct(save.dataset.save);return;}const remove=e.target.closest('[data-remove]');if(remove){saveProduct(remove.dataset.remove);return;}const detail=e.target.closest('[data-detail]');if(detail){showDetail(detail.dataset.detail);return;}const close=e.target.closest('[data-close]');if(close)close.closest('dialog').close();});
document.addEventListener('keydown',e=>{if((e.key==='Enter'||e.key===' ')&&e.target.matches('img[data-detail]')){e.preventDefault();showDetail(e.target.dataset.detail);}});
document.querySelectorAll('dialog').forEach(d=>d.addEventListener('click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close();}}));
document.querySelectorAll('[data-mood]').forEach(b=>b.addEventListener('click',()=>{mood=b.dataset.mood;document.querySelectorAll('[data-mood]').forEach(c=>{const active=c===b;c.classList.toggle('active',active);c.setAttribute('aria-pressed',String(active));});renderGrid();}));
$('search')?.addEventListener('input',e=>{query=e.target.value.trim().toLowerCase();renderGrid();});$('reset')?.addEventListener('click',resetFilters);$('clear-empty')?.addEventListener('click',resetFilters);$('open-saved').addEventListener('click',openSaved);$('share-list').addEventListener('click',shareList);$('own-list').addEventListener('click',()=>{sharedIds=null;renderSaved();$('copy-fallback').hidden=true;});$('select-link').addEventListener('click',()=>{$('share-url').focus();$('share-url').select();});
$('about').addEventListener('click',()=>{$('info-content').innerHTML='<h2>About the finds.</h2><p>Playful finds, independently curated by Dopamine Supply Co.</p><p>Amazon links open the featured product’s listing. Check the current price, variant, and availability before buying. Purchases, shipping, and returns are handled by the retailer.</p><p>As an Amazon Associate I earn from qualifying purchases.</p>';$('info').showModal();});
$('privacy').addEventListener('click',()=>{$('info-content').innerHTML='<h2>Your little list is yours.</h2><p>This version stores favorite product IDs in your browser on this device. There are no accounts, email signups, or analytics scripts in the site itself. Removing favorites updates that local storage.</p><p>Sharing a wish list puts its product IDs in the link. Anyone who can access the site and has that link can see those items. Your name and other personal details are not added to the link.</p><p>Amazon and maker links take you to external websites with their own privacy practices. Amazon links contain our affiliate tracking tag. Google Fonts and the hosting provider may receive ordinary connection information when the page loads.</p>';$('info').showModal();});
window.addEventListener('hashchange',readSharedList);window.addEventListener('storage',e=>{if(e.key!=='dopamine-favorites')return;try{const ids=JSON.parse(e.newValue||'[]');saved=new Set(Array.isArray(ids)?ids.filter(id=>known.has(id)):[]);updateHearts();if($('saved').open)renderSaved();}catch{}});
renderFeature();renderGrid();updateHearts();readSharedList();
})();
