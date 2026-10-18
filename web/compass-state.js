/* Pure Compass transactions. Whole cells remain one target, even after division. */
'use strict';
const CompassState = (() => {
 const clone = value => JSON.parse(JSON.stringify(value));
 const key = (row,col,half) => `${row}:${col}${half?':'+half:''}`;
 const micro = refs => new Set(refs.flatMap(ref=>{const [r,c,h]=ref.split(':');return (h?[h]:['L','R']).map(s=>`${r}:${2*Number(c)+(s==='R'?1:0)}`);}));
 function connected(refs){const todo=micro(refs);if(!todo.size)return true;const pending=[todo.values().next().value];todo.delete(pending[0]);while(pending.length){const [r,c]=pending.pop().split(':').map(Number);for(const [y,x]of [[r-1,c],[r+1,c],[r,c-1],[r,c+1]]){const k=`${y}:${x}`;if(todo.delete(k))pending.push(k);}}return !todo.size;}
 function validate(draft){const owned=new Set();for(const r of draft.rooms){const floor=draft.floors.find(f=>f.id===r.floorId);if(!floor)throw Error('Choose an existing floor.');if(!connected(r.regions))throw Error(`${r.name} would become disconnected. Keep the bridge, choose an adjoining region, or add a separate room.`);for(const ref of r.regions){const [row,col,half]=ref.split(':');if(!/^[0-7]:[0-3](?::[LR])?$/.test(ref)||Number(row)>=draft.grid.rows||floor.splits.includes(`${row}:${col}`)!==!!half)throw Error('A room region must match this floor’s whole or divided cells.');}for(const ref of micro(r.regions)){const k=r.floorId+':'+ref;if(owned.has(k))throw Error('A region already belongs to another room.');owned.add(k);}}return draft;}
 function create(brief,registry){const floors=Array.from({length:brief.storeys},(_,i)=>({id:`compass-floor-${i}`,splits:[]})),rooms=[];let seq=0;
  const add=(kind,name,floor=0,role)=>rooms.push({id:`compass-room-${++seq}`,kind,name,floorId:floors[floor].id,regions:[],required:true,...(role?{role}:{})});
  add('living','Living');add('kitchen','Kitchen');for(let i=0;i<brief.bedrooms;i++)add('bedroom',i===0?'Master bedroom':`Bedroom ${i+1}`,Math.min(floors.length-1,Math.floor(i*floors.length/Math.max(1,brief.bedrooms))),i===0?'master':undefined);
  return {schema:'floorforge.compass-input/1',grid:{rows:4,cols:4,basis:'buildable-envelope',rowOrigin:'front'},floors,rooms,connections:[],stairLinks:[],site:{context:'unknown',gate:'planner',zones:[]},requirements:[]};
 }
 function owner(draft,floorId,ref){return draft.rooms.find(r=>r.floorId===floorId&&r.regions.includes(ref));}
 function assign(draft,floorId,ref,roomId,{replace=false}={}){const next=clone(draft),recipient=roomId?next.rooms.find(r=>r.id===roomId&&r.floorId===floorId):null,donor=owner(next,floorId,ref);if(roomId&&!recipient)throw Error('Choose a room on this floor.');if(donor&&recipient&&donor.id!==roomId&&!replace)return {confirmation:{roomId:donor.id,message:`Replace ${donor.name} here?${donor.regions.length===1?' It will become unplaced and stay in your checklist.':''}`}};
  if(donor?.id===roomId)return {draft:next};
  if(donor)donor.regions=donor.regions.filter(x=>x!==ref);if(recipient)recipient.regions.push(ref);validate(next);return {draft:next};
 }
 function splitAssign(draft,floorId,row,col,half,roomId,options={}){const next=clone(draft),floor=next.floors.find(f=>f.id===floorId),whole=key(row,col);if(!floor.splits.includes(whole)){const donor=owner(next,floorId,whole);floor.splits.push(whole);if(donor)donor.regions=donor.regions.filter(x=>x!==whole).concat(key(row,col,'L'),key(row,col,'R'));}return assign(next,floorId,key(row,col,half),roomId,options);}
 function whole(draft,floorId,row,col,roomId){const next=clone(draft),floor=next.floors.find(f=>f.id===floorId);for(const r of next.rooms)if(r.floorId===floorId)r.regions=r.regions.filter(ref=>ref!==key(row,col,'L')&&ref!==key(row,col,'R'));floor.splits=floor.splits.filter(ref=>ref!==key(row,col));if(roomId){const r=next.rooms.find(r=>r.id===roomId&&r.floorId===floorId);if(!r)throw Error('Choose the whole-cell owner.');r.regions.push(key(row,col));}return validate(next);}
 function moveRoom(draft,roomId,floorId){const next=clone(draft),room=next.rooms.find(r=>r.id===roomId);if(!room||!next.floors.some(f=>f.id===floorId))throw Error('Choose an existing room and floor.');if(room.floorId===floorId)return next;room.floorId=floorId;room.regions=[];next.connections=next.connections.filter(c=>c.from!==roomId&&c.to!==roomId);next.stairLinks=next.stairLinks.filter(s=>!s.roomIds.includes(roomId));if(next.site.entryRoomId===roomId)delete next.site.entryRoomId;return validate(next);}
 class History {
  constructor(draft){this.value=clone(draft);this.past=[];this.future=[];}
  commit(next){validate(next);if(JSON.stringify(next)===JSON.stringify(this.value))return false;this.past.push(clone(this.value));if(this.past.length>100)this.past.shift();this.value=clone(next);this.future=[];return true;}
  undo(){if(!this.past.length)return false;this.future.push(this.value);this.value=this.past.pop();return true;}
  redo(){if(!this.future.length)return false;this.past.push(this.value);this.value=this.future.pop();return true;}
 }
 return {clone,key,micro,connected,validate,create,owner,assign,splitAssign,whole,moveRoom,History};
})();
if(typeof module!=='undefined')module.exports=CompassState;
