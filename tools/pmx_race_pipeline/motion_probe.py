"""Locate failure edges using final package skinning; print physical deformation."""
import sys,json
from pathlib import Path
import numpy as np
from context import config,workspace_root
def probe(root):
    c=config(root);w=workspace_root(root);sys.path[:0]=[str(w/'tools/asset_helpers/tools'),str(w/'tools/asset_helpers/previewer')]
    from georead import read_geo
    from baker.skeleton import parse_skeljson
    from baker.animation import parse_animjson,skin_matrices,lbs
    failure=json.loads((root/'reports/motion_failure.json').read_text())[-1];rig=parse_skeljson(json.loads((root/'reports/final_skeleton.json').read_text()));anim=parse_animjson(json.loads((root/'reports'/(failure['label']+'.json')).read_text()));skin=skin_matrices(rig,anim,failure['worst_frame']);m=next(m for p in (root/'build/final_export_lod0/geo').glob('*.bin') for m in read_geo(p) if m['name']==failure['worst_mesh']);tri=m['idx'].reshape(-1,3);edges=np.unique(np.sort(np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]),axis=1),axis=0);base=np.linalg.norm(m['pos'][edges[:,0]]-m['pos'][edges[:,1]],axis=1);keep=base>.002;edges=edges[keep];base=base[keep];p=lbs(m['pos'],m['bi'],m['bw'],skin);length=np.linalg.norm(p[edges[:,0]]-p[edges[:,1]],axis=1);ratio=length/base;order=np.argsort(-ratio)[:8]
    report={'id':c['id'],'failure':failure,'edges':[{'source_length_m':float(base[k]),'posed_length_m':float(length[k]),'absolute_extension_m':float(length[k]-base[k]),'ratio':float(ratio[k]),'source_positions':m['pos'][edges[k]].tolist(),'influences':[[(rig['names'][bone],int(weight)) for bone,weight in zip(m['bi'][i],m['bw'][i]) if weight] for i in edges[k]]} for k in order]};(root/'build/motion_edge_probe.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':probe(Path(sys.argv[1]).resolve())
