// Isolated browser: preserves the user's camera and browser storage.
import {writeFileSync} from 'node:fs';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const checks=[],errors=[];const check=(name,pass)=>{checks.push({name,pass:!!pass});console.log(pass?'PASS':'FAIL',name);if(!pass)throw Error(name);};
try{
 const p=await browser.newPage({viewport:{width:1500,height:1000}});p.on('pageerror',e=>errors.push(e.message));
 await p.goto('http://127.0.0.1:8765/samples/my-desired-home/preview.html');await p.waitForFunction(()=>window.__ff?.ready,null,{timeout:180000});
 await p.evaluate(()=>{const v=__ff.viewer;v.paused=true;v.setMode('walk');});
 const spawn=async(x,y,z=3.17)=>p.evaluate(({x,y,z})=>{const v=__ff.viewer;v.walker.teleport(v.walker.position.clone().set(x,z,-y));},{x,y,z});
 const walk=async(x,y)=>p.evaluate(({x,y})=>{const w=__ff.viewer.walker;for(let i=0;i<650;i++){const dx=x-w.position.x,dz=-y-w.position.z;if(Math.hypot(dx,dz)<.06)return Math.abs(w.position.y-3.17)<.15;w.yaw=Math.atan2(-dx,-dz);w.update(1/60,{forward:1,strafe:0});}return false;},{x,y});
 const open=async id=>p.evaluate(id=>{const v=__ff.viewer,d=v.openings.items.find(o=>o.id===id);d.goal=1;for(let i=0;i<90;i++)v.openings.update(1/60);},id);
 await spawn(5.1,7.7);const route=[];for(const [x,y]of [[6.7,7.85],[8.25,7.85],[8.25,8.9],[12,8.9]])route.push(await walk(x,y));check('Upper gallery bypasses courtyard and connects rear rooms',route.every(Boolean));
 await spawn(10.2,2.85);await open('u-lobby-terrace');const balcony=[];for(const [x,y]of [[11.7,2.85],[11.7,.6],[8.5,.6],[4.0,.6]])balcony.push(await walk(x,y));check('L-shaped balcony is walkable from right terrace across the front',balcony.every(Boolean));
 check('Clear canopy and bedroom/bathroom lightwell windows are present',await p.evaluate(()=>{const s=__ff.viewer.data;return s.nodes.some(n=>n.id==='g-care-court/glass-canopy'&&n.material==='glass')&&['g-bedroom-garden-window','g-caregiver-lightwell-window'].every(id=>s.opening_model.openings.some(o=>o.id===id));}));
 const shot=async(name,eye,target,fov=55)=>{await p.evaluate(({eye,target,fov})=>{const v=__ff.viewer;v.setMode('solid');v.paused=false;v.fitHeld=null;v.zoomAnim=null;v.camera.fov=fov;v.camera.updateProjectionMatrix();v.camera.position.set(...eye);v.controls.target.set(...target);v.controls.update();v.dirty=true;},{eye,target,fov});await p.waitForTimeout(700);await p.screenshot({path:`evidence/desired-home/${name}.png`});};
 await shot('courtyard-garden',[6.8,1.6,-8.95],[6.55,1.85,-12.7],65);
 await shot('balcony-front',[21,9,18],[8.8,3.1,-4.5],46);
 await shot('facade-side',[-9,10,8],[6.2,3,-6.2],50);
 await shot('balcony-walk',[4.0,4.75,-.55],[12,4.25,-.75],65);
 check('No browser errors',errors.length===0);
 writeFileSync('evidence/desired-home/courtyard-balcony-checks.json',JSON.stringify({checks,errors},null,2));
}finally{await browser.close();}
