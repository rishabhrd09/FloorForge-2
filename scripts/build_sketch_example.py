"""Build the screenshot-derived worked example without replacing the default demo."""
import copy,json,tempfile,shutil
from pathlib import Path
from shapely.geometry import Polygon,box
from floorforge.smart_fit import smart_fit
from floorforge.upper_floor import starter
from floorforge.plan_assist import prepare_plan
from floorforge.pipeline import run
ROOT=Path(__file__).resolve().parents[1]
def main():
    original=json.loads((ROOT/'examples/custom/your-sketch-original.floorforge.json').read_text())
    fitted=smart_fit(original)
    assert fitted['valid'],fitted['errors']
    # Keep already usable bedrooms and the requested outdoor/guest widths where space permits.
    original_rooms={r['id']:r for r in original['customPlan']['floors'][0]['rooms']}
    for room in fitted['customPlan']['floors'][0]['rooms']:
        if room['kind'] not in ('bedroom','drawing-room','veranda'):continue
        x,y,x1,y1=Polygon(room['polygon']).bounds
        a,b,c,d=Polygon(original_rooms[room['id']]['polygon']).bounds
        room['polygon']=[[x,y],[x+c-a,y],[x+c-a,y+(d-b if room['kind']=='bedroom' else y1-y)],[x,y+(d-b if room['kind']=='bedroom' else y1-y)]]
    fitted['customPlan']['floors'][0]['openings']=[]
    retained=prepare_plan({**original,'customPlan':fitted['customPlan']})
    assert retained['valid'],retained['errors']
    fitted['customPlan']=retained['customPlan']
    fitted['changes']=[]
    for room in fitted['customPlan']['floors'][0]['rooms']:
        a,b,c,d=Polygon(original_rooms[room['id']]['polygon']).bounds;x,y,x1,y1=Polygon(room['polygon']).bounds
        if (a,b,c,d)!=(x,y,x1,y1):fitted['changes'].append({'id':room['id'],'message':f"Ground · {room['name']}: {(c-a)/1000:g} × {(d-b)/1000:g} → {(x1-x)/1000:g} × {(y1-y)/1000:g} m; position adjusted for walls and the stair connection."})
    p={**original,'brief':{**original['brief'],'storeys':2},'customPlan':fitted['customPlan']}
    p['customPlan']['floors'].append({'id':'floor-1','rooms':[],'walls':[],'openings':[]})
    upper=starter(p,1);assert upper['valid'],upper['errors']
    p['customPlan']=upper['customPlan']
    for room in p['customPlan']['floors'][1]['rooms']:
        if room['kind']=='kitchen':room.update(kind='hall',name='Upper lobby')
        elif room['kind']=='dining':room.update(kind='bathroom',name='Bathroom')
        elif room['kind']=='drawing-room':room.update(kind='bedroom',name='Bedroom · front')
        elif room['kind']=='living':room.update(kind='family',name='Family lounge')
    p['customPlan']['floors'][1]['openings']=[]
    final=prepare_plan(p,fixed_floors={0});assert final['valid'],final['errors'];p['customPlan']=final['customPlan']
    boards=[];W=9992;D=13788
    for fl in p['customPlan']['floors']:
        labels={};bed=0
        for r in fl['rooms']:
            if r['kind']=='bedroom':bed+=1;labels[r['id']]='bedroom-'+str(bed)
            else:labels[r['id']]=r['kind']
        board=[]
        for row in range(4):
            cells=[]
            for col in range(4):
                cell=box(col*W/4,(3-row)*D/4,(col+1)*W/4,(4-row)*D/4)
                matches=sorted([(Polygon(r['polygon']).intersection(cell).area,r['id']) for r in fl['rooms']],reverse=True)
                cells.append(labels[matches[0][1]] if matches and matches[0][0]>0 else '')
            board.append(cells)
        boards.append(board)
    boards.append([['']*4 for _ in range(4)])
    p['editorState']={'mode':'custom','guideFloors':boards,'guideEdited':False,'customPlan':copy.deepcopy(p['customPlan'])}
    # Browser JSON numbers do not distinguish 1000.0 from 1000. Publish the same representation.
    def browser_numbers(v):
        if isinstance(v,float) and v.is_integer():return int(v)
        if isinstance(v,dict):return {k:browser_numbers(x) for k,x in v.items()}
        if isinstance(v,list):return [browser_numbers(x) for x in v]
        return v
    p=browser_numbers(p)
    path=ROOT/'examples/custom/your-sketch-g1.floorforge.json';path.write_text(json.dumps(p,indent=2)+'\n')
    notes={'source':'Reconstructed from the supplied screenshot dimensions and relative positions; coordinates estimated from the image.','groundAdjustments':fitted['changes'],'upperDesign':'Aligned stair; three bedrooms, family lounge, bathroom, lobby and open terrace. Roof reached by the final stair flight.','guide':'The 16 cells summarize the exact room plan by largest overlap. They show broad placement only; custom geometry is authoritative.'}
    dest=ROOT/'examples/your-sketch';dest.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        result=run(p,Path(tmp),use_cache=False)
        shutil.copytree(result['path'],dest,dirs_exist_ok=True)
    (dest/'example-notes.json').write_text(json.dumps(notes,indent=2)+'\n')
    print(json.dumps({'path':str(dest),'planHash':result.get('planHash'),'id':result['id']}))
if __name__=='__main__':main()
