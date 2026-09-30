// Real built viewer, rendered collisions and keyboard interaction. Only the initial ground spawn is positioned by the harness.
import {spawn, execFileSync} from 'node:child_process';
import {mkdirSync, mkdtempSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'evidence/roof-access'),port=8880,url=`http://127.0.0.1:${port}`;
mkdirSync(out,{recursive:true});
const fixtures=JSON.parse(execFileSync(resolve(root,'.venv/bin/python'),['-c',`import json
from pathlib import Path
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.review import reports,validate
from floorforge.scene import make_scene
from floorforge.exterior import apply_exterior_preferences
cases=[]
for name in ('automatic-g1','custom-rear-g2'):
 p=json.loads(Path('examples/demo/project.floorforge.json' if name=='automatic-g1' else 'examples/custom/g2-terrace.floorforge.json').read_text())
 if name=='automatic-g1':
  cases.append(dict(name=name,project=p,building=json.loads(Path('examples/demo/building.json').read_text()),scene=json.loads(Path('examples/demo/scene.json').read_text())))
  continue
 p['brief']['roof_access']=True
 if name=='custom-rear-g2':
  for fl in p['customPlan']['floors']:
   for room in fl['rooms']:room['polygon']=[[x+400,y+5000] for x,y in room['polygon']]
 b=apply_exterior_preferences(generate_layout(fuse(p)))
 cases.append(dict(name=name,project=p,building=b,scene=make_scene(b,reports(b,validate(b)))))
print(json.dumps(cases))`],{cwd:root,maxBuffer:100*1024*1024}));
const server=spawn(resolve(root,'.venv/bin/python'),['-m','floorforge','serve','--no-browser','--port',String(port),'--out',mkdtempSync('/tmp/ff-roof-access-')],{cwd:root,stdio:['ignore','pipe','pipe']});
server.stderr.on('data',d=>process.stderr.write(d));
const checks=[],errors=[];let browser;
function check(name,pass,data){checks.push({name,pass:!!pass,data});console.log(pass?'PASS':'FAIL',name);if(!pass)throw Error(name);}
try{
 for(let i=0;i<80;i++){try{if((await fetch(url+'/api/session')).ok)break;}catch{}await new Promise(r=>setTimeout(r,250));}
 browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 const page=await browser.newPage({viewport:{width:1440,height:960}});page.on('pageerror',e=>errors.push(e.message));
 await page.goto(url,{timeout:180000});await page.waitForFunction(()=>window.__ffApp?.viewer&&window.__ff?.ready,null,{timeout:240000});
 await page.evaluate(()=>{window.__ffApp.viewer.paused=true;window.__ffApp.viewer.setQuality('performance');});
 check('Actual bundled startup model includes First → roof stair and remains G+1',await page.evaluate(()=>{const {building:b,scene:s}=window.__ff;return b.storeys===2&&s.roof_level===2&&b.stairs.some(st=>st.floor===1&&st.to_floor===2&&st.roof_access);}));
 for(const fixture of fixtures){
  const st=fixture.building.stairs[0],x=st.x/1000,y=st.y/1000,H=fixture.scene.floor_height,floors=fixture.building.storeys;
  const front=y+st.landing_mm/2000,back=y+(st.depth-st.landing_mm/2)/1000,left=x+st.flight_width/2000,right=x+(st.width-st.flight_width/2)/1000;
  await page.evaluate(({name,scene,building,left,front})=>{
   const v=window.__ffApp.viewer;v.setMode('solid');if(name!=='automatic-g1')v.setScene(scene,building);v.paused=true;v.setMode('walk');v.canvas.focus();
   const w=v.walker;w.teleport(w.position.clone().set(left,0,-front),0);
   const door=v.openings.items.find(i=>i.id.endsWith('-roof-door'));door.goal=0;for(let i=0;i<90;i++)v.openings.update(1/60);
  },{...fixture,left,front});
  const walk=async(tx,ty,frames=600)=>page.evaluate(({tx,ty,frames})=>{
   const v=window.__ffApp.viewer,w=v.walker;let reached=false;
   for(let i=0;i<frames;i++){let dx=tx-w.position.x,dz=-ty-w.position.z;if(Math.hypot(dx,dz)<.06){reached=true;break;}w.yaw=Math.atan2(-dx,-dz);w.update(1/60,{forward:1,strafe:0});}
   for(let i=0;i<20;i++)w.update(1/60,{forward:0,strafe:0});
   v.floor=v.levelOf(w.position.y);v.hudUpdate();v.openings.updateTarget();v.camera.position.copy(w.eyePosition(v.camera.position.clone()));v.camera.rotation.set(0,w.yaw,0);
   return {reached,position:w.position.toArray(),floor:v.floor};
  },{tx,ty,frames});
  for(let f=0;f<floors;f++){
   let a=await walk(left,back),b=await walk(right,back),c=await walk(right,front),d=await walk(left,front);
   check(`${fixture.name}: climb floor ${f} → ${f+1} through both flights`,[a,b,c,d].every(r=>r.reached)&&Math.abs(d.position[1]-(f+1)*H)<.1,d);
  }
  check(`${fixture.name}: roof is a distinct walking level, not another occupied floor`,await page.evaluate(n=>{const v=window.__ffApp.viewer;return v.floor===n&&v.data.storeys===n&&v.levelOf(v.walker.position.y)===v.data.roof_level;},floors));
  const exitX=x+3.1;const blocked=await walk(exitX,front,150);
  check(`${fixture.name}: closed rooftop door physically blocks passage`,!blocked.reached&&Math.abs(blocked.position[1]-floors*H)<.1,blocked);
  check(`${fixture.name}: rooftop door is targetable from inside`,await page.evaluate(()=>window.__ffApp.viewer.openings.target?.id.endsWith('-roof-door')));
  await page.focus('#scene');await page.keyboard.press('f');
  await page.evaluate(()=>{const v=window.__ffApp.viewer;for(let i=0;i<90;i++)v.openings.update(1/60);});
  check(`${fixture.name}: F opens the actual rooftop door`,await page.evaluate(()=>window.__ffApp.viewer.openings.items.find(i=>i.id.endsWith('-roof-door')).value===1));
  const exit=await walk(exitX,front);check(`${fixture.name}: walk out onto the roof without teleporting`,exit.reached&&Math.abs(exit.position[1]-floors*H)<.1,exit);
  const roam=await walk(exitX,y+2.1);check(`${fixture.name}: roof surface supports walking`,roam.reached&&Math.abs(roam.position[1]-floors*H)<.1,roam);
  const operateRoofDoor=async()=>{
   await page.evaluate(()=>{const v=window.__ffApp.viewer,w=v.walker,d=v.openings.items.find(i=>i.id.endsWith('-roof-door'));w.yaw=Math.atan2(w.position.x-d.center.x,w.position.z-d.center.z);v.openings.updateTarget();});
   await page.focus('#scene');await page.keyboard.press('f');
   return await page.evaluate(()=>{const v=window.__ffApp.viewer;for(let i=0;i<90;i++)v.openings.update(1/60);const d=v.openings.items.find(i=>i.id.endsWith('-roof-door'));return {target:v.openings.target?.id,value:d.value,goal:d.goal,message:v.openings.message};});
  };
  // The open leaf occupies part of the terrace approach. Close it to pass behind its swing,
  // then reopen from the front of the doorway, just as the visitor would do with F.
  const returnApproach=await walk(exitX,front,150);
  if(!returnApproach.reached){const state=await operateRoofDoor();check(`${fixture.name}: close door from terrace to clear its swing`,state.value===0,state);}
  check(`${fixture.name}: return along terrace to doorway`,(await walk(exitX,front)).reached);
  await page.evaluate(()=>{const v=window.__ffApp.viewer,w=v.walker;w.yaw=Math.PI/2;v.camera.rotation.set(0,w.yaw,0);v.hud.setLocked(true);v.hudUpdate();v.openings.updateTarget();v.composer.render(0);});
  check(`${fixture.name}: rooftop door also works from terrace side`,await page.evaluate(()=>window.__ffApp.viewer.openings.target?.id.endsWith('-roof-door')));
  await page.screenshot({path:out+'/'+fixture.name+'-terrace.png'});
  check(`${fixture.name}: floor selector cannot teleport during walking`,await page.evaluate(()=>{const v=window.__ffApp.viewer,before=v.walker.position.toArray();v.setFloor(0);return before.every((n,i)=>n===v.walker.position.toArray()[i])&&v.floor===v.data.roof_level;}));
  if(await page.evaluate(()=>window.__ffApp.viewer.openings.items.find(i=>i.id.endsWith('-roof-door')).value<.5)){
   // Stand to the front of the swing arc before opening toward ourselves.
   check(`${fixture.name}: step clear of the door swing`,(await walk(exitX,y+.18)).reached);
   const state=await operateRoofDoor();check(`${fixture.name}: reopen door from terrace`,state.value===1,state);
   await walk(exitX,front);
  }
  check(`${fixture.name}: re-enter roof landing through open door`,(await walk(right,front)).reached);
  for(let f=floors;f>0;f--){
   let a=await walk(right,back),b=await walk(left,back),c=await walk(left,front);
   check(`${fixture.name}: descend floor ${f} → ${f-1}`,a.reached&&b.reached&&c.reached&&Math.abs(c.position[1]-(f-1)*H)<.1,{a,b,c});
   if(f>1)await walk(right,front);
  }
  await page.evaluate(()=>{const v=window.__ffApp.viewer;v.setMode('dollhouse');v.setFloor(v.data.roof_level);v.composer.render(0);});
  check(`${fixture.name}: roof slab remains visible in roof cutaway`,await page.evaluate(()=>{const v=window.__ffApp.viewer;return v.meshes.some(m=>m.userData.bucket?.roles?.includes('roof')&&m.visible);}));
  check(`${fixture.name}: entering Walk from roof cutaway starts at ground arrival`,await page.evaluate(()=>{const v=window.__ffApp.viewer;v.setMode('walk');return v.floor===0&&v.walker.position.y<v.H;}));
 }
 const custom=fixtures[1];await page.evaluate(p=>window.__ffApp.applyProject(p),custom.project);await page.click('#custom-open');
 check('Roof access option restores from saved project',await page.isChecked('#plan-roof-access'));
 await page.evaluate(()=>{const e=window.__ffApp.planEditor;e.floor=0;e.selected=new Set([e.active.rooms.find(r=>r.kind==='stair').id]);e.render();});
 await page.click('#plan-detail');await page.fill('#plan-x','.650');await page.click('#plan-apply');
 check('Moving one linked stair updates all three floor cores',await page.evaluate(()=>window.__ffApp.planEditor.plan.floors.every(fl=>Math.min(...fl.rooms.find(r=>r.kind==='stair').polygon.map(p=>p[0]))===650)));
 await page.click('#plan-undo');check('One undo restores all linked stair positions',await page.evaluate(()=>window.__ffApp.planEditor.plan.floors.every(fl=>Math.min(...fl.rooms.find(r=>r.kind==='stair').polygon.map(p=>p[0]))===550)));
 await page.click('#plan-redo');check('One redo reapplies all linked stair positions',await page.evaluate(()=>window.__ffApp.planEditor.plan.floors.every(fl=>Math.min(...fl.rooms.find(r=>r.kind==='stair').polygon.map(p=>p[0]))===650)));
 await page.click('#plan-undo');await page.click('#plan-validate');await page.waitForFunction(()=>document.getElementById('plan-validation').textContent.startsWith('Geometry passes'),null,{timeout:60000});
 await page.screenshot({path:out+'/linked-core-editor.png'});await page.click('#plan-generate');
 await page.waitForFunction(()=>!document.getElementById('generate').disabled&&!window.__ffApp.draftStale,null,{timeout:240000});
  check('Generate wires relocated core and roof into matching active 3D',await page.evaluate(()=>{const {building:b,scene:s}=window.__ff;return b.rooftop&&b.stairs.every(st=>st.y===5150)&&b.planHash===s.planHash&&document.querySelector('#floor option[value="3"]')?.textContent.includes('Roof');}));
 check('Replacing a walking scene clears its old walking overlay',await page.evaluate(()=>window.__ffApp.viewer.mode==='solid'&&!window.__ffApp.viewer.hud.visible));
 await page.evaluate(()=>{document.getElementById('input-coverage').open=false;document.getElementById('home-panel').scrollIntoView({block:'start'});});
 await page.evaluate(()=>{const v=window.__ffApp.viewer;v.paused=true;v.setMode('solid');v.setView('aerial');v.composer.render(0);});
 await page.screenshot({path:out+'/generated-roof-aerial.png'});
 check('No browser runtime errors',errors.length===0,errors);
}finally{
 writeFileSync(out+'/browser-acceptance.json',JSON.stringify({checks,errors},null,2)+'\n');
 if(browser)await browser.close();server.kill();
}
