import { mount } from './host.js';
const start = () => mount();
if (typeof $ === 'function') $(start);
else if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, { once: true });
else start();
