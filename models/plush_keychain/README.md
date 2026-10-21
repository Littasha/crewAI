# Plush keychain 3D model

A full 360° 3D model of the pink fruit plush keychain (closed happy eyes, hot-pink
heart patch, green leaf, brown stem, "MW" monogram on the back, pink clip ring).

| File | Use it for |
| --- | --- |
| `plush_keychain.glb` | Web / AR / game engines (Blender, Unity, Unreal, Three.js, iOS Quick Look, Android Scene Viewer). Texture is embedded. |
| `plush_keychain.obj` + `plush_keychain.mtl` + `plush_keychain_texture.png` | Universal mesh exchange (Blender, Maya, Cinema 4D, SketchUp). Keep the three files together. |
| `plush_keychain.stl` | 3D printing (millimetres, ~80 mm wide). No colour. |
| `viewer.html` | Interactive 360° viewer. Serve the folder over HTTP (e.g. `python -m http.server`) and open it. |
| `turntable.png` | Eight-angle preview render. |
| `build_plush.py` | Regenerates everything: `python build_plush.py .` (needs `trimesh`, `numpy`, `pillow`). |

Scale: GLB/OBJ are in metres (body ≈ 8 cm wide); STL is in millimetres.
The model is built procedurally from the reference photos, so proportions and
embroidery are an approximation rather than a photogrammetry scan.
