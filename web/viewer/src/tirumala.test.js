import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from 'three';
import {buildBuckets} from './scene-builder.js';
import {describeOpenings, OpeningController} from './openings.js';
import {Walker} from './walker.js';

function runtime(slug) {
  const data=JSON.parse(readFileSync(new URL(`../../../examples/gallery/${slug}/scene.json`,import.meta.url)));
  const descriptors=describeOpenings(data);
  const moving=new Set(descriptors.flatMap(d=>d.parts.flatMap(p=>p.ids)));
  const materials={tileSize:()=>[1,1],descriptor:()=>({kind:'tile'})};
  const buckets=buildBuckets({...data,nodes:data.nodes.filter(n=>!moving.has(n.id))},materials);
  const arrays=buckets.filter(b=>b.collide).map(b=>b.geometry.attributes.position.array);
  const positions=new Float32Array(arrays.reduce((sum,a)=>sum+a.length,0)); let offset=0;
  for(const a of arrays){positions.set(a,offset);offset+=a.length;}
  const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.BufferAttribute(positions,3));
  const walker=new Walker(geo,{min:new THREE.Vector3(-5,-2,-22),max:new THREE.Vector3(20,10,5)});
  const viewer={data,walker,materials,root:new THREE.Group(),addBucket(b,g){const m=new THREE.Mesh(b.geometry);g.add(m);return m;}};
  const controller=new OpeningController(viewer,descriptors);
  return {data,walker,controller};
}
function openDoors(c){for(const item of c.items)if(item.kind!=='window'){item.value=1;item.goal=1;c.pose(item);}c.syncGeometry();}
function route(w,points,z=.1){
  w.teleport(new THREE.Vector3(points[0][0],z,-points[0][1]));
  for(const [x,y] of points.slice(1)){
    let dist=Infinity;
    for(let i=0;i<900;i++){
      const dx=x-w.position.x,dz=-y-w.position.z;dist=Math.hypot(dx,dz);
      if(dist<.07)break;
      w.yaw=Math.atan2(-dx,-dz);w.update(1/90,{forward:Math.min(1,dist*4),strafe:0});
    }
    assert.ok(dist<.07,`blocked towards ${x},${y}; feet=${w.position.toArray().join(',')}`);
    assert.ok(w.onGround && w.position.y>-.35,'must remain supported');
  }
}
const common={
  kitchen:[[4.8,6.5],[4.8,5.8],[4.5,4.15],[3.72,4.1],[3.72,2.8]],
  store:[[3.56,4.275],[1.917,4.275],[1.917,2.6]],
  master:[[6.15,7.4],[6.05,8.5],[6.05,9.5],[4.75,9.5],[3.75,10.5]],
  bathroom:[[3,13.15],[4.7,13.15]],
  caregiver:[[6.2,7.4],[6.4,8.55],[7.7428,8.55],[7.7428,12],[8.6536,12]],
  attachedWC:[[8.6536,12],[8.6536,13.05],[7.35,13.05]],
  lightwell:[[7.7428,10.35],[7.7428,11.1],[6.5,11.1]],
  // Approach the basin at the far end; do not ask the walker to pass through it.
  washGully:[[.7,1.0],[.7,2.0],[.7,3.8]],
  stairs:[[2,5.6],[.70,5.6],[.70,8.35],[4,8.35]],
};
for(const p13Slug of ['tirumala-3','tirumala-4'])test(`${p13Slug} P13: full-size walking route around both bed ends and along retained east forecourt`,()=>{
  const {data,walker:w,controller:c}=runtime(p13Slug);openDoors(c);
  const floors=buildBuckets({...data,nodes:data.nodes.filter(n=>n.id==='g-care-floor')},
    {tileSize:()=>[1,1],descriptor:()=>({kind:'tile'})});
  const bounds=new THREE.Box3();for(const b of floors)bounds.union(b.geometry.boundingBox);
  assert.ok(Math.abs(bounds.max.x-bounds.min.x-3.4296)<1e-5);
  assert.ok(Math.abs(bounds.max.z-bounds.min.z-4.0856)<1e-5);
  route(w,[[6.35,6.8],[6.35,5.3],[6.35,3],[6.55,2.2],[8.5,2.2],[8.5,5.3],[6.35,5.3]]);
  route(w,[[8.5,.6],[6.5,.6],[3.5,.6],[.7,.6],[.7,2],[.7,3.8]]);
});
test('Tirumala 4: defaults to empty car porch (defaultCarVisible=false) and exposes calibrated reference cameras',()=>{
  const {data}=runtime('tirumala-4');
  assert.equal(data.defaultCarVisible,false);
  assert.equal(data.tirumala4,true);
  for(const cam of ['ref_r07_east_northwest','ref_r11_ne_corner','ref_r08_north_garden','ref_v01_east_court_road','ref_r09_colony_junction','ref_r14_wall_pole_paving','veranda_north_garden_outlook','care_recliner_eye_level','living_sofa_eye_level']){
    assert.ok(data.cameras[cam],`missing Tirumala 4 camera ${cam}`);
  }
});
for(const slug of ['tirumala-2','tirumala-3','tirumala-4']){
  test(`${slug}: every interior shortcut starts grounded and clear with doors closed or open`,()=>{
    const {data,walker:w,controller:c}=runtime(slug);
    for(const open of [false,true]){
      if(open)openDoors(c);
      for(const [name,cam] of Object.entries(data.cameras).filter(([,cam])=>cam.enter_walk)){
        const [x,y,z]=cam.position;
        w.teleport(new THREE.Vector3(x,z-1.63,-y));
        for(let i=0;i<90;i++)w.update(1/90,{forward:0,strafe:0});
        assert.ok(w.onGround && Math.abs(w.position.y-(z-1.63))<.02,`${name} floor support: ${w.position.toArray()}, intended ${cam.position}`);
        assert.ok(Math.hypot(w.position.x-x,w.position.z+y)<.05,`${name} starts in collision (${open?'open':'closed'}): ${w.position.toArray()}, intended ${cam.position}`);
      }
    }
  });
  test(`${slug}: hall-facing wood conceals glass until opened; both clear the entrance`,()=>{
    const {walker:w,controller:c}=runtime(slug);
    const glass=c.items.find(i=>i.id==='icu-glass-living'),wood=c.items.find(i=>i.id==='icu-glass-living-wood');
    const normal=new THREE.Vector3(glass.axis.z,0,-glass.axis.x);
    const eye=glass.center.clone().addScaledVector(normal,1);eye.y=1.1;
    const ray=new THREE.Ray(eye,normal.clone().negate());
    const owner=()=>{
      const hit=c.bvh.raycastFirst(ray,THREE.DoubleSide,.01,2);
      if(!hit)return null;
      const vertex=c.geometry.index.getX(hit.faceIndex*3)*3;
      return c.chunks.find(chunk=>vertex>=chunk.offset&&vertex<chunk.offset+chunk.source.length)?.owner;
    };
    for(const i of [wood,glass]){i.value=0;c.pose(i);}c.syncGeometry();
    assert.equal(owner(),wood.id,'closed wood must be the first layer seen from the hall');
    wood.value=1;c.pose(wood);c.syncGeometry();
    assert.equal(owner(),glass.id,'opening wood must reveal the glass, still closed');
    glass.value=1;c.pose(glass);c.syncGeometry();
    assert.equal(owner(),null,'both parked layers must leave the central route open');
  });
  test(`${slug}: ICU wooden handle remains reachable when panels are parked`,()=>{
    const {walker:w,controller:c}=runtime(slug);openDoors(c);
    const item=c.items.find(i=>i.id==='icu-glass-living-wood');
    const handle=item.handle.clone().applyMatrix4(item.parts[0].group.matrixWorld);
    const normal=new THREE.Vector3(item.axis.z,0,-item.axis.x);
    const feet=handle.clone().addScaledVector(normal,.95);feet.y=.05;
    w.teleport(feet);
    for(let i=0;i<90;i++)w.update(1/60,{forward:0,strafe:0});
    assert.ok(w.onGround && Math.abs(w.position.y)<.02);
    const direction=handle.clone().sub(w.eyePosition(new THREE.Vector3())).normalize();
    w.yaw=Math.atan2(-direction.x,-direction.z);w.pitch=Math.asin(direction.y);
    c.updateTarget();
    assert.equal(c.target?.id,item.id,'aiming at the parked timber handle selects it independently');
    assert.ok(c.interact());
    for(let i=0;i<90;i++)c.update(1/60);
    assert.equal(item.value,0);assert.equal(c.items.find(i=>i.id==='icu-glass-living').value,1);
  });
  test(`${slug}: every ground-level door is operable; closed/open collision agrees`,()=>{
    const {data,walker:w,controller:c}=runtime(slug);
    for(const o of data.opening_model.openings.filter(o=>o.sill===0&&o.kind!=='cased-opening')){
      const items=c.items.filter(i=>i.id===o.id||i.id.startsWith(o.id+'-'));
      assert.ok(items.length,`missing motion: ${o.id}`);
      const d=items[0],normal=new THREE.Vector3(-d.axis.z,0,d.axis.x),center=d.center.clone();center.y=d.base+1;
      const from=center.clone().addScaledVector(normal,.2),to=center.clone().addScaledVector(normal,-.2);
      for(const i of items){i.value=0;c.pose(i);}c.syncGeometry();
      assert.equal(w.sees(from,to,.01),false,`${o.id} closed must block`);
      for(const i of items){i.value=1;c.pose(i);}c.syncGeometry();
      assert.equal(w.sees(from,to,.01),true,`${o.id} open must clear aperture centre`);
    }
  });
  test(`${slug}: actual walking capsule traverses approved rooms with car parked`,async t=>{
    const {walker:w,controller:c}=runtime(slug);openDoors(c);
    const routes={...common,...(slug==='tirumala-2'?{
      arrival:[[8.5,.3],[8.5,2.25],[6.3,2.25],[6.3,5.7]],
      ICU:[[6.2,7.4],[6.5,7.65],[7.725,7.65],[8.75,7.65]],
      ICUVeranda:[[8.1,2.30],[7.8,2.60],[7.8,4]],
      drawing:[[11.58,.3],[11.58,7.5],[10.9,7.7],[10.9,8.55]],
    }:{
      arrival:[[9.415,.3],[9.415,7.4],[6.2,7.4]],
      ICU:[[6.4,7],[6.5,6.2],[6.5,5.46],[6.5,3.91]],
      ICUVeranda:[[8.2,6.9],[8.15,6.4],[8.15,6.1],[7.85,5.5]],
      drawing:[[9,7.4],[8.95,8.4],[8.95,9.1]],
    })};
    for(const [name,points] of Object.entries(routes))await t.test(name,()=>{
      route(w,points);
      if(name==='stairs'){
        assert.ok(Math.abs(w.position.y-3.15)<.005,'reach the approved top landing');
        assert.ok(w.ceilingClear(w.position,2.2)>2.05,'stair landing needs unobstructed headroom');
      }
    });
  });
  test(`${slug}: porch, house and veranda use their specified floor levels`,()=>{
    const {walker:w}=runtime(slug);
    for(const [x,y,height] of [[11.65,1.8,-.1524],[4,1,0],...(slug==='tirumala-2'?[[6.3,2.5,0]]:[[9.4,7.4,0]])]){
      w.teleport(new THREE.Vector3(x,.1,-y));
      for(let i=0;i<120;i++)w.update(1/60,{forward:0,strafe:0});
      assert.ok(w.onGround&&Math.abs(w.position.y-height)<.004,`unexpected feet height ${w.position.y} at ${x},${y}`);
    }
  });
  test(`${slug}: walk upstairs, through every upper room and onto open terrace`,async t=>{
    const {data,walker:w,controller:c}=runtime(slug);openDoors(c);
    if(data.storeys<2)return;
    const routes={
      stairToGallery:{z:.1,points:[[2,5.6],[.7,5.6],[.7,8.35],[4,8.35],[5.7,8.35],[7.3,8.35]]},
      master:{points:[[6,8.35],[6,9.65],[4.8,9.65],[3.8,10.5]]},
      ensuite:{points:[[3,13.1],[4.4,13.1]]},
      office:{points:[[7.7,9.8],[7.7,12],[8.9,12]]},
      guest:{points:[[7.7,8.95],[8.8,8.95],[8.8,10.4]]},
      sharedBath:{points:[[7.7,12],[7.7,13.1]]},
      terrace:{points:[[7.3,8.35],[7.3,5.4],[7.3,4.1],[6.2,3.1],[5.7,2.8]]},
      sideTerrace:{points:slug==='tirumala-2'?[[7.3,7.3],[8.8,7.3],[9.4,7.3],[9.4,5.7]]:[[7.3,7.3],[8.8,7.3],[9.4,7.3],[9.4,6.7]]},
    };
    for(const [name,r] of Object.entries(routes))await t.test(name,()=>{
      route(w,r.points,r.z??3.558);
      assert.ok(Math.abs(w.position.y-3.508)<.04,`${name} must stay at first-floor level`);
    });
  });
}
