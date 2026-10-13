"""Align only the source-sized arm bind axes; preserve positions and native roll."""
import numpy as np
def align(world,names):
 world=world.copy();S=world[:,:3,3].copy();rows=[]
 for pre in ['l','r']:
  for bone,a,b in [('upperarm_twist','upperarm_twist','foretwist'),('upperarm_twist1','upperarm_twist','foretwist'),('foretwist','foretwist','hand'),('foretwist1','foretwist','hand')]:
   i=names.index(pre+'_'+bone);axis=world[i,:3,0].copy();axis/=np.linalg.norm(axis);v=S[names.index(pre+'_'+b)]-S[names.index(pre+'_'+a)];v/=np.linalg.norm(v);cross=np.cross(axis,v);dot=float(axis@v);assert dot>-.99
   K=np.array([[0,-cross[2],cross[1]],[cross[2],0,-cross[0]],[-cross[1],cross[0],0]]);Q=np.eye(3)+K+K@K/(1+dot);world[i,:3,:3]=Q@world[i,:3,:3];rows.append(dict(bone=pre+'_'+bone,rotation_degrees=float(np.degrees(np.arccos(np.clip(dot,-1,1))))))
 assert np.array_equal(world[:,:3,3],S);return world,rows
