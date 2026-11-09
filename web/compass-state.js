/* Pure Compass transactions. Whole cells remain one target, even after division. */
'use strict';
const CompassState = (() => {
 const clone = value => JSON.parse(JSON.stringify(value));
 // New-map choices come from the server's shared grid registry. Legacy shapes
 // stay readable even if they are no longer offered for a new draft.
 const gridShapes=new Set(['4x4','4x6','4x8']);
 const configureGrids=shapes=>{for(const {cols,rows} of shapes)gridShapes.add(`${cols}x${rows}`);};
 function validateGrid(grid){if(!grid||!Number.isInteger(grid.rows)||!Number.isInteger(grid.cols)||!gridShapes.has(`${grid.cols}x${grid.rows}`)||grid.basis!=='buildable-envelope'||grid.rowOrigin!=='front')throw Error('Choose a supported Compass grid.');}
 const key = (row,col,half) => `${row}:${col}${half?':'+half:''}`;
 const splitHalves=(floor,base)=>floor.horizontalSplits?.includes(base)?['F','B']:floor.splits.includes(base)?['L','R']:[];
 const micro = refs => new Set(refs.flatMap(ref=>{const [r,c,h]=ref.split(':'),points=[];for(let y=0;y<2;y++)for(let x=0;x<2;x++)if((!['L','R'].includes(h)||h===['L','R'][x])&&(!['F','B'].includes(h)||h===['F','B'][y]))points.push(`${2*Number(r)+y}:${2*Number(c)+x}`);return points;}));
 function connected(refs){const todo=micro(refs);if(!todo.size)return true;const pending=[todo.values().next().value];todo.delete(pending[0]);while(pending.length){const [r,c]=pending.pop().split(':').map(Number);for(const [y,x]of [[r-1,c],[r+1,c],[r,c-1],[r,c+1]]){const k=`${y}:${x}`;if(todo.delete(k))pending.push(k);}}return !todo.size;}
 function validate(draft){
  validateGrid(draft.grid);const modern=draft.schema==='floorforge.compass-input/2';
  if(!modern&&draft.schema!=='floorforge.compass-input/1')throw Error('Unsupported Compass version.');
  if('programme' in draft&&(!modern||draft.programme!=='drawn'))throw Error('Drawn-room generation requires Compass version 2.');
  const validRef=ref=>typeof ref==='string'&&/^(0|[1-9]\d*):(0|[1-9]\d*)(?::[LRFB])?$/.test(ref)&&Number(ref.split(':')[0])<draft.grid.rows&&Number(ref.split(':')[1])<draft.grid.cols;
  const owned=new Set();
  for(const floor of draft.floors){
   const refs=[...(floor.splits||[]),...(floor.horizontalSplits||[])];
   if(!Array.isArray(floor.splits)||('horizontalSplits' in floor&&(!modern||!Array.isArray(floor.horizontalSplits)))||new Set(refs).size!==refs.length||refs.some(ref=>!validRef(ref)||ref.split(':').length!==2))throw Error('A divided cell must have one direction inside this floor’s grid.');
  }
  for(const r of draft.rooms){
   const floor=draft.floors.find(f=>f.id===r.floorId);if(!floor)throw Error('Choose an existing floor.');
   for(const ref of r.regions){const [row,col,half]=ref.split(':'),halves=splitHalves(floor,`${row}:${col}`);if(!validRef(ref)||(half?!halves.includes(half):halves.length))throw Error('A room region must match this floor’s whole or divided cells.');}
   if(!connected(r.regions))throw Error(`${r.name} would become disconnected. Keep the bridge, choose an adjoining region, or add a separate room.`);
   const pixels=r.regions.flatMap(ref=>[...micro([ref])]);for(const ref of pixels){const k=r.floorId+':'+ref;if(owned.has(k))throw Error('A region already belongs to another room.');owned.add(k);}
  }return draft;
 }
 function drawnDraft(draft){const next=clone(draft);next.schema='floorforge.compass-input/2';next.programme='drawn';return validate(next);}
 function create(brief,registry){const floors=Array.from({length:brief.storeys},(_,i)=>({id:`compass-floor-${i}`,splits:[]})),rooms=[];let seq=0;
  const add=(kind,name,floor=0,role)=>rooms.push({id:`compass-room-${++seq}`,kind,name,floorId:floors[floor].id,regions:[],required:true,...(role?{role}:{})});
  add('living','Living');add('kitchen','Kitchen');for(let i=0;i<brief.bedrooms;i++)add('bedroom',i===0?'Master bedroom':`Bedroom ${i+1}`,Math.min(floors.length-1,Math.floor(i*floors.length/Math.max(1,brief.bedrooms))),i===0?'master':undefined);
  return {schema:'floorforge.compass-input/1',grid:{rows:4,cols:4,basis:'buildable-envelope',rowOrigin:'front'},floors,rooms,connections:[],stairLinks:[],site:{context:'unknown',gate:'planner',zones:[]},requirements:[]};
 }
 const roomGuides={
  'drawing-room':['Living & gathering','Guest seating and sofa furniture.'],living:['Living & gathering','Everyday seating and lounge furniture.'],family:['Living & gathering','Family seating and lounge furniture.'],dining:['Living & gathering','Dining table, chairs and daylight checks.'],
  bedroom:['Private rooms','Bed and storage; counts towards your bedrooms.'],'care-room':['Private rooms','Care furniture with a larger clear room minimum.'],study:['Private rooms','Desk and workspace furniture.'],pooja:['Private rooms','Prayer space with an altar.'],
  kitchen:['Kitchen & services','Cooking counters and appliances.'],utility:['Kitchen & services','Laundry and service fittings.'],'drying-room':['Kitchen & services','Enclosed laundry with ventilation and drainage.'],store:['Kitchen & services','Storage shelving.'],dress:['Kitchen & services','Wardrobe and dressing storage.'],
  bathroom:['Bath & wash','WC, washbasin and shower where space permits.'],'powder-room':['Bath & wash','WC and washbasin without a shower.'],
  veranda:['Outdoor spaces','Covered outdoor space with open sides.'],balcony:['Outdoor spaces','Open-air deck; upper-floor edges receive guards.'],terrace:['Outdoor spaces','Open-air terrace without a roof above.'],courtyard:['Outdoor spaces','Open-air court that stays clear of upper floors.'],'drying-yard':['Outdoor spaces','Outdoor drying space, open to the sky.'],
  foyer:['Entrances & routes','Enclosed arrival and circulation space.'],'outer-lobby':['Entrances & routes','Covered, open-sided arrival space.'],'inner-lobby':['Entrances & routes','Enclosed circulation between rooms.'],hall:['Entrances & routes','Clear circulation route between rooms.'],
  stair:['Stairs & openings','Link matching stair rooms to create real flights.'],'stair-landing':['Stairs & openings','Circulation landing; does not create a stair flight.'],void:['Stairs & openings','Upper-floor opening with no floor slab.'],'lift-shaft':['Stairs & openings','Lift design is unavailable in Compass.']
 };
 function catalogue(registry,query=''){const search=query.trim().toLowerCase(),groups=[...new Set(Object.values(roomGuides).map(r=>r[0])),'Other spaces'];return Object.entries(registry).map(([kind,spec])=>({kind,...spec,group:roomGuides[kind]?.[0]||'Other spaces',description:roomGuides[kind]?.[1]||'Uses this space type’s shared design rules.'})).filter(r=>!search||`${r.label} ${r.kind} ${r.group} ${r.description}`.toLowerCase().includes(search)).sort((a,b)=>groups.indexOf(a.group)-groups.indexOf(b.group)||a.label.localeCompare(b.label));}
 function roomUnavailable(kind,floor){return kind==='lift-shaft'?'Lift design is unavailable in Compass.':kind==='void'&&floor===0?'Place a double-height void on the floor above the room it opens into.':'';}
 function restoreForAdapter(project,adapterVersion){
  const active=!!project.compass||project.editorState?.mode==='compass',draft=project.compass||project.editorState?.compassDraft,acceptance=project.compassAcceptance||project.editorState?.compassAcceptance;
  if(!active||!draft||!acceptance||!adapterVersion||acceptance.adapterVersion===adapterVersion)return {project,reviewRequired:false};
  const next={...project,editorState:{...project.editorState,mode:'compass',compassDraft:clone(draft),compassScope:project.compassScope||project.editorState?.compassScope||project.brief?.storeys||1}};
  for(const key of ['compass','compassScope','compassAcceptance'])delete next[key];delete next.editorState.compassAcceptance;
  return {project:next,reviewRequired:true};
 }
 function addRoom(draft,registry,floorId,kind,id,name=''){
  const floor=draft.floors.findIndex(f=>f.id===floorId),spec=registry[kind];if(floor<0||!spec)throw Error('Choose a room type and an existing floor.');
  const unavailable=roomUnavailable(kind,floor);if(unavailable)throw Error(unavailable);
  if(draft.rooms.filter(r=>r.floorId===floorId).length>=120)throw Error('Keep at most 120 rooms on each floor.');
  if(!id||draft.rooms.some(r=>r.id===id))throw Error('Give the new room its own identity.');
  const next=clone(draft),taken=new Set(next.rooms.map(r=>r.name));let label=name.trim()||spec.label;
  if(!name.trim()){let suffix=next.rooms.filter(r=>r.kind===kind).length+1;if(next.rooms.some(r=>r.kind===kind)||taken.has(label))label=`${spec.label} ${suffix++}`;while(taken.has(label))label=`${spec.label} ${suffix++}`;}
  if(label.length>120)throw Error('Keep room names within 120 characters.');
  next.rooms.push({id,kind,name:label,floorId,regions:[],required:true});return validate(next);
 }
 function owner(draft,floorId,ref){return draft.rooms.find(r=>r.floorId===floorId&&r.regions.includes(ref));}
 function assign(draft,floorId,ref,roomId,{replace=false}={}){const next=clone(draft),recipient=roomId?next.rooms.find(r=>r.id===roomId&&r.floorId===floorId):null,donor=owner(next,floorId,ref);if(roomId&&!recipient)throw Error('Choose a room on this floor.');if(donor&&recipient&&donor.id!==roomId&&!replace)return {confirmation:{roomId:donor.id,message:`Replace ${donor.name} here?${donor.regions.length===1?' It will become unplaced and stay in your checklist.':''}`}};
  if(donor?.id===roomId)return {draft:next};
  if(donor)donor.regions=donor.regions.filter(x=>x!==ref);if(recipient)recipient.regions.push(ref);validate(next);return {draft:next};
 }
 function splitAssign(draft,floorId,row,col,half,roomId,options={}){
  if(!['L','R','F','B'].includes(half))throw Error('Choose a left, right, front or back half.');
  const next=clone(draft),floor=next.floors.find(f=>f.id===floorId),base=key(row,col);if(!floor)throw Error('Choose an existing floor.');
  const desired=['F','B'].includes(half)?['F','B']:['L','R'],previous=splitHalves(floor,base);
  if(!previous.includes(half)){
   const owners=(previous.length?previous:[null]).map(h=>owner(next,floorId,key(row,col,h))?.id||null),uniform=owners.every(id=>id===owners[0]);
   if(!uniform&&!options.replace)return {confirmation:{message:'Change the split direction? Both existing halves will be cleared, then your chosen half will be assigned. Other room placements must stay connected.'}};
   for(const r of next.rooms)if(r.floorId===floorId)r.regions=r.regions.filter(ref=>ref!==base&&!['L','R','F','B'].some(h=>ref===key(row,col,h)));
   floor.splits=floor.splits.filter(ref=>ref!==base);if(floor.horizontalSplits)floor.horizontalSplits=floor.horizontalSplits.filter(ref=>ref!==base);
   if(desired[0]==='F'){next.schema='floorforge.compass-input/2';(floor.horizontalSplits||=[]).push(base);}else floor.splits.push(base);
   if(uniform&&owners[0])next.rooms.find(r=>r.id===owners[0]).regions.push(...desired.map(h=>key(row,col,h)));
  }
  return assign(next,floorId,key(row,col,half),roomId,options);
 }
 function whole(draft,floorId,row,col,roomId){
  const next=clone(draft),floor=next.floors.find(f=>f.id===floorId);for(const r of next.rooms)if(r.floorId===floorId)r.regions=r.regions.filter(ref=>ref!==key(row,col)&&!['L','R','F','B'].some(h=>ref===key(row,col,h)));
  floor.splits=floor.splits.filter(ref=>ref!==key(row,col));if(floor.horizontalSplits)floor.horizontalSplits=floor.horizontalSplits.filter(ref=>ref!==key(row,col));
  if(roomId){const r=next.rooms.find(r=>r.id===roomId&&r.floorId===floorId);if(!r)throw Error('Choose the whole-cell owner.');r.regions.push(key(row,col));}return validate(next);
 }
 function allocate(draft,floorId,{row,col,half=null},roomId,{replace=false}={}){
  const floor=draft.floors.find(f=>f.id===floorId);
  if(!floor||!Number.isInteger(row)||row<0||row>=draft.grid.rows||!Number.isInteger(col)||col<0||col>=draft.grid.cols||![null,'L','R','F','B'].includes(half))throw Error('Choose an existing cell or half.');
  if(half)return splitAssign(draft,floorId,row,col,half,roomId,{replace});
  const halves=splitHalves(floor,key(row,col));if(!halves.length)return assign(draft,floorId,key(row,col),roomId,{replace});
  const donors=draft.rooms.filter(r=>r.floorId===floorId&&r.id!==roomId&&halves.some(h=>r.regions.includes(key(row,col,h))));
  if(donors.length&&!replace)return {confirmation:{message:`Replace ${donors.map(r=>r.name).join(' and ')} in the whole cell? Their remaining regions must stay connected.`}};
  return {draft:whole(draft,floorId,row,col,roomId)};
 }
 function addAndAllocate(draft,registry,floorId,kind,id,target,options={}){
  return allocate(addRoom(draft,registry,floorId,kind,id),floorId,target,id,options);
 }
 function moveRoom(draft,roomId,floorId){const next=clone(draft),room=next.rooms.find(r=>r.id===roomId);if(!room||!next.floors.some(f=>f.id===floorId))throw Error('Choose an existing room and floor.');if(room.floorId===floorId)return next;room.floorId=floorId;room.regions=[];next.connections=next.connections.filter(c=>c.from!==roomId&&c.to!==roomId);next.stairLinks=next.stairLinks.filter(s=>!s.roomIds.includes(roomId));if(next.site.entryRoomId===roomId)delete next.site.entryRoomId;return validate(next);}
 // Presentation only: place a label inside an owned rectangle, including half cells.
 function labelRect(regions,rows,ratio=1,cols=4){
  const owned=micro(regions);let best=null;
  for(let left=0;left<2*cols;left++)for(let right=left;right<2*cols;right++){
   let start=0;
   for(let row=0;row<=2*rows;row++){
    if(row<2*rows&&Array.from({length:right-left+1},(_,i)=>owned.has(`${row}:${left+i}`)).every(Boolean))continue;
    const width=right-left+1,height=row-start,area=width*height,score=Math.min(width/(2*cols)*ratio,height/(2*rows));
    if(height&&(!best||score>best.score||score===best.score&&area>best.area))best={left,bottom:start,width,height,area,score};
    start=row+1;
   }
  }
  return best;
 }
 class History {
  constructor(draft){this.value=clone(draft);this.past=[];this.future=[];}
  commit(next){validate(next);if(JSON.stringify(next)===JSON.stringify(this.value))return false;this.past.push(clone(this.value));if(this.past.length>100)this.past.shift();this.value=clone(next);this.future=[];return true;}
  undo(){if(!this.past.length)return false;this.future.push(this.value);this.value=this.past.pop();return true;}
  redo(){if(!this.future.length)return false;this.past.push(this.value);this.value=this.future.pop();return true;}
 }
 return {clone,key,splitHalves,drawnDraft,micro,connected,validate,configureGrids,create,catalogue,roomUnavailable,restoreForAdapter,addRoom,owner,assign,splitAssign,whole,allocate,addAndAllocate,moveRoom,labelRect,History};
})();
if(typeof module!=='undefined')module.exports=CompassState;
