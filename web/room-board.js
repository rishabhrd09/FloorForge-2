/* Spatial arrangement first; canonical rooms are created only after approval. */
'use strict';
class FloorForgeRoomBoard {
 constructor(options){
  this.options=options;this.board=null;this.active=false;this.floor=0;this.selected=null;this.targetSlot=null;this.history=[];this.pending=null;this.busy=false;
  this.names=['Ground','First','Second'];this.common=['bedroom','living','drawing-room','kitchen','bathroom','dining','stair','terrace'];
  this.allowed=Object.keys(options.registry).filter(k=>!['void','lift-shaft','stair-landing'].includes(k));
  this.el=id=>document.getElementById(id);this.clone=x=>structuredClone(x);
  this.label=k=>k==='drawing-room'?'Drawing room':k==='stair'?'Staircase':k==='terrace'?'Open terrace':options.registry[k]?.label||k.replaceAll('-',' ').replace(/^./,s=>s.toUpperCase());
  this.el('rb-palette').innerHTML=this.common.map(k=>`<button type="button" data-add="${k}" class="rb-add rb-${k}">${this.safe(this.label(k))}</button>`).join('');
  this.el('rb-more').innerHTML='<option value="">Choose a room…</option>'+this.allowed.filter(k=>!this.common.includes(k)).map(k=>`<option value="${k}">${this.safe(this.label(k))}</option>`).join('');
  this.el('rb-palette').onclick=e=>{if(this.dragged){this.dragged=false;return;}const b=e.target.closest('[data-add]');if(b)this.add(b.dataset.add);};
  this.el('rb-more').onchange=e=>{if(e.target.value)this.add(e.target.value);e.target.value='';};
  this.el('rb-close').onclick=()=>this.el('room-board-dialog').close();
  this.el('rb-undo').onclick=()=>{if(this.history.length){this.board=this.history.pop();this.selected=null;this.changed();}};
  this.el('rb-remove').onclick=()=>this.remove();
  this.el('rb-build').onclick=()=>this.build();this.el('rb-back').onclick=()=>{this.pending=null;this.render();};
  this.el('rb-accept').onclick=()=>this.accept();
  this.el('rb-levels').onchange=e=>this.levels(Number(e.target.value));
  this.el('rb-roof').onchange=e=>{this.options.setRoof(e.target.checked);this.edit(()=>this.syncStairs());};
  this.el('rb-copy').onclick=()=>this.copyBelow();
  this.el('rb-example').onclick=()=>this.example();
  this.el('rb-details').onclick=()=>{this.active=false;this.options.onEdit();this.el('room-board-dialog').close();this.options.details();};
  this.el('rb-floors').onclick=e=>{const b=e.target.closest('[data-floor]');if(b){this.floor=Number(b.dataset.floor);this.selected=null;this.render();}};
  this.el('rb-board').onclick=e=>{if(this.dragged){this.dragged=false;return;}const b=e.target.closest('[data-slot]');if(b)this.tap(Number(b.dataset.slot));};
  this.el('rb-board').onkeydown=e=>{if(e.key==='Escape'){this.selected=null;this.render();}};
  this.bindDrag(this.el('rb-board'));this.bindDrag(this.el('rb-palette'));
 }
 safe(x){return String(x).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
 uid(){return 'room-'+crypto.randomUUID();}
 get rooms(){return this.board?.floors[this.floor]?.rooms||[];}
 slot(r){return r.row*2+r.col;}
 roomAt(n,f=this.floor){return this.board.floors[f].rooms.find(r=>this.slot(r)===n);}
 blocked(n,f=this.floor){return this.board.floors.slice(0,f).some(fl=>fl.rooms.some(r=>this.slot(r)===n&&['terrace','courtyard','drying-yard','balcony'].includes(r.kind)));}
 load(board,active=false){this.board=board?this.clone(board):null;this.active=active;this.history=[];this.floor=0;this.pending=null;this.selected=null;}
 open(){if(!this.board)this.importPlan(this.options.getPlan());this.floor=Math.min(this.floor,this.board.floors.length-1);this.el('room-board-dialog').showModal();this.render();}
 importPlan(plan){
  const n=plan?.floors?.length||this.options.getStoreys();this.board={version:1,floors:Array.from({length:n},()=>({rooms:[]}))};
  const [w,d]=this.options.getEnvelope();let skipped=0;
  (plan?.floors||[]).forEach((fl,f)=>{
   const seenStair=new Set();
   const candidates=fl.rooms.filter(r=>this.allowed.includes(r.kind)&&!['hall','inner-lobby'].includes(r.kind)&&!r.id.startsWith('board-passage-'));
   candidates.sort((a,b)=>(b.kind==='stair')-(a.kind==='stair'));
   for(const r of candidates){if(r.kind==='stair'&&seenStair.size)continue;if(r.kind==='stair')seenStair.add(r.id);
    if(this.board.floors[f].rooms.length>=8){skipped++;continue;}
    const x=r.polygon.reduce((s,p)=>s+p[0],0)/r.polygon.length/w,y=r.polygon.reduce((s,p)=>s+p[1],0)/r.polygon.length/d;
    const slots=Array.from({length:8},(_,i)=>i).filter(i=>!this.roomAt(i,f)).sort((a,b)=>Math.hypot((a%2+.5)/2-x,(Math.floor(a/2)+.5)/4-y)-Math.hypot((b%2+.5)/2-x,(Math.floor(b/2)+.5)/4-y));
    const s=slots[0];this.board.floors[f].rooms.push({id:r.id,kind:r.kind,name:r.name||this.label(r.kind),col:s%2,row:Math.floor(s/2)});
   }
  });
  this.syncStairs();
  this.importNote=skipped?`${skipped} extra rooms remain in your detailed drawing. This simple board holds eight spots per floor; your drawing is unchanged until you approve a new layout.`:'Your rooms are shown as rough positions. The detailed drawing stays saved until you approve a new layout.';
 }
 syncStairs(){
  if(!this.board)return;
  const all=this.board.floors.flatMap(fl=>fl.rooms),first=all.find(r=>r.kind==='stair');
  if(!first&&this.board.floors.length===1&&!this.options.getRoof())return;
  const free=Array.from({length:8},(_,i)=>i).find(i=>this.board.floors.every((fl,f)=>!this.roomAt(i,f)&&!this.blocked(i,f)));
  if(!first&&free===undefined)return;
  const target=first?this.slot(first):free;
  this.board.floors.forEach((fl,f)=>{
   const stairs=fl.rooms.filter(r=>r.kind==='stair');const stair=stairs[0];
   if(stair&&this.slot(stair)!==target){const other=this.roomAt(target,f);if(other){other.col=stair.col;other.row=stair.row;}stair.col=target%2;stair.row=Math.floor(target/2);}
   else if(!stair){const other=this.roomAt(target,f),empty=Array.from({length:8},(_,i)=>i).find(i=>!this.roomAt(i,f)&&!this.blocked(i,f));if(other&&empty===undefined)return;if(other){other.col=empty%2;other.row=Math.floor(empty/2);}fl.rooms.push({id:this.uid(),kind:'stair',name:'Staircase',col:target%2,row:Math.floor(target/2)});}
   for(const duplicate of stairs.slice(1))fl.rooms=fl.rooms.filter(r=>r!==duplicate);
  });
 }
 edit(fn){this.history.push(this.clone(this.board));if(this.history.length>40)this.history.shift();fn();this.changed();}
 changed(){this.active=true;this.pending=null;this.targetSlot=null;this.importNote='';this.options.onEdit();this.render();}
 message(s){this.el('rb-message').textContent=s;}
 add(kind,target){
  if(this.pending||this.busy)return;
  if(kind==='stair'&&this.rooms.some(r=>r.kind==='stair')){this.selected=this.rooms.find(r=>r.kind==='stair').id;this.render();this.message('One staircase connects all floors. Move its card to change the position.');return;}
  let n=target??this.targetSlot??Array.from({length:8},(_,i)=>i).find(i=>!this.roomAt(i)&&!this.blocked(i));
  if(n===undefined||this.roomAt(n)||this.blocked(n)){this.message('Choose an empty spot, or remove a room to make space.');return;}
  if(['terrace','courtyard','drying-yard','balcony'].includes(kind)&&this.board.floors.slice(this.floor+1).some(fl=>fl.rooms.some(r=>this.slot(r)===n))){this.message('Choose a spot with no room above for this open-air space.');return;}
  this.edit(()=>{const r={id:this.uid(),kind,name:this.label(kind),col:n%2,row:Math.floor(n/2)};this.rooms.push(r);this.selected=r.id;this.targetSlot=null;this.syncStairs();});
  this.message(`${this.label(kind)} added. Move it wherever you want on the board.`);
 }
 tap(n){const r=this.roomAt(n);if(this.selected){const chosen=this.rooms.find(r=>r.id===this.selected);if(chosen&&chosen!==r){this.move(chosen,n);return;}}this.selected=r?.id||null;this.targetSlot=r?null:n;this.render();}
 move(r,n){
  if(this.blocked(n)){this.message('This spot stays open above the outdoor space below. Choose another spot.');return;}
  const old=this.slot(r),other=this.roomAt(n);if(old===n)return;
  const changes=r.kind==='stair'||other?.kind==='stair'?this.board.floors.map((_,f)=>f):[this.floor];
  for(const f of changes){const a=this.roomAt(old,f),b=this.roomAt(n,f);
   if((a&&this.blocked(n,f))||(b&&this.blocked(old,f))){this.message('This swap would cover an open-air space below. Choose another spot.');return;}
   if([a,b].some(q=>q&&['terrace','courtyard','drying-yard','balcony'].includes(q.kind)&&this.board.floors.slice(f+1).some(fl=>fl.rooms.some(up=>this.slot(up)===(q===a?n:old))))){this.message('An outdoor space needs a clear spot above it. Choose another spot.');return;}
  }
  this.edit(()=>{for(const f of changes){const a=this.roomAt(old,f),b=this.roomAt(n,f);if(a){a.col=n%2;a.row=Math.floor(n/2);}if(b){b.col=old%2;b.row=Math.floor(old/2);}}this.selected=null;});
  this.message(changes.length>1?'Stairs and affected rooms moved together on each floor.':other?'Rooms swapped.':'Room moved.');
 }
 remove(){const r=this.rooms.find(r=>r.id===this.selected);if(!r)return;if(r.kind==='stair'&&(this.board.floors.length>1||this.options.getRoof())){this.message('This staircase connects your floors and roof. Drag it to move it.');return;}this.edit(()=>{this.board.floors[this.floor].rooms=this.rooms.filter(x=>x!==r);this.selected=null;});}
 levels(n){if(n<this.board.floors.length&&this.board.floors.slice(n).some(fl=>fl.rooms.some(r=>r.kind!=='stair'))&&!confirm('Remove the upper floor rooms? You can Undo this.')){this.render();return;}this.edit(()=>{while(this.board.floors.length<n)this.board.floors.push({rooms:[]});this.board.floors.length=n;this.floor=Math.min(this.floor,n-1);this.syncStairs();});}
 copyBelow(){if(!this.floor)return;if(this.rooms.some(r=>r.kind!=='stair')&&!confirm('Replace this floor with rooms from below? You can Undo this.'))return;this.edit(()=>{this.board.floors[this.floor].rooms=this.board.floors[this.floor-1].rooms.filter(r=>!['terrace','courtyard','drying-yard','balcony'].includes(r.kind)).map(r=>({...r,id:this.uid()}));this.selected=null;this.syncStairs();});}
 example(){this.edit(()=>{this.board={version:1,floors:[{rooms:[]},{rooms:[]}]};const kinds=[['kitchen','drawing-room','stair','living',null,'dining','bedroom','bedroom'],['bathroom','bedroom','stair','family',null,'terrace','bedroom','bedroom']];kinds.forEach((list,f)=>list.forEach((kind,n)=>{if(kind)this.board.floors[f].rooms.push({id:this.uid(),kind,name:this.label(kind),col:n%2,row:Math.floor(n/2)});}));this.floor=0;this.selected=null;});this.message('Sample arrangement ready. Build my layout to see it in 3D. Undo restores your rooms.');}
 bindDrag(element){
  let start=null,ghost=null;
  element.addEventListener('pointerdown',e=>{const source=e.target.closest('[data-room],[data-add]');if(!source||e.button!==0||this.pending||this.busy)return;start={x:e.clientX,y:e.clientY,id:source.dataset.room,kind:source.dataset.add,text:source.textContent,pointer:e.pointerId};source.setPointerCapture(e.pointerId);});
  element.addEventListener('pointermove',e=>{if(!start)return;if(!ghost&&Math.hypot(e.clientX-start.x,e.clientY-start.y)>10){ghost=document.createElement('div');ghost.className='rb-drag-ghost';ghost.textContent=start.text;this.el('room-board-dialog').append(ghost);}if(ghost){e.preventDefault();ghost.style.left=e.clientX+'px';ghost.style.top=e.clientY+'px';}});
  const finish=e=>{if(!start)return;if(ghost){const target=document.elementFromPoint(e.clientX,e.clientY)?.closest('#rb-board [data-slot]');if(target){const n=Number(target.dataset.slot);if(start.kind)this.add(start.kind,n);else{const r=this.rooms.find(r=>r.id===start.id);if(r)this.move(r,n);}}ghost.remove();ghost=null;this.dragged=true;setTimeout(()=>this.dragged=false,50);}start=null;};
  element.addEventListener('pointerup',finish);element.addEventListener('pointercancel',()=>{ghost?.remove();ghost=null;start=null;});
 }
 render(){
  if(!this.board)return;const preview=!!this.pending;
  this.el('rb-floors').innerHTML=this.board.floors.map((f,i)=>`<button type="button" data-floor="${i}" class="${i===this.floor?'active':''}">${this.names[i]}</button>`).join('');
  this.el('rb-levels').value=this.board.floors.length;this.el('rb-roof').checked=this.options.getRoof();
  this.el('rb-undo').disabled=!this.history.length||this.busy;this.el('rb-remove').disabled=!this.selected||this.busy;this.el('rb-copy').hidden=!this.floor;
  this.el('rb-hint').textContent=this.selected?'Tap another spot to move or swap this room.':this.targetSlot!=null?'Choose a room to add in the highlighted spot.':this.floor?'The staircase stays connected to the floor below. Add your rooms around it.':'Add rooms in the positions you prefer.';
  this.el('rb-board').innerHTML=[3,2,1,0].flatMap(row=>[0,1].map(col=>{const n=row*2+col,r=this.roomAt(n),blocked=this.blocked(n);return `<button type="button" data-slot="${n}" ${r?`data-room="${this.safe(r.id)}"`:''} class="rb-slot ${r?'rb-filled rb-'+r.kind:''} ${(r&&r.id===this.selected)||(!r&&n===this.targetSlot)?'rb-selected':''}" ${blocked&&!r?'disabled':''} aria-label="${this.safe((r?.name||(blocked?'Open air below':'Empty spot'))+', '+(col?'right':'left')+', '+(row<2?'front':'rear'))}"><span>${this.safe(r?.name||(blocked?'Open air below':'+ Place here'))}</span>${r?.kind==='stair'?'<small>Linked across floors</small>':''}</button>`;})).join('');
  this.el('rb-board').hidden=preview;this.el('rb-preview').hidden=!preview;this.el('rb-build').hidden=preview;this.el('rb-accept').hidden=!preview;this.el('rb-back').hidden=!preview;
  this.el('rb-build').disabled=this.busy;this.el('rb-build').textContent=this.busy?'Fitting your rooms…':'Build my layout ↗';
  this.el('rb-palette').inert=preview||this.busy;this.el('rb-more').disabled=preview||this.busy;
  if(preview)this.renderPreview();else this.message(this.importNote||'Just positions here. We handle room sizes, walls and connections.');
 }
 renderPreview(){const plan=this.pending.customPlan,fl=plan.floors[this.floor],all=fl.rooms.flatMap(r=>r.polygon),w=Math.max(...all.map(p=>p[0]))+150,d=Math.max(...all.map(p=>p[1]))+150;this.el('rb-preview-drawing').innerHTML=`<svg viewBox="0 0 ${w} ${d}" role="img" aria-label="Connected floor plan">${fl.rooms.map(r=>{const xs=r.polygon.map(p=>p[0]),ys=r.polygon.map(p=>p[1]),x=Math.min(...xs),y=Math.min(...ys),rw=Math.max(...xs)-x,rh=Math.max(...ys)-y;return `<rect x="${x}" y="${d-y-rh}" width="${rw}" height="${rh}" fill="${r.kind==='stair'?'#c9d3df':r.kind==='hall'?'#eeeee6':r.kind==='terrace'?'#d7e3bf':'#d6cfb9'}" stroke="#7e897b" stroke-width="60"/><text x="${x+rw/2}" y="${d-y-rh/2}" text-anchor="middle" font-size="${r.kind==='hall'?170:210}" fill="#243d31">${this.safe(r.kind==='hall'?'Passage':r.name)}</text>`;}).join('')}</svg>`;this.message('Your positions, fitted into a connected home. Approve to generate the matching 3D.');}
 async build(){if(this.busy)return;this.busy=true;const revision=this.options.getRevision(),snapshot=JSON.stringify(this.board);this.render();try{const result=await this.options.arrange(this.clone(this.board));if(revision!==this.options.getRevision()||snapshot!==JSON.stringify(this.board)){this.message('Your arrangement changed. Build again to use the latest positions.');return;}this.pending=result;this.pendingRevision=revision;this.render();}catch(e){this.pending=null;this.message(e.message||'Could not fit this arrangement. Your rooms are saved.');}finally{this.busy=false;this.el('rb-build').disabled=false;this.el('rb-build').textContent='Build my layout ↗';this.el('rb-palette').inert=!!this.pending;this.el('rb-more').disabled=!!this.pending;}}
 async accept(){if(!this.pending||this.busy)return;if(this.pendingRevision!==this.options.getRevision()){this.pending=null;this.render();this.message('Your settings changed. Build again to update the layout.');return;}const result=this.pending;this.board=this.clone(result.board);this.active=true;this.pending=null;this.el('room-board-dialog').close();await this.options.accept(result);}
}
