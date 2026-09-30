"""Authored L-shaped kitchen: front worktop, puja-divider return, opposite fridge."""
from shapely.geometry import box
from shapely.ops import unary_union


def l_shaped_kitchen(k, ctx, floor_height, finishes):
    room, floor = ctx['room'], ctx['floor']
    z = floor * floor_height
    x0, y0, x1, y1 = ctx['clear'].bounds
    left, right, back = x0 + 1.01, x1 - .02, y0 + .02
    front, turn, end = y0 + .66, right - .64, y0 + 1.63
    owner = room['id'] + '/modular-kitchen'
    mark = k.edit_mark()
    sx=turn+.32; sy=(front+end)/2
    sink=box(sx-.205,sy-.27,sx+.205,sy+.27)

    def rect(bounds, material, name, role='furniture'):
        a,b,c,d,e,f = bounds
        return k.rect((a,b,z+c,d,e,z+f), material, floor, role, owner+'/'+name, owner)

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
