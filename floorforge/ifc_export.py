"""Deterministic IFC4 coordination export. Independent IFC schema/viewer gate is external.

The author-written STEP serializer has no IfcOpenShell runtime dependency. The optional
scripts/verify_ifc.py worker uses an independently installed IfcOpenShell process.
"""
from __future__ import annotations
import re,uuid,math
from .model import *
from .scene import opening_polygon
from shapely.geometry import Polygon,box
from shapely import get_parts
from .plan_geometry import plate,roof

ALPHABET='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$'
def guid(key):
    n=uuid.uuid5(uuid.NAMESPACE_URL,'floorforge/'+key).int
    result=''
    for _ in range(22):result=ALPHABET[n%64]+result;n//=64
    return result

def text(value):
    out=''
    for char in str(value):
        n=ord(char)
        if char=="'":out+="''"
        elif char=='\\':out+='\\\\'
        elif 32<=n<=126:out+=char
        elif n<=65535:out+='\\X2\\'+f'{n:04X}'+'\\X0\\'
        else:out+='\\X4\\'+f'{n:08X}'+'\\X0\\'
    return "'"+out+"'"

def number(n):
    if not math.isfinite(float(n)):raise DesignError('IFC_NUMBER','IFC coordinates must be finite.')
    t=f'{float(n):.6f}'.rstrip('0');return t if t.endswith('.') else t

class Writer:
    def __init__(self):self.lines=[]
    def e(self,kind,*args):
        ref='#'+str(len(self.lines)+1);self.lines.append(ref+'='+kind+'('+','.join(args)+');');return ref
    def point(self,xyz):return self.e('IFCCARTESIANPOINT','('+','.join(number(x) for x in xyz)+')')
    def axis(self,z=0):return self.e('IFCAXIS2PLACEMENT3D',self.point([0,0,z]),'$','$')
    def place(self,z=0,parent='$'):return self.e('IFCLOCALPLACEMENT',parent,self.axis(z))
    def curve(self,polygon):
        pts=list(polygon.exterior.coords);return self.e('IFCPOLYLINE','('+','.join(self.point(xy) for xy in pts)+')')
    def solid(self,p,z,depth):
        if p.interiors:
            holes=[]
            for ring in p.interiors:
                holes.append(self.e('IFCPOLYLINE','('+','.join(self.point(xy) for xy in ring.coords)+')'))
            profile=self.e('IFCARBITRARYPROFILEDEFWITHVOIDS','.AREA.','$',self.curve(p),'('+','.join(holes)+')')
        else:profile=self.e('IFCARBITRARYCLOSEDPROFILEDEF','.AREA.','$',self.curve(p))
        return self.e('IFCEXTRUDEDAREASOLID',profile,self.axis(z),self.e('IFCDIRECTION','(0.,0.,1.)'),number(depth))

def export_ifc(b, scene=None):
    from .rooftop import with_rooftop_objects
    b=with_rooftop_objects(b)
    w=Writer();E=w.e;root=w.place();ctx=E('IFCGEOMETRICREPRESENTATIONCONTEXT','$',text('Model'),'3','0.00001',w.axis(),'$')
    units=E('IFCUNITASSIGNMENT','('+','.join([E('IFCSIUNIT','*','.LENGTHUNIT.','.MILLI.','.METRE.'),E('IFCSIUNIT','*','.AREAUNIT.','$','.SQUARE_METRE.'),E('IFCSIUNIT','*','.VOLUMEUNIT.','$','.CUBIC_METRE.'),E('IFCSIUNIT','*','.PLANEANGLEUNIT.','$','.RADIAN.')])+')')
    project=E('IFCPROJECT',text(guid('project')),'$',text(b['brief']['title']),text(b['banner']),'$','$','$','('+ctx+')',units)
    site=E('IFCSITE',text(guid('site')),'$',text('Unsurveyed plot'),'$','$',root,'$','$','.ELEMENT.','$','$','$','$','$')
    building=E('IFCBUILDING',text(guid('building')),'$',text('Preliminary house'),'$','$',root,'$','$','.ELEMENT.','$','$','$')
    def aggregate(key,a,children):E('IFCRELAGGREGATES',text(guid(key)),'$','$','$',a,'('+','.join(children)+')')
    aggregate('project-site',project,[site]);aggregate('site-building',site,[building])
    def rep(solid):return E('IFCPRODUCTDEFINITIONSHAPE','$','$','('+E('IFCSHAPEREPRESENTATION',ctx,text('Body'),text('SweptSolid'),'('+(','.join(solid) if isinstance(solid,list) else solid)+')')+')')
    def properties(obj,key):
        p=E('IFCPROPERTYSINGLEVALUE',text('ReviewStatus'),'$',"IFCLABEL('PRELIMINARY - NOT FOR CONSTRUCTION')",'$')
        ph=E('IFCPROPERTYSINGLEVALUE',text('PlanHash'),'$',f"IFCLABEL({text(b.get('planHash','legacy'))})",'$')
        ps=E('IFCPROPERTYSET',text(guid('ps/'+key)),'$',text('FloorForge_Review'),'$','('+p+','+ph+')')
        E('IFCRELDEFINESBYPROPERTIES',text(guid('rp/'+key)),'$','$','$','('+obj+')',ps)
    floors={}; placements={};contents={};spaces={};walls={};H=b['brief']['floor_height_mm']
    for floor in range(b['storeys']+bool(b.get('rooftop'))):
        place=w.place(floor*H,root);placements[floor]=place
        obj=E('IFCBUILDINGSTOREY',text(guid('floor/'+str(floor))),'$',text('Roof terrace' if floor==b['storeys'] else ['Ground floor','First floor','Second floor'][floor]),'$','$',place,'$','$','.ELEMENT.',number(floor*H))
        floors[floor]=obj;contents[floor]=[];spaces[floor]=[]
    aggregate('building-floors',building,list(floors.values()))
    for wall in b['walls']:
        obj=E('IFCWALL',text(guid(wall['id'])),'$',text(wall['id']),text('Nominal wall; structural role unverified'),'$',placements[wall['floor']],rep(w.solid(Polygon(wall['polygon']),0,wall['height'])),text(wall['id']),'.NOTDEFINED.')
        walls[wall['id']]=obj;contents[wall['floor']].append(obj)
    for space in b['spaces']:
        obj=E('IFCSPACE',text(guid(space['id'])),'$',text(space['name']),text('Clear-space study volume'),'$',placements[space['floor']],rep(w.solid(Polygon(space['clear'],space.get('holes',[])),0,space.get('ceilingHeight',H-150))),text(space['id']),'.ELEMENT.','.NOTDEFINED.','$')
        spaces[space['floor']].append(obj)
    for step in b.get('entrance_steps',[]):
        obj=E('IFCSLAB',text(guid(step['id'])),'$',text('Dining entrance step'),'$','$',placements[0],rep(w.solid(Polygon(step['polygon']),step['bottom'],step['top']-step['bottom'])),text(step['id']),'.LANDING.')
        contents[0].append(obj)
    hosts={wall['id']:wall for wall in b['walls']}
    for opening in b['openings']:
        host=hosts[opening['wall_id']];p=opening_polygon(host,opening)
        obj=E('IFCOPENINGELEMENT',text(guid(opening['id'])),'$',text(opening['id']),text('Nominal '+opening['kind']+' aperture'),'$',placements[opening['floor']],rep(w.solid(p,opening['sill'],opening['height'])),text(opening['id']),'.OPENING.')
        E('IFCRELVOIDSELEMENT',text(guid('void/'+opening['id'])),'$','$','$',walls[opening['wall_id']],obj)
    def solids(p,z,depth):
        return [w.solid(part,z,depth) for part in get_parts(p) if part.geom_type=='Polygon' and part.area>1]
    for f in range(b['storeys']):
        obj=E('IFCSLAB',text(guid('slab/'+str(f))),'$',text('Floor slab / thickness assumption'),'$','$',placements[f],rep(solids(plate(b,f),-150,150)),text('SL-'+str(f)),'.FLOOR.')
        contents[f].append(obj);properties(obj,'slab/'+str(f))
        p=roof(b,f)
        if not p.is_empty:
            obj=E('IFCSLAB',text(guid('roof/'+str(f))),'$',text('Roof / thickness assumption'),'$','$',placements[f],rep(solids(p,H-150,150)),text('ROOF-'+str(f)),'.ROOF.')
            contents[f].append(obj);properties(obj,'roof/'+str(f))
    if b.get('planning',{}).get('custom') or b.get('rooftop'):
        for st in b['stairs']:
            if st['to_floor'] is None:continue
            from .stair_geometry import shape as stair_shape
            stair_box=lambda *args: stair_shape(st,box(*args))
            n=st['riser_count']//2;steps=n-1;x=st['x'];y=st['y'];fw=st['flight_width'];land=st['landing_mm'];t=st['tread_mm'];r=st['riser_mm'];parts=[]
            for j in range(steps):
                yy=y+land+j*t;bottom=max(0,j*r-80);parts.append(w.solid(stair_box(x,yy,x+fw,yy+t),bottom,(j+1)*r-bottom))
                yy=y+land+(steps-1-j)*t;bottom=n*r+j*r-90;parts.append(w.solid(stair_box(x+fw+st['well'],yy,x+st['width'],yy+t),bottom,(n+1+j)*r-bottom))
            parts.append(w.solid(stair_box(x,y+land+steps*t,x+st['width'],y+2*land+steps*t),n*r-160,160))
            parts.append(w.solid(stair_box(x,y,x+st['width'],y+land),H-160,160))
            obj=E('IFCSTAIR',text(guid(st['id'])),'$',text('Linked U staircase'),'$','$',placements[st['floor']],rep(parts),text(st['id']),'.HALF_TURN_STAIR.')
            contents[st['floor']].append(obj);properties(obj,st['id'])
        from shapely.geometry import LineString
        for guard in b.get('guards',[]):
            p=LineString(guard['points']).buffer(8,cap_style=2,join_style=2)
            obj=E('IFCRAILING',text(guid(guard['id'])),'$',text('Exposed-edge guard'),'$','$',placements[guard['floor']],rep(solids(p,60,1040)),text(guard['id']),'.GUARDRAIL.')
            contents[guard['floor']].append(obj)
    if b.get('rooftop'):
        for core in b['rooftop']['cores']:
            p=box(*core['bounds']).buffer(180,join_style=2)
            obj=E('IFCSLAB',text(guid(core['id']+'-lid')),'$',text('Stair headhouse roof'),'$','$',placements[b['storeys']],rep(solids(p,2500,200)),text(core['id']+'-lid'),'.ROOF.')
            contents[b['storeys']].append(obj)
    if scene:
        # The same authored component meshes used by GLB, with placement overrides already applied.
        import numpy as np
        from .scene import transformation
        nodes={n['id']:n for n in scene['nodes']}
        for item in scene.get('editables',[]):
            meshes=[]
            for ident in item['nodeIds']:
                node=nodes[ident];asset=scene['assets'][node['asset']]
                vertices=np.array(asset['vertices'],float)
                matrix=transformation(node)
                vertices=(vertices @ matrix[:3,:3].T+matrix[:3,3])*1000
                vertices[:,2]-=item['floor']*H
                points=E('IFCCARTESIANPOINTLIST3D','('+','.join('('+','.join(number(x) for x in v)+')' for v in vertices)+')')
                faces='('+','.join('('+','.join(str(i+1) for i in face)+')' for face in asset['faces'])+')'
                meshes.append(E('IFCTRIANGULATEDFACESET',points,'$', '.T.' if asset.get('closed') else '.F.',faces,'$'))
            shape=E('IFCPRODUCTDEFINITIONSHAPE','$','$','('+E('IFCSHAPEREPRESENTATION',ctx,text('Body'),text('Tessellation'),'('+','.join(meshes)+')')+')')
            obj=E('IFCFURNISHINGELEMENT',text(guid(item['id'])),'$',text(item['label']),text('Authored furniture assembly'),'$',placements[item['floor']],shape,text(item['id']))
            contents[item['floor']].append(obj);properties(obj,item['id'])
    for f,fl in floors.items():
        E('IFCRELCONTAINEDINSPATIALSTRUCTURE',text(guid('contain/'+str(f))),'$','$','$','('+','.join(contents[f])+')',fl)
        aggregate('floor-spaces/'+str(f),fl,spaces[f])
    properties(building,'building')
    header="ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION(('ViewDefinition [DesignTransferView]','PRELIMINARY - ENGINEER TO REVIEW'),'2;1');\nFILE_NAME('FloorForge.ifc','2026-09-06T00:00:00',('FloorForge'),('FloorForge'),'FloorForge 0.2','FloorForge','');\nFILE_SCHEMA(('IFC4'));\nENDSEC;\nDATA;\n"
    result=header+'\n'.join(w.lines)+'\nENDSEC;\nEND-ISO-10303-21;\n'
    references=set(int(x) for x in re.findall(r'#(\d+)',result));defined=set(range(1,len(w.lines)+1))
    if references-defined:raise DesignError('IFC_DANGLING','IFC contains a dangling STEP reference.')
    return result.encode('ascii'),{'status':'STEP_reference_check_pass','entities':len(w.lines),'schema':'IFC4','independent_schema_validation':'NOT RUN','bim_viewer':'NOT RUN','furnishing_count':len(scene.get('editables',[])) if scene else 0,'scope':'Walls, spaces, floor/roof slabs, related apertures, storeys; authored movable furniture meshes when a scene is supplied. No reinforcement or certified MEP.'}
