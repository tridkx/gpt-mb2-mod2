"""Promote verified Mingyu head/neck candidate; preserve historical releases."""
import json,hashlib,shutil,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];module=ROOT/'module/ShengxiuCollection'
report=json.loads((ROOT/'reports/head_neck_validation.json').read_text());candidate=ROOT/'build/head_neck_candidate_v1.1.6.tpac'
assert report['status']=='pass' and report['head_neck_checks']['all_lods_face_eye_ornament_uniform_transform']
assert report['final_package_sha256']==hashlib.sha256(candidate.read_bytes()).hexdigest()
shutil.copy2(candidate,module/'AssetPackages/sx_mingyu.tpac')
xml=ET.parse(module/'SubModule.xml');xml.find('Version').set('value','v1.1.6');ET.indent(xml,space='  ');xml.write(module/'SubModule.xml',encoding='utf-8',xml_declaration=True)
path=module/'SubModule.xml';path.write_bytes(path.read_bytes().replace(b'\r\n',b'\n'))
shot=Path('C:/Users/DKX/Videos/Captures/Mount and Blade II Bannerlord - Singleplayer.png');shutil.copy2(shot,ROOT/'reports/head_neck_game_feedback_v1.1.5.png')
feedback={'date':'2026-10-09','version':'v1.1.5','user_text':'两个问题。1头发与身体间距太大了。2之前头发盖着我都没发现，原来头往前倾了这么多，脖子是个褶','screenshot':'reports/head_neck_game_feedback_v1.1.5.png','scope':'Excessive posterior hair gap and forward head/neck crease in inventory pose. No new skirt feedback.','assistant_ran_game':False}
(ROOT/'reports/user_feedback_v1.1.5.json').write_text(json.dumps(feedback,ensure_ascii=False,indent=2),encoding='utf-8')
cfg=json.loads((ROOT/'mod.json').read_text());cfg['validation_report']='reports/head_neck_validation.json'
cfg['source_files']=sorted(set(cfg['source_files'])|{'tools/HeadNeckGeometry.cs','tools/HeadNeckGeometry.csproj','tools/fit_head_neck_source.py','tools/prepare_head_neck.py','tools/verify_head_neck.py','tools/render_head_neck.py','tools/finalize_head_neck.py','reports/head_neck_source_fit.json','reports/head_neck_build.json','reports/head_neck_validation.json','reports/head_neck_preview.json','reports/user_feedback_v1.1.5.json','reports/head_neck_game_feedback_v1.1.5.png'}|{f'reports/head_neck_{state}_idle_{view}.png' for state in ['before','after'] for view in ['side','back','neck']})
(ROOT/'mod.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
path=ROOT/'README.md';text=path.read_text(encoding='utf-8');text=text.replace('v1.1.5（明玉后发造型与绑骨测试候选）','v1.1.6（明玉头颈随动与后发间距测试候选）')
start=text.index('明玉 LOD0 包含');end=text.index('\n\n身体 MetaMesh',start)
text=text[:start]+'''明玉 LOD0 包含长发、裙摆和袖纱布料，LOD1 仅袖纱，LOD2/3 使用蒙皮。脸、眼、头饰与发根采用颈骨 85%／头骨 15% 的统一随动，减小本套模型在原生待机中的过度前倾；颈部皮肤在静态 z=1.425–1.515m 之间由上胸骨平滑过渡到相同头部变换，颈口共享顶点的量化权重一致。脸、下颌和眼睛保持相同变换，静态脸形不变。

后发下段相对 v1.1.5 向身体收回 25–45mm：最低发梢留有待机摆动余量，主体收回最多 45mm，收回量在 z=1.26–1.48m 间淡出，避开头颈新随动影响较大的上端；保留原后发下段逐渐随 spine2 的设置。后发活动距离上限为 8mm（量化后约 7.8mm），前发沿用原 Alpha，仍保留布料模拟。更新后的可编辑 Blend/FBX 生成头部和颈部皮肤四级 LOD，并按新几何、权重重新编译长发布料。''' +text[end:]
start=text.index('当前候选检查见');end=text.index('\n\n## 重建与交付',start)
text=text[:start]+'''当前候选检查见 [head_neck_validation.json](reports/head_neck_validation.json)，源文件检查见 [source_validation.json](reports/source_validation.json)。从最终 TPAC 回读全部四级 LOD，检查脸、眼、饰物的统一变换、颈口位置与量化权重、长发布料的位置/骨骼/映射/约束，以及完整待机、跑步、持弓和骑乘周期的后发三角面间距。后发检查的范围与取样方法继承 v1.1.5，具体最小间距和帧数见当前报告。

其余 28 个网格元数据与几何、衣裙袖纱三段布料与编辑器数据、自有碰撞 XML、白凤素问包均保持 v1.1.5 字节。此版改变的是头部与颈部皮肤随动、后发间距；原生骨架和动画不变。相同待机姿态的前后近景见 [原颈部](reports/head_neck_before_idle_neck.png)、[新颈部](reports/head_neck_after_idle_neck.png)、[新后发侧面](reports/head_neck_after_idle_side.png)。这些预览没有运行游戏布料求解器。

用户已确认此前自然下垂与裙子穿腿修复，随后反馈 v1.1.5 后发间距过大、头部前倾和颈部折叠。v1.1.6 尚待游戏确认头颈外观、后发贴背程度与站立/跑步穿模；不同体型、武器、IK、远距离布料和其它套装仍不属于本次离线检查的游戏验收范围。''' +text[end:]
start=text.index('当前 v1.1.6 候选') if '当前 v1.1.6 候选' in text else text.index('当前 v1.1.5 候选');end=text.index('\n\n## 注意事项',start)
text=text[:start]+'''当前 v1.1.6 候选从保留的 v1.1.5 源文件和包增量生成，在工作区根依次运行：

```powershell
& 'D:/Blender Foundation/Blender 5.2/blender.exe' --background --python-exit-code 1 --python mods/ShengxiuCollection/tools/fit_head_neck_source.py
& 'D:/Blender Foundation/Blender 5.2/blender.exe' --background --python-exit-code 1 --python mods/ShengxiuCollection/tools/export_geometry.py
& 'D:/Blender Foundation/Blender 5.2/blender.exe' --background --python-exit-code 1 --python mods/ShengxiuCollection/tools/verify_source.py
dotnet build mods/ShengxiuCollection/tools/HeadNeckGeometry.csproj -o mods/ShengxiuCollection/build/head_neck_geometry
python -X utf8 mods/ShengxiuCollection/tools/prepare_head_neck.py
python -X utf8 mods/ShengxiuCollection/tools/verify_head_neck.py
& 'D:/Blender Foundation/Blender 5.2/blender.exe' --background --python-exit-code 1 --python mods/ShengxiuCollection/tools/render_head_neck.py
python -X utf8 mods/ShengxiuCollection/tools/finalize_head_neck.py
./tools/install_release.ps1 -Mod ShengxiuCollection -Version v1.1.6 -PreviousVersion v1.1.5
```

增量基线缓存为 build/head_neck_baseline_v1.1.5/，包括 TPAC、Blend/FBX、rig_arrays.npz 与 rig_manifest.json；后发的原始部位分类还读取 v1.1.4 缓存。首次重建需从保留的回退包和历史模型流程恢复这些基线。当前构建、验证与渲染入口复用 tools/prepare_hair_shape.py、verify_hair_shape.py、render_hair_fit.py 的流程，并明确覆盖版本、输出目录与本次头颈范围。构建需要既有 build/spec.json、模板和 cloth_probe、cloth_patch；渲染需要 v1.1.5 回读与已解码贴图缓存。

仅移植头部和颈部皮肤的四级流，衣裙与材料不采用完整重建包的数据。实际安装需退出游戏与启动器，旧交付包自动保留。依赖本机 Blender、Python、mbtool、原生资源和工作区 asset_helpers；源 ZIP 保持 source/、tex/ 相邻，并附带 workspace_tools/cloth_compiler/。''' +text[end:]
path.write_text(text,encoding='utf-8')
path=ROOT/'CHANGELOG.md';text=path.read_text(encoding='utf-8')
if '## v1.1.6' in text:text=text[:text.index('## v1.1.6')]+text[text.index('## v1.1.5'):]
pos=text.index('## v1.1.5')
entry='''## v1.1.6 — 2026-10-09 明玉头颈随动与后发间距候选

用户反馈 v1.1.5 后发离身体过远，头部前倾明显、颈部折叠。回读原生待机确认本套头骨姿态随动与颈口权重差异，调整头部全部部件为颈骨 85%／头骨 15%，脸与下颌统一变换；颈部皮肤平滑连接上胸骨与相同头部变换，各级颈口共享权重一致，静态脸形不变。

后发下段相对 v1.1.5 向身体收回最多 45mm，上端保留间距以配合新的颈骨随动，后发活动距离限制 8mm，布料保留。重新生成头部与颈部皮肤四级 LOD 和长发布料，其余 28 个网格、衣裙袖纱布料、碰撞 XML 和另外两套包不变。报告见 reports/head_neck_validation.json，同姿态头颈近景及侧后方预览见 reports/head_neck_preview.json。

完整原生周期和最终包离线检查通过，实际头颈外观、头发贴背与动态穿模仍待用户游戏测试。保留 v1.1.5 回退包，仅安装本合集，助手不启动游戏。

'''
path.write_text(text[:pos]+entry+text[pos:],encoding='utf-8')
print('HEAD_NECK_RELEASE_READY v1.1.6')
