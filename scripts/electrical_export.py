"""Assemble the electrical model JSON: data, walk-through steps and 2D plan."""
from __future__ import annotations

import math

try:
    from .electrical_geometry import inside, FLOOR_HEIGHT, SOFFIT, SLAB_CONDUIT
    from .electrical_design import COLOURS, r4
    from .electrical_sources import SOURCES, FACTS, ASSUMPTIONS, NOT_MODELLED
except ImportError:
    from electrical_geometry import inside, FLOOR_HEIGHT, SOFFIT, SLAB_CONDUIT
    from electrical_design import COLOURS, r4
    from electrical_sources import SOURCES, FACTS, ASSUMPTIONS, NOT_MODELLED

SCHEMA = "floorforge.electrical-tour.v3"
EYE = 1.63          # walker eye height above its feet (viewer WALK_SETTINGS.eye)


def model_dict(d, plan_hash):
    design_kw = round(sum(d.phase_load.values()) / 1000, 1)
    assumptions = [dict(a, text=a["text"].replace("{design_kw}", f"{design_kw:g}")) for a in ASSUMPTIONS]
    by_id = {}
    for coll in (d.enclosures, d.devices, d.points, d.boxes, d.conduits, d.circuits, d.switches, d.regulators):
        for x in coll:
            by_id[x["id"]] = x
    model = {
        "schema": SCHEMA,
        "architecturalPlanHash": plan_hash,
        "status": "Educational planning simulation — not an installation design, approved drawing or as-built record.",
        "units": "m", "up": "Z", "floorHeight": FLOOR_HEIGHT, "soffit": SOFFIT, "slabConduit": SLAB_CONDUIT,
        "supply": {"kind": "Three-phase, four-wire LT (assumed)", "nominal": "230 V phase–neutral / 400 V phase–phase, 50 Hz",
                   "transformer": "Local 11 kV / 433 V distribution transformer (typical; the 11 kV feeder never enters the house)",
                   "designLoadKW": design_kw, "phaseLoadW": d.phase_load, "assumption": "A-SUPPLY",
                   "basis": ["F-SUPPLY-LIMIT", "F-RATINGS", "F-VOLTAGE"]},
        "earthing": {"assumption": "A-EARTHING", "basis": ["F-CEA-EARTH", "F-CEA-2EARTH", "F-EARTH", "F-PE-CONDUIT"]},
        "colours": COLOURS, "colourBasis": "F-COLOUR",
        "sources": SOURCES, "facts": FACTS, "assumptions": assumptions, "notModelled": NOT_MODELLED,
        "distribution": d.distribution,
        "rooms": [{"id": r["id"], "name": r["name"], "kind": r["kind"], "floor": r["floor"], "polygon": r["polygon"],
                   "label": r["label"], "boardId": r.get("boardId"), "phase": d.room_phase.get(r["id"]),
                   "enclosureIds": r.get("enclosureIds", [])} for r in d.rooms],
        "enclosures": d.enclosures, "devices": d.devices, "terminals": d.terminals, "switches": d.switches,
        "regulators": d.regulators, "points": d.points, "boxes": d.boxes, "circuits": d.circuits,
        "conduits": d.conduits, "conductors": d.conductors,
        "notes": d.notes,
    }
    for c in d.conduits:
        c["reveal"] = reveal_pieces(d, c)
    model["traces"] = {c["id"]: trace(d, c, by_id) for c in d.circuits}
    model["plan"] = plan(d)
    return model


# ---------------------------------------------------------------------------
# Surface reveal of concealed runs
# ---------------------------------------------------------------------------

def reveal_pieces(d, conduit, step=.05):
    """Parts of a concealed conduit projected onto the finished room surface in front of it:
    slab runs onto the ceiling soffit, wall chases onto the wall face. Parts inside walls,
    over cove bands or outside enclosed rooms are omitted (they stay concealed)."""
    h = d.house
    pieces = []
    pts = conduit["points"]
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        if math.dist(a, b) < .01:
            continue
        horizontal = abs(a[2] - b[2]) < .002
        vertical = math.dist(a[:2], b[:2]) < .002
        if horizontal:
            floor = int((a[2] - .2) // FLOOR_HEIGHT)
            if floor < 0:
                continue                      # underground: shown on the 2D plan only
            soffit = h.soffit(floor)
            if a[2] < soffit - .01 or a[2] > soffit + .2:
                continue
            n = max(1, int(math.dist(a, b) / step))
            run = []
            for k in range(n + 1):
                t = k / n
                x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                room = h.room_at(x, y, floor)
                ok = room in d.room_by_id and h.overhead_bottom(x, y, floor) >= soffit - .005 and not _in_any_wall(h, x, y, floor)
                run.append((ok, room, x, y))
            start = None
            for k, (ok, room, x, y) in enumerate(run + [(False, None, 0, 0)]):
                if ok and start is None:
                    start = k
                if (not ok or (start is not None and room != run[start][1])) and start is not None:
                    end = k - 1
                    if end > start:
                        _, r0, x0, y0 = run[start]
                        _, _, x1, y1 = run[end]
                        pieces.append({"surface": "ceiling", "roomId": r0, "floor": floor,
                                       "a": [r4(x0), r4(y0), r4(soffit - .002)], "b": [r4(x1), r4(y1), r4(soffit - .002)],
                                       "normal": [0, 0, -1]})
                    start = k if ok else None
        elif vertical:
            x, y = a[0], a[1]
            z0, z1 = sorted((a[2], b[2]))
            floor = max(0, int((z0 + .05) // FLOOR_HEIGHT))
            wall = _wall_at(h, x, y, floor)
            if wall is None:
                continue
            off = wall.offset((x, y))
            side = 1 if off >= 0 else -1
            room = wall.sides[side]
            if room not in d.room_by_id and room != "outside":
                continue
            nx, ny = wall.face_normal(side)
            depth = wall.half - abs(off)
            lo = max(z0, floor * FLOOR_HEIGHT + .05)
            hi = min(z1, floor * FLOOR_HEIGHT + 2.99)
            if hi - lo < .02:
                continue
            # The strip sits on the finished face: tiles or panelling stand proud of the
            # plaster, so split the run where that finish starts or stops.
            along = wall.along((x, y))
            n = max(1, int(math.ceil((hi - lo) / step)))
            zs = [lo + (hi - lo) * k / n for k in range(n + 1)]
            fin = [h.finish_depth(wall, side, along, min(max(z, lo + .001), hi - .001), roles=("wall-tile", "wall-panel"))
                   for z in zs]
            start = 0
            for k in range(1, n + 1):
                if k < n and abs(fin[k] - fin[start]) < 1e-4:
                    continue
                za, zb, out = zs[start], zs[k], depth + fin[start] + .002
                if zb - za >= .02:
                    pieces.append({"surface": "wall", "roomId": room, "floor": floor, "wallId": wall.ident,
                                   "a": [r4(x + nx * out), r4(y + ny * out), r4(za)],
                                   "b": [r4(x + nx * out), r4(y + ny * out), r4(zb)],
                                   "normal": [r4(nx), r4(ny), 0]})
                start = k
    return pieces


def _wall_at(h, x, y, floor):
    for w in h.walls.values():
        if w.floor != floor:
            continue
        if abs(w.offset((x, y))) <= w.half + .002 and -.01 <= w.along((x, y)) <= w.length + .01:
            return w
    return None


def _in_any_wall(h, x, y, floor):
    return _wall_at(h, x, y, floor) is not None


# ---------------------------------------------------------------------------
# Walk-through steps
# ---------------------------------------------------------------------------

def trace(d, c, by_id):
    """Ordered steps from the service to one representative point of a circuit."""
    steps = []
    dist = d.distribution
    meter, main, lwb = d.enc(dist["meter"]), d.enc(dist["mainDB"]), d.enc(dist["mainLWB"])
    svc = [k for k in d.conduits if k["function"] == "service"]
    steps.append(_step(d, "Supply arrives at the sealed meter",
                       "The DISCOM's underground service cable rises inside the external wall into the back of the meter box. "
                       "The meter belongs to the licensee and stays sealed; the incoming cable is live even when the house main switch is off.",
                       [meter["id"]] + [k["id"] for k in svc[:1]], meter))
    q1, f1 = d.board["main"]["incomer"], d.board["main"]["rccb"]
    steps.append(_step(d, "Meter tails reach the main DB",
                       "Four meter tails (R, Y, B, N) pass through a sleeve in the wall into the main DB, behind the meter.",
                       [k["id"] for k in svc[1:2]] + [main["id"]], main))
    steps.append(_step(d, "Main switch and 30 mA RCCB",
                       "The 4-pole incoming MCB isolates and protects the whole installation (CEA Reg. 37). The 4-pole RCCB "
                       "compares the currents in R, Y, B and N and trips on a residual (earth-leakage) current of 30 mA (CEA Reg. 44).",
                       [main["id"], q1["id"], f1["id"]], main))
    if c["floor"] == 1 or c["id"] == "SUB":
        subc = next(x for x in d.circuits if x["id"] == "SUB")
        steps.append(_step(d, "Submain MCB on the B phase",
                           "One outgoing MCB on the blue-phase busbar protects the submain cable to the first floor.",
                           [main["id"], subc["mcb"]], main))
        riser = next(k for k in d.conduits if k["function"] == "submain")
        steps.append(_step(d, "Submain rises to the first floor",
                           "The submain (phase, neutral and protective conductor) leaves the loose-wire box, runs in the first-floor "
                           "slab and rises through a sleeved slab opening into the wall below the first-floor sub-DB.",
                           [riser["id"]], riser, conduit=riser))
        sub = d.enc(dist["subDB"])
        q2 = d.board["sub"]["incomer"]
        steps.append(_step(d, "First-floor sub-DB",
                           "A 2-pole isolator switches the first-floor supply; single-pole MCBs on a comb busbar protect each circuit.",
                           [sub["id"], q2["id"]], sub))
        if c["id"] == "SUB":
            return _numbered(steps)
        lwb = d.enc(dist["subLWB"])
    mcb = by_id.get(c.get("mcb"))
    if mcb:
        steps.append(_step(d, f"{c['id']} MCB on the {c['phase']} phase",
                           f"The single-pole MCB for {c['id']} sits on the {c['phase']}-phase tooth of the busbar and opens only the "
                           "phase conductor. Its neutral returns through the RCCB's neutral bar and is never switched (CEA Reg. 17).",
                           [mcb["id"], d.enc(c["db"])["id"]], d.enc(c["db"])))
    steps.append(_step(d, "Outgoing P/N/E terminal blocks",
                       f"{c['id']} leaves from its own phase, neutral and earth terminal blocks in the loose-wire box (CPWD 3.18.2).",
                       [lwb["id"]], lwb))
    target = _target_point(d, c)
    encs = [d.enc(e) for e in c["enclosures"]]
    last_enc = next((e for e in encs if target and (e["roomId"] == target["roomId"] and (e["kind"] == "switchboard" or
                                                                                       target.get("enclosureId") == e["id"]))), encs[-1])
    path_encs = encs[:encs.index(last_enc) + 1] if last_enc in encs else encs
    prev = lwb
    for e in path_encs:
        run = next((k for k in d.conduits if k["function"] in ("lighting", "power") and k["kind"] == "circuit"
                    and {k["from"], k["to"]} == {prev["id"], e["id"]}), None)
        if run:
            steps.append(_step(d, f"Concealed run to the {e['label'].split(' · ')[0]}",
                               "Phase, neutral and protective conductor run together in one PVC conduit (CPWD 5.4.3(g), 5.4.4): "
                               "up a wall chase, through the RCC slab (laid before concreting) and down a chase to the next box.",
                               [run["id"]], run, conduit=run))
        steps.append(_step(d, f"{e['label']}",
                           "The circuit lands on phase, neutral and earth connector blocks in this box (CPWD 3.5.6); "
                           "point wiring starts here. Open the plate to see the terminals.",
                           [e["id"]], e))
        prev = e
    if target:
        sw = next((s for s in d.switches if target["id"] in s["points"]), None)
        if sw:
            dev = by_id[sw["deviceId"]]
            text = ("The fan switch feeds the step regulator in series; the regulated live goes to the fan (IS 732 C-8.1). "
                    "Only the live is switched." if target["kind"] == "fan" else
                    "The switch interrupts only the live conductor (CPWD 3.11.5); the neutral goes straight to the point.")
            refs = [dev["id"]] + ([by_id[target["regulator"]]["deviceId"]] if target.get("regulator") else [])
            steps.append(_step(d, f"{sw['label']} switch", text, refs, d.enc(sw["enclosureId"])))
        legs = [k for k in d.conduits if k["kind"] == "point" and c["id"] in k["circuitIds"] and
                any(_serves(d, w, target["id"]) for w in k["carries"])]
        legs = _order_legs(legs, d.enc(sw["enclosureId"])["id"] if sw else None)
        if legs:
            what_live = "regulated live" if target["kind"] == "fan" else "switched live"
            steps.append(_step(d, "Point wiring through the slab",
                               f"From the board the {what_live}, neutral and protective conductor rise in a wall chase, then run in the "
                               f"slab{' through ' + str(len(legs) - 1) + ' intermediate point box' + ('es' if len(legs) > 2 else '') if len(legs) > 1 else ''} "
                               "to the point. Neutral and earth are looped at each box; only this point's live is switched.",
                               [leg["id"] for leg in legs], legs[-1], conduit=legs[-1]))
        box = by_id.get(target.get("boxId"))
        what = {"fan": "Fan box with hook: the regulated live, neutral and protective conductor reach the fan's connector. "
                       "The fan's internal motor wiring is not shown.",
                "downlight": "Light point box above the downlight: switched live, neutral and protective conductor.",
                }.get(target["kind"], "Outlet: live (through its control switch or MCB), neutral and protective earth.")
        steps.append(_step(d, target["label"], what, [target["id"]] + ([box["id"]] if box else []), box or target))
    return _numbered(steps)


def _numbered(steps):
    for i, s in enumerate(steps):
        s["n"] = i + 1
    return steps


def _serves(d, wid, pid):
    k = next(x for x in d.conductors if x["id"] == wid)
    return pid in k.get("serves", []) and k["role"] in ("SW", "REG", "N")


def _order_legs(legs, start):
    out, cur, left = [], start, list(legs)
    while left:
        nxt = next((k for k in left if cur in (k["from"], k["to"])), None)
        if nxt is None:
            out.extend(left)
            break
        out.append(nxt)
        left.remove(nxt)
        cur = nxt["to"] if nxt["from"] == cur else nxt["from"]
    return out


def _target_point(d, c):
    pts = [p for p in d.points if p["id"] in c["points"]]
    for kind in ("fan", "downlight", "socket16", "geyser-outlet", "socket6"):
        for p in pts:
            if p["kind"] == kind:
                return p
    return pts[0] if pts else None


def _step(d, title, text, refs, obj, conduit=None):
    view = _view(d, obj, conduit)
    focus = view["target"]
    dev = next((x for x in d.devices if refs and x["id"] == refs[-1]), None)
    if dev is not None and dev.get("enclosureId") and "x" in dev:
        e = d.enc(dev["enclosureId"])
        focus = [r4(v) for v in d.local_to_world(e, dev["x"], dev.get("y", 0), -.02)]
        view = dict(view, target=focus)
    return {"title": title, "text": text, "refs": [r for r in refs if r], "floor": view["floor"], "roomId": view.get("roomId"),
            "focus": focus, "view": view}


def _view(d, obj, conduit):
    """A standing viewpoint inside a room (or outside) from which `obj` is in view."""
    h = d.house
    if conduit is not None and conduit.get("reveal"):
        # The tour opens the longest revealed piece of this conduit in the step's room,
        # so stand where that piece is in view and aim at its middle.
        piece = max((q for q in conduit["reveal"] if q["roomId"] in d.room_by_id),
                    key=lambda q: math.dist(q["a"], q["b"]), default=None)
        if piece is not None:
            mid = [r4((piece["a"][j] + piece["b"][j]) / 2) for j in range(3)]
            floor, room = piece["floor"], piece["roomId"]
            if piece["surface"] == "ceiling":
                eye = _free_spot(d, room, floor, mid, 1.15)
                if eye:
                    return {"foot": [r4(eye[0]), r4(eye[1]), floor * FLOOR_HEIGHT], "target": mid, "floor": floor, "roomId": room}
            else:
                nx, ny = piece["normal"][0], piece["normal"][1]
                for wc, fc in TIERS:
                    for dist in (1.5, 1.2, 1.9, 1.0, .8):
                        ex, ey = mid[0] + nx * dist, mid[1] + ny * dist
                        if _ok_spot(d, room, floor, ex, ey, wc, fc):
                            zt = max(floor * FLOOR_HEIGHT + 1.2, min(mid[2], floor * FLOOR_HEIGHT + 2.6))
                            return {"foot": [r4(ex), r4(ey), floor * FLOOR_HEIGHT], "target": [mid[0], mid[1], r4(zt)],
                                    "floor": floor, "roomId": room}
    if conduit is not None:
        pts = conduit["points"]
        best = None
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            L = math.dist(a, b)
            if L < .15:
                continue
            mid = [(a[j] + b[j]) / 2 for j in range(3)]
            floor = max(0, min(1, int((mid[2] - .2) // FLOOR_HEIGHT)))
            room = h.room_at(mid[0], mid[1], floor)
            if room not in d.room_by_id:
                room = None
            horizontal = abs(a[2] - b[2]) < .01
            score = min(L, 2.5) + (3 if room else 0) + (1 if horizontal else 0)
            if best is None or score > best[0]:
                best = (score, mid, floor, room, horizontal, a, b)
        if best:
            _, mid, floor, room, horizontal, a, b = best
            if horizontal and room:
                eye = _free_spot(d, room, floor, mid, 1.15)
                if eye:
                    return {"foot": [r4(eye[0]), r4(eye[1]), floor * FLOOR_HEIGHT], "target": [r4(v) for v in mid], "floor": floor, "roomId": room}
            # vertical chase: stand in front of the wall face
            wall = min((w for w in h.walls.values() if w.floor == floor and any(s in d.room_by_id for s in w.sides.values())),
                       key=lambda w: abs(abs(w.offset(mid[:2])) - w.half) + (0 if -.05 <= w.along(mid[:2]) <= w.length + .05 else 9))
            side = 1 if wall.offset(mid[:2]) >= 0 else -1
            room = wall.sides[side]
            nx, ny = wall.face_normal(side)
            for wc, fc in TIERS:
                for dist in (1.5, 1.2, 1.9, 1.0, .8):
                    ex, ey = mid[0] + nx * dist, mid[1] + ny * dist
                    if room != "outside" and _ok_spot(d, room, floor, ex, ey, wc, fc):
                        zt = max(floor * FLOOR_HEIGHT + 1.2, min(mid[2], floor * FLOOR_HEIGHT + 2.6))
                        return {"foot": [r4(ex), r4(ey), floor * FLOOR_HEIGHT], "target": [r4(mid[0]), r4(mid[1]), r4(zt)], "floor": floor, "roomId": room}
            return {"foot": None, "target": [r4(v) for v in mid], "floor": floor, "roomId": room}
    if "mount" in obj:
        m = obj["mount"]
        fx, fy, fz = m["face"]
        nx, ny = m["normal"]
        floor = obj["floor"]
        room = obj.get("roomId") if not obj.get("exterior") else None
        if obj.get("exterior"):
            spot = _outside_spot(d, (fx, fy), (nx, ny))
            if spot:
                return {"foot": [r4(spot[0]), r4(spot[1]), r4(d.distribution["ground"])], "target": [fx, fy, fz], "floor": 0, "roomId": None}
            return {"foot": None, "target": [fx, fy, fz], "floor": 0, "roomId": None}
        tx, ty = -ny, nx
        for wc, fc in TIERS:
            for ang in (0, 20, -20, 35, -35, 50, -50, 65, -65):
                a = math.radians(ang)
                ux, uy = nx * math.cos(a) + tx * math.sin(a), ny * math.cos(a) + ty * math.sin(a)
                for dist in (1.3, 1.1, 1.6, .9, 2.0, .75):
                    ex, ey = fx + ux * dist, fy + uy * dist
                    if _ok_spot(d, room, floor, ex, ey, wc, fc):
                        return {"foot": [r4(ex), r4(ey), floor * FLOOR_HEIGHT], "target": [fx, fy, fz], "floor": floor, "roomId": room}
        return {"foot": None, "target": [fx, fy, fz], "floor": floor, "roomId": room}
    pos = obj["position"]
    floor = obj.get("floor", 0)
    room = obj.get("roomId")
    if room:
        eye = _free_spot(d, room, floor, pos, 1.5)
        if eye:
            return {"foot": [r4(eye[0]), r4(eye[1]), floor * FLOOR_HEIGHT], "target": pos, "floor": floor, "roomId": room}
    return {"foot": None, "target": pos, "floor": floor, "roomId": room}


def _outside_spot(d, face, normal):
    """A clear standing spot outside the house (not on the parked car, planting, steps or gates)."""
    foot = [[x / 1000, y / 1000] for x, y in d.building["footprint"]]
    plot = [[x / 1000, y / 1000] for x, y in d.building["plot"]]
    g = d.distribution["ground"]
    nx, ny = normal
    tx, ty = -ny, nx
    blocked = ("vehicle", "landscape", "plant-proxy", "step", "gate", "outdoor-furniture", "pipe", "column", "porch")
    for ang in (0, 25, -25, 45, -45, 60, -60, 75, -75):
        a = math.radians(ang)
        ux, uy = nx * math.cos(a) + tx * math.sin(a), ny * math.cos(a) + ty * math.sin(a)
        for dist in (1.3, 1.1, 1.6, .9, 2.0):
            x, y = face[0] + ux * dist, face[1] + uy * dist
            if inside(x, y, foot) or not inside(x, y, plot):
                continue
            if any(b.role in blocked and b.hits((x - .35, y - .35, g + .05), (x + .35, y + .35, g + 1.8)) for b in d.house.obstacles):
                continue
            return (x, y)
    return None


def _ok_spot(d, room, floor, x, y, wall_clear=.35, furniture=.3):
    if not room or room == "outside" or room not in d.room_by_id:
        return False
    if not d.router(floor)._solid(x, y):
        return False                       # stand under a normal ceiling, not a double-height void or stair well
    r = d.house.rooms.get(room)
    if not r or not inside(x, y, r["polygon"]):
        return False
    poly = r["polygon"]
    for k in range(len(poly)):
        a, b = poly[k], poly[(k + 1) % len(poly)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0, min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / L))
        if math.dist((x, y), (a[0] + dx * t, a[1] + dy * t)) < wall_clear:
            return False
    for it in d.scene["furniture"]:
        if it.get("floor") != floor or not it.get("footprint"):
            continue
        xs = [p[0] for p in it["footprint"]]
        ys = [p[1] for p in it["footprint"]]
        if min(xs) - furniture <= x <= max(xs) + furniture and min(ys) - furniture <= y <= max(ys) + furniture:
            return False
    return True


TIERS = ((.35, .3), (.25, .15), (.2, .05))


def _free_spot(d, room, floor, target, dist):
    for wc, fc in TIERS:
        best = None
        for k in range(24):
            a = k / 24 * math.tau
            for rr in (dist, dist * .75, dist * 1.3, dist * .5, dist * .35):
                x, y = target[0] + math.cos(a) * rr, target[1] + math.sin(a) * rr
                if _ok_spot(d, room, floor, x, y, wc, fc):
                    score = -abs(rr - dist)
                    if best is None or score > best[0]:
                        best = (score, (x, y))
        if best:
            return best[1]
    return None


# ---------------------------------------------------------------------------
# 2D plan
# ---------------------------------------------------------------------------

def plan(d):
    b = d.building
    floors = []
    names = {s["id"]: s["name"] for s in b["spaces"]}
    for f in (0, 1):
        walls = [[[r4(x / 1000), r4(y / 1000)] for x, y in w["polygon"]] for w in b["walls"] if w["floor"] == f]
        openings = []
        for w in d.house.walls.values():
            if w.floor != f:
                continue
            for o in w.openings:
                p0, p1 = w.point(o.s0, 0), w.point(o.s1, 0)
                swing = None
                if o.swing:
                    side = next((s for s in (1, -1) if w.sides[s] == o.swing), None)
                    if side:
                        swing = list(w.face_normal(side))
                openings.append({"id": o.ident, "kind": o.kind, "p0": [r4(v) for v in p0], "p1": [r4(v) for v in p1],
                                 "hinge": o.hinge, "swingNormal": swing})
        rooms = []
        for r in d.scene["rooms"]:
            if r["floor"] != f:
                continue
            room = next((x for x in d.rooms if x["id"] == r["id"]), None)
            rooms.append({"id": r["id"], "name": room["name"] if room else names.get(r["id"], r["name"]),
                          "polygon": [[r4(x), r4(y)] for x, y in r["polygon"]], "label": room["label"] if room else d.label_point(r["polygon"], f),
                          "enclosed": bool(room)})
        roof = next(x for x in b["roofs"] if x["floor"] == f)
        voids = [[[r4(x / 1000), r4(y / 1000)] for x, y in hl] for c in roof["ceiling"] for hl in c.get("holes", [])]
        floors.append({"floor": f, "walls": walls, "openings": openings, "rooms": rooms, "voids": voids})
    xs = [p[0] / 1000 for p in b["plot"]]
    ys = [p[1] / 1000 for p in b["plot"]]
    return {"floors": floors, "bounds": [min(xs), min(ys), max(xs), max(ys)]}
