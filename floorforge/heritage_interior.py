"""Heritage Bungalow interiors (metres, Z up): distemper-painted rooms with moulded cornices, ceiling fans and
period light fittings, and the teak, cane and steel furniture of an old government bungalow.

Only scenes of the heritage-bungalow facade style call this module. Pieces are placed with the shared scene
builder's wall-spot search, so each stands against solid wall, clear of door swings and approaches, low
windows, the stair and the pieces already placed; every group is a movable editable like the other samples.
Bathrooms, the kitchen, stores, the puja room and dressing rooms keep the shared recipes in teak and granite.
"""
from __future__ import annotations

import math

import numpy as np
import trimesh
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from shapely import get_parts

from .plan_geometry import geometry
from .scene_kit import rounded_box


def _polys(geom):
    return [p for p in get_parts(geom) if p.geom_type == 'Polygon' and p.area > 1e-6] if not geom.is_empty else []


class Local:
    """A furniture frame: u along the backing wall (t), v into the room (n), z up from the floor."""

    def __init__(self, k, c, t, n, z, f):
        self.k, self.z, self.f = k, z, f
        self.c, self.t, self.n = np.asarray(c, float), np.asarray(t, float), np.asarray(n, float)
        self.rot = math.atan2(self.t[1], self.t[0])

    def at(self, u, v):
        q = self.c + self.t * u + self.n * v
        return float(q[0]), float(q[1])

    def turn(self, u, v, angle):
        """A frame at (u, v) turned by `angle` (counter-clockwise)."""
        ca, sa = math.cos(angle), math.sin(angle)
        return Local(self.k, self.c + self.t * u + self.n * v, self.t * ca + self.n * sa, -self.t * sa + self.n * ca, self.z, self.f)

    def box(self, u, v, z, size, mat, role='furniture'):
        x, y = self.at(u, v)
        return self.k.node(self.k.cube, mat, (x, y, self.z + z), size, (0, 0, self.rot), self.f, role)

    def rbox(self, u, v, z, size, mat, r=.03, role='furniture', tilt=0.):
        x, y = self.at(u, v)
        key = self.k.asset(rounded_box(size, min(r, min(size) * .35)), smooth=True)
        return self.k.node(key, mat, (x, y, self.z + z), rot=(tilt, 0, self.rot), floor=self.f, role=role)

    def cyl(self, u, v, z, r, h, mat, role='furniture'):
        x, y = self.at(u, v)
        return self.k.cylinder((x, y, self.z + z), r, h, mat, self.f, role)

    def rod(self, u0, v0, z0, u1, v1, z1, r, mat, role='furniture'):
        a, b = self.at(u0, v0), self.at(u1, v1)
        return self.k.beam((a[0], a[1], self.z + z0), (b[0], b[1], self.z + z1), r, mat, self.f, role)

    def ball(self, u, v, z, size, mat, role='furniture'):
        x, y = self.at(u, v)
        return self.k.ball((x, y, self.z + z), size, mat, self.f, role, (0, 0, self.rot))

    def lathe(self, u, v, z, profile, mat, role='detail', sections=24):
        x, y = self.at(u, v)
        mesh = trimesh.creation.revolve(np.array(profile, float), sections=sections)
        return self.k.node(self.k.asset(mesh, smooth=True), mat, (x, y, self.z + z), floor=self.f, role=role)

    def disc(self, u, v, z, r, depth, mat, role='detail'):
        """A disc standing against the wall plane, facing +v (a clock dial, a plate on a shelf)."""
        x, y = self.at(u, v)
        return self.k.node(self.k.cyl, mat, (x, y, self.z + z), (r, r, depth), (math.pi / 2, 0, self.rot), self.f, role)

    def lying(self, u, v, z, r, length, mat, along='u', role='furniture'):
        """A cylinder lying along u or v (bolsters, tube lights, rods)."""
        x, y = self.at(u, v)
        rot = (0, math.pi / 2, self.rot) if along == 'u' else (0, math.pi / 2, self.rot + math.pi / 2)
        return self.k.node(self.k.cyl, mat, (x, y, self.z + z), (r, r, length), rot, self.f, role)

    def poly(self, u0, u1, v0, v1):
        return Polygon([self.at(u0, v0), self.at(u1, v0), self.at(u1, v1), self.at(u0, v1)])


# --------------------------------------------------------------------------------------------- furniture recipes
def teak_sofa(F, length, seats, fabric='fabric', accent='fabric-dark', frame='hb-teak'):
    """A slatted teak sofa with loose seat and back cushions (back at v=0, seat facing +v)."""
    h = length / 2
    for u in (-h + .04, h - .04):
        F.box(u, .06, .43, (.065, .065, .86), frame)
        F.box(u, .76, .31, (.065, .065, .62), frame)
        F.rbox(u, .41, .635, (.11, .84, .036), frame, .012)
        F.box(u, .41, .2, (.05, .7, .05), frame)
        for v in np.arange(.15, .7, .085):
            F.box(u, v, .41, (.03, .022, .38), frame)
    F.box(0, .76, .3, (length - .08, .045, .09), frame)
    F.box(0, .06, .3, (length - .08, .045, .09), frame)
    F.rbox(0, .06, .83, (length - .02, .055, .07), frame, .015)
    for u in np.arange(-h + .16, h - .1, .1):
        F.box(u, .07, .56, (.04, .022, .46), frame)
    width = (length - .2) / seats
    for i in range(seats):
        u = -h + .1 + width * (i + .5)
        F.rbox(u, .44, .41, (width - .015, .64, .14), fabric, .045)
        F.rbox(u, .19, .66, (width - .05, .15, .42), fabric, .05, tilt=.16)
    for su in ((-1, 1) if seats > 1 else (1,)):
        F.rbox(su * (h - .32) if seats > 1 else 0, .3, .63, (.4, .13, .4), accent, .06, tilt=.24)


def cane_sofa(F, length, seats, cushion='hb-print'):
    """A cane sofa: bent-cane frame, woven back and arms, flat cushions."""
    h = length / 2
    for u in (-h + .05, h - .05):
        for v in (.08, .72):
            F.cyl(u, v, .3, .022, .6, 'hb-bamboo')
        F.rod(u, .08, .62, u, .74, .62, .03, 'hb-bamboo')
        F.box(u, .4, .44, (.02, .62, .34), 'hb-cane', 'furniture')
    F.rod(-h + .05, .08, .84, h - .05, .08, .84, .03, 'hb-bamboo')
    F.box(0, .1, .6, (length - .14, .02, .46), 'hb-cane')
    F.box(0, .42, .33, (length - .1, .66, .06), 'hb-cane')
    width = (length - .16) / seats
    for i in range(seats):
        u = -h + .08 + width * (i + .5)
        F.rbox(u, .44, .4, (width - .02, .6, .09), cushion, .035)
        F.rbox(u, .18, .62, (width - .08, .1, .36), cushion, .04, tilt=.15)


def centre_table(F, u, v, length=1.15, depth=.62, top='hb-teak'):
    """A low teak table with a lower shelf, a lace runner and a brass bowl."""
    F.rbox(u, v, .425, (length, depth, .035), top, .012)
    for su in (-1, 1):
        for sv in (-1, 1):
            F.box(u + su * (length / 2 - .05), v + sv * (depth / 2 - .05), .205, (.045, .045, .41), 'hb-teak')
    F.box(u, v, .1, (length - .1, depth - .1, .02), 'hb-teak')
    F.box(u, v, .4435, (length * .5, depth * .6, .002), 'linen', 'detail')
    F.lathe(u + .12, v, .444, [[0, 0], [.05, 0], [.11, .05], [.12, .08], [.105, .08], [.001, .02]], 'hb-brass')
    F.ball(u + .12, v - .03, .5, (.04, .04, .04), 'hb-pot-red', 'detail')
    F.ball(u + .15, v + .02, .5, (.035, .035, .035), 'hb-sign-yellow', 'detail')


def showcase(F, width=1.5, depth=.42, height=1.95):
    """A teak showcase: glass-fronted upper shelves with plates, brass and trophies over a closed cupboard."""
    w = width
    F.box(0, .012, height / 2, (w, .024, height), 'hb-teak')
    for su in (-1, 1):
        F.box(su * (w / 2 - .012), depth / 2, height / 2, (.024, depth, height), 'hb-teak')
    F.rbox(0, depth / 2 + .01, height - .02, (w + .05, depth + .04, .04), 'hb-teak-dark', .01)
    F.box(0, depth / 2, .05, (w - .03, depth - .03, .1), 'hb-teak-dark')
    F.box(0, depth - .012, .5, (w - .05, .024, .78), 'hb-teak')
    F.box(0, depth - .002, .5, (.006, .004, .74), 'hb-teak-dark')
    for su in (-1, 1):
        F.ball(su * .05, depth + .004, .62, (.018, .018, .018), 'hb-brass')
    for zz in (.9, 1.27, 1.62):
        F.box(0, depth / 2, zz, (w - .05, depth - .05, .022), 'hb-teak')
    F.box(0, depth - .01, 1.4, (w - .05, .006, .98), 'hb-glass', 'glass')
    F.box(0, depth - .004, 1.4, (.02, .02, .98), 'hb-teak-dark')
    for zz in (.92, 1.88):
        F.box(0, depth - .004, zz, (w - .05, .03, .03), 'hb-teak-dark')
    # Contents: rows of plates on edge, cups, brass pots, a trophy and a doll.
    for j, uu in enumerate(np.arange(-w / 2 + .15, w / 2 - .1, .19)):
        F.disc(uu, .1, 1.04, .1, .012, 'ceramic' if j % 2 else 'hb-plate-text')
        F.lathe(uu, .26, 1.282, [[0, 0], [.035, 0], [.045, .07], [.04, .07], [.001, .01]], 'ceramic' if j % 3 else 'hb-pot-pink')
    for j, uu in enumerate((-w / 2 + .25, 0, w / 2 - .25)):
        F.lathe(uu, depth / 2, 1.632, [[0, 0], [.05, 0], [.08, .06], [.07, .12], [.035, .15], [.05, .18], [.001, .18]], 'hb-brass')
    F.lathe(w / 2 - .45, depth / 2, 1.632, [[0, 0], [.05, 0], [.05, .02], [.012, .04], [.012, .16], [.06, .2], [.07, .27], [.001, .27]], 'hb-brass')


def diwan(F, length=1.95, depth=.85):
    """A low teak diwan with a printed mattress, round bolsters and wall cushions."""
    for su in (-1, 1):
        for sv in (.05, depth - .05):
            F.box(su * (length / 2 - .05), sv, .14, (.07, .07, .28), 'hb-teak')
    F.box(0, depth / 2, .26, (length, depth, .06), 'hb-teak')
    F.box(0, depth - .015, .2, (length - .1, .03, .1), 'hb-teak-dark')
    F.rbox(0, depth / 2, .36, (length - .04, depth - .04, .14), 'hb-print', .05)
    for su in (-1, 1):
        F.lying(su * (length / 2 - .2), depth / 2 + .05, .5, .1, depth - .2, 'fabric', along='v')
    for uu in (-.45, .45):
        F.rbox(uu, .13, .6, (.5, .14, .45), 'fabric-dark' if uu < 0 else 'fabric', .07, tilt=.22)


def radio_table(F):
    """A turned-leg side table with a valve radio: teak cabinet, cloth grille and a dial."""
    F.rbox(0, .22, .6, (.5, .42, .03), 'hb-teak', .01)
    for su in (-1, 1):
        for sv in (-1, 1):
            F.cyl(su * .2, .22 + sv * .16, .3, .02, .6, 'hb-teak')
    F.rbox(0, .2, .78, (.44, .22, .33), 'hb-teak-dark', .03)
    F.box(-.06, .312, .8, (.22, .004, .2), 'hb-khus', 'detail')
    F.box(.13, .312, .82, (.1, .004, .06), 'hb-plate-text', 'detail')
    for uu in (.1, .16):
        F.disc(uu, .315, .7, .018, .015, 'hb-brass')


def dining_table(F, u, v, length, depth):
    """A teak dining table on turned legs (long axis along u)."""
    F.rbox(u, v, .755, (length, depth, .04), 'hb-teak', .015)
    F.box(u, v, .69, (length - .14, depth - .14, .09), 'hb-teak-dark')
    for su in (-1, 1):
        for sv in (-1, 1):
            x, y = u + su * (length / 2 - .09), v + sv * (depth / 2 - .09)
            F.lathe(x, y, 0, [[0, 0], [.03, 0], [.035, .1], [.025, .14], [.04, .32], [.022, .5], [.03, .62], [.035, .66], [.001, .66]], 'hb-teak', 'furniture', 16)
    # A steel water jug with glasses, a fruit bowl and a table runner.
    F.box(u, v, .7765, (length * .7, .32, .003), 'hb-durrie', 'detail')
    F.lathe(u - .25, v, .776, [[0, 0], [.06, 0], [.07, .14], [.05, .2], [.055, .23], [.001, .23]], 'hb-steel')
    for du in (-.12, -.38):
        F.lathe(u + du, v + .08, .776, [[0, 0], [.028, 0], [.035, .11], [.001, .11]], 'hb-steel')
    F.lathe(u + .3, v, .776, [[0, 0], [.07, 0], [.14, .07], [.001, .02]], 'hb-brass')
    for j, (du, dv) in enumerate(((.27, .03), (.33, -.03), (.3, .05))):
        F.ball(u + du, v + dv, .84, (.045, .045, .045), ('hb-pot-red', 'hb-sign-yellow', 'hb-pot-red')[j], 'detail')


def cane_chair(F, arms=False):
    """A teak dining chair with a woven cane seat and back panel (seat centred at the origin, facing -v)."""
    for su in (-1, 1):
        F.box(su * .2, -.19, .225, (.04, .04, .45), 'hb-teak')
        F.box(su * .2, .2, .48, (.04, .04, .96), 'hb-teak')
    F.box(0, 0, .45, (.46, .44, .035), 'hb-teak')
    F.box(0, 0, .47, (.38, .36, .008), 'hb-cane')
    F.box(0, .2, .93, (.44, .04, .06), 'hb-teak')
    F.box(0, .2, .72, (.34, .012, .34), 'hb-cane')
    for zz in (.15,):
        F.box(0, -.19, zz, (.4, .025, .03), 'hb-teak')
        F.box(0, .2, zz, (.4, .025, .03), 'hb-teak')
    if arms:
        for su in (-1, 1):
            F.box(su * .23, 0, .68, (.05, .44, .03), 'hb-teak')


def moodha(F, u, v, z0=0.):
    """A cane moodha: an hourglass stool of woven cane with a padded top."""
    F.lathe(u, v, z0, [[0, 0], [.2, 0], [.2, .02], [.12, .22], [.18, .4], [.19, .42], [.001, .42]], 'hb-cane', 'furniture', 20)


def plastic_chair_stack(k, F, u, v, count=4):
    from .heritage_scene import plastic_chair
    for i in range(count):
        x, y = F.at(u, v)
        plastic_chair(k, x, y, F.z + i * .045, F.rot + math.pi, F.f)


def teak_bed(F, width, length=2.05):
    """A teak double bed: tall panelled headboard with a crest rail, low footboard, printed bedspread."""
    w = width
    for su in (-1, 1):
        F.box(su * (w / 2 + .03), .04, .58, (.08, .08, 1.16), 'hb-teak')
        F.ball(su * (w / 2 + .03), .04, 1.19, (.05, .05, .05), 'hb-teak-dark')
        F.box(su * (w / 2 + .03), length + .03, .3, (.08, .08, .6), 'hb-teak')
        F.box(su * (w / 2 + .01), length / 2 + .04, .3, (.04, length, .18), 'hb-teak')
    F.box(0, .04, .76, (w, .04, .68), 'hb-teak')
    for uu in (-w / 4, w / 4):
        F.box(uu, .065, .78, (w / 2 - .16, .01, .5), 'hb-teak-dark')
    F.rbox(0, .04, 1.12, (w + .2, .08, .08), 'hb-teak-dark', .02)
    F.box(0, length + .03, .42, (w, .04, .3), 'hb-teak')
    F.box(0, length / 2 + .04, .24, (w, length, .05), 'hb-teak-dark')
    F.rbox(0, length / 2 + .05, .38, (w - .04, length - .05, .2), 'linen', .06)
    F.rbox(0, length / 2 + .28, .49, (w + .04, length - .48, .035), 'hb-print', .015)
    for su in (-1, 1):
        F.box(su * (w / 2 + .025), length / 2 + .28, .39, (.01, length - .48, .2), 'hb-print', 'furniture')
    for su in (-1, 1):
        F.rbox(su * w / 4, .3, .54, (w / 2 - .14, .4, .13), 'linen', .06)
    F.lying(0, length - .25, .55, .09, w - .5, 'fabric', along='u')


def side_table(F, u, v, lamp=True):
    F.rbox(u, v, .56, (.46, .4, .03), 'hb-teak', .01)
    F.box(u, v, .32, (.42, .36, .44), 'hb-teak')
    F.box(u, v + .181, .45, (.36, .004, .12), 'hb-teak-dark', 'detail')
    F.ball(u, v + .19, .45, (.014, .014, .014), 'hb-brass', 'detail')
    if lamp:
        F.lathe(u, v, .575, [[0, 0], [.07, 0], [.07, .02], [.025, .05], [.045, .15], [.012, .25], [.012, .34], [.001, .34]], 'hb-brass', 'fixture')
        F.lathe(u, v, .86, [[.09, 0], [.15, 0], [.15, .004], [.1, .2], [.095, .2], [.088, .004]], 'linen', 'fixture')


def almirah(F, width=.92, depth=.52, height=1.98):
    """The steel almirah of every Indian bedroom: grey-green enamel, a centre handle and a keyhole."""
    F.rbox(0, depth / 2, height / 2 + .04, (width, depth, height - .08), 'hb-almirah', .012)
    F.box(0, depth / 2, .04, (width - .08, depth - .06, .08), 'hb-grille-dark')
    F.box(0, depth + .001, height / 2 + .05, (.006, .004, height - .22), 'hb-grille-dark', 'detail')
    for zz in (.25, height - .2):
        F.box(0, depth + .001, zz, (width - .1, .004, .006), 'hb-grille-dark', 'detail')
    F.rbox(.07, depth + .018, 1.05, (.026, .03, .2), 'hb-steel', .01)
    F.disc(.07, depth + .004, 1.2, .012, .008, 'hb-brass')


def dresser(F, width=1.0):
    """A teak dressing table with a tall mirror, drawers and a cane stool."""
    F.box(0, .23, .37, (width, .45, .74), 'hb-teak')
    F.rbox(0, .24, .755, (width + .04, .48, .03), 'hb-teak-dark', .01)
    for j in range(3):
        F.box(width / 2 - .19, .457, .14 + j * .21, (.34, .01, .18), 'hb-teak-dark', 'detail')
        F.ball(width / 2 - .19, .466, .14 + j * .21, (.016, .016, .016), 'hb-brass', 'detail')
    F.box(-width / 4 + .02, .457, .38, (width / 2 - .1, .01, .62), 'hb-teak-dark', 'detail')
    F.box(0, .04, 1.36, (width * .66, .045, 1.08), 'hb-teak')
    F.box(0, .065, 1.36, (width * .58, .006, .98), 'hb-mirror', 'mirror')
    for j, uu in enumerate((-.3, -.22, -.15, .25)):
        F.lathe(uu, .3, .77, [[0, 0], [.025, 0], [.03, .08], [.012, .12], [.012, .15], [.001, .15]], ('hb-pot-pink', 'hb-glass', 'hb-brass', 'ceramic')[j])
    F.lathe(0, .82, 0, [[0, 0], [.17, 0], [.17, .02], [.12, .38], [.18, .42], [.19, .46], [.001, .46]], 'hb-cane', 'furniture', 20)


def easy_chair(F):
    """An aaram-kursi: a teak planter's chair with long arms and a reclined cane sling (facing +v)."""
    for su in (-1, 1):
        F.box(su * .29, .08, .3, (.05, .05, .6), 'hb-teak')
        F.box(su * .29, .82, .2, (.05, .05, .4), 'hb-teak')
        F.rbox(su * .29, .62, .6, (.09, 1.15, .035), 'hb-teak', .012)
        F.box(su * .29, .45, .14, (.04, .8, .04), 'hb-teak')
    F.rbox(0, .5, .33, (.52, .62, .02), 'hb-cane', .006, tilt=.18)
    F.rbox(0, .2, .62, (.52, .5, .02), 'hb-cane', .006, tilt=.75)
    F.box(0, .82, .38, (.56, .04, .05), 'hb-teak')
    F.box(0, .02, .9, (.56, .04, .05), 'hb-teak')


def ceiling_fan(k, x, y, ceiling, f, mat='hb-fan', drop=.45, phase=0.):
    """A three-blade ceiling fan on a downrod."""
    k.cylinder((x, y, ceiling - .03), .07, .06, mat, f, 'fixture')
    k.beam((x, y, ceiling - .05), (x, y, ceiling - drop), .012, mat, f, 'fixture')
    z = ceiling - drop - .05
    k.cylinder((x, y, z), .11, .1, mat, f, 'fixture')
    k.ball((x, y, z - .06), (.07, .07, .03), mat, f, 'fixture')
    for i in range(3):
        a = phase + i * 2 * math.pi / 3
        ca, sa = math.cos(a), math.sin(a)
        k.node(k.cube, mat, (x + ca * .17, y + sa * .17, z + .01), (.14, .03, .012), (0, 0, a), f, 'fixture')
        k.node(k.cube, mat, (x + ca * .42, y + sa * .42, z + .02), (.5, .105, .006), (.1, 0, a), f, 'fixture')


def tube_light(F, u, z, power=20):
    """A fluorescent batten on the wall (F's wall at v=0)."""
    F.box(u, .03, z, (1.24, .05, .06), 'hb-white-steel', 'fixture')
    F.lying(u, .06, z - .01, .014, 1.18, 'hb-tube', along='u', role='fixture')
    x, y = F.at(u, .35)
    F.k.light((x, y, F.z + z - .1), power, color='#f2f6ff', kind='wall')


def bowl_light(k, x, y, ceiling, f, power=14):
    """A frosted glass bowl on a short brass rod."""
    k.beam((x, y, ceiling - .01), (x, y, ceiling - .2), .006, 'hb-brass', f, 'fixture')
    k.cylinder((x, y, ceiling - .02), .05, .03, 'hb-brass', f, 'fixture')
    mesh = trimesh.creation.revolve(np.array([[.001, 0], [.1, .02], [.16, .09], [.17, .12], [.001, .12]]), sections=28)
    k.node(k.asset(mesh, smooth=True), 'hb-globe', (x, y, ceiling - .32), floor=f, role='fixture')
    k.light((x, y, ceiling - .35), power, kind='pendant')


def chandelier(k, x, y, ceiling, f):
    """A brass chandelier: a turned stem and six curved arms with glass tulip shades."""
    hub = ceiling - .75
    k.cylinder((x, y, ceiling - .03), .08, .05, 'hb-brass', f, 'fixture')
    k.beam((x, y, hub), (x, y, ceiling - .04), .01, 'hb-brass', f, 'fixture')
    k.ball((x, y, hub + .12), (.06, .06, .09), 'hb-brass', f, 'fixture')
    k.ball((x, y, hub), (.09, .09, .07), 'hb-brass', f, 'fixture')
    tulip = k.asset(trimesh.creation.revolve(np.array([[.001, 0], [.03, 0], [.06, .05], [.07, .13], [.055, .13], [.045, .06], [.001, .02]]), sections=20), smooth=True)
    for i in range(6):
        a = i * math.pi / 3
        ex, ey = x + math.cos(a) * .36, y + math.sin(a) * .36
        mx, my = x + math.cos(a) * .2, y + math.sin(a) * .2
        k.beam((x, y, hub), (mx, my, hub - .08), .008, 'hb-brass', f, 'fixture')
        k.beam((mx, my, hub - .08), (ex, ey, hub + .02), .008, 'hb-brass', f, 'fixture')
        k.node(tulip, 'hb-globe', (ex, ey, hub + .02), floor=f, role='fixture')
    k.light((x, y, hub - .1), 45, kind='chandelier')


def lantern(k, x, y, ceiling, f, drop=1.0):
    """A brass hanging lantern with glass panes."""
    z = ceiling - drop
    k.beam((x, y, z + .3), (x, y, ceiling - .02), .006, 'hb-brass', f, 'fixture')
    k.cylinder((x, y, z + .27), .12, .04, 'hb-brass', f, 'fixture')
    k.cylinder((x, y, z), .1, .02, 'hb-brass', f, 'fixture')
    k.cylinder((x, y, z + .14), .095, .24, 'hb-globe', f, 'fixture')
    for i in range(4):
        a = i * math.pi / 2 + math.pi / 4
        k.beam((x + math.cos(a) * .1, y + math.sin(a) * .1, z), (x + math.cos(a) * .11, y + math.sin(a) * .11, z + .28), .006, 'hb-brass', f, 'fixture')
    k.light((x, y, z + .1), 30, kind='pendant')


def wall_clock(F, u, z, pendulum=False):
    if pendulum:
        F.box(u, .05, z - .2, (.32, .1, .78), 'hb-teak-dark', 'art')
        F.box(u, .101, z - .38, (.2, .004, .34), 'hb-glass', 'art')
        F.rod(u, .09, z - .2, u, .09, z - .48, .004, 'hb-brass', 'detail')
        F.disc(u, .09, z - .5, .05, .008, 'hb-brass')
        F.disc(u, .102, z, .12, .006, 'hb-plate-text')
    else:
        F.disc(u, .025, z, .17, .05, 'hb-teak-dark')
        F.disc(u, .052, z, .15, .006, 'hb-plate-text')
    F.box(u + .03, .108 if pendulum else .058, z + .02, (.07, .004, .012), 'hb-plate', 'detail')
    F.box(u, .108 if pendulum else .058, z + .05, (.01, .004, .1), 'hb-plate', 'detail')


def framed_picture(F, u, z, width, height, art='art'):
    F.box(u, .015, z, (width, .03, height), 'hb-teak-dark', 'art')
    F.box(u, .032, z, (width - .1, .004, height - .1), 'hb-plate-text', 'art')
    F.box(u, .036, z, (width - .16, .004, height - .16), art, 'art')


def carrom(F, u, v):
    """A carrom board on a folding stand, with coins in the centre circle."""
    for su in (-1, 1):
        for sv in (-1, 1):
            F.rod(u + su * .3, v + sv * .3, 0, u - su * .1, v - sv * .1, .64, .015, 'hb-teak')
    F.box(u, v, .67, (.86, .86, .03), 'hb-teak-dark')
    F.box(u, v, .687, (.74, .74, .006), 'hb-cane')
    for su in (-1, 1):
        for sv in (-1, 1):
            F.cyl(u + su * .34, v + sv * .34, .689, .022, .003, 'hb-plate')
    for i in range(9):
        a = i * 2 * math.pi / 9
        F.cyl(u + math.cos(a) * .04, v + math.sin(a) * .04, .692, .015, .006, 'hb-plate' if i % 2 else 'hb-plate-text')
    F.cyl(u, v, .692, .015, .006, 'hb-pot-red')


def tv_cabinet(F, width=1.3):
    """A teak television cabinet with its shutters closed over the set, a crocheted runner and a vase on top."""
    F.box(0, .25, .6, (width, .5, 1.0), 'hb-teak')
    for su in (-1, 1):
        for sv in (.05, .45):
            F.box(su * (width / 2 - .05), sv, .05, (.05, .05, .1), 'hb-teak-dark')
        F.box(su * width / 4, .502, .78, (width / 2 - .05, .006, .5), 'hb-teak-dark', 'detail')
        F.box(su * width / 4, .505, .78, (width / 2 - .17, .006, .38), 'hb-teak', 'detail')
        F.ball(su * .05, .52, .78, (.016, .016, .016), 'hb-brass', 'detail')
        F.box(su * width / 4, .502, .32, (width / 2 - .05, .006, .3), 'hb-teak-dark', 'detail')
    F.rbox(0, .26, 1.115, (width + .04, .54, .03), 'hb-teak-dark', .01)
    F.box(0, .26, 1.132, (width * .7, .36, .002), 'linen', 'detail')
    F.lathe(-.35, .26, 1.133, [[0, 0], [.05, 0], [.08, .08], [.05, .2], [.06, .26], [.001, .26]], 'ceramic')
    F.rbox(.25, .26, 1.24, (.4, .18, .22), 'hb-plate', .03)
    F.disc(.33, .352, 1.24, .05, .01, 'hb-steel')
    F.disc(.17, .352, 1.24, .05, .01, 'hb-steel')


def bookcase(F, width=1.2, height=2.0, depth=.36):
    F.box(0, .01, height / 2, (width, .02, height), 'hb-teak')
    for su in (-1, 1):
        F.box(su * (width / 2 - .01), depth / 2, height / 2, (.02, depth, height), 'hb-teak')
    colours = ('hb-pot-red', 'fabric-dark', 'hb-teak-dark', 'hb-leather', 'hb-sign-yellow', 'hb-plate-text', 'hb-durrie')
    for j, zz in enumerate(np.linspace(.08, height - .02, 6)):
        F.box(0, depth / 2, zz, (width - .02, depth - .02, .02), 'hb-teak')
        if j < 5 and zz < height - .3:
            u = -width / 2 + .05
            i = 0
            while u < width / 2 - .08:
                bw = .03 + .015 * ((i * 7 + j * 3) % 3)
                bh = .22 + .04 * ((i * 5 + j) % 3)
                F.box(u + bw / 2, depth / 2 + .02, zz + .01 + bh / 2, (bw - .003, depth - .1, bh), colours[(i + j * 2) % len(colours)], 'detail')
                u += bw
                i += 1
                if i % 9 == 8:
                    u += .1


def office_desk(F, u, v, width=1.7, depth=.9):
    """A large teak officer's desk with a glass top, drawer pedestals, a blotter, a rotary phone and files."""
    for su in (-1, 1):
        F.box(u + su * (width / 2 - .22), v, .37, (.42, depth - .04, .74), 'hb-teak')
        for j in range(3):
            F.box(u + su * (width / 2 - .22), v - depth / 2 + .02, .14 + j * .22, (.36, .01, .18), 'hb-teak-dark', 'detail')
    F.box(u, v + depth / 2 - .04, .5, (width - .9, .02, .45), 'hb-teak')
    F.rbox(u, v, .755, (width, depth, .03), 'hb-teak-dark', .01)
    F.box(u, v, .773, (width - .04, depth - .04, .006), 'hb-glass', 'glass')
    F.box(u, v - .05, .7775, (.6, .42, .003), 'hb-leather', 'detail')
    F.rbox(u + .55, v - .15, .82, (.2, .22, .08), 'hb-plate', .03)
    F.disc(u + .55, v - .26, .82, .05, .01, 'hb-plate-text')
    for j in range(4):
        F.box(u - .58, v + .1, .79 + j * .03, (.26, .34, .028), ('hb-sign-yellow', 'hb-plate-text', 'hb-sign-yellow', 'fabric-dark')[j], 'detail')
    F.lathe(u - .25, v + .3, .776, [[0, 0], [.07, 0], [.07, .015], [.012, .03], [.012, .3], [.001, .3]], 'hb-brass', 'fixture')
    F.rbox(u - .25, v + .22, 1.08, (.36, .14, .1), 'hb-leather', .05, 'fixture')


def office_chair(F, u, v, executive=True):
    """A high-back revolving chair upholstered in green leather (facing -v)."""
    for i in range(5):
        a = i * 2 * math.pi / 5
        F.rod(u, v, .07, u + math.cos(a) * .3, v + math.sin(a) * .3, .04, .016, 'hb-steel')
    F.cyl(u, v, .25, .028, .36, 'hb-steel')
    F.rbox(u, v, .48, (.54, .52, .1), 'hb-leather', .04)
    F.rbox(u, v + .25, .88 if executive else .75, (.54, .1, .8 if executive else .55), 'hb-leather', .05, tilt=.1)
    for su in (-1, 1):
        F.rbox(u + su * .29, v + .02, .66, (.06, .42, .05), 'hb-teak-dark', .015)


def charpai(F, u, v, length=1.9, width=.9):
    """A charpai: a string cot on turned legs."""
    for su in (-1, 1):
        for sv in (-1, 1):
            F.lathe(u + su * (length / 2 - .04), v + sv * (width / 2 - .04), 0,
                    [[0, 0], [.04, 0], [.045, .08], [.03, .14], [.045, .25], [.03, .4], [.03, .44], [.001, .44]], 'hb-teak', 'furniture', 12)
    for sv in (-1, 1):
        F.box(u, v + sv * (width / 2 - .04), .4, (length, .05, .06), 'hb-teak')
    for su in (-1, 1):
        F.box(u + su * (length / 2 - .04), v, .4, (.05, width, .06), 'hb-teak')
    F.box(u, v, .41, (length - .1, width - .1, .012), 'hb-khus')


def swing(F, u, v, ceiling, length=1.45, depth=.6):
    """A teak jhoola hanging from the ceiling on four brass chains (seat facing +v)."""
    seat = .45
    for su in (-1, 1):
        F.box(u + su * (length / 2 - .03), v, seat + .17, (.05, depth, .04), 'hb-teak')
        for sv in (-1, 1):
            F.rod(u + su * (length / 2 - .06), v + sv * (depth / 2 - .05), seat + .02, u + su * (length / 2 - .06), v + sv * (depth / 2 - .05), ceiling - .02, .005, 'hb-brass')
            x, y = F.at(u + su * (length / 2 - .06), v + sv * (depth / 2 - .05))
            F.k.cylinder((x, y, F.z + ceiling - .03), .03, .03, 'hb-brass', F.f, 'fixture')
    F.rbox(u, v, seat, (length, depth, .05), 'hb-teak', .012)
    F.rbox(u, v - depth / 2 + .06, seat + .3, (length - .06, .04, .5), 'hb-teak', .012, tilt=.12)
    F.rbox(u, v + .02, seat + .05, (length - .14, depth - .14, .05), 'hb-print', .02)
    for su in (-1, 1):
        F.rbox(u + su * (length / 2 - .3), v - depth / 2 + .13, seat + .27, (.36, .1, .34), 'fabric', .05, tilt=.25)


def clothesline(k, a, c, z0, height, f):
    """Two GI pipe T-posts with three lines and a few clothes pegged on them."""
    a, c = np.asarray(a, float), np.asarray(c, float)
    d = c - a
    L = float(np.linalg.norm(d))
    if L < 1.2:
        return
    u = d / L
    nrm = np.array([-u[1], u[0]])
    for p in (a, c):
        k.cylinder((p[0], p[1], z0 + height / 2), .022, height, 'hb-steel', f, 'outdoor-furniture')
        q0, q1 = p - nrm * .35, p + nrm * .35
        k.beam((q0[0], q0[1], z0 + height), (q1[0], q1[1], z0 + height), .015, 'hb-steel', f, 'outdoor-furniture')
    for s in (-.3, 0, .3):
        p0, p1 = a + nrm * s, c + nrm * s
        k.beam((p0[0], p0[1], z0 + height - .01), (p1[0], p1[1], z0 + height - .01), .002, 'hb-rope', f, 'detail')
    colours = ('hb-print', 'linen', 'fabric-dark', 'hb-durrie', 'hb-curtain')
    t = .4
    i = 0
    while t < L - .5:
        s = (-.3, 0, .3)[i % 3]
        w = .45 + .2 * (i % 2)
        drop = .55 + .2 * ((i * 3) % 2)
        p = a + u * (t + w / 2) + nrm * s
        k.node(k.cube, colours[i % len(colours)], (p[0], p[1], z0 + height - .01 - drop / 2), (w, .006, drop),
               (0, 0, math.atan2(u[1], u[0])), f, 'detail')
        t += w + .25
        i += 1


# ------------------------------------------------------------------------------------------------------- rooms
class HeritageInterior:
    def __init__(self, hs, tools):
        self.hs, self.t = hs, tools
        self.k, self.b, self.H = hs.k, hs.b, hs.H
        self.metres = hs.metres
        self.hosts = hs.hosts

    # ----------------------------------------------------------------------------------------- shell dressing
    def ceiling(self, room):
        f = room['floor']
        return f * self.H + self.H - .157

    def clear(self, room):
        return Polygon(np.array(room['clear']) / 1000)

    def openings_of(self, room):
        """(opening, exact plan rectangle in metres) for every opening in the walls of this room's floor."""
        out = []
        for o in self.b['openings']:
            if o['floor'] != room['floor']:
                continue
            w = self.hosts[o['wall_id']]
            a = np.array(w['a'], float) / 1000
            c = np.array(w['b'], float) / 1000
            u = (c - a) / np.linalg.norm(c - a)
            n = np.array([-u[1], u[0]])
            p = a + u * o['offset'] / 1000
            q = p + u * o['width'] / 1000
            t = w['thickness'] / 1000 + .3
            out.append((o, Polygon([p - n * t, q - n * t, q + n * t, p + n * t])))
        return out

    def paint(self, room, lo=.09):
        """Distemper lining on the room's walls, cut exactly at every door, window and arch, plus a cornice."""
        name = room.get('wallPaint')
        if not name:
            return
        k = self.k
        f = room['floor']
        z = f * self.H
        top = self.ceiling(room)
        clear = self.clear(room)
        walls = self.t.wall_union[f]
        ring = clear.difference(clear.buffer(-.006, join_style=2)).intersection(walls.buffer(.026, join_style=2))
        ops = [(o, poly) for o, poly in self.openings_of(room) if poly.intersects(ring)]
        cuts = {z + lo, top}
        for o, _ in ops:
            for zz in (o['sill'] / 1000, (o['sill'] + o['height']) / 1000):
                if lo < zz < top - z:
                    cuts.add(z + zz)
        cuts = sorted(cuts)
        for i, (z0, z1) in enumerate(zip(cuts, cuts[1:])):
            mid = (z0 + z1) / 2 - z
            geom = ring
            for o, poly in ops:
                if o['sill'] / 1000 <= mid <= (o['sill'] + o['height']) / 1000:
                    geom = geom.difference(poly)
            for part in _polys(geom):
                k.poly_mesh(part, z0, z1, 'paint-' + name, f, 'wall-panel', owner=room['id'])
        # A two-step moulded cornice where walls meet the ceiling.
        for depth, z0, z1 in ((.05, top - .06, top), (.025, top - .11, top - .06)):
            band = clear.difference(clear.buffer(-depth, join_style=2)).intersection(walls.buffer(depth + .02, join_style=2))
            for o, poly in ops:
                if (o['sill'] + o['height']) / 1000 > z0 - z:
                    band = band.difference(poly)
            for part in _polys(band):
                k.poly_mesh(part, z0, z1, 'hb-limewash', f, 'wall-panel', owner=room['id'])
        # Door architraves in teak on this room's side.
        for o, poly in ops:
            if o['kind'] not in ('door', 'entry') or o.get('timberScreen') or o.get('grille'):
                continue
            frame = poly.intersection(clear.buffer(.001)).buffer(0)
            if frame.is_empty or frame.area < 1e-4:
                continue
            w = self.hosts[o['wall_id']]
            a = np.array(w['a'], float) / 1000
            c = np.array(w['b'], float) / 1000
            u = (c - a) / np.linalg.norm(c - a)
            n = np.array([-u[1], u[0]])
            p = a + u * o['offset'] / 1000
            mid = p + u * o['width'] / 2000
            face = w['thickness'] / 2000
            if not clear.buffer(.05).contains(Point(*(mid + n * (face + .03)))):
                n = -n
            F = Local(k, p + n * face, u, n, z, f)
            ow, oh = o['width'] / 1000, (o['sill'] + o['height']) / 1000
            for uu in (-.04, ow + .04):
                F.box(uu, .012, oh / 2 + .03, (.08, .024, oh + .06), 'hb-teak-dark', 'wall-panel')
            F.box(ow / 2, .012, oh + .05, (ow + .16, .024, .1), 'hb-teak-dark', 'wall-panel')

    def marble_border(self, room):
        """A black marble inlay band set in from the walls of the marble-floored halls."""
        if room.get('floorFinish') != 'white-marble':
            return
        clear = self.clear(room)
        if clear.area < 12:
            return
        z = room['floor'] * self.H
        inner = clear.buffer(-.35, join_style=2)
        band = inner.difference(inner.buffer(-.14, join_style=2))
        for part in _polys(band):
            self.k.poly_mesh(part, z + .0085, z + .0102, 'floor-marble-border', room['floor'], 'finish', owner=room['id'])

    def dress(self, room):
        """Paint, cornice, inlay and the light fittings of rooms this module does not furnish."""
        self.paint(room)
        self.marble_border(room)
        if room['kind'] in ('kitchen', 'bathroom', 'powder-room', 'store', 'pooja', 'dress', 'utility', 'drying-room'):
            c = self.clear(room).representative_point()
            bowl_light(self.k, c.x, c.y, self.ceiling(room), room['floor'], 10 if room['kind'] != 'kitchen' else 16)
            if room['kind'] == 'kitchen':
                self.tube(self.t.room_context(room), 22)

    # ---------------------------------------------------------------------------------------- placement helpers
    def context(self, room):
        ctx = self.t.room_context(room)
        if room['kind'] in ('living', 'drawing-room', 'family', 'dining'):
            ctx['doors'] = ctx['doors'] + [(q, {'kind': 'open'}) for q in self.t.open_keepouts(ctx)]
        ctx['hung'] = []
        return ctx

    def frame(self, ctx, sp):
        return Local(self.k, sp['c'], sp['t'], sp['n'], ctx['floor'] * self.H, ctx['floor'])

    def place(self, ctx, kind, foot, mark, front=None, tall=False):
        ctx['placed'].append(foot if front is None else foot.union(front))
        if tall:
            ctx.setdefault('tall', []).append(foot.buffer(.1))
        self.t.furnishing(kind, ctx['room'], foot)
        self.k.editable(kind, ctx['room'], foot, mark)

    def free(self, ctx, poly, keep_doors=True):
        if not ctx['inside'].covers(poly):
            return False
        zones = [q for q, _ in ctx['doors']] if keep_doors else []
        return not self.t.hits(poly, zones) and not self.t.hits(poly, ctx['placed'])

    def best(self, cands, ctx, prefer=None):
        if not cands:
            return None
        if prefer is None:
            return max(cands, key=lambda s: (round(self.t.far_from_doors(ctx, s), 1), s['L'], -abs(s['s'] - s['L'] / 2)))
        return max(cands, key=prefer)

    def away(self, ctx, sp, others):
        """Distance from a candidate to the nearest already-chosen piece."""
        c = Point(*(sp['c'] + sp['n'] * .4))
        return min((c.distance(o) for o in others), default=10.)

    def hang(self, ctx, width, height, zc, draw, low=None):
        """Something hung on a clear wall stretch at zc (centre height), not over another hung item."""
        cands = self.t.spots({**ctx, 'placed': ctx['hung'] + ctx.get('tall', [])}, width + .3, .04, front=0, height=zc + height / 2 + .05, step=.1)
        if low is not None:
            cands = [s for s in cands if not any(s['foot'].buffer(.05).intersects(q) for q in low)]
        if not cands:
            return None
        sp = max(cands, key=lambda s: (-abs(s['s'] - s['L'] / 2) * .5 + s['L'] * .1, s['L']))
        F = self.frame(ctx, sp)
        draw(F)
        ctx['hung'].append(sp['foot'].buffer(.25))
        return sp

    def tube(self, ctx, power=20, avoid=()):
        cands = self.t.spots({**ctx, 'placed': list(ctx.get('hung', [])) + list(avoid)}, 1.4, .06, front=0, height=3.0, step=.1)
        if not cands:
            return
        sp = max(cands, key=lambda s: (s['L'], -abs(s['s'] - s['L'] / 2)))
        tube_light(self.frame(ctx, sp), 0, 2.62, power)
        ctx.setdefault('hung', []).append(sp['foot'].buffer(.3))

    def fans(self, room, count=None, avoid=None):
        clear = self.clear(room)
        x0, y0, x1, y1 = clear.bounds
        count = count or (2 if clear.area > 26 else 1)
        c = clear.centroid
        pts = [(c.x, c.y)]
        if count == 2:
            if x1 - x0 >= y1 - y0:
                d = (x1 - x0) / 4
                pts = [(c.x - d, c.y), (c.x + d, c.y)]
            else:
                d = (y1 - y0) / 4
                pts = [(c.x, c.y - d), (c.x, c.y + d)]
        if avoid is not None and count == 1 and Point(*pts[0]).distance(avoid) < .9:
            pts = [(c.x + (.9 if c.x < avoid.x else -.9), c.y)]
        roof = self.metres(geometry(self.b['roofs'][room['floor']]['ceiling']))
        for i, (x, y) in enumerate(pts):
            if roof.covers(Point(x, y)):
                ceiling_fan(self.k, x, y, self.ceiling(room), room['floor'], 'hb-fan' if i % 2 == 0 else 'hb-fan', phase=.3 + i * .5)

    def plant_corner(self, ctx, species='areca', scale=.55, pot=(.2, .34, 'hb-brass'), height=2.2):
        cands = self.t.spots(ctx, .55, .55, front=0, height=height, step=.2)
        if not cands:
            return None
        sp = min(cands, key=lambda s: (min(s['s'], s['L'] - s['s']), -self.away(ctx, s, ctx['placed'])))
        F = self.frame(ctx, sp)
        x, y = F.at(0, .3)
        mark = self.k.edit_mark()
        self.k.plant(x, y, F.z, species, f=ctx['floor'], scale=scale, pot=pot)
        self.place(ctx, f'{species}-plant-{len(ctx["placed"])}', F.poly(-.25, .25, .05, .55), mark)
        return sp

    def rug(self, F, u0, u1, v0, v1, clear, mat='hb-carpet'):
        rug = F.poly(u0, u1, v0, v1).intersection(clear.buffer(-.12, join_style=2))
        if rug.is_empty or rug.geom_type != 'Polygon' or rug.area < .5:
            return
        self.k.poly_mesh(rug, F.z + .011, F.z + .021, mat, F.f, 'rug', owner=None)

    # -------------------------------------------------------------------------------------------------- rooms
    def furnish(self, room):
        kind = room['kind']
        handler = {'kitchen': self.kitchen, 'living': self.drawing_hall, 'drawing-room': self.drawing_hall, 'dining': self.dining_hall,
                   'family': self.family_lounge, 'bedroom': self.bedroom, 'study': self.office, 'foyer': self.foyer,
                   'veranda': self.verandah, 'terrace': self.terrace, 'drying-yard': self.wash_yard,
                   'stair': self.stair_hall}.get(kind)
        if handler is None:
            return False
        return handler(room) is not False

    def lounge(self, ctx, length=2.1, sofa=teak_sofa, chairs=True, table=True):
        """A sofa backed by a wall, a centre table and two armchairs turned toward it, on a carpet."""
        room, f = ctx['room'], ctx['floor']
        choice = None
        for L in (length, 1.9, 1.7):
            cands = [s for s in self.t.spots(ctx, L + .1, .86, front=1.9, height=.95, step=.1)]
            if cands:
                choice = (L, self.best(cands, ctx))
                break
        if choice is None:
            return None
        L, sp = choice
        F = self.frame(ctx, sp)
        mark = self.k.edit_mark()
        sofa(F, L, 3)
        foot = F.poly(-L / 2, L / 2, 0, .86)
        self.place(ctx, 'sofa', foot, mark)
        if table:
            tab = F.poly(-.6, .6, 1.38, 2.0)
            if self.free(ctx, tab):
                mark = self.k.edit_mark()
                centre_table(F, 0, 1.69)
                self.place(ctx, 'centre-table', tab, mark)
        if chairs:
            n = 0
            for su in (1, -1):
                u = su * (L / 2 + .95)
                spot = F.poly(u - .45, u + .45, 1.25, 2.13)
                if not self.free(ctx, spot):
                    continue
                G = F.turn(u + su * .41, 1.69, su * math.pi / 2)
                mark = self.k.edit_mark()
                sofa(G, .86, 1)
                n += 1
                self.place(ctx, f'armchair-{n}', spot, mark)
        self.rug(F, -L / 2 - .35, L / 2 + .35, .55, 2.9, ctx['clear'])
        return sp, F, foot

    def drawing_hall(self, room):
        ctx = self.context(room)
        f = room['floor']
        got = self.lounge(ctx)
        if got:
            self.hang(ctx, .32, .8, 1.75, lambda G: wall_clock(G, 0, 2.0, pendulum=True))
        # A diwan with bolsters on the longest free wall, a glass-fronted showcase and a radio on its table.
        sofa = [got[2]] if got else []
        others = list(sofa)
        if self.clear(room).area > 30:
            cands = self.t.spots(ctx, 2.0, .87, front=.9, height=.9, step=.1)
            if cands:
                sp = max(cands, key=lambda s: (round(self.away(ctx, s, others), 0), -abs(s['s'] - s['L'] / 2)))
                G = self.frame(ctx, sp)
                mark = self.k.edit_mark()
                diwan(G)
                self.place(ctx, 'diwan', G.poly(-.98, .98, 0, .86), mark)
                others.append(G.poly(-.98, .98, 0, .86))
                self.hang(ctx, 1.1, .75, 1.65, lambda H_: framed_picture(H_, 0, 1.65, 1.1, .75, 'art'))
        cands = self.t.spots(ctx, 1.6, .45, front=.9, height=2.0, step=.1)
        if cands:
            sp = max(cands, key=lambda s: (round(self.away(ctx, s, others), 0), -abs(s['s'] - s['L'] / 2)))
            G = self.frame(ctx, sp)
            mark = self.k.edit_mark()
            showcase(G, 1.5)
            self.place(ctx, 'showcase', G.poly(-.78, .78, 0, .46), mark, tall=True)
            others.append(G.poly(-.78, .78, 0, .46))
        cands = self.t.spots(ctx, .55, .45, front=.4, height=1.0, step=.1)
        if cands:
            sp = max(cands, key=lambda s: (-round(self.away(ctx, s, sofa), 0) if sofa else 0, -abs(s['s'] - s['L'] / 2)))
            G = self.frame(ctx, sp)
            mark = self.k.edit_mark()
            radio_table(G)
            self.place(ctx, 'radio-table', G.poly(-.27, .27, 0, .44), mark)
        self.hang(ctx, .9, .65, 1.7, lambda H_: framed_picture(H_, 0, 1.7, .9, .65, 'art-2'))
        for _ in range(2):
            self.plant_corner(ctx)
        clear = self.clear(room)
        c = clear.centroid
        chandelier(self.k, c.x, c.y, self.ceiling(room), f)
        self.fans(room, 2)

    def dining_hall(self, room):
        ctx = self.context(room)
        f = room['floor']
        clear = self.clear(room)
        z = f * self.H
        x0, y0, x1, y1 = clear.bounds
        along_x = x1 - x0 >= y1 - y0
        t = np.array([1., 0.]) if along_x else np.array([0., 1.])
        n = np.array([-t[1], t[0]])
        c = np.array(clear.centroid.coords[0])
        table = None
        for length, depth, per_side in ((2.4, 1.05, 3), (2.0, 1.0, 3), (1.6, .95, 2)):
            for dx in (0, .3, -.3, .6, -.6):
                for dy in (0, -.3, .3, -.5, .5, -.7, .7):
                    cc = c + t * dx + n * dy
                    F = Local(self.k, cc, t, n, z, f)
                    zone = F.poly(-length / 2 - .72, length / 2 + .72, -depth / 2 - .72, depth / 2 + .72)
                    if ctx['inside'].covers(zone) and not self.t.hits(zone, [q for q, _ in ctx['doors']]) and not self.t.hits(zone, ctx['placed']):
                        table = (F, length, depth, per_side)
                        break
                if table:
                    break
            if table:
                break
        if table:
            F, length, depth, per_side = table
            mark = self.k.edit_mark()
            dining_table(F, 0, 0, length, depth)
            for i in range(per_side):
                u = -length / 2 + length * (i + .5) / per_side
                for sv in (-1, 1):
                    cane_chair(F.turn(u, sv * (depth / 2 + .2), 0 if sv > 0 else math.pi))
            for su in (-1, 1):
                cane_chair(F.turn(su * (length / 2 + .2), 0, -su * math.pi / 2), arms=True)
            foot = F.poly(-length / 2 - .45, length / 2 + .45, -depth / 2 - .42, depth / 2 + .42)
            self.place(ctx, 'dining-set', foot, mark)
            self.rug(F, -length / 2 - .7, length / 2 + .7, -depth / 2 - .75, depth / 2 + .75, clear, 'hb-durrie')
            x, y = F.at(0, 0)
            lantern(self.k, x, y, self.ceiling(room), f)
        others = list(ctx['placed'])
        cands = self.t.spots(ctx, 1.8, .46, front=.85, height=2.0, step=.1) or self.t.spots(ctx, 1.4, .46, front=.85, height=2.0, step=.1)
        if cands:
            sp = max(cands, key=lambda s: (round(self.t.far_from_doors(ctx, s), 1), s['L'], -abs(s['s'] - s['L'] / 2)))
            G = self.frame(ctx, sp)
            mark = self.k.edit_mark()
            w = 1.7 if sp['L'] >= 1.8 else 1.3
            showcase(G, w, .45, 1.9)
            self.place(ctx, 'crockery-cabinet', G.poly(-w / 2 - .03, w / 2 + .03, 0, .47), mark, tall=True)
        cands = self.t.spots(ctx, .66, .66, front=.7, height=1.7, step=.1)
        if cands:
            sp = min(cands, key=lambda s: (min(s['s'], s['L'] - s['s']), -self.t.far_from_doors(ctx, s)))
            G = self.frame(ctx, sp)
            mark = self.k.edit_mark()
            # A single-door refrigerator with a crocheted cover and a bottle on top: every 1980s dining room.
            G.rbox(0, .33, .78, (.6, .6, 1.52), 'hb-white-steel', .04)
            G.box(0, .635, 1.05, (.5, .01, .006), 'hb-steel', 'detail')
            G.rbox(.22, .645, 1.0, (.025, .03, .28), 'hb-steel', .01)
            G.box(0, .33, 1.545, (.5, .5, .006), 'linen', 'detail')
            G.lathe(-.1, .33, 1.548, [[0, 0], [.04, 0], [.045, .2], [.015, .27], [.015, .3], [.001, .3]], 'hb-glass')
            self.place(ctx, 'refrigerator', G.poly(-.31, .31, 0, .64), mark, tall=True)
        self.hang(ctx, .34, .34, 2.05, lambda H_: wall_clock(H_, 0, 2.05))
        self.hang(ctx, .8, .6, 1.65, lambda H_: framed_picture(H_, 0, 1.65, .8, .6, 'art-2'))
        self.fans(room, 2)

    def family_lounge(self, room):
        ctx = self.context(room)
        f = room['floor']
        got = self.lounge(ctx, 2.0, sofa=cane_sofa, chairs=True)
        others = list(ctx['placed'])
        # A carrom board with four moodhas, the evening game of every bungalow.
        clear = self.clear(room)
        best = None
        for sp in self.t.spots(ctx, 1.9, 1.9, front=.2, height=.9, step=.2) or []:
            F = self.frame(ctx, sp)
            zone = F.poly(-.95, .95, .2, 2.1)
            if self.free(ctx, zone):
                score = self.away(ctx, sp, others)
                if best is None or score > best[0]:
                    best = (score, F, zone)
        if best:
            _, F, zone = best
            mark = self.k.edit_mark()
            carrom(F, 0, 1.15)
            for du, dv in ((0, -.62), (0, .62), (-.62, 0), (.62, 0)):
                moodha(F, du, 1.15 + dv)
            self.place(ctx, 'carrom', zone, mark)
        cands = self.t.spots(ctx, 1.4, .5, front=1.6, height=1.15, step=.1)
        if cands:
            sp = max(cands, key=lambda s: (round(self.away(ctx, s, ctx['placed']), 0), -abs(s['s'] - s['L'] / 2)))
            G = self.frame(ctx, sp)
            mark = self.k.edit_mark()
            tv_cabinet(G)
            self.place(ctx, 'tv-cabinet', G.poly(-.66, .66, 0, .52), mark, tall=True)
        cands = self.t.spots(ctx, 1.25, .38, front=.8, height=2.05, step=.1)
        if cands:
            sp = max(cands, key=lambda s: (round(self.away(ctx, s, ctx['placed']), 0), -abs(s['s'] - s['L'] / 2)))
            G = self.frame(ctx, sp)
            mark = self.k.edit_mark()
            bookcase(G)
            self.place(ctx, 'bookcase', G.poly(-.62, .62, 0, .38), mark, tall=True)
        self.hang(ctx, .34, .34, 2.05, lambda H_: wall_clock(H_, 0, 2.05))
        self.hang(ctx, .9, .65, 1.65, lambda H_: framed_picture(H_, 0, 1.65, .9, .65, 'art'))
        self.plant_corner(ctx, 'monstera', .9, (.2, .3, 'hb-pot-red'), 1.4)
        c = clear.centroid
        bowl_light(self.k, c.x, c.y, self.ceiling(room), f, 16)
        self.fans(room, 2)

    def bedroom(self, room):
        ctx = self.context(room)
        f = room['floor']
        clear = self.clear(room)
        width = 1.8 if clear.area > 15 else 1.5
        choice = None
        for w in (width, 1.5):
            cands = self.t.spots(ctx, w + 1.1, 2.12, front=.6, height=1.2, step=.1)
            if cands:
                choice = (w, max(cands, key=lambda s: (round(self.t.far_from_doors(ctx, s), 0), s['L'], -abs(s['s'] - s['L'] / 2))))
                break
            cands = self.t.spots(ctx, w + .2, 2.12, front=.6, height=1.2, step=.1)
            if cands:
                choice = (w, max(cands, key=lambda s: (s['L'], -abs(s['s'] - s['L'] / 2))))
                break
        bed_point = clear.centroid
        if choice:
            w, sp = choice
            F = self.frame(ctx, sp)
            mark = self.k.edit_mark()
            teak_bed(F, w)
            foot = F.poly(-w / 2 - .08, w / 2 + .08, 0, 2.12)
            self.place(ctx, 'bed', foot, mark, F.poly(-w / 2 - .08, w / 2 + .08, 2.12, 2.7))
            for su in (-1, 1):
                st = F.poly(su * (w / 2 + .32) - .24, su * (w / 2 + .32) + .24, 0, .42)
                if self.free(ctx, st):
                    mark = self.k.edit_mark()
                    side_table(F, su * (w / 2 + .32), .21)
                    x, y = F.at(su * (w / 2 + .32), .21)
                    self.k.light((x, y, F.z + .95), 8, kind='lamp')
                    self.place(ctx, 'bedside-' + ('left' if su < 0 else 'right'), st, mark)
            self.rug(F, -w / 2 - .9, -w / 2 - .1, .4, 1.8, clear, 'hb-durrie')
            ctx.setdefault('tall', []).append(F.poly(-w / 2 - .1, w / 2 + .1, 0, .12).buffer(.1))
            x, y = F.at(0, 1.25)
            bed_point = Point(x, y)
        cands = self.t.spots(ctx, .96, .54, front=.8, height=2.0, step=.1)
        if cands:
            sp = max(cands, key=lambda s: (round(self.away(ctx, s, ctx['placed']), 0), -min(s['s'], s['L'] - s['s'])))
            G = self.frame(ctx, sp)
            mark = self.k.edit_mark()
            almirah(G)
            self.place(ctx, 'almirah', G.poly(-.47, .47, 0, .54), mark, tall=True)
        cands = self.t.spots(ctx, 1.04, .5, front=.95, height=1.95, step=.1)
        if cands:
            sp = max(cands, key=lambda s: (round(self.away(ctx, s, ctx['placed']), 0), -abs(s['s'] - s['L'] / 2)))
            G = self.frame(ctx, sp)
            mark = self.k.edit_mark()
            dresser(G)
            self.place(ctx, 'dressing-table', G.poly(-.52, .52, 0, .5), mark, G.poly(-.3, .3, .5, 1.05), tall=True)
        if clear.area > 14:
            cands = self.t.spots(ctx, .7, 1.25, front=.3, height=.95, step=.1)
            if cands:
                sp = max(cands, key=lambda s: (round(self.away(ctx, s, ctx['placed']), 0), -abs(s['s'] - s['L'] / 2)))
                G = self.frame(ctx, sp)
                mark = self.k.edit_mark()
                easy_chair(G)
                self.place(ctx, 'easy-chair', G.poly(-.35, .35, 0, 1.22), mark)
        self.hang(ctx, .34, .34, 2.1, lambda H_: wall_clock(H_, 0, 2.1))
        self.hang(ctx, .8, .55, 1.6, lambda H_: framed_picture(H_, 0, 1.6, .8, .55, 'art'))
        self.tube(ctx, 18)
        self.fans(room, 1, bed_point)

    def office(self, room):
        ctx = self.context(room)
        f = room['floor']
        cands = self.t.spots(ctx, 2.0, 2.75, front=.5, height=1.25, step=.1)
        if cands:
            sp = max(cands, key=lambda s: (s['L'], round(self.t.far_from_doors(ctx, s), 0), -abs(s['s'] - s['L'] / 2)))
            F = self.frame(ctx, sp)
            mark = self.k.edit_mark()
            office_desk(F, 0, 1.35)
            office_chair(F.turn(0, .55, math.pi), 0, 0)
            for su in (-1, 1):
                cane_chair(F.turn(su * .45, 2.2, 0), arms=True)
            self.place(ctx, 'officer-desk', F.poly(-1.0, 1.0, 0, 2.75), mark)
            self.rug(F, -1.3, 1.3, .2, 2.9, self.clear(room), 'hb-carpet')
        cands = self.t.spots(ctx, 1.25, .38, front=.8, height=2.05, step=.1)
        if cands:
            sp = max(cands, key=lambda s: (round(self.away(ctx, s, ctx['placed']), 0), -abs(s['s'] - s['L'] / 2)))
            G = self.frame(ctx, sp)
            mark = self.k.edit_mark()
            bookcase(G)
            self.place(ctx, 'bookcase', G.poly(-.62, .62, 0, .38), mark, tall=True)
        cands = self.t.spots(ctx, .96, .54, front=.8, height=2.0, step=.1)
        if cands:
            sp = max(cands, key=lambda s: (round(self.away(ctx, s, ctx['placed']), 0), -min(s['s'], s['L'] - s['s'])))
            G = self.frame(ctx, sp)
            mark = self.k.edit_mark()
            almirah(G)
            self.place(ctx, 'almirah', G.poly(-.47, .47, 0, .54), mark, tall=True)
        self.hang(ctx, .34, .34, 2.1, lambda H_: wall_clock(H_, 0, 2.1))
        self.hang(ctx, 1.0, .7, 1.7, lambda H_: framed_picture(H_, 0, 1.7, 1.0, .7, 'art'))
        self.plant_corner(ctx, 'areca', .5, (.18, .32, 'hb-brass'))
        self.tube(ctx, 22)
        self.fans(room, 1)

    def foyer(self, room):
        """The grilled entrance verandah: stacked monobloc chairs, cane moodhas, a bench, a shoe rack, a doormat."""
        ctx = self.context(room)
        f = room['floor']
        cands = self.t.spots(ctx, 1.5, .45, front=.6, height=.95, step=.1)
        if cands:
            sp = max(cands, key=lambda s: (round(self.t.far_from_doors(ctx, s), 1), -abs(s['s'] - s['L'] / 2)))
            F = self.frame(ctx, sp)
            mark = self.k.edit_mark()
            F.rbox(0, .22, .45, (1.4, .4, .04), 'hb-teak', .01)
            for su in (-1, 1):
                F.box(su * .62, .22, .22, (.05, .36, .44), 'hb-teak')
            F.box(0, .22, .12, (1.3, .34, .02), 'hb-teak')
            for j, uu in enumerate((-.45, -.2, .3)):
                F.rbox(uu, .2, .145, (.11, .26, .05), ('hb-plate', 'hb-pot-red', 'hb-leather')[j], .02)
            self.place(ctx, 'bench', F.poly(-.72, .72, 0, .44), mark)
        cands = self.t.spots(ctx, .6, .6, front=.4, height=1.1, step=.1)
        if cands:
            sp = min(cands, key=lambda s: (min(s['s'], s['L'] - s['s']), -self.t.far_from_doors(ctx, s)))
            F = self.frame(ctx, sp)
            mark = self.k.edit_mark()
            plastic_chair_stack(self.k, F, 0, .3, 4)
            self.place(ctx, 'stacked-chairs', F.poly(-.3, .3, 0, .6), mark)
        cands = self.t.spots(ctx, .5, .5, front=.4, height=.6, step=.1)
        if cands:
            sp = min(cands, key=lambda s: (min(s['s'], s['L'] - s['s']), -self.away(ctx, s, ctx['placed'])))
            F = self.frame(ctx, sp)
            mark = self.k.edit_mark()
            moodha(F, 0, .25)
            moodha(F, 0, .25, .425)
            self.place(ctx, 'moodhas', F.poly(-.22, .22, .03, .47), mark)
        cands = self.t.spots(ctx, .8, .32, front=.5, height=.8, step=.1)
        if cands:
            sp = max(cands, key=lambda s: (-self.t.far_from_doors(ctx, s), -abs(s['s'] - s['L'] / 2)))
            F = self.frame(ctx, sp)
            mark = self.k.edit_mark()
            F.box(0, .16, .38, (.76, .3, .76), 'hb-teak')
            for zz in (.22, .48):
                F.box(0, .31, zz, (.7, .004, .012), 'hb-teak-dark', 'detail')
            for j, uu in enumerate((-.22, .05, .25)):
                F.rbox(uu, .17, .79, (.11, .26, .05), ('hb-leather', 'hb-plate', 'hb-pot-red')[j], .02)
            self.place(ctx, 'shoe-rack', F.poly(-.4, .4, 0, .32), mark)
        # A coir doormat inside the main door.
        for q, o in ctx['doors']:
            if o.get('kind') == 'door' and o.get('timberScreen'):
                mat = q.centroid.buffer(.42, cap_style=3).intersection(ctx['clear'])
                if not mat.is_empty:
                    self.k.poly_mesh(mat, f * self.H + .0095, f * self.H + .016, 'hb-khus', f, 'rug')
        self.plant_corner(ctx, 'croton', .7, (.18, .3, 'hb-pot-red'), 1.0)
        self.tube(ctx, 20)
        self.fans(room, 1)

    def verandah(self, room):
        """The rear verandah: a teak jhoola on chains, cane chairs, an easy chair, a matka and potted plants."""
        ctx = self.context(room)
        f = room['floor']
        z = f * self.H
        ceiling = self.H - .157
        cands = self.t.spots(ctx, 1.75, 1.9, front=.3, height=.9, step=.1)
        if cands:
            sp = max(cands, key=lambda s: (round(self.t.far_from_doors(ctx, s), 1), -abs(s['s'] - s['L'] / 2)))
            F = self.frame(ctx, sp)
            mark = self.k.edit_mark()
            swing(F, 0, 1.0, ceiling)
            self.place(ctx, 'jhoola', F.poly(-.85, .85, .45, 1.55), mark, F.poly(-.85, .85, .05, 1.9))
        cands = self.t.spots(ctx, 1.9, 1.05, front=.4, height=.7, step=.1)
        if cands:
            sp = max(cands, key=lambda s: (round(self.away(ctx, s, ctx['placed']), 0), -abs(s['s'] - s['L'] / 2)))
            F = self.frame(ctx, sp)
            mark = self.k.edit_mark()
            easy_chair(F.turn(-.55, 0, 0))
            cane_chair(F.turn(.5, .45, math.pi), arms=True)
            F.cyl(.0, .55, .3, .25, .03, 'hb-cane')
            F.cyl(.0, .55, .15, .05, .3, 'hb-teak')
            F.cyl(.0, .55, .01, .18, .02, 'hb-teak')
            F.lathe(0, .55, .315, [[0, 0], [.04, 0], [.05, .05], [.045, .06], [.001, .06]], 'ceramic')
            self.place(ctx, 'sit-out', F.poly(-.9, .9, 0, 1.05), mark)
        cands = self.t.spots(ctx, .5, .5, front=.3, height=1.0, step=.1)
        if cands:
            sp = min(cands, key=lambda s: (min(s['s'], s['L'] - s['s']), -self.away(ctx, s, ctx['placed'])))
            F = self.frame(ctx, sp)
            mark = self.k.edit_mark()
            # A clay matka cooling water on a three-legged brass stand, a steel tumbler on its lid.
            for i in range(3):
                a = i * 2 * math.pi / 3
                F.rod(math.cos(a) * .16, .25 + math.sin(a) * .16, 0, math.cos(a) * .12, .25 + math.sin(a) * .12, .3, .01, 'hb-brass')
            F.cyl(0, .25, .3, .15, .015, 'hb-brass')
            F.lathe(0, .25, .31, [[0, 0], [.08, 0], [.17, .1], [.18, .16], [.13, .3], [.07, .34], [.08, .37], [.001, .37]], 'hb-pot-red', 'furniture', 28)
            F.lathe(0, .25, .68, [[0, 0], [.03, 0], [.035, .1], [.001, .1]], 'hb-steel')
            self.place(ctx, 'matka', F.poly(-.22, .22, .03, .47), mark)
        # Pots of crotons and ferns along the open garden edge, clear of the steps.
        clear = self.clear(room)
        steps = [Polygon(np.array(ft['polygon']) / 1000) for ft in self.hs.landscape.get('features', []) if ft.get('kind') == 'entry_steps']
        edges = clear.exterior
        k = self.k
        for a, c in zip(list(edges.coords), list(edges.coords)[1:]):
            line = LineString([a, c])
            if line.length < 2 or not self.hs.fp.boundary.buffer(.05).covers(line):
                continue
            for tt in np.arange(.45, line.length - .3, .8):
                q = line.interpolate(tt)
                inward = np.array([-(c[1] - a[1]), c[0] - a[0]]) / line.length
                p = np.array([q.x, q.y]) + inward * .32
                if not clear.buffer(-.2).contains(Point(*p)):
                    p = np.array([q.x, q.y]) - inward * .32
                if not clear.buffer(-.2).contains(Point(*p)):
                    continue
                spot = Point(*p).buffer(.26)
                if any(spot.intersects(s.buffer(.12)) for s in steps) or self.t.hits(spot, ctx['placed']) or self.t.hits(spot, [qq for qq, _ in ctx['doors']]):
                    continue
                self.hs.pot(p[0], p[1], z + .01, .19, .32, 'red' if int(tt) % 2 else 'pink', ('croton', 'marigold', 'geranium', 'jade')[int(tt) % 4], f)
                k.obstacle(spot, f, f"{room['id']}/pot-{tt:.1f}")
        cx, cy = clear.centroid.x, clear.centroid.y
        x0, y0, x1, y1 = clear.bounds
        for i, (x, y) in enumerate(((x0 + (x1 - x0) * .25, cy), (x0 + (x1 - x0) * .75, cy)) if x1 - x0 > 6 else ((cx, cy),)):
            ceiling_fan(k, x, y, z + ceiling, f, phase=.4 * i)
        self.tube(ctx, 20)

    def terrace(self, room):
        """Front terrace: cane chairs under the chick pergola, big pots along the parapet and a charpai in the sun;
        rear terrace: a clothesline and monobloc chairs."""
        ctx = self.context(room)
        f = room['floor']
        z = f * self.H
        k = self.k
        poly = Polygon(np.array(room['polygon']) / 1000)
        clear = self.clear(room)
        pergola = next((a for a in self.hs.exterior.get('assemblies', []) if a['geometry'].get('kind') == 'chick_pergola'
                        and a['geometry'].get('deck_space_id') == room['id']), None)
        placed = []
        if pergola:
            x0, y0, x1, y1 = [q / 1000 for q in pergola['geometry']['bounds_mm']]
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            F = Local(k, (cx, cy), (1, 0), (0, 1), z, f)
            mark = k.edit_mark()
            F.cyl(0, 0, .6, .38, .03, 'hb-teak')
            F.cyl(0, 0, .3, .05, .58, 'hb-teak')
            F.cyl(0, 0, .02, .26, .04, 'hb-teak')
            F.lathe(.1, .05, .615, [[0, 0], [.05, 0], [.06, .08], [.04, .1], [.001, .1]], 'ceramic')
            for i, a in enumerate((0, math.pi / 2, math.pi, 3 * math.pi / 2)):
                if i == 0:
                    easy_chair(F.turn(math.cos(a) * 1.35, math.sin(a) * 1.35, a + math.pi / 2))
                else:
                    cane_chair(F.turn(math.cos(a) * .82, math.sin(a) * .82, a - math.pi / 2), arms=True)
            foot = F.poly(-1.3, 1.3, -1.3, 1.3)
            self.place(ctx, 'pergola-seating', foot, mark)
            placed.append(foot)
            rug_poly = F.poly(-1.5, 1.5, -1.5, 1.5).intersection(clear.buffer(-.3))
            if not rug_poly.is_empty and rug_poly.geom_type == 'Polygon':
                k.poly_mesh(rug_poly, z + .011, z + .02, 'hb-durrie', f, 'rug')
        # Big pots along the parapet, clear of doors.
        doors = [q for q, _ in ctx['doors']]
        ring = poly.exterior
        pots = 0
        for a, c in zip(list(ring.coords), list(ring.coords)[1:]):
            line = LineString([a, c])
            if line.length < 1.5:
                continue
            on_edge = self.hs.fp.boundary.buffer(.05).covers(line) or any(
                LineString(np.array(g['points']) / 1000).buffer(.05).covers(line) for g in self.hs.guards if g.get('owner') == room['id'])
            if not on_edge:
                continue
            inward = np.array([-(c[1] - a[1]), c[0] - a[0]]) / line.length
            for tt in np.arange(.9, line.length - .6, 2.4):
                q = line.interpolate(tt)
                p = np.array([q.x, q.y]) + inward * .55
                if not poly.buffer(-.3).contains(Point(*p)):
                    p = np.array([q.x, q.y]) - inward * .55
                spot = Point(*p).buffer(.36)
                if not clear.buffer(-.05).covers(spot) or self.t.hits(spot, doors) or any(spot.intersects(q_) for q_ in placed + ctx['placed']):
                    continue
                self.hs.pot(p[0], p[1], z + .012, .27, .46, 'red' if pots % 3 else 'pink',
                            'bougainvillea' if pots % 3 == 1 else ('croton', 'poinsettia', 'jade', 'marigold')[pots % 4], f)
                k.obstacle(spot, f, f"{room['id']}/pot-{pots}")
                placed.append(spot)
                pots += 1
        if pergola:
            # A charpai and a drying line in the sun on the open part of the terrace.
            x0, y0, x1, y1 = poly.bounds
            for cx in np.arange(x1 - 1.6, x0 + 6, -.5):
                cy = y0 + 1.6
                F = Local(k, (cx, cy), (1, 0), (0, 1), z, f)
                zone = F.poly(-1.0, 1.0, -.5, .5)
                if self.free(ctx, zone.buffer(.25)) and not any(zone.intersects(q_) for q_ in placed):
                    mark = k.edit_mark()
                    charpai(F, 0, 0)
                    F.rbox(.7, 0, .47, (.36, .7, .12), 'hb-print', .05)
                    self.place(ctx, 'charpai', zone, mark)
                    placed.append(zone)
                    break
        else:
            x0, y0, x1, y1 = clear.bounds
            a, c = (x0 + .6, y1 - 1.0), (x1 - .6, y1 - 1.0)
            line = LineString([a, c]).buffer(.4)
            if self.free(ctx, line):
                mark = k.edit_mark()
                clothesline(k, a, c, z, 1.9, f)
                self.place(ctx, 'clothesline', line, mark)
            cands = self.t.spots(ctx, .6, .6, front=.4, height=1.1, step=.2)
            if cands:
                sp = min(cands, key=lambda s: (min(s['s'], s['L'] - s['s'])))
                F = self.frame(ctx, sp)
                mark = k.edit_mark()
                plastic_chair_stack(k, F, 0, .3, 3)
                self.place(ctx, 'stacked-chairs', F.poly(-.3, .3, 0, .6), mark)
        return True

    def kitchen(self, room):
        """The shared kitchen run in teak and black granite, with a small teak work table and two stools."""
        ctx = self.t.room_context(room)
        self.t.kitchen_set(ctx)
        clear = self.clear(room)
        x0, y0, x1, y1 = clear.bounds
        c = np.array(clear.centroid.coords[0])
        for dx in (0, .4, -.4, .8, -.8):
            for dy in (0, .4, -.4, .8, -.8):
                F = Local(self.k, c + (dx, dy), (1, 0), (0, 1), room['floor'] * self.H, room['floor'])
                zone = F.poly(-.85, .85, -.75, .75)
                if self.free(ctx, zone.buffer(.25)):
                    mark = self.k.edit_mark()
                    F.rbox(0, 0, .74, (1.2, .7, .04), 'hb-teak', .01)
                    for su in (-1, 1):
                        for sv in (-1, 1):
                            F.box(su * .54, sv * .29, .36, (.05, .05, .72), 'hb-teak')
                    F.box(0, 0, .15, (1.1, .6, .02), 'hb-teak')
                    for su in (-1, 1):
                        moodha(F, su * .2, su * -.58)
                    F.lathe(-.3, .1, .76, [[0, 0], [.12, 0], [.15, .06], [.001, .06]], 'hb-steel')
                    F.lathe(.25, -.05, .76, [[0, 0], [.06, 0], [.07, .1], [.05, .16], [.001, .16]], 'hb-brass')
                    self.place(ctx, 'work-table', zone, mark)
                    return True
        return True

    def wash_yard(self, room):
        """Clotheslines, a washing stone and buckets in the open yard behind the kitchen, inside a low wall."""
        ctx = self.context(room)
        f = room['floor']
        z = f * self.H
        k = self.k
        poly = Polygon(np.array(room['polygon']) / 1000)
        clear = self.clear(room)
        steps = [Polygon(np.array(ft['polygon']) / 1000) for ft in self.hs.landscape.get('features', [])
                 if ft.get('kind') == 'entry_steps' and ft.get('opening_id') == room['id'] + '-edge']
        # A low rendered wall with a red coping on the garden edges, open at the steps.
        edge = poly.exterior.intersection(self.hs.fp.boundary.buffer(.02))
        for part in get_parts(edge):
            if part.geom_type != 'LineString' or part.length < .5:
                continue
            body = part.buffer(.115, cap_style=2).intersection(poly)
            for s in steps:
                body = body.difference(s.buffer(.15))
            for piece in _polys(body):
                k.poly_mesh(piece, z, z + .95, 'wall', f, 'wall', owner=room['id'])
                k.poly_mesh(piece.buffer(.02, join_style=2), z + .95, z + 1.02, 'hb-stripe', f, 'coping', owner=room['id'])
                k.obstacle(piece, f, f"{room['id']}/low-wall-{piece.centroid.x:.2f}")
        inner = clear.buffer(-.35, join_style=2)
        x0, y0, x1, y1 = inner.bounds
        clothesline(k, (x0 + .2, y1 - .6), (x1 - .4, y1 - .6), z, 1.95, f)
        k.obstacle(LineString([(x0 + .2, y1 - .6), (x1 - .4, y1 - .6)]).buffer(.05), f, room['id'] + '/clothesline')
        # Washing stone, buckets and a mug by the wall tap.
        sx, sy = x0 + .5, y0 + .5
        k.rect((sx - .32, sy - .25, z, sx + .32, sy + .25, z + .28), 'hb-brick', f, 'furniture', room['id'] + '/washing-stone', room['id'])
        k.rect((sx - .34, sy - .27, z + .28, sx + .34, sy + .27, z + .33), 'hb-kota', f, 'furniture', owner=room['id'])
        k.obstacle(box(sx - .34, sy - .27, sx + .34, sy + .27), f, room['id'] + '/washing-stone')
        for j, (bx, mat) in enumerate(((sx + .62, 'hb-hex'), (sx + 1.05, 'fabric-dark'))):
            mesh = trimesh.creation.revolve(np.array([[0, 0], [.13, 0], [.16, .3], [.165, .32], [.15, .32], [.12, .03], [.001, .03]]), sections=24)
            k.node(k.asset(mesh, smooth=True), mat if j else 'hb-pot-red', (bx, sy, z + .01), floor=f, role='furniture')
        return False

    def stair_hall(self, room):
        """Paint the stair hall, finish its landing floor in terrazzo and hang a lantern in the stair well."""
        from .stair_geometry import footprint as stair_footprint
        self.paint(room, lo=.012)
        f = room['floor']
        z = f * self.H
        clear = self.clear(room)
        stairs = unary_union([self.metres(stair_footprint(st)) for st in self.b['stairs'] if st['floor'] == f] or [Polygon()])
        holes = unary_union([self.metres(stair_footprint(st)) for st in self.b['stairs'] if st['floor'] == f - 1] or [Polygon()])
        landing = clear.difference(stairs.buffer(.01)).difference(holes.buffer(.01))
        for part in _polys(landing):
            if part.area > .2:
                self.k.poly_mesh(part, z + .002, z + .009, 'floor-' + room.get('floorFinish', 'mosaic'), f, 'finish', owner=room['id'])
        parts = sorted(_polys(landing), key=lambda q: -q.area)
        if parts:
            c = parts[0].representative_point()
            bowl_light(self.k, c.x, c.y, self.ceiling(room), f, 14)
        return True
