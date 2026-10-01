/* Placement-only edits. Units are metres here; canonical room boundaries remain mm. */
'use strict';
class FloorForgeLayoutEditor {
  constructor(options) {
    Object.assign(this, options); this.$=id=>document.getElementById(id); this.dialog=this.$('placement-dialog');this.svg=this.$('placement-canvas');
    this.$('placement-close').onclick=()=>this.dialog.close();
    this.$('placement-furniture').onclick=()=>this.setMode('furniture');this.$('placement-rooms').onclick=()=>this.setMode('rooms');
    this.$('placement-undo').onclick=()=>this.travel(-1);this.$('placement-redo').onclick=()=>this.travel(1);
    this.$('placement-swap').onclick=()=>this.swap([...this.selected]);
    this.$('placement-rotate').onclick=()=>this.rotate();
    this.$('placement-exact').onclick=()=>this.exact();
    this.$('placement-reset').onclick=()=>this.reset();
    this.$('placement-check').onclick=()=>this.validate(false);this.$('placement-apply').onclick=()=>this.validate(true);
    this.svg.addEventListener('pointerdown',e=>this.down(e));this.svg.addEventListener('pointermove',e=>this.move(e));this.svg.addEventListener('pointerup',e=>this.up(e));
    this.svg.addEventListener('pointercancel',()=>{if(this.drag){this.edits=this.drag.snapshot;this.drag=null;this.render();}});
    this.dialog.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='z'&&!['INPUT','TEXTAREA'].includes(e.target.tagName)){e.preventDefault();this.travel(e.shiftKey?1:-1);}});
  }
  open(project, building, scene) {
    this.project=structuredClone(project);this.building=building;this.scene=scene;this.floor=0;this.mode='furniture';this.selected=new Set();this.busy=false;this.issueIds=new Set();
    this.edits={roomEdits:structuredClone(project.roomEdits||[]),furnitureLayout:structuredClone(project.furnitureLayout||[])};
    this.history=[JSON.stringify(this.edits)];this.cursor=0;
    this.note('Drag furniture, or select Rooms to swap positions. Your generated design stays unchanged until you apply.');this.render();this.dialog.showModal();
  }
  note(text){this.$('placement-status').textContent=text;}
  setMode(mode){if(mode==='rooms'&&this.project.customPlan){this.dialog.close();this.openCustom();return;}this.mode=mode;this.selected.clear();this.render();this.note(mode==='rooms'?'Drag a room onto another to swap their slots, or Shift-click two rooms and choose Swap. Each takes the destination shape and size.':'Drag a complete furniture item. Rotate or enter exact offsets; fixed architectural surfaces stay in place.');}
  items(){return this.mode==='rooms'?this.building.spaces.filter(r=>r.floor===this.floor):(this.scene.editables||[]).filter(r=>r.floor===this.floor);}
  baseRoom(id){return (this.building.roomEditBase||[]).find(r=>r.id===id);}
  roomPolygon(r){const base=this.baseRoom(r.id);return this.edits.roomEdits.find(e=>e.id===r.id)?.polygon||base?.polygon||r.polygon;}
  placement(item){return this.edits.furnitureLayout.find(e=>e.id===item.id)||{id:item.id,anchorHash:item.anchorHash,dx:0,dy:0,angle:0};}
  polygon(item){if(this.mode==='rooms')return this.roomPolygon(item).map(p=>p.map(x=>x/1000));return this.furniturePolygon(item);}
  furniturePolygon(item){const e=this.placement(item),a=e.angle*Math.PI/180,[cx,cy]=item.pivot;return item.footprint.map(([x,y])=>[cx+(x-cx)*Math.cos(a)-(y-cy)*Math.sin(a)+e.dx,cy+(x-cx)*Math.sin(a)+(y-cy)*Math.cos(a)+e.dy]);}
  save(){this.issueIds.clear();const value=JSON.stringify(this.edits);if(this.history[this.cursor]!==value){this.history.splice(this.cursor+1);this.history.push(value);this.cursor++;}this.note('Unapplied edit · Check placements to review conflicts, then apply to the 3D and exports.');this.render();}
  travel(d){if(this.cursor+d<0||this.cursor+d>=this.history.length)return;this.cursor+=d;this.edits=JSON.parse(this.history[this.cursor]);this.issueIds.clear();this.note('Placement '+(d<0?'undone.':'restored.'));this.render();}
  put(key,e){this.edits[key]=this.edits[key].filter(i=>i.id!==e.id);if(key==='furnitureLayout'&&e.dx===0&&e.dy===0&&e.angle===0)return;this.edits[key].push(e);}
  point(e){const p=new DOMPoint(e.clientX,e.clientY).matrixTransform(this.svg.getScreenCTM().inverse());return [p.x,this.depth-p.y];}
  down(e){if(this.busy||e.button!==0)return;const target=e.target.closest('[data-placement-id]');if(!target)return;const id=target.dataset.placementId;
    if(e.shiftKey){this.selected.has(id)?this.selected.delete(id):this.selected.add(id);this.render();return;}
    this.selected=new Set([id]);const item=this.items().find(i=>i.id===id);this.drag={id,start:this.point(e),snapshot:structuredClone(this.edits),placement:structuredClone(this.placement(item)),moved:false};this.svg.setPointerCapture(e.pointerId);this.render();e.preventDefault();}
  move(e){if(!this.drag||this.busy)return;const p=this.point(e),dx=p[0]-this.drag.start[0],dy=p[1]-this.drag.start[1];if(Math.hypot(dx,dy)<.02)return;this.drag.moved=true;
    if(this.mode==='furniture'){const old=this.drag.placement,snap=x=>this.$('placement-snap').checked?Math.round(x*20)/20:Math.round(x*1000)/1000;this.put('furnitureLayout',{...old,dx:snap(old.dx+dx),dy:snap(old.dy+dy)});this.render();}
    else this.note('Release over the destination room to swap. Sizes follow the destination slots.');}
  up(e){if(!this.drag)return;const d=this.drag;this.drag=null;this.svg.releasePointerCapture?.(e.pointerId);if(!d.moved)return;
    if(this.mode==='rooms'){const [x,y]=this.point(e);const target=this.items().find(r=>r.id!==d.id&&this.contains(this.polygon(r),x,y));if(target)this.swap([d.id,target.id]);else this.note('Drop onto another room to swap. For drawing walls or changing exact dimensions, use Custom Plan.');}
    else this.save();}
  contains(p,x,y){let yes=false;for(let i=0,j=p.length-1;i<p.length;j=i++){const [a,b]=p[i],[c,d]=p[j];if((b>y)!==(d>y)&&x<(c-a)*(y-b)/(d-b)+a)yes=!yes;}return yes;}
  swap(ids){if(ids.length!==2){this.note('Shift-click two rooms, then choose Swap.');return;}const [a,b]=ids.map(id=>this.building.spaces.find(r=>r.id===id));if(!a||!b)return;
    if(a.kind==='stair'||b.kind==='stair'){this.note('Stair cores must stay aligned across floors. Use the Custom Plan editor’s linked-stair move control to place a core anywhere it fits.');return;}
    if(this.edits.furnitureLayout.length){this.note('Reset furniture placements before changing room geometry; their anchors belong to this layout. Your edits are retained.');return;}
    const pa=structuredClone(this.roomPolygon(a)),pb=structuredClone(this.roomPolygon(b));for(const [r,p] of [[a,pb],[b,pa]]){const anchor=this.baseRoom(r.id);if(!anchor){this.note('Generate this plan with the current version before editing rooms.');return;}this.put('roomEdits',{id:r.id,anchorHash:anchor.anchorHash,polygon:p});}this.selected=new Set(ids);this.save();}
  rotate(){const id=[...this.selected][0],item=this.items().find(i=>i.id===id);if(!item||this.mode!=='furniture')return;const p=this.placement(item);this.put('furnitureLayout',{...p,angle:(p.angle+90)%360});this.save();}
  exact(){const id=[...this.selected][0],item=this.items().find(i=>i.id===id);if(!item)return;const dx=Number(this.$('placement-x').value),dy=Number(this.$('placement-y').value),angle=Number(this.$('placement-angle').value);if(![dx,dy,angle].every(Number.isFinite)){this.note('Enter finite numbers.');return;}this.put('furnitureLayout',{id:item.id,anchorHash:item.anchorHash,dx,dy,angle});this.save();}
  reset(){const key=this.mode==='rooms'?'roomEdits':'furnitureLayout';this.edits[key]=[];this.save();}
  payload(){const p=structuredClone(this.project);for(const key of ['roomEdits','furnitureLayout']){if(this.edits[key].length)p[key]=structuredClone(this.edits[key]);else delete p[key];}return p;}
  async validate(apply){if(this.busy)return;this.busy=true;this.render();this.note('Checking room access, furniture clearances and the complete model…');try{const result=await this.check(this.payload());this.note('Placements pass. Applying updates the matching 3D, drawings and exports.');if(apply){this.apply(structuredClone(this.edits));this.dialog.close();}}catch(e){this.showIssues(e);}finally{this.busy=false;this.render();}}
  showIssues(error){
    const detail=error.data?.details||{},issues=detail.errors||[detail];this.issueIds.clear();
    const name=id=>this.building.spaces.find(r=>r.id===id)?.name||this.scene.editables.find(i=>i.id===id)?.label||id||'This placement';
    const lines=[];for(const issue of issues){const ids=issue.ids||[issue.id].filter(Boolean);ids.forEach(id=>this.issueIds.add(id));const label=ids.map(name).join(' / ');
      if(issue.code==='GUIDELINE_ROOM_SIZE')lines.push(`${label}: ${issue.actual_m2} m² available; ${issue.required_m2} m² required, with a clear short side of at least ${issue.target_width_mm/1000} m.`);
      else if(issue.message)lines.push(issue.message);
      else if(issue.code)lines.push(`${label}: ${({'UNREACHABLE':'needs an accessible doorway','UNTILED_FLOOR':'leave no unassigned gaps between room slots','STAIR_ALIGNMENT':'align the linked stair rooms on every floor','PRIVATE_THROUGH_ROUTE':'provide access without passing through another private room'})[issue.code]||issue.code.toLowerCase().replaceAll('_',' ')}.`);
    }
    this.note([error.message,...lines].join(' '));
  }
  render(){const names=['Ground','First','Second'];this.$('placement-floors').replaceChildren();for(let f=0;f<this.building.storeys;f++){const b=document.createElement('button');b.type='button';b.textContent=names[f];b.className=f===this.floor?'active':'';b.disabled=this.busy;b.onclick=()=>{this.floor=f;this.selected.clear();this.render();};this.$('placement-floors').append(b);}
    for(const m of ['furniture','rooms'])this.$('placement-'+m).classList.toggle('active',m===this.mode);
    this.$('placement-floor-summary').textContent=`${this.building.storeys===1?'Ground only':'G+'+(this.building.storeys-1)} · ${this.building.storeys} occupied floors${this.building.rooftop?' · stairs continue to the roof terrace':''}`;
    this.$('placement-undo').disabled=this.busy||this.cursor===0;this.$('placement-redo').disabled=this.busy||this.cursor===this.history.length-1;
    this.$('placement-swap').hidden=this.mode!=='rooms';this.$('placement-swap').disabled=this.busy||this.selected.size!==2;this.$('placement-rotate').hidden=this.mode!=='furniture';this.$('placement-rotate').disabled=this.busy||this.selected.size!==1;
    for(const id of ['placement-check','placement-apply','placement-reset','placement-furniture','placement-rooms'])this.$(id).disabled=this.busy;
    const fp=this.building.footprint.map(p=>p.map(x=>x/1000));this.depth=Math.max(...fp.map(p=>p[1]));const width=Math.max(...fp.map(p=>p[0]));this.svg.setAttribute('viewBox',`-.5 -.5 ${width+1} ${this.depth+1}`);this.svg.replaceChildren();
    const el=(tag,attrs,parent=this.svg)=>{const n=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,v);parent.append(n);return n;};
    const draw=(p,attrs,parent=this.svg)=>el('polygon',{points:p.map(([x,y])=>`${x},${this.depth-y}`).join(' '),...attrs},parent);
    for(const r of this.building.spaces.filter(r=>r.floor===this.floor)){const p=this.roomPolygon(r).map(p=>p.map(x=>x/1000));draw(p,{fill:'#eef0e7',stroke:'#abb3a4','stroke-width':'.025'});}
    if(this.mode==='furniture'){for(const w of this.building.walls.filter(w=>w.floor===this.floor))draw(w.polygon.map(p=>p.map(x=>x/1000)),{fill:'#899382'});for(const f of this.scene.furniture.filter(f=>f.floor===this.floor&&!this.scene.editables.some(i=>i.id===f.id)))draw(f.footprint,{fill:'#dddcd5',stroke:'#babbae','stroke-width':'.02'});}
    if(this.mode==='furniture'){
      const walls=new Map(this.building.walls.map(w=>[w.id,w]));
      for(const o of this.building.openings.filter(o=>o.floor===this.floor)){const w=walls.get(o.wall_id);if(!w)continue;const d=Math.hypot(w.b[0]-w.a[0],w.b[1]-w.a[1]),u=[(w.b[0]-w.a[0])/d,(w.b[1]-w.a[1])/d],a=w.a.map((v,j)=>(v+u[j]*o.offset)/1000),b=w.a.map((v,j)=>(v+u[j]*(o.offset+o.width))/1000);el('line',{x1:a[0],y1:this.depth-a[1],x2:b[0],y2:this.depth-b[1],stroke:o.kind==='window'?'#c1dadd':'#f0f2e9','stroke-width':(w.thickness+12)/1000});}
      for(const st of this.building.stairs.filter(st=>st.floor===this.floor)){const x=st.x/1000,y=st.y/1000,w=st.width/1000,d=st.depth/1000;for(let i=0;i<9;i++){const yy=y+1.1+i*(d-1.1)/9;el('line',{x1:x,y1:this.depth-yy,x2:x+w,y2:this.depth-yy,stroke:'#b0b6aa','stroke-width':'.025'});}const t=el('text',{x:x+w/2,y:this.depth-y-.5,'text-anchor':'middle','font-size':'.2',fill:'#5e6b5c'});t.textContent='↑ Stairs';}
    }
    for(const item of this.items()){const p=this.polygon(item),sel=this.selected.has(item.id),g=el('g',{'data-placement-id':item.id,tabindex:'0',role:'button','aria-label':item.name||item.label});draw(p,{fill:sel?'#c7d9bd':this.mode==='rooms'?'#dedcca':'#d9c9ad',stroke:this.issueIds.has(item.id)?'#b44836':sel?'#244d3c':'#918f7f','stroke-width':sel?'.065':'.025','data-placement-id':item.id},g);const x=p.reduce((n,q)=>n+q[0],0)/p.length,y=p.reduce((n,q)=>n+q[1],0)/p.length;const t=el('text',{x,y:this.depth-y,'text-anchor':'middle','dominant-baseline':'central','font-size':this.mode==='rooms'?'.24':'.18',fill:'#283f32','pointer-events':'none'},g);t.textContent=item.name||item.label;g.addEventListener('click',e=>{if(e.detail===0){this.selected=new Set([item.id]);this.render();}});}
    this.$('placement-list').replaceChildren();for(const item of this.items()){const b=document.createElement('button');b.type='button';b.textContent=item.name||(item.label+' · '+(this.building.spaces.find(r=>r.id===item.roomId)?.name||''));b.className=this.selected.has(item.id)?'active':'';b.onclick=e=>{if(e.shiftKey)this.selected.has(item.id)?this.selected.delete(item.id):this.selected.add(item.id);else this.selected=new Set([item.id]);this.render();};this.$('placement-list').append(b);}
    const item=this.items().find(i=>this.selected.has(i.id));this.$('placement-selected').textContent=item?(item.name||item.label):'Choose an item';this.$('placement-values').hidden=!item||this.mode!=='furniture';if(item&&this.mode==='furniture'){const p=this.placement(item);this.$('placement-x').value=p.dx.toFixed(3);this.$('placement-y').value=p.dy.toFixed(3);this.$('placement-angle').value=p.angle;}
    this.$('placement-help').textContent=this.mode==='rooms'?'Room swaps retain the floor count and the destination boundaries. Access and size checks can block an unsuitable swap. Move linked stairs and author exact geometry in Custom Plan.':'Coloured items move as complete sets: cushions with sofas, chairs with dining tables, bedside tables with beds. Grey fittings and wall finishes are fixed building components. Room changes may require resetting furniture placements.';
  }
}
window.FloorForgeLayoutEditor=FloorForgeLayoutEditor;
