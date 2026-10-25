// Local mobile-sized browser QA; not real Android/SillyTavern acceptance.
const {chromium}=require('playwright');
const fs=require('node:fs/promises'), path=require('node:path'),http=require('node:http'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../../..');
(async()=>{
 const server=http.createServer(async(req,res)=>{
  if(req.url==='/'){res.setHeader('Content-Type','text/html');res.end('<meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;padding:8px}</style>');return;}
  const file=path.resolve(root,'.'+decodeURIComponent(req.url));
  if(!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}
  try{res.setHeader('Content-Type',file.endsWith('.js')?'text/javascript':'application/octet-stream');res.end(await fs.readFile(file));}catch{res.writeHead(404).end();}
 });
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const browser=await chromium.launch({headless:true,args:['--no-sandbox'],executablePath:process.env.HL_CHROMIUM_PATH||chromium.executablePath()}).catch(e=>{server.close();throw e;});
 const results=[];
 try{for(const width of [320,360,390,440]){
  const ctx=await browser.newContext({viewport:{width,height:844},isMobile:true,hasTouch:true});const page=await ctx.newPage();const errors=[];page.on('pageerror',e=>errors.push(String(e)));
  await page.route('https://cdn.jsdelivr.net/**',async route=>{
   const rel=route.request().url().split('@')[1].split('/').slice(1).join('/');
   await route.fulfill({body:await fs.readFile(path.join(root,decodeURIComponent(rel))),contentType:/\.png$/i.test(rel)?'image/png':'image/jpeg'});
  });
  await page.goto(`http://127.0.0.1:${server.address().port}/`);
  await page.evaluate(async()=>{const {createUI}=await import('/modules/hormone-ledger/src/ui.js');window.ui=createUI(document);document.body.append(ui.host);ui.gallery.show(0);ui.render({角色荷尔蒙:{测试:37},角色活体铠甲:{测试:'无'}});});
  const left=page.getByRole('button',{name:'上一页',exact:true}),right=page.getByRole('button',{name:'下一页',exact:true}),enter=page.getByRole('button',{name:'进入荷尔蒙档案'}),back=page.getByRole('button',{name:'返回锁屏'}),label=page.locator('.hl-page');
  const index=()=>page.evaluate(()=>ui.gallery.index);
  assert(await left.isDisabled());await right.tap();assert.equal(await index(),1);assert(await enter.isVisible());
  await page.evaluate(()=>ui.gallery.show(2));await left.tap();assert.equal(await label.textContent(),'2 / 61');await right.tap();await right.tap();assert.equal(await label.textContent(),'4 / 61');
  await page.evaluate(()=>ui.gallery.show(60));assert(await right.isDisabled());await left.tap();assert.equal(await index(),59);assert(await enter.isVisible());
  // Pointer gesture uses the same primary pointer sequence as touch input.
  const swipe=async dx=>page.evaluate(dx=>{const p=ui.gallery.panel;for(const [type,x]of [['pointerdown',180],['pointermove',180+dx],['pointerup',180+dx]])p.dispatchEvent(new PointerEvent(type,{bubbles:true,isPrimary:true,button:0,pointerId:7,clientX:x,clientY:200}));},dx);
  await page.evaluate(()=>ui.gallery.show(16));await swipe(-80);assert.equal(await index(),17);await swipe(80);assert.equal(await index(),16);
  for(let i=0;i<3;i++){
   await enter.tap();assert(await back.isVisible());assert.equal(await page.evaluate(()=>ui.gallery.panel.hidden),true);assert.equal(await page.locator('.hl-gallery>img').getAttribute('src'),null);
   await back.tap();assert.equal(await label.textContent(),'17 / 61');
   await page.waitForFunction(()=>{const img=ui.gallery.panel.querySelector('img');return img.complete&&img.naturalWidth>0;});
   await right.tap();assert.equal(await index(),17);await left.tap();assert.equal(await index(),16);
   assert.equal(await page.locator('.hl-card').textContent(),'测试37 / 100活体铠甲 · 无');
  }
  const geometry=await page.evaluate(()=>{const s=ui.host.shadowRoot,p=s.querySelector('.hl-page').getBoundingClientRect(),buttons=[...s.querySelectorAll('.hl-page-button')].map(b=>{const r=b.getBoundingClientRect();return {w:r.width,h:r.height,overlap:!(r.right<=p.left||r.left>=p.right)};});return{buttons,overflow:document.documentElement.scrollWidth>innerWidth,hosts:document.querySelectorAll('.hormone-ledger-host').length};});
  assert(!geometry.overflow);assert.equal(geometry.hosts,1);for(const b of geometry.buttons){assert(b.w>=44&&b.h>=44);assert(!b.overlap);}
  await enter.tap();const r=await back.boundingBox();assert(r.width>=44&&r.height>=44);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  assert.equal(errors.length,0);await page.screenshot({path:path.join(__dirname,`evidence/candidate3-${width}.png`)});results.push({width,status:'PASS',checks:'boundaries, middle pages, gestures, isolation, 17/61 return with decoded image, three reentries, state, 44px targets, no overflow, single UI'});await ctx.close();
 }
 await fs.writeFile(path.join(__dirname,'evidence/candidate3-navigation.json'),JSON.stringify({status:'PASS',results,real_android_sillytavern:'pending'},null,2)+'\n');console.log(JSON.stringify(results));
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
