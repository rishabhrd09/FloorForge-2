"""Strict, local DXF-to-Custom-Plan conversion; never guesses from line art."""
from __future__ import annotations

import io
import math
from pathlib import Path

import ezdxf
from shapely.geometry import LineString, Polygon, box

from .model import DEFAULTS, DesignError
from .spaces import SPACE_REGISTRY

MAX_BYTES = 750_000
UNITS = {4: 1., 6: 1000., 1: 25.4, 2: 304.8}
ROOM_KINDS = set(SPACE_REGISTRY) - {'stair', 'stair-landing', 'lift-shaft', 'void', 'drying-room'}
OPENINGS = {'FF_ENTRY': 'entry', 'FF_DOOR': 'door', 'FF_WINDOW': 'window'}


def reject(message, entity=None):
    suffix = f' (entity {entity.dxf.handle}, layer {entity.dxf.layer})' if entity else ''
    raise DesignError('DXF_IMPORT', message + suffix)


def import_dxf(text, filename='floor-plan.dxf'):
    """Return an editable project and the normal geometry validation result."""
    if not isinstance(filename, str) or not filename.lower().endswith('.dxf'):
        reject('Upload an ASCII .dxf file. PDF, DWG and images are not traced automatically.')
    if not isinstance(text, str) or not text or len(text.encode('utf-8')) > MAX_BYTES:
        reject('Use a nonempty DXF file up to 750 KB.')
    if '\x00' in text or text.startswith('AutoCAD Binary DXF'):
        reject('Binary DXF is unsupported. Export ASCII DXF R2000 or later.')
    try:
        doc = ezdxf.read(io.StringIO(text))
    except (ezdxf.DXFError, ValueError, TypeError, IndexError) as exc:
        raise DesignError('DXF_IMPORT', 'Cannot read this DXF. Export ASCII DXF R2000 or later.') from exc
    if doc.dxfversion < 'AC1015':
        reject('Export ASCII DXF R2000 or later with closed LWPOLYLINE room outlines.')
    scale = UNITS.get(doc.header.get('$INSUNITS'))
    if scale is None:
        reject('Set DXF drawing units ($INSUNITS) to millimetres, metres, inches or feet. Unitless drawings are ambiguous.')
    entities = list(doc.modelspace())
    if len(entities) > 5000:
        reject('Use at most 5,000 model-space entities in the import drawing.')
    if any(e.dxf.layer.upper().startswith('FF_') for layout in doc.layouts if layout.name != 'Model' for e in layout):
        reject('Put all FF_ geometry in model space, not paper-space layouts.')
    recognized, ignored = [], 0
    for e in entities:
        layer = e.dxf.layer.upper()
        if not layer.startswith('FF_'):
            ignored += 1
            continue
        if layer not in {'FF_PLOT', *OPENINGS} and not layer.startswith('FF_ROOM_'):
            reject('Unknown import layer. Use FF_PLOT, FF_ROOM_<kind>, FF_ENTRY, FF_DOOR or FF_WINDOW.', e)
        if e.dxftype() in ('INSERT', 'XREF'):
            reject('Explode blocks into supported model-space entities first.', e)
        recognized.append(e)

    def point(v, e):
        values = [float(n) * scale for n in v]
        if any(not math.isfinite(n) or abs(n) > 1_000_000 for n in values) or (len(values) > 2 and abs(values[2]) > .001):
            reject('Coordinates must be finite, within 1 km of the origin and at Z=0.', e)
        return [round(n, 6) for n in values[:2]]

    def rectangle(e):
        if e.dxftype() != 'LWPOLYLINE' or not e.closed:
            reject('Plot and rooms require closed rectangular LWPOLYLINE outlines.', e)
        if abs(e.dxf.elevation) > .000001 or tuple(e.dxf.extrusion) != (0., 0., 1.) or e.dxf.get('thickness', 0):
            reject('Use flat XY outlines at Z=0 with the default extrusion.', e)
        vertices = list(e.get_points())
        if any(any(abs(v[i]) > .000001 for i in (2, 3, 4)) for v in vertices):
            reject('Polyline widths and curved bulges are unsupported.', e)
        pts = [point(v[:2], e) for v in vertices]
        if len(pts) > 1 and pts[0] == pts[-1]:
            pts.pop()
        if len(pts) != 4 or any(a[0] != b[0] and a[1] != b[1] for a, b in zip(pts, pts[1:] + pts[:1])):
            reject('Use four-corner axis-aligned rectangles; diagonal or curved boundaries are unsupported.', e)
        poly = Polygon(pts)
        if not poly.is_valid or poly.area < 1 or not poly.equals(box(*poly.bounds)):
            reject('Outline must be a simple rectangle with no crossing edges.', e)
        return poly

    plots = [e for e in recognized if e.dxf.layer.upper() == 'FF_PLOT']
    if len(plots) != 1:
        reject('Provide exactly one rectangular plot outline on FF_PLOT.')
    x0, y0, x1, y1 = rectangle(plots[0]).bounds
    width, depth = x1 - x0, y1 - y0
    if not (5000 <= width <= 50000 and 6500 <= depth <= 60000) or any(abs(n-round(n)) > .001 for n in (width, depth)):
        reject('Plot must be 5–50 m wide and 6.5–60 m deep, with whole-millimetre dimensions.')
    rooms = []
    for e in recognized:
        layer = e.dxf.layer.upper()
        if not layer.startswith('FF_ROOM_'):
            continue
        kind = layer[8:].lower().replace('_', '-')
        if kind not in ROOM_KINDS:
            reject('Unsupported room type. Use the documented single-floor room layers; stairs and voids need the exact editor.', e)
        a, b, c, d = rectangle(e).bounds
        rooms.append(dict(id='dxf-room-'+e.dxf.handle, kind=kind,
                          name=SPACE_REGISTRY[kind]['label']+' '+str(len(rooms)+1),
                          polygon=[[a-x0,b-y0],[c-x0,b-y0],[c-x0,d-y0],[a-x0,d-y0]]))
    if not 1 <= len(rooms) <= 120:
        reject('Provide 1–120 room outlines on FF_ROOM_<kind> layers, for one ground floor only.')
    brief = {**DEFAULTS, 'title': Path(filename).stem[:100], 'width_mm': round(width), 'depth_mm': round(depth),
             'storeys': 1, 'bedrooms': sum(r['kind']=='bedroom' for r in rooms), 'roof_access': False,
             'front_mm': 0, 'rear_mm': 0, 'left_mm': 0, 'right_mm': 0,
             'pooja': False, 'attached_baths': 0, 'vastu': 'off', 'exterior_theme': 'current'}
    floor = dict(id='dxf-ground', rooms=rooms, walls=[], openings=[])
    project = dict(schema='floorforge.project/0.4', brief=brief,
                   customPlan=dict(schema='floorforge.custom-plan/1', units='mm', wallThickness=150, floors=[floor], stairs=[]))
    from .intent import fuse
    from .layout import generate_layout
    from .review import validate
    # Compile real wall axes before hosting the imported opening spans.
    building = generate_layout(fuse(project))
    for e in recognized:
        kind = OPENINGS.get(e.dxf.layer.upper())
        if kind is None:
            continue
        if e.dxftype() != 'LINE':
            reject('Openings must be LINE spans along the wall centreline, not arcs or blocks.', e)
        a, b = point(e.dxf.start, e), point(e.dxf.end, e)
        a, b = sorted(([a[0]-x0,a[1]-y0],[b[0]-x0,b[1]-y0]))
        if (a[0] != b[0] and a[1] != b[1]) or math.dist(a,b) < 100:
            reject('Opening spans must be horizontal or vertical and at least 100 mm long.', e)
        span = LineString([a,b])
        hosts = [w for w in building['walls'] if LineString([w['a'],w['b']]).buffer(.01).covers(span)]
        if len(hosts) != 1:
            reject('Opening must lie on exactly one wall centreline: 75 mm outside a room’s clear outline. Keep it away from corners and junctions.', e)
        host = hosts[0]
        room = next(r for r in rooms if r['id'] in host['rooms'] and SPACE_REGISTRY[r['kind']]['enclosed'])
        from .custom_plan import side_at
        poly = Polygon(room['polygon']); side = side_at(poly, span.interpolate(.5, normalized=True))
        horiz = a[1] == b[1]
        floor['openings'].append(dict(id='dxf-opening-'+e.dxf.handle, roomId=room['id'], side=side, kind=kind,
                                     offset=a[0]-poly.bounds[0] if horiz else a[1]-poly.bounds[1],
                                     width=span.length, sill=900 if kind=='window' else 0,
                                     height=1200 if kind=='window' else 2100))
    notes = ['Imported one ground floor without resizing rooms. Drawing minimum Y is the front.',
             'Assumed 150 mm walls, 3150 mm floor height, 450 mm plinth; doors 2100 mm high; windows 900 mm sill / 1200 mm high.',
             'Plot setbacks are zero in the brief; empty space drawn around rooms is retained. Review local setback requirements before construction.']
    project['notes'] = ' '.join(notes)
    if ignored:
        notes.append(f'{ignored} entities on non-FF layers were ignored (annotations, furniture or other drawing content).')
    try:
        building = generate_layout(fuse(project)); review = validate(building)
        return dict(project=project, valid=True, review=review, notes=notes, roomCount=len(rooms), openingCount=len(floor['openings']))
    except DesignError as exc:
        return dict(project=project, valid=False, issue=exc.record(), notes=notes,
                    roomCount=len(rooms), openingCount=len(floor['openings']))
