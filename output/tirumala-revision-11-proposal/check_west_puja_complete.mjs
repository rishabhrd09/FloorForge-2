import { chromium } from '/Users/rishabh/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import fs from 'node:fs/promises';
const dir='/Users/rishabh/coding_claude_projects/floor_plan_projects/Design_aesthtic_3d_home/output/tirumala-revision-11-proposal';
const browser=await chromium.launch({headless:true});
const page=await browser.newPage({viewport:{width:768,height:1400},deviceScaleFactor:1});
const errors=[];page.on('pageerror',e=>errors.push(String(e)));
await page.goto('file://'+dir+'/west-puja-complete-preview.html');
const frame=page.frameLocator('iframe');
await frame.locator('.tr11-plan svg').waitFor();
const records=[];
for(const width of [768,360]) {
  await page.setViewportSize({width,height:1400});
  for(const option of ['square','compact','deep']) {
    await frame.locator('#tr11-option').selectOption(option);
    for(const floor of ['ground','first']) {
      await frame.locator('#tr11-floor').selectOption(floor);
      await frame.locator('#tirumala-west-puja').screenshot({path:`${dir}/west-puja-${option}-${floor}-${width}.png`});
      records.push(await frame.locator('#tirumala-west-puja').evaluate(root=>({
        width:root.clientWidth,scroll:root.scrollWidth,
        option:root.querySelector('#tr11-option').value,floor:root.querySelector('#tr11-floor').value,
        room:root.querySelector('#tr11-room').value,
        summary:root.querySelector('.tr11-summary').textContent,
        prayerArrow:!!root.querySelector('[data-prayer-facing="east"]'),
        overflow:[...root.querySelectorAll('svg text')].filter(e=>{const b=e.getBoundingClientRect(),p=root.getBoundingClientRect();return b.left<p.left-1||b.right>p.right+1;}).map(e=>e.textContent)
      })));
    }
  }
}
await frame.locator('#tr11-floor').selectOption('ground');
await frame.locator('#tr11-routes').uncheck();
if(await frame.locator('[data-prayer-facing="east"]').count()!==1)errors.push('Prayer direction arrow disappears with route overlay off');
await frame.locator('#tr11-room').selectOption('K');
const result={errors,records};
await fs.writeFile(dir+'/west-puja-preview-check.json',JSON.stringify(result,null,2));
console.log(JSON.stringify(result,null,2));
await browser.close();
if(errors.length||records.some(r=>r.scroll>r.width||r.overflow.length||(r.floor==='ground'&&!r.prayerArrow)))process.exitCode=1;
