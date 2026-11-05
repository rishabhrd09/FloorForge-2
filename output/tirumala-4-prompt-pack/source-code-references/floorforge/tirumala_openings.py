"""Operable joinery for P11/P12; aperture coordinates remain in the approved plan."""
import math
import numpy as np
import trimesh


def pose_initial_opening(k, motion):
    """Bake the default open pose into exports as well as the interactive viewer.

    Runtime transforms then reverse from that pose to close the leaf. This keeps
    GLB/IFC reference meshes and the first interactive frame visually consistent.
    """
    layers = motion.get('layers', [motion])
    nodes = {n['id']: n for n in k.nodes}
    for layer in layers:
        if layer.get('initial', motion.get('initial', 0)) != 1:
            continue
        for part in layer['parts']:
            p = np.array(part.get('pivot', [0, 0, 0]), dtype=float)
            shift = np.array(part.get('slide', [0, 0, 0]), dtype=float)
            angle = part.get('angle', 0)
            scale = np.array(part.get('scaleTo', [1, 1, 1]), dtype=float)
            c, s = math.cos(angle), math.sin(angle)
            r = np.array([[c,-s,0],[s,c,0],[0,0,1]]) @ np.diag(scale)
            matrix = np.eye(4); matrix[:3,:3] = r; matrix[:3,3] = p + shift - r @ p
            if part is layer['parts'][0] and layer.get('handle'):
                layer['handle'] = (matrix @ np.array([*layer['handle'],1]))[:3].tolist()
            for ident in part['ids']:
                node = nodes[ident]; asset = k.assets[node['asset']]
                mesh = trimesh.Trimesh(vertices=asset['vertices'], faces=asset['faces'], process=False)
                mesh.apply_transform(matrix)
                node['asset'] = k.asset(mesh)
            part.update({'pivot':(p+shift).tolist(), 'slide':(-shift).tolist(), 'angle':-angle, 'reverse':True})
            if 'scaleTo' in part:
                part['scaleTo'] = (1 / scale).tolist()


def build_opening(k, op, plan, span_box):
    """Return explicit closed-to-open transforms for complete leaves, including their frames."""
    oid, kind = op['id'], op['raw_kind']
    a = [v / 1000 for v in op['a']]
    b = [v / 1000 for v in op['b']]
    length = math.dist(a, b)
    u = [(b[i] - a[i]) / length for i in range(2)]
    sill, top = op['sill'] / 1000, (op['sill'] + op['height']) / 1000
    fw = .055

    def at(t, z=0):
        return [a[0] + t*u[0], a[1] + t*u[1], z]

    def panel(lo, hi, index, material='icu-glass', wood=False, depth=0):
        mark = len(k.nodes)
        if wood:
            span_box(lo, hi, depth-.022, depth+.022, sill+.015, top-fw, material, 'door', f'leaf-{index}')
        else:
            for name, x0, x1, z0, z1 in [
                ('left',lo,lo+.032,sill+fw,top-fw), ('right',hi-.032,hi,sill+fw,top-fw),
                ('bottom',lo,hi,sill+fw,sill+.087), ('top',lo,hi,top-.087,top-fw)]:
                span_box(x0,x1,depth-.015,depth+.015,z0,z1,'frame','frame',f'leaf-{index}-{name}')
            span_box(lo+.032,hi-.032,depth-.006,depth+.006,sill+.087,top-.087,material,'glass',f'leaf-{index}-glass')
        span_box(hi-.10,hi-.08,depth-.045,depth+.045,1.0,1.22,'brass','detail',f'leaf-{index}-handle')
        return [n['id'] for n in k.nodes[mark:]]

    if kind == 'glass':
        if oid != 'icu-glass-living':
            # The veranda opening retains its approved slide-and-turn side stack;
            # there is insufficient straight wall beside it for a pocket track.
            x0,y0,x1,y1=[v/1000 for v in plan['verandaGlass']['stackBounds']]
            width=(length-2*fw)/3;parts=[]
            for i in range(3):
                lo,hi=fw+i*width,fw+(i+1)*width
                ids=panel(lo,hi,i);center=at((lo+hi)/2)
                target=[(x0+x1)/2+(i-1)*.035*u[0],(y0+y1)/2+(i-1)*.035*u[1],0]
                parts.append({'ids':ids,'pivot':center,'angle':math.pi/2,
                              'slide':[target[j]-center[j] for j in range(3)]})
            return {'parts':parts,'initial':1,'clearWidth':length-2*fw}
        # Hall -> timber privacy panels -> glass slider -> ICU.
        # The positive opening normal points into the hall in both approved plans.
        # Wood conceals the glass when closed; each layer uses its own parallel tracks.
        width = (length-2*fw)/4
        parts=[]
        for i in range(4):
            lo,hi=fw+i*width,fw+(i+1)*width
            ids=panel(lo,hi,i,depth=-.085-i*.035)
            center=at((lo+hi)/2)
            target=at(-width/2-.07)
            parts.append({'ids':ids,'pivot':center,'angle':0,
                          'slide':[target[j]-center[j] for j in range(3)]})
        timber=[]
        for i in range(4):
            lo=fw+i*(length-2*fw)/4;hi=fw+(i+1)*(length-2*fw)/4
            ids=panel(lo,hi,f'wood-{i}',material='teak-warm',wood=True,depth=.095+i*.055)
            center=at((lo+hi)/2);target=at(-(hi-lo)/2-.07)
            timber.append({'ids':ids,'slide':[target[j]-center[j] for j in range(3)]})
        # Select the outermost parked panel's handle, not one hidden in the stack.
        timber.reverse()
        handle=at(length-fw-.09,1.1)
        handle[0]+=-u[1]*.260;handle[1]+=u[0]*.260
        return {'layerOrderFromHall':['wood','glass'],
                'layers':[{'id':oid,'label':'Sliding glass behind wooden ICU door','parts':parts},
                           {'id':oid+'-wood','label':'Wooden ICU door concealing glass','parts':timber,'handle':handle}],
                'initial':1,'clearWidth':length-2*fw}

    if oid == 'living-veranda':
        layers=[]
        parts=[]
        for i in range(4):
            lo=fw+i*(length-2*fw)/4; hi=fw+(i+1)*(length-2*fw)/4
            ids=panel(lo,hi,f'wood-{i}',material='teak-warm',wood=True)
            center=at((lo+hi)/2)
            x0,y0,x1,y1=[v/1000 for v in plan['entrance']['woodStacks'][i//2]]
            target=[(x0+x1)/2+(i%2-.5)*.045*u[0],(y0+y1)/2+(i%2-.5)*.045*u[1],0]
            parts.append({'ids':ids,'pivot':center,'angle':math.pi/2,
                          'slide':[target[j]-center[j] for j in range(3)]})
        layers.append({'id':oid+'-wood','label':'Folding wooden entrance','parts':parts})
        parts=[]
        for i in range(2):
            lo=fw+i*(length-2*fw)/2; hi=fw+(i+1)*(length-2*fw)/2
            mark=len(k.nodes)
            span_box(lo,hi,.063,.071,.015,top-fw,'insect-mesh','door',f'mesh-{i}')
            span_box(hi-.015,hi,.058,.076,.015,top-fw,'frame','door',f'mesh-rail-{i}')
            center=at((lo+hi)/2)
            x0,y0,x1,y1=[v/1000 for v in plan['entrance']['meshStacks'][i]]
            target=[(x0+x1)/2,(y0+y1)/2,0]
            parts.append({'ids':[n['id'] for n in k.nodes[mark:]],'pivot':center,'angle':0,
                          'scaleTo':[.025 if abs(u[0])>.5 else 1,.025 if abs(u[1])>.5 else 1,1],
                          'slide':[target[j]-center[j] for j in range(3)]})
        layers.append({'id':oid+'-mesh','label':'Retractable insect screen','parts':parts})
        return {'layers':layers,'initial':1,'clearWidth':length-2*fw}

    if kind == 'sliding-door':
        ids=panel(fw,length-fw,0,material='frosted')
        return {'parts':[{'ids':ids,'slide':[-u[0]*length,-u[1]*length,0]}],
                'initial':0,'clearWidth':length-2*fw}

    if kind == 'door':
        ids=panel(fw,length-fw,0,material='teak-warm' if 'drawing' in oid else 'oak-warm',wood=True)
        end=op.get('hinge') in ('b','end')
        hinge=b if end else a
        closed=[-v if end else v for v in u]
        swing=op.get('swing_vec')
        direction=[swing[i]/1000-hinge[i] for i in range(2)] if swing else [-u[1],u[0]]
        angle=math.atan2(direction[1],direction[0])-math.atan2(closed[1],closed[0])
        return {'parts':[{'ids':ids,'pivot':[*hinge,0],'angle':math.atan2(math.sin(angle),math.cos(angle))}],
                'initial':0,'clearWidth':length-2*fw}

    if op.get('window_style') == 'picture-with-sliding-vents':
        # A broad fixed centre retains the view; narrow side sashes slide across it.
        # No sash projects into the north gully or terrace walking route.
        span=length-2*fw;side=span*.23
        panel(fw+side,length-fw-side,'picture',material='glass')
        parts=[]
        for i,(lo,hi,shift) in enumerate([(fw,fw+side,side),(length-fw-side,length-fw,-side)]):
            ids=panel(lo,hi,f'vent-{i}',material='glass',depth=.042)
            parts.append({'ids':ids,'slide':[u[0]*shift,u[1]*shift,0]})
        return {'parts':parts,'initial':0,'style':'picture-with-sliding-vents'}

    # Window sashes carry their frames and handles with them, rather than moving only the glass.
    count=3 if length>=1.75 else 2 if length>=.95 else 1
    parts=[]
    for i in range(count):
        lo=fw+i*(length-2*fw)/count; hi=fw+(i+1)*(length-2*fw)/count
        ids=panel(lo,hi,i,material='glass')
        parts.append({'ids':ids,'pivot':at(lo,sill),'angle':-math.pi/2})
    return {'parts':parts,'initial':0}
