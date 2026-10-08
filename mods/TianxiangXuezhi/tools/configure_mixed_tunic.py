"""Model-specific torso/skirt anchoring for Xuezhi's combined tunic mesh."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'tools/rig_model.py';s=path.read_text();start=s.index("    if kind=='skirt':");end=s.index("    if kind=='upper_clothes':",start)
block="""    if kind=='skirt':
        # Central tunic must not inherit the nearby forearm/hand at waist height.
        anatomical=body_weights(p,arms=False)
        parent=list(range(len(p)))
        def find(v):
            while parent[v]!=v:parent[v]=parent[parent[v]];v=parent[v]
            return v
        for edge in o.data.edges:parent[find(edge.vertices[1])]=find(edge.vertices[0])
        components={}
        for vi in range(len(p)):components.setdefault(find(vi),[]).append(vi)
        skirt_mask=np.zeros(len(p),bool)
        for ids in components.values():
            q=p[ids]
            if q[:,2].max()<cfg['mixed_skirt_component_max_z'] and q[:,2].mean()<cfg['mixed_skirt_component_mean_z']:skirt_mask[ids]=True
        width=cfg['skirt_center_width'];right=smooth(-width,width,p[:,0]);low=1-smooth(.40,.78,p[:,2]);amount=cfg['skirt_calf_share']
        left_calf=low*amount*(1-smooth(-width,0,p[:,0]));right_calf=low*amount*smooth(0,width,p[:,0])
        legs=np.zeros_like(w);legs[:,1]=(1-right)*(1-left_calf);legs[:,2]=(1-right)*left_calf;legs[:,5]=right*(1-right_calf);legs[:,6]=right*right_calf
        follow=cfg['skirt_thigh_follow']*(1-smooth(.87,1.09,p[:,2]));skirtw=legs*follow[:,None];skirtw[:,0]+=1-follow
        w=anatomical;w[skirt_mask]=skirtw[skirt_mask]
        alpha[skirt_mask]=cfg['cloth_max_distance'][kind]*(1-smooth(.43,1.10,p[skirt_mask,2]))
"""
s=s[:start]+block+s[end:]
s=s.replace("    if kind=='skirt':", "    if kind=='accessories':\n        w=body_weights(p,arms=False)\n        ear=np.abs(p[:,0])>cfg['ear_accessory_min_x']\n        w[ear]=0;w[ear,13]=1\n    if kind=='skirt':",1)
s=s.replace("free=1-smooth(.85,1.10,p[:,2]);rad=","free=(1-smooth(.85,1.10,p[:,2]))*(a['A']>0);rad=")
path.write_text(s)
path=ROOT/'tools/export_geometry.py';s=path.read_text();s=s.replace("if lod and r['texture_key'] not in ['face','eye','lash']:","if lod and r['texture_key'] not in ['face','eye','lash'] and r['kind']!='skirt' and r['part']!='legs':");path.write_text(s)
print('XUEZHI_MIXED_TUNIC_CONFIGURED')

