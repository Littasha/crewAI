"""Procedurally build a textured 3D model of the pink fruit plush keychain."""
import math, os, sys
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(OUT, exist_ok=True)

# ---------- texture (equirectangular UV on the body sphere) ----------
W, H = 2048, 1024
LAVENDER = (214, 120, 196)
HOTPINK = (236, 64, 150)
HEART = (240, 150, 205)
BLACK = (32, 28, 30)
BLUSH = (242, 220, 232)
MONO = (196, 72, 168)

img = Image.new("RGB", (W, H), LAVENDER)
d = ImageDraw.Draw(img)

# Subtle plush fuzz noise
rng = np.random.default_rng(7)
noise = rng.normal(0, 6, (H, W, 1)).astype(np.float32)
arr = np.clip(np.asarray(img).astype(np.float32) + noise, 0, 255).astype(np.uint8)
img = Image.fromarray(arr)
d = ImageDraw.Draw(img)

def uv(lon_deg, lat_deg):
    """lon 0 = front centre, +lon = viewer's right; lat +90 = top."""
    u = ((lon_deg + 180.0) % 360.0) / 360.0
    v = (90.0 - lat_deg) / 180.0
    return u * W, v * H

# Hot-pink patch: upper-right of the face, from top down to ~eye level
patch = [uv(10, 88), uv(75, 70), uv(70, 45), uv(60, 20), uv(28, 12), uv(14, 30), uv(6, 60)]
d.polygon(patch, fill=HOTPINK)
# heart-shaped lighter stitch on the patch
hx, hy = uv(42, 42)
r = 70
d.ellipse([hx - r, hy - r * 0.6, hx + 4, hy + r * 0.5], fill=HEART)
d.ellipse([hx - 4, hy - r * 0.6, hx + r, hy + r * 0.5], fill=HEART)
d.polygon([(hx - r, hy + 2), (hx + r, hy + 2), (hx, hy + r * 1.1)], fill=HEART)

# Eyes: happy closed arcs with lashes
def eye(lon, lat, flip):
    cx, cy = uv(lon, lat)
    w, h, t = 110, 80, 15
    d.arc([cx - w, cy - h, cx + w, cy + h], 200, 340, fill=BLACK, width=t)
    s = -1 if flip else 1
    ex = cx - s * w * 0.98
    ey = cy - h * 0.3
    for ang in (-35, -5, 25):
        a = math.radians(ang)
        d.line([(ex, ey), (ex - s * 38 * math.cos(a), ey - 38 * math.sin(a))], fill=BLACK, width=t - 3)
eye(-32, 12, False)
eye(32, 12, True)

# Smile
sx, sy = uv(0, -10)
d.arc([sx - 120, sy - 90, sx + 120, sy + 50], 20, 160, fill=BLACK, width=14)

# Blush cheeks
for lon in (-48, 48):
    bx, by = uv(lon, -4)
    d.ellipse([bx - 42, by - 26, bx + 42, by + 26], fill=BLUSH)

# "MW" monogram on the back (lon 180)
mono = Image.new("L", (900, 420), 0)
md = ImageDraw.Draw(mono)
font = None
for path in ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf",
             "/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf"]:
    if os.path.exists(path):
        font = ImageFont.truetype(path, 340)
        break
if font is None:
    font = ImageFont.load_default()
md.text((450, 210), "MW", fill=255, font=font, anchor="mm", stroke_width=6, stroke_fill=255)
mono = mono.filter(ImageFilter.GaussianBlur(1.2))
mx, my = uv(180, 0)
# wrap-safe paste: back centre sits on the u=0/1 seam, so paste at both edges
layer = Image.new("RGB", mono.size, MONO)
for off in (0, W, -W):
    img.paste(layer, (int(mx - 450) + off, int(my - 210)), mono)

tex_path = os.path.join(OUT, "plush_keychain_texture.png")
img.save(tex_path)

# ---------- geometry ----------
def sphere(radius=1.0, sub=5):
    m = trimesh.creation.icosphere(subdivisions=sub, radius=radius)
    return m

body = trimesh.creation.uv_sphere(radius=1.0, count=[96, 192])
# squash: wider than tall, slightly flattened front/back
body.apply_scale([1.0, 0.86, 0.92])  # x width, y height, z depth
body.apply_translation([0, 0, 0])
# UVs: equirect; front faces +Z
v = body.vertices
x, y, z = v[:, 0], v[:, 1], v[:, 2]
lon = np.degrees(np.arctan2(x, z))          # 0 at +Z (front), +toward +X (viewer right)
lat = np.degrees(np.arcsin(np.clip(y / np.linalg.norm(v, axis=1), -1, 1)))
u = ((lon + 180.0) % 360.0) / 360.0
vv = 1.0 - (90.0 - lat) / 180.0  # glTF flips v
uvs = np.column_stack([u, vv])
mat = trimesh.visual.material.PBRMaterial(
    baseColorTexture=Image.open(tex_path), metallicFactor=0.0, roughnessFactor=0.95,
    name="plush_fabric")
body.visual = trimesh.visual.TextureVisuals(uv=uvs, material=mat)
# Seam fix: split triangles whose UVs straddle the wrap
body = body.copy()

UP = trimesh.transformations.rotation_matrix(math.radians(90), [1, 0, 0])

def colored(mesh, rgb, rough=0.9, metal=0.0, name="mat"):
    m = trimesh.visual.material.PBRMaterial(baseColorFactor=list(rgb) + [255],
                                            metallicFactor=metal, roughnessFactor=rough, name=name)
    mesh.visual = trimesh.visual.TextureVisuals(uv=np.zeros((len(mesh.vertices), 2)), material=m)
    return mesh

# Leaf: flattened ellipsoid tilted up-left
leaf = trimesh.creation.icosphere(subdivisions=4, radius=1.0)
leaf.apply_scale([0.46, 0.19, 0.07])
R = trimesh.transformations.rotation_matrix(math.radians(55), [0, 0, 1])
leaf.apply_transform(R)
leaf.apply_translation([-0.36, 1.02, 0.08])
leaf = colored(leaf, (120, 205, 60), name="leaf_green")

# Stem: short brown cylinder with rounded top
stem = trimesh.creation.capsule(radius=0.085, height=0.16, count=[24, 24])
stem.apply_transform(UP)
stem.apply_translation([0.28, 0.98, 0.02])
stem = colored(stem, (88, 52, 36), name="stem_brown")

# Keychain ring (pink metal torus) and lobster clasp
ring = trimesh.creation.torus(major_radius=0.13, minor_radius=0.022, major_sections=48, minor_sections=16)
ring.apply_translation([0.0, 1.03, 0.0])
ring = colored(ring, (240, 140, 180), rough=0.4, metal=0.25, name="pink_metal")

link = trimesh.creation.torus(major_radius=0.05, minor_radius=0.014, major_sections=32, minor_sections=12)
link.apply_translation([0.0, 1.19, 0.0])
link = colored(link, (240, 140, 180), rough=0.4, metal=0.25, name="pink_metal")

clasp = trimesh.creation.capsule(radius=0.045, height=0.34, count=[24, 24])
clasp.apply_transform(UP)
clasp.apply_translation([0.0, 1.42, 0.0])
clasp = colored(clasp, (240, 140, 180), rough=0.4, metal=0.25, name="pink_metal")
hook = trimesh.creation.torus(major_radius=0.07, minor_radius=0.02, major_sections=32, minor_sections=12)
hook.apply_translation([0.0, 1.62, 0.0])
hook = colored(hook, (240, 140, 180), rough=0.4, metal=0.25, name="pink_metal")

# Small loop of thread where the ring attaches to the plush
loop = trimesh.creation.capsule(radius=0.02, height=0.14, count=[12, 12])
loop.apply_transform(UP)
loop.apply_translation([0.0, 0.93, 0.0])
loop = colored(loop, (235, 235, 235), name="thread")

scene = trimesh.Scene()
scene.add_geometry(body, node_name="body", geom_name="body")
scene.add_geometry(leaf, node_name="leaf", geom_name="leaf")
scene.add_geometry(stem, node_name="stem", geom_name="stem")
scene.add_geometry(loop, node_name="thread_loop", geom_name="thread_loop")
scene.add_geometry(ring, node_name="ring", geom_name="ring")
scene.add_geometry(link, node_name="link", geom_name="link")
scene.add_geometry(clasp, node_name="clasp", geom_name="clasp")
scene.add_geometry(hook, node_name="hook", geom_name="hook")

# Scale so the plush body is ~8 cm wide (metres for glTF)
scene.apply_scale(0.04)

glb = os.path.join(OUT, "plush_keychain.glb")
scene.export(glb)
scene.export(os.path.join(OUT, "plush_keychain.obj"))
# Watertight-ish union for printing: STL of all parts
allm = trimesh.util.concatenate([body, leaf, stem, loop, ring, link, clasp, hook])
allm.apply_scale(40.0)  # millimetres
allm.export(os.path.join(OUT, "plush_keychain.stl"))
print("wrote", glb, os.path.getsize(glb), "bytes; faces", sum(len(g.faces) for g in scene.geometry.values()))
