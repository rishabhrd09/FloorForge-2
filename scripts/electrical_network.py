"""Distribution, circuits, concealed routes and the conductor netlist.

Operates on an `electrical_design.Design` after its rooms are laid out:

* meter (DISCOM, sealed), main DB + loose-wire box, first-floor sub-DB, earth pits
* final circuits grouped within CPWD limits, rooms kept on one phase, phases balanced
* conduit runs: vertical wall chases + RCC slab runs (A* around slab openings)
* every conductor from terminal to terminal, with the conduits it passes through
"""
from __future__ import annotations

import math
from collections import defaultdict

try:
    from .electrical_design import (BOXES, BOX_DEPTH, TPN, SPN, LWB_H, METER_BOX, METER, WIRE_OD, CHASE_DEPTH,
                                    JB_D, JB_DEPTH, FILL_BENT, LIGHT_POINTS_MAX, PHASES, COLOURS, r4, p3)
    from .electrical_geometry import SLAB_CONDUIT, inside, make_mount, search_mounts
except ImportError:
    from electrical_design import (BOXES, BOX_DEPTH, TPN, SPN, LWB_H, METER_BOX, METER, WIRE_OD, CHASE_DEPTH,
                                   JB_D, JB_DEPTH, FILL_BENT, LIGHT_POINTS_MAX, PHASES, COLOURS, r4, p3)
    from electrical_geometry import SLAB_CONDUIT, inside, make_mount, search_mounts

DESIGN_W = {"fan": 60, "socket6": 100, "socket16": 1000, "geyser-outlet": 1000}   # CPWD 3.9.2-3.9.3
LIGHTING_KINDS = {"downlight", "cove", "mirror-light", "undercabinet", "fan", "exhaust"}
SOCKET_KINDS = {"socket6", "socket16"}


# ---------------------------------------------------------------------------
# Distribution equipment
# ---------------------------------------------------------------------------

def place_distribution(d):
    """Main DB in the room connecting to the entry (CPWD 3.20.9) with 1 m clear in front
    (CEA Reg. 39), preferably on an external wall so the sealed meter can sit directly
    behind it, readable from outside the house; first-floor sub-DB in a first-floor
    common area (CPWD 3.19.1); two earth pits >= 1.5 m out and >= 3 m apart (CPWD F.8.9)."""
    h = d.house
    w_db, h_db, d_db = TPN
    lwb_h = LWB_H["tpn"]
    z_db = 2.0 - lwb_h - h_db / 2                 # loose-wire box top at 2.0 m (WM: DB not above 2 m)
    ground = -.405
    z_meter = ground + 1.30
    mb_w, mb_h, mb_d = METER_BOX
    entry_wall = next(w for w in h.walls.values() for o in w.openings if o.kind == "entry")
    entry = next(o for o in entry_wall.openings if o.kind == "entry")
    entry_room = next(s for s in entry.connects if s != "outside")
    door = entry_wall.point((entry.s0 + entry.s1) / 2, 0)
    best = None
    for room_id in (entry_room, "g-dining"):
        cands = search_mounts(h, room_id, width=w_db, height=h_db + lwb_h, z=z_db + lwb_h / 2, recess=d_db, access=1.0,
                              access_band=(.2, 2.0), prefer_latch=False, step=.05,
                              reserved=[m for ms in d.reserved.values() for m in ms])
        for m in cands:
            wall = h.walls[m.wall]
            meter_along = None
            if wall.external and wall.sides[-m.side] == "outside":
                for k in range(0, 8):
                    for sgn in (1, -1):
                        a = m.along + sgn * k * .05
                        if not (mb_w / 2 + .15 <= a <= wall.length - mb_w / 2 - .15):
                            continue
                        if h.opening_conflict(wall, a, mb_w, z_meter - mb_h / 2, z_meter + mb_h / 2):
                            continue
                        if h.blockers(wall, -m.side, a, mb_w + .1, z_meter - mb_h / 2, z_meter + mb_h / 2 + .3, mb_d + .6,
                                      ignore=("wall-tile", "court", "plinth", "site")):
                            continue
                        meter_along = a
                        break
                    if meter_along is not None:
                        break
            score = (5.0 if meter_along is not None else 0.) - .15 * math.dist(m.face[:2], door) + \
                    (1.0 if room_id == entry_room else 0.)
            if best is None or score > best[0]:
                best = (score, room_id, wall, m.side, m.along, meter_along)
    if best is None:
        raise ValueError("No clear span for the main DB")
    _, room_id, wall, side, along, meter_along = best
    if meter_along is None:
        raise ValueError("Main DB has no external meter position behind it")
    db = _enclosure(d, room_id, "main-db", "Main distribution board (TPN, double door)", wall, side, along, w_db, h_db, z_db, d_db)
    lwb = _enclosure(d, room_id, "loose-wire-box", "Loose-wire box · outgoing P/N/E terminal blocks", wall, side, along,
                     w_db, lwb_h, 2.0 - lwb_h / 2, d_db)
    db["lwb"] = lwb["id"]
    lwb["db"] = db["id"]
    meter = _enclosure(d, room_id, "meter", "DISCOM energy meter (sealed) in meter box", wall, -side, meter_along,
                       mb_w, mb_h, z_meter, 0., surface=mb_d)
    meter["exterior"] = True
    # First-floor sub-DB: common area, internal wall, 1 m clear, shortest submain
    w_s, h_s, d_s = SPN
    lwb_sh = LWB_H["spn"]
    z_sub = 2.0 - lwb_sh - h_s / 2
    best_sub = None
    router = d.router(0)
    for room_id2 in ("u-lobby", "u-lounge", "u-stair"):
        cands = search_mounts(h, room_id2, width=w_s, height=h_s + lwb_sh, z=z_sub + lwb_sh / 2, recess=d_s, access=1.0,
                              access_band=(.2, 2.0), reserved=[m for ms in d.reserved.values() for m in ms],
                              prefer_latch=False, allow_external=False, step=.05)
        for m in cands[:80]:
            w2 = h.walls[m.wall]
            cx, cy = w2.point(m.along, m.side, d_s / 2)
            if not router._solid(cx, cy):
                continue                      # the riser rises from a solid part of the first-floor slab
            dist = abs(cx - db["mount"]["face"][0]) + abs(cy - db["mount"]["face"][1])
            if best_sub is None or dist < best_sub[0]:
                best_sub = (dist, room_id2, w2, m.side, m.along)
    if best_sub is None:
        raise ValueError("No position for the first-floor sub-DB")
    _, room_id2, w2, side2, along2 = best_sub
    sub = _enclosure(d, room_id2, "sub-db", "First-floor sub-distribution board (SPN, double door)",
                     w2, side2, along2, w_s, h_s, 3.15 + z_sub, d_s)
    slwb = _enclosure(d, room_id2, "loose-wire-box", "Loose-wire box · first-floor P/N/E terminal blocks",
                      w2, side2, along2, w_s, lwb_sh, 3.15 + 2.0 - lwb_sh / 2, d_s)
    sub["lwb"] = slwb["id"]
    slwb["db"] = sub["id"]
    # Earth pits: outside the footprint by >= 1.5 m, >= 3 m apart (CPWD F.8.9), clear of vehicles,
    # steps, gates and planting, as close to the meter as possible.
    pits = [_earth_pit(d, (p[0], p[1], d.house.ground_at(p[0], p[1], ground))) for p in _pit_positions(d, meter, ground)]
    d.distribution = {"meter": meter["id"], "mainDB": db["id"], "mainLWB": lwb["id"], "subDB": sub["id"],
                      "subLWB": slwb["id"], "pits": [p["id"] for p in pits], "ground": ground}
    return d.distribution


def _pit_positions(d, meter, ground):
    h = d.house
    foot = [[x / 1000, y / 1000] for x, y in d.building["footprint"]]
    plot = [[x / 1000, y / 1000] for x, y in d.building["plot"]]
    mx, my, _ = meter["mount"]["face"]
    blocked_roles = ("step", "porch", "gate", "pipe", "canopy", "plant-proxy", "vehicle", "column", "outdoor-furniture", "drain")
    cands = []
    for i in range(-40, 41):
        for j in range(-40, 41):
            px, py = mx + i * .2, my + j * .2
            if not inside(px, py, plot) or inside(px, py, foot):
                continue
            edge = min(_seg(px, py, foot[k], foot[(k + 1) % len(foot)]) for k in range(len(foot)))
            if edge < 1.5:
                continue
            boundary = min(_seg(px, py, plot[k], plot[(k + 1) % len(plot)]) for k in range(len(plot)))
            if boundary < .5:
                continue
            if any(b.role in blocked_roles and b.hits((px - .3, py - .3, ground - .2), (px + .3, py + .3, ground + .6))
                   for b in h.obstacles):
                continue
            cands.append((math.dist((px, py), (mx, my)), px, py))
    cands.sort()
    for a in cands:
        for b in cands:
            if math.dist(a[1:], b[1:]) >= 3.0:
                return [(a[1], a[2], ground), (b[1], b[2], ground)]
    raise ValueError("No room for two earth pits")


def _seg(px, py, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - a[0]) * dx + (py - a[1]) * dy) / L))
    return math.dist((px, py), (a[0] + dx * t, a[1] + dy * t))


def _enclosure(d, room_id, kind, label, wall, side, along, w, hgt, z, depth, surface=0.):
    mount = make_mount(d.house, wall, side, room_id, along, w, hgt, z, depth).as_dict()
    eid = d.nid({"main-db": "DB", "sub-db": "DB", "loose-wire-box": "LW", "meter": "MT"}[kind])
    floor = wall.floor
    enc = {"id": eid, "kind": kind, "label": label, "roomId": room_id, "floor": floor, "mount": mount,
           "size": {"w": r4(w), "h": r4(hgt), "boxW": r4(w), "boxH": r4(hgt), "depth": depth, "surface": surface},
           "modules": [], "circuitIds": [], "conduitIds": []}
    d.enclosures.append(enc)
    d.reserved[mount["wallId"]].append({"wallId": mount["wallId"], "side": mount["side"], "along": mount["along"],
                                        "width": w + .04, "z": mount["z"], "height": hgt, "recess": depth})
    return enc


def _earth_pit(d, pos):
    bid = d.nid("EP")
    pit = {"id": bid, "kind": "earth-pit", "label": "Earth electrode pit (inspection chamber)", "floor": 0,
           "roomId": None, "position": [r4(pos[0]), r4(pos[1]), r4(pos[2])], "size": [.30, .30, .30],
           "electrode": "Pipe or plate electrode below the chamber (type and depth by designer; CPWD F.8.9)"}
    d.boxes.append(pit)
    return pit


# ---------------------------------------------------------------------------
# Circuits
# ---------------------------------------------------------------------------

def group_circuits(d):
    """Group points into final circuits; keep each room on one phase; balance phases."""
    rooms = [r for r in d.rooms if r.get("enclosureIds")]
    load = {r["id"]: sum(DESIGN_W.get(p["kind"], 0) for p in d.points if p["roomId"] == r["id"]) for r in rooms}
    phase_load = {p: 0 for p in PHASES}
    room_phase = {}
    upper = [r for r in rooms if r["floor"] == 1]
    lower = sorted([r for r in rooms if r["floor"] == 0], key=lambda r: -load[r["id"]])
    # the single-phase first-floor sub-DB takes one phase (A-SUBDB)
    up_load = sum(load[r["id"]] for r in upper)
    up_phase = "B"
    phase_load[up_phase] += up_load
    for r in upper:
        room_phase[r["id"]] = up_phase
    # ground floor: contiguous zones (west -> east) so a circuit serves neighbouring rooms;
    # choose the split that best balances the three phases (CPWD 3.2.10)
    sweep = sorted(lower, key=lambda r: (r["label"][0], r["label"][1]))
    best = None
    n = len(sweep)
    for i in range(1, n):
        for j in range(i, n + 1):
            zones = {"R": sweep[:i], "Y": sweep[i:j], "B": sweep[j:]}
            tot = {p: phase_load[p] + sum(load[r["id"]] for r in zones[p]) for p in PHASES}
            spread = max(tot.values()) - min(tot.values())
            if best is None or spread < best[0]:
                best = (spread, zones, tot)
    _, zones, tot = best
    for ph, rs in zones.items():
        for r in rs:
            room_phase[r["id"]] = ph
    phase_load = tot
    d.room_phase = room_phase
    d.phase_load = phase_load
    db_of = {0: d.distribution["mainDB"], 1: d.distribution["subDB"]}
    circuits = []
    # --- lighting circuits: per floor and phase, rooms in a nearest-neighbour chain
    for floor in (0, 1):
        for ph in PHASES:
            rs = [r for r in rooms if r["floor"] == floor and room_phase[r["id"]] == ph and r.get("boardId")]
            if not rs:
                continue
            chain = _chain(d, [d.enc(r["boardId"]) for r in rs], d.enc(db_of[floor]))
            current, count = [], 0
            for board in chain:
                n = sum(1 for p in d.points if p["roomId"] == board["roomId"] and p["kind"] in LIGHTING_KINDS)
                if current and count + n > LIGHT_POINTS_MAX:
                    circuits.append(("lighting", floor, ph, current))
                    current, count = [], 0
                current.append(board)
                count += n
            if current:
                circuits.append(("lighting", floor, ph, current))
    # --- power circuits (CPWD 3.10.3) and dedicated geyser circuits
    for floor in (0, 1):
        for ph in PHASES:
            plates = [e for e in d.enclosures if e["floor"] == floor and e["kind"] == "socket-plate"
                      and room_phase.get(e["roomId"]) == ph]
            if not plates:
                continue
            chain = _chain(d, plates, d.enc(db_of[floor]))
            current, n6, n16 = [], 0, 0
            for plate in chain:
                a6 = sum(1 for p in d.points if p.get("enclosureId") == plate["id"] and p["kind"] == "socket6")
                a16 = sum(1 for p in d.points if p.get("enclosureId") == plate["id"] and p["kind"] == "socket16")
                if current and not _power_ok(n6 + a6, n16 + a16):
                    circuits.append(("power", floor, ph, current))
                    current, n6, n16 = [], 0, 0
                current.append(plate)
                n6 += a6
                n16 += a16
            if current:
                circuits.append(("power", floor, ph, current))
            for mcb in [e for e in d.enclosures if e["floor"] == floor and e["kind"] == "geyser-mcb"
                        and room_phase.get(e["roomId"]) == ph]:
                circuits.append(("geyser", floor, ph, [mcb, d.enc(mcb["feeds"])]))
    # number circuits per DB in a readable order: lighting, power, geyser
    order = {"lighting": 0, "power": 1, "geyser": 2}
    circuits.sort(key=lambda c: (c[1], order[c[0]], PHASES.index(c[2])))
    for kind, floor, ph, encs in circuits:
        cid = f"{'G' if floor == 0 else 'F'}{len([c for c in d.circuits if c['floor'] == floor]) + 1}"
        rooms_served = list(dict.fromkeys(e["roomId"] for e in encs))
        names = [d.room_by_id[rid]["name"] for rid in rooms_served]
        label = {"lighting": "Lights & fans", "power": "Sockets", "geyser": "Water heater"}[kind]
        size = 1.5 if kind == "lighting" else 4.0
        points = [p for p in d.points if (p["roomId"] in rooms_served and p["kind"] in LIGHTING_KINDS)
                  ] if kind == "lighting" else [p for p in d.points if p.get("enclosureId") in {e["id"] for e in encs}]
        if kind == "geyser":
            points = [p for p in d.points if p.get("enclosureId") == encs[1]["id"]]
        circ = {"id": cid, "kind": kind, "floor": floor, "phase": ph, "label": f"{cid} · {label} · {', '.join(names)}",
                "short": f"{label}: {', '.join(names)}", "rooms": rooms_served, "enclosures": [e["id"] for e in encs],
                "points": [p["id"] for p in points], "conductorSize": size,
                "conductorBasis": "CPWD 3.12.2 minimum (final size by designer)" if kind != "geyser" else
                                  "CPWD 3.12.2 minimum 4 mm²; above 1 kW sized by calculation (CPWD 3.10.4)",
                "designW": sum(DESIGN_W.get(p["kind"], 0) for p in points),
                "lightPoints": sum(1 for p in points if p["kind"] in LIGHTING_KINDS)}
        d.circuits.append(circ)
        for e in encs:
            e["circuitIds"].append(cid)
        for p in points:
            p["circuitId"] = cid
    return d.circuits


def _power_ok(n6, n16):
    return (n16 == 0 and n6 <= 3) or (n6 == 0 and n16 <= 2) or (n16 <= 1 and n6 <= 2)


def _chain(d, encs, start):
    left = list(encs)
    out = []
    cur = start["mount"]["face"]
    while left:
        nxt = min(left, key=lambda e: abs(e["mount"]["face"][0] - cur[0]) + abs(e["mount"]["face"][1] - cur[1]))
        out.append(nxt)
        left.remove(nxt)
        cur = nxt["mount"]["face"]
    return out


# ---------------------------------------------------------------------------
# Distribution-board interiors (devices + terminals); positions in enclosure-local metres
# ---------------------------------------------------------------------------

def build_boards(d):
    main = d.enc(d.distribution["mainDB"])
    lwb = d.enc(d.distribution["mainLWB"])
    sub = d.enc(d.distribution["subDB"])
    slwb = d.enc(d.distribution["subLWB"])
    meter = d.enc(d.distribution["meter"])
    W, Hh, D = TPN
    mod = .018
    # ---- meter (sealed)
    mt = d.device(meter, "meter", "Three-phase whole-current energy meter (DISCOM, sealed)", operable=False,
                  standard="Smart meter for new connections (CEA metering regulations)", sealed=True)
    meter["meterDevice"] = mt["id"]
    mt["terminals"] = {}
    tb_y = -METER[1] / 2 + .02
    for i, (lbl, role) in enumerate([("R in", "L1"), ("R out", "L1"), ("Y in", "L2"), ("Y out", "L2"),
                                      ("B in", "L3"), ("B out", "L3"), ("N in", "N"), ("N out", "N")]):
        mt["terminals"][lbl] = d.terminal(meter, f"Meter terminal {lbl}", role, (-.07 + i * .02, tb_y, .07))
    # ---- main DB: incomer row (4P MCB + 4P RCCB), outgoing row (24 SP ways on a 3-phase comb busbar)
    top_y, out_y = .085, -.065
    x_in = -W / 2 + .06
    q1 = d.device(main, "mcb4p", "Incoming 4-pole MCB (main switch)", poles=4, modules=4, operable=True, defaultOn=True,
                  overcurrent=True, rating=None, standard="IS/IEC 60898-1", row=0, x=r4(x_in + 2 * mod), y=top_y)
    f1 = d.device(main, "rccb4p", "4-pole RCCB 30 mA, Type A", poles=4, modules=4, operable=True, defaultOn=True,
                  residual=True, rating={"sensitivity": "30 mA (CEA Reg. 44; CPWD G.3.1)", "current": None},
                  standard="IS 12640-1", row=0, x=r4(x_in + 6 * mod), y=top_y)
    for dev, x0 in ((q1, x_in), (f1, x_in + 4 * mod)):
        dev["terminals"] = {}
        for i, pole in enumerate(("N", "L1", "L2", "L3") if dev is f1 else ("L1", "L2", "L3", "N")):
            px = x0 + (i + .5) * mod
            dev["terminals"][pole + " in"] = d.terminal(main, f"{dev['label'].split(' (')[0]} {pole} in", pole, (px, top_y + .034, -.045), dev)
            dev["terminals"][pole + " out"] = d.terminal(main, f"{dev['label'].split(' (')[0]} {pole} out", pole, (px, top_y - .034, -.045), dev)
    nbar = d.device(main, "neutral-bar", "Neutral bar (after RCCB)", operable=False, x=r4(W / 2 - .07), y=r4(top_y + .02))
    ebar = d.device(main, "earth-bar", "Earth bar · main earthing terminal", operable=False, x=r4(W / 2 - .07), y=r4(-Hh / 2 + .045))
    comb = d.device(main, "busbar", "3-phase comb busbar (L1-L2-L3 repeating)", operable=False, x=0, y=r4(out_y + .034))
    main["devices"] = {"incomer": q1["id"], "rccb": f1["id"], "neutralBar": nbar["id"], "earthBar": ebar["id"], "busbar": comb["id"]}
    nbar["terminals"] = {}
    ebar["terminals"] = {}
    main_ways = []
    # ---- sub DB: incomer 2P isolator + 8 SP ways on a single-phase comb busbar
    sw_, sh_, sd_ = SPN
    q2 = d.device(sub, "isolator2p", "Incoming 2-pole isolator (first-floor main switch)", poles=2, modules=2, operable=True,
                  defaultOn=True, rating=None, standard="IS/IEC 60947-3", row=0, x=r4(-sw_ / 2 + .05 + mod), y=0)
    q2["terminals"] = {}
    for i, pole in enumerate(("L", "N")):
        px = -sw_ / 2 + .05 + (i + .5) * mod
        q2["terminals"][pole + " in"] = d.terminal(sub, f"Isolator {pole} in", pole, (px, .034, -.046), q2)
        q2["terminals"][pole + " out"] = d.terminal(sub, f"Isolator {pole} out", pole, (px, -.034, -.046), q2)
    snbar = d.device(sub, "neutral-bar", "Neutral bar", operable=False, x=r4(-sw_ / 2 + .03), y=r4(-.085))
    sebar = d.device(sub, "earth-bar", "Earth bar", operable=False, x=r4(sw_ / 2 - .03), y=r4(-.085))
    scomb = d.device(sub, "busbar", "Single-phase comb busbar", operable=False, x=0, y=r4(.034))
    sub["devices"] = {"incomer": q2["id"], "neutralBar": snbar["id"], "earthBar": sebar["id"], "busbar": scomb["id"]}
    snbar["terminals"], sebar["terminals"] = {}, {}
    # ---- outgoing MCBs, assigned to comb-busbar ways of the right phase
    used = set()
    sub_ways = []
    submain = {"id": "SUB", "kind": "submain", "floor": 0, "phase": "B", "label": "Submain · main DB → first-floor sub-DB",
               "short": "Submain to the first-floor sub-DB", "rooms": [], "enclosures": [sub["id"]], "points": [],
               "conductorSize": None, "conductorBasis": "Submain size by designer (load, voltage drop, fault level)"}
    feeds = [c for c in d.circuits if c["floor"] == 0] + [submain]
    for c in feeds:
        slot = next(i for i in range(24) if i not in used and PHASES[i % 3] == c["phase"])
        used.add(slot)
        x = -W / 2 + .04 + (slot + .5) * mod
        mcb = d.device(main, "mcb", f"{c['id']} MCB", poles=1, modules=1, operable=True, defaultOn=True, overcurrent=True,
                       rating=None, standard="IS/IEC 60898-1", row=1, slot=slot, phase=c["phase"], circuitId=c["id"],
                       x=r4(x), y=out_y)
        mcb["terminals"] = {"in": d.terminal(main, f"{c['id']} MCB in (busbar)", "L", (x, out_y + .034, -.045), mcb),
                            "out": d.terminal(main, f"{c['id']} MCB out", "L", (x, out_y - .034, -.045), mcb)}
        c["mcb"] = mcb["id"]
        main_ways.append(mcb["id"])
    d.circuits.append(submain)
    for i, c in enumerate([c for c in d.circuits if c["floor"] == 1]):
        x = -sw_ / 2 + .05 + (2 + i + .5) * mod
        mcb = d.device(sub, "mcb", f"{c['id']} MCB", poles=1, modules=1, operable=True, defaultOn=True, overcurrent=True,
                       rating=None, standard="IS/IEC 60898-1", row=0, slot=2 + i, phase=c["phase"], circuitId=c["id"],
                       x=r4(x), y=0)
        mcb["terminals"] = {"in": d.terminal(sub, f"{c['id']} MCB in (busbar)", "L", (x, .034, -.046), mcb),
                            "out": d.terminal(sub, f"{c['id']} MCB out", "L", (x, -.034, -.046), mcb)}
        c["mcb"] = mcb["id"]
        sub_ways.append(mcb["id"])
    # ---- protective chains (what must be closed for each circuit to be supplied)
    for c in d.circuits:
        if c["floor"] == 0 or c["id"] == "SUB":
            c["chain"] = [q1["id"], f1["id"], c["mcb"]]
            c["db"] = main["id"]
        else:
            c["chain"] = [q1["id"], f1["id"], submain["mcb"], q2["id"], c["mcb"]]
            c["db"] = sub["id"]
    # ---- outgoing terminal blocks in the loose-wire boxes (CPWD 3.18.2)
    for box, circs, width in ((lwb, [c for c in d.circuits if c["floor"] == 0 or c["id"] == "SUB"], W),
                              (slwb, [c for c in d.circuits if c["floor"] == 1 and c["id"] != "SUB"], sw_)):
        n = len(circs)
        pitch = min(.03, (width - .06) / max(1, n))
        box["blocks"] = {}
        for i, c in enumerate(circs):
            x = -width / 2 + .03 + (i + .5) * pitch
            blk = {"P": d.terminal(box, f"{c['id']} phase block", "P", (x - .008, -.02, -.045)),
                   "N": d.terminal(box, f"{c['id']} neutral block", "N", (x, -.02, -.045)),
                   "E": d.terminal(box, f"{c['id']} earth block", "E", (x + .008, -.02, -.045))}
            box["blocks"][c["id"]] = blk
            c["blocks"] = blk
            c["lwb"] = box["id"]
    d.board = {"main": {"incomer": q1, "rccb": f1, "nbar": nbar, "ebar": ebar, "comb": comb},
               "sub": {"incomer": q2, "nbar": snbar, "ebar": sebar, "comb": scomb}, "meter": mt}
    return d.board


# ---------------------------------------------------------------------------
# Conduit routing
# ---------------------------------------------------------------------------

class Router:
    def __init__(self, d):
        self.d = d
        self.ports = defaultdict(list)     # enclosure id -> allocated conduit offsets (top)

    def slab_z(self, floor):
        return self.d.house.soffit(floor) + SLAB_CONDUIT

    def wall_port(self, enc, which="top", index=None):
        """Point where a conduit enters an enclosure, and its chase line in plan."""
        m = enc["mount"]
        nx, ny = m["normal"]
        rx, ry = -ny, nx
        w = enc["size"]["boxW"]
        used = self.ports[(enc["id"], which)]
        k = len(used)
        spacing = .034
        slots = max(1, int((w - .03) // spacing))
        order = [0, 1, -1, 2, -2, 3, -3, 4, -4, 5, -5, 6, -6]
        off = order[k % len(order)] * spacing
        off = max(-(w / 2 - .02), min(w / 2 - .02, off))
        used.append(off)
        depth = min(enc["size"]["depth"] - .012, max(CHASE_DEPTH, m.get("finish", 0) + .022))
        if enc["kind"] in ("main-db", "sub-db", "loose-wire-box"):
            depth = enc["size"]["depth"] / 2
        fx, fy, fz = m["face"]
        px, py = fx + rx * off - nx * depth, fy + ry * off - ny * depth
        hz = enc["size"]["boxH"] / 2
        z = fz + (hz if which == "top" else -hz)
        return {"xy": (px, py), "z": z, "enc": enc["id"], "floor": enc["floor"], "normal": (nx, ny), "depth": depth,
                "offset": off}

    def slab_path(self, floor, a, b, rooms=()):
        """Straight run through the slab when it clears every opening (conduits are laid straight
        between boxes with long-radius bends, CPWD 4.4.3(c)); otherwise an orthogonal route around
        the openings, string-pulled to remove needless corners."""
        router = self.d.router(floor)
        if _clear(router, a, b):
            return [tuple(a), tuple(b)]
        path = router.route(a, b, rooms=rooms)
        out = [path[0]]
        i = 0
        while i < len(path) - 1:
            j = len(path) - 1
            while j > i + 1 and not _clear(router, path[i], path[j]):
                j -= 1
            out.append(path[j])
            i = j
        return out

    def run(self, kind, function, a, b, *, floor=None, rooms=(), circuit_ids=(), label=""):
        """Conduit(s) from port/box `a` to port/box `b` through the slab above `floor`. A run with more
        than the equivalent of four quarter-bends is split at a draw-in box (CPWD 5.4.1(ii))."""
        floor = a["floor"] if floor is None else floor
        zs = self.slab_z(floor)
        pts = []
        if a.get("box"):
            pts.append((a["xy"][0], a["xy"][1], zs))
        else:
            pts.append((a["xy"][0], a["xy"][1], a["z"]))
            pts.append((a["xy"][0], a["xy"][1], zs))
        path = self.slab_path(floor, (pts[-1][0], pts[-1][1]), b["xy"], rooms)
        for x, y in path[1:]:
            pts.append((x, y, zs))
        if not b.get("box"):
            pts.append((b["xy"][0], b["xy"][1], b["z"]))
        pts = _dedupe(pts)
        pieces = _split_bends(pts)
        ends = [a.get("enc") or a.get("boxId")]
        for k in range(len(pieces) - 1):
            x, y, _ = pieces[k][-1]
            ends.append(self.draw_box(floor, x, y))
        ends.append(b.get("enc") or b.get("boxId"))
        made = []
        for k, piece in enumerate(pieces):
            cid = self.d.nid("C")
            conduit = {"id": cid, "kind": kind, "function": function, "floor": floor, "planFloor": floor,
                       "points": [p3(p) for p in piece], "from": ends[k], "to": ends[k + 1], "circuitIds": list(circuit_ids),
                       "carries": [], "label": label + (f" (part {k + 1} of {len(pieces)})" if len(pieces) > 1 else ""),
                       "quarterBends": round(bends(piece), 2)}
            self.d.conduits.append(conduit)
            for ref in (ends[k], ends[k + 1]):
                enc = next((e for e in self.d.enclosures if e["id"] == ref), None)
                if enc is not None:
                    enc["conduitIds"].append(cid)
                box = next((x for x in self.d.boxes if x["id"] == ref), None)
                if box is not None:
                    box.setdefault("conduitIds", []).append(cid)
            made.append(conduit)
        return {"id": made[0]["id"], "ids": [c["id"] for c in made], "conduits": made}

    def draw_box(self, floor, x, y):
        d = self.d
        bid = d.nid("JB")
        room = d.house.room_at(x, y, floor)
        d.boxes.append({"id": bid, "kind": "draw-box", "label": "Draw-in box (inspection box in the slab)", "floor": floor,
                        "roomId": room if room in d.room_by_id else None,
                        "position": [r4(x), r4(y), r4(d.house.soffit(floor))], "size": [JB_D, JB_D, JB_DEPTH]})
        return bid

    def ceiling_box(self, point, kind):
        """Slab junction/outlet box above a ceiling point (CPWD 4.4.3(d): >= 65 mm deep)."""
        d = self.d
        bid = d.nid("JB")
        z0 = d.house.soffit(point["floor"])
        box = {"id": bid, "kind": kind, "label": {"light-box": "Light point box (in slab)", "fan-box": "Fan box with hook (in slab)",
                                                  "cove-box": "Cove driver box (in slab, above cove pocket)", "draw-box": "Draw-in box"}[kind],
               "floor": point["floor"], "roomId": point["roomId"], "position": [point["position"][0], point["position"][1], r4(z0)],
               "size": [JB_D, JB_D, JB_DEPTH], "pointId": point["id"]}
        d.boxes.append(box)
        point["boxId"] = bid
        return {"xy": (point["position"][0], point["position"][1]), "box": True, "boxId": bid, "floor": point["floor"],
                "z": z0 + SLAB_CONDUIT}

    def wall_box(self, point, kind, size=(.0765, .0765)):
        """Wall outlet box for a wall-mounted point (mirror light, under-cabinet light, exhaust)."""
        d = self.d
        h = d.house
        x, y, z = point["position"]
        wall = h.walls[point["wallId"]] if point.get("wallId") else _nearest_wall(h, (x, y), point["floor"])
        side = point.get("side") or (1 if wall.offset((x, y)) >= 0 else -1)
        along = point.get("along") or wall.along((x, y))
        if point["kind"] == "exhaust":
            along = along + .30          # beside the exhaust opening (CPWD 3.16.2)
        mount = make_mount(h, wall, side, point["roomId"], along, size[0], size[1], z, BOX_DEPTH).as_dict()
        bid = d.nid("WB")
        box = {"id": bid, "kind": "wall-box", "label": {"mirror-light": "Mirror-light outlet box", "undercabinet": "Under-cabinet light outlet box",
                                                        "exhaust": "Exhaust-fan point (cord outlet)"}.get(point["kind"], "Outlet box"),
               "floor": point["floor"], "roomId": point["roomId"], "mount": mount, "size": [size[0], size[1], BOX_DEPTH],
               "pointId": point["id"], "position": mount["face"]}
        d.boxes.append(box)
        point["boxId"] = bid
        nx, ny = mount["normal"]
        fx, fy, fz = mount["face"]
        return {"xy": (fx - nx * CHASE_DEPTH, fy - ny * CHASE_DEPTH), "z": fz + size[1] / 2, "boxId": bid,
                "floor": point["floor"], "wall": True}


def _clear(router, a, b, step=.05):
    n = max(1, int(math.dist(a, b) / step))
    for k in range(n + 1):
        t = k / n
        if not router._solid(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t):
            return False
    return True


def bends(pts):
    """Equivalent number of quarter-bends along a conduit centre-line."""
    total = 0.
    for i in range(1, len(pts) - 1):
        u = [pts[i][k] - pts[i - 1][k] for k in range(3)]
        v = [pts[i + 1][k] - pts[i][k] for k in range(3)]
        lu, lv = math.sqrt(sum(x * x for x in u)), math.sqrt(sum(x * x for x in v))
        if lu < 1e-6 or lv < 1e-6:
            continue
        ang = math.degrees(math.acos(max(-1., min(1., sum(u[k] * v[k] for k in range(3)) / (lu * lv)))))
        if ang > 10:
            total += ang / 90
    return total


def _split_bends(pts, limit=4.0):
    if bends(pts) <= limit + 1e-6:
        return [pts]
    # split at a horizontal (slab) vertex so each part stays within the limit
    best = None
    for k in range(2, len(pts) - 2):
        if abs(pts[k][2] - pts[k - 1][2]) > 1e-6 or abs(pts[k][2] - pts[k + 1][2]) > 1e-6:
            continue
        a, b = pts[:k + 1], pts[k:]
        score = max(bends(a), bends(b))
        if best is None or score < best[0]:
            best = (score, k)
    if best is None:
        return [pts]
    k = best[1]
    return _split_bends(pts[:k + 1], limit) + _split_bends(pts[k:], limit)


def _nearest_wall(h, p, floor):
    return min((w for w in h.walls.values() if w.floor == floor),
               key=lambda w: abs(abs(w.offset(p)) - w.half) + (0 if -.05 <= w.along(p) <= w.length + .05 else 9))


def _dedupe(pts):
    out = [pts[0]]
    for p in pts[1:]:
        if math.dist(p, out[-1]) > 1e-4:
            out.append(p)
    return out


def conduit_size(counts):
    """Smallest conduit (20/25 mm) that takes the conductors, using CPWD Table 4.1 (bends present)."""
    for size in (20, 25):
        fill = FILL_BENT[size]
        need = sum(n / fill[mm] for mm, n in counts.items())
        if need <= 1 + 1e-9:
            return size
    return None


# ---------------------------------------------------------------------------
# Netlist
# ---------------------------------------------------------------------------

class Net:
    def __init__(self, d):
        self.d = d

    def conductor(self, role, circuit, size, a, b, conduits=(), kind="circuit", serves=(), colour=None, label="", **kw):
        k = {"id": self.d.nid("W"), "role": role, "circuitId": circuit, "size": size, "from": a, "to": b,
             "conduits": list(conduits), "kind": kind, "serves": list(dict.fromkeys(serves)),
             "colour": colour or _colour_for(role), "label": label, **kw}
        self.d.conductors.append(k)
        for cid in conduits:
            c = next(c for c in self.d.conduits if c["id"] == cid)
            c["carries"].append(k["id"])
            if circuit and circuit not in c["circuitIds"]:
                c["circuitIds"].append(circuit)
        return k


def _colour_for(role):
    if role in ("L1",):
        return "R"
    if role in ("L2",):
        return "Y"
    if role in ("L3",):
        return "B"
    if role in ("N",):
        return "N"
    if role in ("PE",):
        return "PE"
    return "LIVE"            # single-phase live, switched and regulated conductors (CPWD 3.5.5)


def wire_everything(d):
    r = Router(d)
    net = Net(d)
    dist = d.distribution
    main, lwb, sub, slwb, meter = (d.enc(dist[k]) for k in ("mainDB", "mainLWB", "subDB", "subLWB", "meter"))
    B = d.board
    q1, f1, nbar, ebar = B["main"]["incomer"], B["main"]["rccb"], B["main"]["nbar"], B["main"]["ebar"]
    q2, snbar, sebar = B["sub"]["incomer"], B["sub"]["nbar"], B["sub"]["ebar"]
    mt = B["meter"]
    all_circuits = [c for c in d.circuits]
    everything = [p["id"] for p in d.points]
    upstairs = [p["id"] for p in d.points if p["floor"] == 1]
    # ---------------- service: street -> meter -> main DB ----------------
    mx, my, mz = meter["mount"]["face"]
    nx, ny = meter["mount"]["normal"]                   # out of the external face
    rx, ry = -ny, nx
    ground = dist["ground"]
    trench = ground - .75                                # assumed burial depth of the DISCOM cable
    m_bottom = mz - METER_BOX[1] / 2
    gland = (mx + nx * .10, my + ny * .10)               # cable gland under the meter box
    db_face = main["mount"]["face"]
    dnx, dny = main["mount"]["normal"]
    chase_in = (db_face[0] - dnx * main["size"]["depth"] / 2, db_face[1] - dny * main["size"]["depth"] / 2)
    db_bottom = db_face[2] - main["size"]["h"] / 2
    ext_chase = (mx - nx * .03, my - ny * .03)          # just inside the external face
    entry_z = m_bottom + .07                             # back-entry knockout near the bottom of the meter box
    svc_pts = [(mx + nx * 2.2, my + ny * 2.2, trench), (mx + nx * .4, my + ny * .4, trench), (ext_chase[0], ext_chase[1], trench),
               (ext_chase[0], ext_chase[1], entry_z), (mx + nx * .03, my + ny * .03, entry_z)]
    svc = _raw_conduit(d, "service", "service", svc_pts, None, meter["id"], 0,
                       "Underground service cable (DISCOM), rising in the external wall into the back of the meter box",
                       diameter=50, material="GI/HDPE pipe (DISCOM)")
    off = rx * .07, ry * .07
    feed_pts = [(mx + nx * .03 + off[0], my + ny * .03 + off[1], entry_z), (ext_chase[0] + off[0], ext_chase[1] + off[1], entry_z),
                (ext_chase[0] + off[0], ext_chase[1] + off[1], entry_z - .10),
                (chase_in[0] + off[0], chase_in[1] + off[1], entry_z - .10),
                (chase_in[0] + off[0], chase_in[1] + off[1], db_bottom)]
    feed = _raw_conduit(d, "service", "service", feed_pts, meter["id"], main["id"], 0,
                        "Meter → main DB, back entry and sleeved through the external wall (CPWD 3.7.1)", diameter=32)
    for role in ("L1", "L2", "L3", "N"):
        lbl = {"L1": "R", "L2": "Y", "L3": "B", "N": "N"}[role]
        net.conductor(role, None, None, "DISCOM network", mt["terminals"][f"{lbl} in"], [svc["id"]], kind="service",
                      serves=everything, label=f"Service core {lbl} (DISCOM cable)", chain=[])
        net.conductor(role, None, None, mt["terminals"][f"{lbl} out"], q1["terminals"][f"{role} in"], [feed["id"]],
                      kind="meter-tail", serves=everything, label=f"Meter → main switch, {lbl}", chain=[])
    # incomer -> RCCB -> busbar / neutral bar
    for pole in ("L1", "L2", "L3", "N"):
        net.conductor(pole, None, None, q1["terminals"][f"{pole} out"], f1["terminals"][f"{pole} in"], [], kind="internal",
                      serves=everything, label=f"Incomer → RCCB link, {pole}", chain=[q1["id"]])
    nbar["terminals"]["in"] = d.terminal(main, "Neutral bar (from RCCB)", "N", (nbar["x"] - .05, nbar["y"], -.05), nbar)
    net.conductor("N", None, None, f1["terminals"]["N out"], nbar["terminals"]["in"], [], kind="internal", serves=everything,
                  label="RCCB → neutral bar", chain=[q1["id"], f1["id"]])
    comb = B["main"]["comb"]
    comb["terminals"] = {}
    for pole in ("L1", "L2", "L3"):
        comb["terminals"][pole] = d.terminal(main, f"Comb busbar feed {pole}", pole, (-TPN[0] / 2 + .03, -.065 + .034, -.04), comb)
        net.conductor(pole, None, None, f1["terminals"][f"{pole} out"], comb["terminals"][pole], [], kind="internal",
                      serves=everything, label=f"RCCB → busbar feed, {pole}", chain=[q1["id"], f1["id"]])
    # ---------------- earthing: two electrodes -> main earthing terminal ----------------
    ebar["terminals"]["met"] = d.terminal(main, "Main earthing terminal", "E", (ebar["x"] - .04, ebar["y"], -.05), ebar)
    for i, pid in enumerate(dist["pits"]):
        pit = next(b for b in d.boxes if b["id"] == pid)
        px, py, pz = pit["position"]
        o = (-.10 + .2 * i)
        wall_x, wall_y = mx + nx * .30 + rx * o, my + ny * .30 + ry * o
        in_x, in_y = chase_in[0] + rx * o, chase_in[1] + ry * o
        bury = ground - .5                                # CPWD F.8.9: earthing conductor at least 0.5 m deep
        e_pts = [(px, py, pz - .25), (px, py, bury), (wall_x, wall_y, bury), (in_x, in_y, bury), (in_x, in_y, db_bottom)]
        e = _raw_conduit(d, "earthing", "earthing", e_pts, pid, main["id"], 0,
                         f"Earthing conductor {i + 1}: electrode → main earthing terminal (buried, then in the wall)", diameter=20)
        pit_t = d.terminal_box(pit, "Electrode clamp", "E", (0, 0, -.25))
        net.conductor("PE", None, None, pit_t, ebar["terminals"]["met"], [e["id"]], kind="earthing", serves=[],
                      label=f"Earthing conductor {i + 1} (two distinct connections: CEA Reg. 43)")
    # ---------------- outgoing pre-wiring (MCB -> LWB blocks; bars -> blocks) ----------------
    def prewire(c, dbm, bar_n, bar_e, comb_dev, chain_upto):
        mcb = next(x for x in d.devices if x["id"] == c["mcb"])
        blocks = c["blocks"]
        net.conductor(_phase_role(c["phase"]), c["id"], c["conductorSize"] or 6.0, comb_dev["terminals"].get(_phase_role(c["phase"])) or comb_dev["terminals"]["L"],
                      mcb["terminals"]["in"], [], kind="busbar", serves=c["points"] if c["id"] != "SUB" else upstairs,
                      label=f"Busbar tooth → {c['id']} MCB", chain=chain_upto)
        via = [d.couplers[dbm]]
        net.conductor("L", c["id"], c["conductorSize"] or 6.0, mcb["terminals"]["out"], blocks["P"], via, kind="prewire",
                      serves=c["points"] if c["id"] != "SUB" else upstairs, label=f"{c['id']} MCB → phase block", chain=c["chain"])
        bar_n["terminals"][c["id"]] = d.terminal(d.enc(dbm), f"Neutral bar · {c['id']}", "N", (bar_n["x"] + .01 * (len(bar_n["terminals"]) - 1), bar_n["y"], -.05), bar_n)
        bar_e["terminals"][c["id"]] = d.terminal(d.enc(dbm), f"Earth bar · {c['id']}", "E", (bar_e["x"] + .01 * (len(bar_e["terminals"]) - 1), bar_e["y"], -.05), bar_e)
        net.conductor("N", c["id"], c["conductorSize"] or 6.0, bar_n["terminals"][c["id"]], blocks["N"], via, kind="prewire",
                      serves=c["points"] if c["id"] != "SUB" else upstairs, label=f"Neutral bar → {c['id']} neutral block")
        net.conductor("PE", c["id"], c["conductorSize"] or 6.0, bar_e["terminals"][c["id"]], blocks["E"], via, kind="prewire",
                      serves=[], label=f"Earth bar → {c['id']} earth block")
    couplers = {}
    for db_enc, box in ((main, lwb), (sub, slwb)):
        f = db_enc["mount"]["face"]
        nx2, ny2 = db_enc["mount"]["normal"]
        dd = db_enc["size"]["depth"] / 2
        z0 = f[2] + db_enc["size"]["h"] / 2 - .03
        couplers[db_enc["id"]] = _raw_conduit(d, "coupler", "prewire",
                                              [(f[0] - nx2 * dd, f[1] - ny2 * dd, z0), (f[0] - nx2 * dd, f[1] - ny2 * dd, z0 + .06)],
                                              db_enc["id"], box["id"], db_enc["floor"],
                                              "Bushed opening between the DB and its loose-wire box (factory pre-wiring)", diameter=40,
                                              material="gland/bush")
    d.couplers = {k: v["id"] for k, v in couplers.items()}
    for c in [c for c in all_circuits if c["floor"] == 0 or c["id"] == "SUB"]:
        prewire(c, main["id"], nbar, ebar, comb, [q1["id"], f1["id"]])
    # ---------------- submain riser: main LWB -> first-floor sub-DB ----------------
    subc = next(c for c in all_circuits if c["id"] == "SUB")
    a = r.wall_port(lwb, "top")
    b = r.wall_port(sub, "bottom")
    zs0 = r.slab_z(0)
    path = r.slab_path(0, a["xy"], b["xy"])
    # (riser bends counted by the validator; straight slab run keeps it within four quarter-bends)
    pts = [(a["xy"][0], a["xy"][1], a["z"]), (a["xy"][0], a["xy"][1], zs0)] + [(x, y, zs0) for x, y in path[1:]] + \
          [(b["xy"][0], b["xy"][1], b["z"])]
    riser = _raw_conduit(d, "riser", "submain", pts, lwb["id"], sub["id"], 0,
                         "Submain riser: slab run, then sleeved rise through the first-floor slab (CPWD 3.7)", diameter=32)
    riser["circuitIds"].append("SUB")
    q2_in = q2["terminals"]
    net.conductor("L", "SUB", None, subc["blocks"]["P"], q2_in["L in"], [riser["id"]], kind="submain", serves=upstairs,
                  label="Submain phase (B) → first-floor isolator", chain=subc["chain"])
    net.conductor("N", "SUB", None, subc["blocks"]["N"], q2_in["N in"], [riser["id"]], kind="submain", serves=upstairs,
                  label="Submain neutral → first-floor isolator")
    sebar["terminals"]["in"] = d.terminal(sub, "Earth bar (from submain PE)", "E", (sebar["x"], sebar["y"] - .02, -.05), sebar)
    net.conductor("PE", "SUB", None, subc["blocks"]["E"], sebar["terminals"]["in"], [riser["id"]], kind="submain",
                  serves=[], label="Submain protective conductor → first-floor earth bar")
    snbar["terminals"]["in"] = d.terminal(sub, "Neutral bar (from isolator)", "N", (snbar["x"], snbar["y"] + .02, -.05), snbar)
    net.conductor("N", "SUB", None, q2_in["N out"], snbar["terminals"]["in"], [], kind="internal", serves=upstairs,
                  label="Isolator → neutral bar", chain=subc["chain"] + [q2["id"]])
    scomb = B["sub"]["comb"]
    scomb["terminals"] = {"L": d.terminal(sub, "Comb busbar feed", "L", (-SPN[0] / 2 + .05 + 2 * .018, .034, -.04), scomb)}
    net.conductor("L", "SUB", None, q2_in["L out"], scomb["terminals"]["L"], [], kind="internal", serves=upstairs,
                  label="Isolator → busbar", chain=subc["chain"] + [q2["id"]])
    for c in [c for c in all_circuits if c["floor"] == 1 and c["id"] != "SUB"]:
        prewire(c, sub["id"], snbar, sebar, scomb, subc["chain"] + [q2["id"]])
    # ---------------- final circuits ----------------
    for c in [c for c in all_circuits if c["id"] != "SUB"]:
        _wire_circuit(d, r, net, c)
    d.router_state = r
    return r


def _phase_role(phase):
    return {"R": "L1", "Y": "L2", "B": "L3"}[phase]


def _port_xyz(port):
    return (port["xy"][0], port["xy"][1], port["z"])


def _through_wall(d, outside_enc, inside_enc, z, start_offset=0.):
    """Sleeved crossing from the meter face to the DB chase inside the same wall."""
    mo = outside_enc["mount"]
    mi = inside_enc["mount"]
    nxo, nyo = mo["normal"]
    nxi, nyi = mi["normal"]
    rx, ry = -nyi, nxi
    xo, yo = mo["face"][0] - nxo * .03, mo["face"][1] - nyo * .03
    xi, yi = mi["face"][0] - nxi * (inside_enc["size"]["depth"] / 2), mi["face"][1] - nyi * (inside_enc["size"]["depth"] / 2)
    return [(xo + rx * start_offset, yo + ry * start_offset, z), (xi + rx * start_offset, yi + ry * start_offset, z)]


def _raw_conduit(d, kind, function, pts, a, b, floor, label, diameter=25, material="rigid PVC (IS 9537-3)"):
    cid = d.nid("C")
    conduit = {"id": cid, "kind": kind, "function": function, "floor": floor, "planFloor": floor,
               "points": [p3(p) for p in _dedupe(pts)], "from": a, "to": b, "circuitIds": [], "carries": [],
               "label": label, "diameter": diameter, "material": material}
    d.conduits.append(conduit)
    for ref in (a, b):
        enc = next((e for e in d.enclosures if e["id"] == ref), None)
        if enc is not None:
            enc["conduitIds"].append(cid)
        box = next((x for x in d.boxes if x["id"] == ref), None)
        if box is not None:
            box.setdefault("conduitIds", []).append(cid)
    return conduit


def _wire_circuit(d, r, net, c):
    encs = [d.enc(e) for e in c["enclosures"]]
    lwb = d.enc(c["lwb"])
    size = c["conductorSize"]
    floor = c["floor"]
    blocks = c["blocks"]
    prev = {"P": blocks["P"], "N": blocks["N"], "E": blocks["E"], "enc": lwb}
    for i, enc in enumerate(encs):
        a = r.wall_port(prev["enc"], "top")
        b = r.wall_port(enc, "top")
        downstream = [p for e in encs[i:] for p in c["points"] if _point_in(d, p, e, c)]
        run = r.run("circuit", "power" if c["kind"] != "lighting" else "lighting", a, b, floor=floor,
                    rooms=set(c["rooms"]), circuit_ids=[c["id"]],
                    label=f"{c['id']} circuit wiring: {prev['enc']['label'].split(' · ')[0]} → {enc['label']}")
        con = enc.get("connectors")
        if con is None:
            raise ValueError(f"Enclosure {enc['id']} has no connectors")
        if c["kind"] == "geyser" and i == 1:
            # MCB box -> geyser socket: the MCB output is the controlled live
            mcb_dev = next(x for x in d.devices if x["enclosureId"] == prev["enc"]["id"] and x["kind"] == "local-mcb")
            sock = next(x for x in d.devices if x["enclosureId"] == enc["id"] and x["kind"] == "socket16")
            sw = next(s for s in d.switches if s["deviceId"] == mcb_dev["id"])
            net.conductor("SW", c["id"], size, mcb_dev["terminals"]["out"], sock["terminals"]["L"], run["ids"], kind="circuit",
                          serves=downstream, controls=[sw["id"]], label=f"{c['id']} switched live (MCB → water-heater socket)", chain=c["chain"])
            net.conductor("N", c["id"], size, prev["N"], sock["terminals"]["N"], run["ids"], serves=downstream,
                          label=f"{c['id']} neutral → water-heater socket")
            net.conductor("PE", c["id"], size, prev["E"], sock["terminals"]["E"], run["ids"], serves=[],
                          label=f"{c['id']} protective conductor → water-heater socket")
            net.conductor("PE", c["id"], size, sock["terminals"]["E"], con["stud"], [], kind="internal", serves=[],
                          label="Socket earth → box earth stud")
            _size_conduit(d, run)
            continue
        net.conductor("L", c["id"], size, prev["P"], con["P"], run["ids"], serves=downstream,
                      label=f"{c['id']} phase → {enc['label']}", chain=c["chain"])
        net.conductor("N", c["id"], size, prev["N"], con["N"], run["ids"], serves=downstream,
                      label=f"{c['id']} neutral → {enc['label']}")
        net.conductor("PE", c["id"], size, prev["E"], con["E"], run["ids"], serves=[],
                      label=f"{c['id']} protective conductor → {enc['label']}")
        net.conductor("PE", c["id"], size, con["E"], con["stud"], [], kind="internal", serves=[],
                      label="Earth connector → box earth stud (CPWD 4.3.3)")
        _size_conduit(d, run)
        _board_internals(d, net, c, enc)
        if enc["kind"] == "switchboard":
            _point_wiring(d, r, net, c, enc)
        prev = {"P": con["P"], "N": con["N"], "E": con["E"], "enc": enc}


def _point_in(d, pid, enc, c):
    p = next(x for x in d.points if x["id"] == pid)
    if enc["kind"] == "switchboard":
        return p["roomId"] == enc["roomId"] and p["kind"] in LIGHTING_KINDS
    return p.get("enclosureId") == enc["id"] or (enc["kind"] == "geyser-mcb" and p.get("enclosureId") == enc.get("feeds"))


def _board_internals(d, net, c, enc):
    """Phase loop to switch inputs; switched sockets; regulator in series with the fan switch."""
    con = enc["connectors"]
    devs = [x for x in d.devices if x["enclosureId"] == enc["id"]]
    prev = con["P"]
    for dev in [x for x in devs if x["kind"] in ("switch", "switch16", "local-mcb")]:
        sw = next(s for s in d.switches if s["deviceId"] == dev["id"])
        net.conductor("L", c["id"], c["conductorSize"], prev, dev["terminals"]["in"], [], kind="internal",
                      serves=_switch_points(d, sw), label=("Phase connector → " if prev == con["P"] else "Phase loop → ") + dev["label"],
                      chain=c["chain"])
        prev = dev["terminals"]["in"]
    for dev in [x for x in devs if x["kind"] in ("socket6", "socket16")]:
        sw_dev = next(x for x in devs if x["kind"] in ("switch", "switch16") and dev["pointId"] in
                      next(s for s in d.switches if s["deviceId"] == x["id"])["points"])
        sw = next(s for s in d.switches if s["deviceId"] == sw_dev["id"])
        net.conductor("SW", c["id"], c["conductorSize"], sw_dev["terminals"]["out"], dev["terminals"]["L"], [], kind="internal",
                      serves=[dev["pointId"]], controls=[sw["id"]], label=f"Switch → socket live ({dev['label']})", chain=c["chain"])
        net.conductor("N", c["id"], c["conductorSize"], con["N"], dev["terminals"]["N"], [], kind="internal",
                      serves=[dev["pointId"]], label="Neutral connector → socket N")
        net.conductor("PE", c["id"], c["conductorSize"], con["E"], dev["terminals"]["E"], [], kind="internal",
                      serves=[], label="Earth connector → socket earth")
    for pair in enc.get("fanPairs", []):
        sw_dev = next(x for x in devs if x["id"] == pair["switch"])
        reg = next(x for x in devs if x["id"] == pair["regulator"])
        sw = next(s for s in d.switches if s["deviceId"] == sw_dev["id"])
        net.conductor("SW", c["id"], c["conductorSize"], sw_dev["terminals"]["out"], reg["terminals"]["in"], [], kind="internal",
                      serves=_switch_points(d, sw), controls=[sw["id"]], label="Fan switch → regulator (series)", chain=c["chain"])
        net.conductor("PE", c["id"], c["conductorSize"], con["E"], reg["terminals"]["earth"], [], kind="internal",
                      serves=[], label="Earth connector → regulator body (CPWD 3.16.3)")


def _switch_points(d, sw):
    return list(sw["points"])


def _point_wiring(d, r, net, c, board):
    """Board -> point boxes as a tree (each point looped from its nearest wired neighbour,
    loop-in practice): neutral and earth looped along every branch, each switched live
    along its own group's branches, the regulated live straight to its fan. A branch whose
    first conduit would exceed CPWD Table 4.1 (8 x 1.5 mm2 in 25 mm) gets its own run."""
    pts = [p for p in d.points if p["roomId"] == board["roomId"] and p["kind"] in LIGHTING_KINDS]
    if not pts:
        return
    devs = {x["id"]: x for x in d.devices if x["enclosureId"] == board["id"]}
    regs = {rg["points"][0]: rg for rg in d.regulators if rg["enclosureId"] == board["id"]}
    bx, by, _ = board["mount"]["face"]
    pos = {p["id"]: (p["position"][0], p["position"][1]) for p in pts}
    parent = {}
    attached = ["ROOT"]
    pos["ROOT"] = (bx, by)
    left = list(pts)
    while left:
        best = None
        for p in left:
            for a in attached:
                dd = abs(pos[p["id"]][0] - pos[a][0]) + abs(pos[p["id"]][1] - pos[a][1])
                if p["kind"] in ("mirror-light", "undercabinet", "exhaust") and a != "ROOT":
                    dd += 1.0          # wall points prefer their own drop from the slab near the board
                if best is None or dd < best[0]:
                    best = (dd, p, a)
        _, p, a = best
        parent[p["id"]] = a
        attached.append(p["id"])
        left.remove(p)
    byid = {p["id"]: p for p in pts}

    def subtree(n):
        out = [n]
        for k, v in parent.items():
            if v == n:
                out += subtree(k)
        return out

    def load(n):
        ids = [x for x in subtree(n) if x != "ROOT"]
        groups = {byid[x].get("switchId") for x in ids if byid[x]["kind"] != "fan"}
        fans = sum(1 for x in ids if byid[x]["kind"] == "fan")
        return len(groups) + fans + 2
    # re-root branches that would overfill their conduit
    changed = True
    while changed:
        changed = False
        for n in list(parent):
            if parent[n] != "ROOT" and load(n) <= 8 and load(parent[n]) > 8:
                parent[n] = "ROOT"
                changed = True
            elif parent[n] == "ROOT" and load(n) > 8:
                kids = [k for k, v in parent.items() if v == n]
                if kids:
                    parent[max(kids, key=load)] = "ROOT"
                    changed = True
    # boxes and conduits (one per tree edge)
    ports = {}
    for p in pts:
        if p["kind"] in ("mirror-light", "undercabinet", "exhaust"):
            ports[p["id"]] = r.wall_box(p, "wall-box")
        else:
            ports[p["id"]] = r.ceiling_box(p, "fan-box" if p["kind"] == "fan" else "cove-box" if p["kind"] == "cove" else "light-box")
    edge = {}
    order = [x for x in attached if x != "ROOT"]
    for n in order:
        a = parent[n]
        src = r.wall_port(board, "top") if a == "ROOT" else _continue_port(ports[a])
        edge[n] = r.run("point", "lighting", src, ports[n], floor=board["floor"], rooms={board["roomId"]},
                        circuit_ids=[c["id"]], label=f"{c['id']} point wiring → {byid[n]['label']}")
    tmap = {}
    for p in pts:
        box = next(b for b in d.boxes if b["id"] == ports[p["id"]]["boxId"])
        tmap[p["id"]] = {"L": d.terminal_box(box, "Point connector L", "SW", (-.012, 0, -.03)),
                         "N": d.terminal_box(box, "Point connector N", "N", (0, 0, -.03)),
                         "E": d.terminal_box(box, "Point connector earth", "E", (.012, 0, -.03))}
        p["terminals"] = tmap[p["id"]]
    con = board["connectors"]

    def path(n):
        out = []
        while n != "ROOT":
            out.append(n)
            n = parent[n]
        return list(reversed(out))
    # neutral and protective earth looped along every edge
    for n in order:
        a = parent[n]
        down = [x for x in subtree(n)]
        net.conductor("N", c["id"], 1.5, con["N"] if a == "ROOT" else tmap[a]["N"], tmap[n]["N"], edge[n]["ids"], kind="point",
                      serves=down, label=f"Neutral loop → {byid[n]['label']}")
        net.conductor("PE", c["id"], 1.5, con["E"] if a == "ROOT" else tmap[a]["E"], tmap[n]["E"], edge[n]["ids"], kind="point",
                      serves=[], label=f"Protective conductor loop → {byid[n]['label']}")
    # switched lives per group: from the switch (or the last group point above) to each group point
    for sw in [s for s in d.switches if s["enclosureId"] == board["id"]]:
        members = [x for x in sw["points"] if x in byid]
        if not members:
            continue
        dev = devs[sw["deviceId"]]
        for m in members:
            p = byid[m]
            route = path(m)
            if p["kind"] == "fan":
                reg = regs[m]
                net.conductor("REG", c["id"], 1.5, devs[reg["deviceId"]]["terminals"]["out"], tmap[m]["L"],
                              [i for x in route for i in edge[x]["ids"]], kind="point", serves=[m],
                              label=f"Regulated live → {p['label']}", chain=c["chain"], controls=[sw["id"]], regulator=reg["id"])
                continue
            # nearest ancestor in the same group supplies this point (loop-in)
            src, start = dev["terminals"]["out"], 0
            for i, x in enumerate(route[:-1]):
                if x in members:
                    src, start = tmap[x]["L"], i + 1
            net.conductor("SW", c["id"], 1.5, src, tmap[m]["L"], [i for x in route[start:] for i in edge[x]["ids"]], kind="point",
                          serves=[x for x in subtree(m) if x in members], label=f"Switched live → {p['label']}",
                          chain=c["chain"], controls=[sw["id"]])
    for n in order:
        _size_conduit(d, edge[n])


def _continue_port(port):
    if port.get("wall"):
        return {"xy": port["xy"], "z": port["z"], "boxId": port["boxId"], "floor": port["floor"]}
    return dict(port)


def _size_conduit(d, run):
    if "conduits" in run:
        for c in run["conduits"]:
            _size_conduit(d, c)
        return
    counts = defaultdict(int)
    for kid in run["carries"]:
        k = next(x for x in d.conductors if x["id"] == kid)
        counts[k["size"] or 4.0] += 1
    size = conduit_size(counts)
    if size is None:
        raise ValueError(f"Conduit {run['id']} overfilled: {dict(counts)}")
    run["diameter"] = size
    run["fill"] = {str(k): v for k, v in counts.items()}
    run["material"] = "rigid PVC (IS 9537-3)"
