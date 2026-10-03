import {WebGLRenderer,Scene,OrthographicCamera,Group,Shape,ShapeGeometry,Mesh,MeshBasicMaterial,DoubleSide} from 'three';
import {gsap} from 'gsap';

// A decorative garden layer, isolated from the architectural viewer and its scene.
const hero=document.querySelector('.start-hero');
if(hero){
 const canvas=hero.querySelector('.hero-garden'),photo=hero.querySelector('.start-hero-image'),button=hero.querySelector('#hero-motion');
 button.hidden=false;
 const reduced=matchMedia('(prefers-reduced-motion: reduce)'),finePointer=matchMedia('(hover: hover) and (pointer: fine)');
 let renderer,scene,camera,observer,resizeObserver,visible=true,paused=false,ticking=false,lastFrame=0,disposed=false;
 const fronds=[],resources=[],motion={x:0,y:0},intro=gsap.timeline({paused:true});
 const canMove=()=>!disposed&&!paused&&!reduced.matches&&visible&&!document.hidden&&document.body.classList.contains('at-start');
 const draw=time=>{
  if(!renderer||time-lastFrame<1/30)return;lastFrame=time;
  fronds.forEach((g,i)=>{g.rotation.z=g.userData.angle+Math.sin(time*.42+i)*.018+motion.x*.014;});
  renderer.render(scene,camera);
 };
 function sync(){
  const active=canMove();hero.dataset.motion=active?'playing':'paused';
  button.textContent=reduced.matches?'Motion reduced':paused?'Play motion':'Pause motion';button.disabled=reduced.matches;button.setAttribute('aria-pressed',String(paused||reduced.matches));
  if(active&&!ticking){gsap.ticker.add(draw);ticking=true;intro.play();}
  if(!active){if(ticking){gsap.ticker.remove(draw);ticking=false;}intro.progress(1).pause();gsap.killTweensOf(motion);gsap.killTweensOf(photo);gsap.set(photo,{x:0,y:0,scale:1});motion.x=motion.y=0;}
 }
 try{
  if(!reduced.matches){
   renderer=new WebGLRenderer({canvas,alpha:true,antialias:true,powerPreference:'low-power'});renderer.setClearColor(0,0);renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));
   scene=new Scene();camera=new OrthographicCamera(-15,15,8,-8,.1,50);camera.position.z=10;
   const leaf=new Shape();leaf.moveTo(0,0);leaf.bezierCurveTo(.7,.45,.7,1.5,0,2);leaf.bezierCurveTo(-.45,1.3,-.6,.5,0,0);
   const geometry=new ShapeGeometry(leaf);resources.push(geometry);
   for(let f=0;f<4;f++){
    const g=new Group(),material=new MeshBasicMaterial({color:[0x375842,0x68835b,0x46684b,0x92a17b][f],transparent:true,opacity:.26,side:DoubleSide,depthWrite:false});resources.push(material);
    for(let i=0;i<9;i++)for(const side of [-1,1]){const m=new Mesh(geometry,material);m.position.set(side*.05,i*.62,0);m.rotation.z=side*(.7+i*.05);const scale=.6+(8-i)*.075;m.scale.set(scale,scale,1);g.add(m);}
    g.position.set(-14+f*1.3,-9-f*.6,f*.05);g.userData.angle=-.7+f*.36;g.rotation.z=g.userData.angle;scene.add(g);fronds.push(g);
   }
   const resize=()=>{const r=hero.getBoundingClientRect();if(!r.width||!r.height)return;renderer.setSize(r.width,r.height,false);camera.left=-8*r.width/r.height;camera.right=-camera.left;camera.updateProjectionMatrix();fronds.forEach((g,i)=>g.position.x=camera.left+1+i*1.25);renderer.render(scene,camera);};
   resizeObserver=new ResizeObserver(resize);resizeObserver.observe(hero);resize();hero.dataset.garden='three';
  }
 }catch{renderer?.dispose();renderer=null;canvas.hidden=true;hero.dataset.garden='static';}
 if(!reduced.matches){intro.from(hero.querySelectorAll('.start-hero-copy > *'),{y:22,opacity:.85,duration:.95,stagger:.13,ease:'power2.out'}).from(hero.querySelector('figcaption'),{y:12,opacity:.85,duration:.7},.6);}
 const point=e=>{if(!canMove()||!finePointer.matches)return;const r=hero.getBoundingClientRect(),x=(e.clientX-r.left)/r.width-.5,y=(e.clientY-r.top)/r.height-.5;gsap.to(motion,{x,y,duration:1.5,overwrite:true,ease:'power2.out'});gsap.to(photo,{x:x*10,y:y*7,scale:1.025,duration:1.6,overwrite:true,ease:'power2.out'});};
 const leave=()=>{if(canMove()){gsap.to(motion,{x:0,y:0,duration:1.4,overwrite:true});gsap.to(photo,{x:0,y:0,scale:1,duration:1.4,overwrite:true});}};
 hero.addEventListener('pointermove',point);hero.addEventListener('pointerleave',leave);
 button.onclick=()=>{paused=!paused;sync();};reduced.addEventListener('change',sync);document.addEventListener('visibilitychange',sync);
 observer=new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;sync();},{threshold:.03});observer.observe(hero);
 const navigation=new MutationObserver(sync);navigation.observe(document.body,{attributes:true,attributeFilter:['class']});
 addEventListener('pagehide',e=>{if(e.persisted)return;disposed=true;sync();observer.disconnect();resizeObserver?.disconnect();navigation.disconnect();intro.kill();resources.forEach(r=>r.dispose());renderer?.dispose();});
 sync();
}
