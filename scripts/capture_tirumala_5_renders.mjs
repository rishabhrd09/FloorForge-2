import {spawn} from 'node:child_process';
import {copyFileSync, mkdirSync, mkdtempSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';

const {chromium} = await import(
  process.env.PLAYWRIGHT_MODULE ||
    '/Users/rishabh/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs'
);

const root = resolve(import.meta.dirname, '..');
const port = 8901;
const url = `http://127.0.0.1:${port}`;
const slug = 'tirumala-5';

const server = spawn(
  resolve(root, '.venv/bin/python'),
  ['-m', 'floorforge', 'serve', '--no-browser', '--port', String(port), '--out', mkdtempSync('/tmp/ff-tirumala-5-')],
  {cwd: root, stdio: ['ignore', 'pipe', 'pipe']}
);
server.stderr.on('data', d => process.stderr.write(d));

let browser;
const outReportDir = resolve(root, 'output/tirumala-5-delivery');
mkdirSync(outReportDir, {recursive: true});
const checks = [];
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

  // 1. Render 2D SVG plans (dimensioned, material overhead, first floor, and site-context-plan) at crisp 2x resolution
  const svgPage = await browser.newPage({
    viewport: {width: 1620, height: 1860},
    deviceScaleFactor: 2,
  });
  const rendersDir = resolve(root, `examples/gallery/${slug}/renders`);
  mkdirSync(rendersDir, {recursive: true});
  for (const svgBase of ['plan-2d-dimensioned', 'plan-2d-material-overhead', 'plan-first-floor', 'plan-second-floor', 'site-context-plan']) {
    const svgUrl = `${url}/samples/${slug}/renders/${svgBase}.svg`;
    const resp = await svgPage.goto(svgUrl);
    check(`${slug} ${svgBase}.svg loads HTTP 200`, resp && resp.ok());
    await svgPage.waitForTimeout(250);
    const svgEl = svgPage.locator('svg').first();
    const pngPath = resolve(rendersDir, `${svgBase}.png`);
    await svgEl.screenshot({path: pngPath});
    copyFileSync(pngPath, resolve(outReportDir, `${svgBase}.png`));
    console.log(`Rendered ${slug}/renders/${svgBase}.png`);
  }
  await svgPage.close();

  // 2. Open Studio & verify + capture 3D views for tirumala-4
  const page = await browser.newPage({
    viewport: {width: 1600, height: 1080},
    deviceScaleFactor: 1.5,
  });
  page.on('pageerror', e => errors.push(e.message));
  page.on('console', m => { if(m.type()==='error') errors.push(m.text()); });

  await page.goto(url);
  await page.waitForFunction(
    () =>
      !document.querySelector('[data-start="continue"]')?.disabled &&
      document.querySelector('#workspace-project option[value="sample:tirumala-4"]') &&
      document.querySelector('#workspace-project option[value="sample:tirumala-3"]') &&
      document.querySelector('#workspace-project option[value="sample:tirumala-2"]') &&
      window.__ffApp?.viewer &&
      window.__ff?.ready,
    null,
    {timeout: 180000, polling: 100}
  );

  await page.click('[data-start="continue"]');
  await page.click('#design-result');
  await page.locator('#workspace-project').waitFor({state: 'visible', timeout: 30000});

  const thumbPath = resolve(root, `examples/gallery/thumbnails/${slug}.png`);

  await page.selectOption('#workspace-project', `sample:${slug}`);
  await page.waitForFunction(
    target => window.__ff?.buildId === target && !window.__ffApp.draftStale,
    `sample:${slug}`,
    {timeout: 45000, polling: 100}
  ).catch(async e => {
    const state=await page.evaluate(()=>({build:window.__ff?.buildId,stale:window.__ffApp?.draftStale,
      toast:document.querySelector('#toast')?.textContent,project:window.__ffApp?.collect()}));
    writeFileSync(resolve(outReportDir,'load-debug.json'),JSON.stringify(state,null,2));
    console.log('Load failure',state.build,state.toast);
    throw e;
  });
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
    defaultCarVisible: window.__ff.scene.defaultCarVisible,
    carVisible: window.__ff.viewer?.carVisible,
    carButtonText: document.getElementById('toggle-car')?.textContent,
    siteMode: window.__ff.viewer?.siteMode,
    siteModeButtonText: document.getElementById('toggle-site-mode')?.textContent,
  }));
  check(
    `${slug} loads in Studio with 40x50 ft East-facing G+2 layout (storeys=3, 23 spaces), empty car porch default (carVisible=false), and Proposed site mode`,
    state.storeys === 3 &&
      state.roomCount === 23 &&
      state.widthFt === '40' &&
      state.depthFt === '50' &&
      state.facing === '90' &&
      state.meshCount > 20 &&
      state.defaultCarVisible === false &&
      state.carVisible === false &&
      state.carButtonText === 'Show car' &&
      state.siteMode === 'proposed',
    state
  );

  const revision = await page.evaluate(() => ({
    display: window.__ff.building.planning.tirumalaMeta.displayOption,
    projectId: window.__ff.building.planning.tirumalaMeta.projectId,
    title: document.querySelector('#tirumala-options-bar .overline').textContent,
    area: window.__ff.building.spaces.find(r => r.id === 'g-care').area_m2 / 0.09290304,
    profile: window.__ff.scene.presentation?.style,
    reclinerShortcut: !!document.querySelector('#tirumala-room-view option[value="care_recliner_eye_level"]'),
    verandaOutlookShortcut: !!document.querySelector('#tirumala-room-view option[value="veranda_north_garden_outlook"]'),
  }));
  check(
    `${slug}: Plan A ICU geometry (201.1 sq ft), tirumala-4 presentation profile, and eye-level shortcuts loaded`,
    revision.display === 'Plan A' &&
      revision.projectId === 'tirumala-5' &&
      revision.title.includes('Tirumala 5') &&
      revision.profile === 'tirumala-5-plan-a' &&
      revision.reclinerShortcut &&
      revision.verandaOutlookShortcut &&
      Math.abs(revision.area - 15 * (4085.6 / 304.8)) < 0.01,
    revision
  );

  // Verify Specifications dialog
  await page.locator('.project-workspace [data-project-view="specs"]').click();
  await page.waitForTimeout(250);
  const specsText = await page.locator('#project-specs-dialog').innerText();
  check(
    `${slug} specifications dialog displays Tirumala 5 and Home ICU`,
    specsText.includes('Tirumala 5') && specsText.includes('Home ICU')
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

  const landscape = await page.evaluate(() => {
    const v=window.__ff.viewer;
    return {revision:v.data.exteriorRefinement?.revision,
      redBlocks:!!v.context.getObjectByName('colony-burgundyShrub'),
      pavedTexture:!!v.context.getObjectByName('colony-paverVerge')?.material.map,
      roadTexture:!!v.context.getObjectByName('colony-concreteRoad')?.material.map,
      grassPockets:v.context.userData.exteriorRefinement?.grassPockets,
      boundaryMaterial:v.data.nodes.find(n=>n.id.startsWith('boundary-east-cladding'))?.material,
      sun:v.env.sun.intensity,
      vacantLots:v.context.userData.vacantAdjoiningLots,
      facade:v.data.facadeRefinement,
      exteriorGlassOpacity:v.materials.get('t4-facade-glass').opacity};
  });
  check('Refined exterior uses leaf planting (no solid red blocks), textured paving/road, edged lawn and limestone boundary',
    !!landscape.revision && !landscape.redBlocks && landscape.pavedTexture && landscape.roadTexture &&
    landscape.grassPockets===4 && landscape.boundaryMaterial==='t4-boundary-limestone', landscape);
  check('Desired Home facade, substantial exterior glass and two vacant adjoining grass lots',
    landscape.facade?.source==='my-desired-home' && landscape.facade.exteriorFinishTriangles>100 &&
    landscape.facade.exteriorOpenings.length>20 && landscape.vacantLots===2 &&
    landscape.exteriorGlassOpacity===.19, landscape.facade);
  const realism = await page.evaluate(() => {
    const v=window.__ff.viewer;
    return {meshFaces:v.context.userData.realismRefinement?.fineMeshFaces,
      shadowRadius:v.env.radius, views:document.querySelectorAll('#tirumala-room-view optgroup option').length,
      geometryChanged:v.data.realismRefinement?.geometryChanged,
      northCameraX:v.data.cameras.ref_r08_north_garden.position[0],plotNorth:v.data.bounds[3]};
  });
  check('Site review has diamond mesh, shadow coverage, eight exterior views and an unobstructed north-road camera',
    realism.meshFaces===2 && realism.shadowRadius===43 && realism.views===8 &&
    realism.geometryChanged===false && realism.northCameraX>realism.plotNorth,realism);

  const captureSolidCamera = async (camName, fileName, opts = {}) => {
    const only=process.env.T5_CAPTURE_ONLY?.split(',');
    if(only && !only.includes(fileName)) return resolve(rendersDir,fileName);
    if (opts.doorState) {
      await page.evaluate(state => document.querySelector(`[data-icu-door-state="${state}"]`).click(), opts.doorState);
    }
    const ok = await page.evaluate(
      async ({camName, opts}) => {
        const v = window.__ff.viewer;
        v.paused = true;
        v.setQuality(opts.quality || 'high');
        v.setSiteMode(opts.siteMode || 'proposed');
        v.setGrade(opts.grade || 'day');
        v.setMode('solid');
        if (typeof opts.carVisible === 'boolean') {
          v.setCarVisible(opts.carVisible);
        } else {
          v.setCarVisible(false);
        }
        const res = v.setNamedCamera(camName);
        const cam = v.data.cameras[camName];
        if (cam.enter_walk) {
          for (let i = 0; i < 90; i++) v.walker.update(1 / 90, {forward: 0, strafe: 0});
          const displacement = Math.hypot(v.walker.position.x - cam.position[0], v.walker.position.z + cam.position[1]);
          const floorError = Math.abs(v.walker.position.y - (cam.position[2] - 1.63));
          if (!v.walker.onGround || displacement > 0.05 || floorError > 0.025) {
            throw Error(`Unsafe room view ${camName}: drift ${displacement}, floor ${floorError}`);
          }
          v.camera.position.copy(v.walker.eyePosition(v.camera.position.clone()));
          v.camera.rotation.set(v.walker.pitch, v.walker.yaw, 0);
        }
        v.metered = null;
        if (opts.doorState) {
          for (let i = 0; i < 120; i++) v.openings.update(1 / 60);
        }
        if (opts.indoor) {
          v.indoor = 1;
          v.updateProbe();
          if (v.env.probe?.statsReady) {
            await v.env.probe.statsReady;
          }
          v.updateLights(true);
          v.metered = null;
          v.adapt(10);
          v.hud.show(false);
        } else {
          v.indoor = 0;
          v.updateProbe();
          if (v.env.probe?.statsReady) {
            await v.env.probe.statsReady;
          }
          v.metered = null;
          v.adapt(10);
        }
        v.dirty = true;
        v.composer.render(0);
        return res;
      },
      {camName, opts}
    );
    check(`${slug} camera ${camName} (${fileName}) activated`, ok);
    if (opts.doorState) {
      const values = await page.evaluate(() =>
        Object.fromEntries(
          window.__ff.viewer.openings.items
            .filter(i => ['icu-glass-living', 'icu-glass-living-wood'].includes(i.id))
            .map(i => [i.id, i.value])
        )
      );
      check(
        `${slug} ${opts.doorState} entrance button operates both layers`,
        values['icu-glass-living'] === (opts.doorState === 'open' ? 1 : 0) &&
          values['icu-glass-living-wood'] === (opts.doorState === 'private' ? 0 : 1),
        values
      );
    }
    await page.waitForTimeout(700);
    const outPath = resolve(rendersDir, fileName);
    await page.locator('#scene').screenshot({path: outPath});
    copyFileSync(outPath, resolve(outReportDir, fileName));
    return outPath;
  };

  // Core exterior views (carVisible: false by default!)
  await captureSolidCamera('exterior_east', 'exterior-east.png');
  const nePath = await captureSolidCamera('exterior_northeast', 'exterior-northeast.png');
  copyFileSync(nePath, thumbPath);
  await captureSolidCamera('exterior_east', 'exterior-east-overcast.png', {grade:'overcast'});
  await captureSolidCamera('north_garden_passage', 'north-garden-passage.png');

  // Reference-matched colony views (R07, R11, R08, V01, R09, R14) + existing plot toggle view
  await captureSolidCamera('ref_r07_east_northwest', 'ref-r07-east-northwest.png');
  await captureSolidCamera('ref_r07_east_northwest', 'ref-r07-existing-plot.png', {siteMode: 'existing'});
  await captureSolidCamera('ref_r11_ne_corner', 'ref-r11-ne-corner.png');
  await captureSolidCamera('ref_r08_north_garden', 'ref-r08-north-garden.png');
  await captureSolidCamera('ref_v01_east_court_road', 'ref-v01-east-court-road.png');
  await captureSolidCamera('ref_r09_colony_junction', 'ref-r09-colony-junction.png');
  await captureSolidCamera('ref_r14_wall_pole_paving', 'ref-r14-wall-pole-paving.png');
  for(const name of ['ref_n03_north_frontage','ref_n02_northwest_utilities','ref_south_vacant','ref_west_vacant'])
    await captureSolidCamera(name,name.replaceAll('_','-')+'.png');

  // Layered ICU door state views
  for (const [state, file] of [
    ['private', 'icu-door-wood-closed'],
    ['glass', 'icu-door-glass-revealed'],
    ['open', 'icu-door-both-open'],
  ]) {
    await captureSolidCamera('icu_layered_entry', file + '.png', {indoor: true, doorState: state});
  }

  // Leave ICU doors closed (wood closed) for normal room renders, or glass revealed for ICU outlook
  await page.evaluate(() => {
    for (const item of window.__ff.viewer.openings.items) {
      if (item.id === 'icu-glass-living') item.value = item.goal = 0;
      if (item.id === 'icu-glass-living-wood') item.value = item.goal = 1;
    }
  });

  await captureSolidCamera('forecourt_utility','forecourt-utility.png',{indoor:false});
  await captureSolidCamera('under_stair_pantry','under-stair-pantry.png',{indoor:true});

  // Ground & First floor interior and terrace views
  await captureSolidCamera('veranda_north_garden_outlook', 'veranda-north-garden-outlook.png', {indoor: false});
  await captureSolidCamera('interior_icu_veranda_garden', 'interior-icu-veranda-garden.png', {indoor: true});
  await captureSolidCamera('interior_icu_veranda_garden', 'interior-icu-overcast.png', {indoor: true, grade: 'overcast'});
  await captureSolidCamera('care_recliner_eye_level', 'interior-icu-recliner-sightline.png', {indoor: true});
  await captureSolidCamera('interior_kitchen_living_dining', 'interior-kitchen-living-dining.png', {indoor: true});
  await captureSolidCamera('living_sofa_eye_level', 'interior-living-sofa-sightline.png', {indoor: true});
  await captureSolidCamera('interior_veranda_living', 'interior-veranda-living.png', {indoor: true});
  await captureSolidCamera('interior_master', 'interior-master.png', {indoor: true});
  await captureSolidCamera('interior_drawing', 'interior-drawing.png', {indoor: true});

  for (const name of ['living_double_height', 'upper_gallery', 'upper_master', 'upper_office', 'upper_guest', 'upper_terrace', 'second_hall', 'second_terrace', 'second_stair_arrival']) {
    await captureSolidCamera(name, name.replaceAll('_', '-') + '.png', {indoor: !['upper_terrace','second_terrace','second_stair_arrival'].includes(name)});
  }

  // 3D Roof-off cutaway view (with carVisible: false by default!)
  const cutOk = await page.evaluate(() => {
    const v = window.__ff.viewer;
    v.setSiteMode('proposed');
    v.setGrade('day');
    v.setCarVisible(false);
    v.setMode('dollhouse');
    v.setFloor(0);
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
  const cutPath = resolve(rendersDir, 'cutaway-3d-roof-off.png');
  await page.locator('#scene').screenshot({path: cutPath});
  copyFileSync(cutPath, resolve(outReportDir, 'cutaway-3d-roof-off.png'));

  // Close-up showing flooring, glazing, and the lower porch (-6 in drop, car hidden)
  await captureSolidCamera('closeup_flooring_glazing_porch', 'closeup-flooring-glazing-lower-porch.png', {carVisible: false});

  // Optional parking check render (showing the removable Škoda Kylaq when toggled on)
  await captureSolidCamera('closeup_flooring_glazing_porch', 'optional-parking-check-car-on.png', {carVisible: true});
  await page.evaluate(() => window.__ff.viewer.setCarVisible(false));

  // Verify walking navigation across ground floor, lower porch (-0.1524 m), and upper floor (+3.508 m) + measure frame time
  const walkPerf = await page.evaluate(() => {
    const v = window.__ff.viewer;
    v.setSiteMode('proposed');
    v.setGrade('day');
    v.setCarVisible(false);
    v.setMode('walk');
    // Check lower car porch datum (-0.1524 m; plot coords x=10.5, y=2.5 -> three.js x=10.5, z=-2.5)
    v.walker.position.set(10.5, 0.2, -2.5);
    v.walker.velocity.set(0, 0, 0);
    for (let i = 0; i < 60; i++) v.walker.update(1 / 60, {forward: 0, strafe: 0});
    const porchFloorY = v.walker.position.y;
    // Check ground floor living datum (0.0 m; plot coords x=4.5, y=6.2 -> three.js x=4.5, z=-6.2)
    v.walker.position.set(4.5, 0.3, -6.2);
    v.walker.velocity.set(0, 0, 0);
    for (let i = 0; i < 60; i++) v.walker.update(1 / 60, {forward: 0, strafe: 0});
    const livingFloorY = v.walker.position.y;
    // Check upper floor gallery datum (+3.508 m; plot coords x=6.95, y=6.2 -> three.js x=6.95, z=-6.2)
    v.walker.position.set(6.95, 3.8, -6.2);
    v.walker.velocity.set(0, 0, 0);
    for (let i = 0; i < 60; i++) v.walker.update(1 / 60, {forward: 0, strafe: 0});
    const upperFloorY = v.walker.position.y;

    // Benchmark 30 frames of rendering with full colony context enabled
    const t0 = performance.now();
    for (let i = 0; i < 30; i++) {
      v.dirty = true;
      v.composer.render(1 / 60);
    }
    const elapsedMs = performance.now() - t0;
    return {
      porchFloorY: Number(porchFloorY.toFixed(4)),
      livingFloorY: Number(livingFloorY.toFixed(4)),
      upperFloorY: Number(upperFloorY.toFixed(4)),
      cpuSubmissionMsPerFrame: Number((elapsedMs / 30).toFixed(2)),
    };
  });
  check(
    `${slug} walking level transitions verified (lower porch -0.1524m, ground 0.0m, upper +3.508m) and CPU submission timing`,
    Math.abs(walkPerf.porchFloorY - -0.1524) < 0.03 &&
      Math.abs(walkPerf.livingFloorY - 0.0) < 0.03 &&
      Math.abs(walkPerf.upperFloorY - 3.508) < 0.03,
    walkPerf
  );

  const routes=await page.evaluate(()=>{
    const v=window.__ff.viewer;v.setMode('walk');v.paused=true;
    for(const item of v.openings.items)item.goal=1;
    for(let i=0;i<120;i++)v.openings.update(1/60);
    const tests=[
      ['pantry aisle',[2.65,0,7.65],[2.65,0,7.94]],
      ['forecourt to utility',[2.65,0,.56],[.75,0,.56]],
      ['kitchen to living',[3.7,0,4.4],[3.7,0,5.4]],
      ['living to ICU',[6.35,0,6.3],[6.35,0,5.2]],
      ['veranda to ICU',[8.0,0,6.4],[8.0,0,5.4]],
    ];
    return tests.map(([name,a,b])=>{
      const w=v.walker;w.position.set(a[0],a[1]+.015,-a[2]);w.velocity.set(0,0,0);
      const dx=b[0]-a[0],dy=b[2]-a[2],dist=Math.hypot(dx,dy);
      w.yaw=Math.atan2(-dx,dy);
      for(let i=0;i<Math.ceil((dist/w.s.walkSpeed+.08)*120);i++)w.update(1/120,{forward:1,strafe:0});
      const err=Math.hypot(w.position.x-b[0],w.position.z+b[2]);
      return {name,error:err,floor:w.position.y,grounded:w.onGround,position:[w.position.x,-w.position.z]};
    });
  });
  for(const r of routes)check('Walk through '+r.name,r.error<.25&&Math.abs(r.floor)<.03&&r.grounded,r);

  // Walk continuously up and back down the new stair, without teleporting
  // between landings. This catches roof/slab cuts and guard obstructions.
  const upperRoute=await page.evaluate(()=>{
    const v=window.__ff.viewer,w=v.walker;v.setMode('walk');v.paused=true;
    for(const item of v.openings.items)item.goal=1;
    for(let i=0;i<120;i++)v.openings.update(1/60);
    w.position.set(5.7,3.523,-7.15);w.velocity.set(0,0,0);
    const points=[[4.0,7.15],[.7,7.15],[.7,8.35],[4.8,8.35],[4.8,9.7],
      [4.8,8.35],[.7,8.35],[.7,7.15],[4.0,7.15],[5.7,7.15]];
    const result=[];
    for(const [x,y] of points){
      let error=99,frames=0;
      while(frames++<2200){
        const dx=x-w.position.x,dy=y+w.position.z;error=Math.hypot(dx,dy);
        if(error<.055)break;
        w.yaw=Math.atan2(-dx,dy);w.update(1/120,{forward:1,strafe:0});
      }
      w.velocity.set(0,0,0);
      for(let i=0;i<20;i++)w.update(1/120,{forward:0,strafe:0});
      result.push({target:[x,y],position:[w.position.x,-w.position.z],height:w.position.y,grounded:w.onGround,error,frames});
      if(error>.12)break;
    }
    return result;
  });
  writeFileSync(resolve(outReportDir,'second-stair-route.json'),JSON.stringify(upperRoute,null,2));
  check('Continuous walk first interior → second hall → first interior',upperRoute.length===10&&
    upperRoute.every(r=>r.error<.12&&r.grounded)&&Math.abs(upperRoute[4].height-7.016)<.035&&
    Math.abs(upperRoute[9].height-3.508)<.035,upperRoute);

  check('Zero uncaught page errors during Tirumala 5 studio & render verification', errors.length === 0, errors);
} catch (e) {
  errors.push(e.message);
  throw e;
} finally {
  writeFileSync(resolve(outReportDir, 'browser-checks.json'), JSON.stringify({checks, errors}, null, 2));
  await browser?.close();
  server.kill('SIGTERM');
}
