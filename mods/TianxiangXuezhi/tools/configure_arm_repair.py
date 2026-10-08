"""Repair sleeve attachment and bend following without changing skirt fitting."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'tools/rig_model.py';s=path.read_text()
start=s.index("        if cfg.get('sleeve_projected_anchor'):") if "        if cfg.get('sleeve_projected_anchor'):" in s else s.index("        # Hanging fabric uses")
end=s.index("        # Limit sleeve motion;",start)
s=s[:start]+'''        # Hanging fabric uses the full upper-arm/elbow/wrist chain.
        # Near the shoulder and arm surface, use the same anatomical function
        # as skin so their attachment cannot rotate about different pivots.
        for sign,upper,elbow,hand in [(-1,15,17,19),(1,22,24,26)]:
            ids=np.where(p[:,0]*sign>0)[0];q=p[ids]
            x=np.abs(q[:,0]);u=source[upper];e=source[elbow];h=source[hand]
            t=smooth(.20,.46,x)
            projected=np.zeros((len(q),28))
            projected[:,upper]=1-t;projected[:,elbow]=t
            blend=smooth(.12,.23,x)
            w[ids]=body_weights(q,arms=True)*(1-blend[:,None])+projected*blend[:,None]
''' +s[end:]
# Restore anatomical shoulder attachment only at the upper dress edge.
needle="        w=anatomical;w[skirt_mask]=skirtw[skirt_mask]"
replacement=needle+"\n        shoulder=(p[:,2]>1.35)&(np.abs(p[:,0])>.07)&(~skirt_mask)\n        w[shoulder]=body_weights(p[shoulder],arms=True)"
if replacement not in s:s=s.replace(needle,replacement)
path.write_text(s,encoding='utf-8')
# Keep shoulder and sleeve attachments in every LOD, avoiding decimation gaps.
path=ROOT/'tools/export_geometry.py';s=path.read_text()
s=s.replace("and r['kind']!='skirt' and r['part']!='legs':", "and r['kind'] not in ['skirt','upper_clothes'] and r['part']!='legs':")
path.write_text(s,encoding='utf-8')
print('ARM_REPAIR_CONFIGURED')
