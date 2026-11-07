"""Calder Quay: photoreal room fly-ins rendered with Blender Cycles.

Usage:
  python3 rooms.py ROOM OUT_DIR [--frames N] [--only i,j] [--res W H] [--samples S]
ROOM: living | kitchen | bedroom | bath
Each frame is a camera position on a path that starts high above the room (ceiling hidden,
a cutaway like an architect's model) and swoops down to eye level.
"""
import bpy, bmesh, math, sys, os, random
from mathutils import Vector, Euler

ARGS = sys.argv[1:]
ROOM, OUT = ARGS[0], ARGS[1]
def arg(name, n=1, default=None):
    if name in ARGS:
        i = ARGS.index(name)
        v = ARGS[i + 1:i + 1 + n]
        return v if n > 1 else v[0]
    return default
FRAMES = int(arg('--frames', default=24))
ONLY = [int(x) for x in arg('--only', default='').split(',') if x != '']
RES = [int(x) for x in arg('--res', 2, ['1280', '720'])]
SAMPLES = int(arg('--samples', default=48))
random.seed(7)

# ---------------------------------------------------------------- scene setup
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
cy = scene.cycles
cy.device = 'CPU'
cy.samples = SAMPLES
cy.use_adaptive_sampling = True
cy.adaptive_threshold = 0.02
cy.use_denoising = True
try:
    cy.denoiser = 'OPENIMAGEDENOISE'
except Exception:
    pass
cy.max_bounces = 6
cy.diffuse_bounces = 3
cy.glossy_bounces = 3
cy.transmission_bounces = 4
cy.transparent_max_bounces = 24
cy.caustics_reflective = False
cy.caustics_refractive = False
cy.blur_glossy = 1.0
cy.sample_clamp_indirect = 6.0
scene.render.resolution_x, scene.render.resolution_y = RES
scene.render.resolution_percentage = 100
scene.render.use_persistent_data = True
scene.render.image_settings.file_format = 'JPEG'
scene.render.image_settings.quality = 92
try:
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
except Exception:
    pass
scene.view_settings.exposure = -0.35

# ---------------------------------------------------------------- materials
def node_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    return m, nt, bsdf, out

def setin(bsdf, key, val):
    if key in bsdf.inputs:
        bsdf.inputs[key].default_value = val

def hexc(h, a=1.0):
    h = h.lstrip('#')
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, a)

def tex_coord(nt, scale=(1, 1, 1)):
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = scale
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    return mp.outputs['Vector']

def bump(nt, bsdf, height_socket, strength=0.1, distance=0.02):
    b = nt.nodes.new('ShaderNodeBump')
    b.inputs['Strength'].default_value = strength
    if 'Distance' in b.inputs:
        b.inputs['Distance'].default_value = distance
    nt.links.new(height_socket, b.inputs['Height'])
    nt.links.new(b.outputs['Normal'], bsdf.inputs['Normal'])

def ramp(nt, fac_socket, stops):
    r = nt.nodes.new('ShaderNodeValToRGB')
    els = r.color_ramp.elements
    els[0].position, els[0].color = stops[0][0], stops[0][1]
    els[1].position, els[1].color = stops[-1][0], stops[-1][1]
    for pos, col in stops[1:-1]:
        e = els.new(pos)
        e.color = col
    nt.links.new(fac_socket, r.inputs['Fac'])
    return r

MATS = {}
def plain(name, color, rough=0.5, metal=0.0, sheen=0.0, coat=0.0, noise_bump=0.0, bump_scale=60.0):
    m, nt, bsdf, _ = node_mat(name)
    setin(bsdf, 'Base Color', hexc(color))
    setin(bsdf, 'Roughness', rough)
    setin(bsdf, 'Metallic', metal)
    if sheen:
        setin(bsdf, 'Sheen Weight', sheen)
        setin(bsdf, 'Sheen Roughness', 0.6)
    if coat:
        setin(bsdf, 'Coat Weight', coat)
        setin(bsdf, 'Coat Roughness', 0.08)
    if noise_bump:
        n = nt.nodes.new('ShaderNodeTexNoise')
        n.inputs['Scale'].default_value = bump_scale
        n.inputs['Detail'].default_value = 8
        nt.links.new(tex_coord(nt), n.inputs['Vector'])
        bump(nt, bsdf, n.outputs['Fac'], noise_bump, 0.005)
    MATS[name] = m
    return m

def wood(name, light, dark, along='x', rough=0.42, planks=False):
    """Oak/walnut: fine straight grain running along one axis, with gentle figure; optional planks."""
    m, nt, bsdf, _ = node_mat(name)
    stretch = {'x': (0.08, 1.0, 1.0), 'y': (1.0, 0.08, 1.0), 'z': (1.0, 1.0, 0.08)}[along]
    across = {'x': 'Y', 'y': 'X', 'z': 'X'}[along]
    vec = tex_coord(nt, stretch)
    wave = nt.nodes.new('ShaderNodeTexWave')
    wave.wave_type = 'BANDS'
    try:
        wave.bands_direction = across
    except Exception:
        pass
    wave.inputs['Scale'].default_value = 9.0
    wave.inputs['Distortion'].default_value = 2.2
    wave.inputs['Detail'].default_value = 3.0
    wave.inputs['Detail Scale'].default_value = 0.6
    nt.links.new(vec, wave.inputs['Vector'])
    col = ramp(nt, wave.outputs['Fac'], [(0.0, hexc(dark)), (0.35, hexc(light)), (1.0, hexc(light))])
    # large soft tone variation so boards don't look printed
    fig = nt.nodes.new('ShaderNodeTexNoise')
    fig.inputs['Scale'].default_value = 1.2
    nt.links.new(tex_coord(nt, stretch), fig.inputs['Vector'])
    tone = nt.nodes.new('ShaderNodeMix'); tone.data_type = 'RGBA'; tone.blend_type = 'MULTIPLY'
    tone.inputs['Factor'].default_value = 0.25
    nt.links.new(col.outputs['Color'], tone.inputs['A'])
    nt.links.new(fig.outputs['Color'], tone.inputs['B'])
    color_out = tone.outputs['Result']
    if planks:
        br = nt.nodes.new('ShaderNodeTexBrick')
        br.inputs['Scale'].default_value = 1.0
        br.inputs['Mortar Size'].default_value = 0.003
        br.inputs['Brick Width'].default_value = 2.2
        br.inputs['Row Height'].default_value = 0.22
        br.inputs['Color1'].default_value = (1, 1, 1, 1)
        br.inputs['Color2'].default_value = (0.85, 0.83, 0.8, 1)
        br.inputs['Mortar'].default_value = (0.4, 0.34, 0.28, 1)
        br.offset = 0.37
        tc = nt.nodes.new('ShaderNodeTexCoord')
        nt.links.new(tc.outputs['Object'], br.inputs['Vector'])
        mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
        mix.inputs['Factor'].default_value = 1.0
        nt.links.new(color_out, mix.inputs['A'])
        nt.links.new(br.outputs['Color'], mix.inputs['B'])
        color_out = mix.outputs['Result']
        bump(nt, bsdf, br.outputs['Fac'], 0.25, 0.002)
    nt.links.new(color_out, bsdf.inputs['Base Color'])
    setin(bsdf, 'Roughness', rough)
    if planks:
        setin(bsdf, 'Coat Weight', 0.2)
        setin(bsdf, 'Coat Roughness', 0.3)
    MATS[name] = m
    return m

def stone(name, base, vein, scale=1.6, vein_width=0.035, rough=0.18, travertine=False):
    """Marble (thin veins) or travertine (soft horizontal banding)."""
    m, nt, bsdf, _ = node_mat(name)
    if travertine:
        vec = tex_coord(nt, (0.6, 0.6, 9.0))
        n = nt.nodes.new('ShaderNodeTexNoise')
        n.inputs['Scale'].default_value = 2.5
        n.inputs['Detail'].default_value = 10
        n.inputs['Roughness'].default_value = 0.65
        nt.links.new(vec, n.inputs['Vector'])
        col = ramp(nt, n.outputs['Fac'], [(0.3, hexc(vein)), (0.6, hexc(base)), (1.0, hexc(base))])
        nt.links.new(col.outputs['Color'], bsdf.inputs['Base Color'])
        pits = nt.nodes.new('ShaderNodeTexNoise')
        pits.inputs['Scale'].default_value = 90
        nt.links.new(vec, pits.inputs['Vector'])
        bump(nt, bsdf, pits.outputs['Fac'], 0.15, 0.002)
        setin(bsdf, 'Roughness', 0.55)
    else:
        vec = tex_coord(nt, (scale, scale, scale))
        cloud = nt.nodes.new('ShaderNodeTexNoise')
        cloud.inputs['Scale'].default_value = 0.8
        cloud.inputs['Detail'].default_value = 4
        nt.links.new(vec, cloud.inputs['Vector'])
        base_col = ramp(nt, cloud.outputs['Fac'], [(0.3, hexc('#e6e2db')), (0.7, hexc(base))])
        n = nt.nodes.new('ShaderNodeTexNoise')
        n.inputs['Scale'].default_value = 0.55
        n.inputs['Detail'].default_value = 10
        n.inputs['Roughness'].default_value = 0.6
        n.inputs['Distortion'].default_value = 1.4
        nt.links.new(vec, n.inputs['Vector'])
        veins = ramp(nt, n.outputs['Fac'], [(0.0, (1, 1, 1, 1)), (0.5 - vein_width, (1, 1, 1, 1)), (0.5, hexc(vein)), (0.5 + vein_width, (1, 1, 1, 1)), (1.0, (1, 1, 1, 1))])
        mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
        mix.inputs['Factor'].default_value = 0.6
        nt.links.new(base_col.outputs['Color'], mix.inputs['A'])
        nt.links.new(veins.outputs['Color'], mix.inputs['B'])
        nt.links.new(mix.outputs['Result'], bsdf.inputs['Base Color'])
        setin(bsdf, 'Roughness', rough)
        setin(bsdf, 'Coat Weight', 0.3)
        setin(bsdf, 'Coat Roughness', 0.05)
    MATS[name] = m
    return m

def emissive(name, color, strength):
    m, nt, bsdf, out = node_mat(name)
    nt.nodes.remove(bsdf)
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = hexc(color)
    em.inputs['Strength'].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0])
    MATS[name] = m
    return m

def window_glass(name='glass'):
    """Clear glazing: mostly transparent (cheap for light), with a fresnel reflection."""
    m, nt, bsdf, out = node_mat(name)
    nt.nodes.remove(bsdf)
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    tr.inputs['Color'].default_value = (0.93, 0.96, 0.97, 1)
    gl = nt.nodes.new('ShaderNodeBsdfGlossy')
    gl.inputs['Roughness'].default_value = 0.0
    fr = nt.nodes.new('ShaderNodeFresnel')
    fr.inputs['IOR'].default_value = 1.5
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    front = nt.nodes.new('ShaderNodeMath'); front.operation = 'SUBTRACT'
    front.inputs[0].default_value = 1.0
    nt.links.new(geo.outputs['Backfacing'], front.inputs[1])
    fac = nt.nodes.new('ShaderNodeMath'); fac.operation = 'MULTIPLY'
    nt.links.new(fr.outputs[0], fac.inputs[0])
    nt.links.new(front.outputs[0], fac.inputs[1])
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(fac.outputs[0], mix.inputs['Fac'])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(gl.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    MATS[name] = m
    return m

def sheer(name='sheer'):
    m, nt, bsdf, out = node_mat(name)
    nt.nodes.remove(bsdf)
    tl = nt.nodes.new('ShaderNodeBsdfTranslucent')
    tl.inputs['Color'].default_value = hexc('#f4f0e8')
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix = nt.nodes.new('ShaderNodeMixShader')
    mix.inputs['Fac'].default_value = 0.55
    nt.links.new(tl.outputs[0], mix.inputs[1])
    nt.links.new(tr.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    MATS[name] = m
    return m

def fire(name='fire'):
    m, nt, bsdf, out = node_mat(name)
    nt.nodes.remove(bsdf)
    vec = tex_coord(nt, (6, 1, 2))
    n = nt.nodes.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = 3.0
    n.inputs['Detail'].default_value = 6
    nt.links.new(vec, n.inputs['Vector'])
    grad = nt.nodes.new('ShaderNodeTexGradient')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    # flames: brighter low, flicker shapes from noise, fading upwards (Generated Z)
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'SUBTRACT'
    nt.links.new(n.outputs['Fac'], mul.inputs[0])
    nt.links.new(sep.outputs['Z'], mul.inputs[1])
    col = ramp(nt, mul.outputs[0], [(0.0, (0, 0, 0, 1)), (0.12, hexc('#ff5a10')), (0.35, hexc('#ffb347')), (0.6, hexc('#fff1c4'))])
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Strength'].default_value = 9.0
    nt.links.new(col.outputs['Color'], em.inputs['Color'])
    nt.links.new(em.outputs[0], out.inputs[0])
    MATS[name] = m
    return m

def water(name='water'):
    m, nt, bsdf, _ = node_mat(name)
    setin(bsdf, 'Base Color', hexc('#21414f'))
    setin(bsdf, 'Roughness', 0.06)
    n = nt.nodes.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = 0.6
    n.inputs['Detail'].default_value = 6
    nt.links.new(tex_coord(nt, (1, 3, 1)), n.inputs['Vector'])
    bump(nt, bsdf, n.outputs['Fac'], 0.08, 1.0)
    MATS[name] = m
    return m

def art(name, a, b):
    m, nt, bsdf, _ = node_mat(name)
    vec = tex_coord(nt, (1.2, 1.2, 1.2))
    n = nt.nodes.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = 1.2
    n.inputs['Detail'].default_value = 3
    nt.links.new(vec, n.inputs['Vector'])
    col = ramp(nt, n.outputs['Fac'], [(0.35, hexc(a)), (0.65, hexc(b))])
    nt.links.new(col.outputs['Color'], bsdf.inputs['Base Color'])
    setin(bsdf, 'Roughness', 0.9)
    MATS[name] = m
    return m

def build_materials():
    wood('oak_floor', '#cdb08b', '#b0906a', along='x', rough=0.38, planks=True)
    wood('oak', '#c9a880', '#ad8a63', along='x', rough=0.45)
    wood('oak_v', '#c9a880', '#ad8a63', along='z', rough=0.45)
    wood('walnut', '#6b4a33', '#4e3323', along='x', rough=0.4)
    plain('plaster', '#ece7df', 0.88, noise_bump=0.04, bump_scale=30)
    plain('ceiling', '#f1eee9', 0.9)
    plain('boucle', '#ebe5da', 1.0, sheen=0.7, noise_bump=0.35, bump_scale=420)
    plain('linen', '#e9e3d7', 0.95, sheen=0.4, noise_bump=0.12, bump_scale=600)
    plain('linen_taupe', '#b9ab98', 0.95, sheen=0.4, noise_bump=0.12, bump_scale=600)
    plain('rug', '#ddd4c4', 1.0, sheen=0.3, noise_bump=0.5, bump_scale=250)
    plain('cushion_clay', '#b78a6a', 1.0, sheen=0.5, noise_bump=0.2, bump_scale=300)
    plain('brass', '#c9a45c', 0.22, metal=1.0)
    plain('steel', '#b8b8b6', 0.18, metal=1.0)
    plain('blackmetal', '#1c1b1a', 0.38, metal=0.6)
    plain('ceramic', '#f3f1ec', 0.08, coat=0.6)
    plain('ceramic_matte', '#e6e0d5', 0.45)
    plain('mattress', '#f2efe9', 0.9, sheen=0.3)
    plain('leaf', '#4e6b3b', 0.55, sheen=0.2)
    plain('soil', '#2b2219', 0.95)
    plain('book_a', '#7d6a55', 0.7)
    plain('book_b', '#d8cfbf', 0.7)
    plain('book_c', '#3e4a4a', 0.7)
    plain('mirror', '#ffffff', 0.0, metal=1.0)
    plain('firebox', '#0b0a09', 0.6)
    plain('city', '#8e8f92', 0.7)
    plain('land', '#3d4a3c', 0.95)
    stone('travertine', '#e3d7c3', '#cdbfa6', travertine=True)
    stone('marble', '#f3f1ed', '#b7b1a7', scale=0.9, vein_width=0.012)
    stone('marble_floor', '#ece9e3', '#b0aaa0', scale=0.6, vein_width=0.01)
    emissive('cove', '#ffe2b8', 6.0)
    emissive('lampglow', '#ffd59a', 14.0)
    emissive('mirrorglow', '#ffe6c4', 5.0)
    window_glass()
    sheer()
    fire()
    water()
    art('art_a', '#d9c9b0', '#8c7a63')
    art('art_b', '#c8cdc8', '#6f7b78')

# ---------------------------------------------------------------- geometry helpers
COLL = bpy.data.collections.new('Room')
scene.collection.children.link(COLL)

def link(obj):
    COLL.objects.link(obj)
    return obj

def box(name, cx, cy, z0, sx, sy, sz, mat, bevel=0.006, seg=2, smooth=False, rz=0.0):
    """Box by its footprint centre (cx, cy), bottom height z0 and size."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(me)
    bm.free()
    ob = link(bpy.data.objects.new(name, me))
    ob.scale = (sx, sy, sz)
    ob.location = (cx, cy, z0 + sz / 2)
    ob.rotation_euler = (0, 0, rz)
    ob.data.materials.append(MATS[mat])
    if bevel > 0:
        md = ob.modifiers.new('bevel', 'BEVEL')
        md.width = bevel
        md.segments = seg
        md.limit_method = 'NONE'
        md.use_clamp_overlap = True
        # bevel works in object space; compensate the non-uniform scale by applying it
    apply_scale(ob)
    if smooth:
        for p in ob.data.polygons:
            p.use_smooth = True
    return ob

def apply_scale(ob):
    me = ob.data
    s = ob.scale.copy()
    for v in me.vertices:
        v.co.x *= s.x; v.co.y *= s.y; v.co.z *= s.z
    ob.scale = (1, 1, 1)

def cyl(name, cx, cy, z0, rx, ry, h, mat, verts=48, bevel=0.0, seg=2, smooth=True):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=1.0, radius2=1.0, depth=1.0)
    bm.to_mesh(me)
    bm.free()
    ob = link(bpy.data.objects.new(name, me))
    ob.scale = (rx, ry, h)
    ob.location = (cx, cy, z0 + h / 2)
    apply_scale(ob)
    ob.data.materials.append(MATS[mat])
    if smooth:
        for p in ob.data.polygons:
            p.use_smooth = True
    if bevel > 0:
        md = ob.modifiers.new('bevel', 'BEVEL')
        md.width = bevel
        md.segments = seg
        md.limit_method = 'ANGLE'
        md.angle_limit = math.radians(50)
        md.harden_normals = False
    return ob

def sphere(name, cx, cy, cz, rx, ry, rz, mat):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1.0)
    bm.to_mesh(me)
    bm.free()
    ob = link(bpy.data.objects.new(name, me))
    ob.scale = (rx, ry, rz)
    ob.location = (cx, cy, cz)
    apply_scale(ob)
    ob.data.materials.append(MATS[mat])
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob

def soft(name, cx, cy, z0, sx, sy, sz, mat, r=0.06, rz=0.0):
    """Upholstery: a box with a big rounded bevel and smooth shading."""
    return box(name, cx, cy, z0, sx, sy, sz, mat, bevel=r, seg=5, smooth=True, rz=rz)

def plant(cx, cy, s=1.0):
    cyl('pot', cx, cy, 0, 0.22 * s, 0.22 * s, 0.42 * s, 'ceramic_matte', bevel=0.02)
    cyl('soil', cx, cy, 0.41 * s, 0.2 * s, 0.2 * s, 0.01, 'soil')
    rnd = random.Random(int(cx * 100 + cy * 10))
    for i in range(14):
        a = rnd.random() * math.tau
        h = (0.6 + rnd.random() * 0.9) * s
        rad = (0.15 + rnd.random() * 0.25) * s
        sphere('leaf', cx + math.cos(a) * rad, cy + math.sin(a) * rad, 0.42 * s + h, 0.16 * s, 0.05 * s, 0.24 * s, 'leaf').rotation_euler = (rnd.random(), rnd.random(), a)
        cyl('stem', cx + math.cos(a) * rad * 0.5, cy + math.sin(a) * rad * 0.5, 0.42 * s, 0.006, 0.006, h, 'walnut', verts=6)

def vase_branches(cx, cy, z0):
    cyl('vase', cx, cy, z0, 0.09, 0.09, 0.32, 'ceramic', bevel=0.01)
    rnd = random.Random(int(cx * 77))
    for i in range(5):
        st = cyl('branch', cx, cy, z0 + 0.25, 0.005, 0.005, 0.5 + rnd.random() * 0.3, 'walnut', verts=6)
        st.rotation_euler = (rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), 0)

def books(cx, cy, z0, rz=0.0):
    h = z0
    for i, (m, t) in enumerate([('book_b', 0.04), ('book_a', 0.03), ('book_c', 0.025)]):
        box('book', cx, cy, h, 0.28 - i * 0.03, 0.2 - i * 0.02, t, m, bevel=0.003, rz=rz + i * 0.15)
        h += t

def table_lamp(cx, cy, z0):
    cyl('lampbase', cx, cy, z0, 0.09, 0.09, 0.32, 'ceramic_matte', bevel=0.02)
    cyl('lampshade', cx, cy, z0 + 0.32, 0.17, 0.17, 0.24, 'linen', smooth=True)
    cyl('lampbulb', cx, cy, z0 + 0.36, 0.06, 0.06, 0.14, 'lampglow')
    light = bpy.data.lights.new('lamp', 'POINT')
    light.energy = 25
    light.color = (1.0, 0.82, 0.6)
    light.shadow_soft_size = 0.08
    ob = link(bpy.data.objects.new('lamp', light))
    ob.location = (cx, cy, z0 + 0.43)

# ---------------------------------------------------------------- shell: floor, walls, ceiling, windows, view
CEIL = 2.9
SHELL = {'ceiling': None}

def shell(w, d, windows, floor_mat='oak_floor', wall_mat='plaster', cove=True):
    """Room from x in [0, w], y in [0, d]. windows: list of walls ('S','E','N','W') that are full glass."""
    box('floor', w / 2, d / 2, -0.1, w + 0.6, d + 0.6, 0.1, floor_mat, bevel=0)
    t = 0.18
    walls = {'S': (w / 2, -t / 2, w + 2 * t, t), 'N': (w / 2, d + t / 2, w + 2 * t, t),
             'W': (-t / 2, d / 2, t, d), 'E': (w + t / 2, d / 2, t, d)}
    for side, (cx, cy_, sx, sy) in walls.items():
        if side in windows:
            glazing(side, w, d)
        else:
            box('wall_' + side, cx, cy_, 0, sx, sy, CEIL, wall_mat, bevel=0)
    ceil = box('ceiling', w / 2, d / 2, CEIL, w + 0.4, d + 0.4, 0.12, 'ceiling', bevel=0)
    SHELL['ceiling'] = ceil
    if cove:
        # a glowing slot between ceiling and walls, the soft perimeter light in luxury interiors
        for side in 'SNEW':
            if side in windows:
                continue
            if side in 'SN':
                y = 0.06 if side == 'S' else d - 0.06
                box('cove', w / 2, y, CEIL - 0.03, w - 0.2, 0.04, 0.02, 'cove', bevel=0)
            else:
                x = 0.06 if side == 'W' else w - 0.06
                box('cove', x, d / 2, CEIL - 0.03, 0.04, d - 0.2, 0.02, 'cove', bevel=0)
    # skirting shadow gap
    view_outside()

def glazing(side, w, d):
    span = w if side in 'SN' else d
    n = max(2, round(span / 1.6))
    for i in range(n + 1):
        p = i * span / n
        if side in 'SN':
            y = 0 if side == 'S' else d
            box('mullion', p, y, 0, 0.06, 0.12, CEIL, 'blackmetal', bevel=0.004)
        else:
            x = 0 if side == 'W' else w
            box('mullion', x, p, 0, 0.12, 0.06, CEIL, 'blackmetal', bevel=0.004)
    if side in 'SN':
        y = 0 if side == 'S' else d
        g = box('glass', w / 2, y, 0, w, 0.012, CEIL, 'glass', bevel=0)
        box('sill', w / 2, y, 0, w, 0.14, 0.03, 'blackmetal', bevel=0.003)
        box('head', w / 2, y, CEIL - 0.06, w, 0.14, 0.06, 'blackmetal', bevel=0.003)
        portal(w / 2, y + (-0.3 if side == 'S' else 0.3), CEIL / 2, w, CEIL, side)
    else:
        x = 0 if side == 'W' else w
        g = box('glass', x, d / 2, 0, 0.012, d, CEIL, 'glass', bevel=0)
        box('sill', x, d / 2, 0, 0.14, d, 0.03, 'blackmetal', bevel=0.003)
        box('head', x, d / 2, CEIL - 0.06, 0.14, d, 0.06, 'blackmetal', bevel=0.003)
        portal(x + (-0.3 if side == 'W' else 0.3), d / 2, CEIL / 2, d, CEIL, side)
    g.visible_shadow = False

def portal(x, y, z, span, h, side):
    """Light portal: tells Cycles where daylight enters, which cleans up interior noise a lot."""
    l = bpy.data.lights.new('portal', 'AREA')
    l.shape = 'RECTANGLE'
    l.size, l.size_y = span, h
    try:
        l.cycles.is_portal = True
    except Exception:
        pass
    ob = link(bpy.data.objects.new('portal', l))
    ob.location = (x, y, z)
    rot = {'S': (math.pi / 2, 0, 0), 'N': (-math.pi / 2, 0, 0), 'W': (0, -math.pi / 2, 0), 'E': (0, math.pi / 2, 0)}[side]
    ob.rotation_euler = rot

def view_outside():
    """We're 30 floors up: harbour water below, a low shoreline and towers on the horizon."""
    box('water', 0, 0, -95, 3000, 3000, 1, 'water', bevel=0)
    rnd = random.Random(3)
    for i in range(70):
        a = rnd.uniform(-1.0, 2.2)
        dist = rnd.uniform(700, 1100)
        x, y = math.cos(a) * dist, math.sin(a) * dist
        h = rnd.uniform(20, 140)
        box('tower', x, y, -95, rnd.uniform(20, 45), rnd.uniform(20, 45), h, 'city', bevel=0)
    for i in range(12):
        a = -1.0 + i * 0.28
        box('shore', math.cos(a) * 900, math.sin(a) * 900, -95, 400, 400, 6, 'land', bevel=0)

def world_sky(sun_elev=22, sun_rot=210, strength=0.9):
    w = bpy.data.worlds.new('sky')
    scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    sky = nt.nodes.new('ShaderNodeTexSky')
    types = [i.identifier for i in sky.bl_rna.properties['sky_type'].enum_items]
    for pref in ('MULTIPLE_SCATTERING', 'NISHITA', 'SINGLE_SCATTERING', 'HOSEK_WILKIE', 'PREETHAM'):
        if pref in types:
            sky.sky_type = pref
            break
    for attr, val in (('sun_elevation', math.radians(sun_elev)), ('sun_rotation', math.radians(sun_rot)),
                      ('altitude', 120.0), ('air_density', 1.2), ('dust_density', 2.0), ('sun_intensity', 0.6)):
        if hasattr(sky, attr):
            try:
                setattr(sky, attr, val)
            except Exception:
                pass
    bg.inputs['Strength'].default_value = strength
    nt.links.new(sky.outputs[0], bg.inputs[0])
    nt.links.new(bg.outputs[0], out.inputs[0])
    sun = bpy.data.lights.new('sun', 'SUN')
    sun.energy = 2.6
    sun.angle = math.radians(1.2)
    sun.color = (1.0, 0.93, 0.84)
    so = link(bpy.data.objects.new('sun', sun))
    so.rotation_euler = Euler((math.radians(90 - sun_elev), 0, math.radians(sun_rot + 90)))

def chubby_chair(x, y, rz, mat='boucle'):
    soft('chair', x, y, 0.0, 0.92, 0.86, 0.42, mat, r=0.16, rz=rz)
    bxo, byo = -math.sin(rz) * -0.3, math.cos(rz) * -0.3
    soft('chairback', x + bxo, y + byo, 0.0, 0.92, 0.32, 0.74, mat, r=0.15, rz=rz)
    for s in (-1, 1):
        ax, ay = math.cos(rz) * s * 0.36, math.sin(rz) * s * 0.36
        soft('chairarm', x + ax, y + ay, 0.0, 0.22, 0.84, 0.58, mat, r=0.1, rz=rz)
    soft('chairseat', x - bxo * 0.15, y - byo * 0.15, 0.42, 0.62, 0.6, 0.1, mat, r=0.05, rz=rz)

# ---------------------------------------------------------------- rooms
def living():
    W, D = 7.4, 6.2
    shell(W, D, windows=('S', 'W'))
    world_sky(sun_elev=24, sun_rot=235)
    # fireplace wall (north): travertine chimney breast with a long linear fire
    box('chimney', 4.3, D - 0.25, 0, 3.0, 0.5, CEIL, 'travertine', bevel=0.004)
    box('firebox', 4.3, D - 0.52, 0.42, 1.7, 0.06, 0.36, 'firebox', bevel=0.002)
    box('flames', 4.3, D - 0.556, 0.45, 1.6, 0.01, 0.3, 'fire', bevel=0)
    box('embers', 4.3, D - 0.556, 0.43, 1.6, 0.02, 0.03, 'lampglow', bevel=0)
    box('hearth', 4.3, D - 0.62, 0, 3.4, 0.36, 0.3, 'travertine', bevel=0.01)
    fl = bpy.data.lights.new('firelight', 'AREA'); fl.size = 1.5; fl.size_y = 0.3; fl.energy = 40; fl.color = (1, 0.55, 0.25)
    flo = link(bpy.data.objects.new('firelight', fl)); flo.location = (4.3, D - 0.62, 0.6); flo.rotation_euler = (math.radians(-90), 0, 0)
    vase_branches(3.2, D - 0.6, 0.3)
    books(5.4, D - 0.62, 0.3)
    # art beside the chimney
    box('artframe', 1.4, D - 0.03, 1.15, 1.2, 0.04, 0.9, 'walnut', bevel=0.004)
    box('art', 1.4, D - 0.055, 1.2, 1.1, 0.01, 0.8, 'art_a', bevel=0)
    # rug
    box('rug', 4.0, 2.9, 0, 4.4, 3.2, 0.015, 'rug', bevel=0.004)
    # long sofa facing the fire
    sx, sy = 4.2, 1.35
    soft('sofa_base', sx, sy, 0.05, 3.3, 1.05, 0.38, 'boucle', r=0.08)
    soft('sofa_back', sx, sy - 0.4, 0.05, 3.3, 0.26, 0.78, 'boucle', r=0.12)
    for s in (-1, 1):
        soft('sofa_arm', sx + s * 1.55, sy, 0.05, 0.26, 1.05, 0.6, 'boucle', r=0.12)
    for i in range(3):
        soft('seat', sx - 1.0 + i, sy + 0.08, 0.42, 0.98, 0.82, 0.16, 'boucle', r=0.07)
        soft('backcushion', sx - 1.0 + i, sy - 0.22, 0.5, 0.95, 0.24, 0.48, 'boucle', r=0.1, rz=0)
    soft('pillow', sx - 1.2, sy - 0.05, 0.56, 0.45, 0.16, 0.42, 'cushion_clay', r=0.07, rz=0.2)
    soft('pillow', sx + 1.25, sy - 0.05, 0.56, 0.45, 0.16, 0.42, 'linen_taupe', r=0.07, rz=-0.2)
    # chubby lounge chairs either side
    for x, rz in ((1.7, -1.2), (6.5, 1.2)):
        chubby_chair(x, 3.1, rz)
    # oak lounge chairs near the window
    for x in (1.0, 2.1):
        box('oakchair_l', x - 0.32, 1.0, 0, 0.06, 0.75, 0.6, 'oak', bevel=0.02)
        box('oakchair_r', x + 0.32, 1.0, 0, 0.06, 0.75, 0.6, 'oak', bevel=0.02)
        soft('oakchair_seat', x, 1.0, 0.28, 0.6, 0.7, 0.14, 'linen', r=0.05)
        soft('oakchair_back', x, 0.72, 0.38, 0.6, 0.14, 0.42, 'linen', r=0.06)
    cyl('sidetable', 1.55, 1.05, 0, 0.22, 0.22, 0.48, 'travertine', bevel=0.01)
    # coffee table
    box('coffee', 4.2, 3.0, 0.0, 1.5, 1.0, 0.34, 'travertine', bevel=0.02, seg=3)
    books(3.9, 3.0, 0.34, 0.2)
    cyl('bowl', 4.6, 3.1, 0.34, 0.16, 0.16, 0.07, 'ceramic', bevel=0.02)
    # floor lamp and plants
    LX, LY = 0.5, 2.4
    cyl('floorlamp_base', LX, LY, 0, 0.16, 0.16, 0.03, 'brass')
    cyl('floorlamp_pole', LX, LY, 0, 0.012, 0.012, 1.55, 'brass', verts=12)
    cyl('floorlamp_shade', LX, LY, 1.45, 0.24, 0.24, 0.3, 'linen')
    cyl('floorlamp_bulb', LX, LY, 1.5, 0.08, 0.08, 0.18, 'lampglow')
    lp = bpy.data.lights.new('fl', 'POINT'); lp.energy = 35; lp.color = (1, 0.82, 0.6); lp.shadow_soft_size = 0.1
    link(bpy.data.objects.new('fl', lp)).location = (LX, LY, 1.6)
    plant(0.55, D - 0.6, 1.3)
    plant(6.9, D - 0.6, 1.0)
    # console on the east wall
    box('console', W - 0.25, 2.2, 0.0, 0.42, 1.8, 0.78, 'walnut', bevel=0.006)
    vase_branches(W - 0.25, 1.7, 0.78)
    books(W - 0.25, 2.6, 0.78)
    return dict(
        start=Vector((3.7, 2.4, 10.5)), start_aim=Vector((3.7, 3.2, 0.0)),
        mid=Vector((5.4, 0.9, 3.6)), end=Vector((6.85, 0.5, 1.42)),
        end_aim=Vector((2.8, 5.0, 1.05)), lens_start=26, lens_end=20)

def kitchen():
    W, D = 7.6, 6.0
    shell(W, D, windows=('S', 'E'))
    world_sky(sun_elev=28, sun_rot=150)
    # cabinetry wall (north): tall oak units, a marble-splash run with hob and integrated hood
    box('tall_l', 0.8, D - 0.33, 0, 1.6, 0.62, 2.45, 'oak_v', bevel=0.003)
    box('tall_r', 6.75, D - 0.33, 0, 1.7, 0.62, 2.45, 'oak_v', bevel=0.003)
    for x in (0.4, 1.2, 6.35, 7.15):
        box('tallseam', x, D - 0.019, 0.02, 0.004, 0.006, 2.4, 'walnut', bevel=0)
    box('base_run', 3.8, D - 0.33, 0, 4.3, 0.62, 0.88, 'oak_v', bevel=0.003)
    box('counter', 3.8, D - 0.33, 0.88, 4.34, 0.66, 0.04, 'marble', bevel=0.003)
    box('splash', 3.8, D - 0.02, 0.92, 4.3, 0.02, 0.62, 'marble', bevel=0)
    box('hood', 3.8, D - 0.3, 1.54, 4.3, 0.58, 0.9, 'oak_v', bevel=0.003)
    box('hob', 3.2, D - 0.33, 0.92, 0.8, 0.5, 0.008, 'firebox', bevel=0.002)
    box('sink', 4.9, D - 0.33, 0.915, 0.7, 0.42, 0.01, 'steel', bevel=0.004)
    cyl('tap', 4.9, D - 0.55, 0.92, 0.015, 0.015, 0.34, 'brass', verts=12)
    box('underglow', 3.8, D - 0.06, 1.52, 4.2, 0.03, 0.01, 'cove', bevel=0)
    for i in range(5):
        box('drawerline', 1.8 + i * 1.0, D - 0.019, 0.05, 0.004, 0.006, 0.8, 'walnut', bevel=0)
    vase_branches(2.2, D - 0.3, 0.92)
    cyl('bowl', 5.7, D - 0.32, 0.92, 0.17, 0.17, 0.08, 'ceramic', bevel=0.02)
    # island with waterfall marble ends and stools
    box('island', 3.8, 3.4, 0, 3.0, 1.1, 0.9, 'oak', bevel=0.004)
    box('island_top', 3.8, 3.4, 0.9, 3.1, 1.16, 0.06, 'marble', bevel=0.004)
    for s in (-1, 1):
        box('waterfall', 3.8 + s * 1.53, 3.4, 0, 0.06, 1.16, 0.96, 'marble', bevel=0.004)
    for i in range(3):
        x = 2.8 + i
        cyl('stool_leg', x, 2.55, 0, 0.02, 0.02, 0.62, 'brass', verts=12)
        cyl('stool_ring', x, 2.55, 0.25, 0.17, 0.17, 0.012, 'brass', verts=32)
        soft('stool_seat', x, 2.55, 0.62, 0.42, 0.42, 0.1, 'boucle', r=0.04)
        soft('stool_back', x, 2.38, 0.68, 0.42, 0.06, 0.2, 'boucle', r=0.03)
    cyl('fruit', 4.4, 3.45, 0.96, 0.18, 0.18, 0.06, 'walnut', bevel=0.02)
    for k in range(4):
        sphere('lemon', 4.32 + (k % 2) * 0.13, 3.4 + (k // 2) * 0.1, 1.06, 0.05, 0.05, 0.045, 'brass')
    books(3.3, 3.5, 0.96, 0.4)
    # pendants
    for i in range(3):
        x = 2.8 + i
        cyl('pendant_cord', x, 3.4, 1.85, 0.004, 0.004, CEIL - 1.85, 'blackmetal', verts=6)
        sphere('pendant', x, 3.4, 1.75, 0.15, 0.15, 0.15, 'lampglow')
        pl = bpy.data.lights.new('pend', 'POINT'); pl.energy = 30; pl.color = (1, 0.83, 0.62); pl.shadow_soft_size = 0.15
        link(bpy.data.objects.new('pend', pl)).location = (x, 3.4, 1.62)
    # dining by the corner windows
    box('dtable_top', 2.0, 1.25, 0.72, 2.4, 1.0, 0.05, 'oak', bevel=0.006)
    box('dtable_leg', 1.1, 1.25, 0, 0.12, 0.8, 0.72, 'oak', bevel=0.006)
    box('dtable_leg', 2.9, 1.25, 0, 0.12, 0.8, 0.72, 'oak', bevel=0.006)
    for i in range(3):
        x = 1.2 + i * 0.8
        for s in (-1, 1):
            y = 1.25 + s * 0.72
            soft('dchair_seat', x, y, 0.42, 0.48, 0.48, 0.08, 'boucle', r=0.035)
            soft('dchair_back', x, y + s * 0.22, 0.48, 0.48, 0.07, 0.42, 'boucle', r=0.035)
            for dx in (-0.2, 0.2):
                for dy in (-0.2, 0.2):
                    box('dchair_leg', x + dx, y + dy, 0, 0.035, 0.035, 0.42, 'oak', bevel=0.004)
    vase_branches(2.0, 1.25, 0.77)
    box('dpendant', 2.0, 1.25, 1.65, 1.8, 0.08, 0.05, 'brass', bevel=0.01)
    box('dpendant_glow', 2.0, 1.25, 1.64, 1.75, 0.05, 0.01, 'lampglow', bevel=0)
    dl = bpy.data.lights.new('dlight', 'AREA'); dl.size = 1.6; dl.size_y = 0.1; dl.energy = 60; dl.color = (1, 0.84, 0.64)
    link(bpy.data.objects.new('dlight', dl)).location = (2.0, 1.25, 1.62)
    plant(7.0, 0.6, 1.2)
    plant(0.5, 3.6, 1.0)
    box('rug', 2.0, 1.25, 0, 3.4, 2.4, 0.012, 'rug', bevel=0.003)
    return dict(
        start=Vector((3.8, 2.4, 10.5)), start_aim=Vector((3.8, 3.2, 0.0)),
        mid=Vector((5.6, 1.5, 3.8)), end=Vector((6.9, 1.1, 1.45)),
        end_aim=Vector((2.4, 4.6, 0.95)), lens_start=26, lens_end=20)

def bedroom():
    W, D = 6.0, 5.4
    shell(W, D, windows=('E',))
    world_sky(sun_elev=20, sun_rot=120)
    # upholstered headboard wall
    for i in range(6):
        soft('headpanel', 1.55 + i * 0.5, D - 0.08, 0.35, 0.48, 0.12, 1.55, 'linen_taupe', r=0.05)
    # bed
    bx, by = 2.8, D - 1.25
    box('bedbase', bx, by, 0, 2.1, 2.2, 0.32, 'oak', bevel=0.01)
    soft('mattress', bx, by, 0.32, 1.95, 2.05, 0.24, 'mattress', r=0.06)
    soft('duvet', bx, by - 0.22, 0.5, 2.05, 1.6, 0.12, 'linen', r=0.08)
    soft('duvet_fold', bx, by + 0.52, 0.56, 2.05, 0.3, 0.1, 'linen', r=0.06)
    soft('throw', bx, by - 0.65, 0.6, 2.1, 0.55, 0.05, 'linen_taupe', r=0.03)
    for dx in (-0.5, 0.5):
        soft('pillow', bx + dx, by + 0.82, 0.58, 0.85, 0.24, 0.42, 'linen', r=0.1)
        soft('pillow2', bx + dx, by + 0.62, 0.56, 0.75, 0.2, 0.34, 'mattress', r=0.09)
    soft('pillow3', bx, by + 0.45, 0.58, 0.55, 0.16, 0.3, 'cushion_clay', r=0.07)
    for s in (-1, 1):
        x = bx + s * 1.45
        box('nightstand', x, D - 0.45, 0, 0.6, 0.45, 0.52, 'walnut', bevel=0.006)
        table_lamp(x, D - 0.45, 0.52)
        books(x + 0.12, D - 0.38, 0.52)
    soft('bench', bx, by - 1.35, 0.0, 1.6, 0.45, 0.45, 'boucle', r=0.08)
    box('rug', bx, by - 0.6, 0, 3.2, 3.0, 0.014, 'rug', bevel=0.003)
    # window corner: lounge chair, side table, sheer curtains
    chubby_chair(W - 1.0, 1.0, 2.4)
    cyl('sidetable', W - 0.55, 1.75, 0, 0.2, 0.2, 0.5, 'travertine', bevel=0.01)
    vase_branches(W - 0.55, 1.75, 0.5)
    for i in range(7):
        c = box('curtain', W - 0.22, 0.2 + i * 0.13 if i < 3 else D - 0.2 - (6 - i) * 0.13, 0, 0.05, 0.14, CEIL - 0.05, 'sheer', bevel=0.02, seg=3, smooth=True)
    # dresser and art on the west wall
    box('dresser', 0.28, 2.0, 0, 0.5, 1.8, 0.8, 'oak', bevel=0.006)
    box('artframe', 0.04, 2.0, 1.25, 0.04, 1.0, 1.2, 'walnut', bevel=0.004)
    box('art', 0.065, 2.0, 1.3, 0.01, 0.9, 1.1, 'art_b', bevel=0)
    vase_branches(0.28, 1.4, 0.8)
    plant(0.5, 0.5, 1.1)
    return dict(
        start=Vector((3.0, 2.3, 9.5)), start_aim=Vector((3.0, 3.1, 0.0)),
        mid=Vector((4.3, 1.0, 3.4)), end=Vector((4.9, 0.45, 1.45)),
        end_aim=Vector((1.6, 4.4, 0.75)), lens_start=26, lens_end=20)

def bath():
    W, D = 4.8, 4.0
    shell(W, D, windows=('S',), floor_mat='marble_floor', wall_mat='marble', cove=True)
    world_sky(sun_elev=26, sun_rot=200)
    # freestanding oval tub by the window
    tub_x, tub_y = 2.9, 0.95
    me = bpy.data.meshes.new('tub')
    bm = bmesh.new()
    ring = bmesh.ops.create_circle(bm, cap_ends=True, segments=64, radius=1.0)['verts']
    for v in ring:
        v.co.x *= 0.88; v.co.y *= 0.42
    face = [f for f in bm.faces][0]
    ext = bmesh.ops.extrude_face_region(bm, geom=[face])
    top = [e for e in ext['geom'] if isinstance(e, bmesh.types.BMFace)][0]
    bmesh.ops.translate(bm, verts=top.verts, vec=(0, 0, 0.58))
    ins = bmesh.ops.inset_region(bm, faces=[top], thickness=0.05)
    ext2 = bmesh.ops.extrude_face_region(bm, geom=[top])
    inner = [e for e in ext2['geom'] if isinstance(e, bmesh.types.BMFace)][0]
    bmesh.ops.translate(bm, verts=inner.verts, vec=(0, 0, -0.45))
    bmesh.ops.scale(bm, verts=inner.verts, vec=(0.9, 0.85, 1), space=__import__('mathutils').Matrix.Translation(-inner.calc_center_median()))
    bm.to_mesh(me); bm.free()
    tub = link(bpy.data.objects.new('tub', me))
    tub.location = (tub_x, tub_y, 0)
    tub.data.materials.append(MATS['ceramic'])
    for p in tub.data.polygons:
        p.use_smooth = True
    md = tub.modifiers.new('bevel', 'BEVEL'); md.width = 0.03; md.segments = 4
    box('tubwater', tub_x, tub_y, 0.5, 1.35, 0.55, 0.005, 'water', bevel=0.2, seg=6)
    cyl('tubfiller', tub_x - 1.05, tub_y, 0, 0.02, 0.02, 0.95, 'brass', verts=12)
    box('tubspout', tub_x - 0.95, tub_y, 0.9, 0.22, 0.03, 0.03, 'brass', bevel=0.01)
    # floating double vanity with vessel basins and a backlit mirror (north wall)
    box('vanity', 2.4, D - 0.28, 0.45, 2.4, 0.52, 0.4, 'oak', bevel=0.004)
    box('vanity_top', 2.4, D - 0.28, 0.85, 2.44, 0.55, 0.04, 'travertine', bevel=0.004)
    for dx in (-0.6, 0.6):
        me2 = cyl('basin', 2.4 + dx, D - 0.3, 0.89, 0.22, 0.22, 0.14, 'ceramic', bevel=0.03, seg=3)
        cyl('basinbowl', 2.4 + dx, D - 0.3, 1.02, 0.17, 0.17, 0.012, 'ceramic_matte')
        cyl('tap', 2.4 + dx, D - 0.05, 1.05, 0.012, 0.012, 0.25, 'brass', verts=12).rotation_euler = (math.radians(90), 0, 0)
    box('mirrorglow', 2.4, D - 0.03, 1.15, 2.1, 0.01, 1.1, 'mirrorglow', bevel=0)
    box('mirror', 2.4, D - 0.06, 1.18, 2.0, 0.02, 1.04, 'mirror', bevel=0.004)
    box('undervanityglow', 2.4, D - 0.3, 0.44, 2.3, 0.4, 0.005, 'cove', bevel=0)
    # walk-in shower (east end) with glass screen and rain head
    box('showerglass', W - 1.35, 2.6, 0, 0.012, 2.2, 2.1, 'glass', bevel=0)
    box('showerframe', W - 1.35, 2.6, 2.1, 0.03, 2.2, 0.03, 'brass', bevel=0.004)
    cyl('rainhead', W - 0.65, 2.6, 2.4, 0.18, 0.18, 0.012, 'brass')
    cyl('rainarm', W - 0.65, 2.6, 2.41, 0.01, 0.01, CEIL - 2.41, 'brass', verts=8)
    box('niche_glow', W - 0.03, 2.6, 1.1, 0.01, 0.8, 0.35, 'cove', bevel=0)
    # towels on a bench, stool, plant
    box('bench', 0.55, 2.0, 0, 0.45, 1.2, 0.42, 'oak', bevel=0.006)
    soft('towel', 0.55, 1.75, 0.42, 0.38, 0.5, 0.1, 'linen', r=0.04)
    soft('towel', 0.55, 1.75, 0.52, 0.36, 0.48, 0.09, 'linen_taupe', r=0.035)
    cyl('stool', 1.55, 0.9, 0, 0.16, 0.16, 0.42, 'travertine', bevel=0.01)
    vase_branches(1.55, 0.9, 0.42)
    plant(0.5, 0.5, 1.0)
    box('bathmat', 2.9, 1.65, 0, 1.0, 0.6, 0.012, 'rug', bevel=0.003)
    return dict(
        start=Vector((2.4, 1.6, 8.5)), start_aim=Vector((2.4, 2.2, 0.0)),
        mid=Vector((1.2, 2.4, 3.2)), end=Vector((0.6, 3.25, 1.5)),
        end_aim=Vector((3.4, 0.6, 0.65)), lens_start=24, lens_end=18)

# ---------------------------------------------------------------- camera path
def bez(p0, p1, p2, p3, t):
    u = 1 - t
    return p0 * u ** 3 + p1 * 3 * u * u * t + p2 * 3 * u * t * t + p3 * t ** 3

def ease(t):
    return t * t * t * (t * (t * 6 - 15) + 10)   # smootherstep: gentle start and landing

def run():
    build_materials()
    path = {'living': living, 'kitchen': kitchen, 'bedroom': bedroom, 'bath': bath}[ROOM]()
    for pref in [x for x in os.environ.get('HIDE', '').split(',') if x]:
        for ob in COLL.objects:
            if ob.name.startswith(pref):
                ob.hide_render = True
    cam_data = bpy.data.cameras.new('cam')
    cam_data.clip_start = 0.05
    cam_data.clip_end = 4000
    cam = link(bpy.data.objects.new('cam', cam_data))
    scene.camera = cam
    os.makedirs(OUT, exist_ok=True)
    s, m, e = path['start'], path['mid'], path['end']
    # control points: drop mostly vertically first, then glide in to eye level
    c1 = Vector((s.x, s.y, s.z * 0.55 + m.z * 0.45))
    c2 = Vector((m.x, m.y, m.z))
    up_cut = CEIL - 0.04   # ceiling shows only once the camera is under it (never render from inside the slab)
    frames = range(FRAMES) if not ONLY else ONLY
    for f in frames:
        t = ease(f / max(FRAMES - 1, 1))
        pos = bez(s, c1, c2, e, t)
        aim = path['start_aim'].lerp(path['end_aim'], ease(min(1.0, (f / max(FRAMES - 1, 1)) * 1.15)))
        cam.location = pos
        d = (aim - pos).normalized()
        cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        cam_data.lens = path['lens_start'] + (path['lens_end'] - path['lens_start']) * t
        SHELL['ceiling'].visible_camera = pos.z < up_cut
        for ob in COLL.objects:
            if ob.name.startswith('cove') and ob.data and ob.type == 'MESH':
                pass
        scene.render.filepath = os.path.join(OUT, f'{f:03d}.jpg')
        bpy.ops.render.render(write_still=True)
        print('FRAME', f, flush=True)

run()
