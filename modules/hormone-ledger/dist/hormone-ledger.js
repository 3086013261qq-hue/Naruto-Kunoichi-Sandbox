(() => {
"use strict";
// User-specified strict schema: invalid source values are rejected, never clamped.
function createSchema(z) {
  return z.object({
    角色荷尔蒙: z.record(z.string(), z.number().int().min(0).max(100)).prefault({}),
    角色活体铠甲: z.record(z.string(), z.string()).prefault({}),
  });
}

const emptyState = () => ({ 角色荷尔蒙: {}, 角色活体铠甲: {} });
const isAssistant = m => !!m && m.is_user !== true && m.is_system !== true &&
  (m.role == null || m.role === 'assistant');
const rawText = m => String(m.message ?? m.mes ?? '');
const normalReply = m => isAssistant(m) && !/<\/?opening\b|\[(?:[A-Z_]+_)?OPENING_FLOW\]/i.test(rawText(m));

// Examine raw messages only. A malformed/duplicate/nested block is not a snapshot.
function parseSnapshot(text, previous = emptyState()) {
  const opens = [...text.matchAll(/<hormone>/gi)];
  const closes = [...text.matchAll(/<\/hormone>/gi)];
  const matches = [...text.matchAll(/<hormone>\s*([\s\S]*?)\s*<\/hormone>\s*/gi)];
  if (!opens.length && !closes.length) return { error: '本回合 hormone 输出缺失' };
  if (opens.length !== 1 || closes.length !== 1 || matches.length !== 1) return { error: 'hormone 块重复或不完整' };
  const block = matches[0];
  // Track surrounding XML; hormone cannot be inside any other XML structure.
  const stack = [];
  const prefix = text.slice(0, block.index).replace(/<!--[\s\S]*?-->/g, '');
  for (const tag of prefix.matchAll(/<(\/)?([A-Za-z_][\w:.-]*)\b[^>]*>/g)) {
    if (tag[1]) {
      if (stack.at(-1) === tag[2].toLowerCase()) stack.pop();
    } else if (!/\/\s*>$/.test(tag[0]) && !/^(br|hr|img|input|meta|link)$/i.test(tag[2])) stack.push(tag[2].toLowerCase());
  }
  if (stack.length || /[<>]/.test(block[1])) return { error: 'hormone 禁止嵌套' };
  const rows = new Map();
  for (const line of block[1].split(/\r?\n/).map(s => s.trim()).filter(Boolean)) {
    const fields = line.split('|').map(s => s.trim());
    const [name, value, armor] = fields;
    if (fields.length !== 3 || !name || !armor || !/^(0|[1-9]\d?|100)$/.test(value) ||
      rows.has(name) || ['__proto__', 'prototype', 'constructor'].includes(name)) return { error: 'hormone 行格式或数值非法' };
    rows.set(name, { value: Number(value), armor });
  }
  const oldNames = Object.keys(previous.角色荷尔蒙);
  if (oldNames.some(name => !rows.has(name))) return { error: 'hormone 完整快照遗漏已记录角色' };
  const names = [...oldNames, ...[...rows.keys()].filter(name => !Object.hasOwn(previous.角色荷尔蒙, name))];
  const state = emptyState();
  for (const name of names) {
    state.角色荷尔蒙[name] = rows.get(name).value;
    state.角色活体铠甲[name] = rows.get(name).armor;
  }
  return { state };
}

// Replay current selected swipes; deletes/edits/chat changes cannot retain future data.
function replay(messages) {
  let state = emptyState(), latest = null;
  const diagnostics = [];
  messages.forEach((m, index) => {
    if (!normalReply(m)) return;
    const id = m.message_id ?? m.id ?? index;
    const result = parseSnapshot(rawText(m), state);
    latest = id;
    if (result.state) state = result.state;
    else diagnostics.push({ message_id: id, error: result.error, cause: '上游输出契约失败' });
  });
  return { state, latest, diagnostics };
}

// Generated from the authoritative manifests; do not reorder.
const pages = ["https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/277699/00001.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/277699/00002.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/277699/00003.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/277699/00004.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/277699/00005.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/277699/00006.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/277699/00007.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/277699/00008.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/277699/00009.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/277699/00010.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/277699/00011.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/277699/00012.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/277699/00013.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/277699/00014.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/277699/00015.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/277699/00016.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/277699/00017.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/277699/00018.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/277699/00019.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/277699/00020.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/277699/00021.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/277699/00022.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/277699/00023.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/277699/00024.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/277699/00025.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/277699/00026.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/277699/00027.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/277699/00028.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00001.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00002.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00003.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00004.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00005.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00006.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00007.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00008.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00009.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00010.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00011.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00012.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00013.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00014.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00015.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00016.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00017.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00018.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00019.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00020.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00021.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00022.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00023.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00024.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00025.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00026.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00027.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00028.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00029.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00030.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00031.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00032.webp", "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/lockscreen/474873/00033.webp"];
const background = "https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27/media/mvu/142996460_p0_master1200.webp";
const css = ":host{display:block;width:100%;max-width:680px;margin:8px auto;box-sizing:border-box;color:#f1e3c8;font:14px/1.6 system-ui,\"Noto Sans SC\",sans-serif;isolation:isolate}\n*,*::before,*::after{box-sizing:border-box} [hidden]{display:none!important}\n.hl-main{--ink:#17151a;background-color:#101014;background-image:linear-gradient(180deg,rgba(15,13,17,.78),rgba(10,9,12,.92)),var(--hl-background),linear-gradient(160deg,#17151a,#101014);background-size:cover;background-position:center center;background-repeat:no-repeat;overflow:hidden;border:1px solid #d8b36a66;border-radius:6px;box-shadow:0 5px 18px #0003}\nheader{min-height:52px;display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:4px 12px;padding:12px 16px;border-top:3px solid #ef8a3a;border-bottom:1px solid #d8b36a44;background:#17151acc}\nh2{font-size:17px;line-height:1.5;margin:0;font-weight:700;overflow-wrap:anywhere;letter-spacing:.04em}header>span{color:#a89fa7;font-size:12px;white-space:nowrap}\n.hl-list{max-height:min(55vh,520px);overflow-y:auto;overflow-x:hidden;padding:12px;scrollbar-color:#d8b36a #17151a}\n.hl-card{min-width:0;margin:0 0 10px;padding:12px 14px;border:1px solid #d8b36a33;border-left:3px solid #ef8a3a;border-radius:3px;background:linear-gradient(110deg,#f1e3c80a,transparent),#17151ae8}.hl-card:last-child{margin-bottom:0}\n.hl-row{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;min-width:0}.hl-row strong{min-width:0;overflow-wrap:anywhere;font-weight:650}.hl-value{color:#ff6f91;font-variant-numeric:tabular-nums;white-space:nowrap;flex-shrink:0}\n.hl-track{height:8px;overflow:hidden;border-radius:4px;background:rgba(255,255,255,.10);margin:9px 0}.hl-track>span{display:block;height:100%;background:linear-gradient(90deg,#79cbd3 0%,#ef8a3a 45%,#ff6f91 100%);transition:width 350ms ease}\n.hl-armor{color:#d8b36a;overflow-wrap:anywhere;font-size:12px}.hl-none{color:#a89fa7}\n.hl-gallery{position:relative;width:100%;height:min(75vh,760px);min-height:220px;background:#101014;overflow:hidden;touch-action:pan-y;user-select:none;border:1px solid #d8b36a44;border-radius:5px}\n.hl-gallery>img{display:block;width:100%;height:100%;object-fit:contain;object-position:center center;pointer-events:none}\n.hl-page{position:absolute;bottom:10px;left:50%;transform:translateX(-50%);padding:3px 10px;border-radius:12px;background:#101014cc;color:#f1e3c8;font-size:12px;pointer-events:none}\n.hl-enter{position:absolute;left:20%;top:20%;width:60%;height:60%;min-width:44px;min-height:44px;border:0;background:transparent;cursor:pointer;color:inherit}.hl-enter:focus-visible{outline:2px solid #ef8a3a;outline-offset:-4px}\n.hl-fallback{position:absolute;top:45%;left:12%;right:12%;text-align:center;color:#a89fa7;pointer-events:none}\n@media(prefers-reduced-motion:reduce){.hl-track>span{transition:none}}\n";

function createGallery(document, pages, enter, storage) {
  if (!storage) { try { storage = document.defaultView.localStorage; } catch {} }
  const panel = document.createElement('section');
  panel.className = 'hl-gallery';
  panel.setAttribute('aria-label', '锁屏画廊，左右滑动翻页，中央轻触进入档案');
  const image = document.createElement('img');
  image.draggable = false;
  const pageLabel = document.createElement('span');
  pageLabel.className = 'hl-page';
  const center = document.createElement('button');
  center.type = 'button'; center.className = 'hl-enter';
  center.setAttribute('aria-label', '进入荷尔蒙档案');
  const fallback = document.createElement('span');
  fallback.className = 'hl-fallback';
  fallback.textContent = '图片暂不可用 · 轻触中央进入档案';
  panel.append(image, fallback, pageLabel, center);
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


function createUI(document) {
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


// Tavern Helper role script entry. No DOM scraping, polling or delayed second pass.
function mount(api = globalThis, win = window.parent) {
  win.__hormoneLedger?.stop();
  const document = win.document;
  const ui = createUI(document);
  let disposed = false, revision = 0, queue = Promise.resolve();
  const listeners = [];
  const diagnostics = [];
  let anchorId = null;
  // Mount readiness only: never read facts from DOM or trigger another replay.
  function attach() {
    if (disposed || anchorId == null) { ui.host.remove(); return; }
    const box = document.querySelector(`#chat > .mes[mesid="${Number(anchorId)}"] .mes_text`);
    if (box && ui.host.parentNode !== box) box.append(ui.host);
    else if (!box) ui.host.remove();
  }
  const observer = new win.MutationObserver(attach);
  observer.observe(document.body, { childList: true, subtree: true });
  async function refresh(ticket) {
    const last = api.getLastMessageId();
    const messages = last < 0 ? [] : await api.getChatMessages(`0-${last}`);
    const result = replay(messages);
    if (disposed || ticket !== revision) return;
    diagnostics.splice(0, diagnostics.length, ...result.diagnostics);
    for (const item of diagnostics) console.warn('[hormone-ledger]', item);
    const latest = result.latest;
    // Opening may host the empty gallery, but never contributes business facts.
    const openingIndex = messages.findLastIndex(isAssistant);
    anchorId = latest ?? (openingIndex < 0 ? null :
      messages[openingIndex].message_id ?? messages[openingIndex].id ?? openingIndex);
    attach(); // Move the one instance; never copy per-message panels.
    ui.render(result.state);
    if (latest == null) return;
    // Native message variable envelope. Raw hormone remains the only fact source.
    const scope = { type: 'message', message_id: latest };
    const envelope = await api.getVariables(scope);
    if (disposed || ticket !== revision) return;
    const old = envelope?.stat_data;
    if (JSON.stringify(old) !== JSON.stringify(result.state)) {
      await api.replaceVariables({ ...envelope, stat_data: result.state }, scope);
    }
  }
  function request() {
    const ticket = ++revision;
    queue = queue.then(() => refresh(ticket)).catch(error => {
      diagnostics.push({ error: String(error), cause: '宿主接线失败' });
      console.error('[hormone-ledger]', error);
    });
    return queue;
  }
  const events = api.tavern_events || {};
  for (const name of ['CHARACTER_MESSAGE_RENDERED', 'MESSAGE_UPDATED', 'MESSAGE_SWIPED', 'MESSAGE_DELETED', 'CHAT_CHANGED']) {
    if (events[name]) listeners.push(api.eventOn(events[name], request));
  }
  const stop = () => {
    disposed = true; ++revision;
    observer.disconnect();
    listeners.forEach(listener => listener?.stop?.());
    ui.destroy();
    api.removeEventListener?.('pagehide', stop);
    if (win.__hormoneLedger?.stop === stop) delete win.__hormoneLedger;
  };
  api.addEventListener?.('pagehide', stop, { once: true });
  win.__hormoneLedger = { stop, refresh: request, diagnostics, whenIdle: () => queue };
  request();
  return win.__hormoneLedger;
}

const start = () => mount();
if (typeof $ === 'function') $(start);
else if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, { once: true });
else start();

})();
