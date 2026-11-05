import { chromium } from '/Users/rishabh/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import fs from 'node:fs/promises';
const dir='/Users/rishabh/coding_claude_projects/floor_plan_projects/Design_aesthtic_3d_home/output/tirumala-revision-11-proposal';
const browser=await chromium.launch({headless:true});
const page=await browser.newPage({viewport:{width:768,height:1100},deviceScaleFactor:1});
const errors=[];page.on('pageerror',e=>errors.push(String(e)));
await page.goto('file://'+dir+'/puja-options-preview.html');
const frame=page.frameLocator('iframe');
await frame.locator('.tpo-plan svg').waitFor();
const records=[];
for(const width of [768,360]) {
  await page.setViewportSize({width,height:1100});
  for(const option of ['swap','compact','niche']) {
    await frame.locator('#tpo-option').selectOption(option);
    await frame.locator('#tirumala-puja-options').screenshot({path:`${dir}/puja-${option}-${width}.png`});
    records.push(await frame.locator('#tirumala-puja-options').evaluate((root)=>({
      width:root.clientWidth,scroll:root.scrollWidth,
      option:root.querySelector('#tpo-option').value,
      values:root.querySelector('.tpo-values').textContent,
      route:root.querySelector('.tpo-route').textContent,
      overflow:[...root.querySelectorAll('svg text')].filter(e=>{const b=e.getBoundingClientRect(),p=root.getBoundingClientRect();return b.left<p.left-1||b.right>p.right+1;}).map(e=>e.textContent)
    })));
  }
}
await frame.locator('#tpo-routes').uncheck();
await frame.locator('#tpo-routes').check();
const result={errors,records};
await fs.writeFile(dir+'/puja-preview-check.json',JSON.stringify(result,null,2));
console.log(JSON.stringify(result,null,2));
await browser.close();
if(errors.length||records.some(r=>r.scroll>r.width||r.overflow.length))process.exitCode=1;
