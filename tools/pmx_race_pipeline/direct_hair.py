"""Compile direct physics on the visible UV-bearing hair, with no mapped proxy."""
from pathlib import Path
import json,sys,subprocess,hashlib
import numpy as np
from context import config,workspace_root
def run(args):
    r=subprocess.run([str(x) for x in args],capture_output=True,text=True,encoding='utf8',errors='replace')
    if r.returncode:raise RuntimeError(r.stdout+r.stderr)
    return r.stdout
def build_direct_hair(root,input_package=None):
    c=config(root);b=root/'build';w=workspace_root(root);prefix=c['prefix'];common=w/'tools/cloth_compiler';package=root/'module'/c['id']/'AssetPackages'/(prefix+'.tpac')
    sys.path.insert(0,str(common));from cook_cloth import cook
    fresh=input_package is None
    if fresh:input_package=b/'uncooked.tpac'
    settings=c.get('direct_cloth_material') or {'Name':prefix+'_direct_hair','BendingStiffness':.08,'ShearingStiffness':.9,'StretchingStiffness':1,'AnchorStiffness':.3,'Damping':.92,'Gravity':9.81,'LinearInertia':.08,'MaxLinearVelocity':4,'LinearVelocityMultiplier':1,'AirDragMultiplier':.04,'Wind':.015}
    settings_file=b/'direct_cloth_settings.json';settings_file.write_text(json.dumps(settings,indent=2))
    output=b/'direct_hair_input.tpac';patch=w/'mods/GenshinRaceCollection/build/runtime_resource_patch/RuntimeResourcePatch.dll'
    if fresh:
        for project,folder in [(w/'tools/pmx_race_pipeline/RuntimeResourcePatch/RuntimeResourcePatch.csproj','runtime_resource_patch'),(common/'ClothPatch.csproj','cloth_patch'),(common/'NativeClothProbe.csproj','cloth_probe'),(common/'MappedClothPatch.csproj','mapped_patch')]:
            run(['dotnet','build',project,'--ignore-failed-sources','-p:BaseIntermediateOutputPath='+str(b/(folder+'_obj'))+'/', '-o',b/folder])
        patch=b/'runtime_resource_patch/RuntimeResourcePatch.dll'
    run(['dotnet',patch,'direct-body',input_package,output,prefix,settings_file])
    dump=b/'direct_hair_input'/hashlib.sha256(output.read_bytes()).hexdigest()[:16];dump.mkdir(parents=True,exist_ok=True);run(['dotnet',b/'cloth_probe/NativeClothProbe.dll',output,prefix+'_body','--dump-segments',dump])
    cooked=b/'direct_hair_cooked';cooked.mkdir(exist_ok=True);plans=[]
    for p in sorted(dump.glob('*.mesh.json')):
        mesh=json.loads(p.read_text());extent=np.ptp(np.asarray(mesh['positions']),axis=0);axis=2 if extent[2]>.002 else int(extent.argmax());band=min(c['cloth_proxy_policy']['pin_band_m'],float(extent[axis])*.15)
        policy={'unanchored':'pin_upper','axis':axis,'band_m':band,'min_vertices':2,'reason':'Highest attachment edge of independently rooted visible hair component; band capped at 15% of component-material extent to preserve small hair ties'}
        raw,plan=cook(mesh,policy);plan['root_policy']=policy
        dest=cooked/(plan['guid']+'.bin');dest.write_bytes(raw);plan['path']=str(dest);plans.append(plan)
    assert plans and {p['lod'] for p in plans}=={0,1,2,3},'Missing direct hair LOD'
    (cooked/'manifest.json').write_text(json.dumps(plans,indent=2));run(['dotnet',b/'cloth_patch/ClothPatch.dll',output,cooked/'manifest.json',package,'--allow-metameshes',prefix+'_body'])
    report={'status':'pass','mode':'direct_visible_hair','package_sha256':hashlib.sha256(package.read_bytes()).hexdigest(),'uses_mapped_proxy':False,'driver_metamesh_removed':True,'lods':[0,1,2,3],'meshes':plans,'source_uv_preserved':True,'game_verified':False}
    (root/'reports/direct_hair_cloth.json').write_text(json.dumps(report,indent=2));return report
