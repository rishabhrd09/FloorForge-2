/* Authoritative clear-space plan editor. Geometry in mm; no optimisation or resizing on generation. */
'use strict';
window.FloorForgePlanEditor=class {
  constructor({registry,onEdit,onSelect,getEnvelope,getFacing=()=>180,getRoofAccess=()=>false,setRoofAccess=()=>{},validate,generate,suggestOpenings,prepare,getRevision=()=>0,getFloorHeight=()=>3150,upperConstraints,upperStarter}) {
    Object.assign(this,{registry,onEdit,onSelect,getEnvelope,getFacing,getRoofAccess,setRoofAccess,validateRequest:validate,generateRequest:generate,suggestOpenings,prepareRequest:prepare,getRevision,getFloorHeight,upperConstraints,upperStarter});
    this.plan=null;this.floor=0;this.selected=new Set();this.past=[];this.future=[];this.errors=[];this.tool='select';this.zoom=1;this.detail=false;this.showAllIssues=false;this.preparing=false;this.inputSerial=0;
    const $=id=>document.getElementById(id);this.$=$;this.svg=$('plan-canvas');
    $('plan-kind').innerHTML=Object.entries(registry).map(([k,v])=>`<option value="${k}">${v.label}</option>`).join('');
    $('plan-kind').value='bedroom';
    this.initPlacement();this.initSimple();
    $('plan-roof-access').onchange=()=>{this.setRoofAccess($('plan-roof-access').checked);this.render();};
    $('plan-add').onclick=()=>{this.tool='room';this.render();};$('plan-select').onclick=()=>{this.tool='select';this.render();};
    $('plan-wall').onclick=()=>{this.tool='wall';this.render();};$('plan-undo').onclick=()=>this.undo();$('plan-redo').onclick=()=>this.redo();
    $('plan-delete').onclick=()=>this.remove();$('plan-apply').onclick=()=>this.applyProperties();
    $('plan-opening-add').onclick=()=>this.addOpening();$('plan-wall-apply').onclick=()=>{const w=this.active.walls.find(w=>this.selected.has(w.id));if(w)this.change(()=>{w.a=[Number($('plan-wall-x0').value)*1000,Number($('plan-wall-y0').value)*1000];w.b=[Number($('plan-wall-x1').value)*1000,Number($('plan-wall-y1').value)*1000];});};$('plan-link-stair').onclick=()=>this.linkStairs();
    $('plan-swap').onclick=()=>this.swapRooms();$('plan-align').onclick=()=>this.align($('plan-alignment').value);$('plan-below').onchange=()=>this.render();
    $('plan-validate').onclick=()=>this.validate();$('plan-generate').onclick=()=>{if(!this.detail){this.prepare(true);return;}this.$('plan-dialog').close();this.generateRequest();};
    $('plan-show-3d').onclick=()=>{const selected=[...this.selected][0],id=this.active.openings.find(o=>o.id===selected)?.roomId||selected;this.onSelect(id,true);this.$('plan-dialog').close();};
    $('plan-zoom-in').onclick=()=>this.setZoom(this.zoom*1.25);$('plan-zoom-out').onclick=()=>this.setZoom(this.zoom/1.25);$('plan-fit').onclick=()=>this.setZoom(1);
    $('plan-thickness').onchange=()=>this.change(()=>{this.plan.wallThickness=Number($('plan-thickness').value);});
    this.svg.addEventListener('pointerdown',e=>this.pointerDown(e));this.svg.addEventListener('pointermove',e=>this.pointerMove(e));
    this.svg.addEventListener('pointerup',e=>this.pointerUp(e));this.svg.addEventListener('pointercancel',()=>this.cancelDrag());
    $('plan-dialog').addEventListener('input',()=>this.inputSerial++);
    $('plan-dialog').addEventListener('keydown',e=>{if(e.target.matches('input,textarea,select'))return;
      if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='z'){e.preventDefault();e.shiftKey?this.redo():this.undo();}
      if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='y'){e.preventDefault();this.redo();}
      if(e.key==='Delete'||e.key==='Backspace'){e.preventDefault();this.remove();}
      if(e.key==='Escape'&&this.drag){e.preventDefault();this.cancelDrag();}
    });
  }
  initSimple(){const $=this.$;
    for(const id of ['plan-add','plan-wall','plan-remove-floor','plan-suggest-openings'])$(id).classList.add('detail-only');
    for(const id of ['plan-smart-snap','plan-snap','plan-x','plan-y','plan-area','plan-room-kind','plan-thickness','plan-alignment'])$(id).closest('label,details')?.classList.add('detail-only');
    $('plan-alignment').closest('details').classList.add('detail-only');$('plan-thickness').closest('details').classList.add('detail-only');$('plan-opening-kind').closest('details').classList.add('detail-only');
    const more=$('plan-kind').closest('label');more.firstChild.textContent='More rooms ';$('plan-palette').before(more);more.classList.add('plan-more-rooms');
    $('plan-place').classList.add('detail-only');$('plan-linked-move-label').classList.add('detail-only');$('plan-link-stair').nextElementSibling.nextElementSibling.classList.add('detail-only');
    $('plan-arrange').onclick=()=>this.setDetail(false);$('plan-detail').onclick=()=>this.setDetail(true);
    $('plan-fit-yes').onclick=()=>this.acceptFit();$('plan-fit-no').onclick=()=>this.dismissFit();
    $('plan-upper-stairs').onclick=()=>this.proposeUpper(true);$('plan-upper-suggest').onclick=()=>this.proposeUpper(false);
    $('plan-copy-below').onclick=()=>this.copyFloorBelow(this.floor);$('plan-assist').onclick=()=>this.prepare(false);$('plan-more-issues').onclick=()=>{this.showAllIssues=!this.showAllIssues;this.renderIssues();};
    $('plan-storeys').onchange=()=>this.setFloorCount(Number($('plan-storeys').value));this.setDetail(false);
  }
  scheduleUpperGuidance(){
    const key=this.floor+':'+this.snapshot();if(this.upperKey===key)return;this.upperKey=key;if(this.upperData?.floor!==this.floor)this.upperData=null;
    clearTimeout(this.upperTimer);this.$('plan-upper-help').hidden=this.floor===0;
    if(this.floor===0||!this.upperConstraints)return;
    this.$('plan-upper-issues').textContent='Reading the floor below…';
    this.upperTimer=setTimeout(async()=>{try{const result=await this.upperConstraints(this.floor);if(this.upperKey!==key)return;this.upperData=result;this.render();
      this.$('plan-upper-issues').replaceChildren();for(const issue of result.issues){const b=document.createElement('button');b.className='upper-issue';b.type='button';b.textContent=issue.message;b.onclick=()=>{this.floor=issue.floor;this.selected=new Set(issue.ids||[issue.id]);this.render();};this.$('plan-upper-issues').append(b);}
      if(!result.issues.length)this.$('plan-upper-issues').textContent='The placement fits the footprint below. Smart fit checks access and openings.';
    }catch(e){if(this.upperKey===key)this.$('plan-upper-issues').textContent=e.message;}},200);
  }
  async proposeUpper(stairsOnly){
    if(this.preparing||this.fitProposal||!this.upperStarter)return;
    const before=this.snapshot(),revision=this.getRevision(),inputSerial=this.inputSerial;this.preparing=true;this.renderSimple();
    try{const result=await this.upperStarter(this.floor,stairsOnly);
      if(before!==this.snapshot()||revision!==this.getRevision()||inputSerial!==this.inputSerial)return;
      this.fitProposal={before,revision,inputSerial,result,preview:false};this.$('plan-fit-choice').hidden=false;
      this.$('plan-fit-summary').textContent=stairsOnly?'Continue the aligned staircase? The lower floor stays unchanged. Review the outline, then Yes or No.':'Use this suggested upper floor? It follows the rooms below and replaces only this upper layout. Your lower floor stays unchanged. Yes applies it; Undo restores the previous upper floor.';
      this.$('plan-fit-changes').replaceChildren();for(const c of result.changes){const li=document.createElement('li');li.textContent=c.message;this.$('plan-fit-changes').append(li);}this.render();
    }catch(e){this.presentErrors(e.data?.details?.errors||[{message:e.message}],e.message);}
    finally{this.preparing=false;this.renderSimple();}
  }
  setDetail(on){this.detail=on;this.$('plan-dialog').dataset.detail=String(on);this.tool='select';this.ghost=null;if(!on)this.$('plan-smart-snap').checked=true;if(this.plan)this.render();}
  renderSimple(){const $=this.$;
    $('plan-arrange').classList.toggle('active',!this.detail);$('plan-detail').classList.toggle('active',this.detail);
    $('plan-arrange').setAttribute('aria-pressed',String(!this.detail));$('plan-detail').setAttribute('aria-pressed',String(this.detail));
    $('plan-empty-actions').hidden=this.active.rooms.length>0||this.floor===0||!this.plan.floors[this.floor-1]?.rooms.length;
    $('plan-generate').textContent=this.detail?'Preview this plan ↗':'Fit & preview 3D ↗';$('plan-storeys').value=String(this.plan.floors.length);
    $('plan-mode-help').textContent=this.detail?'Exact sizes, wall tools and opening positions. Changes stay as you specify.':'Place rooms roughly. Smart fit suggests room sizes, walls and openings. You choose Yes or No.';
    for(const b of $('plan-palette').children)b.classList.toggle('detail-only',!['bedroom','living','drawing-room','kitchen','bathroom','dining','stair','terrace'].includes(b.dataset.kind));
    for(const id of ['plan-new-width','plan-new-depth'])$(id).closest('label').hidden=!this.detail&&this.tool!=='place';
    $('plan-assist').textContent=this.detail?'Help with walls & openings':'Smart fit rooms';$('plan-assist').disabled=this.preparing||!!this.fitProposal;$('plan-generate').disabled=this.preparing||!!this.fitProposal;
  }
  friendlyIssue(e){const messages={
    WALL_CLEARANCE:'Smart fit can adjust these rooms and make space for their shared wall.',
    EMPTY_FLOOR:'This floor has no rooms yet. Copy the floor below to start, or remove unused top floors.',
    UNLINKED_STAIR:'Connect this staircase to the matching stairs above, or enable access to the roof.',
    STAIR_FIT:'This staircase is too small for comfortable steps and landings. Use the suggested size, then adjust the rooms around it.',
    UNREACHABLE:'This room needs a connected route from the entrance. Try help with openings, or connect it to a hall.',
    NO_ENTRY:'The home needs an entrance. Let us suggest doors and windows.',
    NO_EXTERNAL_WINDOW:'This room needs a window to outside. Try help with openings; if it is surrounded by rooms, move it to an outside edge.',
    UNSUPPORTED_FLOOR:'Part of this floor has no floor underneath it. Align it with the floor below.',
    STAIR_ALIGNMENT:'The stairs need the same position on each connected floor.',
    BEDROOM_THROUGH_ROUTE:'Another room can only be reached through this bedroom. Connect it to a hall or living area.',
    DRYING_DRAIN:'A drying room needs drainage. Select the room and confirm its drainage provision.'};
    return messages[e.code]||e.message||'Select this part of the plan to refine it.';
  }
  issueRoom(e){const ids=e.ids||[e.id],core=this.plan.stairs.find(s=>s.id===e.id);return this.plan.floors.flatMap(f=>f.rooms).find(r=>ids.includes(r.id)||core?.roomIds.includes(r.id));}
  addIssueActions(row,e,room){const add=(text,fn)=>{const b=document.createElement('button');b.type='button';b.className='issue-fix';b.textContent=text;b.onclick=fn;row.append(b);};
    if(['WALL_CLEARANCE','SPACE_OVERLAP','ROOM_MINIMUM','WALL_SETBACK','NO_ENTRY','NO_EXTERNAL_WINDOW','UNREACHABLE'].includes(e.code))add('Help me fix this',()=>this.prepare(false));
    if(e.code==='EMPTY_FLOOR'){
      if(e.floor>0&&this.plan.floors[e.floor-1]?.rooms.length)add('Copy floor below',()=>this.copyFloorBelow(e.floor));
      const count=this.plan.floors.reduce((n,f,i)=>f.rooms.length?i+1:n,0);if(count&&count<this.plan.floors.length)add(`Use ${count===1?'Ground only':'G+'+(count-1)}`,()=>this.setFloorCount(count));
    }
    room=room||this.issueRoom(e);
    if(e.code==='UNLINKED_STAIR'&&room)add('Connect stairs',()=>{this.floor=this.plan.floors.findIndex(f=>f.rooms.includes(room));this.selected=new Set([room.id]);this.linkStairs();});
    if(e.code==='STAIR_FIT'&&room){const [w,d]=this.preset('stair');add(`Use ${w/1000} × ${d/1000} m`,()=>this.change(()=>{const [x,y]=this.bounds(room);room.polygon=[[x,y],[x+w,y],[x+w,y+d],[x,y+d]];this.floor=this.plan.floors.findIndex(f=>f.rooms.includes(room));this.selected=new Set([room.id]);}));}
  }
  copyFloorBelow(floor){if(floor<1||this.plan.floors[floor].rooms.length)return;this.change(()=>{
    const source=this.clone(this.plan.floors[floor-1]),target=this.plan.floors[floor],ids=new Map();
    for(const r of source.rooms){const id=this.uid();ids.set(r.id,id);r.id=id;}for(const w of source.walls)w.id=this.uid('wall');
    source.openings=source.openings.filter(o=>o.kind!=='entry').map(o=>({...o,id:this.uid('opening'),roomId:ids.get(o.roomId)}));
    Object.assign(target,{rooms:source.rooms,walls:source.walls,openings:source.openings});this.floor=floor;this.selected.clear();
    for(const r of source.rooms.filter(r=>r.kind==='stair')){const previous=[...ids].find(([,id])=>id===r.id)[0],core=this.plan.stairs.find(s=>s.roomIds.at(-1)===previous);if(core)core.roomIds.push(r.id);}
  });this.$('plan-validation').textContent='Copied the floor below. Move or resize its rooms to make this floor yours. Undo restores the empty floor.';}
  snapRoomEdge(next,index,room){if(!this.$('plan-smart-snap').checked)return next[index];const [W]=this.getEnvelope(),threshold=Math.min(180,Math.max(60,W/55)),axis=index%2,targets=[];
    for(const q of this.active.rooms){if(q.id===room.id)continue;const b=this.bounds(q),other=1-axis;if(Math.min(next[other+2],b[other+2])-Math.max(next[other],b[other])<=0)continue;
      const gap=this.registry[room.kind]?.enclosed&&this.registry[q.kind]?.enclosed?this.plan.wallThickness:0;
      targets.push(index<2?b[axis+2]+gap:b[axis]-gap);
    }
    const near=targets.sort((a,b)=>Math.abs(a-next[index])-Math.abs(b-next[index]))[0];return near!=null&&Math.abs(near-next[index])<=threshold?near:next[index];
  }
  async prepareExact(preview=false){if(this.preparing)return;const before=this.snapshot(),revision=this.getRevision(),inputSerial=this.inputSerial;this.preparing=true;this.renderSimple();this.$('plan-validation').textContent='Preparing wall spacing, doors, windows and stair connections…';
    try{const result=await this.prepareRequest(false);if(before!==this.snapshot()||revision!==this.getRevision()||inputSerial!==this.inputSerial){this.$('plan-validation').textContent='You changed the draft while we checked it. Prepare again to use your latest edits.';return;}
      this.change(()=>{this.plan=result.customPlan;});this.presentErrors(result.errors||[],result.message);
      const changes=this.$('plan-assist-changes');changes.hidden=!result.changes.length;changes.querySelector('ul').replaceChildren();for(const c of result.changes){const li=document.createElement('li');li.textContent=c.message;changes.querySelector('ul').append(li);}
      if(result.changes.length)this.$('plan-validation').textContent=result.valid?'Prepared. All adjustments can be undone.':'Wall and opening help applied where possible. Finish the highlighted part next.';
      if(preview&&result.valid){this.preparedGeneration=true;this.$('plan-dialog').close();await this.generateRequest();}
    }catch(e){this.presentErrors(e.data?.details?.errors||[{message:e.message}],e.message);}
    finally{this.preparing=false;this.renderSimple();}
  }
  dismissFit(){this.fitProposal=null;this.$('plan-fit-choice').hidden=true;this.svg.querySelectorAll('.plan-fit-outline').forEach(n=>n.remove());this.renderSimple();this.$('plan-validation').textContent='Your sketch is unchanged. Keep placing rooms, or use Fine-tune to draw walls yourself.';}
  async acceptFit(){const p=this.fitProposal;if(!p)return;
    if(p.before!==this.snapshot()||p.revision!==this.getRevision()||p.inputSerial!==this.inputSerial){this.dismissFit();this.$('plan-validation').textContent='Your sketch changed. Run Smart fit again for the latest version.';return;}
    this.fitProposal=null;this.$('plan-fit-choice').hidden=true;const linkedMove=this.$('plan-linked-move').checked;this.$('plan-linked-move').checked=false;try{this.change(()=>{this.plan=p.result.customPlan;});}finally{this.$('plan-linked-move').checked=linkedMove;}this.presentErrors(p.result.errors||[],p.result.message);
    const changes=this.$('plan-assist-changes');changes.hidden=!p.result.changes.length;changes.querySelector('ul').replaceChildren();for(const c of p.result.changes){const li=document.createElement('li');li.textContent=c.message;changes.querySelector('ul').append(li);}
    this.$('plan-validation').textContent=p.result.valid?'Fit accepted. Undo restores your sketch; Fine-tune lets you refine exact sizes.':'Fit accepted. Review the remaining highlighted choice before previewing.';
    if(p.preview&&p.result.valid){this.preparedGeneration=true;this.$('plan-dialog').close();await this.generateRequest();}
  }
  async prepare(preview=false){if(this.detail)return this.prepareExact(preview);if(this.preparing||this.fitProposal)return;
    const before=this.snapshot(),revision=this.getRevision(),inputSerial=this.inputSerial;this.preparing=true;this.renderSimple();this.$('plan-validation').textContent='Finding a fit for your room positions…';
    try{const result=await this.prepareRequest(true);
      if(before!==this.snapshot()||revision!==this.getRevision()||inputSerial!==this.inputSerial){this.$('plan-validation').textContent='You changed the draft while we checked it. Run Smart fit again for your latest sketch.';return;}
      if(!result.changes.length&&!result.valid){this.presentErrors(result.errors||[],result.message);return;}
      this.fitProposal={before,revision,inputSerial,result,preview};this.$('plan-fit-choice').hidden=false;this.$('plan-fit-choice').querySelector('details').open=false;
      this.$('plan-fit-summary').textContent=result.valid?'Rooms stay near your chosen positions. The suggested sizes, walls, doors and windows are ready. Nothing changes until you say Yes.':`This fit handles room sizes and wall spacing. ${result.errors.length} access or floor choice(s) still need attention. Nothing changes until you say Yes.`;
      this.$('plan-fit-changes').replaceChildren();for(const c of result.changes){const li=document.createElement('li');li.textContent=c.message;this.$('plan-fit-changes').append(li);}
      this.$('plan-validation').textContent='Dashed outlines show the suggestion. Your sketch is still saved.';this.render();
    }catch(e){this.presentErrors(e.data?.details?.errors||[{message:e.message}],e.message);}
    finally{this.preparing=false;this.renderSimple();}
  }
  uid(prefix='room'){return prefix+'-'+crypto.randomUUID().slice(0,18);}
  clone(x){return JSON.parse(JSON.stringify(x));}
  fresh(n){return {schema:'floorforge.custom-plan/1',units:'mm',wallThickness:150,floors:Array.from({length:n},(_,f)=>({id:'floor-'+f,rooms:[],walls:[],openings:[]})),stairs:[]};}
  load(plan,n){this.fitProposal=null;this.$('plan-fit-choice').hidden=true;this.plan=this.clone(plan||this.fresh(n));this.floor=Math.min(this.floor,this.plan.floors.length-1);this.selected.clear();this.past=[];this.future=[];this.errors=[];this.render();}
  ensureFloors(n){if(!this.plan)this.plan=this.fresh(n);while(this.plan.floors.length<n)this.plan.floors.push({id:'floor-'+this.plan.floors.length,rooms:[],walls:[],openings:[]});this.render();}
  setFloorCount(n){
    if(!this.plan){this.load(null,n);return;}if(this.plan.floors.length===n)return;
    this.change(()=>{while(this.plan.floors.length<n)this.plan.floors.push({id:'floor-'+this.plan.floors.length,rooms:[],walls:[],openings:[]});
      this.plan.floors=this.plan.floors.slice(0,n);const ids=new Set(this.plan.floors.flatMap(f=>f.rooms).map(r=>r.id));
      this.plan.stairs=this.plan.stairs.map(s=>({...s,roomIds:s.roomIds.filter(id=>ids.has(id))})).filter(s=>s.roomIds.length>1||(s.roomIds.length===1&&this.getRoofAccess()));
      this.floor=Math.min(this.floor,n-1);this.selected.clear();});
    this.$('plan-validation').textContent=`${n===1?'Ground only':'G+'+(n-1)} · ${n} occupied floor${n===1?'':'s'}. Roof access does not add another occupied floor. Undo restores removed rooms.`;
  }
  swapRooms(){const rooms=this.active.rooms.filter(r=>this.selected.has(r.id));if(rooms.length!==2)return;
    if(rooms.some(r=>r.kind==='stair')){this.$('plan-validation').textContent='Move a linked stair core with its counterparts; room swaps cannot break its alignment.';return;}
    this.change(()=>{const [a,b]=rooms,old=this.clone(a.polygon);a.polygon=this.clone(b.polygon);b.polygon=old;});
    this.$('plan-validation').textContent='Room positions swapped. Each room uses its destination shape and size. Review its openings and Validate plan; Undo restores the swap.';
  }
  snapshot(){return JSON.stringify(this.plan);}
  commit(before){if(before===this.snapshot())return;this.fitProposal=null;this.$('plan-fit-choice').hidden=true;this.showAllIssues=false;this.syncLinkedStairs(JSON.parse(before));this.past.push(before);if(this.past.length>100)this.past.shift();this.future=[];this.errors=[];this.onEdit();this.render();this.$('plan-assist-changes').hidden=true;this.$('plan-validation').textContent='Saved. Keep arranging rooms, or prepare your 3D preview.';}
  change(fn){const before=this.snapshot();fn();this.commit(before);}
  syncLinkedStairs(before){
    if(!this.$('plan-linked-move').checked)return;
    const old=new Map(before.floors.flatMap(fl=>fl.rooms).map(r=>[r.id,r]));
    const now=new Map(this.plan.floors.flatMap(fl=>fl.rooms).map(r=>[r.id,r]));
    for(const core of this.plan.stairs){const changed=core.roomIds.filter(id=>now.has(id)&&old.has(id)&&JSON.stringify(now.get(id).polygon)!==JSON.stringify(old.get(id).polygon));
      if(changed.length!==1)continue;
      const source=now.get(changed[0]);for(const id of core.roomIds)if(now.has(id)&&id!==source.id)now.get(id).polygon=this.clone(source.polygon);
    }
  }
  undo(){if(!this.past.length)return;this.future.push(this.snapshot());this.plan=JSON.parse(this.past.pop());this.restoreHistorySelection();this.onEdit();this.render();}
  redo(){if(!this.future.length)return;this.past.push(this.snapshot());this.plan=JSON.parse(this.future.pop());this.restoreHistorySelection();this.onEdit();this.render();}
  restoreHistorySelection(){const objects=this.plan.floors.flatMap(fl=>[...fl.rooms,...fl.walls,...fl.openings]);this.selected=new Set([...this.selected].filter(id=>objects.some(o=>o.id===id)));this.errors=[];this.tool='select';this.ghost=null;}
  get active(){return this.plan.floors[this.floor];}
  bounds(r){const xs=r.polygon.map(p=>p[0]),ys=r.polygon.map(p=>p[1]);return [Math.min(...xs),Math.min(...ys),Math.max(...xs),Math.max(...ys)];}
  area(r){return Math.abs(r.polygon.reduce((a,p,i)=>{let q=r.polygon[(i+1)%r.polygon.length];return a+p[0]*q[1]-q[0]*p[1];},0))/2e6;}
  point(e){const pt=new DOMPoint(e.clientX,e.clientY).matrixTransform(this.svg.getScreenCTM().inverse());const [,D]=this.getEnvelope();return [pt.x,D-pt.y];}
  snap(value){let step=Number(this.$('plan-snap').value);return step?Math.round(value/step)*step:Math.round(value);}
  snappedPoint(e){return this.point(e).map(n=>this.snap(n));}
  movePoints(room,dx,dy){room.polygon=room.polygon.map(([x,y])=>[x+dx,y+dy]);}
  preset(kind){if(kind==='stair')return [2200,2100+(Math.ceil(this.getFloorHeight()/190/2)-1)*250];return ({bedroom:[3200,3200],living:[4200,3600],'drawing-room':[3000,3000],kitchen:[3000,2700],bathroom:[1500,2100],dining:[3000,3000],hall:[1200,3000],stair:[2200,4100],'stair-landing':[2200,1100],'drying-room':[1800,2100],terrace:[3500,3000],veranda:[3600,1800],'outer-lobby':[3000,1800],'inner-lobby':[1500,1800],courtyard:[2400,2400]})[kind]||[2400,2400];}
  initPlacement(){const $=this.$;const palette=$('plan-palette');
    for(const kind of ['bedroom','living','drawing-room','kitchen','bathroom','dining','hall','stair','terrace','veranda','outer-lobby','drying-room']){
      const b=document.createElement('button'),v=this.registry[kind],[w,d]=this.preset(kind);b.type='button';b.draggable=true;b.dataset.kind=kind;b.style.setProperty('--room-color',v.color);
      b.append(document.createTextNode(v.label));const small=document.createElement('small');small.textContent=`${w/1000} × ${d/1000} m`;b.append(small);b.onclick=()=>this.chooseRoom(kind);
      b.ondragstart=e=>{this.nativeDrag=true;this.chooseRoom(kind);e.dataTransfer.setData('application/x-floorforge-room',kind);e.dataTransfer.effectAllowed='copy';};b.ondragend=()=>{this.nativeDrag=false;this.ghost=null;this.drawGhost();};palette.append(b);
    }
    $('plan-kind').onchange=()=>this.chooseRoom($('plan-kind').value);$('plan-place').onclick=()=>{this.tool='place';this.render();};
    this.svg.ondragenter=e=>{if(e.dataTransfer.types.includes('application/x-floorforge-room'))e.preventDefault();};
    // Keep the drop target attached throughout native HTML drag events. Rebuilding the SVG
    // under the pointer cancels drop delivery in browsers even though the preview still moves.
    this.svg.ondragover=e=>{if(e.dataTransfer.types.includes('application/x-floorforge-room')){e.preventDefault();e.dataTransfer.dropEffect='copy';this.ghost=this.placementAt(this.point(e));this.drawGhost();}};
    this.svg.ondragleave=e=>{if(!this.svg.contains(e.relatedTarget)){this.ghost=null;this.drawGhost();}};this.svg.ondrop=e=>{const kind=e.dataTransfer.getData('application/x-floorforge-room');if(!this.registry[kind])return;e.preventDefault();this.nativeDrag=false;$('plan-kind').value=kind;this.placeRoom(this.point(e));};
    $('plan-suggest-openings').onclick=async()=>{const snapshot=this.snapshot();$('plan-suggest-openings').disabled=true;$('plan-placement-note').textContent='Checking actual walls for door and window positions…';try{const result=await this.suggestOpenings();if(snapshot!==this.snapshot()){$('plan-placement-note').textContent='Draft changed. Request suggestions again.';return;}this.change(()=>{this.plan=result.customPlan;});$('plan-placement-note').textContent=result.message;await this.validate();}catch(e){this.presentErrors(e.data?.details?.errors||[],e.message);}finally{$('plan-suggest-openings').disabled=false;}};
  }
  chooseRoom(kind){this.$('plan-kind').value=kind;const [w,d]=this.preset(kind);this.$('plan-new-width').value=w/1000;this.$('plan-new-depth').value=d/1000;this.tool='place';this.ghost=null;this.render();}
  drawGhost(){let node=this.svg.querySelector('#plan-ghost-preview');if(!this.ghost){node?.remove();return;}if(!node){node=document.createElementNS('http://www.w3.org/2000/svg','rect');node.id='plan-ghost-preview';this.svg.append(node);}const [x,y,w,h]=this.ghost,[,D]=this.getEnvelope();for(const [key,value] of Object.entries({x,y:D-y-h,width:w,height:h,fill:this.registry[this.$('plan-kind').value].color,'fill-opacity':.5,stroke:'#245d4c','stroke-width':35,'stroke-dasharray':'100 60','pointer-events':'none'}))node.setAttribute(key,String(value));}
  placementAt(point){const w=Number(this.$('plan-new-width').value)*1000,d=Number(this.$('plan-new-depth').value)*1000;return this.fitBounds([this.snap(point[0]-w/2),this.snap(point[1]-d/2),w,d],this.$('plan-kind').value,[]);}
  fitBounds([x,y,w,h],kind,ignore){const [W,D]=this.getEnvelope(),pad=this.registry[kind]?.enclosed?this.plan.wallThickness:0;
    if(this.$('plan-smart-snap').checked){const threshold=Math.min(180,Math.max(60,W/55));let xs=[],ys=[];
      for(const r of this.active.rooms){if(ignore.includes(r.id))continue;const [a,b,c,d]=this.bounds(r),gap=this.registry[kind]?.enclosed||this.registry[r.kind]?.enclosed?this.plan.wallThickness:0;
        if(y+h>b-threshold&&y<d+threshold)xs.push(a-w-gap,c+gap,a,c-w);
        if(x+w>a-threshold&&x<c+threshold)ys.push(b-h-gap,d+gap,b,d-h);
      }
      const nearest=(value,targets)=>targets.reduce((best,v)=>Math.abs(v-value)<Math.abs(best-value)?v:best,value+threshold);
      const sx=nearest(x,xs),sy=nearest(y,ys);if(Math.abs(sx-x)<threshold)x=sx;if(Math.abs(sy-y)<threshold)y=sy;
    }
    // A pointer move can translate, but never shrink a room. Oversize typed rooms stay visibly invalid.
    if(w<=W-2*pad)x=Math.max(pad,Math.min(W-pad-w,x));if(h<=D-2*pad)y=Math.max(pad,Math.min(D-pad-h,y));
    return [Math.round(x),Math.round(y),w,h];
  }
  placeRoom(point){const kind=this.$('plan-kind').value,[x,y,w,h]=this.placementAt(point);if(![x,y,w,h].every(Number.isFinite)||w<100||h<100)return;
    if(kind==='stair'&&!this.detail){const existing=this.active.rooms.find(r=>r.kind==='stair'&&(()=>{const [a,b,c,d]=this.bounds(r);return x<c&&x+w>a&&y<d&&y+h>b;})());if(existing){this.selected=new Set([existing.id]);this.tool='select';this.render();this.$('plan-placement-note').textContent='This staircase is already here. Move or resize it, or Continue stairs from below to align it.';return;}}
    const room={id:this.uid(),kind,name:this.registry[kind].label,polygon:[[x,y],[x+w,y],[x+w,y+h],[x,y+h]]};
    const issue=this.localIssues([room]).find(e=>e.id===room.id);
    if(issue&&this.detail){this.$('plan-placement-note').textContent=issue.message+' Choose a clear position or change the new room size.';return;}
    this.change(()=>{this.active.rooms.push(room);this.selected=new Set([room.id]);});this.tool='select';this.ghost=null;
    this.$('plan-placement-note').textContent=issue?'Placed in your chosen area. Smart fit can make room and add walls; you approve the suggestion.':`${room.name} added. Keep placing rooms, then choose Smart fit.`;this.render();
  }
  localIssues(extra=[]){if(!this.plan)return [];const [W,D]=this.getEnvelope(),issues=[];
    for(const [f,fl] of this.plan.floors.entries()){const rooms=[...fl.rooms,...(f===this.floor?extra:[])];for(let i=0;i<rooms.length;i++){const r=rooms[i],[x,y,x1,y1]=this.bounds(r),pad=this.registry[r.kind]?.enclosed?this.plan.wallThickness:0;
      const excess=[['left',pad-x],['front',pad-y],['right',x1+pad-W],['rear',y1+pad-D]].filter(([,n])=>n>.1);
      if(excess.length){const fix=x1-x<=W-2*pad&&y1-y<=D-2*pad?{action:'move',dx:Math.max(pad,Math.min(x,W-pad-(x1-x)))-x,dy:Math.max(pad,Math.min(y,D-pad-(y1-y)))-y}:undefined;
        issues.push({id:r.id,floor:f,code:'WALL_SETBACK',message:`${r.name} crosses the buildable boundary ${excess.map(([side,n])=>`${side} by ${Math.ceil(n)} mm`).join(', ')}${pad?' including its outer wall':''}.`,fix});}
      if(r.polygon.length!==4)continue;
      for(const q of rooms.slice(0,i)){if(q.polygon.length!==4||r.underStair===q.id||q.underStair===r.id)continue;const [a,b,c,d]=this.bounds(q),gap=this.registry[r.kind]?.enclosed&&this.registry[q.kind]?.enclosed?this.plan.wallThickness:0;
        if(Math.min(x1,c)-Math.max(x,a)>.1&&Math.min(y1,d)-Math.max(y,b)>.1)issues.push({id:r.id,ids:[r.id,q.id],floor:f,code:'SPACE_OVERLAP',message:`${r.name} overlaps ${q.name}.`});
        else if(gap&&Math.min(x1+gap,c)-Math.max(x-gap,a)>.1&&Math.min(y1+gap,d)-Math.max(y-gap,b)>.1)issues.push({id:r.id,ids:[r.id,q.id],floor:f,code:'WALL_CLEARANCE',message:`Leave ${gap} mm for the shared wall between ${r.name} and ${q.name}. Smart snap helps align it.`});
      }
    }}return issues;
  }
  presentErrors(errors,message){this.errors=errors;this.showAllIssues=false;this.$('plan-validation').textContent=this.detail?(message||'Select an issue to locate it on the plan.'):(errors.length?'Let’s finish this part before previewing.':message||'Your plan is ready.');this.render();}
  renderIssues(){const root=this.$('plan-errors');root.replaceChildren();const combined=[...this.errors,...(this.detail?this.localIssues():[])].filter((e,i,all)=>all.findIndex(q=>q.code===e.code&&q.id===e.id)===i);this.displayErrors=combined;
    const shown=this.detail||this.showAllIssues?combined:combined.slice(0,1);this.$('plan-more-issues').hidden=this.detail||combined.length<2;this.$('plan-more-issues').textContent=this.showAllIssues?'Show one at a time':`Show ${combined.length-1} other item${combined.length===2?'':'s'}`;
    for(const e of shown){const row=document.createElement('div');row.className='plan-issue';const b=document.createElement('button');b.type='button';const floor=e.floor==null?'Plan':['Ground','First','Second'][e.floor];const fl=this.plan.floors[e.floor??this.floor];const room=fl?.rooms.find(r=>r.id===e.id||r.id===fl.openings.find(o=>o.id===e.id)?.roomId);const names=e.names?.join(', ')||fl?.rooms.filter(r=>(e.ids||[]).includes(r.id)).map(r=>r.name).join(', ')||room?.name;b.textContent=this.detail?`${floor}${names?' · '+names:''} — ${e.message||e.code} [${e.code}]`:`${floor}${names?' · '+names:''}: ${this.friendlyIssue(e)}`;b.onclick=()=>{if(e.floor!=null)this.floor=e.floor;this.selected=new Set(e.ids||[e.id]);this.render();};row.append(b);this.addIssueActions(row,e,room);
      if(e.fix?.action==='move'&&room){const fix=document.createElement('button');fix.type='button';fix.className='issue-fix';fix.textContent='Move inside';fix.onclick=()=>this.change(()=>{this.movePoints(room,e.fix.dx,e.fix.dy);this.floor=e.floor;this.selected=new Set([room.id]);});row.append(fix);}root.append(row);
    }
  }
  pointerDown(e){if(e.button!==0||!this.plan)return;const target=e.target.closest('[data-id]');const point=this.snappedPoint(e);if(this.tool==='place'){this.placeRoom(this.point(e));e.preventDefault();return;}this.svg.setPointerCapture(e.pointerId);
    if(this.tool==='room'){const [W,D]=this.getEnvelope(),pad=this.registry[this.$('plan-kind').value]?.enclosed?this.plan.wallThickness:0;point[0]=Math.max(pad,Math.min(W-pad,point[0]));point[1]=Math.max(pad,Math.min(D-pad,point[1]));}
    if(this.tool!=='select'){this.drag={type:this.tool,point,current:point,before:this.snapshot(),id:e.pointerId};e.preventDefault();return;}
    if(!target){this.selected.clear();this.render();return;}
    const id=target.dataset.id;if(e.shiftKey){this.selected.has(id)?this.selected.delete(id):this.selected.add(id);this.render();return;}
    if(!this.selected.has(id))this.selected=new Set([id]);const opening=this.active.openings.find(o=>o.id===id);this.onSelect(opening?.roomId||id,false);
    this.drag={type:opening?'opening':target.dataset.handle?'resize':'move',handle:target.dataset.handle,id:e.pointerId,point,before:this.snapshot(),original:this.clone(this.active),selected:[...this.selected]};this.render();e.preventDefault();
  }
  pointerMove(e){if(this.nativeDrag)return;if(this.tool==='place'&&!this.drag){this.ghost=this.placementAt(this.point(e));this.render();return;}if(!this.drag||this.drag.id!==e.pointerId)return;const d=this.drag,p=this.snappedPoint(e);d.current=p;
    if(d.type==='room'||d.type==='wall'){if(d.type==='room'){const [W,D]=this.getEnvelope(),pad=this.registry[this.$('plan-kind').value]?.enclosed?this.plan.wallThickness:0;d.current=[Math.max(pad,Math.min(W-pad,p[0])),Math.max(pad,Math.min(D-pad,p[1]))];}this.render();return;}
    const dx=p[0]-d.point[0],dy=p[1]-d.point[1];
    if(d.type==='opening'){const o=this.active.openings.find(o=>d.selected.includes(o.id)),old=d.original.openings.find(q=>q.id===o?.id);if(o&&old)o.offset=Math.max(0,old.offset+(o.side==='front'||o.side==='rear'?dx:dy));this.render();return;}
    for(const id of d.selected){const original=d.original.rooms.find(r=>r.id===id),room=this.active.rooms.find(r=>r.id===id);
      if(room&&original){if(d.type==='move'){const [x,y,x1,y1]=this.bounds(original),[nx,ny]=this.fitBounds([x+dx,y+dy,x1-x,y1-y],room.kind,d.selected);room.polygon=original.polygon.map(([a,b])=>[a+nx-x,b+ny-y]);}
        else {const [x,y,x1,y1]=this.bounds(original);let next=[x,y,x1,y1];const index={left:0,front:1,right:2,rear:3}[d.handle];next[index]+=index%2?dy:dx;next[index]=this.snapRoomEdge(next,index,room);const [W,D]=this.getEnvelope(),pad=this.registry[room.kind]?.enclosed?this.plan.wallThickness:0;next[index]=Math.max(pad,Math.min(index%2?D-pad:W-pad,next[index]));if(next[2]-next[0]>=100&&next[3]-next[1]>=100)room.polygon=[[next[0],next[1]],[next[2],next[1]],[next[2],next[3]],[next[0],next[3]]];}}
      const ow=d.original.walls.find(w=>w.id===id),w=this.active.walls.find(w=>w.id===id);if(w&&ow){w.a=[ow.a[0]+dx,ow.a[1]+dy];w.b=[ow.b[0]+dx,ow.b[1]+dy];}
    }this.render();
  }
  pointerUp(e){if(!this.drag||this.drag.id!==e.pointerId)return;const d=this.drag;this.drag=null;
    if(d.type==='room'){let [x,y]=d.point,[a,b]=d.current;x=Math.min(x,a);y=Math.min(y,b);const w=Math.abs(d.current[0]-d.point[0]),h=Math.abs(d.current[1]-d.point[1]);
      if(w>=100&&h>=100){const kind=this.$('plan-kind').value,id=this.uid();this.active.rooms.push({id,kind,name:this.registry[kind].label,polygon:[[x,y],[x+w,y],[x+w,y+h],[x,y+h]],...(kind==='drying-room'?{drain:false}:{})});this.selected=new Set([id]);}}
    if(d.type==='wall'){let a=d.point,b=d.current;if(Math.abs(a[0]-b[0])>Math.abs(a[1]-b[1]))b=[b[0],a[1]];else b=[a[0],b[1]];if(Math.hypot(a[0]-b[0],a[1]-b[1])>=100){const id=this.uid('partition');this.active.walls.push({id,a,b});this.selected=new Set([id]);}}
    if(d.type==='opening'){const o=this.active.openings.find(o=>d.selected.includes(o.id));if(o?.id.startsWith('suggest-')){o.id=this.uid('opening');this.selected=new Set([o.id]);}}
    this.tool='select';this.commit(d.before);this.render();
  }
  cancelDrag(){if(this.drag){this.plan=JSON.parse(this.drag.before);this.drag=null;this.render();}}
  remove(){if(!this.selected.size)return;this.change(()=>{const ids=this.selected;this.active.rooms=this.active.rooms.filter(r=>!ids.has(r.id));this.active.walls=this.active.walls.filter(w=>!ids.has(w.id));this.active.openings=this.active.openings.filter(o=>!ids.has(o.id)&&!ids.has(o.roomId));this.plan.stairs=this.plan.stairs.filter(s=>!s.roomIds.some(id=>ids.has(id)));this.selected.clear();});}
  applyProperties(){const opening=this.active.openings.find(o=>this.selected.has(o.id));const r=this.active.rooms.find(r=>this.selected.has(r.id)||r.id===opening?.roomId);if(!r)return;
    const values=['x','y','width','depth'].map(k=>Number(this.$('plan-'+k).value)*1000);if(values.some(n=>!Number.isFinite(n))||values[2]<=0||values[3]<=0)return;
    const [x,y,w,h]=values.map(n=>Math.round(n));this.change(()=>{const [ox,oy,ox1,oy1]=this.bounds(r);r.polygon=r.polygon.map(([a,b])=>[Math.round(x+(a-ox)*w/(ox1-ox)),Math.round(y+(b-oy)*h/(oy1-oy))]);r.name=this.$('plan-name').value.trim()||this.registry[r.kind].label;r.kind=this.$('plan-room-kind').value;r.drain=this.$('plan-drain').checked;});
  }
  addOpening(){const old=this.active.openings.find(o=>this.selected.has(o.id));const r=this.active.rooms.find(r=>this.selected.has(r.id)||r.id===old?.roomId);if(!r)return;const kind=this.$('plan-opening-kind').value;const spec={id:old?.id&&!old.id.startsWith('suggest-')?old.id:this.uid('opening'),roomId:r.id,kind,side:this.$('plan-opening-side').value,
    offset:Math.round(Number(this.$('plan-opening-offset').value)*1000),width:Math.round(Number(this.$('plan-opening-width').value)*1000),
    height:Math.round(Number(this.$('plan-opening-height').value)*1000),sill:Math.round(Number(this.$('plan-opening-sill').value)*1000),hinge:this.$('plan-opening-hinge').value};
    if([spec.offset,spec.width,spec.height,spec.sill].some(n=>!Number.isFinite(n)))return;this.change(()=>{if(old)Object.assign(old,spec);else this.active.openings.push(spec);this.selected=new Set([spec.id]);});
  }
  linkStairs(){const r=this.active.rooms.find(r=>this.selected.has(r.id)&&r.kind==='stair');if(!r)return;
    this.change(()=>{const ids=[];for(const [f,fl] of this.plan.floors.entries()){let same=fl.rooms.find(q=>q.kind==='stair'&&JSON.stringify(q.polygon)===JSON.stringify(r.polygon));if(!same){same={...this.clone(r),id:this.uid('stair'),name:`Staircase · ${['Ground','First','Second'][f]}`};fl.rooms.push(same);}ids.push(same.id);}
      const existing=this.plan.stairs.find(s=>s.roomIds.includes(r.id));this.plan.stairs=this.plan.stairs.filter(s=>!s.roomIds.some(id=>ids.includes(id)));this.plan.stairs.push({flightWidth:1000,well:200,landing:1050,tread:250,...existing,id:existing?.id||this.uid('core'),roomIds:ids});});
  }
  align(mode){const rooms=this.active.rooms.filter(r=>this.selected.has(r.id));if(rooms.length<2)return;
    this.change(()=>{if(mode==='distribute-x'||mode==='distribute-y'){const axis=mode.endsWith('x')?0:1;rooms.sort((a,b)=>this.bounds(a)[axis]-this.bounds(b)[axis]);const first=this.bounds(rooms[0]),last=this.bounds(rooms.at(-1));const total=rooms.reduce((a,r)=>{const b=this.bounds(r);return a+b[axis+2]-b[axis];},0),gap=(last[axis+2]-first[axis]-total)/(rooms.length-1);let pos=first[axis];for(const r of rooms){const b=this.bounds(r);this.movePoints(r,axis?0:Math.round(pos-b[axis]),axis?Math.round(pos-b[axis]):0);pos+=b[axis+2]-b[axis]+gap;}}
      else{const base=this.bounds(rooms[0]);for(const r of rooms.slice(1)){const b=this.bounds(r);this.movePoints(r,mode==='left'?base[0]-b[0]:mode==='right'?base[2]-b[2]:0,mode==='front'?base[1]-b[1]:mode==='rear'?base[3]-b[3]:0);}}});
  }
  setZoom(z){this.zoom=Math.max(.5,Math.min(4,z));this.svg.style.width=(this.zoom*100)+'%';this.svg.style.height=(this.zoom*100)+'%';this.$('plan-fit').textContent=Math.round(this.zoom*100)+'%';}
  async validate(){this.$('plan-validation').textContent='Checking dimensions, access, stairs and open sky…';const snapshot=this.snapshot();try{const r=await this.validateRequest();if(snapshot!==this.snapshot())return;this.presentErrors(r.valid?[]:(r.details?.errors||[{code:r.code,message:r.message}]),r.valid?'Geometry passes. Ready to generate this revision.':r.message);}catch(e){if(snapshot===this.snapshot())this.presentErrors(e.data?.details?.errors||[{message:e.message}],e.message);}}
  openingPoints(o){const r=this.active.rooms.find(r=>r.id===o.roomId);if(!r)return null;const [x,y,x1,y1]=this.bounds(r),t=this.plan.wallThickness/2,d=o.offset,w=o.width;
    return o.side==='front'?[[x+d,y-t],[x+d+w,y-t]]:o.side==='rear'?[[x+d,y1+t],[x+d+w,y1+t]]:o.side==='left'?[[x-t,y+d],[x-t,y+d+w]]:[[x1+t,y+d],[x1+t,y+d+w]];}
  render(){this.$('plan-roof-access').checked=this.getRoofAccess();if(!this.plan)return;const $=this.$,[W,D]=this.getEnvelope();if(!(W>0&&D>0))return;const E=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    this.floor=Math.min(this.floor,this.plan.floors.length-1);this.scheduleUpperGuidance();this.renderSimple();this.renderIssues();for(const [id,mode] of [['plan-select','select'],['plan-add','room'],['plan-wall','wall'],['plan-place','place']])$(id).classList.toggle('active',this.tool===mode);for(const b of $('plan-palette').children)b.classList.toggle('active',this.tool==='place'&&b.dataset.kind===$('plan-kind').value);$('plan-floor-tabs').replaceChildren();this.plan.floors.forEach((fl,f)=>{const b=document.createElement('button');b.type='button';b.textContent=['Ground','First','Second'][f];b.className=f===this.floor?'active':'';b.onclick=()=>{this.floor=f;if(f>0)$('plan-below').checked=true;this.selected.clear();this.render();};$('plan-floor-tabs').append(b);});
    $('plan-swap').disabled=this.active.rooms.filter(r=>this.selected.has(r.id)).length!==2;$('plan-floor-summary').textContent=`${this.plan.floors.length===1?'Ground only':'G+'+(this.plan.floors.length-1)} · ${this.plan.floors.length} occupied floor${this.plan.floors.length===1?'':'s'}${this.getRoofAccess()?' + accessible roof terrace':''}`;$('plan-thickness').value=this.plan.wallThickness;$('plan-undo').disabled=!this.past.length;$('plan-redo').disabled=!this.future.length;
    $('plan-dimensions').textContent=`${(W/1000).toFixed(2)} × ${(D/1000).toFixed(2)} m buildable · clear room dimensions · ${this.detail?this.plan.wallThickness+' mm walls':'walls handled for you'} · front ${['N','NE','E','SE','S','SW','W','NW'][Math.round(this.getFacing()/45)%8]}`;
    $('plan-tool-state').textContent=this.tool==='place'?'Click the plan to place this room. The dashed shape previews its size.':this.tool==='room'?'Drag a rectangle. Boundary protection reserves outer wall space.':this.tool==='wall'?'Drag an orthogonal partition.':'Drag to move · edge handles resize rectangles · Shift-click for multiple selection';
    this.svg.setAttribute('viewBox',`-450 -450 ${W+900} ${D+900}`);
    const points=r=>r.polygon.map(([x,y])=>`${x},${D-y}`).join(' '),bad=id=>this.displayErrors.some(e=>e.id===id||e.ids?.includes(id));let html=`<defs><pattern id="metre-grid" width="1000" height="1000" patternUnits="userSpaceOnUse"><path d="M1000 0H0V1000" fill="none" stroke="#d6ded7" stroke-width="12"/></pattern></defs><rect width="${W}" height="${D}" fill="#f9faf6" stroke="#aab5a9" stroke-width="20"/><rect width="${W}" height="${D}" fill="url(#metre-grid)"/>`;
    html+=`<rect x="${this.plan.wallThickness}" y="${this.plan.wallThickness}" width="${Math.max(0,W-2*this.plan.wallThickness)}" height="${Math.max(0,D-2*this.plan.wallThickness)}" fill="none" stroke="#b18c58" stroke-width="12" stroke-dasharray="80 65"/>`;
    if(!this.active.rooms.length)html+=`<text x="${W/2}" y="${D/2}" text-anchor="middle" fill="#49624a" font-size="260">Place your first room here</text><text x="${W/2}" y="${D/2+420}" text-anchor="middle" fill="#73806a" font-size="180">Choose a room above, then click or drag it onto the plan.</text>`;
    if(this.floor>0&&this.upperData){const path=region=>[region.polygon,...region.holes].map(ring=>'M'+ring.map(([x,y])=>x+','+(D-y)).join('L')+'Z').join('');
      for(const region of this.upperData.supported)html+=`<path class="upper-support" d="${path(region)}" fill="#cfdfc8" fill-rule="evenodd" stroke="#71966c" stroke-width="25" opacity=".65" pointer-events="none"/>`;
      for(const r of this.upperData.openSky)html+=`<polygon class="upper-open-sky" points="${points(r)}" fill="#e8b8a5" opacity=".65" pointer-events="none"/>`;
    }
    const atriums=this.active.rooms.filter(r=>r.kind==='void'&&r.openToBelow);
    for(const r of this.active.rooms)if(this.registry[r.kind]?.enclosed){
      for(let i=0;i<r.polygon.length;i++){
        const a=r.polygon[i],b=r.polygon[(i+1)%r.polygon.length],axis=a[0]===b[0]?1:0,normal=1-axis;
        let spans=[[Math.min(a[axis],b[axis]),Math.max(a[axis],b[axis])]];
        for(const v of atriums)for(let j=0;j<v.polygon.length;j++){
          const c=v.polygon[j],d=v.polygon[(j+1)%v.polygon.length];
          if(c[normal]!==d[normal]||Math.abs(c[normal]-a[normal])>this.plan.wallThickness+.1)continue;
          const lo=Math.min(c[axis],d[axis]),hi=Math.max(c[axis],d[axis]);
          spans=spans.flatMap(([l,h])=>hi<=l||lo>=h?[[l,h]]:[[l,Math.min(h,lo)],[Math.max(l,hi),h]].filter(([x,y])=>y>x));
        }
        for(const [lo,hi] of spans){const c=[...a],d=[...b];c[axis]=lo;d[axis]=hi;html+=`<line x1="${c[0]}" y1="${D-c[1]}" x2="${d[0]}" y2="${D-d[1]}" stroke="#92988a" stroke-width="${this.plan.wallThickness*2}"/>`;}
      }
    }
    const labelBox=r=>{
      if(r.polygon.length===4)return this.bounds(r);
      const ys=[...new Set(r.polygon.map(p=>p[1]))].sort((a,b)=>a-b);let best=null;
      for(let j=0;j<ys.length-1;j++){const y=(ys[j]+ys[j+1])/2,xs=[];
        for(let i=0;i<r.polygon.length;i++){const a=r.polygon[i],b=r.polygon[(i+1)%r.polygon.length];if((a[1]>y)!==(b[1]>y))xs.push(a[0]+(y-a[1])*(b[0]-a[0])/(b[1]-a[1]));}
        xs.sort((a,b)=>a-b);for(let i=0;i+1<xs.length;i+=2){const score=(xs[i+1]-xs[i])*(ys[j+1]-ys[j]);if(!best||score>best.score)best={score,box:[xs[i],ys[j],xs[i+1],ys[j+1]]};}
      }return best?.box||this.bounds(r);
    };
    for(const r of [...this.active.rooms].sort((a,b)=>Number(!!a.underStair)-Number(!!b.underStair))){const [x,y,x1,y1]=this.bounds(r),[lx,ly,lx1,ly1]=labelBox(r),sel=this.selected.has(r.id),color=this.registry[r.kind]?.color||'#ddd';
      html+=`<g data-id="${E(r.id)}" class="plan-room"><polygon points="${points(r)}" fill="${color}" fill-opacity="1" stroke="${bad(r.id)?'#bf453a':sel?'#245d4c':'#818d7a'}" stroke-width="${sel?40:18}"/><text x="${(lx+lx1)/2}" y="${D-(ly+ly1)/2-70}" text-anchor="middle" style="font-size:${Math.min(180,(x1-x)/Math.max(7,r.name.length*.56))}px">${E(r.name)}</text><text x="${(lx+lx1)/2}" y="${D-(ly+ly1)/2+180}" text-anchor="middle" style="font-size:${Math.min(140,(x1-x)/20)}px">${((x1-x)/1000).toFixed(2)} × ${((y1-y)/1000).toFixed(2)} m · ${this.area(r).toFixed(2)} m²</text></g>`;
      if(sel&&r.polygon.length===4)for(const [side,px,py] of [['front',(x+x1)/2,y],['rear',(x+x1)/2,y1],['left',x,(y+y1)/2],['right',x1,(y+y1)/2]])html+=`<rect data-id="${E(r.id)}" data-handle="${side}" x="${px-70}" y="${D-py-70}" width="140" height="140" rx="25" fill="#245d4c" stroke="white" stroke-width="12"/>`;
    }
    if($('plan-below').checked&&this.floor>0)for(const r of this.plan.floors[this.floor-1].rooms)html+=`<polygon points="${points(r)}" fill="none" stroke="#7089aa" stroke-width="30" stroke-dasharray="100 80" opacity=".35"/>`;
    if(this.floor>0&&this.upperData)for(const r of this.upperData.stairs){const [x,y,x1,y1]=this.bounds(r);html+=`<polygon class="upper-stair-guide" points="${points(r)}" fill="none" stroke="#3979b3" stroke-width="55" stroke-dasharray="90 60" pointer-events="none"/><text x="${(x+x1)/2}" y="${D-y+180}" text-anchor="middle" fill="#3979b3" font-size="140" pointer-events="none">Stairs from below</text>`;}
    for(const w of this.active.walls)html+=`<line data-id="${E(w.id)}" x1="${w.a[0]}" y1="${D-w.a[1]}" x2="${w.b[0]}" y2="${D-w.b[1]}" stroke="${this.selected.has(w.id)?'#245d4c':'#60645b'}" stroke-width="${this.plan.wallThickness}"/>`;
    for(const o of this.active.openings){const p=this.openingPoints(o);if(p)html+=`<g data-id="${E(o.id)}"><line x1="${p[0][0]}" y1="${D-p[0][1]}" x2="${p[1][0]}" y2="${D-p[1][1]}" stroke="${bad(o.id)?'#bf453a':o.kind==='window'?'#5799bd':'#fdfbf0'}" stroke-width="${o.kind==='cased'?this.plan.wallThickness+4:100}"/><line x1="${p[0][0]}" y1="${D-p[0][1]}" x2="${p[1][0]}" y2="${D-p[1][1]}" stroke="#23504d" stroke-width="15"/></g>`;}
    for(const o of this.active.openings.filter(o=>o.servingCounter)){const p=this.openingPoints(o);if(!p)continue;const end=[(p[0][0]+p[1][0])/2,(p[0][1]+p[1][1])/2];html+=`<g data-id="${E(o.id)}"><title>Serving counter · 0.95 m high · half opening remains clear</title><line x1="${p[0][0]}" y1="${D-p[0][1]}" x2="${end[0]}" y2="${D-end[1]}" stroke="#b79a73" stroke-width="400"/></g>`;}
    if(this.drag&&['room','wall'].includes(this.drag.type)){const a=this.drag.point,b=this.drag.current;html+=`<rect x="${Math.min(a[0],b[0])}" y="${D-Math.max(a[1],b[1])}" width="${Math.abs(a[0]-b[0])}" height="${Math.abs(a[1]-b[1])}" fill="#d3e4d6" opacity=".6" stroke="#245d4c" stroke-width="30"/>`;}
    if(this.tool==='place'&&this.ghost){const [x,y,w,h]=this.ghost;html+=`<rect id="plan-ghost-preview" x="${x}" y="${D-y-h}" width="${w}" height="${h}" fill="${this.registry[$('plan-kind').value].color}" fill-opacity=".5" stroke="#245d4c" stroke-width="35" stroke-dasharray="100 60" pointer-events="none"/>`;}
    if(this.fitProposal)for(const r of this.fitProposal.result.customPlan.floors[this.floor].rooms)html+=`<polygon class="plan-fit-outline" points="${points(r)}" fill="none" stroke="#245d4c" stroke-width="35" stroke-dasharray="100 65" pointer-events="none"/>`;
    html+=`<text x="${W/2}" y="${D+320}" text-anchor="middle" fill="#547162" font-size="180">ROAD / FRONT · ${['NORTH','NORTHEAST','EAST','SOUTHEAST','SOUTH','SOUTHWEST','WEST','NORTHWEST'][Math.round(this.getFacing()/45)%8]}</text>`;this.svg.innerHTML=html;
    const selectedOpening=this.active.openings.find(o=>this.selected.has(o.id));const selectedWall=this.active.walls.find(w=>this.selected.has(w.id));$('plan-wall-properties').hidden=!selectedWall;if(selectedWall)for(const [id,v] of [['x0',selectedWall.a[0]],['y0',selectedWall.a[1]],['x1',selectedWall.b[0]],['y1',selectedWall.b[1]]])$('plan-wall-'+id).value=(v/1000).toFixed(3);
    const r=this.active.rooms.find(r=>this.selected.has(r.id)||r.id===selectedOpening?.roomId);$('plan-properties').hidden=!r;$('plan-no-selection').hidden=!!r;$('plan-delete').disabled=!this.selected.size;
    if(r){const spec=this.registry[r.kind];$('plan-room-help').textContent=r.kind==='drawing-room'?'Guest sitting room with sofa seating. Use Living for a combined family and guest lounge.':r.kind==='drying-room'?'Laundry drying/service room. Requires drainage and external ventilation.':this.detail?`Minimum screening: ${spec.minimum_area_m2||0} m² · ${(spec.minimum_width_mm||0)/1000} m narrow side. Clear dimensions exclude walls.`:'Drag a room edge to resize, or type its width and depth. Measurements are inside the walls.';$('plan-opening-add').textContent=selectedOpening?'Save opening':'Add opening';if(selectedOpening){for(const key of ['kind','side','hinge'])$('plan-opening-'+key).value=selectedOpening[key]||'start';for(const key of ['offset','width','height','sill'])$('plan-opening-'+key).value=((selectedOpening[key]??(key==='height'?2100:0))/1000).toFixed(3);}const [x,y,x1,y1]=this.bounds(r);$('plan-name').value=r.name;$('plan-room-kind').innerHTML=Object.entries(this.registry).map(([k,v])=>`<option value="${k}" ${r.kind===k?'selected':''}>${v.label}</option>`).join('');for(const [k,v] of [['x',x],['y',y],['width',x1-x],['depth',y1-y]])$('plan-'+k).value=this.detail?(v/1000).toFixed(3):String(Number((v/1000).toFixed(3)));$('plan-area').value=this.area(r).toFixed(3);$('plan-area').disabled=r.polygon.length!==4;$('plan-drain').checked=!!r.drain;$('plan-drain-field').hidden=r.kind!=='drying-room';$('plan-link-stair').hidden=r.kind!=='stair';$('plan-linked-move-label').hidden=r.kind!=='stair';$('plan-object-id').textContent=r.id;
      $('plan-area').onchange=()=>{const width=Number($('plan-width').value),area=Number($('plan-area').value);if(width>0&&area>0)$('plan-depth').value=(area/width).toFixed(3);};
      $('plan-opening-list').replaceChildren();for(const o of this.active.openings.filter(o=>o.roomId===r.id)){const row=document.createElement('div'),button=document.createElement('button');row.className='plan-opening-row';const edit=document.createElement('button');edit.type='button';edit.textContent=`${o.kind} · ${o.side} · ${(o.width/1000).toFixed(2)} m`;edit.onclick=()=>{this.selected=new Set([o.id]);this.render();};row.append(edit);button.type='button';button.textContent='Remove';button.onclick=()=>this.change(()=>{this.active.openings=this.active.openings.filter(q=>q.id!==o.id);});row.append(button);$('plan-opening-list').append(row);}}
    $('plan-room-list').replaceChildren();for(const room of this.active.rooms){const b=document.createElement('button');b.type='button';b.className=this.selected.has(room.id)?'active':'';b.textContent=room.name;b.dataset.invalid=String(bad(room.id));b.onclick=e=>{if(!e.shiftKey)this.selected.clear();this.selected.add(room.id);this.onSelect(room.id,false);this.render();};$('plan-room-list').append(b);}
  }
};
