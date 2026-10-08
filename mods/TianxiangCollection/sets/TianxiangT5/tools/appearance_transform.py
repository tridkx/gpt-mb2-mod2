from pathlib import Path
import json,numpy as np
CONFIG=json.loads((Path(__file__).parent/"appearance_config.json").read_text())

def deform(p,name):
 p=np.asarray(p,dtype=float);q=p-np.array(CONFIG['head_pivot']);w=np.ones(len(p));der=np.zeros(len(p))
 if name.startswith('tx5_head_11'):
  lo,hi=CONFIG['neck_transition'];u=np.clip((p[:,2]-lo)/(hi-lo),0,1);w=u*u*(3-2*u);der=6*u*(1-u)/(hi-lo)
 scale=1+.2*w;J=np.repeat(np.eye(3)[None],len(p),axis=0)*scale[:,None,None];J[:,:,2]+=.2*der[:,None]*q
 return np.array(CONFIG['head_pivot'])+scale[:,None]*q,J
