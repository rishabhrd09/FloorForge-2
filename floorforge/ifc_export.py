"""Deterministic IFC4 coordination export. Independent IFC schema/viewer gate is external.

The author-written STEP serializer has no IfcOpenShell runtime dependency. The optional
scripts/verify_ifc.py worker uses an independently installed IfcOpenShell process.
"""
from __future__ import annotations
import re,uuid,math
from .model import *
from .scene import opening_polygon
from shapely.geometry import Polygon,box

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

def export_ifc(b):
    w=Writer();E=w.e;root=w.place();ctx=E('IFCGEOMETRICREPRESENTATIONCONTEXT','$',text('Model'),'3','0.00001',w.axis(),'$')
    units=E('IFCUNITASSIGNMENT','('+','.join([E('IFCSIUNIT','*','.LENGTHUNIT.','.MILLI.','.METRE.'),E('IFCSIUNIT','*','.AREAUNIT.','$','.SQUARE_METRE.'),E('IFCSIUNIT','*','.VOLUMEUNIT.','$','.CUBIC_METRE.'),E('IFCSIUNIT','*','.PLANEANGLEUNIT.','$','.RADIAN.')])+')')
    project=E('IFCPROJECT',text(guid('project')),'$',text(b['brief']['title']),text(b['banner']),'$','$','$','('+ctx+')',units)
    site=E('IFCSITE',text(guid('site')),'$',text('Unsurveyed plot'),'$','$',root,'$','$','.ELEMENT.','$','$','$','$','$')
    building=E('IFCBUILDING',text(guid('building')),'$',text('Preliminary house'),'$','$',root,'$','$','.ELEMENT.','$','$','$')
    def aggregate(key,a,children):E('IFCRELAGGREGATES',text(guid(key)),'$','$','$',a,'('+','.join(children)+')')
    aggregate('project-site',project,[site]);aggregate('site-building',site,[building])
    def rep(solid):return E('IFCPRODUCTDEFINITIONSHAPE','$','$','('+E('IFCSHAPEREPRESENTATION',ctx,text('Body'),text('SweptSolid'),'('+solid+')')+')')
    def properties(obj,key):
        p=E('IFCPROPERTYSINGLEVALUE',text('ReviewStatus'),'$',"IFCLABEL('PRELIMINARY - NOT FOR CONSTRUCTION')",'$')
        ps=E('IFCPROPERTYSET',text(guid('ps/'+key)),'$',text('FloorForge_Review'),'$','('+p+')')
        E('IFCRELDEFINESBYPROPERTIES',text(guid('rp/'+key)),'$','$','$','('+obj+')',ps)
    floors={}; placements={};contents={};spaces={};walls={};H=b['brief']['floor_height_mm']
    for floor in range(b['storeys']):
        place=w.place(floor*H,root);placements[floor]=place
        obj=E('IFCBUILDINGSTOREY',text(guid('floor/'+str(floor))),'$',text('Ground floor' if floor==0 else 'First floor'),'$','$',place,'$','$','.ELEMENT.',number(floor*H))
        floors[floor]=obj;contents[floor]=[];spaces[floor]=[]
    aggregate('building-floors',building,list(floors.values()))
    for wall in b['walls']:
        obj=E('IFCWALL',text(guid(wall['id'])),'$',text(wall['id']),text('Nominal wall; structural role unverified'),'$',placements[wall['floor']],rep(w.solid(Polygon(wall['polygon']),0,wall['height'])),text(wall['id']),'.NOTDEFINED.')
        walls[wall['id']]=obj;contents[wall['floor']].append(obj)
    for space in b['spaces']:
        obj=E('IFCSPACE',text(guid(space['id'])),'$',text(space['name']),text('Clear-space study volume'),'$',placements[space['floor']],rep(w.solid(Polygon(space['clear']),0,H-150)),text(space['id']),'.ELEMENT.','.NOTDEFINED.','$')
        spaces[space['floor']].append(obj)
    hosts={wall['id']:wall for wall in b['walls']}
    for opening in b['openings']:
        host=hosts[opening['wall_id']];p=opening_polygon(host,opening)
        obj=E('IFCOPENINGELEMENT',text(guid(opening['id'])),'$',text(opening['id']),text('Nominal '+opening['kind']+' aperture'),'$',placements[opening['floor']],rep(w.solid(p,opening['sill'],opening['height'])),text(opening['id']),'.OPENING.')
        E('IFCRELVOIDSELEMENT',text(guid('void/'+opening['id'])),'$','$','$',walls[opening['wall_id']],obj)
    for f in range(b['storeys']):
        p=Polygon(b['footprint'])
        if f and b['stairs']:
            st=b['stairs'][f];p=p.difference(box(st['x'],st['y']+st['landing_mm'],st['x']+st['width'],st['y']+st['depth']))
        obj=E('IFCSLAB',text(guid('slab/'+str(f))),'$',text('Floor slab / thickness assumption'),'$','$',placements[f],rep(w.solid(p,-150,150)),text('SL-'+str(f)),'.FLOOR.')
        contents[f].append(obj);properties(obj,'slab/'+str(f))
    roof_poly=Polygon(b['footprint'])
    for terrace in [s for s in b['spaces'] if s['floor']==b['storeys']-1 and s['kind']=='terrace']:
        roof_poly=roof_poly.difference(Polygon(terrace['polygon']))
    roof=E('IFCSLAB',text(guid('roof')),'$',text('Roof / thickness assumption'),'$','$',placements[b['storeys']-1],rep(w.solid(roof_poly,H-150,150)),text('ROOF'),'.ROOF.')
    contents[b['storeys']-1].append(roof)
    for f,fl in floors.items():
        E('IFCRELCONTAINEDINSPATIALSTRUCTURE',text(guid('contain/'+str(f))),'$','$','$','('+','.join(contents[f])+')',fl)
        aggregate('floor-spaces/'+str(f),fl,spaces[f])
    properties(building,'building')
    header="ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION(('ViewDefinition [DesignTransferView]','PRELIMINARY - ENGINEER TO REVIEW'),'2;1');\nFILE_NAME('FloorForge.ifc','2026-09-06T00:00:00',('FloorForge'),('FloorForge'),'FloorForge 0.2','FloorForge','');\nFILE_SCHEMA(('IFC4'));\nENDSEC;\nDATA;\n"
    result=header+'\n'.join(w.lines)+'\nENDSEC;\nEND-ISO-10303-21;\n'
    references=set(int(x) for x in re.findall(r'#(\d+)',result));defined=set(range(1,len(w.lines)+1))
    if references-defined:raise DesignError('IFC_DANGLING','IFC contains a dangling STEP reference.')
    return result.encode('ascii'),{'status':'STEP_reference_check_pass','entities':len(w.lines),'schema':'IFC4','independent_schema_validation':'NOT RUN','bim_viewer':'NOT RUN','scope':'Walls, spaces, floor/roof slabs, real related apertures, storeys. No reinforcement, finishes or certified MEP.'}
