/* One project, linked views; local checkpoints keep edits while switching homes. */
'use strict';
class FloorForgeProjectWorkspace {
 constructor(options){this.options=options;this.$=id=>document.getElementById(id);this.busy=false;this.active=localStorage.getItem('floorforge-workspace-id')||'current-project';
  try{this.saved=JSON.parse(localStorage.getItem('floorforge-saved-projects')||'{}');}catch{this.saved={};}
  this.$('workspace-project').onchange=e=>this.switch(e.target.value);
  document.querySelectorAll('[data-project-view]').forEach(b=>b.onclick=()=>this.options.view(b.dataset.projectView));
 }
 async init(){this.samples=(await this.options.catalogue()).samples;this.render();}
 render(){const select=this.$('workspace-project');select.replaceChildren();let group=document.createElement('optgroup');group.label='Your saved projects';
  for(const [id,item] of Object.entries(this.saved)){let opt=new Option(item.title,id);group.append(opt);}if(!this.saved[this.active])group.append(new Option(this.options.title(),this.active));select.append(group);
  group=document.createElement('optgroup');group.label='Sample projects';for(const s of this.samples||[])group.append(new Option(s.title,'sample:'+s.id));select.append(group);select.value=this.active;
 }
 save(){const snapshot=this.options.snapshot();this.saved[this.active]={...snapshot,title:snapshot.project.brief.title||this.options.title(),savedAt:new Date().toISOString()};localStorage.setItem('floorforge-saved-projects',JSON.stringify(this.saved));localStorage.setItem('floorforge-workspace-id',this.active);this.render();return this.active;}
 adopted(slug){const base='working:'+slug;this.active=this.saved[base]?base+':'+crypto.randomUUID():base;this.save();}
 async switch(id){if(this.busy)return;this.busy=true;this.$('workspace-project').disabled=true;const previous=this.active;
  try{this.save();if(id.startsWith('sample:')){await this.options.use(this.samples.find(s=>s.id===id.slice(7)));}else{const item=this.saved[id];if(!item)throw Error('This saved project is unavailable.');await this.options.restore(item);this.active=id;localStorage.setItem('floorforge-workspace-id',id);this.render();}return true;}
  catch(e){this.active=previous;this.render();this.options.error(e);return false;}finally{this.busy=false;this.$('workspace-project').disabled=false;}
 }
}
