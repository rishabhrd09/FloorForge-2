import {writeFileSync} from 'node:fs';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const checks=[],errors=[];const check=(name,pass)=>{checks.push({name,pass:!!pass});console.log(pass?'PASS':'FAIL',name);};
try{
const p=await browser.newPage({viewport:{width:1600,height:1100}});p.on('pageerror',e=>errors.push(e.message));await p.goto('http://127.0.0.1:8765/samples/my-desired-home/preview.html');await p.waitForFunction(()=>window.__ff?.ready,null,{timeout:180000});
check('No porch column',await p.evaluate(()=>!__ff.scene.nodes.some(n=>n.id==='exterior-porch-01-column')));
const spawn=async(x,y)=>p.evaluate(({x,y})=>{const v=__ff.viewer;v.setMode('walk');v.paused=true;v.walker.teleport(v.walker.position.clone().set(x,0,-y));},{x,y});
const door=async(id,goal)=>p.evaluate(({id,goal})=>{const v=__ff.viewer,d=v.openings.items.find(o=>o.id===id);d.goal=goal;for(let i=0;i<120;i++)v.openings.update(1/60);return d.value===goal;},{id,goal});
const walk=async(x,y)=>p.evaluate(({x,y})=>{const w=__ff.viewer.walker;for(let i=0;i<600;i++){const dx=x-w.position.x,dz=-y-w.position.z;if(Math.hypot(dx,dz)<.06)return true;w.yaw=Math.atan2(-dx,-dz);w.update(1/60,{forward:1,strafe:0});}return false;},{x,y});
const shot=async(name,eye,target)=>{await p.evaluate(({eye,target})=>{const v=__ff.viewer;v.setMode('walk');v.paused=true;v.fitHeld=null;v.zoomAnim=null;v.walker.teleport(v.walker.position.clone().set(eye[0],0,eye[2]));v.camera.fov=66;v.camera.updateProjectionMatrix();v.camera.position.set(...eye);v.camera.lookAt(...target);for(let i=0;i<100;i++)v.adapt(.05);v.updateProbe();for(let i=0;i<100;i++)v.adapt(.05);v.hud.show(false);v.updateLights();v.vegetation?.update(v.time,v.camera);v.composer.render(.016);},{eye,target});const bytes=await p.evaluate(async()=>Array.from(new Uint8Array(await(await __ff.viewer.snapshot({width:1600})).arrayBuffer())));writeFileSync(`evidence/desired-home/${name}.png`,Buffer.from(bytes));};
await shot('front-entrance-closed',[19.8,2.4,8.7],[13.5,1.45,.6]);
await spawn(13.37,-3);check('Closed pedestrian gate blocks walking',!await walk(13.37,-1));await spawn(16.4,-3);check('Closed vehicle gate blocks walking',!await walk(16.4,1));
await spawn(10,-4);check('Pedestrian slider opens fully',await door('exterior-pedestrian-gate',1));check('Vehicle leaves open fully',await door('exterior-vehicle-gate',1));
await spawn(13.37,-3);check('Entry path and porch steps are walkable',await walk(13.37,-.35));await spawn(16.4,-3);check('Vehicle approach clear through open gate',await walk(16.4,0));await spawn(15.65,-.1);check('Passage beside parked car stays clear',await walk(15.65,4.7));
await shot('front-entrance-open',[19.8,2.0,6.2],[14.5,1.1,.2]);
await shot('front-court-clear',[13.8,1.7,.6],[6,.6,1.1]);
await spawn(10,-4);check('Pedestrian slider closes fully',await door('exterior-pedestrian-gate',0));check('Vehicle leaves close fully',await door('exterior-vehicle-gate',0));
check('No browser errors',errors.length===0);
}finally{writeFileSync('evidence/desired-home/front-entrance-checks.json',JSON.stringify({checks,errors},null,2));await browser.close();}
if(checks.some(c=>!c.pass)||errors.length)process.exitCode=1;
