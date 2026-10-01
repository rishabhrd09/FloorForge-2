// Isolated cameras and walking checks; leaves the user's browser view untouched.
import {writeFileSync} from 'node:fs';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const checks=[],errors=[];const check=(name,pass)=>{checks.push({name,pass:!!pass});console.log(pass?'PASS':'FAIL',name);if(!pass)throw Error(name);};
try{
 const p=await browser.newPage({viewport:{width:1500,height:1000}});p.on('pageerror',e=>errors.push(e.message));
 await p.goto('http://127.0.0.1:8765/samples/my-desired-home/preview.html');await p.waitForFunction(()=>window.__ff?.ready,null,{timeout:180000});
 const shot=async(name,eye,target,fov=65)=>{await p.evaluate(({eye,target,fov})=>{const v=__ff.viewer;v.setMode('solid');v.paused=false;v.fitHeld=null;v.zoomAnim=null;v.camera.fov=fov;v.camera.updateProjectionMatrix();v.camera.position.set(...eye);v.controls.target.set(...target);v.controls.update();v.dirty=true;},{eye,target,fov});await p.waitForTimeout(900);await p.screenshot({path:`evidence/desired-home/${name}.png`});};
 await shot('rotated-stair',[5.65,1.7,-6.25],[2.2,1.95,-4.85],80);
 await shot('stair-east-window',[.77,1.65,-1.55],[.82,2.3,-3.53],75);
 await p.evaluate(()=>{const v=__ff.viewer,d=v.openings.items.find(o=>o.id==='g-care-caregiver');d.goal=1;for(let i=0;i<90;i++)v.openings.update(1/60);});
 await shot('caregiver-door-inward',[10.15,1.7,-11.35],[8.12,1.15,-11.72],68);
 check('Caregiver door swings into caregiver room',await p.evaluate(()=>__ff.viewer.data.opening_model.openings.find(o=>o.id==='g-care-caregiver').swing==='g-caregiver'));
 await p.evaluate(()=>{const v=__ff.viewer;v.paused=true;v.setMode('walk');v.walker.teleport(v.walker.position.clone().set(3.9,6.325,-5.45));const d=v.openings.items.find(o=>o.id==='south-stair-core-1-roof-door');d.goal=1;for(let i=0;i<90;i++)v.openings.update(1/60);});
 const walk=async(x,y)=>p.evaluate(({x,y})=>{const w=__ff.viewer.walker;let reached=false;for(let i=0;i<600;i++){const dx=x-w.position.x,dz=-y-w.position.z;if(Math.hypot(dx,dz)<.06){reached=true;break;}w.yaw=Math.atan2(-dx,-dz);w.update(1/60,{forward:1,strafe:0});}return {reached,position:w.position.toArray()};},{x,y});
 const roofExit=await walk(3.9,6.85);console.log(roofExit);check('Roof landing door leads to terrace',roofExit.reached&&roofExit.position[1]>6.2);
 check('No browser errors',errors.length===0);
 writeFileSync('evidence/desired-home/rotated-stair-checks.json',JSON.stringify({checks,errors},null,2));
}finally{await browser.close();}
