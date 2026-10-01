import {writeFileSync} from 'node:fs';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const checks=[],errors=[];const check=(name,pass)=>{checks.push({name,pass:!!pass});console.log(pass?'PASS':'FAIL',name);};
try {
 const p=await browser.newPage({viewport:{width:1500,height:1000}});p.on('pageerror',e=>errors.push(e.message));
 await p.goto('http://127.0.0.1:8765/samples/my-desired-home/preview.html');await p.waitForFunction(()=>window.__ff?.ready,null,{timeout:180000});
 console.log('Loaded',await p.evaluate(()=>__ff.scene.planHash));
 const shot=async(name,eye,target,fov=70)=>{await p.evaluate(({eye,target,fov})=>{
 const v=__ff.viewer;v.setMode('walk');v.paused=true;v.fitHeld=null;v.zoomAnim=null;
 v.walker.teleport(v.walker.position.clone().set(eye[0],eye[1]>3.15?3.15:0,eye[2]));
 v.camera.fov=fov;v.camera.updateProjectionMatrix();v.camera.position.set(...eye);v.camera.lookAt(...target);
 for(let i=0;i<100;i++)v.adapt(.05);v.updateProbe();for(let i=0;i<100;i++)v.adapt(.05);
 v.hud.show(false);v.updateLights();v.vegetation?.update(v.time,v.camera);v.composer.render(.016);
 },{eye,target,fov});await p.waitForTimeout(250);const bytes=await p.evaluate(async()=>Array.from(new Uint8Array(await (await __ff.viewer.snapshot({width:1600})).arrayBuffer())));writeFileSync(`evidence/desired-home/${name}.png`,Buffer.from(bytes));};
 await shot('corrected-veranda-aerial',[25,12,-.5],[13,3.6,-7.0],60);
 await shot('corrected-veranda-front',[22,6.8,16],[12.5,3.6,-5.5],55);
 await shot('corrected-veranda-sky',[16.2,1.65,-6.7],[16.8,5.3,-8.8],83);
 await shot('corrected-veranda-shelter',[12.8,1.65,-6.3],[14,3.8,-8.5],78);
 await shot('corrected-veranda-bedroom-wall',[16.8,4.9,-6.4],[12.8,4.6,-8.475],75);
 await shot('corrected-veranda-canopy',[17.25,4.78,-12.8],[17.2,5.35,-8.45],75);
 const spawn=async(x,y)=>p.evaluate(({x,y})=>{const v=__ff.viewer;v.paused=true;v.setMode('walk');v.walker.teleport(v.walker.position.clone().set(x,3.15,-y));},{x,y});
 const door=async(id,goal)=>p.evaluate(({id,goal})=>{const v=__ff.viewer,d=v.openings.items.find(o=>o.id===id);if(!d)return false;d.goal=goal;for(let i=0;i<100;i++)v.openings.update(1/60);return d.value===goal;},{id,goal});
 const walk=async(x,y)=>p.evaluate(({x,y})=>{const w=__ff.viewer.walker;let reached=false;for(let i=0;i<600;i++){const dx=x-w.position.x,dz=-y-w.position.z;if(Math.hypot(dx,dz)<.06){reached=true;break;}w.yaw=Math.atan2(-dx,-dz);w.update(1/60,{forward:1,strafe:0});}return {reached,position:w.position.toArray()};},{x,y});
 const route=async(name,points)=>{const results=[];for(const [x,y] of points)results.push(await walk(x,y));check(name,results.every(r=>r.reached));if(results.some(r=>!r.reached))console.log(name,results);};
 await p.evaluate(()=>{const v=__ff.viewer;v.paused=true;v.setMode('walk');v.walker.teleport(v.walker.position.clone().set(4.05,0,-4.15));});
 await route('Ground stair ascends south, turns twice, reaches upper lobby',[[.75,4.15],[.75,5.45],[4.0,5.45],[5.2,5.45]]);
 check('Stair arrives at first-floor level',await p.evaluate(()=>Math.abs(__ff.viewer.walker.position.y-3.15)<.03));
 await spawn(5.2,6.5);await route('Gallery to arrival lobby',[[5.2,4.8],[9.5,4.8],[9.5,3.7]]);
 await spawn(9.4,3.3);check('Studio door opens',await door('u-office-lobby',1));await route('Lobby to studio',[[8.8,3.2],[7.5,3.2]]);
 await spawn(9.5,3.4);check('Lobby terrace door opens',await door('u-lobby-terrace',1));await route('Lobby to front terrace',[[10.0,3.4],[11.6,3.4]]);
 await route('Front and right terraces form a continuous L',[[11.6,1],[5,1],[11.8,1],[12.5,3.5],[13.5,5.0]]);
 await route('Covered veranda terrace connects to the shared L',[[13.5,6.3],[14.7,7.5]]);
 check('Shared terrace guard stops entry into outer sky gap',!(await walk(16.5,7.5)).reached);
 check('Master bedroom wall blocks entry from terrace',!(await walk(14.7,9.2)).reached);
 await spawn(8.2,8.8);check('Master door opens',await door('u-bed-north-door',1));await route('Gallery to master bedroom',[[8.55,9.1],[9.8,9.1]]);
 await spawn(16.8,10.8);check('Master terrace door opens',await door('u-bed-north-terrace',1));await route('Master has direct terrace access',[[16.2,10.8],[14.8,10.8]]);
 await spawn(5.05,8.1);check('Small bedroom door opens',await door('u-bed-south-door',1));await route('Gallery to smaller bedroom',[[5.05,9.2],[4.4,10.3],[3,10.8]]);


 await spawn(4.4,10.3);await route('Bedroom back to gallery',[[5.05,9.2],[5.05,8.0]]);
 await spawn(4.1,10.8);check('Private balcony door opens',await door('u-bedroom-balcony-door',1));await route('Bedroom to its private balcony',[[3.0,10.8],[3.0,12.5]]);
 await spawn(8.2,9.1);check('Shared bathroom door opens',await door('u-bath-door',1));await route('Gallery to bathroom',[[8.3,10.1]]);
 await spawn(16.8,9.0);check('Private master balcony guard stops entry into sky gap',!(await walk(16.8,7.5)).reached);
 await p.evaluate(()=>{const v=__ff.viewer;v.walker.teleport(v.walker.position.clone().set(16.5,0,-6.5));});
 await route('Veranda paved route remains clear',[[14.8,6.5],[12.3,6.5],[14.8,6.5],[17.5,6.5]]);
 await spawn(6.0,6.3);check('Atrium guard blocks falling into living hall',!(await walk(7.2,6.3)).reached);
 await spawn(3,12.5);check('Private balcony guard blocks outer edge',!(await walk(3,14.8)).reached);
 check('No browser errors',errors.length===0);
 await p.close();
 const planPage=await browser.newPage({viewport:{width:1500,height:1060}});
 await planPage.setContent('<body style="margin:0;background:white"><img style="width:1500px;height:1060px;object-fit:contain" src="http://127.0.0.1:8765/samples/my-desired-home/sheets/A-102.svg"></body>');
 await planPage.waitForFunction(()=>document.querySelector('img').complete);
 await planPage.screenshot({path:'evidence/desired-home/corrected-veranda-plan.png',fullPage:false,timeout:60000});
} finally {writeFileSync('evidence/desired-home/corrected-veranda-checks.json',JSON.stringify({checks,errors},null,2));await browser.close();}
if(checks.some(c=>!c.pass))process.exitCode=1;
