"""Finalize only the checked, cloth-disabled stable release."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];cfg=json.loads((R/'tools/model_config.json').read_text());ident=cfg['id'];prefix=cfg['prefix'];pkg=R/'module'/ident/'AssetPackages'/(prefix+'.tpac');sha=hashlib.sha256(pkg.read_bytes()).hexdigest();report=json.loads((R/'reports/release_validation.json').read_text())
assert not cfg['cloth_enabled'] and report['status']=='pass' and report['final_package_sha256']==sha
for name in ['static_cloth_validation','source_validation','registration_validation','preview_idle_validation','ui_scope_validation']:
 item=json.loads((R/'reports'/(name+'.json')).read_text());assert item['status']=='pass';report[name]=item
report.update(cloth_enabled=False,delivery_mode='skeletal_skinning_only',game_test_verified=False,game_cloth_solver_used=False,limitations=['No dynamic cloth: skirts, hair and ribbons use skeletal skinning only.','Skeletal references may intersect during running, combat and riding; no guarantee of all-pose clearance.','Fixed face/fingers; no customization or original armor layering.'])
(R/'reports/release_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
for name in ['cloth_validation','cloth_collision','skirt_collision_validation','skirt_preservation_validation','skirt_surface_coverage']:
 (R/'reports'/(name+'.json')).write_text(json.dumps(dict(status='not_applicable',version=cfg['version'],reason='Dynamic cloth disabled; see static_cloth_validation.json. Previous dynamic evidence retained in history/v0.1.1.',final_package_sha256=sha),indent=2))
review=json.loads((R/'reports/history/v0.1.0/visual_review.json').read_text());review.update(version=cfg['version'],final_package_sha256=sha,scope='Exact preserved GPU geometry and skeletal previews, now without cloth; original reference images reused, game test pending',dynamic_cloth_enabled=False);review.pop('collision_proxy_review',None);(R/'reports/visual_review.json').write_text(json.dumps(review,indent=2))
preview=json.loads((R/'reports/final_preview_manifest.json').read_text());preview['package_sha256']=sha;preview.pop('collision_proxy_comparison',None);preview['dynamic_cloth_enabled']=False;(R/'reports/final_preview_manifest.json').write_text(json.dumps(preview,indent=2))
text=f"""# {cfg['title']}

仙剑7固定完整角色的独立种族资源模块，版本 **{cfg['version']}**。属于[仙剑7系列](../README.md)。模块 ID：`{ident}`；种族 ID：`{cfg['race']}`。按本机 Native v1.4.8 制作。

## 当前功能与验证

保留原模型脸、身体比例、头发、时装、双手、28 骨自定义骨架、四级 LOD 和材质。**全部动态布料已关闭**，裙子、头发和饰带仅随骨骼运动；运行包无布料求解标记、预处理数据或碰撞体引用，源 Blend/FBX 的布料活动距离为 0。

最终包回读、原生动作扫描、源文件重开与 FBX 重导入通过。GPU 网格、权重、UV、材质、贴图和骨架与保留的外观基线完全一致，检查见[静态版专项报告](reports/static_cloth_validation.json)、[发布检查](reports/release_validation.json)和[源文件检查](reports/source_validation.json)。[预览图索引](reports/final_preview_manifest.json)为骨骼蒙皮结果。游戏效果尚待用户确认。

保留限定本种族的队伍、百科、物品栏人物预览组件。本模块不提供兵种树、原版人物替换或招募入口；使用方自行配置成人女性人物的 `race="{cfg['race']}"`、生成方式与装备。

动作集覆盖及动态命名检查见[系列说明](../README.md#动作集注册与检查)，本角色报告为 `reports/action_sets_validation.json`；注册覆盖不代替各场景游戏验收。

## 安装与使用

将 `dist/{ident}_Mod.zip` 的顶层模块目录解压到游戏 `Modules/`。启动器勾选 **{cfg['title']}**，排在 Native、SandBoxCore、Sandbox 后。固定服装身体不适合叠穿原版防具；含此种族的存档需要保留模块。

## 工程与重建

`input/original/` 保留输入；`source/` 为可编辑 Blend/FBX，`tex/` 与其相邻；`tools/` 保存专用脚本；`module/{ident}/` 为运行模块；`reports/` 保存当前证据，`reports/history/` 保存旧版记录；`build/` 为缓存，`dist/` 为当前与保留交付包。

依赖 Blender 5.2、Anaconda Python（NumPy、SciPy、Pillow）、.NET、mbtool、当前游戏资源及工作区 `tools/asset_helpers/`。重建稳定版使用：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -X utf8 mods/Xianjian7Race/{ident}/tools/rebuild.py
./tools/install_release.ps1 -Mod {ident} -Version {cfg['version']} -CheckOnly
```

重建从 `dist/{ident}_v0.1.0_Mod.zip` 恢复外观基线，必须保留此旧包；源包不重复包含历史交付 ZIP。源包的 `workspace_tools/` 恢复到工作区根 `tools/`。发布前运行 `tools/finalize_release.py`。变更见[更新日志](CHANGELOG.md)。

## 当前限制

关闭动态布料后，没有独立裙摆、发尾和饰带摆动。骨骼运动仍可能造成跑动、战斗、骑乘时的衣片、内衬、腿部或头发交叉；本版不声称消除了所有蒙皮穿模。

固定脸和手指，不提供捏脸、表情、动态手势或换装；源 UE 着色近似转换。游戏测试由用户完成。官方布料编辑器研究与当前稳定版分开，不自动重新启用布料。
"""
(R/'README.md').write_text(text,encoding='utf8')
p=R/'CHANGELOG.md';old=p.read_text(encoding='utf8');section=f"## {cfg['version']} — 2026-10-13\n\n- 关闭裙子、头发及饰带的全部动态布料；移除求解标记、预处理数据和碰撞体引用。\n- 保留外观基线 GPU 网格、权重、材质、贴图、骨架及 UI 组件，源文件活动距离清零。\n- 完成最终包回读、动作扫描和源文件检查；游戏蒙皮效果待确认。\n\n"
if f"## {cfg['version']} " not in old:p.write_text(old.replace('# 更新日志\n','# 更新日志\n\n'+section,1),encoding='utf8')
files=[]
for p in R.rglob('*'):
 if not p.is_file():continue
 rel=p.relative_to(R);parts=rel.parts
 if parts[0] in ['build','dist','module','tex'] or any(x in ['__pycache__','obj','bin'] for x in parts) or p.name.endswith('.blend1') or p.name in ['initialize_projects.py','adapt_projects.py','delivery_validation.json']:continue
 files.append(rel.as_posix())
config=json.loads((R/'mod.json').read_text());config['source_files']=sorted(set(files+['mod.json']));(R/'mod.json').write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf8');print('STATIC_RELEASE_READY',ident)
