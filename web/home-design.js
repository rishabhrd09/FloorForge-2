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
 restore(project,compassEnabled){
  const saved=project.editorState?.homeInputs;
  if(Array.isArray(saved)&&saved.length)return [...saved];
  const inputs=['plot'],mode=project.editorState?.mode;
  if(project.compass||mode==='compass')inputs.push('compass');else inputs.push('survey');
  if(project.text||project.sources?.some(s=>s.kind==='text'))inputs.push('text');
  if(project.attachments?.length)inputs.push('sketch');
  return inputs.filter(id=>id!=='compass'||compassEnabled||project.compass||project.editorState?.compassDraft);
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
  this.$('design-map-open').onclick=()=>{const action=this.$('design-map-open').dataset.action;if(action==='brief'||action==='text'){this.showCategory(action==='brief'?1:2);this.$(action==='brief'?'bedrooms':'description').focus();return;}this.$(action==='import'?'import-plan-open':action==='exact'?'custom-open':action==='guide'?'grid-open':'compass-open').click();};
  this.$('design-review').onclick=()=>this.$('understand').click();
  this.$('brief-form').addEventListener('input',()=>this.refresh());
  this.$('brief-form').addEventListener('change',()=>this.refresh());
  this.load(options.getProject());this.setStage(options.compassEnabled()&&!options.isSample()?'edit':'result');
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
  inputTools.remove();form.prepend(intro,nav,...groups);this.buildInputChoices(intro);
  const actions=document.createElement('div');actions.className='design-primary-actions';actions.append(this.$('understand'),this.$('generate'));form.append(actions);
  const context=document.createElement('label');context.textContent='What surrounds the plot?';context.innerHTML+='<select id="design-context"><option value="unknown">Choose later</option><option value="middle">Middle plot · neighbours on both sides</option><option value="corner">Corner plot</option><option value="three-open">Three sides open</option><option value="independent">Independent plot</option></select><small>Saved as site context; it does not infer a second road or change setbacks.</small>';groups[0].append(context);
  this.$('design-context').onchange=()=>this.options.context(this.$('design-context').value);
  nav.querySelectorAll('button').forEach(b=>b.onclick=()=>this.showCategory(Number(b.dataset.briefCategory)));
 }
 buildInputChoices(intro){
  const panel=document.createElement('section');panel.className='design-input-tools';panel.setAttribute('aria-label','Choose your home inputs');
  panel.innerHTML='<h3>Your inputs</h3><p class="design-help">Use one input or combine several. You can add more at any time.</p><div id="design-input-choices" class="design-input-choices"></div><div id="design-input-actions" class="design-input-actions"></div><p id="design-input-status" class="design-help" role="status"></p><h4>Which layout should generate your home?</h4><div id="design-layout-choices" class="design-layout-choices"></div><p class="design-help">The chosen layout controls room geometry. Descriptions add supported requirements; sketches stay as references. Review inputs to see what is applied.</p>';
  panel.append(this.$('generation-input-summary'));intro.before(panel);
  this.$('design-input-choices').innerHTML=FloorForgeHomeInputs.choices.map(([id,title,,icon])=>`<button type="button" data-design-input="${id}" aria-pressed="false"><span aria-hidden="true">${icon}</span> ${title}</button>`).join('');
  this.$('design-input-choices').onclick=e=>{const b=e.target.closest('[data-design-input]');if(!b)return;const chosen=new Set(this.inputs),id=b.dataset.designInput;if(chosen.has(id)&&chosen.size===1){this.$('design-input-status').textContent='Keep at least one input selected.';return;}if(chosen.has(id))chosen.delete(id);else chosen.add(id);this.setInputs([...chosen]);this.$('design-input-status').textContent='Input choices saved. Existing descriptions, references and room drafts are retained.';this.options.changed();};
  this.$('design-input-actions').onclick=e=>{const b=e.target.closest('[data-input-action]');if(!b)return;const id=b.dataset.inputAction;if(id==='compass')this.$('compass-open').click();else if(id==='dxf')this.$('import-plan-open').click();else if(id==='sketch'){this.showCategory(2);this.$('reference-open').click();}else{const category=id==='plot'?0:id==='survey'?1:2;this.showCategory(category);this.$(id==='plot'?'width':id==='survey'?'bedrooms':'description').focus();}};
  this.$('design-layout-choices').innerHTML=[['automatic','Guided brief'],['compass','Compass map'],['custom','Exact rooms / DXF'],['guide','Legacy floor guide']].map(([mode,label])=>`<button type="button" data-layout-mode="${mode}" aria-pressed="false">${label}</button>`).join('');
  this.$('design-layout-choices').onclick=e=>{const b=e.target.closest('[data-layout-mode]');if(!b)return;this.$('plan-mode').value=b.dataset.layoutMode;this.$('plan-mode').dispatchEvent(new Event('change',{bubbles:true}));this.refresh();};
 }
 renderInputChoices(){
  const chosen=new Set(this.inputs||[]),mode=this.$('plan-mode').value;
  document.querySelectorAll('[data-design-input]').forEach(b=>{b.setAttribute('aria-pressed',String(chosen.has(b.dataset.designInput)));b.disabled=b.dataset.designInput==='compass'&&!this.options.compassEnabled()&&!this.options.getDraft?.();});
  const labels={plot:'Edit plot',survey:'Choose requirements',compass:'Arrange rooms ↗',sketch:'Add sketch reference',dxf:'Import 2D plan',text:'Write requirements'};
  this.$('design-input-actions').replaceChildren(...FloorForgeHomeInputs.choices.filter(([id])=>chosen.has(id)).map(([id])=>{const b=document.createElement('button');b.type='button';b.dataset.inputAction=id;b.textContent=labels[id];return b;}));
  document.querySelectorAll('[data-layout-mode]').forEach(b=>{const value=b.dataset.layoutMode;b.setAttribute('aria-pressed',String(value===mode));b.hidden=value==='compass'&&!this.options.compassEnabled()&&!this.options.getDraft?.()||value==='custom'&&!this.options.hasExact()&&mode!=='custom'||value==='guide'&&!this.options.hasGuide()&&mode!=='guide';});
 }
 load(project){this.setInputs(FloorForgeHomeInputs.restore(project,this.options.compassEnabled()));this.$('design-input-status').textContent='';}
 showCategory(index){document.querySelectorAll('[data-brief-panel]').forEach(p=>p.hidden=Number(p.dataset.briefPanel)!==index);document.querySelectorAll('[data-brief-category]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.briefCategory)===index)));}
 buildSummary(){
  const studio=document.querySelector('.studio'),header=document.createElement('nav');header.className='design-stage-nav';header.setAttribute('aria-label','Custom design workspace');header.innerHTML='<button id="design-edit" type="button">1 · Your inputs</button><span>→</span><button id="design-result" type="button">2 · Generated home</button>';studio.prepend(header);
  const summary=document.createElement('section');summary.id='design-summary';summary.className='design-summary';summary.innerHTML=`<p class="overline">YOUR HOME, TAKING SHAPE</p><h2>A clear brief.<br>A home that feels like you.</h2><p id="design-path-explanation">Set the essentials on the left. Arrange your rooms on Compass, then review the checked geometry before generating.</p>${FloorForgeHomeInputs.preview()}<dl id="design-facts"></dl><div class="design-summary-actions"><button id="design-map-open" class="primary" type="button">Arrange on Compass map ↗</button><button id="design-review" class="secondary" type="button">Review my inputs</button></div><p id="design-draft-feedback" role="status"></p><p class="design-help">Cell editor: divide one map cell into equal left/right halves for bathrooms, passages and other smaller spaces. Advanced editing refines the accepted room outlines.</p>`;
  this.$('journey-guide').after(summary);
 }
 setStage(stage){this.stage=stage;this.root.classList.toggle('design-editing',stage==='edit');this.$('design-edit').setAttribute('aria-pressed',String(stage==='edit'));this.$('design-result').setAttribute('aria-pressed',String(stage==='result'));this.options.pause(stage==='edit');this.refresh();requestAnimationFrame(()=>window.dispatchEvent(new Event('resize')));}
 setInputs(inputs){this.inputs=[...inputs];this.source=FloorForgeHomeInputs.route(inputs,this.options.compassEnabled());this.refresh();}

 renderMapSummary(){
  const root=this.$('design-summary').querySelector('.home-map-demo'),draft=this.options.getDraft?.();if(!root)return;
  const floor=draft?.floors[0],rooms=draft?.rooms.filter(r=>r.floorId===floor.id)||[];
  if(!rooms.some(r=>r.regions.length)){root.innerHTML=FloorForgeHomeInputs.preview().replace(/^<div[^>]*>|<\/div>$/g,'')+'<small class="design-demo-caption">How Compass works · illustrative room positions</small>';return;}
  const grid=document.createElement('div');grid.className='home-demo-grid';const envelope=this.options.getEnvelope?.();grid.style.aspectRatio=envelope&&envelope[1]>0?String(envelope[0]/envelope[1]):'1';grid.style.gridTemplateRows=`repeat(${draft.grid.rows},1fr)`;
  for(let row=draft.grid.rows-1;row>=0;row--)for(let col=0;col<4;col++){const split=floor.splits.includes(`${row}:${col}`),owners=(split?['L','R'].map(h=>CompassState.owner(draft,floor.id,`${row}:${col}:${h}`)):[CompassState.owner(draft,floor.id,`${row}:${col}`)]),cell=document.createElement('i');cell.className='demo-cell';cell.textContent=owners.map(r=>r?.name||'Empty').join(' / ');cell.title=cell.textContent;cell.style.background=owners[0]?'#cedbc3':'#f7f7ed';grid.append(cell);}
  const road=document.createElement('span');road.textContent='YOUR GROUND FLOOR · ROAD / FRONT';root.replaceChildren(grid,road);
 }

 refresh(){
  this.renderInputChoices();
  const factor=this.options.unit()==='ft'?304.8:1000,width=Math.round(Number(this.$('width').value)*factor),depth=Math.round(Number(this.$('depth').value)*factor),floors=Number(this.$('storeys').value),bearing=Number(this.$('facing').value),names=['North','North-east','East','South-east','South','South-west','West','North-west'];
  const facts=[['Plot',`${(width/1000).toFixed(2)} × ${(depth/1000).toFixed(2)} m`],['Front / road',names[Math.round(bearing/45)%8]],['Floors',['Ground','Ground + First','Ground + First + Second'][floors-1]],['Bedrooms',this.$('bedrooms').value]];
  this.$('design-facts').replaceChildren(...facts.map(([label,value])=>{const row=document.createElement('div');const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=label;dd.textContent=value;row.append(dt,dd);return row;}));
  const mode=this.$('plan-mode').value,exact=mode==='custom',mapping=mode==='compass',importing=this.source==='dxf'&&!exact&&!mapping,action=exact?'exact':mapping?'compass':mode==='guide'?'guide':importing?'import':this.source==='text'?'text':'brief';
  const actions={exact:['Refine exact rooms →','Your exact room plan controls the design. Refine its outlines or review your inputs before generating the matching 2D and 3D home.'],compass:['Arrange on Compass map ↗','Your Compass map controls room positions. Add other requirements and references alongside it, then review and accept the checked geometry.'],guide:['Edit floor guide →','Your relative floor guide and resolved requirements constrain the planner. Review them before generating.'],import:['Import my 2D plan →','Import your prepared DXF, then review its exact dimensions and rooms. Other descriptions and references can be added in Ideas.'],text:['Write requirements →','Write your requirements, then review which fields are understood. The guided planner uses the resolved plot and home requirements.'],brief:['Choose home requirements →','Your plot and supported home requirements guide the planner. Review the resolved inputs, then generate your home.']};
  this.$('design-map-open').dataset.action=action;this.$('design-map-open').textContent=actions[action][0];this.$('design-map-open').hidden=mapping&&!this.options.compassEnabled();this.$('design-path-explanation').textContent=actions[action][1];
  document.querySelector('.compass-entry').hidden=!this.options.compassEnabled()&&!this.options.getDraft?.()||!mapping&&!this.inputs?.includes('compass');
  this.$('design-summary').querySelector('.home-map-demo').hidden=!mapping;
  const hint=document.querySelector('[data-brief-panel="1"] .chips')?.previousElementSibling?.querySelector('.hint');if(hint)hint.textContent=this.$('plan-mode').value==='compass'?'Add these rooms to your map':'Planned as rooms';
  this.renderMapSummary();
  this.$('design-context').value=this.options.getContext()||'unknown';
 }
}
