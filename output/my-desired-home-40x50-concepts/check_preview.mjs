import { chromium } from '/Users/rishabh/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import fs from 'node:fs/promises';
const dir='/Users/rishabh/coding_claude_projects/floor_plan_projects/Design_aesthtic_3d_home/output/my-desired-home-40x50-concepts';
const browser=await chromium.launch({headless:true});
const page=await browser.newPage({viewport:{width:784,height:1100},deviceScaleFactor:1});
const errors=[];page.on('pageerror',e=>errors.push(String(e)));
await page.goto('file://'+dir+'/preview.html');
const f=page.frameLocator('iframe');
await f.locator('#dh-drawing svg').waitFor();
const checks=[];
for(const width of [784,360]){
 await page.setViewportSize({width,height:1100});
 for(const option of ['A','B','C','D','original']){
  await f.locator('#dh-option').selectOption(option);
  for(const floor of ['ground','first']){
   await f.locator('#dh-floor').selectOption(floor);
   await f.locator('#desired-home-concepts').screenshot({path:`${dir}/${option}-${floor}-${width}.png`});
   const result=await f.locator('#desired-home-concepts').evaluate(root=>{
    const b=root.getBoundingClientRect();
    const texts=[...root.querySelectorAll('svg text')];
    const overflow=texts.filter(t=>{const a=t.getBoundingClientRect();return a.left<b.left-1||a.right>b.right+1;}).map(t=>t.textContent);
    return {rootWidth:root.clientWidth,scrollWidth:root.scrollWidth,overflow,detail:root.querySelector('#dh-detail').textContent};
   });
   checks.push({width,option,floor,...result});
  }
 }
 await f.locator('#dh-floor').selectOption('site');
 await f.locator('#desired-home-concepts').screenshot({path:`${dir}/site-${width}.png`});
 checks.push({width,view:'site',...await f.locator('#desired-home-concepts').evaluate(root=>({rootWidth:root.clientWidth,scrollWidth:root.scrollWidth}))});
}
await page.setViewportSize({width:784,height:1100});
await f.locator('#dh-option').selectOption('A');
await f.locator('#dh-floor').selectOption('ground');
await f.locator('#dh-room').selectOption('DR');
const selectedDrawing=await f.locator('#dh-detail').textContent();
await f.locator('#dh-furniture').uncheck();
const result={errors,checks,selectedDrawing,controlsWorking:selectedDrawing.includes('ONE wooden door')};
await fs.writeFile(dir+'/preview-check.json',JSON.stringify(result,null,2));
console.log(JSON.stringify({errors,overflow:checks.filter(x=>x.scrollWidth>x.rootWidth||(x.overflow?.length)),controlsWorking:result.controlsWorking},null,2));
await browser.close();
if(errors.length||checks.some(x=>x.scrollWidth>x.rootWidth||(x.overflow?.length))||!result.controlsWorking)process.exitCode=1;
