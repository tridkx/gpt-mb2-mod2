"""Keep editable body and source UVs while removing obsolete generated proxies."""
import bpy,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from context import SERIES,config,execute
for root in SERIES.iterdir():
    if not (root/'tools/model_config.json').exists():continue
    c=config(root)
    if c.get('cloth_mode')!='direct':continue
    source=root/'source'/(c['id']+'_Rigged.blend');bpy.ops.wm.open_mainfile(filepath=str(source));proxy=bpy.data.objects.get(c['prefix']+'_cloth_proxy')
    if proxy:bpy.data.objects.remove(proxy,do_unlink=True)
    group=bpy.data.collections.get('Physics proxies')
    if group and not group.objects:bpy.data.collections.remove(group)
    for obj in bpy.data.objects:
        if obj.type=='MESH' and any(obj.name==c['prefix']+f'_part_{i:02d}' for i in c['cloth_materials']):obj['game_cloth_mode']='Direct visible mesh; no mapped proxy'
    bpy.ops.wm.save_as_mainfile(filepath=str(source));execute('verify_source',root);print('DIRECT_SOURCE_VERIFIED',root.name,flush=True)
