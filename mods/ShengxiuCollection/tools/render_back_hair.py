"""Consistent v1.1.6/new rear hair silhouette comparison from actual TPAC."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
code=(ROOT/'tools/render_hair_fit.py').read_text()
code=code.replace('build/hair_shape_final_export/geo','build/back_hair_final_export/geo')
code=code.replace("('before','final_export'),('after','hair_shape_final_export')","('before','head_neck_final_export'),('after','back_hair_final_export')")
code=code.replace('reports/hair_shape_preview.json','reports/back_hair_preview.json').replace('reports/hair_','reports/back_hair_')
code=code.replace('reports/back_hair_shape_diagnosis.json','reports/hair_shape_diagnosis.json')
code=code.replace("('after','back_hair_final_export')]", "('after','back_hair_final_export'),('gravity','back_hair_final_export')]")
code=code.replace("p=lbs(m['pos'],m['bi'],m['bw'],skin)","p=lbs(m['pos'],m['bi'],m['bw'],skin)\n  if state=='gravity' and o.name=='sx_mingyu_head_00':p=np.load(ROOT/'build/free_hair_settled_positions.npz')[f'idle_{frame}']")
code=code.replace("['before','after']", "['before','after','gravity']")
code=code.replace('native skeletal pose without cloth physics','before/after: native skeletal reference; gravity: approximate CPU relaxation, not game solver')
exec(compile(code,__file__,'exec'))
