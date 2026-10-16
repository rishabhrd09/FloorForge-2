"""Wall, slab and obstruction geometry for the electrical teaching edition.

Coordinates are scene metres with Z up, read from the copied architectural
files. Nothing here writes to those files. The helpers choose *plausible study
locations*; they are not surveyed or approved installation positions.
"""
from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field

FLOOR_HEIGHT = 3.15        # storey height in the architectural model
WALL_HEIGHT = 3.0          # wall mesh height above each floor level
SOFFIT = 2.993             # finished ceiling under each slab (F*-ceiling layer)
SLAB_THICKNESS = .15       # 3.000-3.150 m in the architectural slab nodes
SLAB_CONDUIT = .045        # assumed conduit centre above the slab soffit

# Scene roles that make a wall face unusable for an enclosure or block access to it.
WALL_OBSTRUCTIONS = {
    "furniture", "joinery", "wall-panel", "curtain", "art", "mirror", "window-surround",
    "sill", "door", "glass", "railing", "stair", "column", "pipe", "canopy", "gate",
    "outdoor-furniture", "plant-proxy", "detail", "fixture", "downlight", "cove",
    "ceiling-feature", "beam", "vehicle", "site", "landscape", "court", "step", "porch",
    "plinth", "drain", "wall-tile",
}


def xy(point):
    return (round(point[0] / 1000, 4), round(point[1] / 1000, 4))


def inside(x: float, y: float, polygon) -> bool:
    odd = False
    n = len(polygon)
    for i in range(n):
        a, b = polygon[i], polygon[(i + 1) % n]
        if (a[1] > y) != (b[1] > y) and x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]:
            odd = not odd
    return odd


def wall_length(wall):
    return math.dist(xy(wall["a"]), xy(wall["b"]))


def wall_frame(wall):
    a, b = xy(wall["a"]), xy(wall["b"])
    length = math.dist(a, b)
    if length < 1e-6:
        raise ValueError(f"Degenerate wall: {wall['id']}")
    tangent = ((b[0] - a[0]) / length, (b[1] - a[1]) / length)
    return a, tangent, length


def project(wall, point):
    """Distance along a wall centreline and the projected point."""
    a, tangent, length = wall_frame(wall)
    along = max(0., min(length, (point[0] - a[0]) * tangent[0] + (point[1] - a[1]) * tangent[1]))
    return along, (a[0] + tangent[0] * along, a[1] + tangent[1] * along)


def free_intervals(wall, openings, *, clearance=.13):
    """Spans of a wall centreline clear of every opening, at any height."""
    length = wall_length(wall)
    blocked = sorted((max(0., o.get("offset", 0) / 1000 - clearance),
                      min(length, (o.get("offset", 0) + o["width"]) / 1000 + clearance))
                     for o in openings if o.get("wall_id") == wall["id"])
    free, cursor = [], .10
    for lo, hi in blocked:
        if hi <= cursor:
            continue
        if lo > cursor:
            free.append((cursor, lo))
        cursor = max(cursor, hi)
    if length - .10 > cursor:
        free.append((cursor, length - .10))
    return free


@dataclass
class Box:
    lo: tuple
    hi: tuple
    role: str = ""
    ident: str = ""
    parts: list | None = None   # per-triangle boxes of a non-primitive mesh

    def hits(self, lo, hi, pad=0.) -> bool:
        if not all(self.lo[i] - pad < hi[i] and lo[i] < self.hi[i] + pad for i in range(3)):
            return False
        if not self.parts:
            return True
        return any(all(a[i] - pad < hi[i] and lo[i] < b[i] + pad for i in range(3)) for a, b in self.parts)


def mesh_parts(node, assets):
    """Per-triangle world AABBs of a mesh asset placed with identity rotation."""
    asset = assets[node["asset"]]
    p, sc = node["position"], node["scale"]
    verts = [(v[0] * sc[0] + p[0], v[1] * sc[1] + p[1], v[2] * sc[2] + p[2]) for v in asset["vertices"]]
    parts = []
    for f in asset["faces"]:
        tri = [verts[i] for i in f]
        parts.append((tuple(min(t[i] for t in tri) for i in range(3)), tuple(max(t[i] for t in tri) for i in range(3))))
    return parts


def node_box(node, assets):
    """World-space AABB of a scene node (exact for rotated unit primitives)."""
    asset = node["asset"]
    p, sc, rot = node["position"], node["scale"], node.get("rotation", [0, 0, 0])
    if asset.startswith("unit-"):
        corners = [(sx * abs(sc[0]) / 2, sy * abs(sc[1]) / 2, sz * abs(sc[2]) / 2)
                   for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    else:
        corners = [(v[0] * sc[0], v[1] * sc[1], v[2] * sc[2]) for v in assets[asset]["vertices"]]
    if any(abs(r) > 1e-9 for r in rot):
        rx, ry, rz = rot
        cx, sx_, cy, sy_, cz, sz_ = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)

        def turn(v):  # X, then Y, then Z (scene convention: rotation applied as Rz*Ry*Rx)
            x, y, z = v
            y, z = y * cx - z * sx_, y * sx_ + z * cx
            x, z = x * cy + z * sy_, -x * sy_ + z * cy
            x, y = x * cz - y * sz_, x * sz_ + y * cz
            return (x, y, z)
        corners = [turn(c) for c in corners]
    xs = [c[0] + p[0] for c in corners]
    ys = [c[1] + p[1] for c in corners]
    zs = [c[2] + p[2] for c in corners]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


@dataclass
class Opening:
    ident: str
    kind: str
    s0: float
    s1: float
    sill: float
    top: float
    hinge: str | None
    swing: str | None
    connects: list


@dataclass
class Wall:
    ident: str
    floor: int
    a: tuple
    b: tuple
    tangent: tuple
    normal: tuple          # left normal of a -> b
    length: float
    thickness: float
    external: bool
    rooms: list
    polygon: list
    openings: list = field(default_factory=list)
    sides: dict = field(default_factory=dict)   # +1 / -1 -> room id or "outside"

    @property
    def half(self):
        return self.thickness / 2

    def point(self, along, side=0, depth=0.):
        """Plan point at `along`, on face `side` (+1/-1) `depth` metres behind that face."""
        off = 0. if side == 0 else side * (self.half - depth)
        return (self.a[0] + self.tangent[0] * along + self.normal[0] * off,
                self.a[1] + self.tangent[1] * along + self.normal[1] * off)

    def along(self, p):
        return (p[0] - self.a[0]) * self.tangent[0] + (p[1] - self.a[1]) * self.tangent[1]

    def offset(self, p):
        return (p[0] - self.a[0]) * self.normal[0] + (p[1] - self.a[1]) * self.normal[1]

    def face_normal(self, side):
        return (self.normal[0] * side, self.normal[1] * side)


class House:
    """Read-only index of the architectural model used by the electrical study."""

    def __init__(self, building, scene):
        self.building, self.scene = building, scene
        self.H = scene["floor_height"]
        if abs(self.H - FLOOR_HEIGHT) > 1e-6:
            raise ValueError("Unexpected storey height")
        self.rooms = {r["id"]: r for r in scene["rooms"]}
        self.spaces = {s["id"]: s for s in building["spaces"]}
        self.walls: dict[str, Wall] = {}
        openings_by_wall: dict[str, list] = {}
        for o in building["openings"]:
            openings_by_wall.setdefault(o["wall_id"], []).append(o)
        for w in building["walls"]:
            a, t, length = wall_frame(w)
            wall = Wall(w["id"], w["floor"], a, xy(w["b"]), t, (-t[1], t[0]), length,
                        w["thickness"] / 1000, w["external"], list(w.get("rooms", [])),
                        [[round(x / 1000, 4), round(y / 1000, 4)] for x, y in w["polygon"]])
            for o in openings_by_wall.get(w["id"], []):
                s0 = o.get("offset", 0) / 1000
                sill = o.get("sill", 0) / 1000
                wall.openings.append(Opening(o["id"], o["kind"], s0, s0 + o["width"] / 1000, sill,
                                             sill + o.get("height", 2100) / 1000, o.get("hinge"),
                                             o.get("swing"), o.get("connects", [])))
            for side in (1, -1):
                wall.sides[side] = self._side_room(wall, side)
            self.walls[wall.ident] = wall
        self.obstacles = []
        assets = scene["assets"]
        for n in scene["nodes"]:
            if n["role"] in WALL_OBSTRUCTIONS:
                lo, hi = node_box(n, assets)
                parts = None
                if not n["asset"].startswith("unit-") and not any(abs(r) > 1e-9 for r in n.get("rotation", [0, 0, 0])):
                    parts = mesh_parts(n, assets)
                self.obstacles.append(Box(lo, hi, n["role"], n["id"], parts))
        self.furniture = [f for f in scene["furniture"] if f.get("footprint")]
        self._ceilings = {}
        for n in scene["nodes"]:
            if n["role"] in ("ceiling", "ceiling-feature", "cove", "beam") and n["floor"] >= 0:
                lo, hi = node_box(n, assets)
                if n["id"].startswith("F") and n["id"].endswith("-ceiling"):
                    continue  # the finished soffit layer itself
                self._ceilings.setdefault(n["floor"], []).append((n, lo, hi))
        self._ceiling_shapes = {}
        for n in scene["nodes"]:
            if n["role"] in ("ceiling", "cove", "ceiling-feature") and not n["id"].startswith("F") \
                    and n["asset"] in assets and not n["asset"].startswith("unit-"):
                self._ceiling_shapes[n["id"]] = assets[n["asset"]]

    def ground_at(self, x, y, default=-.405):
        """Top of the paved/planted outdoor surface at a plan point (highest below +0.1 m)."""
        best = None
        for n in self.scene["nodes"]:
            if n["role"] not in ("site", "court", "terrain", "lawn", "porch", "step"):
                continue
            lo, hi = node_box(n, self.scene["assets"])
            if lo[0] <= x <= hi[0] and lo[1] <= y <= hi[1] and hi[2] < .1 and hi[2] - lo[2] < .6:
                if best is None or hi[2] > best:
                    best = hi[2]
        return round(best, 4) if best is not None else default

    # ---------- rooms ----------
    def _side_room(self, wall, side):
        mid = wall.length / 2
        for along in (mid, wall.length * .25, wall.length * .75, .2, wall.length - .2):
            px, py = wall.point(along, side, -.12)
            room = self.room_at(px, py, wall.floor)
            if room:
                return room
        return "outside"

    def room_at(self, x, y, floor):
        for r in self.scene["rooms"]:
            if r["floor"] == floor and inside(x, y, r["polygon"]) and \
                    not any(inside(x, y, h) for h in r.get("holes", [])):
                return r["id"]
        return None

    def level(self, floor):
        return floor * self.H

    def soffit(self, floor):
        return floor * self.H + SOFFIT

    def overhead_bottom(self, x, y, floor):
        """Lowest overhead finish (false-ceiling band, feature, beam) above a plan point."""
        z = self.soffit(floor)
        for n, lo, hi in self._ceilings.get(floor, []):
            if lo[0] - 1e-6 <= x <= hi[0] + 1e-6 and lo[1] - 1e-6 <= y <= hi[1] + 1e-6:
                shape = self._ceiling_shapes.get(n["id"])
                if shape is not None and not _mesh_covers(shape, x, y):
                    continue
                z = min(z, lo[2])
        return z

    # ---------- mounting ----------
    def faces_of_room(self, room_id):
        """(wall, side) pairs whose face looks into `room_id`."""
        room = self.rooms[room_id]
        out = []
        for wall in self.walls.values():
            if wall.floor != room["floor"]:
                continue
            for side in (1, -1):
                if wall.sides[side] == room_id:
                    out.append((wall, side))
        return out

    def face_span(self, wall, side, room_id):
        """Along-wall interval of this face that actually lies in `room_id`."""
        step, inside_s = .05, []
        s = .0
        while s <= wall.length + 1e-9:
            px, py = wall.point(s, side, -.08)
            if self.room_at(px, py, wall.floor) == room_id:
                inside_s.append(s)
            s += step
        if not inside_s:
            return None
        return (min(inside_s), max(inside_s))

    def finish_depth(self, wall, side, along, z, roles=("wall-tile",)):
        """Thickness of tiles (or panelling) proud of the plaster face at a point (0 when plain)."""
        fx, fy = wall.point(along, side)
        nx, ny = wall.face_normal(side)
        depth = 0.
        for box in self.obstacles:
            if box.role not in roles:
                continue
            if not (box.lo[2] - 1e-6 <= z <= box.hi[2] + 1e-6):
                continue
            # a tile layer within 4 cm of the face, covering this point in plan
            for d in (.002, .006, .01, .015, .02, .025, .03):
                qx, qy = fx + nx * d, fy + ny * d
                if box.lo[0] - 1e-4 <= qx <= box.hi[0] + 1e-4 and box.lo[1] - 1e-4 <= qy <= box.hi[1] + 1e-4:
                    depth = max(depth, d + .002)
        return round(min(depth, .032), 4)

    def blockers(self, wall, side, along, width, z0, z1, projection, *, ignore=("wall-tile",), pad=.02):
        """Obstacles intersecting a rectangle on a wall face extruded `projection` into the room."""
        nx, ny = wall.face_normal(side)
        tx, ty = wall.tangent
        pts = []
        for s in (along - width / 2 - pad, along + width / 2 + pad):
            for d in (.001, projection):
                fx, fy = wall.point(s, side)
                pts.append((fx + nx * d, fy + ny * d))
        lo = (min(p[0] for p in pts), min(p[1] for p in pts), z0 - pad)
        hi = (max(p[0] for p in pts), max(p[1] for p in pts), z1 + pad)
        return [b for b in self.obstacles if b.role not in ignore and b.hits(lo, hi)]

    def opening_conflict(self, wall, along, width, z0, z1, *, side_clear=.10, vertical_clear=.15):
        for o in wall.openings:
            if along + width / 2 + side_clear <= o.s0 or along - width / 2 - side_clear >= o.s1:
                continue
            if z1 + vertical_clear <= o.sill or z0 - vertical_clear >= o.top:
                continue
            return o
        return None

    def door_zones(self, room_id):
        """Hinge point, hinge direction, into-room normal and leaf width of every door
        that swings into `room_id`."""
        zones = []
        floor = self.rooms[room_id]["floor"]
        for w in self.walls.values():
            if w.floor != floor:
                continue
            for o in w.openings:
                if o.kind not in ("door", "entry") or o.swing != room_id:
                    continue
                side = next((sd for sd in (1, -1) if w.sides[sd] == room_id), None)
                if side is None:
                    continue
                leaf = o.s1 - o.s0
                hinge_s, latch_s = (o.s1, o.s0) if o.hinge == "end" else (o.s0, o.s1)
                h = w.point(hinge_s, side)
                l = w.point(latch_s, side)
                t = ((h[0] - l[0]) / leaf, (h[1] - l[1]) / leaf)      # latch -> hinge
                zones.append({"hinge": h, "t": t, "n": w.face_normal(side), "leaf": leaf, "id": o.ident})
        return zones

    def behind_door(self, wall, side, along, width, room_id):
        """True when an open door leaf would cover the enclosure: on the hinge side of the
        door wall (door swung flat) or on the return wall between the open leaf and the corner."""
        nx, ny = wall.face_normal(side)
        tx, ty = wall.tangent
        for z in self.door_zones(room_id):
            hx, hy = z["hinge"]
            for k in (-.5, 0, .5):
                fx, fy = wall.point(along + k * width, side)
                dx, dy = fx - hx, fy - hy
                beyond = dx * z["t"][0] + dy * z["t"][1]          # past the hinge, away from the latch
                into = dx * z["n"][0] + dy * z["n"][1]            # into the room
                if -.03 <= beyond <= z["leaf"] + .15 and abs(into) < .06:
                    return True                                    # same wall, hinge side
                if -.05 <= beyond <= .45 and -.02 <= into <= z["leaf"] + .15:
                    return True                                    # return wall behind the open leaf
        return False


def _mesh_covers(asset, x, y):
    """Whether a horizontal band/ring mesh covers a plan point (ray test on its bottom faces)."""
    verts = asset["vertices"]
    zmin = min(v[2] for v in verts)
    for f in asset["faces"]:
        tri = [verts[i] for i in f]
        if any(abs(v[2] - zmin) > 1e-6 for v in tri):
            continue
        (x1, y1, _), (x2, y2, _), (x3, y3, _) = tri
        den = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
        if abs(den) < 1e-12:
            continue
        a = ((y2 - y3) * (x - x3) + (x3 - x2) * (y - y3)) / den
        b = ((y3 - y1) * (x - x3) + (x1 - x3) * (y - y3)) / den
        if a >= -1e-6 and b >= -1e-6 and a + b <= 1 + 1e-6:
            return True
    return False


@dataclass
class Mount:
    wall: str
    side: int
    room: str
    along: float
    width: float
    height: float
    z: float                 # centre height (absolute)
    recess: float            # depth of the back box behind the finished face
    finish: float            # tile thickness proud of plaster (0 for plaster)
    face: tuple              # finished-face centre (x, y, z)
    normal: tuple            # outward face normal (into the room / outside)
    tangent: tuple
    thickness: float
    score: float = 0.

    def as_dict(self):
        return {"wallId": self.wall, "side": self.side, "roomSide": self.room,
                "along": round(self.along, 4), "width": self.width, "height": self.height,
                "z": round(self.z, 4), "recess": self.recess, "finish": self.finish,
                "face": [round(v, 4) for v in self.face],
                "normal": [round(v, 4) for v in self.normal],
                "tangent": [round(v, 4) for v in self.tangent],
                "wallThickness": self.thickness}


def make_mount(house, wall, side, room, along, width, height, z, recess, score=0., finishes=("wall-tile",)):
    # the plate rests on the proudest finish under its outline (tiles, or panel slats)
    finish = max(house.finish_depth(wall, side, along + k * width / 2, zz, roles=finishes)
                 for k in (-.9, -.5, 0, .5, .9) for zz in (z - height * .4, z, z + height * .4))
    fx, fy = wall.point(along, side)
    nx, ny = wall.face_normal(side)
    face = (fx + nx * finish, fy + ny * finish, z)
    return Mount(wall.ident, side, room, along, width, height, z, recess, finish, face,
                 (nx, ny), wall.tangent, wall.thickness, score)


def search_mounts(house, room_id, *, width, height, z, recess, projection=.03,
                  access=.45, access_band=None, exterior=False, target=None, corner_clear=.15,
                  reserved=(), prefer_latch=True, step=.025, allow_external=True,
                  extra_score=None, doors=None, walls=None, finishes=("wall-tile",)):
    """Rank clear, flush-mount positions on the faces of `room_id` (or its exterior)."""
    room = house.rooms[room_id]
    level = house.level(room["floor"])
    zc = level + z
    z0, z1 = zc - height / 2, zc + height / 2
    out = []
    pairs = []
    jambs = door_jambs(house, room_id, doors) if prefer_latch and not exterior else []
    if exterior:
        for wall in house.walls.values():
            if wall.floor == room["floor"] and wall.external and room_id in wall.rooms:
                for side in (1, -1):
                    if wall.sides[side] == "outside":
                        pairs.append((wall, side))
    else:
        pairs = [(w, s) for w, s in house.faces_of_room(room_id) if allow_external or not w.external]
    if walls is not None:
        pairs = [(w, s) for w, s in pairs if w.ident in walls]
    for wall, side in pairs:
        span = (0., wall.length) if exterior else house.face_span(wall, side, room_id)
        if not span:
            continue
        lo = span[0] + corner_clear + width / 2
        hi = span[1] - corner_clear - width / 2
        s = lo
        while s <= hi + 1e-9:
            if house.opening_conflict(wall, s, width, z0, z1):
                s += step
                continue
            if not exterior and house.behind_door(wall, side, s, width, room_id):
                s += step
                continue
            if house.blockers(wall, side, s, width, z0, z1, projection, ignore=finishes):
                s += step
                continue
            band = (level + access_band[0], level + access_band[1]) if access_band else (z0 - .1, z1 + .1)
            if access and house.blockers(wall, side, s, width + .1, band[0], band[1], access,
                                         ignore=tuple(finishes) + ("curtain", "detail", "fixture", "downlight", "cove")):
                s += step
                continue
            clash = False
            for other in reserved:
                if other["wallId"] != wall.ident:
                    continue
                gap = (width + other["width"]) / 2 + .08
                if abs(other["along"] - s) < gap:
                    same_side = other["side"] == side
                    vertical_overlap = not (z1 + .05 <= other["z"] - other["height"] / 2 or
                                            z0 - .05 >= other["z"] + other["height"] / 2)
                    deep = other.get("recess", 0) + recess > wall.thickness - .04
                    if (same_side and vertical_overlap) or (not same_side and deep and vertical_overlap):
                        clash = True
                        break
            if clash:
                s += step
                continue
            mount = make_mount(house, wall, side, room_id, s, width, height, zc, recess, finishes=finishes)
            score = 0.
            if target is not None:
                score -= 2.0 * math.dist(mount.face[:2], target)
            if prefer_latch and not exterior:
                score += _latch_score(jambs, mount.face[:2], width)
            if wall.external and not exterior:
                score -= .4      # prefer internal walls for indoor enclosures
            if extra_score:
                score += extra_score(wall, side, s, mount)
            mount.score = score
            out.append(mount)
            s += step
    out.sort(key=lambda m: -m.score)
    return out


def door_jambs(house, room_id, doors=None):
    """Latch and hinge jamb points (plan, on the face toward `room_id`) of the
    doors and cased openings that lead into a room."""
    out = []
    for wall in house.walls.values():
        if wall.floor != house.rooms[room_id]["floor"]:
            continue
        side = next((s for s in (1, -1) if wall.sides[s] == room_id), None)
        for o in wall.openings:
            if o.kind not in ("door", "entry", "cased"):
                continue
            if doors is not None and o.ident not in doors:
                continue
            if doors is None and room_id not in (o.connects or []):
                continue
            face_side = side if side is not None else next(
                (s for s in (1, -1) if wall.sides[s] in (o.connects or [])), 1)
            p0, p1 = wall.point(o.s0, face_side), wall.point(o.s1, face_side)
            if o.kind == "cased":
                out.append({"opening": o.ident, "latch": p0, "hinge": p1, "weight": .6})
                out.append({"opening": o.ident, "latch": p1, "hinge": p0, "weight": .6})
            elif o.hinge == "end":
                out.append({"opening": o.ident, "latch": p0, "hinge": p1, "weight": 1.})
            else:
                out.append({"opening": o.ident, "latch": p1, "hinge": p0, "weight": 1.})
    return out


def _latch_score(jambs, point, width):
    """Reward a face point just beyond the latch jamb (ideal edge gap ~0.15 m)."""
    best = 0.
    for j in jambs:
        lx, ly = j["latch"]
        hx, hy = j["hinge"]
        ux, uy = lx - hx, ly - hy
        n = math.hypot(ux, uy) or 1.
        ux, uy = ux / n, uy / n
        dx, dy = point[0] - lx, point[1] - ly
        ahead = dx * ux + dy * uy
        if ahead < -.02:
            continue
        gap = math.hypot(dx, dy) - width / 2
        if gap < 0 or gap > 1.2:
            continue
        best = max(best, j["weight"] * (3.0 - abs(gap - .15) * 2.5))
    return best


# ---------------------------------------------------------------------------
# Embedded slab conduit router
# ---------------------------------------------------------------------------

class SlabRouter:
    """Orthogonal A* routes through the solid part of one slab.

    `floor` is the storey whose *ceiling* slab is used (0: the first-floor slab,
    1: the roof slab). Slab openings (stair well, double-height void, courts)
    are excluded with a margin. A small cost is added for running directly over
    a wall line (where a beam would normally sit) and for leaving the rooms a
    route serves, so routes cross beams squarely and stay inside served rooms.
    """

    def __init__(self, house, floor, *, grid=.075, margin=.12, wet_penalty=None):
        self.house, self.floor, self.g = house, floor, grid
        roof = next(r for r in house.building["roofs"] if r["floor"] == floor)
        self.regions = [([[x / 1000, y / 1000] for x, y in c["polygon"]],
                         [[[x / 1000, y / 1000] for x, y in h] for h in c.get("holes", [])])
                        for c in roof["ceiling"]]
        xs = [p[0] for poly, _ in self.regions for p in poly]
        ys = [p[1] for poly, _ in self.regions for p in poly]
        self.x0, self.y0 = min(xs), min(ys)
        self.nx = int(math.ceil((max(xs) - self.x0) / grid)) + 1
        self.ny = int(math.ceil((max(ys) - self.y0) / grid)) + 1
        self.margin = margin
        self.free = {}
        self.cost = {}
        walls = [w for w in house.walls.values() if w.floor == floor]
        for i in range(self.nx):
            for j in range(self.ny):
                x, y = self.x0 + i * grid, self.y0 + j * grid
                if not self._solid(x, y):
                    continue
                c = 1.0
                for w in walls:
                    off = abs(w.offset((x, y)))
                    al = w.along((x, y))
                    if off <= w.half + .02 and -.02 <= al <= w.length + .02:
                        c += 1.6
                        break
                room = house.room_at(x, y, floor)
                if wet_penalty and room in wet_penalty:
                    c += wet_penalty[room]
                self.free[(i, j)] = True
                self.cost[(i, j)] = (c, room)

    def _solid(self, x, y):
        for poly, holes in self.regions:
            if inside(x, y, poly) and not any(inside(x, y, h) for h in holes):
                if self._clear(x, y, poly, holes):
                    return True
        return False

    def _clear(self, x, y, poly, holes):
        m = self.margin
        for dx, dy in ((m, 0), (-m, 0), (0, m), (0, -m), (m * .7, m * .7), (-m * .7, m * .7), (m * .7, -m * .7), (-m * .7, -m * .7)):
            if not inside(x + dx, y + dy, poly) or any(inside(x + dx, y + dy, h) for h in holes):
                return False
        return True

    def cell(self, p):
        i = round((p[0] - self.x0) / self.g)
        j = round((p[1] - self.y0) / self.g)
        if (i, j) in self.free:
            return (i, j)
        best = None
        for di in range(-4, 5):
            for dj in range(-4, 5):
                c = (i + di, j + dj)
                if c in self.free:
                    d = math.dist(self.pt(c), p)
                    if best is None or d < best[0]:
                        best = (d, c)
        if best is None:
            raise ValueError(f"Point {p} is not over solid slab on floor {self.floor}")
        return best[1]

    def pt(self, c):
        return (round(self.x0 + c[0] * self.g, 4), round(self.y0 + c[1] * self.g, 4))

    def route(self, start, end, *, rooms=(), turn=4.0, foreign=.35):
        s, e = self.cell(start), self.cell(end)
        if s == e:
            return [tuple(start), tuple(end)]
        dirs = ((1, 0), (-1, 0), (0, 1), (0, -1))
        best = {}
        queue = [(0., 0., s, -1)]
        prev = {}
        rooms = set(rooms)
        goal = None
        while queue:
            f, g, c, d = heapq.heappop(queue)
            if best.get((c, d), math.inf) < g - 1e-9:
                continue
            if c == e:
                goal = (c, d)
                break
            for k, (di, dj) in enumerate(dirs):
                n = (c[0] + di, c[1] + dj)
                if n not in self.free:
                    continue
                step_cost, room = self.cost[n]
                if rooms and room not in rooms:
                    step_cost += foreign
                ng = g + step_cost + (turn if d not in (-1, k) else 0.)
                if ng < best.get((n, k), math.inf):
                    best[(n, k)] = ng
                    prev[(n, k)] = (c, d)
                    h = abs(n[0] - e[0]) + abs(n[1] - e[1])
                    heapq.heappush(queue, (ng + h, ng, n, k))
        if goal is None:
            raise ValueError(f"No slab route on floor {self.floor} from {start} to {end}")
        cells = [goal]
        while cells[-1][0] != s:
            cells.append(prev[cells[-1]])
        cells.reverse()
        pts = [self.pt(c) for c, _ in cells]
        # keep only corners
        simple = [pts[0]]
        for i in range(1, len(pts) - 1):
            a, b, c2 = simple[-1], pts[i], pts[i + 1]
            if (abs(a[0] - b[0]) < 1e-9 and abs(b[0] - c2[0]) < 1e-9) or (abs(a[1] - b[1]) < 1e-9 and abs(b[1] - c2[1]) < 1e-9):
                continue
            simple.append(b)
        simple.append(pts[-1])
        # Connect the exact end points orthogonally to the grid route.
        out = [tuple(start)]
        first = simple[0]
        if abs(first[0] - start[0]) > 1e-6 and abs(first[1] - start[1]) > 1e-6:
            out.append((first[0], start[1]) if len(simple) > 1 and abs(simple[1][1] - first[1]) < 1e-9 else (start[0], first[1]))
        out.extend(simple)
        last = simple[-1]
        if abs(last[0] - end[0]) > 1e-6 and abs(last[1] - end[1]) > 1e-6:
            out.append((end[0], last[1]) if len(simple) > 1 and abs(simple[-2][1] - last[1]) < 1e-9 else (last[0], end[1]))
        out.append(tuple(end))
        clean = [out[0]]
        for p in out[1:]:
            if math.dist(p, clean[-1]) > 1e-6:
                clean.append(p)
        return _drop_collinear(clean)

    def solid_segment(self, a, b, step=.05):
        n = max(1, int(math.dist(a, b) / step))
        for k in range(n + 1):
            t = k / n
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            if not any(inside(x, y, poly) and not any(inside(x, y, h) for h in holes)
                       for poly, holes in self.regions):
                return False
        return True


def _drop_collinear(points):
    out = [points[0]]
    for i in range(1, len(points) - 1):
        a, b, c = out[-1], points[i], points[i + 1]
        cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if abs(cross) < 1e-9 and (b[0] - a[0]) * (c[0] - b[0]) + (b[1] - a[1]) * (c[1] - b[1]) >= 0:
            continue
        out.append(b)
    out.append(points[-1])
    return out
