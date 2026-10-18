/* Navigation only: the existing project compiler and sample assets stay authoritative. */
'use strict';
class FloorForgeStartPage {
 constructor(options) {
  this.options=options;this.$=id=>document.getElementById(id);this.ready=false;
  const icons=[
   '<path d="M6 28V14L20 4l14 10v20H6zm11 6V22h8v12M28 5v8"/>',
   '<path d="m4 15 16-9 16 9v18H4zm0 0 16 9 16-9M20 24v9M12 20v12M28 20v12"/>',
   '<path d="M5 32V11h20v21H5zm0-10h12V11M22 31l4-9 9-9 4 4-9 9z"/>',
   '<path d="M8 5h17l8 8v23H8zm17 0v9h8M20 18v13m-5-5 5 5 5-5"/>',
   '<path d="M4 12h12l4 5h16l-4 17H4zm0 0V7h12l4 5h13v5"/>',
   '<path d="M8 12a15 15 0 1 1-2 16M4 5v10h10M20 11v10l7 4"/>'
  ];
  const cards=[
   ['new','01 / A FRESH START','Design a new home','Start with your plot, your rooms and the way you want to live.','Choose your starting point'],
   ['samples','02 / FIND INSPIRATION','Walk through sample homes','Explore furnished homes in 3D, with floor plans and views to compare.','Explore the collection'],
   ['customize','03 / MAKE IT YOURS','Adapt a sample home','Choose a finished design, then open your own editable working copy.','Choose a home to adapt'],
   ['import','04 / BRING YOUR PLAN','Bring a drawing or sketch','Import a prepared DXF, or work from a rough sketch with optional local AI.','Choose your input'],
   ['saved','05 / YOUR PROJECTS','Open a saved project','Return to projects saved on this device or upload a FloorForge project file.','Find your project'],
   ['continue','06 / PICK UP WHERE YOU LEFT OFF','Continue your workspace','Return to your current draft, room editor and latest generated views.','Back to your workspace']
  ];
  this.$('start-cards').innerHTML=cards.map(([id,kicker,title,copy,cta],i)=>`<button type="button" class="start-card" data-start="${id}" disabled><span class="start-card-top"><svg viewBox="0 0 42 42" aria-hidden="true">${icons[i]}</svg><span class="start-number">0${i+1}</span></span><span class="overline">${kicker.slice(5)}</span><strong>${title}</strong><span class="start-card-copy">${copy}</span><span class="start-card-link">${cta}<span aria-hidden="true">↗</span></span></button>`).join('');
  this.$('start-cards').onclick=e=>{const b=e.target.closest('[data-start]');if(b)this.choose(b.dataset.start);};
  document.querySelector('.identity').onclick=e=>{e.preventDefault();this.show();};
  this.$('start-home').onclick=()=>this.show();
  this.$('start-setup-close').onclick=()=>this.dismissSetup();this.$('start-fullscreen').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen();}catch{this.$('start-setup-status').textContent='This page already fills the browser window. Browser fullscreen is unavailable here.';}};document.addEventListener('fullscreenchange',()=>{this.$('start-fullscreen').textContent=document.fullscreenElement?'Exit fullscreen':'⤢ Fullscreen';});
  this.$('start-saved-close').onclick=()=>this.$('start-saved').close();
  this.$('start-file').onclick=()=>this.$('project-file').click();
  this.$('start-setup-form').onsubmit=e=>{e.preventDefault();this.launch();};
  this.$('start-setup-form').oninput=()=>this.summary();this.$('start-setup-form').onchange=e=>{if(e.target.id==='start-units'){const old=this.setupUnit==='m'?1000:304.8,next=e.target.value==='m'?1000:304.8;for(const id of ['start-width','start-depth'])this.$(id).value=Number((Number(this.$(id).value)*old/next).toFixed(5));this.setupUnit=e.target.value;}this.summary();};
  this.$('journey-action').onclick=()=>this.options.next(this.source,this.ai);
  this.$('journey-dismiss').onclick=()=>{this.$('journey-guide').hidden=true;};
 }
 setReady(){this.ready=true;document.querySelectorAll('[data-start]').forEach(b=>b.disabled=false);this.$('start-status').textContent='Ready when you are. Your work stays on this device.';}
 show(){if(!this.ready)return;this.dismissSetup(false);this.options.save();document.body.classList.add('at-start');this.$('start-page').hidden=false;document.querySelector('.workspace').hidden=true;this.options.pause(true);window.scrollTo(0,0);this.$('start-title').focus();}
 enter(){this.$('start-setup').hidden=true;document.body.classList.remove('setting-up','at-start');this.$('start-page').hidden=true;document.querySelector('.workspace').hidden=false;this.options.pause(false);window.scrollTo(0,0);requestAnimationFrame(()=>window.dispatchEvent(new Event('resize')));}
 choose(id){
  if(id==='continue'){this.enter();this.$('project-title').setAttribute('tabindex','-1');this.$('project-title').focus();return;}
  if(id==='samples'||id==='customize'){this.options.samples(id==='customize');return;}
  if(id==='saved'){this.saved();return;}
  this.$('start-setup-form').reset();this.setupUnit='ft';this.selectedInputs=new Set(id==='import'?['dxf']:this.options.compassEnabled()?['plot','compass']:['plot','survey']);
  this.renderInputs();this.summary();this.$('start-page').hidden=true;document.querySelector('.workspace').hidden=true;this.$('start-setup').hidden=false;document.body.classList.add('setting-up');this.options.pause(true);window.scrollTo(0,0);this.$('start-setup-title').focus();
 }
 dismissSetup(focus=true){this.$('start-setup').hidden=true;document.body.classList.remove('setting-up');this.$('start-page').hidden=false;if(focus){window.scrollTo(0,0);document.querySelector('[data-start="new"]').focus();}}
 renderInputs(){
  const enabled=this.options.compassEnabled();
  this.$('start-input-choices').innerHTML=FloorForgeHomeInputs.choices.map(([id,title,copy,icon])=>`<button type="button" data-home-input="${id}" aria-pressed="${this.selectedInputs.has(id)}"${id==='compass'&&!enabled?' disabled':''}><span class="home-input-icon" aria-hidden="true">${icon}</span><span><strong>${title}</strong><small>${id==='compass'&&!enabled?'Compass is unavailable on this server.':copy}</small></span><span class="home-input-check" aria-hidden="true">${this.selectedInputs.has(id)?'✓':'+'}</span></button>`).join('');
  this.$('start-input-choices').querySelectorAll('button').forEach(button=>button.onclick=()=>{const id=button.dataset.homeInput;if(this.selectedInputs.has(id))this.selectedInputs.delete(id);else this.selectedInputs.add(id);this.renderInputs();this.summary();this.$('start-input-choices').querySelector(`[data-home-input="${id}"]`).focus();});
  this.$('start-compass-demo').innerHTML=FloorForgeHomeInputs.preview();
 }
 summary(){
  const inputs=[...(this.selectedInputs||[])],source=FloorForgeHomeInputs.route(inputs,this.options.compassEnabled()),ai=this.$('start-local').checked;
  this.$('start-source').value=source;
  const help={brief:'Begin with a guided brief. Your plot and home preferences guide the plan.',compass:'Start with Compass: arrange rooms with cells, review their geometry, then generate matching 2D and 3D.',dxf:'Import your DXF first. Its dimensions and room geometry are authoritative; a separate Compass map always needs its own review.',sketch:ai?'Use an installed local model to propose an interpretation. No image is sent until you explicitly request it.':'Keep your sketch as a reference and arrange its rooms on Compass. Images are not automatically traced.',text:'Write your requirements in the Ideas section. Review the fields we understood before generating.'};
  this.$('start-source-help').textContent=inputs.length?`${inputs.length} input${inputs.length===1?'':'s'} selected. ${help[source]}`:'Choose at least one starting input.';
  this.$('start-ai-help').textContent=ai?'Requires Ollama and a compatible installed model. Interpretations remain proposals for you to review.':'The Python planner, Compass and DXF import work without AI.';
  this.$('start-assistance').hidden=!inputs.includes('sketch');
  const w=Number(this.$('start-width').value),d=Number(this.$('start-depth').value),factor=this.$('start-units').value==='m'?1000:304.8;
  this.$('start-dimensions-note').textContent=w>0&&d>0?`${(w*factor/1000).toFixed(2)} × ${(d*factor/1000).toFixed(2)} m · the road runs along the width.`:'Width follows the road. Depth goes from front to back.';
 }
 async launch(){
  const button=this.$('start-launch');button.disabled=true;this.$('start-setup-status').textContent='';
  try{
   const inputs=[...this.selectedInputs];if(!inputs.length)throw Error('Choose at least one starting input.');
   this.source=FloorForgeHomeInputs.route(inputs,this.options.compassEnabled());this.ai=inputs.includes('sketch')&&this.$('start-local').checked;
   const dimensions=FloorForgeHomeInputs.dimensions(Number(this.$('start-width').value),Number(this.$('start-depth').value),this.$('start-units').value);
   await this.options.create({title:this.$('start-name').value.trim()||'My new home',...dimensions,storeys:Number(this.$('start-floors').value),bearing:Number(this.$('start-bearing').value),context:this.$('start-context').value,ai:this.ai,source:this.source,inputs});
   this.enter();this.$('journey-guide').hidden=false;
   this.$('journey-title').textContent='Your custom design';
   const inputNames=FloorForgeHomeInputs.choices.filter(([id])=>inputs.includes(id)).map(([,title])=>title).join(', ');this.$('journey-copy').textContent='Your inputs: '+inputNames+'. '+(this.source==='dxf'?'Import your prepared drawing, then refine its exact rooms. Your other inputs can be added alongside it.':this.source==='sketch'?'Add your sketch as a reference, then arrange its rooms on Compass.':this.source==='text'?'Write your requirements in Ideas, then review the fields we understood before generating.':this.source==='brief'?'Your plot is ready. Choose your home requirements, then review the resolved inputs before generating.':'Your plot is ready. Choose room requirements on the left, then arrange them on Compass.');
   this.$('journey-action').hidden=this.source==='compass';this.$('journey-action').textContent=this.source==='dxf'?'Import my 2D plan':this.source==='compass'?'Open Compass map':this.source==='sketch'?'Add my sketch':this.source==='text'?'Add my description':'Choose home requirements';
   if(this.source==='compass')this.$('compass-open').focus();else this.$('journey-action').focus();
  }catch(e){this.$('start-setup-status').textContent=e.message;}finally{button.disabled=false;}
 }
 saved(){
  const list=this.$('start-saved-list');list.replaceChildren();
  for(const [id,item]of Object.entries(this.options.saved()).sort((a,b)=>(b[1].savedAt||'').localeCompare(a[1].savedAt||''))){
   const b=document.createElement('button');b.type='button';b.className='start-saved-item';const title=document.createElement('strong'),date=document.createElement('span');title.textContent=item.title;date.textContent=item.savedAt?'Saved '+new Date(item.savedAt).toLocaleDateString():'Saved on this device';b.append(title,date);
   b.onclick=async()=>{b.disabled=true;try{if(await this.options.restore(id)){this.$('start-saved').close();this.enter();}}finally{b.disabled=false;}};list.append(b);
  }
  if(!list.children.length)list.textContent='No saved projects yet. Your current workspace is available from Continue.';
  this.$('start-saved').showModal();
 }
}
