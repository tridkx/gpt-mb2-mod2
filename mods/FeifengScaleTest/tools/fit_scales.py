from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
R=Path(__file__).resolve().parents[1];data=np.load(R/'build/scale_fit_input.npz');L=data['native_local'];parent=data['parent'];goal=data['goal'];n=len(parent)
adjustable=[i for i in range(1,n) if i in parent]
def scale_array(x):
 scales=np.ones((n,3));scales[0]=1.5;scales[adjustable]=np.exp(x.reshape(-1,3));return scales
def residual(x):
 scales=scale_array(x);world=np.zeros_like(L)
 for i in range(n):
  local=L[i].copy();local[:3,:3]=local[:3,:3]@np.diag(scales[i]);world[i]=local if parent[i]<0 else world[parent[i]]@local
 return np.r_[(world[:,:3,3]-goal).ravel(),.003*x]
fit=least_squares(residual,np.zeros(len(adjustable)*3),bounds=(np.log(.65),np.log(1.5)),max_nfev=200)
assert fit.success,fit.message
np.save(R/'build/scale_fit_output.npy',scale_array(fit.x));print('SCALE_FIT_READY',fit.cost)
