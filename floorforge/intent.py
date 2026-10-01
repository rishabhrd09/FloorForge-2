"""Source-preserving fusion. Uninterpreted material stays visible, not silently applied."""
from __future__ import annotations
from .model import *
from .exterior import EXTERIOR_THEME_IDS, INTERIOR_THEME_IDS, CHANGE_POLICIES
import re, datetime
from .spaces import guide_labels, guide_kind, GUIDE_AUTOMATIC_KINDS, SPACE_REGISTRY


WORDS={'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'single':1,'double':2}
COUNT=r'(\d+|one|two|three|four|five|six|seven|eight)'
DIRECTIONS={'north':0.,'north-east':45.,'east':90.,'south-east':135.,'south':180.,'south-west':225.,'west':270.,'north-west':315.}
DIR_SHORT={'n':'north','ne':'north-east','e':'east','se':'south-east','s':'south','sw':'south-west','w':'west','nw':'north-west'}
DIR_WORD=r'(north[ -]?east|north[ -]?west|south[ -]?east|south[ -]?west|north|east|south|west)'
LENGTH_UNIT=r'(mm|millimetres?|millimeters?|cm|m|mtrs?|metres?|meters?|ft|feet|foot|inch(?:es)?|in)\b'
STANDARD_PLOTS=((20,30),(20,40),(25,40),(30,40),(30,50),(30,60),(40,60),(50,80),(60,90),(80,120))   # feet, common Indian layouts
AREA_M2={'ft':.09290304,'yd':.83612736,'m':1.,'cent':40.468564224,'guntha':101.17141056,'marla':25.29285264}
STYLE_WORDS={'modern':'minimal','contemporary':'minimal','minimalist':'minimal','kerala':'tropical','tropical':'tropical',
             'traditional':'terracotta','heritage':'terracotta','ethnic':'terracotta','industrial':'concrete'}
ROOM_WORDS=r'(bed\s*room|bedroom|kitchen|living|hall|bath|toilet|dining|study|pooja|puja|balcony|garage|room|parking|porch)'
PLOT_WORDS=r'(plot|site|land|sital|layout|property)'
STOP={'i','we','want','need','needs','would','like','to','a','an','the','house','home','please','have','has','my','our','for','family','build',
      'new','of','in','on','it','is','be','should','and','with','also','that','this','looking','plan','design','place','me','us','are','will','can'}
LEFTOVER={'plot','site','land','sital','property','size','facing','road','budget','around','about','approx','approximately','total',
          'only','floor','floors','must','required','want','bhk','rooms','room','each','all','every','ft','feet','sq','m'}

# The 4 x 4 board is deliberately semantic: its cells have no physical size.  Row 0 is the road/front edge and
# columns run from the viewer's left to right.  These labels are shared by the board and the small spatial-language
# grammar below; the planner, rather than the board, remains responsible for safe room sizes and circulation.
SPATIAL_LABELS = set(guide_labels())
_SPATIAL_ROOM = (r'(master\s+bed(?:\s*room)?|bed(?:\s*room)?\s*(?:-|number\s*)?[1-8]|living(?:\s+room)?|'
                 r'drawing\s+room|drying\s+room|dining(?:\s+room)?|kitchen|hall|family(?:\s+(?:room|lounge))?|common\s+bath(?:room)?|'
                 r'bath(?:room)?(?:\s*(?:-|number\s*)?[1-8])?|utility(?:\s+room)?|study|'
                 r'pooja|puja|prayer(?:\s+room)?|store(?:\s+room)?)')
_LOCAL_POSITION = (r'(front(?:[ -]+(?:left|right|centre|center))?|rear(?:[ -]+(?:left|right|centre|center))?|'
                   r'back(?:[ -]+(?:left|right|centre|center))?|left(?:[ -]+(?:front|rear|back))?|'
                   r'right(?:[ -]+(?:front|rear|back))?|centre|center)')


def _spatial_label(room: str) -> str:
    room=re.sub(r'\s+',' ',room.strip().lower())
    if room.startswith('master'):return 'master-bedroom'
    if room.startswith('bed'):
        n=re.search(r'[1-8]',room);return f'bedroom-{n.group()}' if n else 'master-bedroom'
    if room.startswith('drawing'):return 'drawing-room'
    if room.startswith('drying'):return 'drying-room'
    if room.startswith('living'):return 'living'
    if room.startswith('dining'):return 'dining'
    if room.startswith('family'):return 'family'
    if room.startswith('common bath'):return 'bathroom'
    if room.startswith('bath'):
        n=re.search(r'[1-8]',room);return f'bathroom-{n.group()}' if n else 'bathroom'
    if room.startswith(('pooja','puja','prayer')):return 'pooja'
    if room.startswith('utility'):return 'utility'
    if room.startswith('store'):return 'store'
    return room


def _local_target(position: str) -> tuple[float,float]:
    words=position.replace('-',' ').split();x=y=.5
    if 'left' in words:x=.125
    if 'right' in words:x=.875
    if 'front' in words:y=.125
    if 'rear' in words or 'back' in words:y=.875
    return x,y


def _text_spatial_hints(text: str, normalised: str) -> list[dict]:
    """Extract only explicit room/location phrases. Compass locations are resolved after source fusion, when the
    final road bearing is known; local front/rear/left/right locations can be stored immediately."""
    hints=[];seen=set()
    join=r'\s+(?:at|in|on|towards?|to)\s+(?:the\s+)?'
    for m in re.finditer(r'\b'+_SPATIAL_ROOM+join+_LOCAL_POSITION+r'(?:\s+side)?\b',normalised):
        label=_spatial_label(m[1]);x,y=_local_target(m[2])
        key=(m.start(),m.end(),label)
        if key not in seen:
            hints.append({'label':label,'frame':'local','x':x,'y':y,'phrase':text[m.start():m.end()].strip(),'span':[m.start(),m.end()]});seen.add(key)
    # "south-east kitchen" and "master bedroom in south-east" are both common homeowner shorthand.  A compass
    # target is geographic, unlike the board's road-relative left/right, and is transformed later.
    compass=DIR_WORD
    patterns=(r'\b'+_SPATIAL_ROOM+join+compass+r'\b',r'\b'+compass+r'[ -]+'+_SPATIAL_ROOM+r'\b')
    for i,pat in enumerate(patterns):
        for m in re.finditer(pat,normalised):
            room=m[1] if i==0 else m[2];direction=m[2] if i==0 else m[1]
            label=_spatial_label(room);key=(m.start(),m.end(),label)
            if key not in seen:
                hints.append({'label':label,'frame':'compass','bearing':_dir(direction),'phrase':text[m.start():m.end()].strip(),'span':[m.start(),m.end()]});seen.add(key)
    return hints


def _validate_spatial_grid(grid, storeys=None) -> list[dict]:
    if not isinstance(grid,dict) or set(grid)-{'mode','rows','cols','floors','floorIds'}:
        raise DesignError('GRID_SCHEMA','The spatial guide accepts mode, rows, cols, floors and stable floorIds.')
    if grid.get('mode')!='spatial_hint' or grid.get('rows')!=4 or grid.get('cols')!=4:
        raise DesignError('GRID_SIZE','Every floor guide is always exactly 4 x 4 (16 cells).')
    floors=grid.get('floors')
    if not isinstance(floors,list) or not 1<=len(floors)<=3:
        raise DesignError('GRID_FLOORS','Use Ground, First and Second guides, one board per requested floor.')
    scoped='floorIds' in grid or len(floors)>1 or storeys==1
    if scoped and len(floors)!=storeys:
        raise DesignError('GRID_FLOORS','Guide floor count must match the requested storeys.')
    floor_ids=grid.get('floorIds',[f'floor-{f}' for f in range(len(floors))])
    if not isinstance(floor_ids,list) or len(floor_ids)!=len(floors) or any(not isinstance(i,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_.-]{0,79}',i) for i in floor_ids) or len(set(floor_ids))!=len(floor_ids):
        raise DesignError('GRID_FLOOR_IDS','Give each guide a unique stable floor ID.')
    hints=[]
    for f,rows in enumerate(floors):
        if not isinstance(rows,list) or len(rows)!=4 or any(not isinstance(row,list) or len(row)!=4 for row in rows):
            raise DesignError('GRID_SIZE','Every guide must contain exactly four rows of four cells.',{'floor':f})
        grouped={}
        for y,row in enumerate(rows):
            for x,label in enumerate(row):
                if label in ('',None):continue
                if not isinstance(label,str) or label not in SPATIAL_LABELS:
                    raise DesignError('GRID_LABEL','Unsupported guide room: '+str(label),{'floor':f,'cells':[[x,y]]})
                grouped.setdefault(label,[]).append((x,y))
        for label,cells in grouped.items():
            hint={'label':label,'x':round(sum(x+.5 for x,_ in cells)/(4*len(cells)),6),
                  'y':round(sum(y+.5 for _,y in cells)/(4*len(cells)),6),'source':'grid','cells':[[x,y] for x,y in cells]}
            if scoped:hint.update(floor=f,floorId=floor_ids[f])
            hints.append(hint)
    if not hints:raise DesignError('GRID_EMPTY','Paint at least one room before applying the guides.')
    return hints


def _resolve_text_spatial(hints: list[dict], road_bearing: float) -> list[dict]:
    resolved=[]
    for hint in hints:
        if hint['frame']=='local':x,y=hint['x'],hint['y']
        else:
            a=math.radians(hint['bearing']);east,north=math.sin(a),math.cos(a)
            dx,dy=enu_to_local(east,north,road_bearing)
            x=max(.125,min(.875,.5+.375*dx));y=max(.125,min(.875,.5+.375*dy))
        resolved.append({'label':hint['label'],'x':round(x,6),'y':round(y,6),'source':'text','phrase':hint['phrase']})
    return resolved


def _check_spatial_programme(hints: list[dict], values: dict) -> None:
    for hint in hints:
        issue=_spatial_programme_issue(hint,values)
        if issue:raise DesignError('PLACEMENT_PROGRAMME',f'The spatial guide requests {hint["label"]}, but {issue}',{'rooms':[{**hint,'message':issue}]})
    numbered_floors={}
    for h in hints:
        key=h['label']
        if key=='master-bedroom':key=f'bedroom-{values["bedrooms"]}'
        if key.startswith('bedroom-'):
            if key in numbered_floors and numbered_floors[key]!=h.get('floor'):
                raise DesignError('PLACEMENT_CONFLICT','A numbered bedroom cannot be assigned to two floors.',{'rooms':[{'label':key,'floor':h.get('floor'),'cells':h.get('cells',[])}]})
            numbered_floors[key]=h.get('floor')
    by_label={h['label']:h for h in hints};numbered=by_label.get(f'bedroom-{values["bedrooms"]}');master=by_label.get('master-bedroom')
    if numbered and master and math.hypot(numbered['x']-master['x'],numbered['y']-master['y'])>.15:
        raise DesignError('PLACEMENT_CONFLICT',f'Master bedroom and bedroom-{values["bedrooms"]} identify the same planned room but request different positions.')


def _attached_room_numbers(values: dict) -> set[int]:
    """Mirror the planner's stable bedroom order so impossible numbered bath hints fail before search."""
    total=values['bedrooms'];ground=total if values['storeys']==1 else max(1,total//2);master=total
    order=[master]+[n for n in range(1,ground+1) if n!=master]+[n for n in range(ground+1,total+1) if n!=master]
    if values.get('eldercare') and values['storeys']==2:
        first=next((n for n in order if n<=ground),None)
        if first is not None:order=[first]+[n for n in order if n!=first]
    requested=total if values['attached_baths']=='all' else min(int(values['attached_baths']),total)
    return set(order[:requested])


def _spatial_programme_issue(hint: dict, values: dict) -> str | None:
    label=hint['label'];m=re.fullmatch(r'(bedroom|bathroom)-([1-8])',label)
    if m and int(m[2])>values['bedrooms']:
        return f'the resolved brief contains only {values["bedrooms"]} bedroom(s).'
    if m and m[1]=='bathroom' and int(m[2]) not in _attached_room_numbers(values):
        return f'bedroom {m[2]} has no attached bathroom in the resolved brief.'
    if label=='pooja' and not values['pooja']:return 'Pooja room is turned off in the resolved brief.'
    if label=='family' and values['storeys']<2:return 'a family lounge requires a G+1 brief in this generator.'
    return None


def _dir(t):
    t=t.strip().replace(' ','-')
    t=re.sub(r'^(north|south)-?(east|west)$',r'\1-\2',t)
    return DIRECTIONS[DIR_SHORT.get(t,t)]


def _count(t):
    return int(t) if t.isdigit() else WORDS[t]


def _mm(n,unit):
    unit=(unit or '').rstrip('s')
    if unit in ('mm','millimetre','millimeter'):return n
    if unit=='cm':return n*10
    if unit in ('ft','feet','foot',"'"):return n*304.8
    if unit in ('inch','inche','in','"'):return n*25.4
    return n*1000


def parse_text(text: str) -> dict:
    """Read the brief fields a homeowner usually writes: plot size or area, facing, bedrooms, attached baths, storeys,
    budget, pooja, parking, kitchen, Vastu, setbacks, heights and style. Everything else stays visible as prose."""
    if not isinstance(text,str) or len(text)>20000:
        raise DesignError('TEXT_LIMIT','Description must be text, at most 20,000 characters.')
    # Same-length normalisation so match positions index the original text.
    s=text.lower().replace('×','x').replace('’',"'").replace('′',"'").replace('″','"')
    values={};found=[];assumptions=[]
    def hit(m,field,value,group=0):
        found.append((m.start(group),m.end(group),field,value))
        if isinstance(field,tuple):
            for f,v in zip(field,value):values[f]=v
        else:values[field]=value
    def near(m,pattern,before=30,after=0):
        return re.search(pattern,s[max(0,m.start()-before):m.end()+after]) is not None
    # Plot size: "30x40", "30 x 40 ft", "30' x 40'", "30 by 40", "9m x 12m", "30*40", "30 into 40".
    unit=r"(?:\s*(feet|foot|ft|metres|meters|metre|meter|mtrs|mtr|m)\b|\s*(')|)"
    dims=[]
    plots=[w.start() for w in re.finditer(PLOT_WORDS,s)]
    for m in re.finditer(r'(?<![\d.])(\d+(?:\.\d+)?)'+unit+r'\s*(?:x|\*|by|into)\s*(\d+(?:\.\d+)?)'+unit+r'(?!\.?\d)',s):
        a,b=float(m[1]),float(m[4]);u=m[2] or m[3] or m[5] or m[6]
        # A size right after a room name ("living 15x18") is a room, not the plot; the plot is the size nearest "plot".
        room=re.search(ROOM_WORDS+r'\W{0,3}(?:(?:of|is|size|about)\W+)?$',s[max(0,m.start()-22):m.start()]) is not None
        gap=min((max(0,m.start()-q,q-m.end()) for q in plots),default=10**6)
        dims.append((room,gap if gap<=40 else 10**6,m.start(),m,a,b,u))
    dims.sort(key=lambda t:t[:3])
    for room,gap,_,m,a,b,u in dims:
        if room and gap>40:continue
        feet=u in ('feet','foot','ft',"'") if u else max(a,b)>=20
        lo,hi=(15,300) if feet else (5,90)
        if not (lo<=min(a,b) and max(a,b)<=hi):continue
        if not u:assumptions.append(f'"{text[m.start():m.end()]}" read as {"feet" if feet else "metres"}.')
        k=304.8 if feet else 1000
        hit(m,('width_mm','depth_mm'),(round(a*k),round(b*k)));break
    for m in re.finditer(r'\b(?:width|frontage|wide)\s*(?:of|is|:|=)?\s*(\d+(?:\.\d+)?)\s*'+LENGTH_UNIT,s):
        hit(m,'width_mm',round(_mm(float(m[1]),m[2])))
    for m in re.finditer(r'\b(?:depth|length|deep)\s*(?:of|is|:|=)?\s*(\d+(?:\.\d+)?)\s*'+LENGTH_UNIT,s):
        hit(m,'depth_mm',round(_mm(float(m[1]),m[2])))
    # Plot area: sq ft, sq yd / gaj, sq m, cents, guntha, marla. A built-up or carpet area is not the plot.
    area_pat=(r'(?<![\d.,])(\d[\d,]*(?:\.\d+)?)\s*(sq\.?\s*(?:ft|feet)\b|sqft|sft|square\s+f(?:ee|oo)t|ft2|ft²|sq\.?\s*y(?:ar)?ds?\b|square\s+yards?|'
              r'gaj|gaz|sq\.?\s*m(?:trs?|etres?|eters?)?\b|sqm|m2|m²|square\s+met(?:re|er)s?|cents?\b|gunthas?|guntas?|marlas?)')
    for m in re.finditer(area_pat,s):
        if near(m,r'(built|carpet|super|bua|construction)',25,25):continue
        u=m[2];n=float(m[1].replace(',',''))
        key='ft' if re.match(r'(sq\.?\s*f|sqft|sft|square\s+f|ft)',u) else 'yd' if re.match(r'(sq\.?\s*y|square\s+y|gaj|gaz)',u) else \
            'cent' if u.startswith('cent') else 'guntha' if u.startswith('gun') else 'marla' if u.startswith('marla') else 'm'
        a=n*AREA_M2[key]
        if not 40<=a<=5000:continue
        found.append((m.start(),m.end(),'plot_area_m2',round(a,1)))
        if 'width_mm' not in values:
            ft2=a/AREA_M2['ft'];std=next(((w,d) for w,d in STANDARD_PLOTS if abs(w*d-ft2)<=.03*w*d),None)
            if std:
                wmm,dmm=round(std[0]*304.8),round(std[1]*304.8)
                assumptions.append(f'Plot area {ft2:.0f} ft2 read as the standard {std[0]} x {std[1]} ft plot; give the frontage if it differs.')
            else:
                wmm=round(math.sqrt(a*1e6/1.5)/10)*10;dmm=round(wmm*1.5/10)*10
                assumptions.append(f'Plot area {a:.0f} m2 read as {wmm/1000:.2f} x {dmm/1000:.2f} m (a 2:3 plot assumed); give the frontage for the exact size.')
            values.update(width_mm=wmm,depth_mm=dmm)
        elif abs(values['width_mm']*values['depth_mm']/1e6-a)>.1*a:
            assumptions.append(f'The stated area ({a:.0f} m2) does not match the plot size; the size was used.')
        break
    for m in re.finditer(r'\b'+COUNT+r'\s*-?\s*(?:bhk|b\.h\.k\.?|bed\s*rooms?|beds?\b|br\b)',s):
        n=_count(m[1])
        if 1<=n<=8:hit(m,'bedrooms',n)
    # Attached baths: all, a count, only the master, none; else from the total number of baths.
    attached=None
    noun=r'(?:\s+(?:bath(?:room)?s?|toilets?|washrooms?))?'
    for pat,val in ((r'\b(?:all|every|each)\s+(?:the\s+)?(?:bed\s*rooms?|rooms?)\s+(?:with\s+|having\s+|have\s+|has\s+)?(?:an?\s+)?(?:attached|ensuite|en-suite)'+noun,'all'),
                    (r'\b(?:attached|ensuite|en-suite)\s+(?:bath(?:room)?s?|toilets?|washrooms?)\s+(?:for|in|with|to)\s+(?:all|every|each)','all'),
                    (r'\b(?:master|main)\s+(?:bed\s*room\s+)?(?:with\s+)?(?:an?\s+)?(?:attached|ensuite|en-suite)'+noun,1),
                    (r'\b(?:attached|ensuite|en-suite)\s+(?:bath(?:room)?|toilet|washroom)\s+(?:for|in|to|with)\s+(?:the\s+)?(?:master|main)',1),
                    (r'\bno\s+(?:attached|ensuite|en-suite)'+noun,0)):
        for m in re.finditer(pat,s):
            hit(m,'attached_baths',val);attached=val
    for m in re.finditer(r'\b'+COUNT+r'\s+(?:attached|ensuite|en-suite)\s+(?:bath(?:room)?s?|toilets?|washrooms?)',s):
        n=_count(m[1])
        if 0<=n<=8:hit(m,'attached_baths',n);attached=n
    if attached is None:
        for m in re.finditer(r'\b'+COUNT+r'\s*(?:bath\s*rooms?|baths?\b|toilets?|washrooms?|t\b)',s):
            total=_count(m[1]);beds=values.get('bedrooms',DEFAULTS['bedrooms'])
            if 1<=total<=10:
                hit(m,'attached_baths','all' if total>beds else max(0,total-1))
                assumptions.append(f'{total} baths read as {values["attached_baths"]} attached' +
                                   (' (every bedroom) plus a common bath.' if total>beds else ' and one common bath.'))
    # Storeys: G+1, duplex, two-storey, ground only.
    for m in re.finditer(r'\bg\s*\+\s*(\d)\b',s):
        n=int(m[1])+1
        if n>3:raise DesignError('STOREYS_UNSUPPORTED','This release supports Ground, First and Second floors; extra floors were not silently removed.')
        hit(m,'storeys',n)
    for m in re.finditer(r'\b(?:duplex|(?:two|double|2)[ -]?stor(?:e?y|eys|ies|ied)|(?:two|2)\s+floors|ground\s*(?:\+|plus)\s*(?:one|first|1))\b',s):
        hit(m,'storeys',2)
    for m in re.finditer(r'\b(?:(?:single|one|1)[ -]?stor(?:e?y|ied)|ground[ -](?:floor[ -])?only|only\s+(?:the\s+)?ground\s+floor|(?:one|single|1)\s+floor\b)',s):
        hit(m,'storeys',1)
    # Facing: "east facing", "NE-facing", "facing north", "road on the west", "south road".
    for m in re.finditer(r'\b(north[ -]?east|north[ -]?west|south[ -]?east|south[ -]?west|north|east|south|west|ne|nw|se|sw|n|e|s|w)[ -]?facing\b',s):
        hit(m,'road_bearing_deg',_dir(m[1]))
    for m in re.finditer(r'\bfacing\s+(?:the\s+)?'+DIR_WORD+r'\b',s):
        hit(m,'road_bearing_deg',_dir(m[1]))
    for m in re.finditer(r'\broad\s+(?:is\s+)?(?:on|to|towards|at|in)\s+(?:the\s+)?'+DIR_WORD+r'\b|\b'+DIR_WORD+r'\s+(?:side\s+)?road\b',s):
        hit(m,'road_bearing_deg',_dir(m[1] or m[2]))
    # Budget: lakh, crore, or rupees in full after the word budget.
    for m in re.finditer(r'(?:₹|\brs\.?|\binr)?\s*(\d+(?:\.\d+)?)\s*(lakhs?|lacs?|lakh|lac|lk)\b',s):
        hit(m,'budget_lakh',float(m[1]))
    for m in re.finditer(r'(?:₹|\brs\.?|\binr|budget\D{0,12}?)\s*(\d+(?:\.\d+)?)\s*l\b',s):
        hit(m,'budget_lakh',float(m[1]))
    for m in re.finditer(r'(?:₹|\brs\.?|\binr)?\s*(\d+(?:\.\d+)?)\s*(?:crores?|cr)\b',s):
        hit(m,'budget_lakh',float(m[1])*100)
    for m in re.finditer(r'\bbudget\D{0,15}?(\d{1,3}(?:,\d{2,3})+|\d{6,})\b',s):
        hit(m,'budget_lakh',round(float(m[1].replace(',',''))/1e5,2))
    # Pooja, parking, kitchen, eldercare.
    neg_pooja=list(re.finditer(r'\b(?:no|without)\s+(?:pooja|puja|prayer|mandir)(?:\s+room)?',s))
    for m in neg_pooja:hit(m,'pooja',False)
    if not neg_pooja:
        for m in re.finditer(r'\b(?:pooja|puja|prayer|mandir|temple)(?:\s+(?:room|space|area|corner|unit))?\b',s):hit(m,'pooja',True)
    neg_park=list(re.finditer(r'\b(?:no|without)\s+(?:car\s+)?parking\b',s))
    for m in neg_park:hit(m,'parking',False)
    if not neg_park:
        for m in re.finditer(r'\b(?:car\s+parking|car\s+porch|garage|carport|(?:one|two|1|2)\s+cars?\b|parking(?:\s+for\s+(?:a|one|two|1|2)\s+cars?)?)',s):
            hit(m,'parking',True)
    for m in re.finditer(r'\b(?:open(?:[ -]plan)?\s+kitchen|kitchen\s+open\s+to\s+(?:the\s+)?(?:living|dining|hall))\b',s):hit(m,'open_kitchen',True)
    for m in re.finditer(r'\b(?:closed|separate|enclosed)\s+kitchen\b',s):hit(m,'open_kitchen',False)
    for m in re.finditer(r'\b(?:elderly|senior\s+citizens?|aged|old)\s+(?:parents?|people|persons?|members?|mother|father)\b|\bwheel\s*chair\b|\belder\s*care\b',s):
        hit(m,'eldercare',True)
    # Vastu: off, strict, flexible, else a mention means moderate.
    vastu=None
    for pat,val in ((r'\b(?:no|without|ignore|skip)\s+vastu\b|\bvastu\s+(?:is\s+)?not\s+(?:needed|required|important|necessary)\b|\bdon\'?t\s+(?:need|want|care\s+about)\s+vastu\b','off'),
                    (r'\b(?:strict(?:ly)?|100\s*%|fully|full|complete(?:ly)?|perfect|proper)\s+vastu\b|\bvastu[ -](?:compliant|compliance|shastra\s+compliant)\b|\bas\s+per\s+vastu\b','strict'),
                    (r'\b(?:some|basic|flexible|partial|little)\s+vastu\b|\bvastu\s+(?:if\s+possible|preferred|where\s+possible)\b','flexible')):
        for m in re.finditer(pat,s):
            hit(m,'vastu',val);vastu=val
        if vastu:break
    if vastu is None:
        for m in re.finditer(r'\bvaa?stu(?:\s+shastra)?\b',s):hit(m,'vastu','moderate')
    # Setbacks, heights.
    for m in re.finditer(r'\b(front|rear|back|left|right|sides?)\s+(?:setback|margin|open\s+space|offset)s?\s*(?:of|is|:|=|-)?\s*(\d+(?:\.\d+)?)\s*'+LENGTH_UNIT,s):
        v=round(_mm(float(m[2]),m[3]));keys={'front':['front_mm'],'rear':['rear_mm'],'back':['rear_mm'],'left':['left_mm'],'right':['right_mm']}.get(m[1],['left_mm','right_mm'])
        hit(m,tuple(keys),tuple([v]*len(keys)))
    for m in re.finditer(r'(?<![\d.])(\d+(?:\.\d+)?)\s*'+LENGTH_UNIT+r'\s+(front|rear|back|left|right|sides?)\s+(?:setback|margin|open\s+space)',s):
        v=round(_mm(float(m[1]),m[2]));keys={'front':['front_mm'],'rear':['rear_mm'],'back':['rear_mm'],'left':['left_mm'],'right':['right_mm']}.get(m[3],['left_mm','right_mm'])
        hit(m,tuple(keys),tuple([v]*len(keys)))
    for m in re.finditer(r'\b(floor[ -]to[ -]floor|floor|storey|ceiling)\s+height\s*(?:of|is|:|=)?\s*(\d+(?:\.\d+)?)\s*'+LENGTH_UNIT,s):
        v=round(_mm(float(m[2]),m[3])+(150 if m[1]=='ceiling' else 0),-1)
        if 2950<=v<=3600:hit(m,'floor_height_mm',int(v))
        else:assumptions.append(f'"{text[m.start():m.end()]}" is outside the 2.95-3.6 m floor-to-floor range this generator builds; not applied.')
    for m in re.finditer(r'\bplinth\s*(?:height|level)?\s*(?:of|is|:|=)?\s*(\d+(?:\.\d+)?)\s*'+LENGTH_UNIT,s):
        v=round(_mm(float(m[1]),m[2]))
        if 0<=v<=900:hit(m,'plinth_mm',v)
    # Style: a style name, or a common word for one when it describes the house.
    for style in STYLES:
        for m in re.finditer(r'\b'+style+r'\b',s):hit(m,'style',style)
    if 'style' not in values:
        for word,style in STYLE_WORDS.items():
            for m in re.finditer(r'\b'+word+r'\b(?:\s+\w+){0,2}?\s+(?:style|look|design|house|home|elevation|facade|villa|architecture)\b(?:\s+(?:house|home|elevation|design))?',s):
                hit(m,'style',style)
    for m in re.finditer(r'\b(?:(no|without)\s+)?(?:roof(?:top)?(?: terrace)? access|(?:stairs?|staircase)\s+to\s+(?:the\s+)?roof(?:top)?(?: terrace)?)\b',s):
        hit(m,'roof_access',not bool(m[1]))
    spatial_hints=_text_spatial_hints(text,s)
    for hint in spatial_hints:
        start,end=hint['span'];phrase=hint['phrase']
        found.append((start,end,'__placement__',{'label':hint['label'],'position':phrase}))
    # What was read, and which phrases were not.
    found.sort(key=lambda t:t[0])
    understood=[{'text':text[a:b].strip(),'values':({'spatial placement':v} if f=='__placement__' else dict(zip(f,v)) if isinstance(f,tuple) else {f:v})} for a,b,f,v in found]
    covered=[False]*len(s)
    for a,b,_,_ in found:
        for i in range(a,b):covered[i]=True
    missed=[]
    for m in re.finditer(r'[^.;,\n!?]+',text):
        # A phrase is unread when words that carry meaning are left once the recognised parts are taken out.
        rest=''.join(' ' if covered[i] else text[i] for i in range(m.start(),m.end()))
        if [w for w in re.findall(r'[a-z]+',rest.lower()) if w not in STOP and w not in LEFTOVER]:
            missed.append(m.group().strip())
    spans=[(a,b) for a,b,_,_ in found]
    return {'values':values,'spatial_hints':spatial_hints,'raw_text':text,'unparsed_notice':
        'Only the listed structured fields were extracted. Other prose remains a reference; it is not a satisfied constraint.',
        'matched_spans':spans,'reading':{'understood':understood,'not_understood':missed,'assumptions':assumptions}}


# Open spaces as many Indian byelaws tabulate them: front and rear by plot depth, each side by plot width (m -> mm).
SETBACKS_BY_DEPTH=((10,1000,500),(12,1200,600),(15,1800,900),(20,3000,1200),(25,3500,1500),(30,4500,2000),(math.inf,6000,3000))
SETBACKS_BY_WIDTH=((6.5,300),(8,450),(10,750),(13,1000),(16,1500),(20,2000),(math.inf,3000))


def derive_setbacks(width_mm,depth_mm,parking=False):
    """Front, rear and side open spaces typical of Indian municipal byelaws for a plot of this size (mm); a parking
    court takes a 5.5 m front where the plot is deep enough. Design assumptions to verify locally, not a rule pack."""
    front,rear=next((f,r) for limit,f,r in SETBACKS_BY_DEPTH if depth_mm/1000<=limit)
    side=next(sd for limit,sd in SETBACKS_BY_WIDTH if width_mm/1000<=limit)
    if parking and depth_mm-5500-rear>=8000:
        front=max(front,5500)
    return {'front_mm':front,'rear_mm':rear,'left_mm':side,'right_mm':side}


def validate_values(values: dict, custom=False) -> dict:
    unknown=set(values)-set(DEFAULTS)
    if unknown: raise DesignError('UNKNOWN_FIELD','Unsupported structured fields: '+', '.join(sorted(unknown)))
    d={**DEFAULTS,**values}
    ints={'width_mm':(5000,50000),'depth_mm':(6500,60000),'bedrooms':(1,8),'storeys':(1,3),
          'front_mm':(0,15000),'rear_mm':(0,10000),'left_mm':(0,10000),'right_mm':(0,10000),
          'plinth_mm':(0,900),'floor_height_mm':(2950,3600),'variant':(0,2),'seed':(0,2147483647)}
    if custom:ints['bedrooms']=(0,360)
    for k,(lo,hi) in ints.items():
        if type(d[k]) is not int or not lo<=d[k]<=hi:
            raise DesignError('FIELD_RANGE',f'{k} must be an integer between {lo} and {hi}.')
    nums={'road_bearing_deg':(0,359.999999),'budget_lakh':(.1,100000),'latitude':(-89,89),
          'longitude':(-180,180),'timezone_hours':(-12,14),'solar_hour':(0,24),
          'rate_low_inr_ft2':(0,100000),'rate_high_inr_ft2':(0,100000),'cost_contingency_pct':(0,100)}
    for k,(lo,hi) in nums.items():
        v=d[k]
        if isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) or not lo<=v<=hi:
            raise DesignError('FIELD_RANGE',f'{k} must be a finite number between {lo} and {hi}.')
    if d['rate_low_inr_ft2']>d['rate_high_inr_ft2']:
        raise DesignError('RATE_ORDER','Low scenario rate must not exceed high scenario rate.')
    for k in ('parking','pooja','eldercare','open_kitchen','roof_access'):
        if type(d[k]) is not bool: raise DesignError('FIELD_TYPE',f'{k} must be a boolean.')
    if d['attached_baths']!='all' and (type(d['attached_baths']) is not int or not 0<=d['attached_baths']<=8):
        raise DesignError('FIELD_RANGE','attached_baths must be "all" or an integer between 0 and 8.')
    for key, choices in [('style',list(STYLES)),('exterior_theme',list(EXTERIOR_THEME_IDS)),
                         ('interior_theme',list(INTERIOR_THEME_IDS)),
                         ('change_policy',list(CHANGE_POLICIES)),
                         ('finish',['economy','standard','premium']),('vastu',['off','flexible','moderate','strict']),
                         ('soil',['unknown','black-cotton','rocky','sandy','alluvial','red-laterite','murrum'])]:
        if d[key] not in choices: raise DesignError('FIELD_CHOICE',f'Invalid {key}.')
    if type(d['interior_layout_locked']) is not bool:
        raise DesignError('FIELD_TYPE','interior_layout_locked must be a boolean.')
    if not isinstance(d['theme_version'],str) or not 1<=len(d['theme_version'])<=32:
        raise DesignError('FIELD_TYPE','theme_version must be a non-empty string of at most 32 characters.')
    if not isinstance(d['title'],str) or not 1<=len(d['title'])<=120: raise DesignError('TITLE','Use a title of 1-120 characters.')
    try: datetime.date.fromisoformat(d['solar_date'])
    except (TypeError,ValueError): raise DesignError('SOLAR_DATE','Use a valid ISO calendar date.')
    if d['eldercare']:
        # Preserve request, but do not call a standard room an ICU or accessible space.
        pass
    return d


def fuse(payload: dict) -> dict:
    if not isinstance(payload,dict): raise DesignError('INPUT_OBJECT','Expected a project object.')
    if set(payload)-{'schema','sources','brief','text','grid','customPlan','draftRevision','editorState','attachments','notes','roomEdits','furnitureLayout'}:
        raise DesignError('PROJECT_FIELDS','Unknown project top-level fields.')
    brief_input=payload.get('brief') if isinstance(payload.get('brief'),dict) else {}
    defaults=dict(DEFAULTS)
    # Projects written before the exterior upgrade must retain their current
    # appearance until the owner explicitly selects an upgrade.
    if 'exterior_theme' not in brief_input and payload.get('schema') not in ('floorforge.project/0.3','floorforge.project/0.4'):
        defaults['exterior_theme']='current'
    if 'interior_theme' not in brief_input and payload.get('schema') not in ('floorforge.project/0.3','floorforge.project/0.4'):
        defaults['interior_theme']='current'
    sources=[{'id':'defaults','kind':'defaults','enabled':True,'values':defaults}]
    if payload.get('brief') is not None:
        sources.append({'id':'quick-survey','kind':'survey','enabled':True,'values':payload['brief']})
    reading=None;text_spatial=[]
    if payload.get('text'):
        p=parse_text(payload['text']); reading=p.pop('reading');text_spatial=p.pop('spatial_hints',[])
        sources.append({'id':'description','kind':'text','enabled':True,**p})
    extra=payload.get('sources',[])
    if not isinstance(extra,list):raise DesignError('SOURCE_SCHEMA','Sources must be a list.')
    sources += extra
    if not isinstance(sources,list) or len(sources)>64: raise DesignError('SOURCE_LIMIT','Maximum 64 input sources.')
    seen=set(); notices=[]
    for src in sources:
        if not isinstance(src,dict) or set(src)-{'id','kind','enabled','values','raw_text','unparsed_notice','matched_spans','reference'}:
            raise DesignError('SOURCE_SCHEMA','Invalid source record.')
        if not re.fullmatch(r'[A-Za-z0-9_.-]{1,80}',str(src.get('id',''))) or src['id'] in seen:
            raise DesignError('SOURCE_ID','Source IDs must be unique, safe identifiers.')
        seen.add(src['id'])
        if src.get('kind') not in SOURCE_PRIORITY or type(src.get('enabled',True)) is not bool:
            raise DesignError('SOURCE_SCHEMA','Unknown source kind or invalid Used/Off value.')
        if not isinstance(src.get('values',{}),dict): raise DesignError('SOURCE_VALUES','Source values must be an object.')
        if set(src.get('values',{}))-set(DEFAULTS): raise DesignError('UNKNOWN_FIELD','A source contains unsupported fields.')
        try: canonical(src)
        except (ValueError,TypeError) as exc:
            raise DesignError('SOURCE_JSON','Sources must contain finite JSON data; NaN and infinity are not permitted.') from exc
        if src.get('unparsed_notice'): notices.append(src['unparsed_notice'])
    # Open spaces follow the plot unless an input states them.
    def strongest(key):
        cands=[x for x in sources if x.get('enabled',True) and key in x.get('values',{})]
        return max(cands,key=lambda x:SOURCE_PRIORITY[x['kind']])['values'][key] if cands else None
    w,d=strongest('width_mm'),strongest('depth_mm')
    if all(isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x) and x>0 for x in (w,d)):
        sources.insert(1,{'id':'derived-setbacks' if 'derived-setbacks' not in seen else 'derived-setbacks-auto','kind':'derived','enabled':True,
                          'values':derive_setbacks(w,d,strongest('parking') is True)})
    out={};provenance={};conflicts=[]
    for key in DEFAULTS:
        candidates=[s for s in sources if s.get('enabled',True) and key in s.get('values',{})]
        rank=max(SOURCE_PRIORITY[s['kind']] for s in candidates)
        chosen=[s for s in candidates if SOURCE_PRIORITY[s['kind']]==rank]
        if len({canonical(s['values'][key]) for s in chosen})>1:
            conflicts.append({'field':key,'sources':[s['id'] for s in chosen]})
            continue
        out[key]=chosen[0]['values'][key]
        provenance[key]={'value':out[key],'selected':[s['id'] for s in chosen],
                         'superseded':[s['id'] for s in candidates if s not in chosen]}
    if conflicts: raise DesignError('INPUT_CONFLICT','Equal-priority inputs disagree. Resolve them before generating.',conflicts)
    out=validate_values(out,custom=payload.get('customPlan') is not None)
    grid=payload.get('grid');grid_hints=[]
    if isinstance(grid,dict) and grid.get('mode')=='spatial_hint':
        grid_hints=_validate_spatial_grid(grid,out['storeys'])
    grid_labels={h['label'] for h in grid_hints}
    # Master bedroom and bedroom-N address the same stable planned room. A painted target wins over the prose alias too.
    if 'master-bedroom' in grid_labels:grid_labels.add(f'bedroom-{out["bedrooms"]}')
    if f'bedroom-{out["bedrooms"]}' in grid_labels:grid_labels.add('master-bedroom')
    placement={}
    for hint in _resolve_text_spatial(text_spatial,out['road_bearing_deg']):
        if hint['label'] in grid_labels:continue
        issue=_spatial_programme_issue(hint,out)
        if issue:
            notices.append(f'Ignored description placement "{hint["phrase"]}" because {issue}')
            continue
        old=placement.get(hint['label'])
        if old and math.hypot(old['x']-hint['x'],old['y']-hint['y'])>.15:
            raise DesignError('PLACEMENT_CONFLICT',f'The description gives more than one location for {hint["label"]}.')
        placement[hint['label']]=hint
    if grid_hints:
        # The painted board is the user's most direct placement instruction and therefore supersedes a prose location
        # for the same room.  Other prose fields continue through the normal source-priority rules above.
        for hint in grid_hints:placement[(hint.get('floor'),hint['label'])]=hint
        notices.append('The 4 x 4 board is a relative-position guide, not a dimension grid. Room sizes and circulation remain planner-determined.')
    placement_hints=list(placement.values());_check_spatial_programme(grid_hints,out)
    editor=payload.get('editorState')
    if editor is not None:
        if not isinstance(editor,dict) or set(editor)-{'mode','guideFloors','guideEdited','customPlan','savedRoomEdits','savedFurnitureLayout','usePlacements','roomBoard','useRoomBoard'} or editor.get('mode') not in ('automatic','guide','custom'):
            raise DesignError('EDITOR_STATE','Invalid saved editor state.')
        if 'usePlacements' in editor and type(editor['usePlacements']) is not bool:
            raise DesignError('EDITOR_STATE','Saved placement selection must be true or false.')
        if editor.get('roomBoard') is not None:
            from .room_board import normalize_board
            normalize_board(editor['roomBoard'])
        if 'useRoomBoard' in editor and type(editor['useRoomBoard']) is not bool:
            raise DesignError('EDITOR_STATE','Saved room board selection must be true or false.')
        from .placement_edits import normalize_edits
        normalize_edits({'roomEdits':editor.get('savedRoomEdits',[]),'furnitureLayout':editor.get('savedFurnitureLayout',[])})
        boards=editor.get('guideFloors')
        if not isinstance(boards,list) or len(boards)!=3 or any(not isinstance(board,list) or len(board)!=4 or any(not isinstance(row,list) or len(row)!=4 or any(not isinstance(x,str) or (x and x not in SPATIAL_LABELS) for x in row) for row in board) for board in boards):
            raise DesignError('EDITOR_GUIDES','Saved editor state needs three fixed 16-cell guide drafts.')
        if editor.get('customPlan') is not None:
            from .custom_plan import normalize
            saved=editor['customPlan'];n=len(saved.get('floors',[])) if isinstance(saved,dict) else 0
            if not 1<=n<=3:raise DesignError('EDITOR_FLOORS','Saved custom draft must have one to three floors.')
            normalize(saved,n)
    revision=payload.get('draftRevision',0)
    if type(revision) is not int or not 0<=revision<=9007199254740991:raise DesignError('DRAFT_REVISION','draftRevision must be a nonnegative safe integer.')
    custom=payload.get('customPlan')
    if custom is not None:
        if grid is not None:raise DesignError('PLAN_MODE','Choose either Custom Plan or Quick Guide for generation.')
        from .custom_plan import normalize
        custom=normalize(custom,out['storeys'])
        count=sum(room['kind']=='bedroom' for fl in custom['floors'] for room in fl['rooms'])
        if count!=out['bedrooms']:
            provenance['bedrooms']={'value':count,'selected':['custom-plan'],'superseded':provenance['bedrooms']['selected']}
            out['bedrooms']=count
            notices.append('The bedroom count is taken from the authored Custom Plan.')
        notices.append('Custom Plan is authoritative: room geometry, floor assignments and openings bypass the automatic planner.')
    from .placement_edits import normalize_edits
    placements=normalize_edits(payload)
    plan_hash=sha({'values':out,'grid':grid,'placement_hints':placement_hints,'customPlan':custom,**placements})
    attachments=payload.get('attachments',[])
    if not isinstance(attachments,list) or len(attachments)>12: raise DesignError('ATTACHMENT_LIMIT','Maximum 12 reference records.')
    for a in attachments:
        if not isinstance(a,dict) or set(a)-{'name','kind','sha256','note'}:
            raise DesignError('ATTACHMENT_SCHEMA','References contain name, kind, hash and note only; images stay on your device.')
    if attachments: notices.append('Uploaded images are references only until manually traced; automatic OCR/CV recognition is not implemented.')
    if out['eldercare']: notices.append('Eldercare request preserved. Specialist care-room and step-free access design require professional review; this generator does not certify them.')
    if provenance['front_mm']['selected'][:1]==[sources[1]['id']] and sources[1]['kind']=='derived':
        notices.append(f'Open spaces set from the plot size (typical Indian byelaw values): front {out["front_mm"]/1000:g} m, '
                       f'rear {out["rear_mm"]/1000:g} m, sides {out["left_mm"]/1000:g} m. Enter your authority\'s figures under Go deeper.')
    if reading:notices += reading['assumptions']
    notices += ['Setbacks are user-editable design assumptions, not verified municipal byelaws.',
                'Cost rates are editable illustrative scenarios, not researched local quotations.']
    result = {**placements,'planHash':plan_hash,'draftRevision':revision,'customPlan':custom,'values':out,'provenance':provenance,'sources':sources,'grid':grid,'placement_hints':placement_hints,'text_reading':reading,
            'attachments':attachments,'notes':payload.get('notes',''),'notices':notices,
            'schema':'floorforge.intent/0.2','orientation':'Road at local -Y; bearing is the outward road-facing true azimuth.'}
    from .input_audit import audit_inputs
    result['input_audit'] = audit_inputs(payload, result)
    return result
