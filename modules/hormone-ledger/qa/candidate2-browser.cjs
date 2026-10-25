// Execute the actual script embedded in each Candidate JSON in a hidden role iframe.
const {chromium}=require('playwright');
const fs=require('node:fs/promises');
const path=require('node:path');
const http=require('node:http');
const assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../../..');
const candidate=path.join(root,'release/火影姬世界_Candidate2_v1.0.json');
const oldFile=process.env.HL_PREVIOUS_CANDIDATE;
const opening='<opening>仅测试挂载的开场夹具</opening>';
const snapshot='<hormone>漩涡鸣子|37|九尾九喇嘛活体铠甲</hormone>';
const output=path.join(__dirname,'evidence/candidate2-mount.json');

(async()=>{
  const card=JSON.parse(await fs.readFile(candidate,'utf8'));
  const old=oldFile?JSON.parse(await fs.readFile(oldFile,'utf8')):null;
  assert.match(card.data.first_mes,/<opening>/i,'Existing opening really uses the marker');
  const status=c=>c.data.extensions.tavern_helper.scripts.find(x=>x.name==='变量状态栏').content;
  const server=http.createServer(async(req,res)=>{
    if(req.url==='/font.ttf'&&process.env.HL_QA_FONT){res.setHeader('Content-Type','font/ttf');res.end(await fs.readFile(process.env.HL_QA_FONT));return;}
    res.setHeader('Content-Type','text/html');res.end('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>@font-face{font-family:"Noto Sans SC";src:url(/font.ttf)}body{margin:8px;font-family:"Noto Sans SC",sans-serif}</style><div id="chat"></div>');
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const browser=await chromium.launch({headless:true,executablePath:process.env.HL_CHROMIUM_PATH||chromium.executablePath(),args:['--no-sandbox','--disable-dev-shm-usage']}).catch(e=>{server.close();throw e;});
  const results=[];
  try{
    for(const variant of old?[{name:'previous',script:status(old)},{name:'Candidate2',script:status(card)}]:[{name:'Candidate2',script:status(card)}]){
      for(const scenario of ['opening-existing-dom','normal-reply-late-dom']){
        const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
        const page=await context.newPage(),errors=[];
        page.on('pageerror',e=>errors.push(String(e)));
        await page.route('https://cdn.jsdelivr.net/**',r=>r.abort());
        await page.goto(`http://127.0.0.1:${server.address().port}/`);
        if(process.env.HL_QA_FONT)await page.evaluate(()=>document.fonts.load('14px "Noto Sans SC"'));
        await page.evaluate(({scenario,opening,snapshot})=>{
          window.messages=[{message_id:0,is_user:false,mes:scenario==='opening-existing-dom'?opening:snapshot}];
          window.values={};window.events=new Map();window.writes=0;
          window.$=fn=>{if(typeof fn==='function')Promise.resolve().then(fn);};
          window.helperAPI={
            getLastMessageId:()=>messages.length-1,getChatMessages:()=>messages,
            getVariables:scope=>values[scope.message_id]||{},replaceVariables:(data,scope)=>{writes++;values[scope.message_id]=data;},
            tavern_events:Object.fromEntries(['CHARACTER_MESSAGE_RENDERED','MESSAGE_UPDATED','MESSAGE_SWIPED','MESSAGE_DELETED','CHAT_CHANGED'].map(x=>[x,x])),
            eventOn:(key,fn)=>{events.set(key,fn);return{stop:()=>events.delete(key)};}
          };
          window.addFloor=id=>{const floor=document.createElement('div');floor.className='mes';floor.setAttribute('mesid',id);floor.innerHTML='<div class="mes_text">测试正文</div>';document.querySelector('#chat').append(floor);return floor;};
          if(scenario==='opening-existing-dom')addFloor(0);
        },{scenario,opening,snapshot});
        await page.evaluate(script=>{
          const iframe=document.createElement('iframe');iframe.hidden=true;iframe.id='TH-script--变量状态栏--hormone-ledger-statusbar';
          iframe.srcdoc='<!doctype html><body><script>window.$=parent.$;Object.assign(window,parent.helperAPI);<\/script><script type="module">'+script+'\nparent.roleScriptRan=true;<\/script>';
          document.body.append(iframe);
        },variant.script);
        await page.waitForFunction(()=>window.roleScriptRan&&window.__hormoneLedger);
        await page.evaluate(()=>window.__hormoneLedger.whenIdle());
        if(scenario==='normal-reply-late-dom')await page.evaluate(()=>addFloor(0));
        if(variant.name==='Candidate2')await page.locator('.hormone-ledger-host').waitFor({state:'attached'});
        const mounted=await page.locator('.hormone-ledger-host').count();
        assert.equal(mounted,variant.name==='Candidate2'?1:0);
        if(variant.name==='Candidate2'){
          if(scenario==='opening-existing-dom'){
            assert.equal(await page.evaluate(()=>writes),0,'Opening must not manufacture record state');
            assert.equal(await page.locator('.hl-card').count(),0);
          }
          await page.locator('.hl-enter').tap();
          assert.equal(await page.locator('.hl-main').isVisible(),true);
          if(scenario==='opening-existing-dom'){
            await page.evaluate(async snapshot=>{
              messages.push({message_id:1,role:'assistant',message:snapshot});addFloor(1);
              await events.get('CHARACTER_MESSAGE_RENDERED')();
            },snapshot);
            assert.equal(await page.locator('.mes[mesid="1"] .hormone-ledger-host').count(),1);
            assert.equal(await page.locator('.hl-value').textContent(),'37 / 100');
            await page.evaluate(async()=>{messages.push({message_id:2,is_user:false,mes:'漏块测试'});addFloor(2);await events.get('CHARACTER_MESSAGE_RENDERED')();});
            assert.equal(await page.locator('.hl-value').textContent(),'37 / 100');
            assert.ok(await page.evaluate(()=>__hormoneLedger.diagnostics.some(x=>x.error==='本回合 hormone 输出缺失')));
          }
          // Simulate SillyTavern replacing a rendered message body without a data update.
          await page.evaluate(()=>{const host=document.querySelector('.hormone-ledger-host');host.parentNode.innerHTML='替换后的正文';});
          await page.locator('.hormone-ledger-host').waitFor({state:'attached'});
          assert.equal(await page.locator('.hormone-ledger-host').count(),1);
          if(process.env.HL_QA_FONT)await page.evaluate(()=>document.fonts.load('14px "Noto Sans SC"'));
          await page.screenshot({path:path.join(__dirname,`evidence/candidate2-${scenario}.png`),fullPage:true});
        }
        await page.evaluate(()=>__hormoneLedger.stop());
        assert.equal(await page.evaluate(()=>events.size),0);
        assert.equal(await page.locator('.hormone-ledger-host').count(),0);
        assert.deepEqual(errors,[]);
        results.push({variant:variant.name,scenario,initial_panel_count:mounted,result:variant.name==='Candidate2'?'PASS':'original failure reproduced'});
        await context.close();
      }
    }
    await fs.writeFile(output,JSON.stringify({status:'PASS',scope:'Actual embedded status script in hidden srcdoc type=module iframe; native host APIs simulated; external media blocked; not real Android/SillyTavern',results},null,2)+'\n');
    console.log('PASS: '+(old?'previous failures reproduced; ':'')+'Candidate2 opening, late DOM, rendered-body replacement, current floor, missing snapshot and teardown verified.');
  }finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
})().catch(e=>{console.error(e);process.exitCode=1;});
