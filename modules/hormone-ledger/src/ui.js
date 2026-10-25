import { createGallery } from './gallery.js';
import { pages, background, css } from './media.js';

export function createUI(document) {
  const host = document.createElement('div'); host.className = 'hormone-ledger-host';
  const shadow = host.attachShadow({ mode: 'open' });
  const style = document.createElement('style'); style.textContent = css;
  const main = document.createElement('section'); main.className = 'hl-main'; main.hidden = true;
  main.style.setProperty('--hl-background', `url("${background}")`);
  const header = document.createElement('header');
  const title = document.createElement('h2'); title.textContent = '火影姬 · 荷尔蒙档案';
  const count = document.createElement('span');
  header.append(title, count);
  const list = document.createElement('div'); list.className = 'hl-list';
  main.append(header, list);
  const gallery = createGallery(document, pages, () => {
    gallery.panel.hidden = true; main.hidden = false; gallery.release();
  });
  shadow.append(style, gallery.panel, main);
  const cards = new Map();
  function render(state) {
    const names = Object.keys(state.角色荷尔蒙);
    count.textContent = `已记录 ${names.length} 人`;
    for (const [name, card] of cards) if (!names.includes(name)) { card.remove(); cards.delete(name); }
    for (const name of names) {
      let card = cards.get(name);
      if (!card) {
        card = document.createElement('article'); card.className = 'hl-card';
        card.innerHTML = '<div class="hl-row"><strong></strong><span class="hl-value"></span></div><div class="hl-track" role="progressbar" aria-valuemin="0" aria-valuemax="100"><span></span></div><div class="hl-armor"></div>';
        cards.set(name, card);
      }
      const value = state.角色荷尔蒙[name], armor = state.角色活体铠甲[name];
      card.querySelector('strong').textContent = name;
      card.querySelector('.hl-value').textContent = `${value} / 100`;
      const track = card.querySelector('.hl-track');
      track.setAttribute('aria-valuenow', String(value)); track.setAttribute('aria-label', `${name}荷尔蒙`);
      track.firstElementChild.style.width = `${value}%`;
      const equipment = card.querySelector('.hl-armor');
      equipment.textContent = `活体铠甲 · ${armor}`; equipment.classList.toggle('hl-none', armor === '无');
      list.append(card);
    }
  }
  render({ 角色荷尔蒙: {}, 角色活体铠甲: {} });
  return { host, render, gallery, destroy() { gallery.release(); host.remove(); } };
}
