import { replay } from './runtime.js';
import { createUI } from './ui.js';

// Tavern Helper role script entry. No DOM scraping, polling or delayed second pass.
export function mount(api = globalThis, win = window.parent) {
  win.__hormoneLedger?.stop();
  const document = win.document;
  const ui = createUI(document);
  let disposed = false, revision = 0, queue = Promise.resolve();
  const listeners = [];
  const diagnostics = [];
  async function refresh(ticket) {
    const last = api.getLastMessageId();
    const messages = last < 0 ? [] : await api.getChatMessages(`0-${last}`);
    const result = replay(messages);
    if (disposed || ticket !== revision) return;
    diagnostics.splice(0, diagnostics.length, ...result.diagnostics);
    for (const item of diagnostics) console.warn('[hormone-ledger]', item);
    const latest = result.latest;
    if (latest == null) { ui.host.remove(); return; }
    const box = document.querySelector(`#chat > .mes[mesid="${Number(latest)}"] .mes_text`);
    if (!box) { ui.host.remove(); return; }
    box.append(ui.host); // Move the one instance; never copy per-message panels.
    ui.render(result.state);
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
