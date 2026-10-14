"""Read preserved PMX, identify cloth by source bone chains and export raw arrays."""
import importlib.util,json,hashlib,collections,sys
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];C=json.loads((R/'tools/model_config.json').read_text());B=R/'build'
spec=importlib.util.spec_from_file_location('pmx_reader',C['pmx_reader']);reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
m=reader.load(str(R/'input/original/艾梅莉埃.pmx'));p=np.array([v.co for v in m.vertices]);f=np.array(m.faces)
bi=np.zeros((len(p),4),'i4');bw=np.zeros((len(p),4))
for i,v in enumerate(m.vertices):
 w=v.weight;ids=w.bones
 weights=[1] if w.type==0 else [w.weights[0],1-w.weights[0]] if w.type==1 else w.weights if w.type==2 else [w.weights.weight,1-w.weights.weight]
 for j,(bone,weight) in enumerate(zip(ids,weights)):
  if bone>=0:bi[i,j]=bone;bw[i,j]=weight
assert np.max(abs(bw.sum(1)-1))<1e-5
groups=[];materials={};start=0;summary=[]
for mi,mat in enumerate(m.materials):
 faces=f[start:start+mat.vertex_count//3];start+=len(faces);key=f'm{mi:02d}'
 tex=Path(m.textures[mat.texture].path);im=Image.open(tex).convert('RGBA');out=R/'tex'/tex.name
 if not out.exists():im.save(out)
 materials[key]={'source_name':mat.name,'diffuse':tex.name,'normal':None,'specular':None,'cutout':im.getchannel('A').getextrema()[0]<255,'double_sided':mat.is_double_sided}
 # Expand selection only inside each geometric component; seams are welded
 # for identification, but source topology, UV and positions remain unchanged.
 ix=np.unique(faces);_,owners=np.unique(np.round(p[ix],5),axis=0,return_inverse=True);lookup=dict(zip(ix.tolist(),owners.tolist()));parent=list(range(owners.max()+1))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for tri in faces:
  a=find(lookup[int(tri[0])])
  for x in tri[1:]:parent[find(lookup[int(x)])]=a
 comp=collections.defaultdict(list)
 for fi,tri in enumerate(faces):comp[find(lookup[int(tri[0])])].append(fi)
 selected=np.full(len(faces),'none',dtype='<U20')
 for inds in comp.values():
  vertices=np.unique(faces[inds]);scores={}
  for kind,prefixes in C['cloth_bone_prefixes'].items():
   target=np.array([any(b.name.startswith(pref) for pref in prefixes) for b in m.bones]);scores[kind]=float((bw[vertices]*target[bi[vertices]]).sum())
  kind=max(scores,key=scores.get)
  if scores[kind]>0.25:
   selected[inds]=kind
   summary.append({'material':mat.name,'kind':kind,'triangles':len(inds),'vertices':len(vertices),'min_source':p[vertices].min(0).tolist(),'max_source':p[vertices].max(0).tolist(),'source_weight_sum':scores[kind]})
 for kind in ['none','hat_trail','back_ribbons']:
  fs=faces[selected==kind]
  if not len(fs):continue
  name=f'emilie_part_{mi:02d}'+('' if kind=='none' else '_'+kind)
  groups.append({'object':name,'source_material_index':mi,'source_material':mat.name,'material':key,'kind':kind,'part':'body','faces':fs.tolist()})
np.savez_compressed(B/'raw_model.npz',p=p,n=np.array([v.normal for v in m.vertices]),uv=np.array([v.uv for v in m.vertices]),bi=bi,bw=bw)
(B/'source_groups.json').write_text(json.dumps(groups,ensure_ascii=False,indent=2),encoding='utf8')
(B/'source_bones.json').write_text(json.dumps([{'name':b.name,'parent':b.parent,'position':b.location} for b in m.bones],ensure_ascii=False,indent=2),encoding='utf8')
(R/'tex/materials.json').write_text(json.dumps(materials,ensure_ascii=False,indent=2),encoding='utf8')
hashes={q.relative_to(R).as_posix():hashlib.sha256(q.read_bytes()).hexdigest() for q in (R/'input').rglob('*') if q.is_file()}
(R/'reports/input_hashes.json').write_text(json.dumps(hashes,ensure_ascii=False,indent=2),encoding='utf8')
report={'vertices':len(p),'triangles':len(f),'bones':len(m.bones),'rigids':len(m.rigids),'joints':len(m.joints),'morphs':len(m.morphs),'cloth_scope':summary,'skirt_cloth_enabled':False,'source_reader':C['pmx_reader']}
(R/'reports/input_inspection.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False,indent=2))
