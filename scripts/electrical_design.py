"""Illustrative electrical design for the copied My Desired Home.

Produces a complete, checkable model: points (from the architectural scene where
it has them), flush enclosures on clear wall spans, grouped final circuits on
balanced phases, concealed conduit runs (RCC slab + vertical wall chases) and a
terminal-to-terminal conductor netlist from the DISCOM service to every point.
The rules applied are cited in scripts/electrical_sources.py. This is an
educational planning simulation, not an installation design.
"""
from __future__ import annotations

import math
from collections import defaultdict

try:
    from .electrical_geometry import House, SlabRouter, search_mounts, inside, FLOOR_HEIGHT
except ImportError:
    from electrical_geometry import House, SlabRouter, search_mounts, inside, FLOOR_HEIGHT

# ---------------------------------------------------------------------------
# Dimensions (metres). See facts F-LG-DIM, F-E9-DIM, F-WIRE-OD, F-CONDUIT-OD.
# ---------------------------------------------------------------------------
MODULE_W, MODULE_H = .0225, .045
PLATES = {2: (.086, .086), 3: (.121, .086), 4: (.146, .086), 6: (.224, .086), 8: (.245, .086), 12: (.224, .172)}
BOXES = {2: (.0765, .0765), 3: (.0997, .0765), 4: (.1368, .0765), 6: (.2142, .0765), 8: (.2328, .0773), 12: (.215, .1453)}
BOX_DEPTH = .060            # CPWD 4.3.3 minimum clear depth (Legrand lists 51 mm for 2-9M boxes)
PLATE_DEPTH = .0065
TPN = (.471, .422, .090)    # Easy9 TPN double door 8 way, W x H x D
SPN = (.293, .224, .093)    # Easy9 SPN double door 8 way
LWB_H = {"tpn": .150, "spn": .120}   # loose-wire box above each DB (estimate, CPWD Fig. 8 arrangement)
METER_BOX = (.30, .40, .20) # W x H x D; a DISCOM meter box specification (WBSEDCL) lists 400 x 300 x 200 mm
METER = (.191, .255, .082) # three-phase whole-current meter, e.g. Secure Sprint 350 brochure (W x H x D)
WIRE_OD = {1.5: .0030, 2.5: .0034, 4.0: .0042, 6.0: .0047, 10.0: .0061}
CHASE_DEPTH = .030          # conduit centre behind the finished wall face
JB_D, JB_DEPTH = .070, .065  # slab junction box (CPWD 4.4.3(d): >= 65 mm deep)
FILL_BENT = {20: {1.5: 4, 2.5: 3, 4.0: 2}, 25: {1.5: 8, 2.5: 6, 4.0: 5}}   # CPWD Table 4.1
LIGHT_POINTS_MAX = 12       # illustrative grouping cap (CPWD 3.10.1 allows up to 20)
FAN_BLADES = 2.69           # blade plane above floor: >= 300 mm below the 2.993 m soffit (IS 732:1989 C-8.1)
PHASES = ("R", "Y", "B")
COLOURS = {
    "R": {"name": "Red", "hex": "#b5302a"}, "Y": {"name": "Yellow", "hex": "#d7a81c"},
    "B": {"name": "Blue", "hex": "#2a55a6"}, "LIVE": {"name": "Red", "hex": "#b5302a"},
    "N": {"name": "Black", "hex": "#1e1f21"}, "PE": {"name": "Yellow/green", "hex": "#3e9440", "stripe": "#d8c529"},
}
ROOM_LABEL = {"g-caregiver": "Caregiver bedroom", "g-care": "Care room", "g-drawing": "Drawing room & foyer"}

FAN_TABLE_W = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
FAN_TABLE_L = [4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 16]
FAN_TABLE = {  # CPWD Table 3.1 (indicative): width -> per-length "size/number"
    3: "1200/1 1400/1 1500/1 1050/2 1200/2 1400/2 1400/2 1400/2 1200/3 1400/3 1400/3",
    4: "1200/1 1400/1 1200/2 1200/2 1200/2 1400/2 1400/2 1500/2 1200/3 1400/3 1500/3",
    5: "1400/1 1400/1 1400/2 1400/2 1400/2 1400/2 1400/2 1500/2 1400/3 1400/3 1500/3",
    6: "1200/2 1400/2 900/4 1050/4 1200/4 1400/4 1400/4 1500/4 1200/6 1400/6 1500/6",
}


def r4(v):
    return round(v, 4)


def p3(p):
    return [r4(p[0]), r4(p[1]), r4(p[2])]


def fan_table(width, length):
    w = min(FAN_TABLE.keys(), key=lambda k: abs(k - width))
    l_idx = min(range(len(FAN_TABLE_L)), key=lambda i: abs(FAN_TABLE_L[i] - length))
    size, number = FAN_TABLE[w].split()[l_idx].split("/")
    return int(size), int(number), w, FAN_TABLE_L[l_idx]


class Design:
    def __init__(self, building, scene):
        self.building, self.scene = building, scene
        self.house = House(building, scene)
        self.H = FLOOR_HEIGHT
        self.rooms = []
        self.enclosures = []
        self.devices = []
        self.terminals = []
        self.switches = []
        self.regulators = []
        self.points = []
        self.boxes = []
        self.circuits = []
        self.conduits = []
        self.conductors = []
        self.reserved = defaultdict(list)   # wallId -> mounts
        self.notes = []
        self._ids = defaultdict(int)
        self.routers = {}

    # ------------------------------------------------------------------ ids
    def nid(self, prefix):
        self._ids[prefix] += 1
        return f"{prefix}{self._ids[prefix]:02d}"

    # ------------------------------------------------------------------ rooms
    def collect_rooms(self):
        for sp in self.building["spaces"]:
            if not (sp.get("enclosed") and sp.get("walkable")):
                continue
            room = self.house.rooms[sp["id"]]
            poly = room["polygon"]
            xs, ys = [p[0] for p in poly], [p[1] for p in poly]
            full = ROOM_LABEL.get(sp["id"], sp["name"])
            self.rooms.append({
                "id": sp["id"], "name": full.split(" · ")[0], "fullName": full, "kind": sp["kind"],
                "floor": sp["floor"], "polygon": poly, "wet": bool(sp.get("wet")),
                "ventilation": bool(sp.get("mechanicalVentilation")),
                "bbox": [min(xs), min(ys), max(xs), max(ys)], "area": sp.get("area_m2"),
                "label": self.label_point(poly, sp["floor"]),
            })
        self.room_by_id = {r["id"]: r for r in self.rooms}

    def label_point(self, poly, floor):
        xs, ys = [p[0] for p in poly], [p[1] for p in poly]
        best = None
        for i in range(1, 12):
            for j in range(1, 12):
                x = min(xs) + (max(xs) - min(xs)) * i / 12
                y = min(ys) + (max(ys) - min(ys)) * j / 12
                if not inside(x, y, poly):
                    continue
                d = min(_seg_dist((x, y), poly[k], poly[(k + 1) % len(poly)]) for k in range(len(poly)))
                if best is None or d > best[0]:
                    best = (d, [r4(x), r4(y)])
        return best[1]

    # ------------------------------------------------------------------ enclosures
    def place(self, room_id, kind, label, modules=None, *, size=None, z_bottom=None, z_centre=None,
              recess=BOX_DEPTH, doors=None, walls=None, target=None, access=.45, access_band=None,
              prefer_latch=True, exterior=False, extra_score=None, required=True, corner_clear=.15,
              finishes=("wall-tile",)):
        """Find a clear flush mount for an enclosure and reserve it."""
        if size is None:
            pw, ph = PLATES[modules]
            bw, bh = BOXES[modules]
        else:
            pw, ph = size
            bw, bh = size
        floor = self.house.rooms[room_id]["floor"]
        if z_centre is None:
            z_centre = z_bottom + bh / 2
        reserved = [m for ms in self.reserved.values() for m in ms]
        cands = search_mounts(self.house, room_id, width=pw, height=ph, z=z_centre, recess=recess,
                              access=access, access_band=access_band, exterior=exterior, target=target,
                              reserved=reserved, prefer_latch=prefer_latch, doors=doors, walls=walls,
                              extra_score=extra_score, corner_clear=corner_clear, finishes=finishes)
        if not cands:
            if required:
                raise ValueError(f"No clear wall span for {kind} in {room_id}")
            return None
        m = cands[0]
        mount = m.as_dict()
        eid = self.nid({"switchboard": "SB", "socket-plate": "SP", "geyser-mcb": "GM", "geyser-outlet": "GO",
                        "exhaust-point": "EX", "wall-point": "WP", "main-db": "DB", "sub-db": "DB",
                        "loose-wire-box": "LW", "meter": "MT"}.get(kind, "EN"))
        enc = {"id": eid, "kind": kind, "label": label, "roomId": room_id, "floor": floor,
               "mount": mount, "size": {"w": r4(pw), "h": r4(ph), "boxW": r4(bw), "boxH": r4(bh),
                                         "depth": recess, "plateDepth": PLATE_DEPTH if modules else 0},
               "modules": [], "circuitIds": [], "conduitIds": []}
        if modules:
            enc["plateModules"] = modules
        self.enclosures.append(enc)
        self.reserved[mount["wallId"]].append({"wallId": mount["wallId"], "side": mount["side"], "along": mount["along"],
                                               "width": pw + .02, "z": mount["z"], "height": ph, "recess": recess})
        return enc

    def enc(self, eid):
        return next(e for e in self.enclosures if e["id"] == eid)

    def local_to_world(self, enc, lx, ly, lz):
        m = enc["mount"]
        nx, ny = m["normal"]
        rx, ry = -ny, nx                     # local +x (viewer's right when facing the wall)
        fx, fy, fz = m["face"]
        return (fx + rx * lx + nx * lz, fy + ry * lx + ny * lz, fz + ly)

    # ------------------------------------------------------------------ devices & terminals
    def device(self, enc, kind, label, **kw):
        did = self.nid("D")
        d = {"id": did, "enclosureId": enc["id"] if enc else None, "kind": kind, "label": label, **kw}
        self.devices.append(d)
        return d

    def terminal_box(self, box, label, role, local):
        tid = self.nid("T")
        self.terminals.append({"id": tid, "boxId": box["id"], "enclosureId": None, "deviceId": None,
                               "label": label, "role": role, "local": [r4(v) for v in local]})
        return tid

    def terminal(self, enc, label, role, local, device=None):
        tid = self.nid("T")
        self.terminals.append({"id": tid, "enclosureId": enc["id"], "deviceId": device["id"] if device else None,
                               "label": label, "role": role, "local": [r4(v) for v in local]})
        return tid

    # ------------------------------------------------------------------ points
    def scene_lights(self, room):
        z0 = room["floor"] * self.H
        out = []
        for i, l in enumerate(self.scene["lights"]):
            x, y, z = l["position"]
            if not (z0 - .05 < z < z0 + 3.05):
                continue
            if self.house.room_at(x, y, room["floor"]) != room["id"]:
                continue
            if l["kind"] in ("downlight",) and z > z0 + 2.2:
                ceiling = self.house.overhead_bottom(x, y, room["floor"])
                lens = self.lens_of(x, y, z0)
                out.append({"kind": "downlight", "scene": i, "position": [r4(x), r4(y), r4(ceiling)], "lens": lens})
            elif l["kind"] == "mirror":
                out.append({"kind": "mirror-light", "scene": i, "position": [r4(x), r4(y), r4(z)]})
            elif l["kind"] == "undercabinet":
                out.append({"kind": "undercabinet", "scene": i, "position": [r4(x), r4(y), r4(z)]})
        return out

    def lens_of(self, x, y, z0):
        """Visible lamp disc of the architectural downlight above a light (centre, bottom, radius)."""
        best = None
        for n in self.scene["nodes"]:
            if n["role"] != "downlight" or n["material"] != "lamp":
                continue
            px, py, pz = n["position"]
            if abs(px - x) < .02 and abs(py - y) < .02 and z0 + 2.0 < pz < z0 + 3.1:
                r = abs(n["scale"][0]) / 2
                bottom = pz - abs(n["scale"][2]) / 2
                if best is None or bottom < best[1]:
                    best = ([r4(px), r4(py)], r4(bottom), r4(r))
        return {"xy": best[0], "bottom": best[1], "r": best[2]} if best else None

    def add_point(self, room, kind, position, label, *, provenance, scene=None, **kw):
        pid = self.nid("P")
        pt = {"id": pid, "kind": kind, "label": label, "roomId": room["id"], "floor": room["floor"],
              "position": p3(position), "provenance": provenance, "controls": [], **kw}
        if scene is not None:
            pt["sceneLight"] = scene
        self.points.append(pt)
        return pt

    # ------------------------------------------------------------------ layout of each room
    def design_rooms(self):
        for room in self.rooms:
            room["pointIds"], room["enclosureIds"] = [], []
            lights = self.scene_lights(room)
            room["_lights"] = lights
        for room in self.rooms:
            self.design_room(room)

    def entry_doors(self, room):
        """Doors a person uses to enter the room (from circulation), preferring internal ones."""
        doors = []
        for w in self.house.walls.values():
            for o in w.openings:
                if o.kind in ("door", "entry", "cased") and room["id"] in (o.connects or []):
                    other = next((c for c in o.connects if c != room["id"]), None)
                    other_kind = self.house.spaces.get(other, {}).get("kind") if other else None
                    rank = 0
                    if o.kind == "entry":
                        rank = -1          # the main entrance: switches beside the front door
                    elif other == "outside" or other is None:
                        rank = 2
                    elif other_kind in ("bathroom",):
                        rank = 3
                    elif other_kind in ("hall", "living", "stair", "drawing-room", "care-room"):
                        rank = 0
                    else:
                        rank = 1
                    doors.append((rank, o.ident))
        doors.sort()
        best = doors[0][0] if doors else None
        return [d for r, d in doors if r == best] or None

    def design_room(self, room):
        f = room["floor"]
        kind = room["kind"]
        level = f * self.H
        doors = self.entry_doors(room)
        lights = list(room["_lights"])
        # Proposed fittings where the scene has none (stairs).
        if not [l for l in lights if l["kind"] == "downlight"] and kind == "stair":
            p = self.stair_light(room)
            lights.append({"kind": "downlight", "scene": None, "position": p, "proposed": True})
        # --- switch groups for ceiling lights
        downs = [l for l in lights if l["kind"] == "downlight"]
        groups = self.light_groups(room, downs)
        modules = []
        for gi, g in enumerate(groups):
            modules.append(("switch", g))
        cove = self.cove_point(room)
        if cove:
            modules.append(("switch", [cove]))
        for l in lights:
            if l["kind"] in ("mirror-light", "undercabinet"):
                modules.append(("switch", [l]))
        fans = self.fan_points(room, downs)
        exhaust = self.exhaust_opening(room) if room["ventilation"] else None
        if exhaust:
            modules.append(("switch", [exhaust]))
        for fan in fans:
            modules.append(("fan", fan))
        n_mod = sum(3 if m[0] == "fan" else 1 for m in modules)
        if n_mod == 0:
            return
        size = next(s for s in (2, 3, 4, 6, 8, 12) if s >= n_mod)
        label = f"{room['name']} switchboard"
        board = self.place(room["id"], "switchboard", label, size, z_bottom=1.10, doors=doors,
                           access=.45)
        board["purpose"] = "lighting"
        room["enclosureIds"].append(board["id"])
        room["boardId"] = board["id"]
        self.populate_board(board, room, modules, size)
        # --- power outlets
        if room["kind"] in ("bedroom", "living", "drawing-room", "hall", "care-room", "study"):
            self.socket_plate(room, "general", [("socket6", "6 A socket")], near=board)
        if room["kind"] == "bedroom":
            self.bedside_plates(room)
        if room["kind"] == "kitchen":
            self.kitchen_outlets(room)
        if room["kind"] == "pooja":
            self.socket_plate(room, "lamp", [("socket6", "6 A socket for lamp")], near=board, z_bottom=1.10)
        if room["kind"] == "study":
            self.desk_plate(room)
        if room["kind"] == "care-room":
            self.care_plate(room)
        if room["kind"] == "bathroom":
            self.bathroom_outlets(room, board)

    def stair_light(self, room):
        f = room["floor"]
        best = None
        poly = room["polygon"]
        router = self.router(f)
        for i in range(1, 16):
            for j in range(1, 16):
                bb = room["bbox"]
                x = bb[0] + (bb[2] - bb[0]) * i / 16
                y = bb[1] + (bb[3] - bb[1]) * j / 16
                if not inside(x, y, poly) or not router._solid(x, y):
                    continue
                d = min(_seg_dist((x, y), poly[k], poly[(k + 1) % len(poly)]) for k in range(len(poly)))
                if best is None or d > best[0]:
                    best = (d, (x, y))
        x, y = best[1]
        return [r4(x), r4(y), r4(self.house.overhead_bottom(x, y, f))]

    def light_groups(self, room, downs):
        if not downs:
            return []
        n = len(downs)
        k = 1 if n <= 4 else 2 if n <= 8 else 3
        bb = room["bbox"]
        axis = 0 if bb[2] - bb[0] >= bb[3] - bb[1] else 1
        ordered = sorted(downs, key=lambda l: (l["position"][axis], l["position"][1 - axis]))
        # keep fittings at a distinct ceiling height (feature ceilings) together
        heights = sorted(set(round(l["position"][2], 2) for l in downs))
        if len(heights) > 1 and k > 1:
            low = [l for l in ordered if round(l["position"][2], 2) == heights[0]]
            rest = [l for l in ordered if l not in low]
            return [rest[i * len(rest) // (k - 1):(i + 1) * len(rest) // (k - 1)] for i in range(k - 1)] + [low]
        return [ordered[i * n // k:(i + 1) * n // k] for i in range(k)]

    def cove_point(self, room):
        f = room["floor"]
        for n in self.scene["nodes"]:
            if n["role"] != "cove" or n["floor"] != f:
                continue
            asset = self.scene["assets"][n["asset"]]
            vs = asset["vertices"]
            cx = sum(v[0] for v in vs) / len(vs)
            cy = sum(v[1] for v in vs) / len(vs)
            if self.house.room_at(cx, cy, f) != room["id"]:
                continue
            zt = max(v[2] for v in vs)
            # driver/connection on the band nearest the room's entry wall (assumed)
            xs, ys = [v[0] for v in vs], [v[1] for v in vs]
            return {"kind": "cove", "scene": None, "node": n["id"],
                    "position": [r4(min(xs) + .08), r4((min(ys) + max(ys)) / 2), r4(self.house.soffit(f))]}
        return None

    def fan_points(self, room, downs):
        if room["kind"] not in ("bedroom", "living", "drawing-room", "care-room", "study") and \
                not (room["kind"] == "hall" and room["floor"] == 0) and room["id"] != "u-lounge":
            return []
        bb = room["bbox"]
        w, l = sorted((bb[2] - bb[0], bb[3] - bb[1]))
        size, number, tw, tl = fan_table(w, l)
        number = min(number, 2)
        basis = f"CPWD Table 3.1 for about {tw} m × {tl} m: {size} mm × {number}"
        f = room["floor"]
        router = self.router(f)
        poly = room["polygon"]

        def candidates(sweep):
            out = []
            for i in range(1, 30):
                for j in range(1, 30):
                    x = bb[0] + (bb[2] - bb[0]) * i / 30
                    y = bb[1] + (bb[3] - bb[1]) * j / 30
                    if not inside(x, y, poly) or not router._solid(x, y):
                        continue
                    if self.house.overhead_bottom(x, y, f) < self.house.soffit(f) - .01:
                        continue          # under a cove band or ceiling feature
                    wall_d = min(_seg_dist((x, y), poly[k], poly[(k + 1) % len(poly)]) for k in range(len(poly)))
                    if wall_d < sweep + .3:
                        continue
                    light_d = min((math.dist((x, y), d["position"][:2]) for d in downs), default=3)
                    out.append((x, y, wall_d, light_d))
            return out

        cands = candidates(size / 1000 / 2)
        if not cands:
            # The bounding box overstates narrow L-shaped spaces: step down through the
            # smaller standard sweeps until one fan clears the walls by 0.3 m.
            for smaller in (s for s in (1200, 1050, 900) if s < size):
                cands = candidates(smaller / 1000 / 2)
                if cands:
                    basis = (f"{basis}; reduced to one {smaller} mm fan because the space is narrow "
                             f"(blade tips at least 0.3 m from the walls)")
                    size, number = smaller, 1
                    break
        if not cands:
            self.notes.append(f"{room['name']}: no ceiling fan proposed; no point under the solid slab keeps "
                              f"even a 900 mm sweep 0.3 m clear of the walls and cove bands.")
            return []
        sweep = size / 1000 / 2
        out = []
        if number == 1:
            cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
            best = max(cands, key=lambda c: min(c[3], .9) * 2 + min(c[2], 1.5) - .35 * math.dist(c[:2], (cx, cy)))
            out.append(best[:2])
        else:
            axis = 0 if bb[2] - bb[0] >= bb[3] - bb[1] else 1
            for q in (.25, .75):
                tx = bb[0] + (bb[2] - bb[0]) * (q if axis == 0 else .5)
                ty = bb[1] + (bb[3] - bb[1]) * (q if axis == 1 else .5)
                pool = [c for c in cands if all(math.dist(c[:2], o) > 2 * sweep + .4 for o in out)]
                if not pool:
                    break
                best = max(pool, key=lambda c: min(c[3], .9) * 2 + min(c[2], 1.5) - .6 * math.dist(c[:2], (tx, ty)))
                out.append(best[:2])
            if len(out) < number:
                basis = f"{basis}; only one placed because a second would not clear the first"
        fans = []
        for x, y in out:
            z = self.house.soffit(f)
            fans.append({"kind": "fan", "position": [r4(x), r4(y), r4(z)], "sweep": size, "table": basis})
        return fans

    def exhaust_opening(self, room):
        """Exhaust fan in an external wall of a mechanically ventilated bathroom, high level."""
        f = room["floor"]
        best = None
        for wall, side in self.house.faces_of_room(room["id"]):
            other = wall.sides[-side]
            if other != "outside" and self.house.spaces.get(other, {}).get("enclosed", True):
                continue
            span = self.house.face_span(wall, side, room["id"])
            if not span:
                continue
            s = (span[0] + span[1]) / 2
            for ds in (0, .3, -.3, .6, -.6):
                a = s + ds
                if not (span[0] + .3 <= a <= span[1] - .3):
                    continue
                zc = f * self.H + 2.30
                if self.house.opening_conflict(wall, a, .32, zc - .16, zc + .16, side_clear=.15, vertical_clear=.1):
                    continue
                if self.house.blockers(wall, side, a, .32, zc - .16, zc + .16, .05):
                    continue
                best = (wall, side, a, zc)
                break
            if best:
                break
        if not best:
            self.notes.append(f"{room['name']}: no exhaust fan proposed; no clear high-level position on an external wall.")
            return None
        wall, side, a, zc = best
        fx, fy = wall.point(a, side)
        return {"kind": "exhaust", "position": [r4(fx), r4(fy), r4(zc)], "wallId": wall.ident, "side": side,
                "along": r4(a), "size": .30}

    # ------------------------------------------------------------------ boards
    def populate_board(self, board, room, modules, size):
        """Lay out modules on the plate and create switches, regulators, terminals and points."""
        pw = PLATES[size][0]
        cols = size if size <= 8 else 6
        slots = []
        x0 = -cols * MODULE_W / 2
        row_y = [0.] if size <= 8 else [.043, -.043]
        cursor = 0
        bw, bh = BOXES[size]
        # connector blocks (CPWD 3.5.6): phase, neutral, earth — on the box back, lower area (visible from eye level)
        cb_y = -bh / 2 + .015
        board["connectors"] = {
            "P": self.terminal(board, "Phase connector", "P", (-bw / 2 + .022, cb_y, -BOX_DEPTH + .012)),
            "N": self.terminal(board, "Neutral connector", "N", (-bw / 2 + .042, cb_y, -BOX_DEPTH + .012)),
            "E": self.terminal(board, "Earth connector", "E", (-bw / 2 + .062, cb_y, -BOX_DEPTH + .012)),
            "stud": self.terminal(board, "Box earth stud", "E", (bw / 2 - .014, -bh / 2 + .012, -BOX_DEPTH + .004)),
        }
        n_groups = sum(1 for k, pl in modules if k == "switch" and pl and pl[0]["kind"] == "downlight")
        n_fans = sum(1 for k, _ in modules if k == "fan")
        gi = fi = 0
        # fan pairs (switch + 2-module regulator) never straddle the two rows of a 12-module plate
        if len(row_y) == 2:
            first = sum(3 if k == "fan" else 1 for k, _ in modules if k != "fan")
            modules = sorted(modules, key=lambda m: m[0] == "fan")
        for kind, payload in modules:
            span = 3 if kind == "fan" else 1
            if len(row_y) == 2 and cursor < cols < cursor + span:
                for c in range(cursor, cols):
                    board["modules"].append({"kind": "blank", "row": 0, "col": c, "span": 1,
                                             "x": r4(x0 + (c + .5) * MODULE_W), "y": r4(row_y[0])})
                cursor = cols
            row = 0 if (len(row_y) == 1 or cursor < cols) else 1
            col = cursor if row == 0 else cursor - cols
            cursor += span
            if kind == "switch":
                pts = []
                for l in payload:
                    label = {"downlight": "Ceiling light", "cove": "Cove LED strip", "mirror-light": "Mirror light",
                             "undercabinet": "Under-cabinet light", "exhaust": "Exhaust fan"}[l["kind"]]
                    prov = ("architectural scene" if l.get("scene") is not None else
                            "proposed (stair has no fitting in the scene)" if l.get("proposed") else
                            "architectural cove; driver position assumed" if l["kind"] == "cove" else "proposed")
                    extra = {k: l[k] for k in ("wallId", "side", "along", "size", "node", "lens") if k in l}
                    pts.append(self.add_point(room, l["kind"], l["position"], f"{room['name']} · {label}",
                                              provenance=prov, scene=l.get("scene"), **extra))
                k0 = payload[0]["kind"]
                if k0 == "downlight":
                    gi += 1
                    desc = "Ceiling lights" + (f" {gi} of {n_groups}" if n_groups > 1 else "") + f" ({len(pts)})"
                else:
                    desc = {"cove": "Cove light", "mirror-light": "Mirror light", "undercabinet": "Under-cabinet light",
                            "exhaust": "Exhaust fan"}[k0]
                self.switch_module(board, row_y[row], x0, col, desc, pts)
            else:
                fi += 1
                fan = self.add_point(room, "fan", payload["position"],
                                     f"{room['name']} · Ceiling fan" + (f" {fi}" if n_fans > 1 else ""),
                                     provenance="proposed (CPWD Table 3.1 indicative size)", sweep=payload["sweep"],
                                     basis=payload["table"])
                self.fan_modules(board, row_y[row], x0, col, fan, f"Fan {fi}" if n_fans > 1 else "Fan")
        # fill remaining slots with blanks
        total = cols * len(row_y)
        taken = {(m["row"], m["col"] + k) for m in board["modules"] for k in range(m["span"])}
        for c in range(0, total):
            if (0 if c < cols else 1, c if c < cols else c - cols) in taken:
                continue
            row = 0 if c < cols else 1
            col = c if row == 0 else c - cols
            board["modules"].append({"kind": "blank", "row": row, "col": col, "span": 1,
                                     "x": r4(x0 + (col + .5) * MODULE_W), "y": r4(row_y[row])})

    def switch_module(self, board, y, x0, col, label, points, *, kind="switch", control=None):
        x = x0 + (col + .5) * MODULE_W
        dev = self.device(board, "switch", f"{label} switch", poles=1, modules=1, rating=None,
                          standard="IS 3854 (modular, ON when knob is down)")
        t_in = self.terminal(board, "L (in)", "L", (x, y + .012, -.030), dev)
        t_out = self.terminal(board, "Load (out)", "SW", (x, y - .012, -.030), dev)
        sid = self.nid("S")
        # Lights start ON so the house looks as lit as the architectural sample; fans,
        # exhaust fans and outlets start OFF.
        lights_only = bool(points) and all(p["kind"] in ("downlight", "cove", "mirror-light", "undercabinet") for p in points)
        self.switches.append({"id": sid, "deviceId": dev["id"], "enclosureId": board["id"], "label": label,
                              "points": [p["id"] for p in points], "defaultOn": lights_only})
        for p in points:
            p["controls"].append(sid)
            p["switchId"] = sid
        board["modules"].append({"kind": "switch", "row": 0 if y >= 0 else 1, "col": col, "span": 1, "x": r4(x), "y": r4(y),
                                 "deviceId": dev["id"], "switchId": sid, "label": label})
        dev["terminals"] = {"in": t_in, "out": t_out}
        dev["switchId"] = sid
        return dev

    def fan_modules(self, board, y, x0, col, fan, label="Fan"):
        sw = self.switch_module(board, y, x0, col, label, [fan])
        x = x0 + (col + 1 + 1) * MODULE_W
        reg = self.device(board, "regulator", "Fan regulator (step type, 2-module)", poles=1, modules=2,
                          rating=None, standard="IS 11037 type step regulator (assumed)")
        t_in = self.terminal(board, "Regulator in", "SW", (x - .010, y + .010, -.035), reg)
        t_out = self.terminal(board, "Regulator out (to fan)", "REG", (x + .010, y + .010, -.035), reg)
        t_earth = self.terminal(board, "Regulator earth", "E", (x, y - .016, -.040), reg)
        rid = self.nid("RG")
        self.regulators.append({"id": rid, "deviceId": reg["id"], "enclosureId": board["id"], "steps": 5,
                                "defaultStep": 3, "points": [fan["id"]]})
        fan["regulator"] = rid
        reg["terminals"] = {"in": t_in, "out": t_out, "earth": t_earth}
        reg["regulatorId"] = rid
        board["modules"].append({"kind": "regulator", "row": 0 if y >= 0 else 1, "col": col + 1, "span": 2,
                                 "x": r4(x), "y": r4(y), "deviceId": reg["id"], "regulatorId": rid})
        board.setdefault("fanPairs", []).append({"switch": sw["id"], "regulator": reg["id"]})

    # ------------------------------------------------------------------ sockets
    def socket_plate(self, room, purpose, items, *, near=None, z_bottom=1.10, target=None, walls=None,
                     access=.40, label=None, prefer_latch=False, finishes=("wall-tile",), quiet=False):
        n_mod = sum(3 if k in ("socket6", "socket16") else 2 if k in ("mcb",) else 2 for k, _ in items)
        size = next(s for s in (2, 3, 4, 6, 8, 12) if s >= n_mod)
        if near is not None:
            m = near["mount"]
            target = target or (m["face"][0] + m["tangent"][0] * .3, m["face"][1] + m["tangent"][1] * .3)
        enc = self.place(room["id"], "socket-plate", label or f"{room['name']} · {purpose} sockets", size,
                         z_bottom=z_bottom, target=target, walls=walls, access=access, prefer_latch=prefer_latch,
                         required=False, finishes=finishes)
        if enc is None:
            if not quiet:
                self.notes.append(f"{room['name']}: no clear wall position for the {purpose} socket plate.")
            return None
        enc["purpose"] = purpose
        room["enclosureIds"].append(enc["id"])
        self.populate_sockets(enc, room, items, size)
        return enc

    def populate_sockets(self, enc, room, items, size):
        bw, bh = BOXES[size]
        cb_y = -bh / 2 + .014
        enc["connectors"] = {
            "P": self.terminal(enc, "Phase connector", "P", (-bw / 2 + .018, cb_y, -BOX_DEPTH + .012)),
            "N": self.terminal(enc, "Neutral connector", "N", (-bw / 2 + .036, cb_y, -BOX_DEPTH + .012)),
            "E": self.terminal(enc, "Earth connector", "E", (-bw / 2 + .054, cb_y, -BOX_DEPTH + .012)),
            "stud": self.terminal(enc, "Box earth stud", "E", (bw / 2 - .012, -bh / 2 + .012, -BOX_DEPTH + .004)),
        }
        cols = size if size <= 8 else 6
        x0 = -cols * MODULE_W / 2
        col = 0
        for kind, label in items:
            if kind in ("socket6", "socket16"):
                amp = 6 if kind == "socket6" else 16
                # socket (2 modules) followed by its control switch (1 module): CPWD 3.11.7
                sx = x0 + (col + 1) * MODULE_W
                pt = self.add_point(room, kind, self.local_to_world(enc, sx, 0, .006), f"{room['name']} · {label}",
                                    provenance="proposed (CPWD 3.11.6 height)", enclosureId=enc["id"], amps=amp)
                sock = self.device(enc, kind, f"{amp} A 3-pin shuttered socket", poles=1, modules=2,
                                   standard="IS 1293:2019", pointId=pt["id"])
                tl = self.terminal(enc, "Socket L", "SW", (sx + .008, -.010, -.034), sock)
                tn = self.terminal(enc, "Socket N", "N", (sx - .008, -.010, -.034), sock)
                te = self.terminal(enc, "Socket earth", "E", (sx, .012, -.034), sock)
                sock["terminals"] = {"L": tl, "N": tn, "E": te}
                enc["modules"].append({"kind": kind, "row": 0, "col": col, "span": 2, "x": r4(sx), "y": 0,
                                       "deviceId": sock["id"], "pointId": pt["id"]})
                col += 2
                sw = self.switch_module(enc, 0., x0, col, f"{amp} A socket", [pt])
                sw["kind"] = "switch16" if amp == 16 else "switch"
                col += 1
                pt["deviceId"] = sock["id"]
            elif kind == "mcb":
                sx = x0 + (col + .5) * MODULE_W
                dev = self.device(enc, "local-mcb", label, poles=1, modules=1, rating=None,
                                  standard="IS/IEC 60898 modular MCB (rating by designer)")
                t_in = self.terminal(enc, "MCB in", "L", (sx, .016, -.034), dev)
                t_out = self.terminal(enc, "MCB out", "SW", (sx, -.016, -.034), dev)
                dev["terminals"] = {"in": t_in, "out": t_out}
                sid = self.nid("S")
                self.switches.append({"id": sid, "deviceId": dev["id"], "enclosureId": enc["id"], "label": label,
                                      "points": [], "defaultOn": False, "mcb": True})
                dev["switchId"] = sid
                enc["modules"].append({"kind": "mcb", "row": 0, "col": col, "span": 1, "x": r4(sx), "y": 0,
                                       "deviceId": dev["id"], "switchId": sid, "label": label})
                col += 1
        for c in range(col, cols):
            enc["modules"].append({"kind": "blank", "row": 0, "col": c, "span": 1, "x": r4(x0 + (c + .5) * MODULE_W), "y": 0})

    def bedside_plates(self, room):
        """6 A sockets 70 cm above floor on each side of the bed head (CPWD 3.11.6(d)(i))."""
        beds = [it for it in self.scene["furniture"] if it.get("room_id") == room["id"] and it["kind"] == "bed"]
        for bed in beds:
            xs = [p[0] for p in bed["footprint"]]
            ys = [p[1] for p in bed["footprint"]]
            x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
            long_x = (x1 - x0) >= (y1 - y0)
            # the head is a short edge against a wall
            heads = ([("x0", [(x0, y0), (x0, y1)]), ("x1", [(x1, y0), (x1, y1)])] if long_x else
                     [("y0", [(x0, y0), (x1, y0)]), ("y1", [(x0, y1), (x1, y1)])])
            best = None
            for wall, side in self.house.faces_of_room(room["id"]):
                for edge, pts in heads:
                    d = max(abs(wall.offset(p) - side * wall.half) for p in pts)
                    if d < .15 and all(-.05 <= wall.along(p) <= wall.length + .05 for p in pts):
                        if best is None or d < best[0]:
                            best = (d, wall, side, sorted(wall.along(p) for p in pts))
            if not best:
                self.notes.append(f"{room['name']}: the bed head is not against a wall, so no bedside sockets are proposed.")
                continue
            _, wall, side, (a0, a1) = best
            span = self.house.face_span(wall, side, room["id"])
            placed, missing = 0, []
            for edge_s, direction in ((a0, -1), (a1, 1)):
                target_s = edge_s + direction * .2
                if not span or not (span[0] + .15 <= target_s <= span[1] - .15):
                    missing.append("is in a corner")       # bed side against a corner: no socket that side
                    continue
                tx, ty = wall.point(target_s, side)
                plate = self.socket_plate(room, "bedside", [("socket6", "Bedside 6 A socket")], z_bottom=.70,
                                          target=(tx, ty), walls={wall.ident}, access=.2,
                                          finishes=("wall-tile", "wall-panel"),
                                          label=f"{room['name']} · bedside socket", quiet=True)
                if plate is None:
                    missing.append("has no clear wall: the open door leaf, furniture or an opening covers it")
                    continue
                placed += 1
                if abs(plate["mount"]["along"] - target_s) > .35:
                    self.notes.append(f"{room['name']}: a bedside socket sits {abs(plate['mount']['along'] - target_s):.2f} m "
                                      f"from the bed side, the nearest clear wall position.")
            if missing and placed:
                self.notes.append(f"{room['name']}: bedside socket on one side only; the other side of the bed head {missing[0]}.")
            elif missing:
                self.notes.append(f"{room['name']}: no bedside socket; one side of the bed head {missing[0]} and the other "
                                  f"{missing[-1]}. The room's general socket serves the bed.")

    def kitchen_outlets(self, room):
        f = room["floor"]
        counter_top = .865   # from the kitchen splash-back tiles (0.865 m)
        run = next((it for it in self.scene["furniture"] if it.get("room_id") == room["id"] and it["kind"] == "kitchen-run"), None)
        if run:
            xs = [p[0] for p in run["footprint"]]
            ys = [p[1] for p in run["footprint"]]
            target = ((min(xs) + max(xs)) / 2 + .8, min(ys) + .6)
        else:
            target = None
        self.socket_plate(room, "counter", [("socket16", "16 A socket (appliance)"), ("socket6", "6 A socket (small appliance)")],
                          z_bottom=counter_top + .23, target=target, access=0., label="Kitchen counter sockets")
        fridge = next((it for it in self.scene["furniture"] if it.get("room_id") == room["id"] and it["kind"] == "kitchen-fridge"), None)
        if fridge:
            xs = [p[0] for p in fridge["footprint"]]
            ys = [p[1] for p in fridge["footprint"]]
            self.socket_plate(room, "refrigerator", [("socket16", "16 A socket (refrigerator)")], z_bottom=1.10,
                              target=(max(xs) + .2, max(ys)), access=.3, label="Refrigerator socket")

    def desk_plate(self, room):
        desk = next((it for it in self.scene["furniture"] if it.get("room_id") == room["id"] and it["kind"] == "desk"), None)
        if not desk:
            return
        xs = [p[0] for p in desk["footprint"]]
        ys = [p[1] for p in desk["footprint"]]
        self.socket_plate(room, "desk", [("socket6", "Desk 6 A socket"), ("socket6", "Desk 6 A socket")], z_bottom=1.10,
                          target=((min(xs) + max(xs)) / 2, max(ys)), access=0., label=f"{room['name']} · desk sockets")

    def care_plate(self, room):
        table = next((it for it in self.scene["furniture"] if it.get("room_id") == room["id"] and it["kind"] == "equipment-table"), None)
        if not table:
            return
        xs = [p[0] for p in table["footprint"]]
        ys = [p[1] for p in table["footprint"]]
        self.socket_plate(room, "equipment", [("socket16", "16 A socket (care equipment)"), ("socket6", "6 A socket (care equipment)")],
                          z_bottom=1.10, target=((min(xs) + max(xs)) / 2, max(ys)), access=0.,
                          label="Care room · equipment sockets")

    def bathroom_outlets(self, room, board):
        mirror = next((p for p in self.points if p["roomId"] == room["id"] and p["kind"] == "mirror-light"), None)
        target = mirror["position"][:2] if mirror else None
        self.socket_plate(room, "basin", [("socket6", "6 A socket (shaver / hair dryer)")], z_bottom=1.10, target=target,
                          access=.25, label=f"{room['name']} · basin socket")
        # Geyser control: 16 A MCB in a modular box at 1.1 m beside the bathroom switchboard (CPWD 3.11.6(c))
        m = board["mount"]
        mcb = None
        for direction in (1, -1):
            tgt = (m["face"][0] + m["tangent"][0] * .2 * direction, m["face"][1] + m["tangent"][1] * .2 * direction)
            mcb = self.socket_plate(room, "geyser control", [("mcb", "Geyser 16 A MCB")], target=tgt, access=.3,
                                    walls={m["wallId"]}, label=f"{room['name']} · geyser MCB", quiet=True)
            if mcb:
                break
        if mcb is None:
            tgt = (m["face"][0], m["face"][1])
            mcb = self.socket_plate(room, "geyser control", [("mcb", "Geyser 16 A MCB")], target=tgt, access=.3,
                                    label=f"{room['name']} · geyser MCB")
        if mcb:
            mcb["kind"] = "geyser-mcb"
        # Geyser socket >= 2 m, near an assumed heater position
        out = self.place(room["id"], "geyser-outlet", f"{room['name']} · geyser socket", 2, z_bottom=2.05,
                         access=0., prefer_latch=False, required=False,
                         extra_score=lambda w, s, a, mt: -abs(mt.face[0] - (mirror["position"][0] if mirror else mt.face[0])) * 0 +
                         (1.5 if mirror and math.dist(mt.face[:2], mirror["position"][:2]) > 1.0 else 0))
        if out:
            room["enclosureIds"].append(out["id"])
            bw, bh = BOXES[2]
            out["connectors"] = {
                "P": self.terminal(out, "Phase connector", "P", (-bw / 2 + .016, -bh / 2 + .014, -BOX_DEPTH + .012)),
                "N": self.terminal(out, "Neutral connector", "N", (-bw / 2 + .032, -bh / 2 + .014, -BOX_DEPTH + .012)),
                "E": self.terminal(out, "Earth connector", "E", (-bw / 2 + .048, -bh / 2 + .014, -BOX_DEPTH + .012)),
                "stud": self.terminal(out, "Box earth stud", "E", (bw / 2 - .012, -bh / 2 + .012, -BOX_DEPTH + .004)),
            }
            sx = 0.
            pt = self.add_point(room, "geyser-outlet", self.local_to_world(out, sx, 0, .006), f"{room['name']} · Water-heater socket",
                                provenance="assumed heater position (A-GEYSER)", enclosureId=out["id"], amps=16)
            sock = self.device(out, "socket16", "16 A 3-pin socket (water heater)", poles=1, modules=2,
                               standard="IS 1293:2019", pointId=pt["id"])
            tl = self.terminal(out, "Socket L", "SW", (.008, -.010, -.034), sock)
            tn = self.terminal(out, "Socket N", "N", (-.008, -.010, -.034), sock)
            te = self.terminal(out, "Socket earth", "E", (0, .012, -.034), sock)
            sock["terminals"] = {"L": tl, "N": tn, "E": te}
            out["modules"].append({"kind": "socket16", "row": 0, "col": 0, "span": 2, "x": 0, "y": 0,
                                   "deviceId": sock["id"], "pointId": pt["id"]})
            pt["deviceId"] = sock["id"]
            if mcb:
                sw = next(s for s in self.switches if s["enclosureId"] == mcb["id"])
                sw["points"].append(pt["id"])
                pt["controls"].append(sw["id"])
                pt["switchId"] = sw["id"]
                out["controlledFrom"] = mcb["id"]
                mcb["feeds"] = out["id"]

    # ------------------------------------------------------------------ routers
    def router(self, floor):
        if floor not in self.routers:
            wet = {r["id"]: 2.5 for r in self.rooms if r["wet"] and r["floor"] == floor + 1}
            self.routers[floor] = SlabRouter(self.house, floor, wet_penalty=wet)
        return self.routers[floor]


def _seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L))
    return math.dist(p, (ax + dx * t, ay + dy * t))
