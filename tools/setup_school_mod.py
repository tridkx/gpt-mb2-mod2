"""Adapt proven pipeline logic to an inspected, individually configured model.

Run after source inspection and reviewed model_config.json. No source IDs,
mesh plans, fitting landmarks or baseline assertions are inherited.
"""
import sys,json,shutil
from pathlib import Path
WS=Path(__file__).resolve().parents[1];root=WS/'mods'/sys.argv[1]
cfg=json.loads((root/'tools/model_config.json').read_text());ident=cfg['id'];prefix=cfg['prefix'];title=cfg['title'];display=cfg['display_name']
inspection=json.loads((root/'reports/source_inspection.json').read_text());assert inspection['armatures']==0
assert set(cfg['parts'])=={m['name'] for m in inspection['meshes']}
base=WS/'mods/TianxiangRenqiu'
def adapt(s):return s.replace('TianxiangRenqiu',ident).replace('rq1',prefix).replace('Renqiu',ident)
for name in ['rig_model.py','export_geometry.py','build_package.py','verify_release.py','verify_source.py','render_review.py','prepare_delivery.py']:
    s=adapt((base/'tools'/name).read_text())
    if name=='rig_model.py':
        s=s.replace("waist=weights(p,[0,9,10]);right=", "waist=weights(p,[0,9] if cfg.get('skirt_weight_mode')=='four_anchor' else [0,9,10]);right=")
        s=s.replace("low=1-smooth(.40,.78,p[:,2])", "low=np.zeros(len(p)) if cfg.get('skirt_weight_mode')=='four_anchor' else 1-smooth(.40,.78,p[:,2])")
    if name=='verify_release.py':
        s=s.replace("assert len(visibility['materials'])==9","assert len(visibility['materials'])==len(json.loads((ROOT/'tools/model_config.json').read_text())['textures'])")
        s=s.replace('assert len(meshes)==15',f"assert len(meshes)=={len(cfg['parts'])}")
        s=s.replace(f"if m['name']=='{prefix}_body_12':","if m['name'] in {r['object'] for r in fit['parts'] if r['kind']=='skirt'}:")
        start=s.index("baseline=ROOT/");end=s.index("report=",start);s=s[:start]+s[end:]
        s=s.replace("sha(baseline) if baseline.exists() else None","None").replace("'v1.0.0 eye repair baseline' if baseline.exists() else 'first release, original FBX retained'","'first release; original input preserved'")
    if name=='verify_source.py':s=s.replace("original=Path('D:/dsh-tiandao/天香少女校服8套/01纫秋为佩')","original=Path(cfg['original_directory'])")
    if name=='render_review.py':
        s=s.replace(f"eye=next(o for o in objects if o.name=='{prefix}_head_00')","eye=next(o for o in objects if o.name in {r['object'] for r in json.loads((ROOT/'build/rig_manifest.json').read_text()) if r['texture_key']=='eye'})")
        s=s.replace('for o in objects:o.hide_render=False','for o in objects:o.hide_render=False\n    s.render.resolution_x=800;s.render.resolution_y=1000;s.cycles.samples=12')
        s=s.replace(f"['{prefix}_head_03','{prefix}_head_09']", "[r['object'] for r in json.loads((ROOT/'build/rig_manifest.json').read_text()) if r['texture_key']=='lash']")
    (root/'tools'/name).write_text(s,encoding='utf-8')
patch=root/'tools/PackagePatch';patch.mkdir(exist_ok=True)
for name in ['Program.cs','PackagePatch.csproj']:(patch/name).write_text(adapt((base/'tools/PackagePatch'/name).read_text()),encoding='utf-8')
for name in ['human_skeleton.json','idle.json','run.json','bow.json','riding.json']:
    shutil.copy2(base/'reports'/name,root/'reports'/name)
desc=adapt((base/'module/TianxiangRenqiu/SubModule.xml').read_text()).replace('Tianxiang '+ident,display).replace('v1.0.1','v1.0.0')
(root/f'module/{ident}/SubModule.xml').write_text(desc,encoding='utf-8')
items=adapt((base/'module/TianxiangRenqiu/ModuleData/items.xml').read_text()).replace('纫秋为佩',title)
(root/f'module/{ident}/ModuleData/items.xml').write_text(items,encoding='utf-8')
(root/'.gitignore').write_text('tools/PackagePatch/obj/\ntools/PackagePatch/bin/\nreports/source_rest_*.png\n')
(root/'README.md').write_text(f'''# {display} v1.0.0

“{title}”完整角色装备，独立模组 ID `{ident}`，资源前缀 `{prefix}_`。管理器英文显示，装备名称中文。

三件配套：{title} · 发容（头盔）、{title} · 衣裙与手饰（身体）、{title} · 腿部与绣鞋（靴子）。手套和披肩槽留空。依赖 Native、SandBoxCore、Sandbox。Mod ZIP 顶层可解压至 Modules。

原始输入保存在 input/，原始贴图在 tex/。每套独立测量的物体计划、解剖标记、UV 修正和布料参数在 tools/model_config.json，测量证据在 reports/source_inspection.json。不是物理身高的源坐标按 {cfg['source_coordinate_to_meters']} 比例适配原生 28 骨 human skeleton。固定脸型，不提供原版表情变形。

最终 TPAC 回读验证四级 LOD、量化权重、跨网格皮肤接缝、原生站立/跑步/拉弓/骑乘；贴图所有 mip 从最终包解码。Blend 打包贴图，FBX 重新导入，原始 FBX 和 PNG 哈希不变。预览来自最终 TPAC，透明按阈值裁切。LOD0 有有限布料距离，远处仅蒙皮；未运行游戏布料求解器。腿部代理接触只是诊断，游戏中裙摆、武器握持、体型滑块和骑乘碰撞仍需实测。游戏测试由你完成。

重建：后台 Blender 执行 tools/rig_model.py、tools/export_geometry.py；编译 tools/PackagePatch 到 build/package_patch；Python 执行 tools/build_package.py、tools/verify_release.py；后台 Blender 执行 tools/verify_source.py、tools/render_review.py -- final face；Python 执行 tools/prepare_delivery.py。工作区 tools/install_release.ps1 -Mod {ident} -Version v1.0.0 打包并安装自己的模块。源码包保持 source/ 与 tex/ 相邻；外部工具和原生游戏资源不随源包交付。本地 Git，不上传远程。
''',encoding='utf-8')
print('INDEPENDENT_PIPELINE_READY',ident)
