"""Promote a verified hair candidate and synchronize release documentation."""
import json,shutil,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];module=ROOT/'module/ShengxiuCollection'
report=json.loads((ROOT/'reports/hair_shape_validation.json').read_text());candidate=ROOT/'build/hair_shape_candidate_v1.1.5.tpac'
assert report['status']=='pass' and report['final_package_sha256']==hashlib.sha256(candidate.read_bytes()).hexdigest()
assert len([r for r in report['motions'] if r['lod']==0 and r['animation']=='idle'])>16
shutil.copy2(candidate,module/'AssetPackages/sx_mingyu.tpac')
descriptor=ET.parse(module/'SubModule.xml');descriptor.find('Version').set('value','v1.1.5');ET.indent(descriptor,space='  ');descriptor.write(module/'SubModule.xml',encoding='utf-8',xml_declaration=True)
path=module/'SubModule.xml';path.write_bytes(path.read_bytes().replace(b'\r\n',b'\n'))
shot=Path('C:/Users/DKX/Videos/Captures/Mount and Blade II Bannerlord2 .png')
if shot.exists():shutil.copy2(shot,ROOT/'reports/hair_game_feedback_v1.1.4.png')
feedback=json.loads((ROOT/'reports/user_feedback_v1.1.4.json').read_text());feedback['additional_user_text']='哪怕是待机站立姿态也会穿模。整个后方的头发穿进衣服里'
feedback['screenshot']='reports/hair_game_feedback_v1.1.4.png';feedback['interpretation']='User confirms whole rear sheet clips at inventory idle. Final baseline skeletal preview reproduces this; rest shape and head-only weights both permit garment intersections. Game cloth collision behavior is still not established.'
feedback['next_evidence']='v1.1.5 reshapes rear hair, blends lower weights toward spine2 and preserves cloth; user must verify standing and running in game.'
(ROOT/'reports/user_feedback_v1.1.4.json').write_text(json.dumps(feedback,ensure_ascii=False,indent=2),encoding='utf-8')
cfg=json.loads((ROOT/'mod.json').read_text());cfg['validation_report']='reports/hair_shape_validation.json'
cfg['source_files']=sorted(set(cfg['source_files'])|{'tools/HairGeometry.cs','tools/HairGeometry.csproj','tools/fit_hair_source.py','tools/hair_shape_analysis.py','tools/prepare_hair_shape.py','tools/verify_hair_shape.py','tools/render_hair_fit.py','tools/finalize_hair_shape.py','reports/hair_source_fit.json','reports/hair_shape_diagnosis.json','reports/hair_shape_build.json','reports/hair_shape_validation.json','reports/hair_shape_preview.json','reports/user_feedback_v1.1.4.json','reports/hair_game_feedback_v1.1.4.png'}|{f'reports/hair_{state}_idle_{view}.png' for state in ['before','after'] for view in ['side','back']})
(ROOT/'mod.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
readme=(ROOT/'README.md').read_text(encoding='utf-8')
readme=readme.replace('# Shengxiu Collection v1.1.4（明玉长发活动距离测试候选）','# Shengxiu Collection v1.1.5（明玉后发造型与绑骨测试候选）')
start=readme.index('明玉 LOD0 包含');end=readme.index('\n\n身体 MetaMesh',start)
readme=readme[:start]+'''明玉 LOD0 包含长发、裙摆和袖纱布料，LOD1 仅袖纱，LOD2/3 使用蒙皮。后发按本套衣服背面重新留出间距，变形只沿后颈到下段平滑展开；头顶发根、脸、眼睛、头饰与正前方发束保持原样。后发下段的上身权重逐渐增加至 spine2 98%，上端仍随头部，避免整片长发随头骨前倾而切入后背。后发活动距离上限为 12mm（量化后约 11.8mm），保留布料；前发沿用原 Alpha。四级长发 LOD 与 LOD0 预处理数据均由更新后的可编辑 Blend/FBX 生成。''' +readme[end:]
start=readme.index('当前候选检查见');end=readme.index('\n\n## 重建与交付',start)
readme=readme[:start]+'''当前候选检查见 [hair_shape_validation.json](reports/hair_shape_validation.json)，造型参数和源文件检查见 [hair_source_fit.json](reports/hair_source_fit.json)、[source_validation.json](reports/source_validation.json)。从最终 TPAC 回读全部四级 LOD，核对长发布料的位置、骨骼、映射、约束和并行分组；其余 52 个网格元数据与几何、衣裙袖纱的预处理和编辑器数据、碰撞 XML 保持 v1.1.4 字节。白凤、素问包哈希不变。v1.1.0 的完整基线检查另见 [collection_release_validation.json](reports/collection_release_validation.json)，不作为当前包哈希依据。

对原生待机、跑步、持弓与骑乘从第 1 帧起的完整周期，检查后发顶点、面片中心和边中点与实际躯干三角面。检查限定原始后发 Y<-25mm、Z<1.50m；在上胸骨动画局部坐标沿前后方向投射，排除袖纱外侧与低处裙摆。各级 LOD 的具体最小间距和帧数见候选报告。这项检查证明所查蒙皮姿态与躯干的间距，不能代替游戏布料求解、不同体型、武器碰撞或 IK。源包中保留旧版原生姿态报告作为历史参考。

用户确认自然下垂和裙子穿腿问题已修复，但 v1.1.4 整片后发在待机站立时仍穿衣。相同姿态的最终包预览复现了旧版后发进入背部，新候选后发位于衣服外侧，见 [修复前侧面](reports/hair_before_idle_side.png)、[修复后侧面](reports/hair_after_idle_side.png)、[修复后背面](reports/hair_after_idle_back.png)。预览未运行游戏布料求解器。v1.1.5 尚待用户确认站立、跑步的后发位置与自然摆动；白凤、素问和明玉远距离布料仍待游戏验收。''' +readme[end:]
start=readme.index('当前 v1.1.5 候选') if '当前 v1.1.5 候选' in readme else readme.index('当前 v1.1.4 候选');end=readme.index('\n\n## 注意事项',start)
readme=readme[:start]+'''当前 v1.1.5 候选从保留的 v1.1.4 源文件和包增量生成，在工作区根依次运行：

```powershell
& 'D:/Blender Foundation/Blender 5.2/blender.exe' --background --python-exit-code 1 --python mods/ShengxiuCollection/tools/fit_hair_source.py
& 'D:/Blender Foundation/Blender 5.2/blender.exe' --background --python-exit-code 1 --python mods/ShengxiuCollection/tools/export_geometry.py
& 'D:/Blender Foundation/Blender 5.2/blender.exe' --background --python-exit-code 1 --python mods/ShengxiuCollection/tools/verify_source.py
dotnet build mods/ShengxiuCollection/tools/HairGeometry.csproj -o mods/ShengxiuCollection/build/hair_geometry
python -X utf8 mods/ShengxiuCollection/tools/prepare_hair_shape.py
python -X utf8 mods/ShengxiuCollection/tools/verify_hair_shape.py
& 'D:/Blender Foundation/Blender 5.2/blender.exe' --background --python-exit-code 1 --python mods/ShengxiuCollection/tools/render_hair_fit.py
python -X utf8 mods/ShengxiuCollection/tools/finalize_hair_shape.py
./tools/install_release.ps1 -Mod ShengxiuCollection -Version v1.1.5 -PreviousVersion v1.1.4
```

增量基线缓存为 build/hair_shape_baseline_v1.1.4/，包括 TPAC、Blend/FBX、rig_arrays.npz 和 rig_manifest.json；脚本核对旧包哈希。首次重建需从 v1.1.4 Mod/Source 回退包和旧版模型流程恢复这些基线。prepare_hair_shape.py 使用既有 build/spec.json、本机模板和编译好的 cloth_probe、cloth_patch；完整基线流程见历史更新日志。候选只移植重新生成的四个长发流并编译长发，不采用完整重建包的衣裙或材料数据。render_hair_fit.py 使用保留的旧版 final_export/geo、贴图解码缓存和新候选回读数据做相同视角对比。

实际安装需退出游戏与启动器，旧交付包自动保留。依赖本机 Blender、Python、mbtool、原生资源和工作区 asset_helpers；源 ZIP 保持 source/、tex/ 相邻，并附带 workspace_tools/cloth_compiler/。''' +readme[end:]
(ROOT/'README.md').write_text(readme,encoding='utf-8')
path=ROOT/'CHANGELOG.md';text=path.read_text(encoding='utf-8')
if '## v1.1.5' in text:text=text[:text.index('## v1.1.5')]+text[text.index('## v1.1.4'):]
where=text.index('## v1.1.4')
entry='''## v1.1.5 — 2026-10-09 明玉后发造型与绑骨候选

用户补充：整片后发在待机站立时进入衣服，并提供库存侧后方截图。旧包的原生待机蒙皮预览复现穿背；原造型后发下段已有静态交叉，所有长发仅绑定头骨，头颈姿态进一步将后发带入躯干。此前仅改变碰撞与活动距离未解决反馈。

沿后颈至下段重新调整后发前后位置，上端保留发根；下段平滑增加 spine2 权重至 98%，后发活动距离限制 12mm，保留布料。更新 Blend/FBX、四级长发 LOD，并按新几何/权重重新编译 LOD0 长发布料。最终包回读确认其余 52 个网格、衣裙袖纱布料与编辑器数据、自有碰撞 XML、白凤素问包均不变。报告见 reports/hair_shape_validation.json；相同待机姿态的侧后方前后预览见 reports/hair_shape_preview.json。

四级 LOD 检查待机、跑步、持弓、骑乘完整原生周期中的后发顶点、面片中心和边中点。通过的是离线蒙皮与躯干三角面间距检查；游戏布料、体型与武器行为尚待用户测试。自动安装本合集、保留 v1.1.4 回退包，助手未运行游戏。

'''
path.write_text(text[:where]+entry+text[where:],encoding='utf-8')
print('HAIR_SHAPE_RELEASE_READY v1.1.5')
