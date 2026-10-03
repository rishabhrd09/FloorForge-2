import {mkdirSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');

const root = process.cwd();
const out = resolve(root, 'tmp/pdfs/views');
mkdirSync(out, {recursive:true});
const browser = await chromium.launch({headless:true,args:[
  '--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist',
]});
try {
  const page = await browser.newPage({viewport:{width:1800,height:1200},deviceScaleFactor:1});
  const errors=[];
  page.on('pageerror', e => errors.push(e.message));
  await page.goto(pathToFileURL(resolve(root,'examples/gallery/my-desired-home/preview.html')).href);
  await page.waitForFunction(()=>window.__ff?.ready, null, {timeout:180000});
  await page.addStyleTag({content:'header,aside,.tools,.status,.ffhud{display:none!important}main{display:block!important;height:100vh!important}section{height:100vh!important}body{margin:0!important}'});
  await page.evaluate(()=>{
    const v=window.__ff.viewer;
    v.frameInsets={top:0,bottom:0,left:0,right:0};
    v.setFocus(true); v.resize(); v.paused=false; v.tour=false;
  });
  const records=[];
  for(const [name,floor,mode] of [['ground-3d',0,'dollhouse'],['first-3d',1,'dollhouse'],['roof-3d',2,'dollhouse'],['exterior-3d',0,'solid']]){
    await page.evaluate(({floor,mode})=>{
      const v=window.__ff.viewer;
      v.setFloor(floor); v.setMode(mode); v.setGrade('overcast');
      v.scene.background=v.env.sun.color.clone().set('#ffffff');
      v.scene.fog=null;
      if(v.groundMesh)v.groundMesh.visible=false;
      v.fitHouse({fill:.87,animate:false}); v.dirty=true;
    },{floor,mode});
    await page.waitForTimeout(1500);
    const raw=await page.evaluate(async()=>{
      const b=await window.__ff.viewer.snapshot({width:2400});
      const bytes=new Uint8Array(await b.arrayBuffer());
      let s=''; for(let i=0;i<bytes.length;i+=32768)s+=String.fromCharCode(...bytes.subarray(i,i+32768));
      return btoa(s);
    });
    writeFileSync(resolve(out,name+'.png'),Buffer.from(raw,'base64'));
    const state=await page.evaluate(()=>({planHash:window.__ff.scene.planHash,floor:window.__ff.viewer.floor,mode:window.__ff.viewer.mode}));
    records.push({name,...state}); console.log('Captured '+name+' '+state.planHash.slice(0,12));
  }
  writeFileSync(resolve(out,'capture-checks.json'),JSON.stringify({records,errors},null,2));
  if(errors.length)throw new Error(errors.join('\n'));
} finally {await browser.close();}
