"""Three complete two-floor comparisons with west puja entries. Live samples are untouched."""
import copy
import json
import math
from pathlib import Path
from shapely.geometry import Polygon, box, LineString
from shapely.ops import unary_union

ROOT=Path(__file__).parent
BASE=json.loads((ROOT/'plan.json').read_text())
def poly(g):return [[round(x,3),round(y,3)] for x,y in g.exterior.coords[:-1]]
def rect(x,y,w,h):return [[x,y],[x+w,y],[x+w,y+h],[x,y+h]]
def room(id,name,p,kind,at,short,detail):
    return dict(id=id,name=name,p=p,kind=kind,at=at,short=short,area=round(Polygon(p).area,2),detail=detail)
def line(a,b,kind='wall'):return dict(a=a,b=b,kind=kind)
def door(id,a,b,clear,swing=1,leaves=1):return dict(id=id,a=a,b=b,clear=clear,kind='wood',swing=swing,hinge=0,leaves=leaves)
def item(kind,p):return dict(kind=kind,p=p,label='',floor=0)

config=[
 ('square','Square puja',13,9,4,'4 × 4 ft','Balanced enclosed puja with a square prayer space.'),
 ('compact','Compact puja',14,10,4,'3 × 4 ft','Most kitchen space of these three enclosed-room options.'),
 ('deep','Deeper puja',13.5,9.5,4.5,'3.5 × 4.5 ft','Extra depth between the west doorway and east-wall altar.'),
]
options=[]
for option,name,pl,entry_left,depth,dimensions,tradeoff in config:
    p=copy.deepcopy(BASE)
    west=5+depth;wc=west+.25;left=pl-.25;cx=(pl+17)/2;ex=entry_left+1.75
    p.update(option=option,name=name,status='Complete 2D review alternative; not implemented in 3D',update='West puja entry: '+name,
             summary=tradeoff,pujaDimensions=dimensions,routeLabel='Front court → EN → open hall; approach puja from its west side. PO → drawing only.',
             frontCounterFt=entry_left-5,
             worship=dict(entrySide='west',doorY=wc,altarWall='east',facing='east',seat=[cx,7.25],direction=[0,-1],roomId='P'))
    kitchen=unary_union([box(4.5,5,entry_left,9.5),box(4.5,9.5,17,20.5)])
    kitchen=kitchen.difference(box(pl-.5,5,17,west+.5))
    replacements={
      'K':room('K','Kitchen',poly(kitchen),'open',[10.5,14],'Kitchen','Open kitchen with no partition to the entry strip. The front counter is '+str(p['frontCounterFt'])+' ft long. Clear area excludes EN, the enclosed puja and its walls.'),
      'P':room('P','Puja · west entry',rect(pl,5,17-pl,depth),'room',[cx,west-.65],'Puja',dimensions+' enclosed room. Door is on the WEST wall (top of this plan). Enter from the open interior, sit on the marked mat and face EAST toward the altar on the front wall. South and north walls are closed; no side entry or PO entry. Two short timber leaves provide 2.5 ft net clear entry.'),
      'EN':room('EN','Front-court entry',rect(entry_left,5,3.5,4.5),'open',[ex,7.3],'Entry','3.5 ft clear timber entrance directly from the 4 ft front court. The entry strip opens into kitchen/living. Walk past the puja, then turn into its west-side doorway.'),
      'PO':room('PO','Drawing porch',rect(17.5,4.5,11,4),'outdoor',[24.25,6.5],'PO · 4 ft deep','11 × 4 ft porch, open to the sky. Its only room entrance is the separate drawing-room timber door.'),
    }
    p['floors']['ground']=[replacements.get(r['id'],r) for r in p['floors']['ground']]
    p['walls']['ground']=[w for w in p['walls']['ground'] if (w['a'],w['b']) not in [([8.75,4.75],[8.75,9.25]),([12.75,4.75],[12.75,9.25])]]
    p['walls']['ground'] += [line([left,4.75],[left,wc]),line([left,wc],[17.25,wc])]
    # Existing drawing side wall continues the north wall behind the old EN area.
    p['doors']['ground']=[d for d in p['doors']['ground'] if d['id']!='PO to EN living entrance']
    p['doors']['ground'] += [door('Court to EN',[entry_left-.125,4.75],[entry_left+3.625,4.75],3.5),
                             door('Puja WEST entry',[cx-1.375,wc],[cx+1.375,wc],2.5,swing=-1,leaves=2)]
    p['furniture']=[f for f in p['furniture'] if not (f['floor']==0 and (f['kind']=='altar' or (f['kind']=='counter' and min(q[1] for q in f['p'])==5)))]
    p['furniture'] += [item('altar',rect(pl+.25,5.1,17-pl-.5,.8)),
                       item('prayer-mat',rect(cx-1,6,2,2)),
                       item('counter',rect(4.5,5,p['frontCounterFt'],2))]
    p['windows']['ground'][0]=line([4.75,4.75],[entry_left-.75,4.75],'glass')
    original=p['routes']['ground']
    p['routes']['ground']=[[[22,2.8],[ex,2.8],[ex,6.75],[ex,10.75],[15,14],[15,23],[19,23],[24.5,23],[27,24.5]],
                           [[22,6.5],[22,10]],
                           [[ex,12],[cx,12],[cx,wc+.8],[cx,west-.45]],
                           original[1],original[2]]
    p['notes']=['Complete ground and first-floor comparison; no changes to the live 3D samples.',
                'Puja west-side entrance, east-wall altar, seated facing east. Earlier south-side puja doors and shallow-niche alternative are superseded.',
                'Front court is 4 ft deep; kitchen, puja and entry share the same front wall alignment.',
                'The first-floor layout is common to all three options: two bedrooms, office, family lounge, terrace and stair continuing to roof.',
                'Structure, local setbacks and stair headroom still require coordination.']
    # Correct a descriptive centreline/outer-face ambiguity without changing care geometry.
    for r in p['floors']['ground']:
        if r['id']=='C':r['detail']=r['detail'].replace('The care wall is 3.75 ft from the north plot boundary and over 12 ft from the west boundary.','Retain the 3 ft clear north garden path and the open rear veranda; the care room remains separated from the north and west boundaries.')
    options.append(p)

checks=[]
for p in options:
    for fn,rooms in p['floors'].items():
        for i,r in enumerate(rooms):
            shape=Polygon(r['p']);assert shape.is_valid and box(0,0,40,50).covers(shape),(p['option'],r['id'])
            for r2 in rooms[i+1:]:assert shape.intersection(Polygon(r2['p'])).area<.001,(p['option'],r['id'],r2['id'])
        walls=unary_union([LineString([w['a'],w['b']]) for w in p['walls'][fn]])
        allowed=unary_union([Polygon(r['p']) for r in rooms if r['kind']!='void'])
        fi=0 if fn=='ground' else 1
        for f in p['furniture']:
            if f['floor']==fi:assert Polygon(f['p']).difference(allowed).area<.01,(p['option'],f['kind'])
        for d in p['doors'][fn]:
            assert LineString([d['a'],d['b']]).difference(walls.buffer(.01)).length<.01,(p['option'],d['id'])
            if d['kind']!='wood':continue
            dx=d['b'][0]-d['a'][0];dy=d['b'][1]-d['a'][1];length=math.hypot(dx,dy);tx,ty=dx/length,dy/length
            assert length-d['clear']>=.249
            leaves=d.get('leaves',2 if d['clear']>=4 else 1);leaf=(length-.25)/leaves
            for k in range(leaves):
                sign=1 if k==0 else -1;base=d['a'] if k==0 else d['b'];h=[base[0]+sign*tx*.125,base[1]+sign*ty*.125]
                arc=[(h[0]+(tx*sign*math.cos(a)-ty*d['swing']*math.sin(a))*leaf,h[1]+(ty*sign*math.cos(a)+tx*d['swing']*math.sin(a))*leaf) for a in [i/48*math.pi/2 for i in range(49)]]
                sweep=Polygon([h]+arc+[h])
                for f in p['furniture']:
                    if f['floor']==fi:assert sweep.intersection(Polygon(f['p'])).area<.015,(p['option'],d['id'],f['kind'])
    by_id={r['id']:r for r in p['floors']['ground']}
    shrine=Polygon(by_id['P']['p']);front_y=shrine.bounds[1];back_y=shrine.bounds[3]
    pd=next(d for d in p['doors']['ground'] if d['id']=='Puja WEST entry')
    assert pd['a'][1]==pd['b'][1]==back_y+.25
    altar=next(f for f in p['furniture'] if f['floor']==0 and f['kind']=='altar')
    assert min(v[1] for v in altar['p'])==front_y+.1
    assert p['worship']['direction']==[0,-1] and p['worship']['seat'][1]>max(v[1] for v in altar['p'])
    assert not any(d['a'][0]==d['b'][0] and 'puja' in d['id'].lower() for d in p['doors']['ground'])
    assert Polygon(by_id['FC']['p']).equals(box(.5,.5,28.5,4.5))
    assert by_id['DR']['area']==121 and by_id['CAR']['area']==199.5
    for section in ['floors','walls','doors','windows']:
        assert p[section]['first']==BASE[section]['first']
    for rid in ['L','M','CG','S','V','N']:
        assert by_id[rid]==next(r for r in BASE['floors']['ground'] if r['id']==rid)
    checks.append(dict(option=p['option'],kitchenSqFt=by_id['K']['area'],pujaSqFt=by_id['P']['area'],entrySide='WEST',altarWall='EAST',facing='EAST',status='PASS'))

out={'comparison':'Complete plans with west-entry puja','selected':None,'options':options}
(ROOT/'west-puja-complete-plans.json').write_text(json.dumps(out,indent=2)+'\n')
(ROOT/'west-puja-validation.json').write_text(json.dumps({'status':'PASS','options':checks,'verified':['Both floors: valid room polygons, plot containment, non-overlap, furniture containment, opening alignment and timber door sweeps','Every puja entrance is on its west wall; every altar and seated direction face east','Court, parking, other main ground rooms and first floor preserved'],'limits':['Concept floor-plan checks only; not construction or 3D walk-through approval.']},indent=2)+'\n')
print(json.dumps(checks,indent=2))
