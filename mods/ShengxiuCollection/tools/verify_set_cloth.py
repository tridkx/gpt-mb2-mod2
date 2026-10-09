"""Validate generated cloth and editor bindings from the final TPAC."""
import sys,json,hashlib,subprocess
from pathlib import Path
from collections import Counter
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
BASE=Path(__file__).resolve().parents[1]
WS=next(p for p in BASE.parents if (p/'tools/cloth_compiler').is_dir())
sys.path.insert(0,str(WS/'tools'))
from cloth_compiler.cloth_payload import read,write,decode_positions
from cloth_compiler.validation import check_structure
root=BASE/'sets'/sys.argv[1]
cfg=json.loads((root/'tools/model_config.json').read_text(encoding='utf-8'));prefix=cfg['prefix']
package=root/f'module/ShengxiuCollection/AssetPackages/{prefix}.tpac'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
dump=root/'build/final_cooked_cloth';dump.mkdir(exist_ok=True)
names=[prefix+'_'+n for n in ['head','body','legs']]
probe=['dotnet',str(BASE/'build/cloth_probe/NativeClothProbe.dll')]
before=json.loads(subprocess.check_output([*probe,str(root/'build/uncooked.tpac'),*names],encoding='utf-8'))
after=json.loads(subprocess.check_output([*probe,str(package),*names,'--dump-segments',str(dump)],encoding='utf-8'))
plans=json.loads((root/'build/cooked_cloth/manifest.json').read_text(encoding='utf-8'))
assert len(plans)==6 and {p['lod'] for p in plans}=={0,1}
for oldmm,mm in zip(before,after):
 assert oldmm['Guid']==mm['Guid']
 for old,m in zip(oldmm['meshes'],mm['meshes']):
  assert {k:v for k,v in old.items() if k!='edit_bones'}=={k:v for k,v in m.items() if k!='edit_bones'}
  if any(p['guid']==m['Guid'] for p in plans):assert m['edit_bones']==m['SkinDataSize']==m['edit_positions']
for plan in plans:
 raw=(dump/(plan['metamesh']+'_'+plan['guid']+'.bin')).read_bytes()
 assert hashlib.sha256(raw).hexdigest()==plan['sha256']
 data=read(raw);assert write(data)==raw;check_structure(data)
 m=json.loads((dump/(plan['metamesh']+'_'+plan['guid']+'.mesh.json')).read_text())
 mapping=data['render_to_sim'];nv=data['vertex_count'];p=np.array(m['positions'])
 pos=np.zeros((nv,3));pos[mapping]=p
 assert np.max(np.linalg.norm(decode_positions(data)[mapping]-p,axis=1))<.00018
 c=data['constraints'];length=np.linalg.norm(pos[c[:,0]]-pos[c[:,1]],axis=1)
 assert np.max(abs(length-data['rest_lengths']))<2e-7
 alpha=np.array(m['alpha'],np.float32)/255;alpha[plan['solver_pinned_render_vertices']]=0
 assert np.max(abs(data['max_distances'][mapping]-alpha))<1e-6
 assert np.array_equal(data['bone_indices'].reshape(-1,4)[mapping],m['bones'])
 assert np.max(abs(data['bone_weights'].reshape(-1,4)[mapping]-np.array(m['weights'])/255))<1e-7
 assert np.max(abs(data['bone_weights'].reshape(-1,4).sum(1)-1))<1e-6
 tri=mapping[np.array(m['indices']).reshape(-1,3)];selected=tri[np.any(data['max_distances'][tri]>0,axis=1)]
 assert Counter(map(tuple,selected))==Counter(map(tuple,data['dummy_indices'].reshape(-1,3)))
 edges=np.vstack((tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]))
 graph=coo_matrix((np.ones(len(edges)),(edges[:,0],edges[:,1])),shape=(nv,nv)).tocsr()
 _,labels=connected_components(graph,directed=False)
 assert np.all(labels==labels[data['anchors']>>16])
 assert np.all(labels[c[:,0]]==labels[c[:,1]])
rows=[{k:v for k,v in p.items() if k!='path'} for p in plans]
report={'status':'pass','final_package_sha256':sha(package),'uncooked_package_sha256':sha(root/'build/uncooked.tpac'),
 'all_runtime_geometry_alpha_and_skin_streams_preserved':True,'cooked_meshes':rows,
 'native_format_structure_checked':True,'game_solver_verified':False,
 'limitations':'Offline triangle network compiler; game simulation and natural falling require user testing.'}
(root/'reports/cooked_cloth_validation.json').write_text(json.dumps(report,indent=2))
print('FINAL_SET_CLOTH_VERIFIED',prefix,len(plans),'meshes')
