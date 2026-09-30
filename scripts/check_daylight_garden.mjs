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
 await shot('garden-living-day',[10.2,1.6,-7.05],[16.4,.95,-7.65],70);
 await shot('garden-sofa-view',[10.0,1.18,-4.425],[16.1,.85,-7.75],75);
 await shot('garden-dining-view',[7.2,1.25,-5.3],[16.1,.85,-7.75],70);
 await shot('garden-veranda-day',[12.1,1.65,-6.35],[16.65,1.3,-7.8],75);
 await shot('garden-terrace-opening',[17.55,4.9,-9.45],[16.05,2.6,-7.8],76);
 await p.evaluate(()=>__ff.viewer.setGrade('dusk'));
 await shot('garden-living-evening',[10.2,1.6,-7.05],[16.4,.95,-7.65],70);
 await p.evaluate(()=>{__ff.viewer.setGrade('day');__ff.viewer.paused=true;__ff.viewer.setMode('walk');});
 const spawn=async(x,y,z=0)=>p.evaluate(({x,y,z})=>{const w=__ff.viewer.walker;w.teleport(w.position.clone().set(x,z,-y));},{x,y,z});
 const door=async(id,goal)=>p.evaluate(({id,goal})=>{const v=__ff.viewer,d=v.openings.items.find(o=>o.id===id);d.goal=goal;for(let i=0;i<100;i++)v.openings.update(1/60);return d.value===goal;},{id,goal});
 const walk=async(x,y)=>p.evaluate(({x,y})=>{const w=__ff.viewer.walker;let reached=false;for(let i=0;i<600;i++){const dx=x-w.position.x,dz=-y-w.position.z;if(Math.hypot(dx,dz)<.06){reached=true;break;}w.yaw=Math.atan2(-dx,-dz);w.update(1/60,{forward:1,strafe:0});}return {reached,position:w.position.toArray()};},{x,y});
 const leaves=['timber-left','timber-right','mesh-right'].map(x=>'g-living-veranda/'+x);
 check('Living doorway has hinged timber and sliding mesh leaves',await p.evaluate(ids=>ids.every(id=>__ff.viewer.openings.items.some(o=>o.id===id)),leaves));
 await spawn(10.2,7.1);check('Closed living doors block walking',!(await walk(12.8,7.1)).reached);
 await spawn(14,7.1);for(const id of leaves)check(id+' opens',await door(id,1));
 await spawn(10.2,7.7);check('Open living doors allow walking',(await walk(12.8,7.7)).reached);
 const route=[];for(const [x,y] of [[12.2,6.55],[14.5,6.55],[17.5,6.55],[16.1,6.1],[16.1,5.15]])route.push(await walk(x,y));console.log('veranda route',route);check('Veranda route reaches outside parking approach',route.every(r=>r.reached));
 await spawn(14.3,6.9);check('Drawing room door opens',await door('g-drawing-veranda',1));await walk(13.15,6.9);check('Drawing room remains accessible',(await walk(13.15,5.1)).reached);
 await spawn(14.45,7.45);for(const panel of ['b','c'])check('ICU veranda panel '+panel+' opens',await door('g-care-veranda/panel-'+panel,1));check('ICU remains accessible',(await walk(14.45,9.2)).reached);
 await spawn(17.5,9.3,3.15);const upper=[];for(const [x,y] of [[17.5,8.7],[17.5,7.7],[17.5,6.8],[15,6.8]])upper.push(await walk(x,y));console.log('upper route',upper);check('Upper terrace bypass remains walkable',upper.every(r=>r.reached));
 await spawn(17.5,7.9,3.15);check('Guard prevents entering daylight opening',!(await walk(16,7.9)).reached);
 check('No browser errors',errors.length===0);
} finally {writeFileSync('evidence/desired-home/daylight-garden-checks.json',JSON.stringify({checks,errors},null,2));await browser.close();}
