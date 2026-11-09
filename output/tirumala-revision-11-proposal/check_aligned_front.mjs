import { chromium } from '/Users/rishabh/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import fs from 'node:fs/promises';
const dir='/Users/rishabh/coding_claude_projects/floor_plan_projects/Design_aesthtic_3d_home/output/tirumala-revision-11-proposal';
const browser=await chromium.launch({headless:true});
const page=await browser.newPage({viewport:{width:784,height:1200},deviceScaleFactor:1});
const errors=[];page.on('pageerror',e=>errors.push(String(e)));
await page.goto('file://'+dir+'/aligned-front-preview.html');
const frame=page.frameLocator('iframe');
await frame.locator('.tr11-plan svg').waitFor();
await frame.locator('#tirumala-r11-aligned').screenshot({path:dir+'/aligned-front-ground.png'});
await frame.locator('#tr11-floor').selectOption('first');
await frame.locator('#tr11-room').selectOption('US');
await frame.locator('#tirumala-r11-aligned').screenshot({path:dir+'/aligned-front-first.png'});
await frame.locator('#tr11-routes').check();
const check=async()=>frame.locator('#tirumala-r11-aligned').evaluate(root=>({
  width:root.clientWidth,scroll:root.scrollWidth,svg:!!root.querySelector('svg'),
  selected:root.querySelector('#tr11-room').value,
  detail:root.querySelector('.tr11-detail').textContent,
  overflow:[...root.querySelectorAll('svg text')].filter(e=>{
    const b=e.getBoundingClientRect(),p=root.getBoundingClientRect();return b.left<p.left-1||b.right>p.right+1;
  }).map(e=>e.textContent)
}));
const desktop=await check();
await page.setViewportSize({width:360,height:1100});
await frame.locator('#tr11-floor').selectOption('ground');
await frame.locator('#tr11-room').selectOption('EN');
await frame.locator('#tirumala-r11-aligned').screenshot({path:dir+'/aligned-front-mobile-ground.png'});
const mobileGround=await check();
await frame.locator('#tr11-floor').selectOption('first');
await frame.locator('#tr11-room').selectOption('U1');
await frame.locator('#tirumala-r11-aligned').screenshot({path:dir+'/aligned-front-mobile-first.png'});
const mobileFirst=await check();
const result={errors,desktop,mobileGround,mobileFirst};
await fs.writeFile(dir+'/aligned-front-check.json',JSON.stringify(result,null,2));
console.log(JSON.stringify(result,null,2));
await browser.close();
if(errors.length||[desktop,mobileGround,mobileFirst].some(r=>r.scroll>r.width||r.overflow.length))process.exitCode=1;
