"""v1.4.0-based appearance repair; never uses the later cloth experiments."""
from pathlib import Path
import json,subprocess,hashlib,numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/no_cloth';OUT.mkdir(parents=True,exist_ok=True)
from appearance_transform import CONFIG,deform


def components(mesh):
 p=np.array(mesh['pos']);f=np.array(mesh['idx']).reshape(-1,3);_,inv=np.unique(np.round(p,5),axis=0,return_inverse=True)
 t=inv[f];e=np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]]);n,lab=connected_components(coo_matrix((np.ones(len(e)),(e[:,0],e[:,1])),shape=(inv.max()+1,)*2),directed=False)
 return p,f,lab[inv]

def main():
 for rel,name in [('module/TianxiangT5/AssetPackages/tx5.tpac','baseline.tpac'),('source/TianxiangT5_Rigged.blend','baseline.blend'),('source/TianxiangT5_Rigged.fbx','baseline.fbx')]:
  (OUT/name).write_bytes(subprocess.run(['git','show',CONFIG['baseline_tag']+':mods/TianxiangT5/'+rel],check=True,capture_output=True).stdout)
 assert hashlib.sha256((OUT/'baseline.tpac').read_bytes()).hexdigest()==CONFIG['baseline_package_sha256']
 subprocess.run(['dotnet',str(ROOT/'build/sleeve_tool/bin/SleeveTool.dll'),'dump',str(OUT/'baseline.tpac'),str(OUT/'baseline.json')],check=True)
 data=json.loads((OUT/'baseline.json').read_text());recipe={'config':CONFIG,'meshes':{}}
 for m in data:
  p=np.array(m['pos']);ids=np.arange(len(p));faces=np.array(m['idx']).reshape(-1,3)
  if m['name'].startswith('tx5_body_00'):
   p,faces,lab=components(m);tails=[i for i in np.unique(lab) if p[lab==i][:,2].min()<.8 and abs(p[lab==i][:,0].mean())>.25]
   assert len(tails)==2 and all(len(p[lab==i])>=20 for i in tails)
   remove=np.isin(lab,tails);assert not np.any(np.any(remove[faces],1)!=np.all(remove[faces],1))
   ids=ids[~remove];remap=np.full(len(p),-1);remap[ids]=np.arange(len(ids));faces=remap[faces[~np.any(remove[faces],1)]]
  elif not m['name'].startswith('tx5_head_'):continue
  r={'keep':ids.tolist(),'idx':faces.flatten().tolist()}
  if m['name'].startswith('tx5_head_'):
   dest,J=deform(p,m['name']);n=np.array(m['normal']);t=np.array(m['tangent']);changed=np.max(np.abs(J-np.eye(3)*1.2),axis=(1,2))>1e-10
   # Only the neck transition changes surface directions; uniform scaling keeps them byte-exact.
   changed &= np.max(np.abs(J-np.eye(3)),axis=(1,2))>1e-10
   nn=np.einsum('nij,nj->ni',np.linalg.inv(J[changed]).transpose(0,2,1),n[changed]);nn/=np.linalg.norm(nn,axis=1)[:,None]
   tt=np.einsum('nij,nj->ni',J[changed],t[changed,:3]);tt-=nn*np.sum(tt*nn,1)[:,None];tt/=np.linalg.norm(tt,axis=1)[:,None]
   n[changed]=nn;t[changed,:3]=tt;r.update(pos=dest.tolist(),normal=n.tolist(),tangent=t.tolist())
  recipe['meshes'][m['name']]=r
 (OUT/'recipe.json').write_text(json.dumps(recipe));(ROOT/'tools/appearance_config.json').write_text(json.dumps(CONFIG,indent=2))
 subprocess.run(['dotnet',str(ROOT/'build/sleeve_tool/bin/SleeveTool.dll'),'appearance',str(OUT/'baseline.tpac'),str(OUT/'recipe.json'),str(OUT/'tx5.tpac')],check=True)
if __name__=='__main__':main()
