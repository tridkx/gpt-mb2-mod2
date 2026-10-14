"""Prepare only the selected PMX and default visible geometry; no props imports."""
from pathlib import Path
import json,importlib.util,hashlib,collections
import numpy as np
from PIL import Image
from context import config

def prepare(root):
    c=config(root);b=root/'build';spec=importlib.util.spec_from_file_location('pmx_reader',c['pmx_reader']);reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader);m=reader.load(str(root/c['source_model']))
    p=np.array([v.co for v in m.vertices]);f=np.array(m.faces);bi=np.zeros((len(p),4),'i4');bw=np.zeros((len(p),4))
    for i,v in enumerate(m.vertices):
        x=v.weight;weights=[1] if x.type==0 else [x.weights[0],1-x.weights[0]] if x.type==1 else x.weights if x.type==2 else [x.weights.weight,1-x.weights.weight]
        for j,(bone,value) in enumerate(zip(x.bones,weights)):
            if bone>=0:bi[i,j]=bone;bw[i,j]=value
    assert np.max(abs(bw.sum(1)-1))<1e-5
    groups=[];materials={};excluded=[];start=0;seen_faces=set();selected=[]
    # MMD sphere/highlight overlays duplicate the primary rendered surface.
    # Remove only near-coincident duplicate triangles from these named passes;
    # retain all unique geometry, including real hair roots and ornaments.
    for mi,mat in enumerate(m.materials):
        faces=f[start:start+mat.vertex_count//3];start+=len(faces)
        if mat.diffuse[3]<=1e-6 or mi in c.get('exclude_materials',[]):
            excluded.append({'material_index':mi,'name':mat.name,'triangles':len(faces),'reason':'Default hidden expression/material or explicit prop exclusion'});continue
        if not len(faces):continue
        overlay=any(token in mat.name.lower() for token in ['spa','sph','+']) or mat.name in c.get('overlay_materials',[])
        mask=[]
        for tri in faces:
            key=tuple(sorted(tuple(x) for x in np.round(p[tri],3)))
            duplicate=overlay and key in seen_faces;mask.append(not duplicate)
            if not duplicate:seen_faces.add(key)
        filtered=faces[mask]
        if len(filtered)<len(faces):excluded.append({'material_index':mi,'name':mat.name,'triangles':len(faces)-len(filtered),'reason':'Coincident MMD highlight/sphere overlay; primary geometry retained'})
        if not len(filtered):continue
        key=f'm{mi:02d}';tex_index=mat.texture
        if tex_index>=0:
            tex=Path(m.textures[tex_index].path);assert tex.is_file(),tex;im=Image.open(tex).convert('RGBA');filename=f't{tex_index:02d}.png'
        else:
            im=Image.new('RGBA',(32,32),tuple(int(np.clip(v,0,1)*255) for v in mat.diffuse));filename=f'flat{mi:02d}.png'
        dest=root/'tex'/filename
        if not dest.exists():im.save(dest)
        cut=im.getchannel('A').getextrema()[0]<255
        materials[key]={'source_name':mat.name,'diffuse':filename,'normal':None,'specular':None,'cutout':cut,'double_sided':mat.is_double_sided,'source_material_index':mi,'source_alpha':mat.diffuse[3]}
        kind='hair' if any(t in mat.name.lower() for t in ['髪','髮','头发','发','辫','hair']) and not any(t in mat.name for t in ['饰','绳','带','帶']) else 'none'
        name=c['prefix']+f'_part_{mi:02d}';cloth=bool(c['cloth_enabled'] and mi in c.get('cloth_materials',[]))
        groups.append({'object':name,'source_material_index':mi,'source_material':mat.name,'material':key,'kind':kind,'part':'body','cloth':cloth,'faces':filtered.tolist()});selected.extend(np.unique(filtered).tolist())
    np.savez_compressed(b/'raw_model.npz',p=p,n=np.array([v.normal for v in m.vertices]),uv=np.array([v.uv for v in m.vertices]),bi=bi,bw=bw)
    (b/'source_groups.json').write_text(json.dumps(groups,ensure_ascii=False,indent=2),encoding='utf8')
    (b/'source_bones.json').write_text(json.dumps([{'name':v.name,'parent':v.parent,'position':v.location} for v in m.bones],ensure_ascii=False,indent=2),encoding='utf8')
    (root/'tex/materials.json').write_text(json.dumps(materials,ensure_ascii=False,indent=2),encoding='utf8')
    hashes={q.relative_to(root).as_posix():hashlib.sha256(q.read_bytes()).hexdigest() for q in (root/'input').rglob('*') if q.is_file()};(root/'reports/input_hashes.json').write_text(json.dumps(hashes,ensure_ascii=False,indent=2),encoding='utf8')
    report={'vertices':len(p),'source_triangles':len(f),'selected_triangles':sum(len(g['faces']) for g in groups),'bones':len(m.bones),'morphs':len(m.morphs),'excluded':excluded,'ignored_models':c['ignored_models'],'source_model':c['source_model'],'selected_source_height_m':float(np.ptp(p[np.unique(selected),1]))*c['unit_scale'],'skirt_cloth_enabled':False}
    (root/'reports/preparation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print('PMX_PREPARED',c['id'],report['selected_triangles'],len(groups),'parts; exclusions',len(excluded))

if __name__=='__main__':
    import sys
    from context import SERIES
    roots=[Path(sys.argv[1])] if len(sys.argv)>1 else [Path(r['root']) for r in json.loads((SERIES/'batch_inventory.json').read_text(encoding='utf8'))['characters']]
    for root in roots:prepare(root)
