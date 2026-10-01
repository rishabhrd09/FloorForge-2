import {writeFileSync} from 'node:fs';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const checks=[],errors=[];const check=(name,pass)=>{checks.push({name,pass:!!pass});console.log(pass?'PASS':'FAIL',name);};
try{
const p=await browser.newPage({viewport:{width:1600,height:1100}});p.on('pageerror',e=>errors.push(e.message));await p.goto('http://127.0.0.1:8765/samples/my-desired-home/preview.html');await p.waitForFunction(()=>window.__ff?.ready,null,{timeout:180000});
const spawn=async(x,y)=>p.evaluate(({x,y})=>{const v=__ff.viewer;v.setMode('walk');v.paused=true;v.walker.teleport(v.walker.position.clone().set(x,0,-y));},{x,y});
const door=async(id,goal)=>p.evaluate(({id,goal})=>{const v=__ff.viewer,d=v.openings.items.find(o=>o.id===id);d.goal=goal;for(let i=0;i<120;i++)v.openings.update(1/60);return d.value===goal;},{id,goal});
const walk=async(x,y)=>p.evaluate(({x,y})=>{const w=__ff.viewer.walker;for(let i=0;i<600;i++){const dx=x-w.position.x,dz=-y-w.position.z;if(Math.hypot(dx,dz)<.06)return true;w.yaw=Math.atan2(-dx,-dz);w.update(1/60,{forward:1,strafe:0});}return false;},{x,y});
const shot=async(name,eye,target)=>{await p.evaluate(({eye,target})=>{const v=__ff.viewer;v.setMode('walk');v.paused=true;v.fitHeld=null;v.zoomAnim=null;v.walker.teleport(v.walker.position.clone().set(eye[0],0,eye[2]));v.camera.fov=66;v.camera.updateProjectionMatrix();v.camera.position.set(...eye);v.camera.lookAt(...target);for(let i=0;i<100;i++)v.adapt(.05);v.updateProbe();for(let i=0;i<100;i++)v.adapt(.05);v.hud.show(false);v.updateLights();v.vegetation?.update(v.time,v.camera);v.composer.render(.016);},{eye,target});const bytes=await p.evaluate(async()=>Array.from(new Uint8Array(await(await __ff.viewer.snapshot({width:1600})).arrayBuffer())));writeFileSync(`evidence/desired-home/${name}.png`,Buffer.from(bytes));};

await spawn(7.8,2.35);
check('Kitchen entrance stays clear',await walk(6.0,2.35));
check('Sink approach stays clear',await walk(5.3,1.45));
check('Return hob approach stays clear',await walk(6.05,1.35));
check('Fridge approach stays clear',await walk(4.85,2.05));
check('Pantry door opens fully',await door('g-kitchen-south',1));
check('Wash door opens fully',await door('g-kitchen-wash',1));
check('Pantry approach stays clear',await walk(3.8,1.0));
check('Pantry threshold remains walkable',await walk(2.8,1.0));
check('Return from pantry stays clear',await walk(3.8,1.0));
check('Central service aisle stays clear',await walk(4.28,1.5));
check('Passage beside open wash door stays clear',await walk(4.28,2.85));
check('Wash approach stays clear',await walk(3.8,2.98));
check('Wash threshold remains walkable',await walk(2.8,2.98));
await door('g-kitchen-south',0);await door('g-kitchen-wash',0);
await shot('kitchen-l-shaped',[4.3,1.68,-2.5],[6.10,1.20,-.55]);
await shot('kitchen-fridge-opposite',[6.2,1.68,-1.25],[4.65,1.15,-3.35]);
check('No browser errors',errors.length===0);
}finally{writeFileSync('evidence/desired-home/kitchen-checks.json',JSON.stringify({checks,errors},null,2));await browser.close();}
if(checks.some(c=>!c.pass)||errors.length)process.exitCode=1;
