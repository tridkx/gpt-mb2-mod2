"""Preserve skirt semantic selection after LOD decimation moves vertices."""
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
def skirt_mask(name,p,f,source):
 _,near=cKDTree(source[name+'_p']).query(p);mask=source[name+'_sk'][near].copy()
 if not source[name+'_sk'].any():return mask
 q,inv=np.unique(np.round(p,6),axis=0,return_inverse=True);ff=inv[f];e=np.concatenate([ff[:,[0,1]],ff[:,[1,2]],ff[:,[2,0]]]);count,labels=connected_components(coo_matrix((np.ones(len(e)),e.T),shape=(len(q),len(q))),directed=False)
 for c in range(count):
  ids=np.flatnonzero(labels[inv]==c);lo,hi=p[ids].min(0),p[ids].max(0)
  if lo[2]<.45 and hi[2]-lo[2]>.2:mask[ids]=p[ids,2]<1.045
 return mask
