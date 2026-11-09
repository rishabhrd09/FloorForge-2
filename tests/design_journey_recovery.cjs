/* Regression: an edit decision must open its real editor, never become an answer. */
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const sandbox={module:{exports:{}},structuredClone};
vm.runInNewContext(fs.readFileSync('web/design-journey.js','utf8'),sandbox);
const {MyVerandahJourneyState:S,MyVerandahDesignJourney:Journey}=sandbox.module.exports;
const project={brief:{storeys:3},editorState:{mode:'compass',compassDraft:{grid:{cols:4,rows:4},floors:[{id:'ground'},{id:'first'},{id:'second'}],rooms:[{id:'living',floorId:'ground',regions:['0:0']},{id:'bed',floorId:'first',regions:['1:2:L']},{id:'study',floorId:'second',regions:['2:1:F']}]}},designJourney:{answers:{kept:'choice'},pins:{positions:['bed']}}};
const snapshot=JSON.stringify(project);
const q={id:'upper-room',prompt:'Make the bedroom usable',explanation:'It needs an outside wall.',editor:{kind:'compass'},affected:[{floorId:'first',roomId:'bed',name:'Bedroom',current:{width_mm:1700,area_m2:6},required:{minimum_width_mm:2400,minimum_area_m2:9}}],steps:['Move its cells beside an outside wall.'],choices:[{id:'edit',action:'edit-layout'}]};
const target=S.editorTarget(q,q.choices[0],project);
assert.equal(target.floorIndex,1);assert.equal(target.floorId,'first');assert.equal(target.roomId,'bed');assert.equal(target.steps[0],q.steps[0]);
assert.equal(S.editorTarget({affected:[{floorId:'second'}]}, {},project).floorIndex,2);
assert.equal(S.editorTarget({affected:[{floor:2}]},{},project).floorIndex,2);
assert.match(S.measurementText(q.affected[0]),/1.70 m/);assert.match(S.measurementText(q.affected[0]),/6.00 m²/);assert.match(S.measurementText(q.affected[0]),/9.00 m²/);
const journey=Object.create(Journey.prototype);let routed,requests=0,closed=0;
journey.options={project:()=>project,editTarget:t=>{routed=t;},request:()=>{requests++;throw Error('Editor navigation must not prepare a fictitious answer');},notify:message=>{throw Error(message);}};
journey.dialog={close:()=>closed++};journey.sequence=1;journey.selectedChoice='edit';journey.result={question:q};
assert.match(journey.affectedIllustration(q),/First; affected rooms/);
assert.match(journey.affectedIllustration({...q,affected:[{floorId:'second',roomId:'study'}]}),/Second; affected rooms/);
async function main(){
 for(const [action,kind] of Object.entries({'edit-layout':'compass','edit':'compass','edit-stairs':'compass','review-pin':'compass','choose-scope':'compass','edit-text':'text','edit-input':'inputs','edit-sketch':'sketch','edit-plan':'plan','edit-dxf':'dxf','edit-survey':'survey','edit-plot':'plot'})){
  journey.result={question:{...q,choices:[{id:'edit',action}]}};await journey.previewAnswer();assert.equal(routed.kind,kind,action);assert.equal(routed.floorIndex,1,action);
 }
 assert.equal(requests,0);assert.equal(closed,12);assert.equal(JSON.stringify(project),snapshot);
 const exact={editorState:{mode:'custom',compassDraft:project.editorState.compassDraft},customPlan:{floors:[{id:'a',rooms:[]},{id:'b',rooms:[]},{id:'c',rooms:[{id:'study',polygon:[[0,0],[1000,0],[1000,3000],[0,3000]]}]}]}};
 assert.equal(S.editorTarget({affected:[{roomId:'study'}]},{action:'edit-plan'},exact).floorIndex,2);
 journey.options.project=()=>exact;
 const exactPicture=journey.affectedIllustration({editor:{kind:'plan',floorIndex:2},affected:[{roomId:'study'}]});assert.match(exactPicture,/Second; actual exact-plan geometry/);assert.match(exactPicture,/<polygon/);assert.doesNotMatch(exactPicture,/<rect/);assert.match(exactPicture,/#ca8455/);
 assert.doesNotMatch(journey.affectedIllustration({editor:{kind:'plan',floorIndex:1}}),/<rect|<polygon/);journey.options.project=()=>project;
 const compassSandbox={module:{exports:{}}};vm.runInNewContext(fs.readFileSync('web/compass-state.js','utf8'),compassSandbox);vm.runInNewContext(fs.readFileSync('web/compass-editor.js','utf8')+'\nmodule.exports=FloorForgeCompassEditor;',compassSandbox);
 const compass=Object.create(compassSandbox.module.exports.prototype),calls=[];compass.history={value:project.editorState.compassDraft};compass.brief={storeys:3};compass.floor=0;compass.render=()=>calls.push({floor:compass.floor,selected:compass.selected});compass.message=()=>{};compass.$=id=>({focus:()=>calls.push(id),scrollIntoView:()=>{}});
 compass.focusIssue(target);assert.equal(calls[0].floor,1);assert.equal(calls[0].selected,'bed');assert.equal(calls[1],'c-cell-1-2');
 compass.focusIssue(S.editorTarget({affected:[{floorId:'second'}]},{},project));assert.equal(compass.floor,2);assert.equal(compass.selected,null);
 // A missing middle-floor stair must not select a related stair on Ground.
 const missingStair=S.editorTarget({editor:{kind:'compass',floorId:'first',floorIndex:1},affected:[{floorId:'first'},{floorId:'ground',roomId:'living'},{floorId:'second',roomId:'study'}]}, {},project);
 assert.equal(missingStair.floorIndex,1);assert.equal(missingStair.roomId,undefined);compass.focusIssue(missingStair);assert.equal(compass.floor,1);assert.equal(compass.selected,null);
 compass.load(project);assert.equal(compass.draft.site.context,'unknown');assert.equal(compass.draft.requirements.length,0);assert.equal(JSON.stringify(compass.draft.rooms),JSON.stringify(project.editorState.compassDraft.rooms));assert.equal(JSON.stringify(project),snapshot);
 // Matching geometry in an uploaded project cannot keep foreign signatures locked
 // behind disabled Approve buttons. Preparation returns the studio's trusted set.
 const draft=structuredClone(project);draft.editorState.homeInputs=['plot','compass'];const localApproval={floorHash:'first-v1',signature:'verified-by-server'},localConfirmation={geometryHash:'home-v1',signature:'verified-by-server'};
 journey.options.project=()=>({...draft,designJourney:journey.state});journey.clearEditorGuidance=()=>{};journey.show=()=>{};journey.status=()=>{};journey.persist=()=>{};journey.renderReview=()=>{};journey.renderAppearance=()=>{};journey.$=()=>({textContent:'',innerHTML:''});
 for(const trusted of [{approvals:{},confirmation:null},{approvals:{first:localApproval},confirmation:localConfirmation}]){
  journey.state={schema:S.schema,enabledInputs:['plot','compass'],answers:{},approvals:{first:{floorHash:'first-v1',signature:'foreign-studio'}},geometryHash:'home-v1',confirmation:{geometryHash:'home-v1',signature:'foreign-studio'}};
  journey.options.request=async()=>({valid:true,preparationId:'new-preparation',geometryHash:'home-v1',floors:[{id:'first',geometryHash:'first-v1'}],...trusted});await journey.prepare();
  assert.equal(JSON.stringify(journey.state.approvals),JSON.stringify(trusted.approvals));assert.equal(journey.state.confirmation,trusted.confirmation);assert.equal(journey.allApproved(),!!trusted.confirmation);assert.equal(journey.ready(),!!trusted.confirmation);
 }
 console.log('PASS editor navigation for 12 actions, all 3 floors, exact plans, unchanged drafts, measurements, missing-middle stair, legacy metadata and Compass render/focus');
 console.log('PASS prepare replaces foreign approval certificates and retains only server-verified approvals/confirmation');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
