"""Identify actual stretched final-package meshes without weakening release checks."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
code=(ROOT/'tools/verify_release.py').read_text()
exec(code[:code.index("rig=parse_skeljson")])
rig=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()))
for label in ['idle','run','bow','riding']:
    anim=parse_animjson(json.loads((ROOT/'reports'/(label+'.json')).read_text()))
    results=[]
    for m in exports[0]:
        tri=m['idx'].reshape(-1,3);edges=np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]);a,b=edges.T
        length=np.linalg.norm(m['pos'][a]-m['pos'][b],axis=1);valid=length>.003
        mx=0;q99=0
        for frame in range(max(1,anim['start']),anim['frames'],max(1,anim['frames']//20)):
            p=lbs(m['pos'],m['bi'],m['bw'],skin_matrices(rig,anim,frame))
            ratio=np.linalg.norm(p[a[valid]]-p[b[valid]],axis=1)/length[valid]
            mx=max(mx,float(ratio.max()));q99=max(q99,float(np.quantile(ratio,.99)))
        results.append((round(mx,3),round(q99,3),m['name']))
    print(label,sorted(results,reverse=True))
