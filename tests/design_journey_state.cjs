/* Metamorphic checks for frontend approval identity: appearance does not mask geometry edits. */
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const sandbox={module:{exports:{}},structuredClone};vm.runInNewContext(fs.readFileSync('web/design-journey.js','utf8'),sandbox);const {MyVerandahJourneyState:S}=sandbox.module.exports;
for(let i=1;i<=100;i++){
 const base={draftRevision:i,brief:{width_mm:8000+i*13,depth_mm:12000,title:'Home '+i,style:'warm'},sources:[{id:'form',values:{interior_theme:'bright_natural'}}],customPlan:{floors:[{id:'floor-'+i,rooms:[{id:'room-'+i,polygon:[[0,0],[2000+i,0],[2000+i,3000],[0,3000]]}]}]},designJourney:{enabledInputs:['plot','dxf'],answers:{},pins:{positions:[]},appearance:{preset:'warm-natural'},approvals:{}}};
 const key=S.geometryKey(base),cosmetic=structuredClone(base);cosmetic.brief.style='minimal';cosmetic.brief.title='Renamed';cosmetic.sources[0].values.interior_theme='quiet_minimal';cosmetic.designJourney.appearance.preset='quiet-modern';cosmetic.draftRevision++;cosmetic.designJourney.approvals={'floor':{signature:'saved'}};assert.equal(S.geometryKey(cosmetic),key);
 for(const mutate of [p=>p.brief.width_mm++,p=>p.customPlan.floors[0].rooms[0].polygon[1][0]++,p=>p.designJourney.enabledInputs.push('text'),p=>p.designJourney.pins.positions.push('room-'+i),p=>p.designJourney.answers.conflict='text',p=>p.designJourney.imports=[{id:'new-drawing',enabled:true,provenance:{geometry:{floors:[]}}}],p=>p.designJourney.layoutSources=[{id:'manual',kind:'plan',geometry:{floors:[]}}]]){const changed=structuredClone(base);mutate(changed);assert.notEqual(S.geometryKey(changed),key);}
 assert.equal(S.geometryKey(JSON.parse(JSON.stringify(base))),key);
}
const approvals={a:{geometryHash:'a1'},b:{geometryHash:'b1'}};assert.equal(JSON.stringify(S.compatibleApprovals(approvals,[{id:'a',geometryHash:'a2'},{id:'b',geometryHash:'b1'}])),JSON.stringify({b:approvals.b}));
console.log('PASS 100 appearance/geometry/source/pin/answer metamorphic cases, approval filtering and JSON round-trip');
