"""Checks for the electrical teaching model. Each returns a list of problems.

Used by the builder (which refuses to write a model with problems) and by the
tests. The checks are geometric and topological; they do not certify that the
design complies with any regulation.
"""
from __future__ import annotations

import math
from collections import defaultdict, deque

try:
    from .electrical_geometry import inside, SOFFIT, FLOOR_HEIGHT, WALL_HEIGHT
except ImportError:
    from electrical_geometry import inside, SOFFIT, FLOOR_HEIGHT, WALL_HEIGHT

LIGHTING = {"downlight", "cove", "mirror-light", "undercabinet", "fan", "exhaust"}
FILL_BENT = {20: {1.5: 4, 2.5: 3, 4.0: 2}, 25: {1.5: 8, 2.5: 6, 4.0: 5}}


def _walls(building):
    out = {}
    for w in building["walls"]:
        poly = [[x / 1000, y / 1000] for x, y in w["polygon"]]
        out[w["id"]] = {"floor": w["floor"], "poly": poly, "t": w["thickness"] / 1000, "rooms": w.get("rooms", []),
                        "a": (w["a"][0] / 1000, w["a"][1] / 1000), "b": (w["b"][0] / 1000, w["b"][1] / 1000)}
    return out


def _slab(building, floor):
    roof = next(r for r in building["roofs"] if r["floor"] == floor)
    return [([[x / 1000, y / 1000] for x, y in c["polygon"]], [[[x / 1000, y / 1000] for x, y in h] for h in c.get("holes", [])])
            for c in roof["ceiling"]]


def _in_slab(regions, x, y):
    return any(inside(x, y, poly) and not any(inside(x, y, h) for h in holes) for poly, holes in regions)


def _in_wall(walls, x, y, z, tol=.004):
    floor = int(math.floor((z + .0001) / FLOOR_HEIGHT))
    for w in walls.values():
        if w["floor"] != floor:
            continue
        zl = z - floor * FLOOR_HEIGHT
        if not (-.001 <= zl <= WALL_HEIGHT + .001):
            continue
        if inside(x, y, w["poly"]) or _near_poly(w["poly"], x, y, tol):
            return w
    return None


def _near_poly(poly, x, y, tol):
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0, min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / L))
        if math.dist((x, y), (a[0] + dx * t, a[1] + dy * t)) <= tol:
            return True
    return False


def classify_point(building, x, y, z, walls=None, slabs=None, ground=-.405):
    """Where a conduit centre-line point is embedded: wall, slab, plinth, ground or None (air)."""
    walls = walls or _walls(building)
    slabs = slabs or {f: _slab(building, f) for f in (0, 1)}
    foot = [[px / 1000, py / 1000] for px, py in building["footprint"]]
    for f in (0, 1):
        top = f * FLOOR_HEIGHT + FLOOR_HEIGHT
        if f * FLOOR_HEIGHT + SOFFIT - .001 <= z <= top + .001 and _in_slab(slabs[f], x, y):
            return "slab"
    if _in_wall(walls, x, y, z):
        return "wall"
    if z <= 0 and inside(x, y, foot) or (z <= 0 and _near_poly(foot, x, y, .2)):
        return "plinth"
    if z <= ground - .2:
        return "ground"
    return None


def check_conduits(model, building, step=.05):
    """Every conduit centre-line sample lies inside a wall, slab, plinth or the ground, or inside
    the enclosure/box it connects; nothing runs through open air."""
    problems = []
    walls = _walls(building)
    slabs = {f: _slab(building, f) for f in (0, 1)}
    encs = {e["id"]: e for e in model["enclosures"]}
    boxes = {b["id"]: b for b in model["boxes"]}
    for c in model["conduits"]:
        pts = c["points"]
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            n = max(1, int(math.dist(a, b) / step))
            for k in range(n + 1):
                t = k / n
                p = [a[j] + (b[j] - a[j]) * t for j in range(3)]
                where = classify_point(building, *p, walls=walls, slabs=slabs)
                if where:
                    continue
                if _inside_end(p, c, encs, boxes):
                    continue
                problems.append(f"{c['id']} ({c['label']}) passes through open air near {[round(v, 3) for v in p]}")
                break
            else:
                continue
            break
    return problems


def _inside_end(p, c, encs, boxes):
    for ref in (c["from"], c["to"]):
        if ref in encs:
            e = encs[ref]
            m = e["mount"]
            nx, ny = m["normal"]
            rx, ry = -ny, nx
            dx, dy, dz = p[0] - m["face"][0], p[1] - m["face"][1], p[2] - m["face"][2]
            lx, lz = dx * rx + dy * ry, dx * nx + dy * ny
            depth = max(e["size"].get("depth", .06), .06)
            surface = e["size"].get("surface", 0)
            if abs(lx) <= e["size"]["w"] / 2 + .01 and abs(dz) <= e["size"]["h"] / 2 + .01 and -depth - .01 <= lz <= surface + .01:
                return True
        if ref in boxes:
            b = boxes[ref]
            if b["kind"] == "earth-pit":
                x, y, z = b["position"]
                if abs(p[0] - x) <= .2 and abs(p[1] - y) <= .2 and z - .4 <= p[2] <= z + .02:
                    return True
    return False


def check_mounts(model, building, house):
    """Enclosures are flush on a real wall face, clear of openings and obstructions, with no
    back-to-back clash, inside the wall height."""
    problems = []
    seen = defaultdict(list)
    for e in model["enclosures"]:
        m = e["mount"]
        wall = house.walls[m["wallId"]]
        fx, fy, fz = m["face"]
        off = wall.offset((fx, fy))
        expect = m["side"] * (wall.half + m["finish"])
        if abs(off - expect) > .003:
            problems.append(f"{e['id']} face is {off:.3f} m from the wall centre-line, expected {expect:.3f}")
        al = wall.along((fx, fy))
        if not (e["size"]["w"] / 2 - .01 <= al <= wall.length - e["size"]["w"] / 2 + .01):
            problems.append(f"{e['id']} overhangs the end of {wall.ident}")
        level = wall.floor * FLOOR_HEIGHT
        if not (level + .05 <= fz - e["size"]["h"] / 2 and fz + e["size"]["h"] / 2 <= level + WALL_HEIGHT - .3):
            problems.append(f"{e['id']} is outside the usable wall height")
        if house.opening_conflict(wall, al, e["size"]["w"], fz - e["size"]["h"] / 2, fz + e["size"]["h"] / 2, side_clear=.05, vertical_clear=.05):
            problems.append(f"{e['id']} overlaps an opening on {wall.ident}")
        if e["size"].get("depth", 0) > wall.thickness - .04:
            problems.append(f"{e['id']} recess {e['size']['depth']} is too deep for a {wall.thickness} m wall")
        finishes = ("wall-tile", "wall-panel") if m["finish"] > .024 else ("wall-tile",)
        blk = house.blockers(wall, m["side"], al, e["size"]["w"], fz - e["size"]["h"] / 2, fz + e["size"]["h"] / 2,
                             max(.012, e["size"].get("surface", 0)), ignore=finishes, pad=.0)
        if blk:
            problems.append(f"{e['id']} collides with {[(b.role, b.ident) for b in blk][:3]}")
        room = e["roomId"] if not e.get("exterior") else None
        if room and house.behind_door(wall, m["side"], al, e["size"]["w"], room):
            problems.append(f"{e['id']} is behind a door leaf")
        seen[m["wallId"]].append((e, al))
    for wid, items in seen.items():
        wall = house.walls[wid]
        for i, (a, aa) in enumerate(items):
            for b, ab in items[i + 1:]:
                if {a["kind"], b["kind"]} <= {"main-db", "loose-wire-box"} or {a["kind"], b["kind"]} <= {"sub-db", "loose-wire-box"}:
                    continue
                if abs(aa - ab) >= (a["size"]["w"] + b["size"]["w"]) / 2 + .005:
                    continue
                za0, za1 = a["mount"]["face"][2] - a["size"]["h"] / 2, a["mount"]["face"][2] + a["size"]["h"] / 2
                zb0, zb1 = b["mount"]["face"][2] - b["size"]["h"] / 2, b["mount"]["face"][2] + b["size"]["h"] / 2
                if za1 <= zb0 or zb1 <= za0:
                    continue
                if a["mount"]["side"] == b["mount"]["side"]:
                    problems.append(f"{a['id']} and {b['id']} overlap on {wid}")
                elif a["size"].get("depth", 0) + b["size"].get("depth", 0) > wall.thickness - .02:
                    problems.append(f"{a['id']} and {b['id']} are back to back without enough wall between")
    return problems


def check_conductor_paths(model):
    """Each conductor's conduits form one continuous chain from its source enclosure/box to its
    destination; internal conductors stay inside one enclosure."""
    problems = []
    terms = {t["id"]: t for t in model["terminals"]}
    conduits = {c["id"]: c for c in model["conduits"]}
    for k in model["conductors"]:
        a = terms.get(k["from"])
        b = terms.get(k["to"])
        if b is None or (a is None and k["from"] != "DISCOM network"):
            problems.append(f"{k['id']} has a missing terminal")
            continue
        ra = (a.get("enclosureId") or a.get("boxId")) if a else None
        rb = b.get("enclosureId") or b.get("boxId")
        if not k["conduits"]:
            if ra != rb:
                problems.append(f"{k['id']} ({k['label']}) jumps between {ra} and {rb} without a conduit")
            continue
        chain = [conduits[c] for c in k["conduits"]]
        cur = ra                         # None = the DISCOM network beyond the property
        for c in chain:
            ends = {c["from"], c["to"]}
            if cur not in ends:
                problems.append(f"{k['id']} ({k['label']}) enters {c['id']} from {cur}, but it joins {sorted(map(str, ends))}")
                break
            cur = c["to"] if c["from"] == cur else c["from"]
        else:
            if cur != rb:
                problems.append(f"{k['id']} ({k['label']}) ends at {cur}, not its terminal enclosure {rb}")
    return problems


def check_netlist(model):
    """Every point has a live path to its circuit's MCB, a neutral path back to the RCCB-protected
    neutral bar, and an earth path to the electrodes. Switches and MCBs are only in live
    conductors; protective earth is never a return path."""
    problems = []
    devices = {d["id"]: d for d in model["devices"]}
    terms = {t["id"]: t for t in model["terminals"]}
    adj = {"live": defaultdict(set), "N": defaultdict(set), "PE": defaultdict(set)}
    cls = {"L": "live", "L1": "live", "L2": "live", "L3": "live", "SW": "live", "REG": "live", "N": "N", "PE": "PE"}
    for k in model["conductors"]:
        net = cls[k["role"]]
        adj[net][k["from"]].add(k["to"])
        adj[net][k["to"]].add(k["from"])
    # devices conduct between their own terminals (closed state)
    for d in model["devices"]:
        t = d.get("terminals") or {}
        if d["kind"] in ("switch", "switch16", "local-mcb", "mcb", "regulator"):
            if "in" in t and "out" in t:
                adj["live"][t["in"]].add(t["out"]); adj["live"][t["out"]].add(t["in"])
        if d["kind"] in ("mcb4p", "rccb4p", "isolator2p"):
            for name, tid in t.items():
                pole, io = name.rsplit(" ", 1)
                other = t.get(f"{pole} {'out' if io == 'in' else 'in'}")
                net = "N" if pole == "N" else "live"
                adj[net][tid].add(other); adj[net][other].add(tid)
        if d["kind"] == "meter":
            for name, tid in t.items():
                ph, io = name.split(" ")
                other = t.get(f"{ph} {'out' if io == 'in' else 'in'}")
                net = "N" if ph == "N" else "live"
                adj[net][tid].add(other); adj[net][other].add(tid)
        if d["kind"] in ("busbar", "neutral-bar", "earth-bar"):
            ids = list(t.values())
            net = {"busbar": "live", "neutral-bar": "N", "earth-bar": "PE"}[d["kind"]]
            if d["kind"] == "busbar":
                continue        # comb busbar: each tooth belongs to one phase, wired via its feed
            for x in ids:
                for y in ids:
                    if x != y:
                        adj[net][x].add(y)
    # comb busbar teeth: each MCB input is connected (by its own busbar conductor) to the right phase feed
    meter = next(d for d in model["devices"] if d["kind"] == "meter")
    sources_live = {meter["terminals"][f"{p} in"] for p in ("R", "Y", "B")}
    source_n = {meter["terminals"]["N in"]}
    electrodes = {t["id"] for t in model["terminals"] if t.get("boxId", "").startswith("EP")}

    def reach(net, start, goals, banned=()):
        seen, q = {start}, deque([start])
        while q:
            n = q.popleft()
            if n in goals:
                return True
            for m in adj[net][n]:
                if m not in seen and m not in banned:
                    seen.add(m)
                    q.append(m)
        return False

    for p in model["points"]:
        t = p.get("terminals") or _point_terms(model, p)
        if not t:
            problems.append(f"{p['id']} has no terminals")
            continue
        if not reach("live", t["L"], sources_live):
            problems.append(f"{p['id']} ({p['label']}) has no live path to the service")
        if not reach("N", t["N"], source_n):
            problems.append(f"{p['id']} ({p['label']}) has no neutral path to the service")
        if not reach("PE", t["E"], electrodes):
            problems.append(f"{p['id']} ({p['label']}) has no protective-earth path to the electrodes")
        circuit = next((c for c in model["circuits"] if c["id"] == p.get("circuitId")), None)
        if circuit is None:
            problems.append(f"{p['id']} has no circuit")
            continue
        mcb = devices[circuit["mcb"]]
        # the live path must pass through this circuit's MCB: removing it disconnects the point
        if reach("live", t["L"], sources_live, banned={mcb["terminals"]["in"], mcb["terminals"]["out"]}):
            problems.append(f"{p['id']} is live without passing through {circuit['id']}'s MCB")
        rccb = next(d for d in model["devices"] if d["kind"] == "rccb4p")
        rccb_n = {rccb["terminals"]["N in"], rccb["terminals"]["N out"]}
        if reach("N", t["N"], source_n, banned=rccb_n):
            problems.append(f"{p['id']} neutral bypasses the RCCB")
        if reach("N", t["N"], electrodes) or reach("PE", t["E"], source_n):
            problems.append(f"{p['id']} neutral and protective earth are joined")
    # no switching device in the neutral or protective conductor
    for k in model["conductors"]:
        if k["role"] in ("N", "PE"):
            for tid in (k["from"], k["to"]):
                tm = terms.get(tid)
                if tm and tm.get("deviceId"):
                    dev = devices[tm["deviceId"]]
                    if dev["kind"] in ("switch", "switch16", "local-mcb", "mcb", "regulator") and tm["role"] not in ("E",):
                        problems.append(f"{k['id']} ({k['role']}) lands on switching device {dev['id']}")
        if k["role"] == "PE" and k.get("serves"):
            problems.append(f"{k['id']} protective conductor is marked as carrying load current")
    return problems


def _point_terms(model, p):
    if p.get("deviceId"):
        dev = next(d for d in model["devices"] if d["id"] == p["deviceId"])
        t = dev.get("terminals") or {}
        return {"L": t.get("L"), "N": t.get("N"), "E": t.get("E")}
    return None


def check_rules(model):
    """Circuit composition, conduit fill and separation, single phase per room."""
    problems = []
    points = {p["id"]: p for p in model["points"]}
    for c in model["circuits"]:
        pts = [points[p] for p in c["points"]]
        if c["kind"] == "lighting":
            if any(p["kind"] not in LIGHTING for p in pts):
                problems.append(f"{c['id']} lighting circuit feeds a socket")
            if len(pts) > 20:
                problems.append(f"{c['id']} has {len(pts)} points (CPWD 3.10.1 limit 20)")
        if c["kind"] == "power":
            n6 = sum(p["kind"] == "socket6" for p in pts)
            n16 = sum(p["kind"] == "socket16" for p in pts)
            if not ((n16 == 0 and n6 <= 3) or (n6 == 0 and n16 <= 2) or (n16 <= 1 and n6 <= 2)):
                problems.append(f"{c['id']} outlets exceed CPWD 3.10.3 ({n6} × 6 A, {n16} × 16 A)")
        if c["kind"] == "geyser" and len(pts) != 1:
            problems.append(f"{c['id']} water heater is not on an independent circuit")
    kinds = {c["id"]: c["kind"] for c in model["circuits"]}
    conductors = {k["id"]: k for k in model["conductors"]}
    for cd in model["conduits"]:
        ks = [conductors[k] for k in cd["carries"]]
        light = {k["circuitId"] for k in ks if kinds.get(k["circuitId"]) == "lighting"}
        power = {k["circuitId"] for k in ks if kinds.get(k["circuitId"]) in ("power", "geyser")}
        if light and power and cd["function"] in ("lighting", "power"):
            problems.append(f"{cd['id']} mixes light and power wiring (CPWD 3.2.6)")
        if cd["function"] in ("lighting", "power") and ks:
            counts = defaultdict(int)
            for k in ks:
                counts[k["size"] or 4.0] += 1
            fill = FILL_BENT.get(cd["diameter"])
            if not fill or sum(n / fill[s] for s, n in counts.items()) > 1 + 1e-9:
                problems.append(f"{cd['id']} is overfilled for {cd['diameter']} mm ({dict(counts)})")
        # not more than the equivalent of four quarter-bends from outlet to outlet (CPWD 5.4.1(ii))
        if cd["function"] in ("lighting", "power", "submain") and _bends(cd["points"]) > 4.01:
            problems.append(f"{cd['id']} has {_bends(cd['points']):.1f} quarter-bends between boxes (CPWD 5.4.1(ii) limit 4)")
        # outgoing and return conductors of a circuit share the conduit (CPWD 5.4.3(g))
        by_c = defaultdict(set)
        for k in ks:
            if k["circuitId"]:
                by_c[k["circuitId"]].add(k["role"])
        for cid, roles in by_c.items():
            if roles & {"L", "SW", "REG"} and "N" not in roles:
                problems.append(f"{cd['id']} carries {cid} live without its neutral")
            if roles & {"L", "SW", "REG", "N"} and "PE" not in roles:
                problems.append(f"{cd['id']} carries {cid} without its protective conductor (CPWD 5.4.4)")
    by_room = defaultdict(set)
    phase = {c["id"]: c["phase"] for c in model["circuits"]}
    for p in model["points"]:
        by_room[p["roomId"]].add(phase[p["circuitId"]])
    for room, phases in by_room.items():
        if len(phases) > 1:
            problems.append(f"{room} has points on phases {sorted(phases)}")
    return problems


def _bends(pts):
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


def validate(model, building, house):
    report = {
        "mounts": check_mounts(model, building, house),
        "conduits": check_conduits(model, building),
        "paths": check_conductor_paths(model),
        "netlist": check_netlist(model),
        "rules": check_rules(model),
    }
    return report
