"""Native barycentric mapping constrained to one shared skirt chart."""
import json,numpy as np
from pathlib import Path
from mapping_payload import project as nearest_project, reconstruct
from cloth_payload import read

def mapper(root):
    def project(points,vertices,normals,triangles):
        b=root/'build';source=json.loads((b/'proxy_source.json').read_text());n=len(source['skirt_vertices'])
        plan=json.loads((b/'mapped_proxy_cooked/manifest.json').read_text())[0]
        d=read(Path(plan['path']));grid=d['render_to_sim'][:n]
        if not np.isin(triangles,grid).all():
            return nearest_project(points,vertices,normals,triangles)
        chart=source['chart'];cols,rings=chart['columns'],chart['rings'];center=np.array(chart['center_xy'])
        angle=np.mod(np.arctan2(points[:,1]-center[1],points[:,0]-center[0]),2*np.pi)
        col=np.floor(angle*cols/(2*np.pi)).astype(int)
        row=np.floor((chart['top']-points[:,2])/(chart['top']-chart['bottom'])*(rings-1)).astype(int)
        row=np.clip(row,0,rings-2)
        offsets=np.array([(a,c,h) for a in [-1,0,1] for c in [-1,0,1] for h in [0,1]])
        rr=np.clip(row[:,None]+offsets[:,0],0,rings-2);cc=(col[:,None]+offsets[:,1])%cols
        i=rr*cols+cc;j=rr*cols+(cc+1)%cols;k=i+cols;l=j+cols
        candidates=np.stack([np.where(offsets[:,2]==0,i,j),k,np.where(offsets[:,2]==0,j,l)],axis=-1)
        indices=grid[candidates];corners=vertices[indices];tn=normals[indices]
        e1=corners[:,:,1]-corners[:,:,0];e2=corners[:,:,2]-corners[:,:,0]
        normal=np.cross(e1,e2);normal/=np.maximum(np.linalg.norm(normal,axis=2)[:,:,None],1e-12)
        q=points[:,None]-corners[:,:,0]
        coeff=np.linalg.solve(np.stack([e1,e2,normal],axis=-1),q[...,None])[...,0]
        for _ in range(30):
            bary=np.stack([1-coeff[:,:,0]-coeff[:,:,1],coeff[:,:,0],coeff[:,:,1]],axis=-1)
            raw=(tn*bary[:,:,:,None]).sum(2);size=np.maximum(np.linalg.norm(raw,axis=2),1e-12);normal=raw/size[:,:,None]
            da=tn[:,:,1]-tn[:,:,0];db=tn[:,:,2]-tn[:,:,0]
            dna=(da-normal*(normal*da).sum(2)[:,:,None])/size[:,:,None]
            dnb=(db-normal*(normal*db).sum(2)[:,:,None])/size[:,:,None]
            residual=q-e1*coeff[:,:,0,None]-e2*coeff[:,:,1,None]-normal*coeff[:,:,2,None]
            jac=np.stack([e1+dna*coeff[:,:,2,None],e2+dnb*coeff[:,:,2,None],normal],axis=-1)
            step=np.linalg.solve(jac,residual[...,None])[...,0]
            coeff+=step*np.minimum(1,.25/np.maximum(abs(step[:,:,:2]).max(2),1e-12))[:,:,None]
        bary=np.stack([1-coeff[:,:,0]-coeff[:,:,1],coeff[:,:,0],coeff[:,:,1]],axis=-1)
        normal=(tn*bary[:,:,:,None]).sum(2);normal/=np.maximum(np.linalg.norm(normal,axis=2)[:,:,None],1e-12)
        rebuilt=(corners*bary[:,:,:,None]).sum(2)+normal*coeff[:,:,2,None]
        error=np.linalg.norm(rebuilt-points[:,None],axis=2)
        penalty=np.maximum(-bary,0).sum(2)+np.maximum(bary-1,0).sum(2)
        # Prefer contained chart coordinates rather than another overlapping
        # render layer or a nearby fold with the smallest normal offset.
        cost=penalty*10+error*1000+np.abs(offsets[:,0])[None,:]*.0001+np.abs(offsets[:,1])[None,:]*.0001
        choice=cost.argmin(1);rows=np.arange(len(points))
        out_i=indices[rows,choice];out_w=np.column_stack([bary[rows,choice],coeff[rows,choice,2]]).astype('f4')
        assert np.isfinite(out_w).all()
        assert np.max(np.linalg.norm(reconstruct(vertices,normals,out_i,out_w)-points,axis=1))<.001
        return out_i,out_w
    return project
