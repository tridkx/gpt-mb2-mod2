"""Promote verified natural-drape candidate and refresh current documentation."""
import json,hashlib,shutil,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];module=ROOT/'module/ShengxiuCollection'
candidate=ROOT/'build/back_hair_candidate_v1.1.7.tpac'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=json.loads((ROOT/'reports/back_hair_validation.json').read_text())
physics=json.loads((ROOT/'reports/free_hair_diagnostic.json').read_text())
assert report['status']==physics['status']=='pass'
assert report['final_package_sha256']==physics['final_package_sha256']==sha(candidate)
assert report['source_non_hair_arrays_identical_to_v1_1_6'] and report['accepted_leg_collision_body_unchanged']
assert json.loads((ROOT/'reports/source_validation.json').read_text())['status']=='pass'
report['gravity_diagnostic']='reports/free_hair_diagnostic.json'
report['gravity_diagnostic_scope']=physics['scope']
(ROOT/'reports/back_hair_validation.json').write_text(json.dumps(report,indent=2))
shutil.copy2(candidate,module/'AssetPackages/sx_mingyu.tpac')
xml=ET.parse(module/'SubModule.xml');xml.find('Version').set('value','v1.1.7');ET.indent(xml,space='  ')
xml.write(module/'SubModule.xml',encoding='utf-8',xml_declaration=True)
path=module/'SubModule.xml';path.write_bytes(path.read_bytes().replace(b'\r\n',b'\n'))
feedback={'date':'2026-10-09','version':'v1.1.6','user_text':'头发离身体还是太远了；希望保留布料模拟，让头发自然下垂。轻微穿模可以接受，不影响观感即可，不必追求完美。查看 v1.1.7 候选的离线预览后要求后颈向外折处更平滑。','scope':'Rear hair spacing and natural drape; nape smoothing requested from offline candidate preview, not game test. Skirt previously accepted. No new confirmation of head/neck or full animation coverage.','assistant_ran_game':False}
(ROOT/'reports/user_feedback_v1.1.6.json').write_text(json.dumps(feedback,ensure_ascii=False,indent=2),encoding='utf-8')
new_files={'tools/BackHairGeometry.cs','tools/BackHairGeometry.csproj','tools/fit_back_hair_source.py','tools/fit_free_hair_collision.py','tools/prepare_back_hair.py','tools/verify_back_hair.py','tools/diagnose_free_hair.py','tools/render_back_hair.py','tools/finalize_back_hair.py','reports/back_hair_source_fit.json','reports/free_hair_collision_fit.json','reports/back_hair_build.json','reports/back_hair_validation.json','reports/free_hair_diagnostic.json','reports/back_hair_preview.json','reports/user_feedback_v1.1.6.json'}
new_files|={f'reports/back_hair_{state}_idle_{view}.png' for state in ['before','after','gravity'] for view in ['side','back']}
cfg=json.loads((ROOT/'mod.json').read_text());cfg['validation_report']='reports/back_hair_validation.json'
cfg['source_files']=sorted(set(cfg['source_files'])|new_files)
(ROOT/'mod.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
path=ROOT/'README.md';text=path.read_text(encoding='utf-8')
text=text.replace('v1.1.6（明玉头颈随动与后发间距测试候选）','v1.1.7（明玉长发自然下垂测试候选）')
start=text.index('后发下段相对') if '后发下段相对' in text else text.index('后发基础造型')
end=text.index('\n\n白凤、素问按',start)
text=text[:start]+'''后发基础造型按衣服背面平滑收拢，主体参考间距约 24mm，保留发束的前后层次；后颈隆起局部收回最多 45mm，在 z=1.32–1.59m 内平滑淡入淡出，固定头皮和下段主体不受此局部调整影响。下段蒙皮参考按高度平滑跟随对应躯干部位。布料的蒙皮位置仅作为活动范围中心，实际长发可在重力、约束和碰撞下离开该位置。后发活动距离从固定头皮逐渐增加，发尾最大 200mm；前侧发束保留原活动距离，原头皮零距离固定点不变。弯曲刚度为 0.18，重力为 7，拉伸与锚点刚度保持 1，阻尼保持 0.48。LOD0 按新几何、权重和 Alpha 重新编译长发布料，LOD1–3 仍为蒙皮。

头部引用自有 sx_mingyu_back_collision：28 个重叠胶囊覆盖后腰到上背，端点按模型对应高度的躯干权重随动；靠近上端逐渐缩小半径，避免挤压前侧发束和发根。碰撞表面按衣服背面拟合，轻微局部交叉以不影响整体观感为准，不以继续外移整片头发作为消除穿模的手段。

身体 MetaMesh 引用已获裙子修复反馈的 sx_mingyu_leg_collision，四个腿部胶囊、身体引用和衣裙袖纱布料保持原设置。白凤、素问资源包保持 v1.1.0 字节，在 LOD0/1 包含自有布料预处理数据，LOD2/3 使用蒙皮。''' +text[end:]
start=text.index('当前候选检查见');end=text.index('\n\n## 重建与交付',start)
text=text[:start]+'''当前候选检查见 [back_hair_validation.json](reports/back_hair_validation.json)，源文件检查见 [source_validation.json](reports/source_validation.json)。最终 TPAC 回读覆盖全部四级 LOD、完整待机/跑步/持弓/骑乘周期中的后发蒙皮参考间距，以及长发布料位置、量化权重、映射、固定点和并行约束。其余 52 个网格的元数据与几何、衣裙袖纱三段布料及编辑器数据保持 v1.1.6 字节；头颈、脸、眼、饰物、原生骨架和动画不变，裙子腿部碰撞体不变。

[free_hair_diagnostic.json](reports/free_hair_diagnostic.json) 另记录七个静态原生姿态的近似 CPU 重力与胶囊约束诊断：每个姿态以 120Hz 松弛 3 秒，核对发根不漂移、活动距离与碰撞的冲突、后发下落和局部穿模。它没有运行游戏求解器或连续动画惯性，不能代替游戏测试。模型参考前后侧面见 [原后发](reports/back_hair_before_idle_side.png)、[新参考造型](reports/back_hair_after_idle_side.png)；近似重力诊断图见 [侧面](reports/back_hair_gravity_idle_side.png)、[背面](reports/back_hair_gravity_idle_back.png)。

用户已确认此前裙子修复，并要求优先自然下垂和整体观感，接受轻微局部穿模。当前长发候选尚待游戏确认贴背程度、待机/跑动摆动和明显穿模；不同体型、武器、IK、远距离布料和其它套装不属于本次离线诊断的游戏验收范围。助手未启动游戏。''' +text[end:]
start=text.index('当前 v1.1.6 候选') if '当前 v1.1.6 候选' in text else text.index('当前 v1.1.7 候选')
end=text.index('\n\n## 注意事项',start)
text=text[:start]+'''当前 v1.1.7 候选从保留的 v1.1.6 源文件和包增量生成，在工作区根依次运行：

```powershell
& 'D:/Blender Foundation/Blender 5.2/blender.exe' --background --python-exit-code 1 --python mods/ShengxiuCollection/tools/fit_back_hair_source.py
python -X utf8 mods/ShengxiuCollection/tools/fit_free_hair_collision.py
& 'D:/Blender Foundation/Blender 5.2/blender.exe' --background --python-exit-code 1 --python mods/ShengxiuCollection/tools/export_geometry.py
& 'D:/Blender Foundation/Blender 5.2/blender.exe' --background --python-exit-code 1 --python mods/ShengxiuCollection/tools/verify_source.py
dotnet build mods/ShengxiuCollection/tools/BackHairGeometry.csproj -o mods/ShengxiuCollection/build/back_hair_geometry
python -X utf8 mods/ShengxiuCollection/tools/prepare_back_hair.py
python -X utf8 mods/ShengxiuCollection/tools/verify_back_hair.py
python -X utf8 mods/ShengxiuCollection/tools/diagnose_free_hair.py
& 'D:/Blender Foundation/Blender 5.2/blender.exe' --background --python-exit-code 1 --python mods/ShengxiuCollection/tools/render_back_hair.py
python -X utf8 mods/ShengxiuCollection/tools/finalize_back_hair.py
./tools/install_release.ps1 -Mod ShengxiuCollection -Version v1.1.7 -PreviousVersion v1.1.6
```

增量基线缓存为 build/back_hair_baseline_v1.1.6/，包括 TPAC、Blend/FBX、rig_arrays.npz、rig_manifest.json 和 cloth_bodies.xml；后发布位分类读取 v1.1.4 原始坐标缓存，衣服拟合读取 v1.1.6 最终回读几何。首次重建需从保留的回退包和历史模型流程恢复这些基线。构建需要既有 build/spec.json、模板及 cloth_probe、cloth_patch；入口复用 prepare_hair_shape.py、verify_hair_shape.py、render_hair_fit.py，并覆盖版本、输出目录和检查范围。预览需要已解码的贴图缓存。

仅移植长发四级流，并修改 LOD0 长发弯曲参数和自有背部碰撞 XML。实际安装需退出游戏与启动器，旧交付包自动保留。依赖本机 Blender、Python、mbtool、原生资源和工作区 asset_helpers；源 ZIP 保持 source/、tex/ 相邻，并附带 workspace_tools/cloth_compiler/。''' +text[end:]
path.write_text(text,encoding='utf-8')
path=ROOT/'CHANGELOG.md';text=path.read_text(encoding='utf-8');pos=text.index('## v1.1.6')
entry='''## v1.1.7 — 2026-10-09 明玉长发自然下垂候选

用户反馈后发仍离身体过远，并要求保留布料、自然下垂，以整体观感为准接受轻微穿模；查看近似重力预览后补充后颈向外折、需要平滑。此前 8mm 活动上限让重力无法明显改变后发形状。本版按衣服背面平滑收拢基础造型，后颈隆起在 z=1.32–1.59m 内平滑收回最多 45mm，下段参考权重按躯干高度过渡，头皮零距离固定点保持不变，后发活动范围向发尾逐渐放宽至 200mm；弯曲刚度改为 0.18，其余重力、阻尼和拉伸锚点设置保持原值。重新生成四级长发流和 LOD0 布料。

后背碰撞改为 28 个重叠且上端缩小的自有胶囊，覆盖后腰至上背，四个腿部胶囊及衣裙袖纱数据不变，头颈和另外两套包不变。最终包、源文件和完整原生蒙皮周期检查见 reports/back_hair_validation.json；近似 CPU 重力诊断见 reports/free_hair_diagnostic.json，同姿态参考与近似重力预览见 reports/back_hair_preview.json。CPU 检查不等同于游戏布料验收；长发实际观感与摆动待用户游戏测试。保留 v1.1.6 回退包，仅安装本合集，助手不启动游戏。

'''
if '## v1.1.7' not in text:path.write_text(text[:pos]+entry+text[pos:],encoding='utf-8')
print('BACK_HAIR_RELEASE_READY v1.1.7',sha(candidate))
