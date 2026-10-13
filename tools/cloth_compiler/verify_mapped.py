"""Validate final native mapping bytes and preserve all original GPU geometry."""
from pathlib import Path
import json,sys,subprocess,hashlib,struct,zipfile
import numpy as np
from cloth_payload import read as read_cloth,write as write_cloth
from mapping_payload import read as read_map,write as write_map
from validation import check_structure

def streams(path):
    raw=path.read_bytes();offset=12;magic,version,count=struct.unpack_from('<III',raw);result={}
    def take(n):
        nonlocal offset
        value=raw[offset:offset+n];offset+=n;return value
    def blob():return take(struct.unpack('<I',take(4))[0])
    for _ in range(count):
        name=blob().decode();lod=take(4);material=blob();guid=blob();n,ni=struct.unpack('<II',take(8));bbox=take(24);flags=struct.unpack('<I',take(4))[0];fields={}
        for key,size,enabled in [('positions',12,1),('normals',12,flags&1),('uv',8,1),('uv2',8,flags&2),('colors',4,flags&4),('colors2',4,flags&8),('tangents',16,flags&16),('bones',4,flags&32),('weights',4,1)]:
            if enabled:fields[key]=take(n*size)
        fields['indices']=take(ni*4);result[name]=dict(lod=lod,material=material,guid=guid,n=n,ni=ni,bbox=bbox,flags=flags,fields=fields)
    assert offset==len(raw);return result

def verify(root):
    cfg=json.loads((root/'tools/model_config.json').read_text());prefix=cfg.get('prefix','yqs');b=root/'build';candidate=b/'mapped_candidate.tpac';mb='D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe'
    def run(args):return subprocess.run([str(x) for x in args],check=True,capture_output=True,text=True,encoding='utf8').stdout
    run([mb,'metacheck',candidate]);run([mb,'mataudit',candidate])
    output=b/'mapped_final';output.mkdir(exist_ok=True)
    run(['dotnet',b/'mapped_patch/MappedClothPatch.dll','--inspect',candidate,prefix+'_body',prefix+'_cloth_proxy',output])
    inspected=json.loads((output/'inspection.json').read_text());body=next(m for m in inspected if m['Name']==prefix+'_body');proxy=next(m for m in inspected if m['Name']==prefix+'_cloth_proxy')
    assert body['ClothMetamesh']==proxy['Guid'] and proxy['ClothMetamesh']=='00000000-0000-0000-0000-000000000000'
    assert body['body']==prefix+'_collision' and proxy['body']==prefix+'_collision'
    assert len(proxy['meshes'])==1 and len(proxy['segments'])==1
    direct=proxy['segments'][0];assert direct['TypeGuid']=='b97e0f10-df49-4666-8f1d-ada6630d4b4e'
    data=read_cloth(Path(direct['path']));check_structure(data);assert write_cloth(data)==Path(direct['path']).read_bytes()
    expected=json.loads((b/'mapped_proxy_cooked/manifest.json').read_text())[0];assert direct['sha256']==expected['sha256']
    plans=json.loads((b/'mapped_render_maps/manifest.json').read_text());segments={m['OwnerGuid']:m for m in body['segments']}
    assert len(segments)==len(plans) and all(m['TypeGuid']=='af41613e-bd4d-46ec-8284-debb56c042dc' for m in body['segments'])
    for plan in plans:
        segment=segments[plan['guid']];assert segment['sha256']==plan['sha256'];raw=Path(segment['path']).read_bytes();i,w=read_map(raw);assert write_map(i,w)==raw
        assert i.max()<data['vertex_count'] and np.isfinite(w).all() and abs(w[:,:3].sum(1)-1).max()<2e-6
    rows=[];allowed_by_guid={plan['guid']:set(plan['unmapped_vertices']) for plan in plans};allowed={}
    for path in (b/'cloth_final').glob('*.mesh.json'):
        reference=json.loads(path.read_text());allowed[reference['name']]=allowed_by_guid[reference['guid']]
    baseline=b/'mapped_baseline_direct.tpac'
    if not baseline.exists():baseline=root/'module'/cfg['id']/'AssetPackages'/(prefix+'.tpac')
    for lod in range(4):
        old=b/f'mapping_baseline_lod{lod}';new=b/f'mapping_candidate_lod{lod}'
        run([mb,'exportmod',baseline,old,lod]+(['--all-mips'] if lod==0 else []));run([mb,'exportmod',candidate,new,lod]+(['--all-mips'] if lod==0 else []))
        before={};after={}
        for path in (old/'geo').glob('*.bin'):before.update(streams(path))
        for path in (new/'geo').glob('*.bin'):after.update(streams(path))
        changed=[]
        for name,a in before.items():
            z=after[name];assert {k:v for k,v in a.items() if k!='fields'}=={k:v for k,v in z.items() if k!='fields'},name
            for field,raw in a['fields'].items():
                current=z['fields'][field]
                if current==raw:continue
                assert field=='colors',(name,field)
                ac=np.frombuffer(raw,'u1').reshape(-1,4);bc=np.frombuffer(current,'u1').reshape(-1,4);assert np.array_equal(ac[:,:3],bc[:,:3]);ids=set(np.flatnonzero(ac[:,3]!=bc[:,3]).tolist());assert ids<=allowed[name] and not bc[list(ids),3].any()
                changed.append(dict(mesh=name,previous_solver_pins_unmapped=len(ids)))
        oldpack=json.loads((old/'pack.json').read_text());newpack=json.loads((new/'pack.json').read_text());assert oldpack['materials']==newpack['materials'] and oldpack['skeletons']==newpack['skeletons']
        if lod==0:
            for texture in oldpack['textures']:assert (old/texture['file']).read_bytes()==(new/texture['file']).read_bytes()
        rows.append(dict(lod=lod,original_meshes=len(before),geometry_normals_uv_tangents_bones_weights_indices_identical=True,alpha_changes=changed))
    candidate_report=json.loads((root/'reports/mapped_cloth_candidate.json').read_text())
    report=dict(status='pass',candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),baseline_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),proxy_simulation_vertices=data['vertex_count'],render_mapping_segments=len(plans),lods=rows,materials_textures_skeleton_identical=True,rest_reconstruction_max_error_m=max(m['rest_reconstruction_max_error_m'] for m in candidate_report['render_maps']),game_verified=False,scope='Candidate TPAC reopened; native mapping and cloth roundtrips, ownership, shared reference and full GPU stream preservation')
    (root/'reports/mapped_structure_validation.json').write_text(json.dumps(report,indent=2));print('MAPPED_STRUCTURE_VERIFIED',root.name,report['proxy_simulation_vertices'],len(plans))

if __name__=='__main__':verify(Path(sys.argv[1]).resolve())
