"""Create one smooth skirt chart for coherent outer/inner layer following.

The visible source mesh is preserved. Only the shared skirt driver is solved;
all overlapping source layers use the same circumferential/height chart.
"""
from pathlib import Path
import json, numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

def make_driver(root):
    b=root/'build';cfg=json.loads((root/'tools/outer_driver_config.json').read_text())
    source=np.load(b/'fitted_model.npz');p=source['yqs_part_10_p']
    q,inv=np.unique(p,axis=0,return_inverse=True);f=inv[source['yqs_part_10_f']]
    edges=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]])
    _,labels=connected_components(coo_matrix((np.ones(len(edges)),edges.T),shape=(len(q),len(q))),directed=False)
    row=next(x for x in json.loads((root/'reports/cloth_paint.json').read_text()) if x['object']=='yqs_part_10')
    components=[x['component'] for x in row['components'] if x['kind']=='skirt']
    primary=max(components,key=lambda c:int((labels[inv]==c).sum()))
    main=p[labels[inv]==primary];all_skirt=p[np.isin(labels[inv],components)]
    center=np.array(cfg['center_xy']);radial=main[:,:2]-center
    angles=np.arctan2(radial[:,1],radial[:,0]);radius=np.linalg.norm(radial,axis=1)
    top=all_skirt[:,2].max();bottom=all_skirt[:,2].min()
    columns,rings=cfg['columns'],cfg['rings'];theta=np.arange(columns)*2*np.pi/columns
    height=np.linspace(top,bottom,rings);radii=np.empty((rings,columns))
    # Interpolate local source cross sections, then remove narrow folds. The
    # folds remain in the render mesh, not as separate solver trajectories.
    for row,z in enumerate(height):
        for col,angle in enumerate(theta):
            delta=np.arctan2(np.sin(angles-angle),np.cos(angles-angle))
            cost=(delta/.18)**2+((main[:,2]-z)/.025)**2
            ids=np.argsort(cost)[:12];w=1/np.maximum(cost[ids],.03)
            radii[row,col]=np.sum(radius[ids]*w)/w.sum()
    radii=gaussian_filter1d(radii,.75,axis=1,mode='wrap')
    radii=gaussian_filter1d(radii,.6,axis=0,mode='nearest')
    positions=np.stack([center[0]+radii*np.cos(theta),center[1]+radii*np.sin(theta),
                       np.repeat(height[:,None],columns,axis=1)],axis=-1).reshape(-1,3)
    faces=[]
    for row in range(rings-1):
        for col in range(columns):
            i=row*columns+col;j=row*columns+(col+1)%columns;k=i+columns;l=j+columns
            faces.extend([[i,k,j],[j,k,l]])
    # A horizontal radial normal makes all rest layer projections use the
    # same height coordinate and prevents projection onto another folded face.
    normals=np.tile(np.column_stack([np.cos(theta),np.sin(theta),np.zeros(columns)]),(rings,1))
    result=dict(positions=positions.tolist(),indices=faces,normals=normals.tolist(),
                chart=dict(center_xy=center.tolist(),top=float(top),bottom=float(bottom),columns=columns,rings=rings),
                source_component=primary,source_vertices=len(main))
    (b/'outer_driver.json').write_text(json.dumps(result))
    return result

def prepare(root):
    make_driver(root)
    # Keep the project's existing non-skirt source islands and package layout.
    original=(root/'tools/prepare_skirt_proxy.py').read_text()
    original=original.replace("root/'tools/skirt_proxy_config.json'", "root/'tools/outer_driver_config.json'")
    original=original.replace("build/'simplified_primary_skirt.json'", "build/'outer_driver.json'")
    original=original.replace("alpha[active]=np.maximum(alpha[active],needed[active]+.006)",
                              "alpha[active]=np.maximum(alpha[active],np.minimum(needed[active]+.004,policy['max_travel_m']))")
    original=original.replace("normals/=np.linalg.norm(normals,axis=1)[:,None]",
                              "normals=np.array(primary_mesh['normals'])")
    original=original.replace("method='Simplified primary skirt surface drives layers; separate source attachment islands for other cloth'",
                              "method='Coherent shared skirt chart: outer motion, inner following; non-skirt islands preserved'")
    namespace={'__name__':'outer_driver_preparation'}
    exec(compile(original,str(root/'tools/prepare_skirt_proxy.py'),'exec'),namespace)
    namespace['prepare'](root)
    source=json.loads((root/'build/proxy_source.json').read_text());source['chart']=json.loads((root/'build/outer_driver.json').read_text())['chart']
    (root/'build/proxy_source.json').write_text(json.dumps(source))
