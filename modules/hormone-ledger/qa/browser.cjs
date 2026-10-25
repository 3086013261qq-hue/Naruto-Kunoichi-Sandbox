// Chromium mobile-sized automation; media requests use the pinned repository bytes.
// This is not an Android/SillyTavern integration acceptance test.
const { chromium } = require('playwright');
const fs = require('node:fs/promises');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');
const moduleRoot = path.resolve(__dirname, '..');
const repoRoot = path.resolve(moduleRoot, '../..');
const output = path.join(moduleRoot, 'qa/evidence');
const baseline = 'b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27';
const prefix = `https://cdn.jsdelivr.net/gh/3086013261qq-hue/Naruto-Kunoichi-Sandbox@${baseline}/`;
const snapshot = '<hormone>\n极长正式角色名称用于手机窄屏换行验证|0|无\n日向雏田|100|极长活体铠甲名称用于自动换行验证不允许横向溢出九尾九喇嘛活体铠甲\n</hormone>';

(async () => {
  await fs.mkdir(output, {recursive:true});
  const server = http.createServer(async (req,res) => {
    if (req.url === '/qa-font.ttf' && process.env.HL_QA_FONT) {res.setHeader('Content-Type','font/ttf');res.end(await fs.readFile(process.env.HL_QA_FONT));return;}
    if (req.url === '/') { res.setHeader('Content-Type','text/html'); res.end('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>@font-face{font-family:"Noto Sans SC";src:url(/qa-font.ttf)}body{margin:0;font-family:"Noto Sans SC",sans-serif}#chat{padding:0 8px}</style><div id="chat"><div class="mes" mesid="0"><div class="mes_text">正文</div></div><div class="mes" mesid="1"><div class="mes_text">后续正文</div></div></div>'); return; }
    const file = path.resolve(repoRoot, '.'+decodeURIComponent(req.url.split('?')[0]));
    if (!file.startsWith(repoRoot+path.sep)) {res.writeHead(403).end();return;}
    try {res.setHeader('Content-Type',file.endsWith('.js')?'text/javascript':'application/octet-stream');res.end(await fs.readFile(file));}
    catch {res.writeHead(404).end();}
  });
  await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
  const browser = await chromium.launch({headless:true,executablePath:process.env.HL_CHROMIUM_PATH || chromium.executablePath(),args:['--no-sandbox','--disable-dev-shm-usage']}).catch(error=>{server.close();throw error;});
  const results = [];
  try {
    for (const width of [320,360,390,440]) {
      const context = await browser.newContext({viewport:{width,height:844},isMobile:true,hasTouch:true});
      const page = await context.newPage();
      const requests = [], errors = [];
      page.on('pageerror', e => errors.push(String(e)));
      await page.route('https://cdn.jsdelivr.net/**',async route => {
        const url = route.request().url();requests.push(url);
        assert.ok(url.startsWith(prefix), 'Every media URL must be commit-pinned');
        if (url.endsWith('142996460_p0_master1200.webp')) return route.abort();
        const relative = url.slice(prefix.length);
        assert.match(relative,/^media\/mvu\/lockscreen\/(277699|474873)\/\d{5}\.webp$/);
        await route.fulfill({path:path.join(repoRoot,relative),contentType:'image/webp'});
      });
      await page.goto(`http://127.0.0.1:${server.address().port}/`);
      if(process.env.HL_QA_FONT)await page.evaluate(()=>document.fonts.load('14px "Noto Sans SC"'));
      await page.evaluate(async snapshot => {
        const {mount} = await import('/modules/hormone-ledger/src/host.js');
        window.messages = [{message_id:0,is_user:false,mes:snapshot}];
        window.variables = {};window.listeners = new Map();
        window.mock = {
          getLastMessageId:()=>messages.length-1,
          getChatMessages:()=>messages,
          getVariables:scope=>variables[scope.message_id]||{unrelated:'preserved'},
          replaceVariables:(data,scope)=>{variables[scope.message_id]=data;},
          tavern_events:Object.fromEntries(['CHARACTER_MESSAGE_RENDERED','MESSAGE_UPDATED','MESSAGE_SWIPED','MESSAGE_DELETED','CHAT_CHANGED'].map(x=>[x,x])),
          eventOn:(name,fn)=>{listeners.set(name,fn);return {stop:()=>listeners.delete(name)};},
        };
        window.ledger = mount(mock, window);
        await ledger.whenIdle();
      }, snapshot);
      await page.locator('.hormone-ledger-host').waitFor();
      await page.waitForFunction(()=>document.querySelector('.hormone-ledger-host').shadowRoot.querySelector('.hl-gallery>img').naturalWidth>0);
      assert.equal(requests.filter(x=>x.includes('/lockscreen/')).length,2,'Only current plus existing neighbor at first page');
      assert.equal(await page.locator('.hormone-ledger-host').evaluate(h=>getComputedStyle(h.shadowRoot.querySelector('.hl-gallery>img')).objectFit),'contain');
      const box = await page.locator('.hl-enter').boundingBox();
      assert.ok(box.width>=44&&box.height>=44);
      // Swipe across center then synthesize the trailing browser click: must stay locked.
      await page.locator('.hl-gallery').evaluate(panel=>{
        const r=panel.getBoundingClientRect(),y=r.top+r.height/2;
        for(const [type,x] of [['pointerdown',r.left+r.width*.7],['pointermove',r.left+r.width*.3],['pointerup',r.left+r.width*.3]]) panel.dispatchEvent(new PointerEvent(type,{clientX:x,clientY:y,pointerId:1,isPrimary:true,bubbles:true}));
        panel.querySelector('button').dispatchEvent(new MouseEvent('click',{detail:1,bubbles:true}));
      });
      assert.equal(await page.locator('.hl-main').isVisible(),false);
      assert.equal(await page.locator('.hl-page').textContent(),'2 / 61');
      // Real touch tap at the center opens the single main page.
      await page.locator('.hl-enter').tap();
      assert.equal(await page.locator('.hl-main').isVisible(),true);
      const layout = await page.locator('.hormone-ledger-host').evaluate(host=>{
        const root=host.shadowRoot, cards=[...root.querySelectorAll('.hl-card')];
        return {width:host.clientWidth,scroll:host.scrollWidth,documentOverflow:document.documentElement.scrollWidth>innerWidth,
          listOverflow:root.querySelector('.hl-list').scrollWidth>root.querySelector('.hl-list').clientWidth,
          tracks:cards.map(card=>({value:card.querySelector('.hl-track').getAttribute('aria-valuenow'),width:card.querySelector('.hl-track>span').getBoundingClientRect().width,full:card.querySelector('.hl-track').getBoundingClientRect().width})),
          background:getComputedStyle(root.querySelector('.hl-main')).backgroundImage};
      });
      // Initial fill starts at final width, so no timing-dependent assertion is needed.
      assert.equal(layout.documentOverflow,false);assert.equal(layout.listOverflow,false);assert.ok(layout.scroll<=layout.width);
      assert.equal(layout.tracks[0].width,0);assert.equal(layout.tracks[1].width,layout.tracks[1].full);
      assert.ok(layout.background.includes('linear-gradient'));
      await page.screenshot({path:path.join(output,`main-${width}.png`),fullPage:true});
      // New reply, repeated event, missing block: one host, previous data, diagnostics.
      await page.evaluate(async()=>{
        messages.push({message_id:1,role:'assistant',message:'本回合缺失结构块'});
        await listeners.get('CHARACTER_MESSAGE_RENDERED')();
        await listeners.get('MESSAGE_UPDATED')();
      });
      assert.equal(await page.locator('.hormone-ledger-host').count(),1);
      assert.equal(await page.locator('.mes[mesid="1"] .hormone-ledger-host').count(),1);
      assert.ok(await page.evaluate(()=>ledger.diagnostics.some(x=>x.error==='本回合 hormone 输出缺失')));
      assert.equal(await page.evaluate(()=>variables[1].stat_data.角色荷尔蒙.日向雏田),100);
      assert.equal(await page.evaluate(()=>variables[1].unrelated),'preserved');
      // Current swipe replaces history; future characters disappear.
      await page.evaluate(async()=>{
        messages=[{message_id:0,is_user:false,mes:'<hormone>另一名角色|50|无</hormone>'}];
        await listeners.get('MESSAGE_SWIPED')();
      });
      assert.deepEqual(await page.locator('.hl-row strong').allTextContents(),['另一名角色']);
      // Remove and change chat, then remount: no listener/panel leaks.
      await page.evaluate(async()=>{messages=[];await listeners.get('MESSAGE_DELETED')();});
      assert.equal(await page.locator('.hormone-ledger-host').count(),0);
      await page.evaluate(async()=>{messages=[{message_id:0,role:'user',message:'hello'}];await listeners.get('CHAT_CHANGED')();});
      assert.equal(await page.locator('.hormone-ledger-host').count(),0);
      await page.evaluate(()=>ledger.stop());
      assert.equal(await page.evaluate(()=>listeners.size),0);
      results.push({width,result:'PASS',layout});
      // All gallery pages, boundaries, bounded resident set, remembered index.
      await page.evaluate(async()=>{
        const {createGallery}=await import('/modules/hormone-ledger/src/gallery.js');
        const {pages}=await import('/modules/hormone-ledger/src/media.js');
        window.g=createGallery(document,pages,()=>{});document.body.append(g.panel);
      });
      for(let index=0;index<61;index++) {
        await page.evaluate(index=>g.show(index),index);
        try { await page.waitForFunction(index=>g.index===index&&g.panel.querySelector('img').complete&&g.panel.querySelector('img').naturalWidth>0,index); }
        catch(error) {throw new Error(`Gallery ${width}px index ${index}: ${await page.evaluate(()=>JSON.stringify({src:g.panel.querySelector('img').src,complete:g.panel.querySelector('img').complete,width:g.panel.querySelector('img').naturalWidth}))}`,{cause:error});}
        assert.ok(await page.evaluate(()=>g.residentPages.length<=3&&g.residentPages.every(i=>Math.abs(i-g.index)<=1)));
        assert.equal(await page.locator('.hl-page').textContent(),`${index+1} / 61`);
      }
      await page.evaluate(()=>g.show(27));
      await page.locator('.hl-gallery').evaluate(panel=>{
        const r=panel.getBoundingClientRect();
        for(const [type,x] of [['pointerdown',r.left+200],['pointerup',r.left+80]])panel.dispatchEvent(new PointerEvent(type,{clientX:x,clientY:r.top+100,pointerId:2,isPrimary:true,bubbles:true}));
      });
      assert.equal(await page.evaluate(()=>g.index),28,'Book 1 -> Book 2 continuous');
      await page.evaluate(async()=>{
        g.release();g.panel.remove();
        const {createGallery}=await import('/modules/hormone-ledger/src/gallery.js');
        const {pages}=await import('/modules/hormone-ledger/src/media.js');
        window.g=createGallery(document,pages,()=>{});document.body.append(g.panel);
      });
      assert.equal(await page.evaluate(()=>g.index),28,'Remembers index');
      // Failure remains operable and visible as a fallback.
      await page.route('https://cdn.jsdelivr.net/**',route=>route.abort());
      await page.evaluate(()=>{g.show(60);g.panel.querySelector('img').src+='?qa-failure=1';});
      await page.waitForFunction(()=>!g.panel.querySelector('.hl-fallback').hidden);
      // Execute the built role script twice as Tavern Helper would on a reload.
      await page.evaluate(()=>{
        g.release();g.panel.remove();
        Object.assign(window,mock);
        messages=[{message_id:0,is_user:false,mes:'<hormone>构建包验证|37|无</hormone>'}];
      });
      for(let attempt=0;attempt<2;attempt++){
        await page.addScriptTag({path:path.join(moduleRoot,'dist/hormone-ledger.js')});
        await page.evaluate(()=>window.__hormoneLedger.whenIdle());
        assert.equal(await page.locator('.hormone-ledger-host').count(),1);
        assert.equal(await page.evaluate(()=>listeners.size),5);
      }
      await page.evaluate(()=>window.__hormoneLedger.stop());
      assert.deepEqual(errors,[]);
      await context.close();
    }
    await fs.writeFile(path.join(output,'browser-results.json'),JSON.stringify({engine:'Chromium mobile emulation; local pinned-media mirror; background intentionally blocked',results,gallery:'61/61 decoded at each width, 28→29 boundary, <=3 residents, remembered page, swipe/tap separated',host:'raw message events, missing block inheritance, one instance, selected swipe, deletes, chat reset, teardown'},null,2)+'\n');
    console.log('PASS: 320/360/390/440 layouts, 61-page galleries, pointer guards, fallback and native-host simulation.');
  } finally {await browser.close();await new Promise(resolve=>server.close(resolve));}
})().catch(error=>{console.error(error);process.exitCode=1;});
