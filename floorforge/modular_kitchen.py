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


def straight_run_kitchen(k, ctx, floor_height, finishes, spec=None):
    """Straight east-wall modular kitchen run + work-bay tall units + prep counter (Tirumala 7).

    Ergonomics follow standard Indian modular kitchen dimensions:
    - Worktop height: 860 mm (within 850-900 mm), depth: 600 mm
    - Backsplash height: 600 mm (from +860 mm to +1460 mm)
    - Upper cabinets: +1460 mm to +2160 mm (depth 350 mm)
    - Stepped full-depth ceiling loft: +2160 mm to +2970 mm (depth 600 mm)
    """
    room, floor = ctx['room'], ctx['floor']
    z = floor * floor_height
    owner = room['id'] + '/modular-kitchen'
    mark = k.edit_mark()
    spec = spec or {}

    def rect(bounds, material, name, role='furniture'):
        a, b, c, d, e, f = bounds
        return k.rect((a, b, z + c, d, e, z + f), material, floor, role, owner + '/' + name, owner)

    # In building coordinates (+X north, +Y west):
    # East exterior wall (at x_ft=47.0, 3' west of plot line) inner face is at y_wall (~0.9744 m).
    # Wide 2'9" (840 mm) quartz platform extends west to y_front (~1.8144 m), running uninterrupted
    # along the east wall from x_south (y_ft=34.75 -> 1.6002 m) to x_north (y_ft=22.25 -> 5.4102 m).
    x_south = spec.get('x_south', 1.6002)
    x_north = spec.get('x_north', 5.4102)
    y_wall = spec.get('y_wall', 0.9744)
    depth = spec.get('depth', 0.840)
    y_front = y_wall + depth

    # Sink centered beneath the north east-wall kitchen window (y_ft 23.50..25.70 -> X 4.3586..5.0292 m)
    sink_x0 = spec.get('sink_x0', 4.3586)
    sink_x1 = spec.get('sink_x1', 5.0292)
    sink_xm = 0.5 * (sink_x0 + sink_x1)
    sink_ym = y_wall + 0.5 * depth

    # Hob positioned on the solid masonry pier between the two east windows (X 2.84..3.46 m)
    hob_x0 = spec.get('hob_x0', 2.8400)
    hob_x1 = spec.get('hob_x1', 3.4600)
    hob_xm = 0.5 * (hob_x0 + hob_x1)
    hob_ym = y_wall + 0.48 * depth

    teal_gloss = finishes.get('fronts', 'kitchen_sage_teal_gloss')
    teal_loft = finishes.get('loft', 'kitchen_sage_teal_loft')
    gola_black = finishes.get('gola', 'gola_matte_black')
    quartz_top = finishes.get('counter', 'quartz_nano_white')
    fluted_splash = finishes.get('backsplash', 'backsplash_fluted_ivory')
    teak_wood = finishes.get('casework', 'cladding_fluted_teak')
    led_warm = finishes.get('led', 'cove_led_warm')
    smoked_glass = finishes.get('smoked_glass', 'glass_smoked_fluted')

    # 1. Recessed dark plinth kickboard (0..100 mm) + warm LED toe-kick + deep base carcass (100..832 mm)
    rect((x_south, y_wall, 0.0, x_north, y_front - 0.050, 0.100), gola_black, 'plinth-kickboard', 'detail')
    rect((x_south + 0.04, y_front - 0.052, 0.015, x_north - 0.04, y_front - 0.036, 0.032), led_warm, 'plinth-toe-led', 'cove')
    worktop_poly = box(x_south, y_wall, x_north, y_front)
    sink_box = box(sink_x0 + 0.05, y_wall + 0.14, sink_x1 - 0.05, y_front - 0.16)
    base_poly = box(x_south, y_wall, x_north, y_front - 0.022)
    k.poly_mesh(base_poly.difference(sink_box.buffer(0.01)), z + 0.100, z + 0.832,
                teak_wood, floor, 'furniture', owner + '/base-carcass', owner)

    # 2. Matte-black horizontal Gola J-profile channels (+808..832 mm and +465..485 mm)
    rect((x_south, y_front - 0.030, 0.808, x_north, y_front - 0.004, 0.832), gola_black, 'gola-top-channel', 'detail')
    rect((x_south, y_front - 0.030, 0.465, x_north, y_front - 0.004, 0.485), gola_black, 'gola-mid-channel', 'detail')

    # 3. Full under-platform modular storage: 6 wide high-gloss sage-teal drawer & shutter bays
    bays = 6
    bay_w = (x_north - x_south) / bays
    for i in range(bays):
        bx0 = x_south + i * bay_w + 0.004
        bx1 = x_south + (i + 1) * bay_w - 0.004
        if abs(0.5 * (bx0 + bx1) - sink_xm) < bay_w * 0.55:
            bm = 0.5 * (bx0 + bx1)
            rect((bx0, y_front - 0.022, 0.105, bm - 0.002, y_front, 0.806), teal_gloss, f'sink-door-L-{i}')
            rect((bm + 0.002, y_front - 0.022, 0.105, bx1, y_front, 0.806), teal_gloss, f'sink-door-R-{i}')
        elif abs(0.5 * (bx0 + bx1) - hob_xm) < bay_w * 0.65:
            rect((bx0, y_front - 0.022, 0.105, bx1, y_front, 0.340), teal_gloss, f'hob-drawer-bot-{i}')
            rect((bx0, y_front - 0.022, 0.346, bx1, y_front, 0.575), teal_gloss, f'hob-drawer-mid-{i}')
            rect((bx0, y_front - 0.022, 0.581, bx1, y_front, 0.806), teal_gloss, f'hob-drawer-top-{i}')
        else:
            rect((bx0, y_front - 0.022, 0.105, bx1, y_front, 0.462), teal_gloss, f'base-drawer-low-{i}')
            rect((bx0, y_front - 0.022, 0.488, bx1, y_front, 0.806), teal_gloss, f'base-drawer-high-{i}')

    # 4. Wide 840 mm Nano-white engineered quartz platform (832..865 mm) + sill-safe 80 mm upstand
    k.poly_mesh(worktop_poly.difference(sink_box), z + 0.832, z + 0.865,
                quartz_top, floor, 'furniture', owner + '/quartz-worktop', owner)
    # Upstand tops out at +945 mm so it stays cleanly below the +960 mm east-wall kitchen windows
    rect((x_south, y_wall, 0.865, x_north, y_wall + 0.020, 0.945), quartz_top, 'quartz-upstand', 'detail')

    # 5. Matte-black undermount quartz sink + drainboard + sleek gooseneck mixer under north east window
    k.poly_mesh(sink_box, z + 0.675, z + 0.692, gola_black, floor, 'detail', owner + '/sink-bottom', owner)
    k.poly_mesh(sink_box.buffer(0.018, join_style=2).difference(sink_box), z + 0.860, z + 0.868,
                gola_black, floor, 'detail', owner + '/sink-rim', owner)
    k.poly_mesh(sink_box.difference(sink_box.buffer(-0.012)), z + 0.692, z + 0.862,
                gola_black, floor, 'detail', owner + '/sink-walls', owner)
    rect((sink_x1 - 0.02, y_wall + 0.16, 0.863, sink_x1 + 0.24, y_front - 0.18, 0.868), gola_black, 'sink-drainboard', 'detail')
    k.cylinder((sink_xm, sink_ym, z + 0.693), 0.042, 0.006, 'steel', floor, 'detail')
    tap_x, tap_y = sink_xm, y_wall + 0.085
    k.cylinder((tap_x, tap_y, z + 0.865), 0.024, 0.055, gola_black, floor, 'detail')
    k.beam((tap_x, tap_y, z + 0.90), (tap_x, tap_y, z + 1.15), 0.018, gola_black, floor, 'detail')
    k.beam((tap_x, tap_y, z + 1.15), (tap_x, tap_y + 0.22, z + 1.15), 0.018, gola_black, floor, 'detail')
    k.beam((tap_x, tap_y + 0.22, z + 1.15), (tap_x, tap_y + 0.22, z + 1.03), 0.022, gola_black, floor, 'detail')

    # 6. 3-burner black glass hob + fluted splash panel + sleek architectural T-chimney on the center pier (clear of both east windows)
    pier_x0 = spec.get('pier_x0', 2.820)
    pier_x1 = spec.get('pier_x1', 3.950)
    rect((pier_x0, y_wall, 0.945, pier_x1, y_wall + 0.018, 1.480), fluted_splash, 'fluted-backsplash', 'detail')
    n_flutes = int((pier_x1 - pier_x0) / 0.050)
    for i in range(n_flutes):
        fx = pier_x0 + i * 0.050 + 0.010
        rect((fx, y_wall + 0.016, 0.950, fx + 0.018, y_wall + 0.024, 1.475), fluted_splash, f'splash-rib-{i}', 'detail')

    rect((hob_x0, y_wall + 0.14, 0.865, hob_x1, y_front - 0.16, 0.878), 'blackglass', 'hob-glass-plate', 'detail')
    for bx, by, rad in ((hob_xm - 0.16, hob_ym - 0.07, 0.056),
                        (hob_xm + 0.16, hob_ym - 0.07, 0.056),
                        (hob_xm, hob_ym + 0.09, 0.046)):
        k.cylinder((bx, by, z + 0.878), rad, 0.014, gola_black, floor, 'detail')
        k.cylinder((bx, by, z + 0.892), rad * 0.52, 0.008, 'brass', floor, 'detail')

    rect((hob_x0 - 0.02, y_wall + 0.02, 1.480, hob_x1 + 0.02, y_wall + 0.52, 1.535), 'blackglass', 'chimney-canopy', 'detail')
    rect((hob_x0 + 0.05, y_wall + 0.08, 1.474, hob_x1 - 0.05, y_wall + 0.24, 1.480), led_warm, 'chimney-task-led', 'cove')
    rect((hob_xm - 0.14, y_wall + 0.02, 1.535, hob_xm + 0.14, y_wall + 0.30, 2.980), gola_black, 'chimney-flue', 'detail')

    # 7. Very minimalist above-platform storage on the solid center pier beside the hood (2 slim floating teak shelves + warm LED)
    sh_x0, sh_x1 = hob_x1 + 0.04, pier_x1 - 0.02
    if sh_x1 - sh_x0 > 0.25:
        for s_idx, sz in enumerate((1.480, 1.840)):
            rect((sh_x0, y_wall, sz, sh_x1, y_wall + 0.250, sz + 0.032), teak_wood, f'minimal-floating-shelf-{s_idx}', 'furniture')
            rect((sh_x0 + 0.02, y_wall + 0.04, sz - 0.008, sh_x1 - 0.02, y_wall + 0.065, sz), led_warm, f'minimal-shelf-led-{s_idx}', 'cove')

    # 8. Shifted West Tall Appliance & Fridge Bank against Home ICU South Wall (y_ft=25.0 -> X=4.512 m, x_ft=35.05..38.95)
    # Completely clear of the east wall and NE corner so the wide east platform stays open, bright, and spacious!
    app_x0 = spec.get('app_x0', 3.860)
    app_x1 = spec.get('app_x1', 4.512)
    fridge_y0 = spec.get('fridge_y0', 3.368)
    fridge_y1 = spec.get('fridge_y1', 4.100)
    pantry_y0 = spec.get('pantry_y0', 4.108)
    pantry_y1 = spec.get('pantry_y1', 4.557)

    # Side-by-side black mirror-glass refrigerator in sage-teal & fluted-teak architectural surround
    rect((app_x0, fridge_y0, 0.0, app_x1, fridge_y1, 2.160), teal_gloss, 'fridge-housing')
    f_mid = 0.5 * (fridge_y0 + fridge_y1)
    rect((app_x0 - 0.022, fridge_y0 + 0.012, 0.080, app_x0, f_mid - 0.004, 1.920), 'blackglass', 'fridge-door-L')
    rect((app_x0 - 0.022, f_mid + 0.004, 0.080, app_x0, fridge_y1 - 0.012, 1.920), 'blackglass', 'fridge-door-R')
    rect((app_x0 - 0.020, fridge_y0 + 0.004, 1.926, app_x0, fridge_y1 - 0.004, 2.156), teal_gloss, 'fridge-over-door')
    rect((app_x0, fridge_y0 + 0.004, 2.160, app_x1, fridge_y1 - 0.004, 2.980), teal_loft, 'fridge-loft-door')

    # Tall appliance & pantry column (built-in oven + microwave + sage-teal storage shifted away from east wall)
    rect((app_x0, pantry_y0, 0.0, app_x1, pantry_y1, 2.160), teak_wood, 'tall-pantry-carcass')
    rect((app_x0 - 0.020, pantry_y0 + 0.004, 0.105, app_x0, pantry_y1 - 0.004, 0.720), teal_gloss, 'tall-pantry-lower')
    rect((app_x0 - 0.022, pantry_y0 + 0.018, 0.730, app_x0, pantry_y1 - 0.018, 1.320), 'blackglass', 'built-in-oven', 'detail')
    rect((app_x0 - 0.022, pantry_y0 + 0.018, 1.335, app_x0, pantry_y1 - 0.018, 1.720), 'blackglass', 'built-in-microwave', 'detail')
    rect((app_x0 - 0.020, pantry_y0 + 0.004, 1.730, app_x0, pantry_y1 - 0.004, 2.156), teal_gloss, 'tall-pantry-upper')
    rect((app_x0 - 0.020, pantry_y0 + 0.004, 2.166, app_x0, pantry_y1 - 0.004, 2.980), teal_loft, 'tall-pantry-loft')

    # 9. Sculptural Waterfall Quartz & Fluted-Teak Prep Island (x_ft: 35.40..39.20, y_ft: 30.00..31.65)
    px0 = spec.get('prep_x0', 2.545)
    px1 = spec.get('prep_x1', 3.048)
    py0 = spec.get('prep_y0', 3.292)
    py1 = spec.get('prep_y1', 4.450)
    rect((px0 + 0.02, py0 + 0.02, 0.0, px1 - 0.02, py1 - 0.02, 0.865), teak_wood, 'prep-counter-base')
    rect((px0 + 0.015, py0 + 0.015, 0.012, px1 - 0.015, py1 - 0.015, 0.032), led_warm, 'prep-toe-led', 'cove')
    rect((px0 + 0.015, py0 + 0.015, 0.845, px1 - 0.015, py1 - 0.015, 0.862), led_warm, 'prep-lip-led', 'cove')
    p_flutes = int((py1 - py0) / 0.045)
    for i in range(p_flutes):
        fy = py0 + i * 0.045 + 0.012
        rect((px0 - 0.008, fy, 0.040, px0 + 0.012, fy + 0.022, 0.860), teak_wood, f'prep-flute-{i}', 'detail')
    rect((px0 - 0.015, py0 - 0.015, 0.865, px1 + 0.015, py1 + 0.015, 0.902), quartz_top, 'prep-quartz-top')
    rect((px0 - 0.015, py0 - 0.015, 0.0, px1 + 0.015, py0 + 0.025, 0.902), quartz_top, 'prep-waterfall-east', 'detail')
    rect((px0 - 0.015, py1 - 0.025, 0.0, px1 + 0.015, py1 + 0.015, 0.902), quartz_top, 'prep-waterfall-west', 'detail')
    # Minimalist linear brushed-gold & warm-LED pendant bar over the prep island
    pxm = 0.5 * (px0 + px1)
    rect((pxm - 0.04, py0 + 0.20, 2.96, pxm + 0.04, py1 - 0.20, 3.00), gola_black, 'prep-pendant-canopy', 'detail')
    for py_p in (py0 + 0.28, py1 - 0.28):
        k.beam((pxm, py_p, z + 2.08), (pxm, py_p, z + 2.96), 0.005, gola_black, floor, 'detail')
    rect((pxm - 0.022, py0 + 0.14, 2.04, pxm + 0.022, py1 - 0.14, 2.08), 'chandelier_gold_ring', 'prep-pendant-bar', 'fixture')
    rect((pxm - 0.016, py0 + 0.16, 2.025, pxm + 0.016, py1 - 0.16, 2.04), led_warm, 'prep-pendant-glow', 'cove')

    # Register footprints with scene kit
    k.furnishing('kitchen-counter', room, worktop_poly)
    k.furnishing('kitchen-sink', room, sink_box)
    k.furnishing('kitchen-hob', room, box(hob_x0, y_wall, hob_x1, y_front))
    k.furnishing('kitchen-fridge', room, box(app_x0, fridge_y0, app_x1, fridge_y1))
    k.furnishing('prep-counter', room, box(px0, py0, px1, py1))
    ctx['placed'].extend([worktop_poly, box(app_x0, fridge_y0, app_x1, pantry_y1), box(px0, py0, px1, py1)])
    for n in k.nodes[mark[0]:]:
        n['owner'] = owner

