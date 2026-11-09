import assert from 'node:assert/strict';
import {readFileSync, writeFileSync} from 'node:fs';
import * as THREE from '../web/viewer/node_modules/three/build/three.module.js';
import {buildBuckets} from '../web/viewer/src/scene-builder.js';
import {describeOpenings, OpeningController} from '../web/viewer/src/openings.js';
import {Walker} from '../web/viewer/src/walker.js';

const out = new URL('../output/tirumala-icu-trials/', import.meta.url), results = [];
const mat = {tileSize:()=>[1,1],descriptor:()=>({kind:'tile'})};
function check(name, condition, detail) {
  results.push({name,pass:!!condition,detail});
  console.log(condition?'PASS':'FAIL',name,detail?JSON.stringify(detail):'');
  assert.ok(condition,name);
}
function route(w, points) {
  w.teleport(new THREE.Vector3(points[0][0], .05, -points[0][1]));
  for(const [x,y] of points.slice(1)) {
    let distance=Infinity;
    for(let i=0;i<1100;i++) {
      const dx=x-w.position.x,dz=-y-w.position.z;
      distance=Math.hypot(dx,dz);if(distance<.065)break;
      w.yaw=Math.atan2(-dx,-dz);w.update(1/90,{forward:Math.min(1,distance*4),strafe:0});
    }
    assert.ok(distance<.065,`blocked towards ${x},${y}; at ${w.position.toArray()}`);
    assert.ok(w.onGround && Math.abs(w.position.y)<.015,'ground support');
  }
}
for(const key of ['compact-only','south-extension']) {
  const data=JSON.parse(readFileSync(new URL(`${key}/scene.json`,out)));
  const d=describeOpenings(data),moving=new Set(d.flatMap(o=>o.parts.flatMap(p=>p.ids)));
  const buckets=buildBuckets({...data,nodes:data.nodes.filter(n=>!moving.has(n.id))},mat);
  const arrays=buckets.filter(b=>b.collide).map(b=>b.geometry.attributes.position.array);
  const pos=new Float32Array(arrays.reduce((sum,a)=>sum+a.length,0));let offset=0;
  for(const a of arrays){pos.set(a,offset);offset+=a.length;}
  const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.BufferAttribute(pos,3));
  const walker=new Walker(geo,{min:new THREE.Vector3(-5,-2,-22),max:new THREE.Vector3(20,10,5)});
  const v={data,walker,materials:mat,root:new THREE.Group(),addBucket(b,g){const m=new THREE.Mesh(b.geometry);g.add(m);return m;}};
  const c=new OpeningController(v,d);
  for(const item of c.items)if(item.kind!=='window'){item.value=1;item.goal=1;c.pose(item);}c.syncGeometry();
  const floors=buildBuckets({...data,nodes:data.nodes.filter(n=>n.id==='g-care-floor')},mat);
  const box=new THREE.Box3();for(const b of floors)box.union(b.geometry.boundingBox);
  check(`${key}: rendered ICU metre dimensions`,Math.abs(box.max.x-box.min.x-(key==='south-extension'?3.5502:3.093))<1e-5&&Math.abs(box.max.z-box.min.z-4.5472)<1e-5,{width:box.max.x-box.min.x,depth:box.max.z-box.min.z});
  for(const id of ['icu-glass-living','living-veranda','icu-veranda-glass']) {
    const door=d.find(o=>o.id===id||o.id.startsWith(id+'-'));
    const center=door.center.clone();center.y=1.1;
    const normal=new THREE.Vector3(-door.axis.z,0,door.axis.x);
    const a=center.clone().addScaledVector(normal,.2),b=center.clone().addScaledVector(normal,-.2);
    const items=c.items.filter(o=>o.id===id||o.id.startsWith(id+'-'));
    check(`${key}: ${id} open is clear`,walker.sees(a,b,.01));
    for(const o of items){o.value=0;c.pose(o);}c.syncGeometry();
    check(`${key}: ${id} closed blocks`,!walker.sees(a,b,.01));
    for(const o of items){o.value=1;c.pose(o);}c.syncGeometry();
  }
  for(const [name,pts] of Object.entries({
    arrival:[[8.5,.3],[8.5,2.25],[6.05,2.25],[6.05,3.8],[6.05,6.5]],
    kitchen:[[6.05,4.2],[4.5,4.2],[3.7,4.15],[3.7,2.8]],
    hallICU:[[6.05,7.25],[7.7,7.25],[8.7,7.25]],
    verandaICU:[[8.1,2.3],[7.8,2.6],[7.8,4]],
    drawing:[[11.58,.3],[11.58,7.5],[10.9,7.7],[10.9,8.55]],
    ...(key==='south-extension'?{bedHead:[[8.5,7.25],[7.155,7.25],[7.155,4.85],[7.8,4.85]],
      bedFoot:[[8.5,7.25],[10.03,7.25],[10.03,4.85],[7.8,4.85]]}:{}),
  })) {route(walker,pts);check(`${key}: walking ${name}`,true);}
}
writeFileSync(new URL('walking-checks.json',out),JSON.stringify(results,null,2));
