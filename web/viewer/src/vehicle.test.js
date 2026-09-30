import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import { readFileSync } from 'node:fs';
import { ParkedVehicle } from './vehicle.js';
import { Walker } from './walker.js';
function fixture() {
  const data = JSON.parse(readFileSync(new URL('../../../examples/gallery/my-desired-home/scene.json', import.meta.url)));
  const g = new THREE.PlaneGeometry(60, 60).rotateX(-Math.PI/2).translate(0,-.41,0);
  const walker = new Walker(g,{min:new THREE.Vector3(-30,-5,-30),max:new THREE.Vector3(30,20,30)});
  walker.teleport(new THREE.Vector3(15.5,-.41,-2.6));
  const viewer = { data, walker, mode:'walk', materials:{tileSize:()=>[1,1],descriptor:()=>({})},
    addBucket:b=>new THREE.Mesh(b.geometry), clearProbes(){}, onStatus(){},
    mergeForCollision(gs){const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(gs.flatMap(g=>Array.from(g.attributes.position.array)),3));return g;} };
  return { viewer, car:new ParkedVehicle(viewer,data.nodes.filter(n=>n.owner==='parked-car')) };
}
test('hiding car removes only vehicle collision and showing restores it, without mutating design',()=>{
  const {viewer:v,car}=fixture(), before=JSON.stringify(v.data);
  const a=new THREE.Vector3(15.5,.4,-2.6),b=new THREE.Vector3(18,.4,-2.6);
  assert.equal(v.walker.sees(a,b),false);
  assert.equal(car.setVisible(false),true);
  assert.equal(v.walker.sees(a,b),true);
  assert.ok(car.meshes.every(m=>!m.visible));
  assert.equal(car.setVisible(true),true);
  assert.equal(v.walker.sees(a,b),false);
  assert.equal(JSON.stringify(v.data),before);
  car.dispose();v.walker.dispose();
});
test('car cannot be shown on top of the visitor',()=>{
  const {viewer:v,car}=fixture();car.setVisible(false);
  v.walker.teleport(new THREE.Vector3(17.03,-.41,-2.6));
  assert.equal(car.setVisible(true),false);
  assert.equal(car.visible,false);
  v.walker.teleport(new THREE.Vector3(15.5,-.41,-2.6));
  assert.equal(car.setVisible(true),true);
  car.dispose();v.walker.dispose();
});
