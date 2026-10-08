"""Prepare true native skinning poses; no physics approximation."""
from pathlib import Path
import json,numpy as np
from sleeve_motion import skin_frames,posed
ROOT=Path(__file__).resolve().parents[1]
meshes={m['name']:m for m in json.loads((ROOT/'build/direct_cloth/final.json').read_text()) if m['lod']==0}
rig=json.loads((ROOT/'reports/human_skeleton.json').read_text());records=[]
for label,filename in [('idle','idle'),('block','grip_twohanded_block'),('run','run')]:
    anim=json.loads((ROOT/f'reports/{filename}.json').read_text());skins,worlds=skin_frames(rig,anim)
    frame=0 if label=='idle' else int(np.argmax(worlds[:,[19,26],2,3].mean(1))) if label=='block' else int(np.argmax(np.abs(worlds[:,3,1,3]-worlds[:,7,1,3])))
    np.savez_compressed(ROOT/f'build/direct_cloth/review_{label}.npz',**{name:posed(m,skins[frame]) for name,m in meshes.items()})
    records.append({'pose':label,'asset':anim['name'],'frame':frame+1,'image':f'direct_review_{label}.png'})
(ROOT/'reports/direct_review.json').write_text(json.dumps({'version':'v1.6.0','method':'Final TPAC skinning, no cloth solver or weapon IK. Mask colors indicate alpha, not movement.','frames':records},indent=2))
