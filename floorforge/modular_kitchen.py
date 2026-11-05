"""Authored L-shaped kitchen: front worktop, puja-divider return, opposite fridge."""
from shapely.geometry import box
from shapely.ops import unary_union


def l_shaped_kitchen(k, ctx, floor_height, finishes):
    room, floor = ctx['room'], ctx['floor']
    z = floor * floor_height
    x0, y0, x1, y1 = ctx['clear'].bounds
    owner = room['id'] + '/modular-kitchen'
    mark = k.edit_mark()

    def rect(bounds, material, name, role='furniture'):
        a,b,c,d,e,f = bounds
        return k.rect((a,b,z+c,d,e,z+f), material, floor, role, owner+'/'+name, owner)

    if room.get('kitchenLayout') == 'open-south-return':
        # A fitted perimeter kitchen leaves the enlarged working bay open to
        # the hall. Derive every run from the actual L-shaped clear polygon.
        clear = ctx['clear']
        left, front = x0 + .025, y0 + .025
        # Keep the fridge clear of a serving counter crossing the rear interface.
        rear_obstacles=[q for q in ctx.get('placed',[]) if not q.is_empty and q.intersects(box(left,y1-.50,left+.75,y1))]
        fridge_end=min([y1-.04]+[q.bounds[1]-.04 for q in rear_obstacles])
        end = fridge_end - .76
        east_run = clear.intersection(box(left, front, x1, front + .60)).buffer(-.025, join_style=2)
        south_run = box(left, front + .55, left + .60, end)
        worktop = unary_union([east_run, south_run])
        sink_x, sink_y = left + .30, front + 1.05
        sink = box(sink_x - .22, sink_y - .27, sink_x + .22, sink_y + .27)
        base = worktop.buffer(-.025, join_style=2)
        k.poly_mesh(base, z + .12, z + .69,
                    finishes['casework'], floor, 'furniture', owner + '/base', owner)
        k.poly_mesh(base.difference(sink.buffer(.01)), z + .69, z + .83,
                    finishes['casework'], floor, 'furniture', owner + '/base-sink-recess', owner)
        k.poly_mesh(worktop.difference(sink), z + .83, z + .87,
                    finishes['counter'], floor, 'furniture', owner + '/worktop', owner)
        k.poly_mesh(sink, z + .69, z + .70, 'appliance', floor, 'detail', owner + '/sink-bowl', owner)
        k.poly_mesh(sink.buffer(.015, join_style=2).difference(sink), z + .865, z + .878,
                    'appliance', floor, 'detail', owner + '/sink-rim', owner)
        k.poly_mesh(sink.difference(sink.buffer(-.01)), z + .70, z + .866,
                    'appliance', floor, 'detail', owner + '/sink-sides', owner)
        k.beam((sink_x - .24, sink_y, z + .87), (sink_x - .24, sink_y, z + 1.13),
               .022, 'steel', floor, 'detail')
        k.beam((sink_x - .24, sink_y, z + 1.13), (sink_x - .07, sink_y, z + 1.13),
               .022, 'steel', floor, 'detail')
        # Front hob and a continuous south preparation/sink run; no island in the circulation.
        hx, hy = east_run.centroid.x, front + .29
        rect((hx - .28, hy - .22, .87, hx + .28, hy + .22, .885), 'blackglass', 'hob', 'detail')
        for dx in (-.14, .14):
            for dy in (-.12, .12):
                k.cylinder((hx + dx, hy + dy, z + .89), .075, .012, 'frame', floor, 'detail')
        count = max(2, round((end - front - .60) / .60))
        span = (end - front - .60) / count
        for i in range(count):
            yy = front + .60 + i * span
            for j in range(3):
                low = .13 + j * .225
                rect((left + .598, yy + .01, low, left + .62, yy + span - .01, low + .21),
                     finishes['fronts'], f'drawer-{i}-{j}')
        # Upper storage only on the solid south wall, leaving the front window and hall clear.
        rect((left, front + .65, 1.55, left + .34, end - .03, 2.30), finishes['casework'], 'wall-storage')
        upper_count = max(2, round((end - front - .65) / .55))
        upper_span = (end - front - .65) / upper_count
        for i in range(upper_count):
            a = front + .65 + i * upper_span
            b = a + upper_span
            rect((left + .34, a + .008, 1.56, left + .36, b - .008, 2.29),
                 finishes['fronts'], f'wall-storage-front-{i}')
            rect((left + .36, a + .07, 1.59, left + .375, b - .07, 1.603),
                 'frame', f'wall-storage-pull-{i}', 'detail')
        k.light((left + .38, (front + .65 + end) / 2, z + 1.48), 18, kind='undercabinet')
        fridge = box(left, end + .05, left + .70, fridge_end)
        rect((fridge.bounds[0], fridge.bounds[1], .03, fridge.bounds[2], fridge.bounds[3], 2.05),
             'appliance', 'fridge')
        fx = fridge.bounds[2]
        for low, high, label in ((.06, .62, 'freezer'), (.64, 2.02, 'fridge-door')):
            rect((fx, fridge.bounds[1] + .012, low, fx + .018, fridge.bounds[3] - .012, high),
                 'appliance', label, 'detail')
            rect((fx + .018, fridge.bounds[1] + .08, high - .11, fx + .04,
                  fridge.bounds[3] - .08, high - .09), 'frame', label + '-pull', 'detail')
        for kind, footprint in [('kitchen-run', worktop), ('kitchen-fridge', fridge)]:
            assert clear.buffer(.001).covers(footprint), 'Kitchen furniture must stay inside its clear zone'
            ctx['placed'].append(footprint)
            k.furnishing(kind, room, footprint)
        for node in k.nodes[mark[0]:]:
            node['owner'] = owner
        return

    if x1 - x0 < 2.0:
        # Compact L-shaped kitchen (Tirumala Revision 8): East front worktop beneath window + South left leg + West-end fridge.
        back = y0 + .02
        front = y0 + .60
        left = x0 + .02
        turn = x0 + .62
        right = x1 - .04
        end = y1 - .82
        sx = (turn + right) / 2
        sy = (back + front) / 2
        sink = box(sx - .22, sy - .18, sx + .22, sy + .18)
        rect((left + .02, back + .02, .015, right - .02, front - .06, .11), 'frame', 'front-plinth')
        rect((left + .02, front, .015, turn - .06, end - .02, .11), 'frame', 'south-plinth')
        rect((left, back, .11, right, front - .02, .65), finishes['casework'], 'front-base')
        rect((left, front, .11, turn - .02, end, .65), finishes['casework'], 'south-base')
        worktop = unary_union([box(left, back, right, front), box(left, front, turn, end)])
        k.poly_mesh(worktop.difference(sink), z + .83, z + .865, finishes['counter'], floor, 'furniture', owner + '/l-worktop', owner)
        k.poly_mesh(sink.buffer(.015, join_style=2).difference(sink), z + .861, z + .87, 'appliance', floor, 'detail', owner + '/sink-rim', owner)
        hx, hy = left + .30, front + (end - front) * .45
        rect((hx - .22, hy - .26, .865, hx + .22, hy + .26, .878), 'blackglass', 'hob', 'detail')
        for dx in (-.11, .11):
            for dy in (-.14, .14):
                k.cylinder((hx + dx, hy + dy, z + .882), .075, .012, 'frame', floor, 'detail')
        rect((left, front, 1.58, left + .35, end, 2.32), finishes['casework'], 'south-wall-cabinet')
        rect((left + .35, front + .01, 1.59, left + .37, end - .01, 2.31), finishes['fronts'], 'south-wall-cabinet-front')
        k.light((left + .32, (front + end) / 2, z + 1.48), 10, kind='undercabinet')
        ctx['placed'].append(worktop)
        k.furnishing('kitchen-run', room, worktop)
        k.furnishing('kitchen-upper-storage', room, box(left, front, left + .37, end))
        fa, fb = left, left + .64
        ff, fy = end + .04, y1 - .04
        rect((fa, ff, .035, fb, fy, 2.05), 'appliance', 'fridge-body')
        fridge = box(fa, ff, fb, fy)
        ctx['placed'].append(fridge)
        k.furnishing('kitchen-fridge', room, fridge)
        for n in k.nodes[mark[0]:]:
            n['owner'] = owner
        return

    left, right, back = x0 + 1.01, x1 - .02, y0 + .02
    front, turn, end = y0 + .66, right - .64, y0 + 1.63
    sx=turn+.32; sy=(front+end)/2
    sink=box(sx-.205,sy-.27,sx+.205,sy+.27)

    # Recessed toe-kicks and full drawer fronts give the cabinetry a continuous,
    # fitted appearance. The corner is shared by both legs, with no doubled slab.
    rect((left+.03,back+.02,.015,right-.03,front-.08,.12),'frame','front-plinth')
    rect((turn+.08,front,.015,right-.03,end-.03,.12),'frame','return-plinth')
    count=4; width=(turn-left)/count
    for i in range(count):
        a=left+i*width; b=a+width
        body=box(a,back,b-.003,front-.026)
        rect((a,back,.11,b-.003,front-.026,.65),finishes['casework'],f'base-{i}')
        k.poly_mesh(body.difference(sink.buffer(.012,join_style=2)),z+.65,z+.83,finishes['casework'],floor,'furniture',owner+f'/base-top-{i}',owner)
        for j,(lo,hi) in enumerate(((.13,.34),(.352,.57),(.582,.815))):
            rect((a+.008,front-.023,lo,b-.008,front-.002,hi),finishes['fronts'],f'drawer-{i}-{j}')
            rect((a+.10,front-.002,hi-.045,b-.10,front+.012,hi-.029),'frame',f'pull-{i}-{j}','detail')
    rect((turn,back,.11,right,front-.026,.83),finishes['casework'],'corner-base')
    rect((turn+.008,front-.023,.13,right-.008,front-.002,.815),finishes['fronts'],'corner-door')
    rect((turn+.10,front-.002,.767,right-.10,front+.012,.783),'frame','corner-pull','detail')
    for i in range(2):
        a=front+i*(end-front)/2; b=front+(i+1)*(end-front)/2
        rect((turn+.026,a,.11,right,b-.004,.65),finishes['casework'],f'return-base-{i}')
        body=box(turn+.026,a,right,b-.004).difference(sink.buffer(.012,join_style=2))
        k.poly_mesh(body,z+.65,z+.83,finishes['casework'],floor,'furniture',owner+f'/return-base-top-{i}',owner)
        for j,(lo,hi) in enumerate(((.13,.34),(.352,.57),(.582,.815))):
            rect((turn+.002,a+.008,lo,turn+.023,b-.008,hi),finishes['fronts'],f'return-drawer-{i}-{j}')
            rect((turn-.012,a+.09,hi-.045,turn+.002,b-.09,hi-.029),'frame',f'return-pull-{i}-{j}','detail')
    # A true continuous L-shaped stone surface with an inset rectangular sink.
    worktop=unary_union([box(left,back,right,front),box(turn,front,right,end)])
    k.poly_mesh(worktop.difference(sink),z+.83,z+.865,finishes['counter'],floor,'furniture',owner+'/l-worktop',owner)
    k.poly_mesh(sink.buffer(.015,join_style=2).difference(sink),z+.861,z+.87,'appliance',floor,'detail',owner+'/sink-rim',owner)
    ax,ay,bx,by=sink.bounds
    rect((ax,ay,.665,bx,by,.677),'appliance','sink-bottom','detail')
    for i,p in enumerate((box(ax,ay,ax+.011,by),box(bx-.011,ay,bx,by),box(ax,ay,bx,ay+.011),box(ax,by-.011,bx,by))):
        k.poly_mesh(p,z+.675,z+.864,'appliance',floor,'detail',owner+f'/sink-side-{i}',owner)
    k.cylinder((sx,sy,z+.68),.025,.005,'frame',floor,'detail')
    k.beam((right-.065,sy,z+.866),(right-.065,sy,z+1.17),.012,'brass',floor,'detail')
    k.beam((right-.065,sy,z+1.17),(sx,sy,z+1.17),.012,'brass',floor,'detail')
    # The stove now occupies the former sink position beneath the window.
    hx,hy=left+1.15,back+.32
    rect((hx-.285,hy-.2575,.865,hx+.285,hy+.2575,.878),'blackglass','hob','detail')
    for dx in (-.155,.155):
        for dy in (-.13,.13):
            k.cylinder((hx+dx,hy+dy,z+.882),.085,.012,'frame',floor,'detail')
    # A low rear extractor replaces the hood over the now-relocated sink.
    # It stays below the window sill and keeps the glazing unobstructed.
    rect((hx-.28,back+.015,.865,hx+.28,back+.055,1.025),'appliance','rear-extractor','detail')
    rect((hx-.25,back+.056,.91,hx+.25,back+.062,1.01),'frame','extractor-grille','detail')
    rect((right-.02,back,.865,right,end,1.62),'tilewall','return-splashback','wall-tile')
    rect((left,back,.865,turn,back+.015,1.065),'tilewall','window-upstand','wall-tile')
    for i in range(3):
        a=back+i*(end-back)/3; b=back+(i+1)*(end-back)/3
        rect((right-.34,a,1.62,right,b-.005,2.38),finishes['casework'],f'wall-cabinet-{i}')
        rect((right-.362,a+.009,1.636,right-.342,b-.013,2.364),finishes['fronts'],f'wall-cabinet-front-{i}')
        rect((right-.377,a+.08,1.671,right-.363,b-.08,1.687),'frame',f'wall-cabinet-pull-{i}','detail')
    rect((right-.30,back+.02,1.603,right-.035,end-.02,1.612),'lamp','cabinet-light','fixture')
    k.light((right-.37,(back+end)/2,z+1.48),10,kind='undercabinet')
    ctx['placed'].append(worktop)
    k.furnishing('kitchen-run',room,worktop)
    k.furnishing('kitchen-upper-storage',room,box(right-.377,back,right,end))
    # The entire former rear prep run is removed. The standalone refrigerator
    # occupies that position, faces the worktop and has NO overhead cupboard.
    fc=x0+1.81; fa,fb=fc-.39,fc+.39; fy=y1-.08; ff=fy-.70
    rect((fa,ff,.035,fb,fy,2.085),'appliance','fridge-body')
    rect((fa+.012,ff-.025,.11,fb-.012,ff,1.48),'appliance','fridge-main-door')
    rect((fa+.012,ff-.025,1.497,fb-.012,ff,2.065),'appliance','fridge-freezer-door')
    rect((fa+.07,ff-.055,.86,fa+.087,ff-.025,1.38),'frame','fridge-pull','detail')
    rect((fa+.07,ff-.055,1.57,fa+.087,ff-.025,1.96),'frame','freezer-pull','detail')
    rect((fa+.07,ff-.027,.052,fb-.07,ff-.01,.096),'frame','fridge-vent','detail')
    fridge=box(fa,ff-.055,fb,fy)
    ctx['placed'].append(fridge)
    k.furnishing('kitchen-fridge',room,fridge)
    # Give every new detail a stable owner for scoped edits and regression checks.
    for n in k.nodes[mark[0]:]:n['owner']=owner
