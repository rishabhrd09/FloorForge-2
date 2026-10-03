/* Optional proposal workflow. Never changes a draft until the editor's Yes. */
'use strict';
window.FloorForgePlanAssistance=class {
  constructor({editor,project,request,revision}) {
    Object.assign(this,{editor,project,request,revision});this.busy=false;this.serial=0;
    this.$=id=>document.getElementById('plan-help-'+id);this.dialog=this.$('dialog');
    document.getElementById('plan-explore').onclick=()=>this.open();
    this.$('close').onclick=()=>this.dialog.close();
    this.dialog.addEventListener('input',()=>{this.serial++;this.$('results').replaceChildren();});
    this.dialog.addEventListener('close',()=>this.serial++);
    this.$('search').onclick=()=>this.run(false);this.$('ask').onclick=()=>this.run(true);
    this.$('discover').onclick=async()=>{try{const r=await request('/api/local-plan/models',{});this.$('models').replaceChildren(...r.models.map(m=>{const o=document.createElement('option');o.value=m.name;return o;}));this.$('status').textContent=r.models.length?`Installed: ${r.models.map(m=>m.name).join(', ')}`:'No local models found. Install qwen3.5:9b in Ollama first.';}catch(e){this.$('status').textContent=e.message;}};
  }
  open(){
    if(this.editor.preparing||this.editor.fitProposal)return;
    this.serial++;this.$('scale').checked=false;this.$('results').replaceChildren();this.$('status').textContent='Your current draft stays saved while you explore.';
    const [w,d]=this.editor.getEnvelope();this.$('site').textContent=`Buildable area: ${(w/1000).toFixed(2)} × ${(d/1000).toFixed(2)} m · ${this.editor.floor===0?'Ground floor':'Floor '+this.editor.floor}. Plot dimensions and setbacks are set on the home screen.`;
    this.$('locks').replaceChildren();for(const r of this.editor.active.rooms){const label=document.createElement('label'),c=document.createElement('input');c.type='checkbox';c.value=r.id;label.append(c,document.createTextNode(' '+r.name));this.$('locks').append(label);}
    this.dialog.showModal();
  }
  async images(){
    const files=[...this.$('images').files];if(files.length>2)throw Error('Attach up to two PNG or JPEG images.');
    return Promise.all(files.map(async file=>{
      if(!['image/png','image/jpeg'].includes(file.type)||file.size>12000000)throw Error('Use PNG/JPEG files under 12 MB.');
      const bitmap=await createImageBitmap(file),scale=Math.min(1,1400/Math.max(bitmap.width,bitmap.height)),canvas=document.createElement('canvas');
      canvas.width=Math.round(bitmap.width*scale);canvas.height=Math.round(bitmap.height*scale);const ctx=canvas.getContext('2d');ctx.fillStyle='white';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.drawImage(bitmap,0,0,canvas.width,canvas.height);bitmap.close();
      const data=canvas.toDataURL('image/jpeg',.82).split(',')[1];if(data.length>800000)throw Error('This drawing is too detailed to send. Use a smaller or more tightly cropped image.');return data;
    }));
  }
  async run(local){
    if(this.busy)return;this.busy=true;for(const id of ['search','ask'])this.$(id).disabled=true;
    const e=this.editor,before=e.snapshot(),revision=this.revision(),inputSerial=e.inputSerial,serial=this.serial;
    this.$('results').replaceChildren();this.$('status').textContent=local?'Interpreting locally, then checking geometry…':'Searching connected layouts and checking access…';
    const current=()=>this.dialog.open&&before===e.snapshot()&&revision===this.revision()&&inputSerial===e.inputSerial&&serial===this.serial;
    try{
      const body={project:this.project(),floor:e.floor,lockedIds:[...this.$('locks').querySelectorAll('input:checked')].map(c=>c.value)};
      if(local)Object.assign(body,{instruction:this.$('instruction').value,model:this.$('model').value,images:await this.images(),dimensionsConfirmed:this.$('scale').checked,confirm:true});
      if(!current())return;
      const result=await this.request(local?'/api/local-plan/propose':'/api/plan/alternatives',body);
      if(!current()){if(this.dialog.open)this.$('status').textContent='The draft or request changed. Run again to use the latest version.';return;}
      this.$('status').textContent=result.message;
      const out=this.$('results'),text=(tag,value)=>{const n=document.createElement(tag);n.textContent=value;out.append(n);};
      if(result.rationale)text('p',result.rationale);
      for(const q of result.questions||[])text('p','Please clarify: '+q);
      for(const err of (result.errors||[]).slice(0,4))text('p',err.message||err.code);
      for(const option of result.alternatives||[]){
        if(!option.valid)continue;
        const article=document.createElement('article');article.className='plan-help-option';const h=document.createElement('h4');h.textContent=option.label;article.append(h);
        article.append(this.miniPlan(option.customPlan.floors[e.floor]));
        const p=document.createElement('p');p.textContent=`${option.customPlan.floors[e.floor].rooms.length} rooms · geometry and access checked`;article.append(p);
        const b=document.createElement('button');b.type='button';b.className='secondary';b.textContent='Review this layout';
        b.onclick=()=>{if(!current()){this.$('status').textContent='The draft or request changed. Search again.';return;}
          this.dialog.close();e.fitProposal={before,revision,inputSerial,result:option,preview:false};document.getElementById('plan-fit-choice').hidden=false;
          document.getElementById('plan-fit-summary').textContent=option.strategy==='local-edit'?'Review the requested room edit. Yes applies it; Undo restores your previous plan.':'Rooms have been rearranged around connected circulation. Compare the dashed outlines; Yes applies this option and Undo restores your sketch.';
          const ul=document.getElementById('plan-fit-changes');ul.replaceChildren();for(const change of option.changes){const li=document.createElement('li');li.textContent=change.message;ul.append(li);}e.render();};
        article.append(b);out.append(article);
      }
    }catch(error){if(this.dialog.open)this.$('status').textContent=error.message;}
    finally{this.busy=false;for(const id of ['search','ask'])this.$(id).disabled=false;}
  }
  miniPlan(floor){
    const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg'),[w,d]=this.editor.getEnvelope();svg.setAttribute('viewBox',`0 0 ${w} ${d}`);svg.setAttribute('role','img');svg.setAttribute('aria-label','Proposed room arrangement; front at bottom');
    for(const r of floor.rooms){const poly=document.createElementNS(ns,'polygon');poly.setAttribute('points',r.polygon.map(([x,y])=>`${x},${d-y}`).join(' '));poly.setAttribute('fill',this.editor.registry[r.kind]?.color||'#ddd');poly.setAttribute('stroke','#687768');poly.setAttribute('stroke-width','30');svg.append(poly);const b=this.editor.bounds(r),label=document.createElementNS(ns,'text');label.setAttribute('x',(b[0]+b[2])/2);label.setAttribute('y',d-(b[1]+b[3])/2);label.setAttribute('text-anchor','middle');label.setAttribute('font-size',Math.max(w,d)/35);label.textContent=r.name;svg.append(label);}
    return svg;
  }
};
