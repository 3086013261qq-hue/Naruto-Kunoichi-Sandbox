export const emptyState = () => ({ 角色荷尔蒙: {}, 角色活体铠甲: {} });
export const isAssistant = m => !!m && m.is_user !== true && m.is_system !== true &&
  (m.role == null || m.role === 'assistant');
export const rawText = m => String(m.message ?? m.mes ?? '');
export const normalReply = m => isAssistant(m) && !/<\/?opening\b|\[(?:[A-Z_]+_)?OPENING_FLOW\]/i.test(rawText(m));

// Examine raw messages only. A malformed/duplicate/nested block is not a snapshot.
export function parseSnapshot(text, previous = emptyState()) {
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
export function replay(messages) {
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
