"""Rooflight and compact photovoltaic roof equipment for Tirumala 5.

Scene coordinates are metres, +x north and +y west. These are architectural
representations; glazing build-up, anchorage, drainage and roof loads need
project engineering. Slab/ceiling openings are authored by tirumala_5_upper.
"""
from __future__ import annotations

import math

import trimesh


APERTURE_MM = [1675, 6075, 5000, 7800]
ROOF_TOP_M = 10.546
SOLAR_HALL_ROOF_MM = [150, 9050, 5335.6, 14328]


def _prism(k, bounds, lower, upper, material, name, owner):
    """Closed prism with a planar inclined top/bottom, without Euler ambiguity."""
    x0, y0, x1, y1 = bounds
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    vertices = [[x, y, z(x, y)] for z in (lower, upper) for x, y in corners]
    faces = [[0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7],
             [0, 1, 5], [0, 5, 4], [1, 2, 6], [1, 6, 5],
             [2, 3, 7], [2, 7, 6], [3, 0, 4], [3, 4, 7]]
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=True)
    mesh.fix_normals()
    k.node(k.asset(mesh), material, floor=2, role='roof', name=name, owner=owner)


def _sheet(k, bounds, surface, thickness, material, name, owner):
    _prism(k, bounds, lambda x, y: surface(x, y)-thickness,
           surface, material, name, owner)


def add_rooflight_and_solar(k, mats, b):
    """Add roof-only objects and return an explicit architectural equipment record.

    The clear aperture is fixed to the coordinated all-floor void. No object
    added here closes that aperture with an opaque horizontal sheet. Narrow
    mullions are visible; curb, gutter and solar equipment remain outside it.
    ``b`` is accepted for the shared scene-helper convention, and is not mutated.
    """
    mats.update({
        't5-rooflight-curb': {'color': '#efede6', 'kind': 'render',
                              'texture': 'plaster', 'roughness': .8, 'normal': .06},
        't5-rooflight-frame': {'color': '#303631', 'kind': 'metal',
                               'metallic': .42, 'roughness': .3, 'params': [.3]},
        't5-rooflight-glass': {'color': '#cfdfdf', 'alpha': .23,
                               'glassOpacity': .16, 'glassReflectivity': .48,
                               'glassEnv': 1.2, 'roughness': .04,
                               'roughness_override': .035},
        't5-solar-frame': {'color': '#323a3d', 'kind': 'metal',
                            'metallic': .65, 'roughness': .26, 'params': [.3]},
        't5-solar-support': {'color': '#a5aaa9', 'kind': 'metal',
                              'metallic': .7, 'roughness': .4, 'params': [.35]},
        't5-solar-backing': {'color': '#111a24', 'roughness': .38, 'metallic': .2},
        't5-solar-cell': {'color': '#1a2b40', 'roughness': .17, 'metallic': .28,
                           'clearcoat': .8, 'clearcoat_roughness': .08},
        't5-solar-cell-alt': {'color': '#20334b', 'roughness': .19, 'metallic': .28,
                               'clearcoat': .8, 'clearcoat_roughness': .08},
        't5-roof-pad': {'color': '#d5d2c9', 'kind': 'concrete', 'roughness': .85},
    })
    x0, y0, x1, y1 = (v/1000 for v in APERTURE_MM)
    slope = math.tan(math.radians(3))
    # The glazed plane rises toward the west, draining to its east-side gutter.
    glass_top = lambda x, y: ROOF_TOP_M + .285 + (y-y0)*slope
    curb_top = lambda x, y: glass_top(x, y)-.052
    curb_base = lambda x, y: ROOF_TOP_M
    curb = .12
    bounds = [
        (x0-curb, y0-curb, x0, y1+curb),
        (x1, y0-curb, x1+curb, y1+curb),
        (x0, y0-curb, x1, y0),
        (x0, y1, x1, y1+curb),
    ]
    for i, bb in enumerate(bounds):
        _prism(k, bb, curb_base, curb_top, 't5-rooflight-curb',
               f't5-rooflight-curb-{i}', 't5-rooflight')

    # Three transparent panes sit on the curb, with narrow perimeter cappings.
    # Mullions are 36 mm wide, so the ground-to-sky view is mostly unobstructed.
    gx0, gy0, gx1, gy1 = x0-.045, y0-.045, x1+.045, y1+.045
    _sheet(k, (gx0, gy0, gx1, gy1), glass_top, .014,
           't5-rooflight-glass', 't5-rooflight-solar-control-glazing', 't5-rooflight')
    perimeter = [
        (gx0-.025, gy0-.025, gx0+.025, gy1+.025),
        (gx1-.025, gy0-.025, gx1+.025, gy1+.025),
        (gx0+.025, gy0-.025, gx1-.025, gy0+.025),
        (gx0+.025, gy1-.025, gx1-.025, gy1+.025),
    ]
    frame_top = lambda x, y: glass_top(x, y)+.012
    for i, bb in enumerate(perimeter):
        _sheet(k, bb, frame_top, .065, 't5-rooflight-frame',
               f't5-rooflight-perimeter-{i}', 't5-rooflight')
    for i in (1, 2):
        xx = x0+(x1-x0)*i/3
        _sheet(k, (xx-.018, gy0, xx+.018, gy1), frame_top, .055,
               't5-rooflight-frame', f't5-rooflight-mullion-{i}', 't5-rooflight')

    # An open, shallow metal gutter catches the low glazing edge. Its mouth is
    # outside the shaft; the outlet is only a conceptual roof-drain connection.
    gutter_y0, gutter_y1 = y0-.205, y0-.12
    gutter_z = ROOF_TOP_M+.19
    for name, bb in [
        ('base', (x0-.12, gutter_y0, gutter_z, x1+.12, gutter_y1, gutter_z+.012)),
        ('east-lip', (x0-.12, gutter_y0, gutter_z, x1+.12, gutter_y0+.012, gutter_z+.05)),
        ('west-lip', (x0-.12, gutter_y1-.012, gutter_z, x1+.12, gutter_y1, gutter_z+.045)),
        ('south-cap', (x0-.12, gutter_y0, gutter_z, x0-.108, gutter_y1, gutter_z+.05)),
        ('north-cap', (x1+.108, gutter_y0, gutter_z, x1+.12, gutter_y1, gutter_z+.05)),
    ]:
        k.rect(bb, 't5-rooflight-frame', 2, 'roof',
               f't5-rooflight-drain-{name}', 't5-rooflight')
    # Small discharge pipe remains on the roof, not inside the glazed void.
    k.cylinder((x1+.075, (gutter_y0+gutter_y1)/2, ROOF_TOP_M+.11),
               .025, .2, 't5-rooflight-frame', 2, 'roof')

    # Four modest modules over the opaque family hall roof, well clear of the
    # rooflight and roof perimeter. +x is north, so the tilted modules face south.
    panel_w, panel_l, panel_gap = 1.13, 1.76, .10
    array_x, array_y = 1.15, 10.0
    tilt = math.tan(math.radians(8))
    modules = []
    for row in range(2):
        for col in range(2):
            px, py = array_x+col*(panel_w+panel_gap), array_y+row*(panel_l+panel_gap)
            ident = f't5-solar-module-{row+1}-{col+1}'
            plane = lambda x, y, start=px: ROOF_TOP_M+.29+(x-start)*tilt
            bb = (px, py, px+panel_w, py+panel_l)
            modules.append([round(v*1000, 3) for v in bb])

            # Two rails per module, each on two vertical standoffs and footpads.
            # These illustrate a supported assembly, without sizing real fixings.
            for rail_index, yy in enumerate((py+.26, py+panel_l-.26)):
                for side, xx in enumerate((px+.13, px+panel_w-.13)):
                    k.rect((xx-.08, yy-.08, ROOF_TOP_M,
                            xx+.08, yy+.08, ROOF_TOP_M+.035),
                           't5-roof-pad', 2, 'roof', f'{ident}-pad-{rail_index}-{side}', ident)
                    k.rect((xx-.022, yy-.022, ROOF_TOP_M+.035,
                            xx+.022, yy+.022, plane(xx, yy)-.046),
                           't5-solar-support', 2, 'roof', f'{ident}-leg-{rail_index}-{side}', ident)
                _sheet(k, (px+.06, yy-.026, px+panel_w-.06, yy+.026),
                       lambda x, y, pp=plane: pp(x, y)-.043, .032,
                       't5-solar-support', f'{ident}-rail-{rail_index}', ident)

            _sheet(k, bb, lambda x, y, pp=plane: pp(x, y)-.004, .036,
                   't5-solar-backing', f'{ident}-backing', ident)
            border = .025
            panel_frame = [
                (px, py, px+border, py+panel_l),
                (px+panel_w-border, py, px+panel_w, py+panel_l),
                (px+border, py, px+panel_w-border, py+border),
                (px+border, py+panel_l-border, px+panel_w-border, py+panel_l),
            ]
            for i, edge in enumerate(panel_frame):
                _sheet(k, edge, lambda x, y, pp=plane: pp(x, y)+.006, .045,
                       't5-solar-frame', f'{ident}-frame-{i}', ident)

            # Physical cell grid with narrow gaps, instead of a tiled black slab.
            ix, iy = px+border+.014, py+border+.014
            iw, il = panel_w-2*(border+.014), panel_l-2*(border+.014)
            gap = .006
            cell_w, cell_l = (iw-5*gap)/6, (il-9*gap)/10
            for cy in range(10):
                for cx in range(6):
                    xx, yy = ix+cx*(cell_w+gap), iy+cy*(cell_l+gap)
                    mat = 't5-solar-cell-alt' if (cx+cy+row+col)%7 == 0 else 't5-solar-cell'
                    _sheet(k, (xx, yy, xx+cell_w, yy+cell_l), plane, .003,
                           mat, f'{ident}-cell-{cy}-{cx}', ident)

    return {
        'status': 'Architectural concept; glazing, drainage, anchorage and roof loads require engineering.',
        'clearApertureMm': APERTURE_MM[:],
        'clearSizeMm': [APERTURE_MM[2]-APERTURE_MM[0], APERTURE_MM[3]-APERTURE_MM[1]],
        'roofSlabTopMm': ROOF_TOP_M*1000,
        'rooflightSlopeDegrees': 3,
        'rooflightDrainDirection': 'East, into an external curb-side gutter',
        'rooflightCurbOutsideClearAperture': True,
        'rooflightOuterBoundsMm': [(x0-.12)*1000, gutter_y0*1000, (x1+.12)*1000, (y1+.12)*1000],
        'solarModules': 4,
        'solarModuleBoundsMm': modules,
        'solarArrayBoundsMm': [array_x*1000, array_y*1000,
                               (array_x+2*panel_w+panel_gap)*1000,
                               (array_y+2*panel_l+panel_gap)*1000],
        'solarTiltDegrees': 8,
        'solarFaces': 'South',
        'solarHallRoofBoundsMm': SOLAR_HALL_ROOF_MM[:],
        'solarMaintenanceClearancesMm': {'south': 1000, 'north': 1825.6, 'east': 950, 'west': 708},
    }
