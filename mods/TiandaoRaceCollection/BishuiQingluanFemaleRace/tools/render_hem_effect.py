"""Render one CPU-run cycle with a fixed camera; sleeves use ordinary skinning."""
from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1]
code=(R/'tools/render_final.py').read_text().split("render('rest_front'")[0]
exec(compile(code,str(R/'tools/render_final.py'),'exec'))
sys.path.insert(0,str(WORKSPACE/'tools/cloth_compiler'))
from cloth_payload import read as read_cloth
from mapping_payload import read as read_map,reconstruct
inspection=json.loads((R/'build/mapped_final/inspection.json').read_text());body=next(m for m in inspection if m['Name']=='bql_body');proxy=next(m for m in inspection if m['Name']=='bql_cloth_proxy');segments={m['OwnerGuid']:m for m in body['segments']};d=read_cloth(Path(proxy['segments'][0]['path']));tri=d['render_to_sim'][np.array(json.loads((R/'build/proxy_source.json').read_text())['indices']).reshape(-1,3)]
inputs={json.loads(p.read_text())['name']:json.loads(p.read_text()) for p in (R/'build/cloth_final').glob('*.mesh.json')};plans={p['guid']:p for p in json.loads((R/'build/mapped_render_maps/manifest.json').read_text())};report=json.loads((R/'reports/cloth_diagnostics.json').read_text());entry=next(x for x in report['results'] if x.get('metamesh')=='bql_cloth_proxy' and x.get('motion')=='run');detail=json.loads((R/entry['report']).read_text());trace=np.load((R/entry['report']).parent/'frames.npz');rig=parse_skeljson(json.loads((R/'reports/final_skeleton.json').read_text()));anim=parse_animjson(json.loads((R/'reports/run.json').read_text()));out=R/'build/hem_preview_frames';out.mkdir(exist_ok=True)
s.render.resolution_x=600;s.render.resolution_y=760;s.cycles.samples=10;center=Vector((0,0,.83));cam.location=center+Vector((0,4,0));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.9
for light,loc in lights:light.location=center+loc;light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler()
indices=list(range(0,len(trace['positions']),3));files=[]
for k in indices:
 points=trace['positions'][k];normal=np.zeros_like(points);pt=points[tri];fn=np.cross(pt[:,1]-pt[:,0],pt[:,2]-pt[:,0]);np.add.at(normal,tri.ravel(),np.repeat(fn,3,axis=0));size=np.linalg.norm(normal,axis=1);normal[size>1e-9]/=size[size>1e-9,None];normal[size<=1e-9]=[0,0,1];frame=detail['frame_metrics'][k]['source_frame'];skin=skin_matrices(rig,anim,frame)
 for o,m in zip(objects,meshes):
  posed=lbs(m['pos'],m['bi'],m['bw'],skin)
  if m['name'] in inputs:
   source=inputs[m['name']];plan=plans[source['guid']];i,w=read_map(Path(segments[source['guid']]['path']).read_bytes());active=np.array(source['alpha'])>0;active[plan['unmapped_vertices']]=False;posed[active]=reconstruct(points,normal,i[active],w[active])
  o.data.vertices.foreach_set('co',posed.astype('f4').ravel());o.data.update()
 file=out/f'frame_{k:03d}.png';s.render.filepath=str(file);bpy.ops.render.render(write_still=True);files.append(str(file))
(R/'build/hem_preview_manifest.json').write_text(json.dumps(dict(files=files,source_indices=indices,fps=detail['settings']['fps'],game_solver_used=False),indent=2));print('HEM_SEQUENCE_RENDERED',len(files))
