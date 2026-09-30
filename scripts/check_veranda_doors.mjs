import {writeFileSync} from 'node:fs';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const checks=[],errors=[];const check=(name,pass)=>{checks.push({name,pass:!!pass});console.log(pass?'PASS':'FAIL',name);if(!pass)throw Error(name);};
try {
 const p=await browser.newPage({viewport:{width:1500,height:1000}});p.on('pageerror',e=>errors.push(e.message));
 await p.goto('http://127.0.0.1:8765/samples/my-desired-home/preview.html');await p.waitForFunction(()=>window.__ff?.ready,null,{timeout:180000});
 console.log('Loaded plan',await p.evaluate(()=>__ff.scene.planHash));
 check('All doors and gates begin closed',await p.evaluate(()=>__ff.viewer.openings.items.filter(o=>o.kind!=='window').every(o=>o.value===0&&!o.partial)));
 const shot=async(name,eye,target,fov=70)=>{await p.evaluate(({eye,target,fov})=>{
 const v=__ff.viewer;v.setMode('walk');v.paused=true;v.fitHeld=null;v.zoomAnim=null;
 v.walker.teleport(v.walker.position.clone().set(eye[0],eye[1]>3.15?3.15:0,eye[2]));
 v.camera.fov=fov;v.camera.updateProjectionMatrix();v.camera.position.set(...eye);v.camera.lookAt(...target);
 for(let i=0;i<100;i++)v.adapt(.05);v.updateProbe();for(let i=0;i<100;i++)v.adapt(.05);
 v.hud.show(false);v.updateLights();v.vegetation?.update(v.time,v.camera);v.composer.render(.016);
 },{eye,target,fov});await p.waitForTimeout(250);const bytes=await p.evaluate(async()=>Array.from(new Uint8Array(await (await __ff.viewer.snapshot({width:1600})).arrayBuffer())));writeFileSync(`evidence/desired-home/${name}.png`,Buffer.from(bytes));};
 await shot('veranda-timber-closed',[14.2,1.6,-7.1],[11.35,1.25,-7.1],70);
 await p.evaluate(()=>{__ff.viewer.paused=true;__ff.viewer.setMode('walk');});
 const spawn=async(x,y,z=0)=>p.evaluate(({x,y,z})=>{const w=__ff.viewer.walker;w.teleport(w.position.clone().set(x,z,-y));},{x,y,z});
 const door=async(id,goal)=>p.evaluate(({id,goal})=>{const v=__ff.viewer,d=v.openings.items.find(o=>o.id===id);d.goal=goal;for(let i=0;i<100;i++)v.openings.update(1/60);return d.value===goal;},{id,goal});
 const walk=async(x,y)=>p.evaluate(({x,y})=>{const w=__ff.viewer.walker;let reached=false;for(let i=0;i<600;i++){const dx=x-w.position.x,dz=-y-w.position.z;if(Math.hypot(dx,dz)<.06){reached=true;break;}w.yaw=Math.atan2(-dx,-dz);w.update(1/60,{forward:1,strafe:0});}return {reached,position:w.position.toArray()};},{x,y});
 const leafIds=['timber-left','timber-right','mesh-right'].map(x=>'g-living-veranda/'+x);
 check('Two hinged timber leaves and one sliding mesh panel',await p.evaluate(ids=>ids.every(id=>{const d=__ff.viewer.openings.items.find(o=>o.id===id);return d&&d.parts.length===1&&d.handle&&(id.includes('/mesh-')?d.parts[0].slide&&Math.abs(d.clearWidth-1.166)<.001:Math.abs(d.clearWidth-2.46)<.001);}),leafIds));
 await spawn(10.2,7.1);check('Closed timber and mesh block walking',!(await walk(12.8,7.1)).reached);
 await spawn(14,7.1);
 for(const id of leafIds.slice(0,2))check(id+' opens',await door(id,1));
 check('Mesh stays closed when timber opens',await p.evaluate(ids=>ids.every(id=>__ff.viewer.openings.items.find(o=>o.id===id).value===0),leafIds.slice(2)));
 await shot('veranda-mesh-closed',[14.2,1.6,-7.1],[11.35,1.25,-7.1],70);
 await spawn(10.2,7.1);check('Closed mesh still blocks passage',!(await walk(12.8,7.1)).reached);
 await spawn(14,7.1);for(const id of leafIds.slice(2))check(id+' opens',await door(id,1));
 await shot('veranda-doors-open',[14.2,1.6,-7.1],[11.35,1.25,-7.1],70);
 await shot('living-doors-garden-view',[9.8,1.6,-7.1],[15.6,1.0,-7.5],70);
 await spawn(10.2,7.7);check('Stacked mesh clears the right-hand passage',(await walk(13,7.7)).reached);
 // Open handles move with their leaves and can still be targeted for closing.
 check('Open leaves remain individually targetable',await p.evaluate(ids=>{const v=__ff.viewer;return ids.every(id=>{const d=v.openings.items.find(o=>o.id===id);const h=d.handle.clone().applyMatrix4(d.parts[0].group.matrixWorld);const eye=h.clone();eye.z=-7.1;eye.y=1.63;v.walker.position.set(eye.x,0,eye.z);const found=v.openings.findTarget(eye,h.clone().sub(eye).normalize());return found?.id===id;});},leafIds));
 await spawn(14,7.1);for(const id of leafIds)check(id+' closes',await door(id,0));
 await spawn(10.2,7.1);check('Reclosed layers block passage',!(await walk(12.8,7.1)).reached);
 await spawn(14,7.1);for(const id of leafIds)await door(id,1);
 await spawn(13,7.1);
 const route=[];for(const [x,y] of [[12.2,6.55],[14.5,6.55],[17.5,6.55],[16.1,6.1],[16.1,5.15]])route.push(await walk(x,y));console.log('veranda route',route);check('Veranda route reaches outside parking approach',route.every(r=>r.reached));
 await spawn(14.3,6.9);check('Drawing room door opens',await door('g-drawing-veranda',1));await walk(13.15,6.9);check('Drawing room remains accessible',(await walk(13.15,5.1)).reached);
 await spawn(14.45,7.45);for(const panel of ['b','c'])check('ICU veranda panel '+panel+' opens',await door('g-care-veranda/panel-'+panel,1));check('ICU remains accessible',(await walk(14.45,9.2)).reached);
 await spawn(17.5,9.3,3.15);const upper=[];for(const [x,y] of [[17.5,8.7],[17.5,7.7],[17.5,6.8],[15,6.8]])upper.push(await walk(x,y));console.log('upper route',upper);check('Upper terrace bypass remains walkable',upper.every(r=>r.reached));
 await spawn(17.5,7.9,3.15);check('Guard prevents entering daylight opening',!(await walk(16,7.9)).reached);
 check('No browser errors',errors.length===0);
} finally {writeFileSync('evidence/desired-home/veranda-door-checks.json',JSON.stringify({checks,errors},null,2));await browser.close();}
