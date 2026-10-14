"""Inspect the final candidate's skirt driver and mapped surfaces in CPU motion.

The source clips are sampled at an assumed 60 fps, without game blending.
Non-skirt islands are excluded from this bounded diagnostic. This is not
engine simulation, self collision, or complete rendered-body acceptance.
"""
from pathlib import Path
from types import SimpleNamespace
import json, sys, hashlib
import numpy as np
from threadpoolctl import threadpool_limits
from workspace_paths import workspace_root

R = Path(__file__).resolve().parents[1]
W = workspace_root(R)
sys.path[:0] = [str(W/'tools'), str(W/'tools/cloth_compiler'), str(W/'tools/asset_helpers/previewer')]
from cloth_payload import read, decode_positions
from mapping_payload import read as read_map, reconstruct
from cloth_simulator.run import native_motion, render_output
from cloth_simulator.solver import Simulator, Settings
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson, skin_matrices, lbs

def main():
    b = R/'build'
    inspection = json.loads((b/'mapped_final/inspection.json').read_text())
    proxy = next(x for x in inspection if x['Name']=='yqs_cloth_proxy')
    d = read(Path(proxy['segments'][0]['path']))
    source = json.loads((b/'proxy_source.json').read_text())
    cfg = json.loads((R/'tools/skirt_proxy_config.json').read_text())
    cage = np.unique(d['render_to_sim'][source['skirt_vertices']])
    mask = np.zeros(d['vertex_count'], bool); mask[cage] = True
    native_data = dict(d)
    d['max_distances'] = d['max_distances'].copy(); d['max_distances'][~mask] = 0
    # Retain the final payload's grouping; remove only independent islands.
    edges, lengths, sets = [], [], []
    for row in d['constraint_sets']:
        result = []
        for start, count in row.reshape(4,2):
            e = d['constraints'][start:start+count]
            keep = mask[e].all(1)
            result.extend([len(edges), int(keep.sum())])
            edges.extend(e[keep]); lengths.extend(d['rest_lengths'][start:start+count][keep])
        sets.append(result)
    inverse = np.full(d['vertex_count'],-1,int); inverse[cage]=np.arange(len(cage))
    d['constraints'] = inverse[np.asarray(edges)]; d['rest_lengths'] = np.asarray(lengths)
    d['constraint_sets'] = np.asarray(sets)
    d['dummy_sets'] = np.empty((0,2),int)
    tri = d['render_to_sim'][np.asarray(source['indices']).reshape(-1,3)]
    tri = tri[mask[tri].all(1)]
    full_tri = tri.copy()
    tri = inverse[tri]
    roots = inverse[(d['anchors'][cage]>>16).astype(int)]
    assert roots.min()>=0, 'Skirt anchors cross into another cloth island'
    d['anchors']=(roots.astype('u4')<<16)|(d['anchors'][cage]&65535)
    d['max_distances']=d['max_distances'][cage]
    d['vertex_count']=len(cage)
    output = b/'simplified_skirt_motion'
    output.mkdir(exist_ok=True)
    settings = Settings(fps=60, substeps=2, iterations=4, bend=.3, anchor=.8,
                        damping=.92, dummy_collision=False)
    rig = parse_skeljson(json.loads((R/'reports/final_skeleton.json').read_text()))
    manifest = {x['guid']: x for x in json.loads((b/'mapped_render_maps/manifest.json').read_text())}
    summary = []
    for name in ['ui_neutral_female','run','riding']:
        args = SimpleNamespace(skeleton=R/'reports/final_skeleton.json',
            animation=R/'reports'/(name+'.json'), capsules=R/'module/YueQingShuRace/ModuleData/cloth_bodies.xml',
            body='yqs_collision', start=0, end=61 if name=='ui_neutral_female' else None)
        all_anchors, capsules, frames, metadata = native_motion(args, native_data)
        anchors = all_anchors[:,cage]
        warmup = 30
        anchors = np.concatenate([np.repeat(anchors[:1],warmup,0), anchors])
        capsules = np.concatenate([np.repeat(capsules[:1],warmup,0), capsules])
        sim = Simulator(d, tri, settings)
        points, rows, heat = sim.run(anchors, capsules, d['max_distances'])
        points, anchors, capsules, heat, rows = points[warmup:], anchors[warmup:], capsules[warmup:], heat[warmup:], rows[warmup:]
        for row, frame in zip(rows,frames): row['source_frame']=frame
        folder = output/name; folder.mkdir(exist_ok=True)
        worst = render_output(folder,points,anchors,capsules,tri,rows,heat,60,'CPU skirt driver: '+name)
        np.savez_compressed(folder/'frames.npz', positions=points, anchors=anchors, triangles=tri, capsules=capsules)
        metrics = {key:max(row[key] for row in rows) for key in rows[0] if key not in ('frame','source_frame','time_s')}
        # Reconstruct visible surfaces from final native mapping at worst contact.
        x = all_anchors[worst].copy(); x[cage]=points[worst]
        normals = np.zeros_like(x)
        cross = np.cross(x[full_tri[:,1]]-x[full_tri[:,0]],x[full_tri[:,2]]-x[full_tri[:,0]])
        np.add.at(normals,full_tri.ravel(),np.repeat(cross,3,axis=0))
        normals /= np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12)
        anim = parse_animjson(json.loads(args.animation.read_text()))
        skin = skin_matrices(rig,anim,frames[worst])
        for path in (b/'cloth_final').glob('*.mesh.json'):
            mesh = json.loads(path.read_text())
            if mesh['lod']!=0: continue
            plan=manifest[mesh['guid']]; i,w=read_map(Path(plan['path']).read_bytes())
            active=np.asarray(mesh['alpha'])>0; active[plan['unmapped_vertices']]=False
            selected=active&mask[i].all(1)
            if not selected.any(): continue
            before=lbs(np.asarray(mesh['positions']),np.asarray(mesh['bones']),np.asarray(mesh['weights']),skin)
            after=before.copy(); after[selected]=reconstruct(x,normals,i[selected],w[selected])
            assert np.isfinite(after).all()
            np.savez_compressed(folder/(mesh['name']+'_mapped.npz'), before=before,after=after,indices=mesh['indices'])
        row=dict(motion=name,frames=len(frames),worst_source_frame=frames[worst],maxima=metrics,
            scope='Skirt driver only; final mapping reconstructed at worst contact frame',
            source_frame_range=[frames[0],frames[-1]],warmup_frames=warmup,
            diagnostic_parameters=dict(substeps=settings.substeps,iterations=settings.iterations,bend=settings.bend,anchor=settings.anchor,damping=settings.damping),fps=60,fps_calibrated_to_game=False,game_solver_used=False,game_verified=False,
            self_collision_supported=False,interior_collision_projection=False)
        (folder/'report.json').write_text(json.dumps(dict(**row,per_frame=rows),indent=2))
        summary.append(row); print('SKIRT_MOTION',name,metrics,flush=True)
    report=dict(candidate_sha256=hashlib.sha256((b/'mapped_candidate.tpac').read_bytes()).hexdigest(),
        status='needs_visual_review',motions=summary,game_verified=False)
    (R/'reports/simplified_skirt_motion.json').write_text(json.dumps(report,indent=2))

if __name__=='__main__':
    # These small matrix/vector operations are slower with a large BLAS pool.
    with threadpool_limits(limits=1):
        main()
