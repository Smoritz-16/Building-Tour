"""Calder Quay: furnished floor plates for the in-browser 3D cutaway, modelled and lit in Blender.

Usage:
  python3 floor.py LAYOUT OUT.glb [--tex 2048] [--samples 96]
LAYOUT: half1 | half2 | half3 | full
  half1/2/3 : one residence on the east half of a floor (1, 2 or 3 bedrooms). The site mirrors it for the west half.
  full      : a full-floor residence (sky residences and penthouses).

The layout matches halfResidence()/fullResidence() in src/page.html (metres, x east, z south; y up), so the
room labels on the site line up with the furniture. Proportions and finishes follow real high-end waterfront
residences: wide-plank oak floors, 24 in marble tiles in the baths, oak kitchen runs with marble counters and
a waterfall island, freestanding soaking tubs, walk-in showers behind glass, standard furniture sizes
(king bed 1.93 x 2.03 m, counter 0.9 m, counter stools 0.65 m, dining table 0.75 m, seats 0.42-0.46 m).

Everything is lit with Cycles (sun, sky, lamps; no ceiling, like an architect's cutaway model) and the
lighting and materials are baked into one texture, so the browser shows it as-is with no lights at all.
Glass is exported separately (untextured) and drawn see-through by the site.
"""
import sys, os, math, random

LAYOUT, OUT_GLB = sys.argv[1], sys.argv[2]
_A = sys.argv[3:]
def _arg(name, default):
    return type(default)(_A[_A.index(name) + 1]) if name in _A else default
TEX = _arg('--tex', 2048)
BAKE_SAMPLES = _arg('--samples', 96)

# Reuse the scene setup, materials and modelling helpers of rooms.py (everything above its rooms section).
HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, 'rooms.py')).read()
_head = _src.split('# ---------------------------------------------------------------- rooms')[0]
sys.argv = ['rooms.py', 'living', '/tmp/unused', '--samples', str(BAKE_SAMPLES)]
exec(compile(_head, 'rooms.py', 'exec'), globals())

import bpy, bmesh
from mathutils import Matrix, Vector

# ---------------------------------------------------------------- extra materials
def tiles(name, base, vein, size, grout='#bdb6ab', marble=True):
    """Large-format floor tiles with fine grout lines (24 in marble in baths, stone in the kitchen)."""
    m = stone(name, base, vein, scale=0.7, vein_width=0.01) if marble else plain(name, base, 0.5, noise_bump=0.05, bump_scale=40)
    nt = m.node_tree
    bsdf = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'][0]
    src = bsdf.inputs['Base Color'].links[0].from_socket if bsdf.inputs['Base Color'].links else None
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.offset = 0.0
    br.inputs['Scale'].default_value = 1.0 / size
    br.inputs['Mortar Size'].default_value = 0.0025 / size
    br.inputs['Brick Width'].default_value = 1.0
    br.inputs['Row Height'].default_value = 1.0
    br.inputs['Color1'].default_value = (1, 1, 1, 1)
    br.inputs['Color2'].default_value = (0.96, 0.96, 0.95, 1)
    br.inputs['Mortar'].default_value = hexc(grout)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nt.links.new(tc.outputs['Object'], br.inputs['Vector'])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
    mix.inputs['Factor'].default_value = 1.0
    if src is not None:
        nt.links.new(src, mix.inputs['A'])
    else:
        mix.inputs['A'].default_value = hexc(base)
    nt.links.new(br.outputs['Color'], mix.inputs['B'])
    nt.links.new(mix.outputs['Result'], bsdf.inputs['Base Color'])
    return m

def extra_materials():
    plain('wallcap', '#2b2825', 0.9)
    plain('core', '#34322f', 0.85)
    plain('stairs', '#55524d', 0.8)
    plain('liftdoor', '#8d8e8f', 0.3, metal=0.7)
    plain('cabinet', '#d9ccb9', 0.55)                     # pale oak-veneer flat fronts (Poliform-style)
    plain('groove', '#2a241d', 0.8)
    plain('induction', '#0d0d0e', 0.08, coat=0.8)
    plain('screen', '#0a0b0c', 0.12, coat=0.6)
    plain('sinkbowl', '#55585a', 0.25, metal=0.9)
    plain('bronze', '#4a4038', 0.12, metal=0.9)          # smoked bronze mirror
    plain('rug2', '#8b7b69', 1.0, sheen=0.3, noise_bump=0.5, bump_scale=250)
    plain('sage', '#8e9a88', 1.0, sheen=0.7, noise_bump=0.3, bump_scale=420)
    plain('clay', '#b1805f', 1.0, sheen=0.6, noise_bump=0.3, bump_scale=420)
    plain('throw_a', '#9b7656', 0.95, sheen=0.5, noise_bump=0.15, bump_scale=500)
    plain('throw_b', '#5f6e7c', 0.95, sheen=0.5, noise_bump=0.15, bump_scale=500)
    plain('fruit', '#d4883b', 0.35)
    plain('laptop', '#a9abad', 0.3, metal=0.8)
    plain('bathwater', '#bcd3d4', 0.04, coat=0.5)
    tiles('bath_tile', '#efece6', '#b3ada3', 0.61)
    tiles('kitchen_tile', '#d6cfc4', '#bfb6a8', 0.9, grout='#a59d91', marble=False)

# ---------------------------------------------------------------- layout frame (matches page.html)
IN_HX, IN_HZ, IN_R = 10.8, 7.85, 4.85
WALL_H, WALL_T = 1.3, 0.12

def inside_plate(x, z, inset=0.0):
    hx, hz, r = IN_HX - inset, IN_HZ - inset, IN_R - inset
    ax, az = abs(x), abs(z)
    if ax > hx or az > hz:
        return False
    qx, qz = ax - (hx - r), az - (hz - r)
    return qx <= 0 or qz <= 0 or qx * qx + qz * qz <= r * r

_frames = []   # stack of (matrix, set of objects existing when the piece began)

class piece:
    """A piece of furniture at (x, z) turned by ry, in page.html's frame. Local -z is its back.
    Objects made inside are built in local coordinates and moved into place on exit (pieces nest)."""
    def __init__(self, x=0.0, z=0.0, ry=0.0):
        self.m = Matrix.Translation((x, -z, 0.0)) @ Matrix.Rotation(ry, 4, 'Z')
    def __enter__(self):
        self.before = set(COLL.objects)
        return self
    def __exit__(self, *a):
        for ob in COLL.objects:
            if ob not in self.before and ob.parent is None:
                ob.matrix_basis = self.m @ ob.matrix_basis

# primitives in page.html's convention: (x, y = bottom, z) and size (w, h, d); z grows towards the front
def B(mat, x, y, z, w, h, d, bevel=0.006, seg=2, ry=0.0):
    return box('b', x, -z, y, w, d, h, mat, bevel=bevel, seg=seg, rz=ry)
def S(mat, x, y, z, w, h, d, r=0.05, ry=0.0):
    r = min(r, w / 2.05, h / 2.05, d / 2.05)
    return soft('s', x, -z, y, w, d, h, mat, r=r, rz=ry)
def C(mat, x, y, z, dx, h, dz=None, verts=40, bevel=0.0, smooth=True):
    return cyl('c', x, -z, y, dx / 2, (dz if dz else dx) / 2, h, mat, verts=verts, bevel=bevel, smooth=smooth)
def lamp(x, y, z):
    table_lamp(x, -z, y)

# ---------------------------------------------------------------- furniture
def bed(x, z, ry, w, throw):
    L = 2.1
    with piece(x, z, ry):
        S('linen_taupe', 0, 0, 0, w + 0.14, 0.3, L, r=0.04)                       # upholstered platform
        S('mattress', 0, 0.28, -0.02, w, 0.22, L - 0.1, r=0.06)
        S('linen', 0, 0.46, 0.25, w + 0.08, 0.08, L - 0.6, r=0.04)                 # duvet, folded back
        S('linen', 0, 0.47, -0.24, w + 0.04, 0.05, 0.3, r=0.025)                   # turned-down edge
        S(throw, 0, 0.53, L / 2 - 0.38, w + 0.12, 0.05, 0.5, r=0.025)
        for s in (-1, 1):
            S('linen', s * w / 4, 0.48, -L / 2 + 0.32, w / 2 - 0.1, 0.17, 0.48, r=0.08)
            S('cushion_clay' if s < 0 else 'linen_taupe', s * w / 5.5, 0.5, -L / 2 + 0.6, 0.42, 0.3, 0.13, r=0.06, ry=s * 0.12)
            # walnut nightstand with a lamp
            nx = s * (w / 2 + 0.42)
            B('walnut', nx, 0, -L / 2 + 0.26, 0.52, 0.5, 0.42, bevel=0.012, seg=3)
            B('groove', nx, 0.24, -L / 2 + 0.47, 0.48, 0.006, 0.006, bevel=0)
            lamp(nx - s * 0.06, 0.5, -L / 2 + 0.2)
        books(-(w / 2 + 0.42), L / 2 - 0.34, 0.5)
        n = 5 if w > 1.5 else 4
        pw = (w + 0.5) / n
        for i in range(n):                                                          # channel-tufted headboard
            S('linen_taupe', -(w + 0.5) / 2 + pw * (i + 0.5), 0, -L / 2 - 0.07, pw - 0.012, 1.18, 0.1, r=0.035)

def wardrobe(x, z, ry, length):
    with piece(x, z, ry):
        B('cabinet', 0, 0, 0, length, 1.6, 0.6, bevel=0.004)
        B('oak', 0, 1.6, 0, length, 0.012, 0.6, bevel=0.002)
        doors = max(2, round(length / 0.55))
        for i in range(1, doors):
            B('groove', -length / 2 + i * length / doors, 0, 0.3, 0.006, 1.6, 0.004, bevel=0)
        for i in range(1, doors):
            for s in (-0.05, 0.05):
                B('bronze', -length / 2 + i * length / doors + s, 0.75, 0.305, 0.015, 0.5, 0.012, bevel=0.003)

def sofa(x, z, ry, length, mat='boucle'):
    d = 1.0
    with piece(x, z, ry):
        S(mat, 0, 0, 0.02, length - 0.02, 0.4, d - 0.04, r=0.09)
        S(mat, 0, 0, -d / 2 + 0.14, length, 0.74, 0.28, r=0.12)
        for s in (-1, 1):
            S(mat, s * (length / 2 - 0.13), 0, 0.0, 0.26, 0.6, d, r=0.12)
        inner = length - 0.52
        seats = max(2, round(inner / 0.8))
        sw = inner / seats
        for i in range(seats):
            cx = -inner / 2 + sw * (i + 0.5)
            S(mat, cx, 0.36, 0.12, sw - 0.02, 0.15, d - 0.34, r=0.07)
            S(mat, cx, 0.42, -d / 2 + 0.34, sw - 0.04, 0.38, 0.2, r=0.09)
        S('cushion_clay', -inner / 2 + 0.3, 0.5, -0.12, 0.44, 0.4, 0.14, r=0.07, ry=0.2)
        S('sage', inner / 2 - 0.3, 0.5, -0.12, 0.44, 0.4, 0.14, r=0.07, ry=-0.2)

def armchair(x, z, ry, mat='boucle'):
    with piece(x, z, ry):
        S(mat, 0, 0, 0.02, 0.88, 0.4, 0.84, r=0.16)
        S(mat, 0, 0, -0.29, 0.88, 0.76, 0.28, r=0.13)
        for s in (-1, 1):
            S(mat, s * 0.34, 0, 0.02, 0.2, 0.6, 0.82, r=0.09)
        S(mat, 0, 0.38, 0.08, 0.5, 0.12, 0.56, r=0.05)

def coffee_table(x, z, w, d):
    with piece(x, z, 0):
        B('travertine', 0, 0, 0, w, 0.36, d, bevel=0.02, seg=3)
        books(-w * 0.22, 0.0, 0.36, 0.3)
        C('ceramic', w * 0.24, 0.36, 0.02, 0.28, 0.07, verts=48, bevel=0.01)
        sphere('fruit', w * 0.24 - 0.03, 0.0, 0.46, 0.04, 0.04, 0.04, 'fruit')
        sphere('fruit', w * 0.24 + 0.05, -0.04, 0.46, 0.04, 0.04, 0.04, 'fruit')

def rug(x, z, w, d, mat):
    B(mat, x, 0, z, w, 0.016, d, bevel=0.006)

def patch(mat, x0, z0, x1, z1):
    B(mat, (x0 + x1) / 2, 0, (z0 + z1) / 2, x1 - x0, 0.008, z1 - z0, bevel=0)

def chair(x, z, ry):
    with piece(x, z, ry):
        for dx in (-0.2, 0.2):
            for dz in (-0.2, 0.2):
                C('oak', dx, 0, dz, 0.035, 0.42, verts=10)
        S('linen_taupe', 0, 0.4, 0.01, 0.48, 0.08, 0.48, r=0.03)
        S('linen_taupe', 0, 0.44, -0.22, 0.46, 0.42, 0.06, r=0.025)

def dining(x, z, ry, seats):
    L = 2.5 if seats >= 8 else 1.95 if seats >= 6 else 1.4
    n = seats // 2
    with piece(x, z, ry):
        B('oak', 0, 0.71, 0, L, 0.045, 1.0, bevel=0.01, seg=3)
        for s in (-1, 1):
            B('oak', s * L * 0.33, 0, 0, 0.07, 0.71, 0.78, bevel=0.006)
        for i in range(n):
            cx = -L / 2 + (i + 0.5) * (L / n)
            chair(cx, -0.72, 0)
            chair(cx, 0.72, math.pi)
        vase_branches(0.0, 0.0, 0.755)

def kitchen_run(x, z, ry, length, sink_at, hob_at):
    with piece(x, z, ry):
        B('cabinet', 0, 0.1, 0.0, length, 0.78, 0.6, bevel=0.003)
        B('groove', 0, 0, 0.0, length - 0.02, 0.1, 0.54, bevel=0)                 # recessed plinth
        n = max(2, round(length / 0.6))
        for i in range(1, n):
            B('groove', -length / 2 + i * length / n, 0.1, 0.3, 0.005, 0.78, 0.004, bevel=0)
        B('groove', 0, 0.74, 0.3, length, 0.012, 0.004, bevel=0)                  # handle-less finger rail
        B('marble', 0, 0.88, 0.01, length + 0.02, 0.03, 0.65, bevel=0.003)
        B('marble', 0, 0.91, -0.3, length, 0.62, 0.025, bevel=0.002)               # slab backsplash
        B('cove', 0, 1.5, -0.27, length - 0.1, 0.01, 0.02, bevel=0)                 # under-cabinet light strip
        B('cabinet', 0, 1.52, -0.12, length, 0.08, 0.36, bevel=0.003)              # wall cabinets, cut at section
        B('sinkbowl', sink_at, 0.905, 0.03, 0.7, 0.008, 0.42, bevel=0.01)
        C('brass', sink_at, 0.91, -0.22, 0.045, 0.34)
        B('brass', sink_at, 1.22, -0.12, 0.025, 0.025, 0.22, bevel=0.008)
        B('induction', hob_at, 0.91, 0.03, 0.6, 0.008, 0.52, bevel=0.003)
        for dx, dz in ((-0.15, -0.11), (0.15, -0.11), (-0.15, 0.13), (0.15, 0.13)):
            C('blackmetal', hob_at + dx, 0.919, 0.03 + dz, 0.19, 0.001, verts=32)
            C('induction', hob_at + dx, 0.9195, 0.03 + dz, 0.17, 0.001, verts=32)
        vase_branches(-length / 2 + 0.25, 0.1, 0.91) if length > 3 else None

def fridge(x, z, ry):
    with piece(x, z, ry):
        B('cabinet', 0, 0, 0, 0.9, 1.6, 0.66, bevel=0.003)
        B('groove', 0, 0, 0.33, 0.006, 1.6, 0.004, bevel=0)
        B('bronze', -0.08, 0.6, 0.335, 0.015, 0.6, 0.012, bevel=0.003)
        B('bronze', 0.08, 0.6, 0.335, 0.015, 0.6, 0.012, bevel=0.003)
        B('oak', 0, 1.6, 0, 0.9, 0.012, 0.66, bevel=0.002)

def island(x, z, ry, length):
    with piece(x, z, ry):
        B('walnut', 0, 0.1, -0.1, length - 0.1, 0.78, 0.78, bevel=0.004)
        B('marble', 0, 0.88, 0, length + 0.06, 0.05, 1.05, bevel=0.004)
        for s in (-1, 1):                                                           # waterfall ends
            B('marble', s * (length / 2 + 0.005), 0, 0, 0.05, 0.89, 1.05, bevel=0.004)
        n = max(2, int(length / 0.68))
        for i in range(n):
            sx = -length / 2 + 0.2 + (i + 0.5) * ((length - 0.4) / n)
            C('brass', sx, 0, 0.82, 0.34, 0.012, verts=40)
            C('brass', sx, 0, 0.82, 0.035, 0.62, verts=12)
            S('boucle', sx, 0.6, 0.82, 0.42, 0.08, 0.4, r=0.035)
            S('boucle', sx, 0.66, 1.0, 0.4, 0.2, 0.06, r=0.025)
        C('ceramic', length * 0.28, 0.93, -0.12, 0.32, 0.08, verts=48, bevel=0.01)
        for k in range(4):
            sphere('fruit', length * 0.28 + math.cos(k * 1.7) * 0.07, 0.12 + math.sin(k * 1.7) * 0.07, 1.03, 0.045, 0.045, 0.045, 'fruit')
        books(-length * 0.3, 0.1, 0.93, 0.4)

def vanity(x, z, ry, length, basins=1):
    with piece(x, z, ry):
        B('walnut', 0, 0.32, 0, length, 0.48, 0.5, bevel=0.006)                    # floating vanity
        B('groove', 0, 0.56, 0.25, length - 0.04, 0.006, 0.004, bevel=0)
        B('marble', 0, 0.8, 0, length, 0.035, 0.52, bevel=0.003)
        for i in range(basins):
            bx_ = 0 if basins == 1 else (-length / 4 if i == 0 else length / 4)
            C('ceramic', bx_, 0.835, 0.03, 0.42, 0.12, 0.34, verts=56, bevel=0.012)
            C('ceramic_matte', bx_, 0.95, 0.03, 0.36, 0.006, 0.28, verts=48)
            C('steel', bx_, 0.952, 0.03, 0.04, 0.002, verts=16)
            C('brass', bx_, 0.835, -0.21, 0.035, 0.3)
            B('brass', bx_, 1.11, -0.15, 0.022, 0.022, 0.14, bevel=0.006)
        B('bronze', 0, 0.98, -0.245, length * 0.92, 0.52, 0.012, bevel=0.002)
        B('mirrorglow', 0, 1.5, -0.24, length * 0.92, 0.01, 0.02, bevel=0)

def toilet(x, z, ry):
    with piece(x, z, ry):
        B('marble', 0, 0, -0.27, 0.6, 1.05, 0.18, bevel=0.004)                       # stone-clad cistern ledge
        B('brass', 0, 0.8, -0.178, 0.2, 0.12, 0.006, bevel=0.002)                   # flush plate
        C('ceramic', 0, 0.18, 0.02, 0.38, 0.22, 0.54, verts=56, bevel=0.03)          # wall-hung pan
        C('ceramic', 0, 0.395, 0.03, 0.37, 0.025, 0.5, verts=56, bevel=0.01)         # seat

def shower(x, z, ry, w, d):
    with piece(x, z, ry):
        B('bath_tile', 0, 0, 0, w, 0.02, d, bevel=0)
        B('steel', 0, 0.021, -d / 2 + 0.08, w - 0.2, 0.004, 0.04, bevel=0)          # linear drain
        g = B('glass', 0, 0.02, d / 2 - 0.02, w, 1.55, 0.012, bevel=0)
        g.name = 'glass_screen'
        B('brass', 0, 1.56, d / 2 - 0.02, w, 0.02, 0.02, bevel=0.003)
        C('brass', 0, 1.0, -d / 2 + 0.04, 0.08, 0.02)
        B('brass', 0.25, 0.6, -d / 2 + 0.03, 0.02, 0.9, 0.02, bevel=0.005)          # hand-shower rail
        B('marble', -w / 2 + 0.25, 0.02, -d / 2 + 0.15, 0.4, 0.45, 0.3, bevel=0.004)  # stone bench

def tub(x, z, ry):
    with piece(x, z, ry):
        C('ceramic', 0, 0, 0, 1.72, 0.58, 0.82, verts=72, bevel=0.03)
        C('bathwater', 0, 0.5, 0, 1.52, 0.006, 0.62, verts=64)
        C('brass', -1.0, 0, 0, 0.05, 0.95)                                           # floor-mounted filler
        B('brass', -0.92, 0.9, 0, 0.18, 0.025, 0.025, bevel=0.008)
        B('linen', 0, 0, 0.75, 0.8, 0.012, 0.5, bevel=0.004)                         # bath mat
        C('travertine', 1.05, 0, -0.1, 0.34, 0.45, verts=40, bevel=0.01)             # stool with towels
        S('linen', 1.05, 0.45, -0.1, 0.3, 0.08, 0.22, r=0.03)

def desk(x, z, ry):
    with piece(x, z, ry):
        for dx, dz in ((-0.6, -0.26), (0.6, -0.26), (-0.6, 0.26), (0.6, 0.26)):
            B('blackmetal', dx, 0, dz, 0.03, 0.72, 0.03, bevel=0.004)
        B('walnut', 0, 0.72, 0, 1.3, 0.03, 0.62, bevel=0.006)
        B('laptop', 0.08, 0.75, 0.04, 0.34, 0.012, 0.24, bevel=0.004)
        lamp(-0.45, 0.75, -0.15)
        books(0.45, -0.1, 0.75)
        C('blackmetal', 0, 0, 0.62, 0.55, 0.03, verts=40)
        C('blackmetal', 0, 0.03, 0.62, 0.05, 0.38, verts=12)
        S('boucle', 0, 0.4, 0.62, 0.5, 0.09, 0.48, r=0.04)
        S('boucle', 0, 0.48, 0.86, 0.48, 0.42, 0.07, r=0.03)

def floor_lamp(x, z):
    with piece(x, z, 0):
        C('blackmetal', 0, 0, 0, 0.32, 0.025, verts=40)
        C('brass', 0, 0, 0, 0.025, 1.3, verts=12)
        C('linen', 0, 1.18, 0, 0.44, 0.3, verts=48)
        C('lampglow', 0, 1.2, 0, 0.14, 0.2, verts=16)
        light = bpy.data.lights.new('flamp', 'POINT'); light.energy = 30; light.color = (1.0, 0.82, 0.6); light.shadow_soft_size = 0.1
        link(bpy.data.objects.new('flamp', light)).location = (0, 0, 1.25)

def tv_unit(x, z, ry, length):
    with piece(x, z, ry):
        B('walnut', 0, 0.14, 0, length, 0.4, 0.44, bevel=0.008)
        for dx in (-length / 2 + 0.1, length / 2 - 0.1):
            B('blackmetal', dx, 0, 0, 0.03, 0.14, 0.36, bevel=0.004)
        B('screen', 0, 0.56, -0.14, length * 0.72, 0.82, 0.04, bevel=0.004)
        vase_branches(length / 2 - 0.2, 0.05, 0.54)

def house_plant(x, z, s=1.0):
    plant(x, -z, 0.62 * s)

def wall(x1, z1, x2, z2, gaps=()):
    horiz = z1 == z2
    a0, a1 = (min(x1, x2), max(x1, x2)) if horiz else (min(z1, z2), max(z1, z2))
    lo, hi = math.inf, -math.inf
    a = a0
    while a <= a1 + 1e-6:
        if inside_plate(a if horiz else x1, z1 if horiz else a, 0.02):
            lo, hi = min(lo, a), max(hi, a)
        a += 0.03
    if lo >= hi:
        return
    segs = [(lo, hi)]
    for g0, g1 in gaps:
        nxt = []
        for s0, s1 in segs:
            if g1 <= s0 or g0 >= s1:
                nxt.append((s0, s1)); continue
            if g0 > s0: nxt.append((s0, g0))
            if g1 < s1: nxt.append((g1, s1))
        segs = nxt
    for s0, s1 in segs:
        ln, mid = s1 - s0, (s0 + s1) / 2
        if ln < 0.05:
            continue
        if horiz:
            B('plaster', mid, 0, z1, ln, WALL_H, WALL_T, bevel=0)
            B('wallcap', mid, WALL_H, z1, ln, 0.012, WALL_T, bevel=0)
            for s in (-1, 1):
                B('oak', mid, 0, z1 + s * (WALL_T / 2 + 0.006), ln, 0.08, 0.012, bevel=0)   # skirting
        else:
            B('plaster', x1, 0, mid, WALL_T, WALL_H, ln, bevel=0)
            B('wallcap', x1, WALL_H, mid, WALL_T, 0.012, ln, bevel=0)
            for s in (-1, 1):
                B('oak', x1 + s * (WALL_T / 2 + 0.006), 0, mid, 0.012, 0.08, ln, bevel=0)

def center_wall(z1, z2):
    """The party wall on x = 0: only its east half (the site mirrors the residence for the west half)."""
    a0 = min(z1, z2)
    while not inside_plate(0.0, a0, 0.02):
        a0 += 0.03
    a1 = max(z1, z2)
    while not inside_plate(0.0, a1, 0.02):
        a1 -= 0.03
    ln, mid = a1 - a0, (a0 + a1) / 2
    B('plaster', WALL_T / 4, 0, mid, WALL_T / 2, WALL_H, ln, bevel=0)
    B('wallcap', WALL_T / 4, WALL_H, mid, WALL_T / 2, 0.012, ln, bevel=0)
    B('oak', WALL_T / 2 + 0.006, 0, mid, 0.012, 0.08, ln, bevel=0)

def lift_core(half):
    x0 = 0.0 if half else -2.25
    w = 2.25 if half else 4.5
    B('core', x0 + w / 2, 0, 0, w, WALL_H + 0.05, 6.0, bevel=0.004)
    for lx in ((1.05,) if half else (-1.05, 1.05)):
        B('liftdoor', lx, WALL_H + 0.05, -1.55, 1.5, 0.01, 1.7, bevel=0.002)
        B('groove', lx, WALL_H + 0.061, -1.55, 0.008, 0.002, 1.7, bevel=0)
    for i in range(9):
        B('stairs', 0.9 if half else 0.0, WALL_H + 0.05, 0.4 + i * 0.27, 1.8 if half else 3.6, 0.012, 0.13, bevel=0)

def plate_floor(half):
    """The oak floor plate: the tower's rounded rectangle (or its east half), 4 cm thick, top at y = 0."""
    pts = []
    hx, hz, r = IN_HX, IN_HZ, IN_R
    corners = [(hx - r, hz - r, 0), (-(hx - r), hz - r, 90), (-(hx - r), -(hz - r), 180), (hx - r, -(hz - r), 270)]
    for cx, cz, a0 in corners:
        for k in range(25):
            a = math.radians(a0 + k * 90 / 24)
            pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    if half:
        # keep x >= 0 and close along x = 0
        right = [(x, z) for x, z in pts if x >= 0]
        # order: from (0, -hz) round the east side to (0, hz)
        right.sort(key=lambda p: math.atan2(p[1], p[0]))
        pts = [(0.0, -hz)] + right + [(0.0, hz)]
    bm = bmesh.new()
    vs = [bm.verts.new((x, -z, 0.0)) for x, z in pts]
    f = bm.faces.new(vs)
    if f.normal.z < 0:
        f.normal_flip()
    ext = bmesh.ops.extrude_face_region(bm, geom=[f], use_keep_orig=True)
    for v in [e for e in ext['geom'] if isinstance(e, bmesh.types.BMVert)]:
        v.co.z -= 0.04
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new('plate')
    bm.to_mesh(me); bm.free()
    ob = link(bpy.data.objects.new('plate', me))
    ob.data.materials.append(MATS['oak_floor'])
    return ob

# ---------------------------------------------------------------- residences (same positions as page.html)
R = math.pi / 2

def half_residence(beds):
    if beds == 1:
        wall(0, -3.2, 10.8, -3.2, [(2.4, 3.2), (5.4, 6.2)])
        wall(3.4, -7.85, 3.4, -3.2)
        patch('bath_tile', 0.06, -7.8, 3.34, -3.26)
        tub(1.75, -7.15, 0)
        toilet(0.43, -4.5, R)
        vanity(3.09, -5.6, -R, 1.2)
        rug(5.3, -5.5, 2.6, 3.0, 'rug')
        bed(4.61, -5.5, R, 1.8, 'throw_a')
        wardrobe(8.0, -3.56, math.pi, 2.4)
        armchair(8.4, -5.9, -2.4)
        house_plant(9.6, -4.6)
        wall(2.5, 3.0, 2.5, 6.0)
        desk(1.2, 7.4, math.pi)
        house_plant(0.55, 3.6, 0.9)
    else:
        third = beds == 3
        wall(0, -3.2, 10.8, -3.2, [(2.4, 3.2), (4.2, 5.0), (8.6, 9.4)])
        wall(3.6, -7.85, 3.6, -3.2)
        wall(6.0, -7.85, 6.0, -3.2)
        bed(1.8, -6.6, 0, 1.4, 'throw_b')
        wardrobe(1.0, -3.56, math.pi, 1.6)
        patch('bath_tile', 3.66, -7.8, 5.94, -3.26)
        shower(4.8, -7.3, 0, 1.6, 1.0)
        toilet(4.03, -5.4, R)
        vanity(5.63, -5.0, -R, 1.1)
        rug(7.9, -5.5, 2.6, 3.0, 'rug')
        bed(7.21, -5.5, R, 1.8, 'throw_a')
        wardrobe(7.2, -3.56, math.pi, 1.7)
        armchair(9.2, -5.2, -2.2)
        house_plant(9.9, -3.9, 0.9)
        wall(2.6, 3.0, 2.6, 7.85, [(3.3, 4.1)])
        patch('bath_tile', 0.06, 3.06, 2.54, 7.8)
        shower(1.3, 7.25, math.pi, 1.6, 1.0)
        toilet(0.43, 4.6, R)
        vanity(2.29, 5.6, -R, 1.1)
        if third:
            wall(7.6, 3.2, 7.6, 7.85)
            wall(7.6, 3.2, 10.8, 3.2, [(9.8, 10.5)])
            bed(8.81, 4.6, R, 1.4, 'throw_b')
            house_plant(8.3, 6.8, 0.9)
    patch('kitchen_tile', 2.31, -3.14, 5.9, 1.95)
    kitchen_run(2.56, -0.9, R, 3.6, -0.9, 0.9)
    fridge(2.6, 1.42, R)
    island(4.5, -0.9, R, 2.4)
    dining(8.9, -1.0, R, 6)
    if beds == 3:
        rug(4.9, 4.7, 3.4, 2.6, 'rug2')
        sofa(4.9, 5.95, math.pi, 2.6)
        coffee_table(4.9, 4.55, 1.1, 0.6)
        armchair(3.35, 4.3, R, 'sage')
        armchair(6.5, 4.3, -R, 'sage')
        floor_lamp(6.7, 6.2)
    else:
        rug(7.4, 3.1, 3.6, 2.8, 'rug2')
        sofa(7.4, 4.35, math.pi, 2.8)
        coffee_table(7.4, 2.9, 1.2, 0.65)
        armchair(5.5, 2.7, R, 'sage')
        armchair(9.3, 2.7, -R, 'clay')
        floor_lamp(5.6, 4.5)
        house_plant(9.5, 4.7)
    center_wall(-7.85, -3.0)
    center_wall(3.0, 7.85)
    lift_core(True)

def full_residence():
    wall(-10.8, -3.2, 10.8, -3.2, [(-7.2, -6.4), (-3.4, -2.6), (-1.0, -0.2), (4.2, 5.0), (8.4, 9.2)])
    wall(-4.4, -7.85, -4.4, -3.2)
    wall(-1.2, -7.85, -1.2, -3.2)
    wall(3.4, -7.85, 3.4, -3.2)
    wall(5.9, -7.85, 5.9, -3.2)
    rug(-6.2, -5.5, 2.8, 3.2, 'rug')
    bed(-5.61, -5.5, -R, 1.93, 'throw_a')
    wardrobe(-8.5, -3.56, math.pi, 2.2)
    armchair(-8.5, -5.6, 2.3)
    house_plant(-9.9, -4.0, 0.9)
    patch('bath_tile', -4.34, -7.8, -1.26, -3.26)
    tub(-2.8, -7.15, 0)
    vanity(-1.51, -5.4, -R, 1.8, 2)
    toilet(-3.95, -4.45, R)
    bed(1.1, -6.6, 0, 1.6, 'throw_b')
    desk(2.4, -3.57, math.pi)
    patch('bath_tile', 3.46, -7.8, 5.84, -3.26)
    shower(4.65, -7.3, 0, 1.5, 1.0)
    toilet(3.83, -5.4, R)
    vanity(5.59, -4.9, -R, 1.0)
    rug(7.7, -5.5, 2.4, 2.8, 'rug')
    bed(7.11, -5.5, R, 1.6, 'throw_a')
    wardrobe(7.0, -3.56, math.pi, 1.5)
    armchair(9.2, -5.2, -2.2, 'clay')
    house_plant(9.9, -3.9, 0.9)
    patch('kitchen_tile', -5.9, -3.14, -2.31, 1.95)
    kitchen_run(-2.56, -0.9, -R, 3.6, 0.9, -0.9)
    fridge(-2.6, 1.42, -R)
    island(-4.5, -0.9, -R, 2.6)
    dining(-8.6, -0.6, R, 8)
    rug(-2.0, 5.0, 4.6, 3.0, 'rug2')
    sofa(-2.0, 6.6, math.pi, 3.2)
    coffee_table(-2.0, 5.0, 1.4, 0.7)
    armchair(-4.6, 4.8, R, 'sage')
    armchair(0.6, 4.8, -R, 'clay')
    floor_lamp(-4.4, 6.9)
    house_plant(0.6, 7.0)
    armchair(-7.4, 5.2, 2.4)
    floor_lamp(-8.4, 4.3)
    house_plant(-6.3, 6.9, 1.1)
    rug(4.6, 0, 3.0, 3.4, 'rug')
    tv_unit(2.52, 0, R, 2.2)
    sofa(6.2, 0, -R, 2.8, 'sage')
    coffee_table(4.4, 0, 0.7, 1.2)
    desk(10.4, -1.6, -R)
    house_plant(10.2, 1.8, 0.9)
    wall(2.25, 3.0, 2.25, 5.8)
    wall(4.6, 3.0, 4.6, 5.8)
    wall(2.25, 5.8, 4.6, 5.8, [(3.0, 3.8)])
    patch('bath_tile', 2.31, 3.06, 4.54, 5.74)
    toilet(4.17, 4.3, -R)
    vanity(2.56, 4.3, R, 0.9)
    wall(7.6, 3.2, 7.6, 7.85)
    wall(7.6, 3.2, 10.8, 3.2, [(9.8, 10.5)])
    bed(8.81, 4.6, R, 1.4, 'throw_b')
    house_plant(8.3, 6.8, 0.9)
    house_plant(6.6, 6.6, 1.1)
    lift_core(False)

# ---------------------------------------------------------------- bake + export
def objects_of(kind):
    return [o for o in COLL.objects if o.type == kind]

def realise(ob):
    """Apply modifiers and the transform, so the mesh is final and in world space."""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    me.transform(ob.matrix_world)
    old = ob.data
    ob.modifiers.clear()
    ob.data = me
    ob.matrix_world = Matrix.Identity(4)
    if old.users == 0:
        bpy.data.meshes.remove(old)

def drop_undersides(ob):
    """Faces pointing down are never seen from the cutaway camera: don't spend texture or triangles on them."""
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bad = [f for f in bm.faces if f.normal.z < -0.6]
    bmesh.ops.delete(bm, geom=bad, context='FACES')
    bm.to_mesh(ob.data); bm.free()

def run():
    build_materials()
    extra_materials()
    MATS['glass'].name = 'glass'
    world_sky(sun_elev=52, sun_rot=205, strength=float(os.environ.get('SKY', 0.3)))
    for ob in COLL.objects:
        if ob.type == 'LIGHT' and ob.data.type == 'SUN':
            ob.data.energy = float(os.environ.get('SUN', 1.4))
    scene.view_settings.exposure = float(os.environ.get('EXPO', -1.15))
    half = LAYOUT.startswith('half')
    plate_floor(half)
    if half:
        half_residence(int(LAYOUT[-1]))
    else:
        full_residence()

    meshes = objects_of('MESH')
    for ob in meshes:
        realise(ob)
    glass = [o for o in meshes if o.data.materials and o.data.materials[0].name.startswith('glass')]
    for g in glass:
        g.visible_shadow = False
    solid = [o for o in meshes if o not in glass]
    for ob in solid:
        drop_undersides(ob)
    print('objects', len(solid), 'glass', len(glass), flush=True)

    # one mesh, one UV atlas
    bpy.ops.object.select_all(action='DESELECT')
    for ob in solid:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = solid[0]
    bpy.ops.object.join()
    main = bpy.context.view_layer.objects.active
    main.name = 'residence'
    me = main.data
    while me.uv_layers:
        me.uv_layers.remove(me.uv_layers[0])
    me.uv_layers.new(name='bake')
    print('tris', sum(len(p.vertices) - 2 for p in me.polygons), flush=True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.0015, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    try:
        bpy.ops.uv.pack_islands(rotate=True, margin=0.0015)
    except Exception as e:
        print('pack_islands skipped:', e)
    bpy.ops.object.mode_set(mode='OBJECT')

    img = bpy.data.images.new('bake', TEX, TEX, alpha=False, float_buffer=True)
    for slot in main.material_slots:
        nt = slot.material.node_tree
        node = nt.nodes.new('ShaderNodeTexImage')
        node.image = img
        for n in nt.nodes:
            n.select = False
        node.select = True
        nt.nodes.active = node
    cy.samples = BAKE_SAMPLES
    cy.use_adaptive_sampling = False
    bk = scene.render.bake
    bk.margin = 6
    bk.margin_type = 'EXTEND'
    bk.use_clear = True
    bk.target = 'IMAGE_TEXTURES'
    bpy.ops.object.select_all(action='DESELECT')
    main.select_set(True)
    bpy.context.view_layer.objects.active = main
    print('baking', TEX, 'px at', BAKE_SAMPLES, 'samples', flush=True)
    bpy.ops.object.bake(type='COMBINED')

    base = os.path.splitext(OUT_GLB)[0]
    tex_path = base + '-bake.jpg'
    scene.render.image_settings.file_format = 'JPEG'
    scene.render.image_settings.quality = 90
    img.save_render(tex_path, scene=scene)
    print('saved', tex_path, flush=True)

    # export: the baked mesh with a single textured material, plus the glass
    baked = bpy.data.materials.new('baked')
    baked.use_nodes = True
    nt = baked.node_tree
    bsdf = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'][0]
    tn = nt.nodes.new('ShaderNodeTexImage')
    tn.image = bpy.data.images.load(tex_path)
    nt.links.new(tn.outputs['Color'], bsdf.inputs['Base Color'])
    me.materials.clear()
    me.materials.append(baked)
    for p in me.polygons:
        p.material_index = 0
    if glass:
        bpy.ops.object.select_all(action='DESELECT')
        for g in glass:
            g.select_set(True)
        bpy.context.view_layer.objects.active = glass[0]
        bpy.ops.object.join()
        gl = bpy.context.view_layer.objects.active
        gl.name = 'glass'
        gl.data.materials.clear()
        gm = bpy.data.materials.new('glass_pane'); gm.use_nodes = True
        gl.data.materials.append(gm)
        while gl.data.uv_layers:
            gl.data.uv_layers.remove(gl.data.uv_layers[0])
    bpy.ops.object.select_all(action='DESELECT')
    main.select_set(True)
    for o in COLL.objects:
        if o.name.startswith('glass') and o.type == 'MESH':
            o.select_set(True)
    kw = dict(filepath=OUT_GLB, export_format='GLB', use_selection=True, export_apply=True, export_yup=True,
              export_normals=False, export_materials='EXPORT', export_image_format='JPEG', export_jpeg_quality=88,
              export_cameras=False, export_lights=False)
    try:
        bpy.ops.export_scene.gltf(**kw, export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=7,
                                  export_draco_position_quantization=14, export_draco_texcoord_quantization=12)
    except Exception as e:
        print('draco export failed, exporting plain:', e, flush=True)
        bpy.ops.export_scene.gltf(**kw)
    print('wrote', OUT_GLB, os.path.getsize(OUT_GLB), flush=True)

run()
