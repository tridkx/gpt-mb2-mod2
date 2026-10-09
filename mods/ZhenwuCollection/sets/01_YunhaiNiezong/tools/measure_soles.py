from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
a=np.load(ROOT/'build/rig_arrays.npz');p=a['zw_yunhai_legs_02_S'];d=a['zw_yunhai_legs_02_P']
for sign in [-1,1]:
 ids=np.where((p[:,0]*sign>0)&(p[:,2]<p[:,2].min()+.002))[0]
 print('SOLE',sign,len(ids),'source',p[ids].tolist(),'target',d[ids].tolist())
