// Physically follow the connected route, with no teleportation between floors.
import {writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const {chromium}=await import('/Users/rishabh/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs');
const browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
try {
 const page=await browser.newPage({viewport:{width:1000,height:800}});
 await page.goto('file://'+resolve('examples/gallery/tirumala-5/preview.html'));
 await page.waitForFunction(()=>window.__ff?.ready,{timeout:60000});
 const result=await page.evaluate(()=>{
  const v=window.__ff.viewer,w=v.walker;v.setMode('walk');v.paused=true;
  for(const item of v.openings.items)item.goal=1;
  for(let i=0;i<120;i++)v.openings.update(1/60);
  w.position.set(1.9,.015,-5.6);w.velocity.set(0,0,0);
  const points=[
   ['ground south flight',.7,5.6,.35],['ground west flight',.7,8.35,1.575],
   ['first landing',5.45,8.35,3.508],['gallery',6.95,8.35,3.508],
   ['terrace door',6.95,4.1,3.508],['pergola approach',5.9,3.35,3.508],
   ['past north planter',4.55,3.85,3.508],['behind coffee table',3.25,4.35,3.508],
   ['past south planter',3.0,3.45,3.508],['terrace clear aisle',1.9,3.45,3.508],['terrace approach',.7,4.1,3.508],
   ['new west flight',.7,8.35,5.262],['second landing',4.8,8.35,7.016],
   ['second hall',4.8,9.7,7.016],['hall garden door',4.8,13.3,7.016],
   ['roof garden',6.1,13.3,7.016]
  ];
  const segments=[];
  for(const [name,x,y,h] of points){
   let error=99,frames=0;
   while(frames++<1800){const dx=x-w.position.x,dy=y+w.position.z;error=Math.hypot(dx,dy);
    if(error<.055)break;w.yaw=Math.atan2(-dx,dy);w.update(1/120,{forward:1,strafe:0});}
   w.velocity.set(0,0,0);for(let i=0;i<20;i++)w.update(1/120,{forward:0,strafe:0});
   segments.push({name,target:[x,y,h],position:[w.position.x,-w.position.z,w.position.y],error,grounded:w.onGround,
    pass:error<.12&&w.onGround&&Math.abs(w.position.y-h)<.04});
   if(!segments.at(-1).pass)break;
  }
  return {planHash:v.data.planHash,segments,passed:segments.length===points.length&&segments.every(s=>s.pass)};
 });
 writeFileSync(resolve('output/tirumala-5-delivery/complete-stair-route.json'),JSON.stringify(result,null,2));
 console.log(JSON.stringify(result,null,2));
 if(!result.passed)process.exitCode=1;
} finally {await browser.close();}
