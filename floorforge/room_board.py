"""A spatial room board compiled to connected, dimensioned geometry.

The board records relative positions, never clear dimensions. A shared passage
connects each room independently; one stair core is continued on every floor.
The normal custom compiler validates the resulting plan and exports.
"""
from __future__ import annotations
import copy,math
from .spaces import SPACE_REGISTRY,OPEN_SKY
from .model import DesignError

KINDS=set(SPACE_REGISTRY)-{'void','lift-shaft','stair-landing'}
def normalize_board(board):
    if not isinstance(board,dict) or set(board)-{'version','floors'} or board.get('version')!=1:
        raise DesignError('ROOM_BOARD','Choose rooms and positions on the room board.')
    floors=board.get('floors')
    if not isinstance(floors,list) or not 1<=len(floors)<=3:raise DesignError('ROOM_BOARD','Choose one to three floors.')
    ids=set();result={'version':1,'floors':[]}
    for f,fl in enumerate(floors):
        if not isinstance(fl,dict) or set(fl)!={'rooms'} or not isinstance(fl['rooms'],list) or len(fl['rooms'])>8:
            raise DesignError('ROOM_BOARD','Use up to eight room cards on each floor.')
        cells=set();rooms=[]
        for r in fl['rooms']:
            if not isinstance(r,dict) or set(r)!={'id','kind','name','col','row'}:raise DesignError('ROOM_BOARD','A room card has missing or unknown fields.')
            if not isinstance(r['id'],str) or not r['id'] or len(r['id'])>80 or r['id'] in ids:raise DesignError('ROOM_BOARD','Each room needs its own ID.')
            if r['kind'] not in KINDS or not isinstance(r['name'],str) or not 1<=len(r['name'])<=120:raise DesignError('ROOM_BOARD','Choose a room from the room list.')
            if type(r['col']) is not int or type(r['row']) is not int or not 0<=r['col']<2 or not 0<=r['row']<4:raise DesignError('ROOM_BOARD','Drop the room into a place on the board.')
            if (r['col'],r['row']) in cells:raise DesignError('ROOM_BOARD','Place one room card in each spot.')
            ids.add(r['id']);cells.add((r['col'],r['row']));rooms.append(copy.deepcopy(r))
        result['floors'].append({'rooms':sorted(rooms,key=lambda r:(r['row'],r['col']))})
    return result

def arrange(project,board):
    from .intent import fuse
    from .custom_plan import compile_plan
    from .review import validate
    board=normalize_board(board)
    base=copy.deepcopy(project)
    for k in ('grid','customPlan','roomEdits','furnitureLayout'):base.pop(k,None)
    base.setdefault('brief',{})['storeys']=len(board['floors'])
    # Programme counts are derived from the board after compilation. Use a
    # neutral count while resolving the site without an authored plan.
    base['brief']['bedrooms']=1
    for source in base.get('sources',[]):
        source.get('values',{}).pop('storeys',None)
        source.get('values',{}).pop('bedrooms',None)
    intent=fuse(base);v=intent['values'];W=v['width_mm']-v['left_mm']-v['right_mm'];D=v['depth_mm']-v['front_mm']-v['rear_mm']
    t=150;hall=1200;lane=(W-hall-4*t)/2
    if lane<2400:raise DesignError('BOARD_WIDTH','The buildable plot is too narrow for rooms on both sides. Increase the plot width or reduce the side open spaces on the home screen.')
    occupied={(f,r['col'],r['row']):r for f,fl in enumerate(board['floors']) for r in fl['rooms']}
    if not occupied:raise DesignError('ROOM_BOARD','Add a few rooms first, then build your layout.')
    stair_cards=[(f,r) for f,fl in enumerate(board['floors']) for r in fl['rooms'] if r['kind']=='stair']
    need_stair=len(board['floors'])>1 or v.get('roof_access') or bool(stair_cards)
    notes=[]
    if need_stair:
        if stair_cards:core=(stair_cards[0][1]['col'],stair_cards[0][1]['row'])
        else:
            free=[(c,r) for r in range(4) for c in range(2) if all((f,c,r) not in occupied for f in range(len(board['floors'])))]
            if not free:raise DesignError('BOARD_STAIR','Leave one spot for the staircase. It will connect every floor automatically.')
            core=free[0];notes.append('Added one staircase and connected it across the floors.')
        for f,fl in enumerate(board['floors']):
            stairs=[r for r in fl['rooms'] if r['kind']=='stair']
            if len(stairs)>1:raise DesignError('BOARD_STAIR','Use one staircase card. The same staircase serves every floor.')
            old=stairs[0] if stairs else None
            if old and (old['col'],old['row'])!=core:
                # Swap with the occupant instead of discarding it.
                other=occupied.pop((f,*core),None)
                occupied.pop((f,old['col'],old['row']),None)
                if other:other['col'],other['row']=old['col'],old['row'];occupied[(f,other['col'],other['row'])]=other
                old['col'],old['row']=core
                notes.append('Aligned the upstairs staircase with the one below; swapped the affected room.')
            elif not old:
                if (f,*core) in occupied:raise DesignError('BOARD_STAIR','The staircase position is occupied upstairs. Move that card to an empty spot; the blue stair spot is shared by all floors.')
                old={'id':f'board-stair-{f}','kind':'stair','name':'Staircase','col':core[0],'row':core[1]};fl['rooms'].append(old)
            occupied[(f,*core)]=old
        if v.get('roof_access'):notes.append('Stairs continue from the top floor to the roof terrace.')
    depth=[[0.0]*4 for _ in range(2)]
    for (f,c,row),r in occupied.items():
        spec=SPACE_REGISTRY[r['kind']]
        minimum=max(1200,spec['minimum_width_mm'],spec['minimum_area_m2']*1e6/lane)
        if r['kind']=='stair':minimum=2000+(math.ceil(v['floor_height_mm']/190/2)-1)*250
        if r['kind']=='dining':minimum=max(minimum,2400)
        depth[c][row]=max(depth[c][row],minimum)
    # Each side fits independently. A long staircase must not stretch the
    # room opposite it. Bands stay shared vertically so upper floors line up.
    bounds={}
    for col in range(2):
        rows=[i for i,d in enumerate(depth[col]) if d]
        if not rows:rows=[0];depth[col][0]=1200
        available=D-(len(rows)+1)*t
        total=sum(depth[col])
        if total>available:
            raise DesignError('BOARD_CAPACITY','These rooms need more space on one side. Move a card to an empty spot on the other side, remove one room, or increase the plot depth. Your arrangement is saved.')
        extra=(available-total)/len(rows);y=t
        for row in rows:
            height=depth[col][row]+extra;bounds[col,row]=(y,y+height);y+=height+t
    plan={'schema':'floorforge.custom-plan/1','units':'mm','wallThickness':t,'floors':[],'stairs':[]}
    def room(ident,kind,name,x,y,w,h):
        return {'id':ident,'kind':kind,'name':name,'polygon':[[round(x,3),round(y,3)],[round(x+w,3),round(y,3)],[round(x+w,3),round(y+h,3)],[round(x,3),round(y+h,3)]],**({'drain':True} if kind=='drying-room' else {})}
    def opening(ident,rid,kind,side,offset,width,height=2100,sill=0):
        return dict(id=ident,roomId=rid,kind=kind,side=side,offset=round(offset,3),width=round(width,3),height=height,sill=sill,hinge='start')
    blocked=set();stairs=[]
    for f,fl in enumerate(board['floors']):
        target={'id':f'board-floor-{f}','rooms':[],'walls':[],'openings':[]}
        hid=f'board-hall-{f}';target['rooms'].append(room(hid,'hall','Connecting hall',lane+2*t,t,hall,D-2*t))
        if f==0:target['openings'].append(opening('board-entry',hid,'entry','front',150,900))
        for col in range(2):
            for row in range(4):
                if (col,row) not in bounds:continue
                y,y1=bounds[col,row];h=y1-y
                r=occupied.get((f,col,row))
                if (col,row) in blocked:
                    if r:raise DesignError('BOARD_OPEN_AIR',f"{r['name']} sits above an open-air space. Move its card to a free spot; that outdoor area stays open.")
                    continue
                kind=r['kind'] if r else 'hall';rid=r['id'] if r else f'board-passage-{f}-{col}-{row}'
                x=t if col==0 else lane+hall+3*t
                q=room(rid,kind,r['name'] if r else 'Extra space',x,y,lane,h);target['rooms'].append(q)
                side='right' if col==0 else 'left'
                # Every room has its own door from the connecting hall. Stair doors enter the landing.
                target['openings'].append(opening('board-door-'+rid,rid,'door' if kind not in ('hall','living','dining','family','veranda','outer-lobby') else 'cased',side,75,900))
                if SPACE_REGISTRY[kind]['enclosed'] and kind not in ('hall','stair'):
                    width=min(1800,h-600)
                    target['openings'].append(opening('board-window-'+rid,rid,'window','left' if col==0 else 'right',(h-width)/2,width,1450,850))
                    # Front and rear rooms also face the garden/road, avoiding
                    # blank facades while using the existing window styling.
                    for edge,at_boundary in [('front',abs(y-t)<1),('rear',abs(y1-(D-t))<1)]:
                        if at_boundary:
                            facade_width=min(2400,lane-900)
                            target['openings'].append(opening('board-'+edge+'-window-'+rid,rid,'window',edge,(lane-facade_width)/2,facade_width,1450,850))
                if kind=='stair':stairs.append(rid)
        for r in fl['rooms']:
            if r['kind'] in OPEN_SKY:blocked.add((r['col'],r['row']))
        plan['floors'].append(target)
    if stairs:plan['stairs'].append(dict(id='board-linked-stair',roomIds=stairs,flightWidth=1000,well=200,landing=1000,tread=250))
    candidate={**base,'customPlan':plan};final=fuse(candidate)
    building=compile_plan(final);validate(building)
    return {'valid':True,'customPlan':final['customPlan'],'board':board,'planHash':final['planHash'],'notes':notes+['Added walls, a connected passage, doors and outside windows.'],'brief':v}
