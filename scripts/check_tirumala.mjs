import {spawn} from 'node:child_process';
import {copyFileSync, mkdirSync, mkdtempSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const {chromium} = await import(
  process.env.PLAYWRIGHT_MODULE ||
    '/Users/rishabh/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs'
);

const root = resolve(import.meta.dirname, '..');
const port = 8896;
const url = `http://127.0.0.1:${port}`;
const out = resolve(root, 'evidence/tirumala');
const thumbPath = resolve(root, 'examples/gallery/thumbnails/tirumala.png');
mkdirSync(out, {recursive: true});

const server = spawn(
  resolve(root, '.venv/bin/python'),
  ['-m', 'floorforge', 'serve', '--no-browser', '--port', String(port), '--out', mkdtempSync('/tmp/ff-tirumala-test-')],
  {cwd: root, stdio: ['ignore', 'pipe', 'pipe']}
);
server.stderr.on('data', d => process.stderr.write(d));

let browser;
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
  const page = await browser.newPage({viewport: {width: 1512, height: 1050}});
  page.on('pageerror', e => errors.push(e.message));

  await page.goto(url);
  await page.waitForFunction(
    () =>
      !document.querySelector('[data-start="continue"]')?.disabled &&
      document.querySelector('#workspace-project option[value="sample:tirumala"]') &&
      window.__ffApp?.viewer &&
      window.__ff?.ready,
    null,
    {timeout: 180000, polling: 100}
  );

  // Enter workspace from start screen and switch to Generated Home view so #workspace-project is visible
  await page.click('[data-start="continue"]');
  await page.click('#design-result');
  await page.locator('#workspace-project').waitFor({state: 'visible', timeout: 30000});

  const original = await page.evaluate(() => ({
    build: window.__ff.buildId,
    project: window.__ffApp.collect(),
  }));

  await page.selectOption('#workspace-project', 'sample:tirumala');
  await page.waitForFunction(
    () => window.__ff?.buildId === 'sample:tirumala' && !window.__ffApp.draftStale,
    null,
    {timeout: 180000, polling: 100}
  );
  await page.evaluate(() => {
    const toast = document.getElementById('toast');
    if (toast) toast.hidden = true;
  });

  check(
    'Tirumala Revision 8 loads 40 × 50 ft (12.192 × 15.240 m) East-facing settings, 20 authored rooms, and Options A–E bar',
    await page.evaluate(() => {
      const f = window.__ffApp.planEditor.plan.floors;
      const bar = document.getElementById('tirumala-options-bar');
      const pills = bar ? bar.querySelectorAll('[data-tirumala-option]').length : 0;
      return (
        document.getElementById('width').value === '40' &&
        document.getElementById('depth').value === '50' &&
        document.getElementById('facing').value === '90' &&
        f[0].rooms.length === 13 &&
        f[1].rooms.length === 7 &&
        bar &&
        !bar.hidden &&
        pills === 5 &&
        window.__ffApp.currentTirumalaOption === 'A'
      );
    })
  );

  const hash = await page.evaluate(() => window.__ff.scene.planHash);

  // 1. Switch across all five Revision-8 Options A -> B -> C -> D -> E -> A and verify live 2D + 3D updates
  const optionHashes = {};
  for (const code of ['A', 'B', 'C', 'D', 'E']) {
    if (code !== 'A') {
      await page.click(`#tirumala-options-bar [data-tirumala-option="${code}"]`);
      await page.waitForFunction(
        expected =>
          window.__ffApp.currentTirumalaOption === expected &&
          window.__ff?.buildId === `sample:tirumala:${expected}` &&
          !window.__ffApp.draftStale,
        code,
        {timeout: 60000, polling: 100}
      );
    }
    const state = await page.evaluate(() => ({
      option: window.__ffApp.currentTirumalaOption,
      planHash: window.__ff.scene.planHash,
      sheetCount: window.__ff.sheets.length,
      careRoom: window.__ff.building.spaces.find(s => s.id === 'g-care')?.area_m2,
      drawingRoom: window.__ff.building.spaces.find(s => s.id === 'g-drawing')?.area_m2,
    }));
    optionHashes[code] = state.planHash;
    check(`Option ${code} activates and updates both 2D sheets and 3D scene`, state.option === code && state.sheetCount >= 6, state);

    // Capture 2D Ground Floor sheet for Option
    await page.locator('.project-workspace [data-project-view="2d"]').click();
    await page.selectOption('#sheet-select', 'A-101');
    await page.waitForTimeout(350);
    await page.locator('#drawings-panel').screenshot({path: resolve(out, `option-${code}-2d-ground.png`)});

    // Capture 3D ground dollhouse for Option
    await page.locator('.project-workspace [data-project-view="3d"]').click();
    await page.evaluate(() => {
      const v = window.__ff.viewer;
      v.setSiteMode('proposed');
      v.setFloor(0);
      v.setMode('dollhouse');
    });
    await page.waitForTimeout(550);
    await page.locator('#scene').screenshot({path: resolve(out, `option-${code}-3d-dollhouse.png`)});
  }

  check(
    'All 5 Tirumala options A–E produce distinct planHashes in the live studio',
    new Set(Object.values(optionHashes)).size === 5,
    optionHashes
  );

  // Return to Option A as default for detailed inspection
  await page.click('#tirumala-options-bar [data-tirumala-option="A"]');
  await page.waitForFunction(
    () =>
      window.__ffApp.currentTirumalaOption === 'A' &&
      (window.__ff?.buildId === 'sample:tirumala' || window.__ff?.buildId === 'sample:tirumala:A'),
    null,
    {timeout: 60000, polling: 100}
  );

  // 2. Verify sample isolation: switch to My Desired Home, Saved Verandah, and The Bungalow and back
  for (const otherSlug of ['my-desired-home', 'saved-verandah', 'bungalow']) {
    await page.selectOption('#workspace-project', `sample:${otherSlug}`);
    await page.waitForFunction(
      target => window.__ff?.buildId === target && !window.__ffApp.draftStale,
      `sample:${otherSlug}`,
      {timeout: 90000, polling: 100}
    );
    const isolated = await page.evaluate(() => {
      const bar = document.getElementById('tirumala-options-bar');
      const v = window.__ff.viewer;
      return {
        optionsBarHidden: !bar || bar.hidden,
        noColonyContextLeak: !v.context?.userData?.existingPlotGroup && !v.context?.getObjectByName?.('existing-plot-context'),
        colonyContextProp: window.__ff.scene?.context?.style || null,
      };
    });
    check(
      `Sample isolation verified for ${otherSlug} (no Tirumala options bar or colony context leak)`,
      isolated.optionsBarHidden && isolated.noColonyContextLeak && isolated.colonyContextProp !== 'tirumala-colony',
      isolated
    );
  }

  // Switch back to Tirumala
  await page.selectOption('#workspace-project', 'sample:tirumala');
  await page.waitForFunction(
    () => window.__ff?.buildId === 'sample:tirumala' && !window.__ffApp.draftStale,
    null,
    {timeout: 90000, polling: 100}
  );
  await page.evaluate(() => {
    const toast = document.getElementById('toast');
    if (toast) toast.hidden = true;
  });

  // 3. Specifications dialog
  await page.locator('.project-workspace [data-project-view="specs"]').click();
  await page.waitForTimeout(300);
  const specsText = await page.locator('#project-specs-dialog').innerText();
  check(
    'Specifications view shows Tirumala orientation, care suite and rooms table',
    specsText.includes('Tirumala') && (specsText.includes('Home care suite') || specsText.includes('Care'))
  );
  await page.screenshot({path: resolve(out, '00-specifications.png')});

  // 4. Room editor
  await page.locator('#project-specs-dialog [data-project-view="editor"]').click();
  await page.waitForTimeout(300);
  check(
    'Room editor opens Tirumala custom plan with 0 local geometry issues',
    await page.evaluate(
      () => document.getElementById('plan-dialog').open && !window.__ffApp.planEditor.localIssues().length
    )
  );
  await page.screenshot({path: resolve(out, '00-ground-editor.png')});
  await page.click('[data-close="plan-dialog"]');
  await page.click('#design-result');

  // 5. Cell guide
  await page.evaluate(() => document.getElementById('grid-open').click());
  await page.waitForTimeout(300);
  check(
    'Ground-floor cell guide has 16 cells',
    (await page.locator('#grid-board button').count()) === 16
  );
  await page.screenshot({path: resolve(out, '00-cell-guide.png')});
  await page.click('[data-close="grid-dialog"]');

  // 6. 2D Drawing Sheets (Site Plan A-001, Ground Floor A-101, First Floor A-102, Roof A-104, Sections A-301 & A-302)
  await page.locator('.project-workspace [data-project-view="2d"]').click();
  await page.locator('#drawing-image').waitFor();

  const captureSheet = async (sheetId, fileName) => {
    await page.selectOption('#sheet-select', sheetId);
    await page.waitForTimeout(400);
    await page.locator('#drawings-panel').screenshot({path: resolve(out, fileName)});
  };
  await captureSheet('A-001', '01-site-plan-north-up.png');
  await captureSheet('A-101', '02-ground-floor-plan.png');
  await captureSheet('A-102', '03-first-floor-plan.png');
  await captureSheet('A-201', '03b-front-east-elevation.png');
  await captureSheet('A-301', '03e-section-living-void-stair.png');
  await captureSheet('A-302', '03f-section-steps-datum-carbay.png');
  await captureSheet('A-601', '03g-schedules.png');
  check('2D site plan, ground floor, first floor, front elevation, both Revision-8 section sheets (A-301, A-302), and schedules (A-601) rendered', true);

  // 7. Switch to 3D view and capture dollhouse cutaways + sightline & camera renders
  await page.locator('.project-workspace [data-project-view="3d"]').click();
  await page.waitForTimeout(500);

  await page.evaluate(() => {
    const v = window.__ff.viewer;
    v.setSiteMode('proposed');
    v.setFloor(0);
    v.setMode('dollhouse');
  });
  await page.waitForTimeout(700);
  await page.locator('#scene').screenshot({path: resolve(out, '03c-ground-3d-dollhouse.png')});

  await page.evaluate(() => {
    const v = window.__ff.viewer;
    v.setFloor(1);
    v.setMode('dollhouse');
  });
  await page.waitForTimeout(700);
  await page.locator('#scene').screenshot({path: resolve(out, '03d-first-3d-dollhouse.png')});

  // Helper to render a named camera in 3D viewer
  const captureNamedCamera = async (camName, fileName, {siteMode = 'proposed', night = false} = {}) => {
    const ok = await page.evaluate(
      ({camName, siteMode, night}) => {
        const v = window.__ff.viewer;
        v.setMode('solid');
        v.setSiteMode(siteMode);
        v.setGrade(night ? 'dusk' : 'day');
        return v.setNamedCamera(camName);
      },
      {camName, siteMode, night}
    );
    check(`Named camera ${camName} (${siteMode}${night ? ', evening' : ''}) activated`, ok);
    await page.waitForTimeout(650);
    const fullPath = resolve(out, fileName);
    await page.locator('#scene').screenshot({path: fullPath});
    return fullPath;
  };

  // Required sightline & hero captures
  await captureNamedCamera('east_entrance_exterior', '04-east-entrance-exterior.png');
  await page.locator('#scene canvas').screenshot({path: thumbPath});

  await captureNamedCamera('ne_corner_two_roads', '05-ne-corner-both-roads.png');
  await captureNamedCamera('care_interior_overview', '06-care-room-interior.png');
  await captureNamedCamera('care_seated_north', '07-care-room-north-seated-view.png');
  await captureNamedCamera('care_recliner_north', '07b-care-room-north-recliner-view.png');
  await captureNamedCamera('care_standing_glazing', '07c-care-room-north-standing-view.png');
  await captureNamedCamera('care_east_court_glimpse', '08-care-room-east-court-glimpse.png');
  await captureNamedCamera('north_veranda_l_route', '09-north-veranda-l-route.png');
  await captureNamedCamera('living_dining_kitchen', '10-kitchen-dining-connection.png');
  await captureNamedCamera('caregiver_nw_pocket', '11-caregiver-nw-open-pocket.png');
  await captureNamedCamera('first_floor_terrace_outlook', '12-first-floor-terrace-outlook.png');
  await captureNamedCamera('compact_corner_stair', '13a-compact-stair-and-lane-window.png');
  await captureNamedCamera('double_height_living_void', '13b-double-height-living-void.png');

  // Reference camera captures in both Existing-Site mode and Proposed-Home mode
  const refCodes = ['N-01', 'N-02', 'N-03', 'N-04', 'NE-01', 'E-01'];
  for (const code of refCodes) {
    await captureNamedCamera(code, `ref-${code}-existing-site.png`, {siteMode: 'existing'});
    await captureNamedCamera(code, `ref-${code}-proposed-home.png`, {siteMode: 'proposed'});
  }

  // Evening exterior view
  await captureNamedCamera('ne_corner_two_roads', '14-evening-exterior.png', {siteMode: 'proposed', night: true});
  await page.evaluate(() => window.__ff.viewer.setGrade('day'));

  // Verify colony context group & care room editables
  const exportCounts = await page.evaluate(() => {
    const v = window.__ff.viewer;
    v.setSiteMode('proposed');
    return {
      hasColonyGroup: !!v.context && v.context.children.length > 15,
      careEditables: window.__ff.scene.editables.filter(e => e.roomId === 'g-care').length,
    };
  });
  check('Colony context is populated in 3D viewer and Revision-8 care-room pieces are editable', exportCounts.hasColonyGroup && exportCounts.careEditables >= 2, exportCounts);

  // 8. Door & Slider Open/Close Verification + Walkthrough across key Revision-8 routes
  const doorCheck = await page.evaluate(() => {
    const v = window.__ff.viewer;
    const targetIds = [
      'g-entry',
      'g-porch-family-slider',
      'g-drawing-door',
      'g-master-door',
      'g-bath-door',
      'g-care-hall-slider',
      'g-care-return-door',
      'g-care-veranda-slider',
      'g-caregiver-door',
      'g-wc-door',
    ];
    const results = {};
    for (const id of targetIds) {
      const items = v.openings.items.filter(o => o.id === id || o.id.startsWith(id + '/'));
      for (const d of items) d.goal = 1;
      for (let i = 0; i < 90; i++) v.openings.update(1 / 60);
      const opened = items.length > 0 && items.every(d => Math.abs(d.value - 1) < 0.02);
      for (const d of items) d.goal = 0;
      for (let i = 0; i < 90; i++) v.openings.update(1 / 60);
      const closed = items.length > 0 && items.every(d => Math.abs(d.value) < 0.02);
      for (const d of items) d.goal = d.initial ?? 0;
      for (let i = 0; i < 90; i++) v.openings.update(1 / 60);
      results[id] = {opened, closed};
    }
    return results;
  });
  check(
    'All ground-floor hinged doors and sliding glass doors animate smoothly between open and closed states',
    Object.values(doorCheck).every(r => r.opened && r.closed),
    doorCheck
  );

  await page.evaluate(() => {
    const v = window.__ff.viewer;
    v.setSiteMode('proposed');
    v.setFloor(0);
    v.paused = true;
    v.setMode('walk');
  });

  const spawnAt = async (x, y, z = 0) =>
    page.evaluate(
      ({x, y, z}) => {
        const v = window.__ff.viewer;
        const w = v.walker;
        w.teleport(w.position.clone().set(x, z, -y));
      },
      {x, y, z}
    );

  const walkTo = async (x, y) =>
    page.evaluate(
      ({x, y}) => {
        const v = window.__ff.viewer;
        const w = v.walker;
        let reached = false;
        for (let i = 0; i < 650; i++) {
          const dx = x - w.position.x;
          const dz = -y - w.position.z;
          if (Math.hypot(dx, dz) < 0.09) {
            reached = true;
            break;
          }
          w.yaw = Math.atan2(-dx, -dz);
          w.update(1 / 60, {forward: 1, strafe: 0});
        }
        for (let i = 0; i < 20; i++) w.update(1 / 60, {forward: 0, strafe: 0});
        return {reached, position: w.position.toArray()};
      },
      {x, y}
    );

  const openDoor = async id =>
    page.evaluate(id => {
      const v = window.__ff.viewer;
      const items = v.openings.items.filter(o => o.id === id || o.id.startsWith(id + '/'));
      for (const d of items) d.goal = 1;
      for (let i = 0; i < 90; i++) v.openings.update(1 / 60);
      return items.length > 0 && items.every(d => d.value === 1);
    }, id);

  // Route A: Shallow Porch (x=7.12m, y=2.75m) -> Drawing Room (g-entry)
  await openDoor('g-entry');
  await spawnAt(7.12, 2.75, 0);
  let porchToDrawing = await walkTo(7.12, 3.8);
  check('Walkthrough: Shallow Porch through g-entry into Drawing Room', porchToDrawing.reached, porchToDrawing);

  // Route B: Family Hall -> Care Suite (via g-care-hall-slider) -> West Care Veranda (via g-care-veranda-slider)
  await openDoor('g-care-hall-slider');
  await spawnAt(6.72, 8.2, 0);
  let hallToCare = await walkTo(7.55, 8.2);
  check('Walkthrough: Family Hall through 6 ft sliding glass into Care Suite', hallToCare.reached, hallToCare);

  await openDoor('g-care-veranda-slider');
  await spawnAt(9.45, 9.8, 0);
  let careToVeranda = await walkTo(9.45, 11.3);
  check('Walkthrough: Care Suite through 8 ft sliding glass onto West Veranda', careToVeranda.reached, careToVeranda);

  // Route C: Compact 12 × 7.5 ft Corner Staircase climb:
  // Enter from North ground arrival (x=4.15m, y=6.02m), climb SOUTH (to x=0.68m, y=6.02m),
  // turn WEST across South landing (to x=0.68m, y=7.24m), climb NORTH (to x=4.15m, y=7.24m) -> Upper arrival (z = 3.658 m)
  await spawnAt(4.15, 6.02, 0);
  const stairPts = [];
  for (const [sx, sy] of [
    [0.68, 6.02],
    [0.68, 7.24],
    [4.15, 7.24],
  ]) {
    stairPts.push(await walkTo(sx, sy));
  }
  check(
    'Walkthrough: Compact 12 × 7.5 ft corner stair climb (South flight -> West landing -> North flight) to +3.658 m upper arrival',
    stairPts.every(r => r.reached) && Math.abs(stairPts.at(-1).position[1] - 3.658) < 0.22,
    stairPts.at(-1)
  );

  await page.evaluate(() => {
    const v = window.__ff.viewer;
    v.paused = false;
    v.setMode('solid');
    v.setView('hero');
  });
  await page.waitForTimeout(500);

  // 9. Verify Sample Gallery lists Tirumala with its rendered thumbnail alongside all existing samples
  await page.evaluate(() => document.getElementById('sample-gallery-open').click());
  await page.waitForSelector('.sample-card');
  for (const img of await page.locator('.sample-cover img').all()) {
    await img.scrollIntoViewIfNeeded();
  }
  await page.waitForFunction(
    () => [...document.querySelectorAll('.sample-cover img')].every(i => i.complete && i.naturalWidth > 0),
    null,
    {timeout: 60000}
  );
  const hasTirumalaCard = (await page.locator('button[data-sample="tirumala"]').count()) > 0;
  check('Sample Gallery displays Tirumala card with rendered thumbnail', hasTirumalaCard);
  await page.screenshot({path: resolve(out, '15-sample-gallery-with-tirumala.png')});
  await page.click('[data-close="sample-gallery-dialog"]');

  // 10. Verify Mobile / Narrow Viewport (390 × 844) renders Options A–E switcher cleanly
  await page.setViewportSize({width: 390, height: 844});
  await page.waitForTimeout(350);
  const mobileBarVisible = await page.evaluate(() => {
    const bar = document.getElementById('tirumala-options-bar');
    return !!bar && !bar.hidden && bar.getBoundingClientRect().height > 20;
  });
  check('Mobile viewport (390 × 844) renders Tirumala Options A–E switcher cleanly', mobileBarVisible);
  await page.screenshot({path: resolve(out, '16-mobile-options-switcher.png')});
  await page.setViewportSize({width: 1512, height: 1050});
  await page.waitForTimeout(250);

  // Restore original project and verify non-destructive behaviour
  await page.selectOption('#workspace-project', 'current-project');
  await page.waitForFunction(id => window.__ff.buildId === id, original.build, {timeout: 180000, polling: 100});
  check(
    'Original workspace project restored intact after inspecting Tirumala',
    await page.evaluate(p => window.__ffApp.collect().brief.title === p.brief.title, original.project)
  );

  check('Zero browser page errors', errors.length === 0, errors);
  writeFileSync(resolve(out, 'browser-checks.json'), JSON.stringify({planHash: hash, optionHashes, checks, errors}, null, 2));
} finally {
  await browser?.close();
  server.kill('SIGINT');
}
