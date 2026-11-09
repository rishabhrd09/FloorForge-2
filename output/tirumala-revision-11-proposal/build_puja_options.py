"""Comparison only: do not replace the selected plan or change the live samples."""
import copy
import json
import math
from pathlib import Path
from shapely.geometry import Polygon, box, LineString
from shapely.ops import unary_union

ROOT=Path(__file__).parent
BASE=json.loads((ROOT/'plan.json').read_text())
def rect(x,y,w,h): return [[x,y],[x+w,y],[x+w,y+h],[x,y+h]]
def space(id,name,p,kind,at,short,detail):
    return dict(id=id,name=name,p=p,kind=kind,at=at,short=short,area=round(Polygon(p).area,2),detail=detail)
def line(a,b,kind='wall'): return dict(a=a,b=b,kind=kind)
def door(id,a,b,clear,kind='wood',swing=1,leaves=1):return dict(id=id,a=a,b=b,clear=clear,kind=kind,swing=swing,hinge=0,leaves=leaves)
def item(kind,p): return dict(kind=kind,p=p,label='',floor=0)

options=[]
for option,name,puja_left,entry_left in [('swap','Corner swap',13,9),('compact','Compact corner',14,10)]:
    p=copy.deepcopy(BASE)
    p['option']=option;p['name']=name;p['status']='Comparison only; not selected for implementation'
    p['summary']='Closed puja beside PO; separate front-court entry to living.' if option=='swap' else 'Smaller enclosed puja; one extra foot of front counter compared with the swap.'
    p['routeLabel']='Front court → EN → hall · PO → drawing only'
    p['tradeoff']='Closest to your suggested swap; entry shares the open kitchen frontage.' if option=='swap' else 'Recommended if you want a separate puja room: smaller shrine, wider kitchen return.'
    p['frontCounterFt']=4 if option=='swap' else 5
    p['pujaDimensions']=('4 × 4 ft' if option=='swap' else '3 × 4 ft')
    replacements={
        'K':space('K','Kitchen',[[4.5,5],[entry_left,5],[entry_left,9.5],[17,9.5],[17,20.5],[4.5,20.5]],'open',[10.5,14],'Kitchen','Open to the entry strip with no partition between them. The labelled kitchen area excludes EN and the enclosed puja.'),
        'P':space('P','Enclosed corner puja',rect(puja_left,5,17-puja_left,4),'room',[(puja_left+17)/2,7.2],'Puja','Altar on the east wall. A 2.5 ft clear timber door opens from EN through the left side wall. Enclosed room, beside PO; no entry from PO.'),
        'EN':space('EN','Front-court entry',rect(entry_left,5,3.5,4.5),'open',[entry_left+1.75,7.3],'Entry','3.5 ft clear timber entrance directly from the front court, in the former puja area. Open to kitchen and living; the left side has no partition.'),
        'PO':space('PO','Drawing porch',rect(17.5,4.5,11,4),'outdoor',[24.25,6.5],'PO','11 × 4 ft, open to the sky. Its only room entrance is the separate drawing-room timber door.'),
    }
    p['floors']['ground']=[replacements.get(r['id'],r) for r in p['floors']['ground']]
    # Remove only old shrine screens and the old PO/EN divider segment, then rebuild the closed corner.
    p['walls']['ground']=[w for w in p['walls']['ground'] if (w['a'],w['b']) not in [([8.75,4.75],[8.75,9.25]),([12.75,4.75],[12.75,9.25])]]
    left=puja_left-.25
    p['walls']['ground'] += [line([left,4.75],[left,9.25]),line([left,9.25],[17.25,9.25]),line([17.25,8.75],[17.25,9.25])]
    p['doors']['ground']=[d for d in p['doors']['ground'] if d['id']!='PO to EN living entrance']
    p['doors']['ground'] += [door('Court to EN',[entry_left-.125,4.75],[entry_left+3.625,4.75],3.5),door('EN to puja',[left,5.875],[left,8.625],2.5,swing=-1)]
    p['furniture']=[f for f in p['furniture'] if not (f['floor']==0 and (f['kind']=='altar' or (f['kind']=='counter' and min(q[1] for q in f['p'])==5)))]
    p['furniture'] += [item('altar',rect(puja_left+.25,5.1,17-puja_left-.5,.8)),item('counter',rect(4.5,5,p['frontCounterFt'],2))]
    if option=='compact':
        p['windows']['ground'][0]=line([4.75,4.75],[9.25,4.75],'glass')
    cx=entry_left+1.75
    p['routes']['ground']=[[[22,2.8],[cx,2.8],[cx,6.75],[cx,10.5],[15,14],[15,21.5]],[[22,6.5],[22,10]],[[cx,7.25],[puja_left+.6,7.25]]]
    options.append(p)

p=copy.deepcopy(BASE)
p['option']='niche';p['name']='Shuttered niche';p['status']='Comparison only; not selected for implementation'
p['summary']='Remove the shrine-room walls; use a shallow timber cabinet with sliding shutters.'
p['routeLabel']='Front court → PO → EN → hall · separate PO → drawing door'
p['tradeoff']='Most open kitchen; puja is a closable niche, not a separate room.'
p['frontCounterFt']=4;p['pujaDimensions']='3.5 × 1.5 ft cabinet'
replacements={
 'K':space('K','Kitchen',[[4.5,5],[9,5],[9,6.5],[12.5,6.5],[12.5,5],[13,5],[13,9.5],[17,9.5],[17,20.5],[4.5,20.5]],'open',[10.5,14],'Kitchen','170.5 sq ft, excluding the entry strip and shrine cabinet. Removing the shrine-room screens opens the front working area; prayer standing space shares the open kitchen/hall floor.'),
 'P':space('P','Shuttered puja niche',rect(9,5,3.5,1.5),'joinery',[10.75,7.4],'Puja niche','East-wall cabinet, 3.5 ft wide × 1.5 ft deep. Timber sliding shutters close it. No enclosing room walls or door swing into the passage. Prayer standing space remains in the open interior.'),
}
p['floors']['ground']=[replacements.get(r['id'],r) for r in p['floors']['ground']]
p['walls']['ground']=[w for w in p['walls']['ground'] if (w['a'],w['b']) not in [([8.75,4.75],[8.75,9.25]),([12.75,4.75],[12.75,9.25])]]
p['furniture']=[f for f in p['furniture'] if not (f['floor']==0 and f['kind']=='altar')]
p['furniture'].append(item('shrine-cabinet',rect(9,5,3.5,1.5)))
p['routes']['ground']=[[[22,2.8],[22,6.75],[15,6.75],[15,21.5]],[[22,6.5],[22,10]]]
options.append(p)

checks=[]
for p in options:
    p['update']='Puja/entry comparison: '+p['name']
    p['notes']=['Comparison only: do not replace the selected proposal until the user chooses an option.',p['routeLabel'],p['tradeoff'],'Altar remains on the east wall; no Vastu compliance determination is made.','Uniform 4 ft court and aligned frontage retained.']
    rooms=p['floors']['ground']; by_id={r['id']:r for r in rooms}
    for i,r in enumerate(rooms):
        shape=Polygon(r['p'])
        assert shape.is_valid and box(0,0,40,50).covers(shape)
        for r2 in rooms[i+1:]:assert shape.intersection(Polygon(r2['p'])).area<.001,(p['option'],r['id'],r2['id'])
    assert Polygon(by_id['FC']['p']).equals(box(.5,.5,28.5,4.5))
    assert by_id['DR']['area']==121 and by_id['CAR']['area']==199.5
    assert p['floors']['first']==BASE['floors']['first']
    for rid in ['C','L','M','CG','S','V','N']:
        assert by_id[rid]==next(r for r in BASE['floors']['ground'] if r['id']==rid)
    wall_lines=unary_union([LineString([w['a'],w['b']]) for w in p['walls']['ground']])
    floor_poly=unary_union([Polygon(r['p']) for r in rooms])
    for f in p['furniture']:
        if f['floor']==0:assert Polygon(f['p']).difference(floor_poly).area<.01,(p['option'],f['kind'])
    for d in p['doors']['ground']:
        assert LineString([d['a'],d['b']]).difference(wall_lines.buffer(.01)).length<.01,(p['option'],d['id'])
        if d['kind']!='wood':continue
        dx=d['b'][0]-d['a'][0];dy=d['b'][1]-d['a'][1];length=math.hypot(dx,dy);tx,ty=dx/length,dy/length
        assert length-d['clear']>=.249
        leaves=d.get('leaves',2 if d['clear']>=4 else 1);leaf=(length-.25)/leaves
        for k in range(leaves):
            sign=1 if k==0 else -1;base=d['a'] if k==0 else d['b'];h=[base[0]+sign*tx*.125,base[1]+sign*ty*.125]
            arc=[(h[0]+(tx*sign*math.cos(a)-ty*d['swing']*math.sin(a))*leaf,h[1]+(ty*sign*math.cos(a)+tx*d['swing']*math.sin(a))*leaf) for a in [i/48*math.pi/2 for i in range(49)]]
            sweep=Polygon([h]+arc+[h])
            for f in p['furniture']:
                if f['floor']==0:assert sweep.intersection(Polygon(f['p'])).area<.015,(p['option'],d['id'],f['kind'])
    checks.append({'option':p['option'],'kitchenSqFt':by_id['K']['area'],'pujaSqFt':by_id['P']['area'],'checks':'Room containment, non-overlap, furniture containment, door alignment and sweeps passed; other rooms and first floor unchanged.'})

(ROOT/'puja-options.json').write_text(json.dumps({'comparison':'Puja and entry permutations','selected':None,'options':options},indent=2)+'\n')
(ROOT/'puja-options-validation.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps(checks,indent=2))
