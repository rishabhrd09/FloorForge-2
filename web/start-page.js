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
  this.$('start-setup-close').onclick=()=>this.$('start-setup').close();
  this.$('start-saved-close').onclick=()=>this.$('start-saved').close();
  this.$('start-file').onclick=()=>this.$('project-file').click();
  this.$('start-setup-form').onsubmit=e=>{e.preventDefault();this.launch();};
  this.$('start-setup-form').onchange=()=>this.summary();
  this.$('journey-action').onclick=()=>this.options.next(this.source,this.ai);
  this.$('journey-dismiss').onclick=()=>{this.$('journey-guide').hidden=true;};
 }
 setReady(){this.ready=true;document.querySelectorAll('[data-start]').forEach(b=>b.disabled=false);this.$('start-status').textContent='Ready when you are. Your work stays on this device.';}
 show(){if(!this.ready)return;this.options.save();document.body.classList.add('at-start');this.$('start-page').hidden=false;document.querySelector('.workspace').hidden=true;this.options.pause(true);window.scrollTo(0,0);this.$('start-title').focus();}
 enter(){document.body.classList.remove('at-start');this.$('start-page').hidden=true;document.querySelector('.workspace').hidden=false;this.options.pause(false);requestAnimationFrame(()=>window.dispatchEvent(new Event('resize')));}
 choose(id){
  if(id==='continue'){this.enter();this.$('project-title').setAttribute('tabindex','-1');this.$('project-title').focus();return;}
  if(id==='samples'||id==='customize'){this.options.samples(id==='customize');return;}
  if(id==='saved'){this.saved();return;}
  this.$('start-setup-form').reset();this.$('start-source').value=id==='import'?'dxf':'brief';this.summary();this.$('start-setup').showModal();
 }
 summary(){
  const source=this.$('start-source').value,ai=this.$('start-local').checked;
  const help={brief:'Set your plot and room requirements. Python generates the plan; you can review the 2D layout before exploring 3D.',editor:'Place rooms roughly, then use Smart fit to review a usable arrangement. You stay in control of every proposal.',dxf:'Use a single ground-floor ASCII DXF with FloorForge layers and units. The import screen includes a template and exact requirements. File dimensions replace the starting plot size.',sketch:ai?'Attach up to two PNG or JPEG sketches in the local assistant. Confirm the plot and review its interpretation before applying a proposal.':'Open the room editor and recreate your sketch by placing rooms. Automatic image interpretation requires the optional local assistant.',mixed:'Begin with plot dimensions and a room arrangement. Add your description and references in the workspace; review which sources are used before generating. Images are interpreted only when explicitly sent to local AI.'};
  this.$('start-source-help').textContent=help[source];
  this.$('start-ai-help').textContent=ai?'Local AI is selected. Ollama and a compatible installed model are required. Nothing is sent until you explicitly ask; Python tools remain available.':'AI is off for this new project. Room editing, Smart fit, DXF import and 3D generation work without a model.';
  this.$('start-plot-fields').hidden=source==='dxf';
 }
 async launch(){
  const button=this.$('start-launch');button.disabled=true;this.$('start-setup-status').textContent='';
  try{
   this.source=this.$('start-source').value;this.ai=this.$('start-local').checked;
   await this.options.create({title:this.$('start-name').value.trim()||'My new home',width:Number(this.$('start-width').value),depth:Number(this.$('start-depth').value),storeys:Number(this.$('start-floors').value),ai:this.ai,source:this.source});
   this.enter();this.$('start-setup').close();this.$('journey-guide').hidden=false;
   this.$('journey-title').textContent=this.ai?'Your new home · local assistance available':'Your new home · no AI required';
   this.$('journey-copy').textContent=this.source==='dxf'?'Choose your prepared drawing. Review the import requirements before uploading.':'Confirm your plot, road direction and setbacks in the left panel. Then open your chosen tool below. Generate when your draft is ready.';
   this.$('journey-action').textContent=this.source==='dxf'?'Import my DXF':this.ai?'Open local planning assistant':this.source==='brief'?'Set my home requirements':'Open room planner';
   if(this.source==='dxf')this.options.next(this.source,this.ai);else this.$('journey-action').focus();
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
