"""Read-only Blender survey of all Zhenwu sources; writes reports only."""
import bpy, json, sys, hashlib
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('D:/dsh-tiandao/真武少女校服8套')
rows = []
for folder in sorted(SOURCE.iterdir()):
    if not folder.is_dir():
        continue
    variants = []
    for fbx in sorted(folder.glob('*.fbx')):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.fbx(filepath=str(fbx), use_anim=False)
        meshes = []
        images = []
        for im in bpy.data.images:
            if im.source != 'FILE':
                continue
            raw = bpy.path.abspath(im.filepath).replace('\\', '/')
            local = folder / 'tex' / Path(raw).name
            images.append({'name': im.name, 'import_path': raw, 'import_path_exists': Path(raw).is_file(), 'local_path': str(local), 'local_exists': local.is_file(), 'size': list(im.size)})
        for o in sorted(bpy.context.scene.objects, key=lambda x: x.name):
            if o.type != 'MESH':
                continue
            m = o.data
            p = np.array([o.matrix_world @ v.co for v in m.vertices])
            parent = list(range(len(p)))
            def find(i):
                while parent[i] != i:
                    parent[i] = parent[parent[i]]
                    i = parent[i]
                return i
            for e in m.edges:
                parent[find(e.vertices[1])] = find(e.vertices[0])
            groups = {}
            for i in range(len(p)):
                groups.setdefault(find(i), []).append(i)
            mats = []
            for mat in m.materials:
                mats.append({'name': mat.name, 'images': [n.image.name for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image] if mat.use_nodes else []})
            meshes.append({'name': o.name, 'vertices': len(p), 'triangles': sum(len(f.vertices)-2 for f in m.polygons), 'finite': bool(np.isfinite(p).all()), 'bounds_min': p.min(0).tolist(), 'bounds_max': p.max(0).tolist(), 'uv_layers': [u.name for u in m.uv_layers], 'vertex_groups': len(o.vertex_groups), 'weighted_vertices': sum(bool(v.groups) for v in m.vertices), 'armature_modifiers': sum(x.type == 'ARMATURE' for x in o.modifiers), 'materials': mats, 'components': [{'vertices': len(ids), 'min': p[ids].min(0).tolist(), 'max': p[ids].max(0).tolist()} for ids in groups.values()]})
        lo = np.min([m['bounds_min'] for m in meshes], axis=0)
        hi = np.max([m['bounds_max'] for m in meshes], axis=0)
        geometry_hash = hashlib.sha256()
        for o in sorted((o for o in bpy.context.scene.objects if o.type == 'MESH'), key=lambda o:o.name):
            geometry_hash.update(np.array([o.matrix_world @ v.co for v in o.data.vertices], dtype='<f8').tobytes())
            geometry_hash.update(np.array([i for p in o.data.polygons for i in p.vertices], dtype='<i4').tobytes())
            for uv in o.data.uv_layers:
                geometry_hash.update(np.array([v.uv[:] for v in uv.data], dtype='<f8').tobytes())
        variants.append({'file': fbx.name, 'sha256': hashlib.sha256(fbx.read_bytes()).hexdigest(), 'geometry_uv_sha256': geometry_hash.hexdigest(), 'armatures': [{'name':o.name, 'bones':len(o.data.bones)} for o in bpy.context.scene.objects if o.type == 'ARMATURE'], 'vertices':sum(m['vertices'] for m in meshes), 'triangles':sum(m['triangles'] for m in meshes), 'bounds_min':lo.tolist(), 'bounds_max':hi.tolist(), 'dimensions':(hi-lo).tolist(), 'meshes':meshes, 'images':images})
        print('SURVEY', folder.name, fbx.name, len(meshes), variants[-1]['vertices'], variants[-1]['triangles'], 'armatures', len(variants[-1]['armatures']), flush=True)
    repair = json.loads((folder/'repair_report.json').read_text(encoding='utf-8-sig'))
    rows.append({'name':folder.name, 'source':str(folder), 'prior_repair_status':repair.get('status'), 'prior_unresolved':repair.get('unresolved'), 'variants':variants})
out = ROOT/'reports/source_survey.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({'scope':'Source imports only; no rigging, export, installation or game test', 'blender':bpy.app.version_string, 'sets':rows}, ensure_ascii=False, indent=2), encoding='utf-8')
print('REPORT', out)
