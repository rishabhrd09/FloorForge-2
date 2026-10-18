/* Navigation and presentation only. Geometry remains in the existing Python pipeline. */
'use strict';
const FloorForgeHomeInputs = {
 choices: [
  ['plot','Plot dimensions','I know the width and depth of my plot.','↔'],
  ['compass','Compass map','I want to arrange rooms with simple cells.','▦'],
  ['survey','Guided home brief','Help me choose rooms and home preferences.','☷'],
  ['sketch','A rough sketch','I have a sketch to use as a reference.','✎'],
  ['dxf','A 2D floor plan','I have a prepared DXF drawing to import.','⌑'],
  ['text','Written requirements','I have a description or a wish list.','≡']
 ],
 route(inputs, compassEnabled){
  const chosen=new Set(inputs);
  if(chosen.has('dxf'))return 'dxf';
  if(chosen.has('compass')&&compassEnabled)return 'compass';
  if(chosen.has('sketch'))return 'sketch';
  if(chosen.has('text'))return 'text';
  return 'brief';
 },
 dimensions(width,depth,unit){
  const factor=unit==='m'?1000:304.8;
  if(![width,depth].every(v=>Number.isFinite(v)&&v>0))throw Error('Enter a positive plot width and depth.');
  return {width_mm:Math.round(width*factor),depth_mm:Math.round(depth*factor)};
 },
 fitMap(availableWidth,availableHeight,ratio){
  if(![availableWidth,availableHeight,ratio].every(v=>Number.isFinite(v)&&v>0))return {width:0,height:0};
  const width=Math.min(availableWidth,availableHeight*ratio);
  return {width:Math.floor(width),height:Math.floor(width/ratio)};
 },
 preview(){return `<div class="home-map-demo" aria-hidden="true"><div class="home-demo-grid">${Array.from({length:16},(_,i)=>`<i class="demo-cell demo-${i}">${({0:'Bedroom',2:'Bedroom',8:'Living',10:'Kitchen'})[i]||''}</i>`).join('')}</div><span>ROAD / FRONT OF YOUR HOME</span><b class="demo-pointer">↖</b></div>`;}
};

class FloorForgeHomeWorkspace {
 constructor(options){
  this.options=options;this.$=id=>document.getElementById(id);this.root=document.querySelector('.workspace');
  this.root.classList.add('planning-workspace');this.buildBrief();this.buildSummary();
  this.$('design-edit').onclick=()=>this.setStage('edit');this.$('design-result').onclick=()=>this.setStage('result');
  this.$('design-map-open').onclick=()=>{const action=this.$('design-map-open').dataset.action;this.$(action==='import'?'import-plan-open':action==='exact'?'custom-open':'compass-open').click();};
  this.$('design-review').onclick=()=>this.$('understand').click();
  this.$('brief-form').addEventListener('input',()=>this.refresh());
  this.$('brief-form').addEventListener('change',()=>this.refresh());
  this.setStage(options.compassEnabled()&&!options.isSample()?'edit':'result');
 }
 buildBrief(){
  const aside=document.querySelector('.brief-panel'),form=this.$('brief-form');
  aside.querySelector('h1').textContent='Your custom design';aside.querySelector('.intro').textContent='Start with the essentials. Add detail when you are ready.';
  const tools=document.createElement('details');tools.className='design-saved-tools';tools.innerHTML='<summary>Examples & saved inputs</summary>';
  for(const id of ['sample-gallery-open','sample-return','preset','import-plan-open','sketch-example-home']){const el=this.$(id);tools.append(id==='preset'?el.closest('label'):el);}
  form.before(tools);
  const nav=document.createElement('nav');nav.className='brief-categories';nav.setAttribute('aria-label','Home requirement categories');
  nav.innerHTML=['Plot','Rooms','Ideas','Details'].map((label,i)=>`<button type="button" data-brief-category="${i}" aria-pressed="${i===0}">${label}</button>`).join('');
  const children=[...form.children],plotStart=children.findIndex(e=>e.classList.contains('field-heading')),roomsStart=children.findIndex(e=>e.querySelector('#bedrooms')),detailsStart=children.findIndex(e=>e.querySelector('#advanced-fields')),ideasStart=children.findIndex(e=>e.querySelector('#description'));
  const groups=Array.from({length:4},(_,i)=>{const panel=document.createElement('section');panel.className='brief-category';panel.dataset.briefPanel=i;panel.hidden=i!==0;return panel;});
  form.append(...groups);
  groups[0].innerHTML='<h3>Your plot</h3><p class="design-help">The road marks the front. Width runs along it; depth runs towards the back.</p>';
  groups[1].innerHTML='<h3>The way you want to live</h3><p class="design-help">Choose the home programme. In Compass, add the corresponding rooms and connections to your map.</p>';
  groups[2].innerHTML='<h3>Your ideas & references</h3><p class="design-help">Add a description or keep a sketch beside your work. Review which requests the planner understands.</p>';
  groups[3].innerHTML='<h3>Site & advanced settings</h3><p class="design-help">Setbacks, themes, saved input modes and exact tools are here when you need them.</p>';
  for(let i=plotStart;i<roomsStart;i++)groups[0].append(children[i]);
  for(let i=roomsStart;i<detailsStart;i++)groups[1].append(children[i]);
  groups[3].append(children[0],children[detailsStart]);
  groups[2].append(children[ideasStart]);groups[2].querySelector('details').open=true;
  const inputTools=form.querySelector('.input-tools');
  this.$('compass-open').className='primary wide compass-primary';this.$('compass-open').textContent='Open Compass map ↗';
  const intro=document.createElement('section');intro.className='compass-entry';intro.innerHTML='<span class="overline">ARRANGE YOUR HOME</span><p><strong>Compass map</strong> is a simple room map: join cells to show where each room belongs. Refine a cell for smaller spaces.</p>';
  intro.append(this.$('compass-open'));intro.hidden=!this.options.compassEnabled()&&!this.options.getDraft?.();
  groups[3].append(this.$('custom-open'),this.$('grid-open'));this.$('custom-open').textContent='Advanced room editing';this.$('grid-open').textContent='Legacy positional guide';
  groups[2].append(this.$('reference-open'));groups[3].append(this.$('loaded-sources'));
  for(const id of ['references'])groups[2].append(this.$(id));
  const scopeNote=form.querySelector('.input-scope-note');if(scopeNote)groups[2].append(scopeNote);
  inputTools.remove();form.prepend(intro,nav,...groups);
  const actions=document.createElement('div');actions.className='design-primary-actions';actions.append(this.$('understand'),this.$('generate'));form.append(actions);
  const context=document.createElement('label');context.textContent='What surrounds the plot?';context.innerHTML+='<select id="design-context"><option value="unknown">Choose later</option><option value="middle">Middle plot · neighbours on both sides</option><option value="corner">Corner plot</option><option value="three-open">Three sides open</option><option value="independent">Independent plot</option></select><small>Saved as site context; it does not infer a second road or change setbacks.</small>';groups[0].append(context);
  this.$('design-context').onchange=()=>this.options.context(this.$('design-context').value);
  nav.querySelectorAll('button').forEach(b=>b.onclick=()=>this.showCategory(Number(b.dataset.briefCategory)));
 }
 showCategory(index){document.querySelectorAll('[data-brief-panel]').forEach(p=>p.hidden=Number(p.dataset.briefPanel)!==index);document.querySelectorAll('[data-brief-category]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.briefCategory)===index)));}
 buildSummary(){
  const studio=document.querySelector('.studio'),header=document.createElement('nav');header.className='design-stage-nav';header.setAttribute('aria-label','Custom design workspace');header.innerHTML='<button id="design-edit" type="button">1 · Your inputs</button><span>→</span><button id="design-result" type="button">2 · Generated home</button>';studio.prepend(header);
  const summary=document.createElement('section');summary.id='design-summary';summary.className='design-summary';summary.innerHTML=`<p class="overline">YOUR HOME, TAKING SHAPE</p><h2>A clear brief.<br>A home that feels like you.</h2><p id="design-path-explanation">Set the essentials on the left. Arrange your rooms on Compass, then review the checked geometry before generating.</p>${FloorForgeHomeInputs.preview()}<dl id="design-facts"></dl><div class="design-summary-actions"><button id="design-map-open" class="primary" type="button">Arrange on Compass map ↗</button><button id="design-review" class="secondary" type="button">Review my inputs</button></div><p id="design-draft-feedback" role="status"></p><p class="design-help">Cell editor: divide one map cell into equal left/right halves for bathrooms, passages and other smaller spaces. Advanced editing refines the accepted room outlines.</p>`;
  this.$('journey-guide').after(summary);
 }
 setStage(stage){this.stage=stage;this.root.classList.toggle('design-editing',stage==='edit');this.$('design-edit').setAttribute('aria-pressed',String(stage==='edit'));this.$('design-result').setAttribute('aria-pressed',String(stage==='result'));this.options.pause(stage==='edit');this.refresh();requestAnimationFrame(()=>window.dispatchEvent(new Event('resize')));}
 setInputs(inputs,source){this.inputs=inputs;this.source=source;this.refresh();}

 renderMapSummary(){
  const root=this.$('design-summary').querySelector('.home-map-demo'),draft=this.options.getDraft?.();if(!root)return;
  const floor=draft?.floors[0],rooms=draft?.rooms.filter(r=>r.floorId===floor.id)||[];
  if(!rooms.some(r=>r.regions.length)){root.innerHTML=FloorForgeHomeInputs.preview().replace(/^<div[^>]*>|<\/div>$/g,'')+'<small class="design-demo-caption">How Compass works · illustrative room positions</small>';return;}
  const grid=document.createElement('div');grid.className='home-demo-grid';const envelope=this.options.getEnvelope?.();grid.style.aspectRatio=envelope&&envelope[1]>0?String(envelope[0]/envelope[1]):'1';grid.style.gridTemplateRows=`repeat(${draft.grid.rows},1fr)`;
  for(let row=draft.grid.rows-1;row>=0;row--)for(let col=0;col<4;col++){const split=floor.splits.includes(`${row}:${col}`),owners=(split?['L','R'].map(h=>CompassState.owner(draft,floor.id,`${row}:${col}:${h}`)):[CompassState.owner(draft,floor.id,`${row}:${col}`)]),cell=document.createElement('i');cell.className='demo-cell';cell.textContent=owners.map(r=>r?.name||'Empty').join(' / ');cell.title=cell.textContent;cell.style.background=owners[0]?'#cedbc3':'#f7f7ed';grid.append(cell);}
  const road=document.createElement('span');road.textContent='YOUR GROUND FLOOR · ROAD / FRONT';root.replaceChildren(grid,road);
 }

 refresh(){
  const factor=this.options.unit()==='ft'?304.8:1000,width=Math.round(Number(this.$('width').value)*factor),depth=Math.round(Number(this.$('depth').value)*factor),floors=Number(this.$('storeys').value),bearing=Number(this.$('facing').value),names=['North','North-east','East','South-east','South','South-west','West','North-west'];
  const facts=[['Plot',`${(width/1000).toFixed(2)} × ${(depth/1000).toFixed(2)} m`],['Front / road',names[Math.round(bearing/45)%8]],['Floors',['Ground','Ground + First','Ground + First + Second'][floors-1]],['Bedrooms',this.$('bedrooms').value]];
  this.$('design-facts').replaceChildren(...facts.map(([label,value])=>{const row=document.createElement('div');const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=label;dd.textContent=value;row.append(dt,dd);return row;}));
  const exact=this.$('plan-mode').value==='custom',importing=this.source==='dxf'&&!exact;this.$('design-map-open').dataset.action=importing?'import':exact?'exact':'compass';this.$('design-map-open').textContent=importing?'Import my 2D plan →':exact?'Refine exact rooms →':'Arrange on Compass map ↗';this.$('design-map-open').hidden=!this.options.compassEnabled()&&!importing&&!exact;this.$('design-path-explanation').textContent=importing?'Import your prepared DXF, then review its exact dimensions and rooms. Other descriptions and references can be added in Ideas.':exact?'Your exact room plan controls the design. Refine its outlines or review your inputs before generating the matching 2D and 3D home.':'Set the essentials on the left. Arrange your rooms on Compass, then review the checked layout before generating.';
  const hint=document.querySelector('[data-brief-panel="1"] .chips')?.previousElementSibling?.querySelector('.hint');if(hint)hint.textContent=this.$('plan-mode').value==='compass'?'Add these rooms to your map':'Planned as rooms';
  this.renderMapSummary();
  this.$('design-context').value=this.options.getContext()||'unknown';
 }
}
