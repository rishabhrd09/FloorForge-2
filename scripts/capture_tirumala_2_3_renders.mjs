import {spawn} from 'node:child_process';
import {copyFileSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';

const {chromium} = await import(
  process.env.PLAYWRIGHT_MODULE ||
    '/Users/rishabh/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs'
);

const root = resolve(import.meta.dirname, '..');
const port = 8898;
const url = `http://127.0.0.1:${port}`;

const server = spawn(
  resolve(root, '.venv/bin/python'),
  ['-m', 'floorforge', 'serve', '--no-browser', '--port', String(port), '--out', mkdtempSync('/tmp/ff-tirumala-2-3-')],
  {cwd: root, stdio: ['ignore', 'pipe', 'pipe']}
);
server.stderr.on('data', d => process.stderr.write(d));

let browser;
const slugs=process.env.TIRUMALA_SAMPLES?process.env.TIRUMALA_SAMPLES.split(','):['tirumala-2','tirumala-3'];
const checkPath=resolve(root,'output/tirumala-spacious-gallery/browser-checks.json');
const checks = process.env.TIRUMALA_RESUME ? JSON.parse(readFileSync(checkPath)).checks.filter(c=>
  ['tirumala-2','tirumala-3'].some(s=>!slugs.includes(s)&&c.name.startsWith(s))) : [];
const errors = [];
const check = (name, pass, detail = null) => {
  checks.push({name, pass: !!pass, ...(detail ? {detail} : {})});
  console.log(pass ? 'PASS' : 'FAIL', name, detail ? JSON.stringify(detail) : '');
  if (!pass) throw Error(name);
};

try {
  for (let i = 0; i < 120; i++) {
    try {
      if ((await fetch(url + '/api/session')).ok) break;
    } catch {}
    await new Promise(r => setTimeout(r, 200));
  }

  browser = await chromium.launch({
    headless: true,
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'],
  });

  // 1. Render 2D SVG plans (dimensioned & material overhead) at crisp 2x resolution
  const svgPage = await browser.newPage({
    viewport: {width: 1480, height: 1840},
    deviceScaleFactor: 2,
  });
  for (const slug of slugs) {
    const rendersDir = resolve(root, `examples/gallery/${slug}/renders`);
    mkdirSync(rendersDir, {recursive: true});
    for (const svgBase of ['plan-2d-dimensioned', 'plan-2d-material-overhead', 'plan-first-floor']) {
      const svgUrl = `${url}/samples/${slug}/renders/${svgBase}.svg`;
      const resp = await svgPage.goto(svgUrl);
      check(`${slug} ${svgBase}.svg loads HTTP 200`, resp && resp.ok());
      await svgPage.waitForTimeout(250);
      const svgEl = svgPage.locator('svg').first();
      await svgEl.screenshot({path: resolve(rendersDir, `${svgBase}.png`)});
      console.log(`Rendered ${slug}/renders/${svgBase}.png`);
    }
  }
  await svgPage.close();

  // 2. Open Studio & verify + capture 3D views for tirumala-2 and tirumala-3
  const page = await browser.newPage({
    viewport: {width: 1600, height: 1080},
    deviceScaleFactor: 1,
  });
  page.on('pageerror', e => errors.push(e.message));

  await page.goto(url);
  await page.waitForFunction(
    () =>
      !document.querySelector('[data-start="continue"]')?.disabled &&
      document.querySelector('#workspace-project option[value="sample:tirumala-2"]') &&
      document.querySelector('#workspace-project option[value="sample:tirumala-3"]') &&
      window.__ffApp?.viewer &&
      window.__ff?.ready,
    null,
    {timeout: 180000, polling: 100}
  );

  await page.click('[data-start="continue"]');
  await page.click('#design-result');
  await page.locator('#workspace-project').waitFor({state: 'visible', timeout: 30000});

  for (const slug of slugs) {
    const rendersDir = resolve(root, `examples/gallery/${slug}/renders`);
    const thumbPath = resolve(root, `examples/gallery/thumbnails/${slug}.png`);

    await page.selectOption('#workspace-project', `sample:${slug}`);
    await page.waitForFunction(
      target => window.__ff?.buildId === target && !window.__ffApp.draftStale,
      `sample:${slug}`,
      {timeout: 120000, polling: 100}
    );
    await page.evaluate(() => {
      const toast = document.getElementById('toast');
      if (toast) toast.hidden = true;
    });

    const state = await page.evaluate(() => ({
      buildId: window.__ff.buildId,
      planHash: window.__ff.scene.planHash,
      storeys: window.__ff.building.storeys,
      roomCount: window.__ff.building.spaces.length,
      widthFt: document.getElementById('width').value,
      depthFt: document.getElementById('depth').value,
      facing: document.getElementById('facing').value,
      meshCount: window.__ff.viewer?.meshes?.length || 0,
    }));
    check(
      `${slug} loads in Studio with 40x50 ft East-facing ground-floor layout (storeys=2, 21 spaces) and populated 3D meshes`,
      state.storeys === 2 && state.roomCount === 21 && state.widthFt === '40' && state.depthFt === '50' && state.facing === '90' && state.meshCount > 20,
      state
    );
    const revision=await page.evaluate(()=>({
      display:window.__ff.building.planning.tirumalaMeta.displayOption,
      title:document.querySelector('#tirumala-options-bar .overline').textContent,
      area:window.__ff.building.spaces.find(r=>r.id==='g-care').area_m2/.09290304,
      profile:!!window.__ff.scene.presentation,
      masterShortcut:!!document.querySelector('#tirumala-room-view option[value="interior_master"]')
    }));
    const display=slug==='tirumala-3'?'P13':'P12';
    check(`${slug}: current ICU revision, spacious profile and interior shortcuts loaded`,
      revision.display===display && revision.title.includes(display) && revision.profile && revision.masterShortcut &&
      Math.abs(revision.area-(slug==='tirumala-3'?150.8236:158.6279))<.01,revision);

    // Verify Specifications dialog
    await page.locator('.project-workspace [data-project-view="specs"]').click();
    await page.waitForTimeout(250);
    const specsText = await page.locator('#project-specs-dialog').innerText();
    check(
      `${slug} specifications dialog displays title and Home ICU`,
      specsText.includes(slug === 'tirumala-2' ? 'Tirumala 2' : 'Tirumala 3') && specsText.includes('Home ICU')
    );
    await page.evaluate(() => {
      const dlg = document.getElementById('project-specs-dialog');
      if (dlg?.open) dlg.close();
    });
    await page.waitForTimeout(150);

    // Switch to 3D view and expand #scene to full 1600x1040 architectural frame for clean canvas renders
    await page.locator('.project-workspace [data-project-view="3d"]').click();
    await page.waitForTimeout(450);

    await page.evaluate(() => {
      const sceneEl = document.getElementById('scene');
      sceneEl.style.position = 'fixed';
      sceneEl.style.inset = '0';
      sceneEl.style.width = '1600px';
      sceneEl.style.height = '1040px';
      sceneEl.style.zIndex = '9999';
      window.__ff.viewer.resize();
    });
    await page.waitForTimeout(350);

    const captureSolidCamera = async (camName, fileName, opts = {}) => {
      if(opts.doorState){
        await page.evaluate(state=>document.querySelector(`[data-icu-door-state="${state}"]`).click(),opts.doorState);
      }
      const ok = await page.evaluate(
        ({camName, opts}) => {
          const v = window.__ff.viewer;
          v.paused = true;
          v.setQuality('balanced');
          v.setSiteMode('proposed');
          v.setGrade('day');
          v.setMode('solid');
          if (typeof opts.carVisible === 'boolean') {
            v.setCarVisible(opts.carVisible);
          } else {
            v.setCarVisible(true);
          }
          const res = v.setNamedCamera(camName);
          const cam = v.data.cameras[camName];
          if (cam.enter_walk) {
            for(let i=0;i<90;i++)v.walker.update(1/90,{forward:0,strafe:0});
            const displacement=Math.hypot(v.walker.position.x-cam.position[0],v.walker.position.z+cam.position[1]);
            const floorError=Math.abs(v.walker.position.y-(cam.position[2]-1.63));
            if(!v.walker.onGround || displacement>.05 || floorError>.025)throw Error(`Unsafe room view ${camName}: drift ${displacement}, floor ${floorError}`);
            v.camera.position.copy(v.walker.eyePosition(v.camera.position.clone()));
            v.camera.rotation.set(v.walker.pitch,v.walker.yaw,0);
          }
          v.metered=null;
          if(opts.doorState){
            for(let i=0;i<120;i++)v.openings.update(1/60);
          }
          if (opts.indoor) {
            v.indoor = 1;
            v.updateProbe();
            v.updateLights(true);
            v.adapt(3);
            v.hud.show(false);
          } else {
            v.indoor = 0;
            v.updateProbe();
            v.adapt(2.5);
          }
          v.dirty = true;
          v.composer.render(0);
          return res;
        },
        {camName, opts}
      );
      check(`${slug} camera ${camName} activated`, ok);
      if(opts.doorState){
        const values=await page.evaluate(()=>Object.fromEntries(window.__ff.viewer.openings.items.filter(i=>['icu-glass-living','icu-glass-living-wood'].includes(i.id)).map(i=>[i.id,i.value])));
        check(`${slug} ${opts.doorState} entrance button operates both layers`,values['icu-glass-living']===(opts.doorState==='open'?1:0)&&values['icu-glass-living-wood']===(opts.doorState==='private'?0:1),values);
      }
      await page.waitForTimeout(750);
      const outPath = resolve(rendersDir, fileName);
      await page.locator('#scene').screenshot({path: outPath});
      if (opts.carVisible === false) {
        await page.evaluate(() => {
          window.__ff.viewer.setCarVisible(true);
        });
      }
      return outPath;
    };

    // 1. Real-time PBR East exterior view
    await captureSolidCamera('exterior_east', 'exterior-east.png');

    // 2. Real-time PBR Northeast exterior view (+ thumbnail)
    const nePath = await captureSolidCamera('exterior_northeast', 'exterior-northeast.png');
    copyFileSync(nePath, thumbPath);

    for(const [state,file] of [['private','icu-door-wood-closed'],['glass','icu-door-glass-revealed'],['open','icu-door-both-open']]){
      await captureSolidCamera('icu_layered_entry',file+'.png',{indoor:true,doorState:state});
    }

    for (const name of ['living_double_height','upper_gallery','upper_master','upper_office','upper_guest','upper_terrace']) {
      await captureSolidCamera(name, name.replaceAll('_','-')+'.png', {indoor:name!=='upper_terrace'});
    }

    // 3. 3D Roof-off cutaway view (with walls & glazed doors/windows clipped at 1.48 m)
    const cutOk = await page.evaluate(() => {
      const v = window.__ff.viewer;
      v.setSiteMode('proposed');
      v.setGrade('day');
      v.setCarVisible(true);
      v.setFloor(0);
      v.setMode('dollhouse');
      const res = v.setNamedCamera('cutaway_roof_off');
      v.materials.clipPlane.constant = 1.48;
      for (const mesh of v.meshes) {
        const b = mesh.userData.bucket;
        if (b.cls === 'opening' && b.floor === 0) {
          mesh.visible = true;
          if (mesh.material && !mesh.material.clippingPlanes?.length) {
            mesh.material = mesh.material.clone();
            mesh.material.clippingPlanes = [v.materials.clipPlane];
          }
        }
      }
      v.adapt(2.5);
      v.dirty = true;
      v.composer.render(0);
      return res;
    });
    check(`${slug} camera cutaway_roof_off activated`, cutOk);
    await page.waitForTimeout(800);
    await page.locator('#scene').screenshot({path: resolve(rendersDir, 'cutaway-3d-roof-off.png')});

    // 4. Kitchen / living / dining interior view
    await captureSolidCamera('interior_kitchen_living_dining', 'interior-kitchen-living-dining.png', {indoor: true});

    // 5. ICU-to-veranda and garden-facing view
    await captureSolidCamera('interior_icu_veranda_garden', 'interior-icu-veranda-garden.png', {indoor: true});
    for(const name of ['interior_veranda_living','interior_master','interior_drawing']){
      await captureSolidCamera(name,name.replaceAll('_','-')+'.png',{indoor:true});
    }

    // 6. Close-up showing flooring, glazing, and the lower porch (-6 in provisional drop, car hidden to reveal full porch & ICU notch/veranda return)
    await captureSolidCamera('closeup_flooring_glazing_porch', 'closeup-flooring-glazing-lower-porch.png', {carVisible: false});

    // Restore #scene layout before switching sample
    await page.evaluate(() => {
      const sceneEl = document.getElementById('scene');
      sceneEl.style.position = '';
      sceneEl.style.inset = '';
      sceneEl.style.width = '';
      sceneEl.style.height = '';
      sceneEl.style.zIndex = '';
      window.__ff.viewer.resize();
    });
    await page.waitForTimeout(200);
  }

  check('Zero uncaught page errors during Tirumala 2 and Tirumala 3 studio & render verification', errors.length === 0, errors);
} catch(e) {
  errors.push(e.message);throw e;
} finally {
  writeFileSync(resolve(root,'output/tirumala-spacious-gallery/browser-checks.json'),JSON.stringify({checks,errors},null,2));
  await browser?.close();
  server.kill('SIGTERM');
}
