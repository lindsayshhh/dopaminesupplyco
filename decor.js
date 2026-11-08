// Home decor page: the room chips show one room at a time ("All rooms" shows the whole house).
// Without JavaScript the chips are plain links that jump to each room.
(() => {
  'use strict';
  const nav = document.querySelector('.room-nav');
  const picks = document.getElementById('picks');
  if (!nav || !picks) return;
  const rooms = [...picks.querySelectorAll('.room')];
  const chips = [...nav.querySelectorAll('a[data-room]')];
  const known = new Set(rooms.map(r => r.dataset.room));

  function show(slug, scroll) {
    const all = !known.has(slug);
    rooms.forEach(r => { r.hidden = !all && r.dataset.room !== slug; });
    picks.classList.toggle('one-room', !all);
    chips.forEach(c => {
      const on = c.dataset.room === (all ? 'all' : slug);
      c.classList.toggle('active', on);
      if (on) c.setAttribute('aria-current', 'true'); else c.removeAttribute('aria-current');
      if (on && c.scrollIntoView) c.scrollIntoView({block: 'nearest', inline: 'center'});
    });
    if (scroll) {
      const top = picks.getBoundingClientRect().top + window.scrollY - nav.offsetHeight;
      window.scrollTo({top: Math.max(0, top), behavior: 'smooth'});
    }
  }

  chips.forEach(c => c.addEventListener('click', e => {
    e.preventDefault();
    const slug = c.dataset.room;
    try { history.replaceState(null, '', slug === 'all' ? location.pathname + location.search : '#room-' + slug); } catch {}
    show(slug, true);
  }));

  const fromHash = () => location.hash.startsWith('#room-') ? location.hash.slice(6) : null;
  const start = fromHash();
  if (start && known.has(start)) show(start, true);
  window.addEventListener('hashchange', () => { const s = fromHash(); if (s && known.has(s)) show(s, true); });
})();
