export function createGallery(document, pages, enter, storage) {
  if (!storage) { try { storage = document.defaultView.localStorage; } catch {} }
  const panel = document.createElement('section');
  panel.className = 'hl-gallery';
  panel.setAttribute('aria-label', '锁屏画廊，左右滑动翻页，中央轻触进入档案');
  const image = document.createElement('img');
  image.draggable = false;
  const pageLabel = document.createElement('span');
  pageLabel.className = 'hl-page';
  const nav = document.createElement('nav'); nav.className = 'hl-gallery-nav';
  nav.setAttribute('aria-label', '锁屏翻页');
  const previous = document.createElement('button'), next = document.createElement('button');
  for (const [button, label, text, delta] of [[previous, '上一页', '‹', -1], [next, '下一页', '›', 1]]) {
    button.type = 'button'; button.className = 'hl-page-button';
    button.setAttribute('aria-label', label); button.textContent = text;
    button.addEventListener('click', e => { e.preventDefault(); e.stopPropagation(); show(current + delta); });
  }
  for (const event of ['pointerdown', 'pointermove', 'pointerup', 'pointercancel']) {
    nav.addEventListener(event, e => e.stopPropagation());
  }
  nav.append(previous, pageLabel, next);
  const center = document.createElement('button');
  center.type = 'button'; center.className = 'hl-enter';
  center.setAttribute('aria-label', '进入荷尔蒙档案');
  const fallback = document.createElement('span');
  fallback.className = 'hl-fallback';
  fallback.textContent = '图片暂不可用 · 轻触中央进入档案';
  panel.append(image, fallback, center, nav);
  let current = 0, down = null, dragged = false;
  const preload = new Map();
  try { current = Math.max(0, Math.min(pages.length - 1, Number(storage?.getItem('hormone-ledger:gallery-page')) || 0)); } catch {}
  current = Math.floor(current);
  image.onload = () => { fallback.hidden = true; image.hidden = false; };
  image.onerror = () => { fallback.hidden = false; image.hidden = true; };
  function show(index) {
    current = Math.max(0, Math.min(pages.length - 1, index));
    fallback.hidden = true; image.hidden = false;
    image.alt = `锁屏第 ${current + 1} / ${pages.length} 页`;
    image.src = pages[current];
    pageLabel.textContent = `${current + 1} / ${pages.length}`;
    previous.disabled = current === 0;
    next.disabled = current === pages.length - 1;
    for (const [i, img] of preload) if (Math.abs(i - current) > 1 || i === current) { img.removeAttribute('src'); preload.delete(i); }
    for (const i of [current - 1, current + 1]) {
      if (pages[i] && !preload.has(i)) {
        const img = document.createElement('img'); img.src = pages[i]; preload.set(i, img);
      }
    }
    try { storage?.setItem('hormone-ledger:gallery-page', String(current)); } catch {}
  }
  panel.addEventListener('pointerdown', e => {
    if (!e.isPrimary || e.button !== 0) return;
    down = { x: e.clientX, y: e.clientY, id: e.pointerId }; dragged = false;
    try { panel.setPointerCapture(e.pointerId); } catch { /* Detached/synthetic pointer: still honor movement guard. */ }
  });
  panel.addEventListener('pointermove', e => {
    if (!down || e.pointerId !== down.id) return;
    if (Math.hypot(e.clientX - down.x, e.clientY - down.y) > 12) dragged = true;
  });
  panel.addEventListener('pointerup', e => {
    if (!down || e.pointerId !== down.id) return;
    const dx = e.clientX - down.x, dy = e.clientY - down.y;
    dragged ||= Math.hypot(dx, dy) > 12;
    const wasDragged = dragged;
    down = null;
    if (Math.abs(dx) >= 36 && Math.abs(dx) > Math.abs(dy) * 1.25) show(current + (dx < 0 ? 1 : -1));
    else if (!wasDragged) {
      const rect = panel.getBoundingClientRect();
      const x = e.clientX - rect.left, y = e.clientY - rect.top;
      if (x >= rect.width * .2 && x <= rect.width * .8 && y >= rect.height * .2 && y <= rect.height * .8) enter();
    }
  });
  panel.addEventListener('pointercancel', () => { down = null; dragged = true; });
  // Pointer clicks are handled above; keyboard/assistive clicks use detail === 0.
  center.addEventListener('click', e => { e.preventDefault(); if (e.detail === 0 && !down) enter(); });
  center.addEventListener('keydown', e => {
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') { e.preventDefault(); show(current + (e.key === 'ArrowRight' ? 1 : -1)); }
  });
  function release() {
    image.removeAttribute('src');
    for (const img of preload.values()) img.removeAttribute('src');
    preload.clear();
  }
  show(current);
  return { panel, show, release, get index() { return current; }, get residentPages() { return [current, ...preload.keys()]; } };
}
