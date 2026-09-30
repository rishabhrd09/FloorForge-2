import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import * as THREE from 'three';
import { Walker } from './walker.js';
import { describeOpenings, OpeningController } from './openings.js';

function fixture(kind = 'door', handle = false) {
  const g = new THREE.BoxGeometry(1, 1, 1), p = g.attributes.position, vertices = [];
  for (let i = 0; i < p.count; i++) vertices.push([p.getX(i), p.getY(i), p.getZ(i)]);
  const faces = []; for (let i = 0; i < g.index.count; i += 3) faces.push([g.index.getX(i), g.index.getX(i + 1), g.index.getX(i + 2)]);
  g.dispose();
  const window = kind === 'window';
  const node = { id: 'leaf', owner: 'opening', floor: 0, role: window ? 'glass' : 'door', asset: 'box', material: 'wood', rotation: [0, 0, 0],
    position: window ? [-.3, 0, 1.5] : [-.545, .55, 1.05], scale: window ? [.56, .012, .9] : [.042, 1.1, 2.1] };
  const data = { nodes: [node], assets: { box: { vertices, faces } }, materials: { wood: {} }, floor_height: 3, rooms: [] };
  if (handle) data.nodes.push({ ...node, id: 'handle', owner: 'handle', position: [-.49, 1, 1.05], scale: [.08,.12,.02] });
  if (window) data.nodes.push({ ...node, id: 'second', position: [.3, .028, 1.5] });
  const building = { walls: [{ id: 'wall', a: [-600, 0], b: [600, 0] }], openings: [{ id: 'opening', wall_id: 'wall', kind, floor: 0, offset: 0, width: 1200, height: window ? 1000 : 2100, sill: window ? 1000 : 0, hinge: 'start' }] };
  const ground = new THREE.PlaneGeometry(20, 20).rotateX(-Math.PI / 2);
  const walker = new Walker(ground, { min: new THREE.Vector3(-10, -2, -10), max: new THREE.Vector3(10, 10, 10) });
  walker.teleport(new THREE.Vector3(0, 0, 2), 0);
  const viewer = { data, walker, root: new THREE.Group(), materials: { tileSize: () => [1, 1], descriptor: () => ({ kind: 'wood' }) },
    addBucket(b, group) { const mesh = new THREE.Mesh(b.geometry); group.add(mesh); return mesh; } };
  const controller = new OpeningController(viewer, describeOpenings(data, building));
  return { controller, walker, item: controller.items[0], viewer, data };
}
const finish = c => { for (let i = 0; i < 65; i++) c.update(1 / 60); };

test('all legacy opening types resolve to real scene objects without mutating the design', () => {
  const scene = JSON.parse(readFileSync(new URL('../../../examples/demo/scene.json', import.meta.url)));
  const building = JSON.parse(readFileSync(new URL('../../../examples/demo/building.json', import.meta.url)));
  const before = JSON.stringify(scene), descriptors = describeOpenings(scene, building), ids = new Set(scene.nodes.map(n => n.id));
  assert.equal(descriptors.length, building.openings.filter(o => o.kind !== 'cased').length);
  for (const d of descriptors) assert.ok(d.parts.every(p => p.ids.length && p.ids.every(id => ids.has(id))));
  assert.equal(JSON.stringify(scene), before);
});

test('hinged doors close across the actual opening and reopen with matching collision', () => {
  const { controller: c, walker: w, item, data } = fixture(), before = JSON.stringify(data);
  const from = new THREE.Vector3(0, 1, 1), to = new THREE.Vector3(0, 1, -1);
  assert.equal(w.sees(from, to), true);
  item.goal = 0; finish(c); assert.equal(item.value, 0); assert.equal(w.sees(from, to), false);
  const mesh = item.parts[0].group.children[0], box = new THREE.Box3().setFromObject(mesh);
  assert.ok(box.getSize(new THREE.Vector3()).x > 1.09 && box.getSize(new THREE.Vector3()).z < .05);
  item.goal = 1; finish(c); assert.equal(w.sees(from, to), true);
  assert.equal(JSON.stringify(data), before);
});

test('a closed door blocks walking while an open door allows passage', () => {
  const { controller: c, walker: w, item } = fixture();
  item.goal = 0; finish(c); w.teleport(new THREE.Vector3(0, 0, 1), 0);
  for (let i = 0; i < 90; i++) w.update(1 / 60, { forward: 1, strafe: 0 });
  assert.ok(w.position.z > .25);
  w.teleport(new THREE.Vector3(0, 0, 1), 0); item.goal = 1; finish(c);
  for (let i = 0; i < 90; i++) w.update(1 / 60, { forward: 1, strafe: 0 });
  assert.ok(w.position.z < -1);
});

test('legacy self-owned handles move with the leaf instead of leaving an invisible obstacle', () => {
  const { controller: c, item, data, walker: w } = fixture('door', true);
  assert.ok(item.parts[0].ids.includes('handle'));
  const n=data.nodes.find(n=>n.id==='handle');
  const authored=new THREE.Vector3(n.position[0],n.position[2],-n.position[1]);
  item.goal=0; finish(c);
  const closed=authored.clone().applyMatrix4(item.parts[0].group.matrixWorld);
  assert.ok(closed.distanceTo(authored)>.7);
  assert.equal(w.sees(new THREE.Vector3(-.49,1.05,-.7),new THREE.Vector3(-.49,1.05,-1.3)),true);
});

test('nearby openings are reachable from both sides but not at distance, behind the visitor, or another floor', () => {
  const { controller: c, walker: w, item } = fixture();
  for (const sign of [-1, 1]) {
    w.position.set(0, 0, sign); const eye = new THREE.Vector3(0, 1.63, sign), look = new THREE.Vector3(0, 0, -sign);
    assert.equal(c.findTarget(eye, look), item);
    assert.equal(c.findTarget(eye, look.negate()), null);
  }
  w.position.set(0, 3, 1); assert.equal(c.findTarget(new THREE.Vector3(0, 4.63, 1), new THREE.Vector3(0, 0, -1)), null);
  w.position.set(0, 0, 5); assert.equal(c.findTarget(new THREE.Vector3(0, 1.63, 5), new THREE.Vector3(0, 0, -1)), null);
});

test('a panel stops before sweeping through the walking capsule', () => {
  const { controller: c, walker: w, item } = fixture();
  w.position.set(0, 0, -.3); item.goal = 0; finish(c);
  assert.ok(item.value > 0); assert.equal(w.overlaps(c.bvh), false); assert.match(c.message, /Step clear/);
});

test('sliding windows visibly open, update collision and retain the sill in their descriptor', () => {
  const { controller: c, walker: w, item } = fixture('window');
  const from = new THREE.Vector3(-.3, 1.5, 1), to = new THREE.Vector3(-.3, 1.5, -1);
  assert.equal(w.sees(from, to), false); item.goal = 1; finish(c); assert.equal(w.sees(from, to), true);
  c.target = item; assert.match(c.prompt().note, /raised sill/);
  item.goal = 0; finish(c); assert.equal(w.sees(from, to), false);
});

test('a wall in front of the opening prevents remote interaction', () => {
  const { controller: c, walker: w } = fixture();
  const blocker = new THREE.BoxGeometry(4, 3, .15).translate(0, 1.5, .6);
  const temp = new Walker(blocker, w.bounds);
  w.bvh = temp.bvh; w.position.set(0, 0, 1.4);
  assert.equal(c.findTarget(new THREE.Vector3(0, 1.63, 1.4), new THREE.Vector3(0, 0, -1)), null);
});

test('three-track care doors stack in the frame and open a collision-free passage', () => {
  const {viewer,walker:w,data}=fixture('glazed');
  const template=data.nodes[0];
  data.nodes=[0,1,2].map(pane=>({...template,id:`pane-${pane}`,owner:'opening',role:'glass',slidingPanel:pane,position:[-.4+pane*.4,pane*.035,1.05],scale:[.38,.018,2.0]}));
  viewer.data=data;
  const building={walls:[{id:'wall',a:[-600,0],b:[600,0]}],openings:[{id:'opening',wall_id:'wall',kind:'glazed',sliding:true,floor:0,offset:0,width:1200,height:2100,sill:0}]};
  const c=new OpeningController(viewer,describeOpenings(data,building)),item=c.items[0];
  assert.equal(item.parts.length,2);assert.ok(item.parts.every(p=>p.slide&&!p.pivot));
  const from=new THREE.Vector3(.35,1,1),to=new THREE.Vector3(.35,1,-1);
  assert.equal(w.sees(from,to),false);
  item.goal=1;finish(c);assert.equal(item.value,1);assert.equal(w.sees(from,to),true);
  for(const part of item.parts) assert.ok(part.group.matrix.elements[12]<0);
  item.goal=0;finish(c);assert.equal(w.sees(from,to),false);
});

test('main gate opens both leaves, clears its collision and can close from inside', () => {
  const {viewer, walker:w, data}=fixture();
  const template=data.nodes[0];
  data.nodes=[-1,1].map((sign,i)=>({...template,id:`gate-${i}`,owner:'main-gate',floor:-1,role:'gate',position:[sign*.75,0,.8],scale:[1.5,.05,1.6]}));
  data.gate_model=[{id:'main-gate',label:'Main vehicle gate',kind:'gate',floor:-1,base:0,sill:0,start:[-1.5,0,0],axis:[1,0,0],width:3,height:1.6,initial:0,
    parts:[{ids:['gate-0'],pivot:[-1.5,0,0],angle:Math.PI/2},{ids:['gate-1'],pivot:[1.5,0,0],angle:-Math.PI/2}]}];
  const before=JSON.stringify(data),c=new OpeningController(viewer,describeOpenings(data)),item=c.items[0];
  w.teleport(new THREE.Vector3(0,0,1),0);c.updateTarget();
  assert.equal(c.target,item);assert.match(c.prompt().text,/Open main vehicle gate/);
  const from=new THREE.Vector3(0,1,1),to=new THREE.Vector3(0,1,-1);
  assert.equal(w.sees(from,to),false);assert.equal(c.interact(),true);finish(c);
  assert.equal(item.value,1);assert.equal(w.sees(from,to),true);
  for(let i=0;i<90;i++)w.update(1/60,{forward:1,strafe:0});
  assert.ok(w.position.z < -1);
  w.teleport(new THREE.Vector3(0,0,-1),Math.PI);c.updateTarget();
  assert.equal(c.target,item);assert.match(c.prompt().text,/Close main vehicle gate/);
  assert.equal(c.interact(),true);finish(c);assert.equal(item.value,0);assert.equal(w.sees(from,to),false);
  assert.equal(JSON.stringify(data),before);
});

test('closed authored doors use explicit swing data and keep collision aligned', () => {
  const {viewer,walker:w,data}=fixture();
  data.nodes[0].position=[0,0,1.05];data.nodes[0].rotation=[0,0,-Math.PI/2];
  data.door_motion={opening:{ids:['leaf'],pivot:[-.545,0,0],angle:Math.PI/2}};
  const building={walls:[{id:'wall',a:[-600,0],b:[600,0]}],openings:[{id:'opening',wall_id:'wall',kind:'door',floor:0,offset:0,width:1200,height:2100,sill:0}]};
  const before=JSON.stringify(data),c=new OpeningController(viewer,describeOpenings(data,building)),item=c.items[0];
  const from=new THREE.Vector3(0,1,1),to=new THREE.Vector3(0,1,-1);
  assert.equal(item.value,0);assert.equal(w.sees(from,to),false);
  item.goal=1;finish(c);assert.equal(item.value,1);assert.equal(w.sees(from,to),true);
  item.goal=0;finish(c);assert.equal(w.sees(from,to),false);assert.equal(JSON.stringify(data),before);
});

test('two-panel living slider opens half the aperture and keeps its fixed panel in place', () => {
  const {viewer,walker:w,data}=fixture('glazed');const template=data.nodes[0];
  data.nodes=[0,1].map(pane=>({...template,id:`pane-${pane}`,owner:'opening',role:'glass',slidingPanel:pane,position:[-.625+pane*1.25,pane*.035,1.2],scale:[1.215,.018,2.3]}));
  viewer.data=data;
  const building={walls:[{id:'wall',a:[-1300,0],b:[1300,0]}],openings:[{id:'opening',wall_id:'wall',kind:'glazed',sliding:true,slidingPanels:2,floor:0,offset:0,width:2600,height:2400,sill:0}]};
  const c=new OpeningController(viewer,describeOpenings(data,building)),item=c.items[0];
  assert.equal(item.parts.length,1);assert.equal(item.clearWidth,1.21);
  assert.deepEqual(item.parts[0].ids,['pane-1']);
  const from=new THREE.Vector3(.65,1,1),to=new THREE.Vector3(.65,1,-1);
  assert.equal(w.sees(from,to),false);item.goal=1;finish(c);assert.equal(w.sees(from,to),true);
  item.goal=0;finish(c);assert.equal(w.sees(from,to),false);
});

test('paired timber and mesh leaves move independently and remain selectable after opening', () => {
  const {viewer,walker:w,data}=fixture();const template=data.nodes[0];
  const layers=[];data.nodes=[];
  for(const [layer,depth,sign] of [['timber',.1,1],['mesh',-.1,-1]]) for(const side of [-1,1]) {
    const id=`${layer}-${side}`;
    data.nodes.push({...template,id,position:[side*.62,depth,1.2],scale:[1.22,.03,2.3]});
    layers.push({id,label:id,ids:[id],pivot:[side*1.23,depth,0],angle:-side*sign*Math.PI/2,handle:[side*.13,depth,1.15]});
  }
  data.door_motion={opening:{layers,clearWidth:2.46}};
  const building={walls:[{id:'wall',a:[-1300,0],b:[1300,0]}],openings:[{id:'opening',wall_id:'wall',kind:'door',floor:0,offset:0,width:2600,height:2400,sill:0}]};
  const c=new OpeningController(viewer,describeOpenings(data,building));
  assert.equal(c.items.length,4);assert.ok(c.items.every(i=>i.value===0));
  w.teleport(new THREE.Vector3(0,0,3));
  c.items[0].goal=1;finish(c);
  assert.equal(c.items[0].value,1);assert.ok(c.items.slice(1).every(i=>i.value===0));
  const item=c.items[0],handle=item.handle.clone().applyMatrix4(item.parts[0].group.matrixWorld);
  const eye=handle.clone();eye.x=0;eye.y=1.63;w.position.set(eye.x,0,eye.z);
  assert.equal(c.findTarget(eye,handle.clone().sub(eye).normalize()),item);
  w.teleport(new THREE.Vector3(0,0,3));
  for(const i of c.items)i.goal=1;finish(c);
  const from=new THREE.Vector3(0,1,1),to=new THREE.Vector3(0,1,-1);
  assert.equal(w.sees(from,to),true);
  c.items[2].goal=0;finish(c);
  assert.equal(w.sees(new THREE.Vector3(-.6,1,1),new THREE.Vector3(-.6,1,-1)),false);
  assert.equal(c.items[0].value,1);
});
