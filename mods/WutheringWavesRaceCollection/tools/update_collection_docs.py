"""Keep the one-module collection documentation coherent across source projects."""
from pathlib import Path
import json
S=Path(__file__).resolve().parents[1]
def main():
 rows=json.loads((S/'batch_inventory.json').read_text(encoding='utf8'))['characters']
 for row in rows:
  root=S/row['id'];p=root/'README.md';text=p.read_text(encoding='utf8');ident=root.name
  text=text.replace('独立工程与可单独启用的游戏模块。版本','保留独立源工程，运行资源由上级合集统一加载。角色资源版本')
  if ident=='ShorekeeperRace':text=text.replace('角色资源版本 `v0.1.0`','角色资源版本 `v0.1.1`')
  start=text.index('从[鸣潮合集]');end=text.index('角色带完整',start)
  text=text[:start]+f'随[鸣潮合集](../README.md)安装，在启动器只启用 `Wuthering Waves Race Collection`。`module/{ident}/` 为独立构建资源，不与合集同时启用，避免重复注册。'+text[end:]
  text=text.replace('使用本种族的存档依赖本模块。','使用本种族的存档依赖合集模块。')
  text=text.replace(f'`module/{ident}/` 可安装模块',f'`module/{ident}/` 独立构建资源')
  if ident=='ShorekeeperRace':
   text=text.replace('## 验证与限制','## 验证与限制\n\n[创建页面手臂检查](reports/creation_arm_validation.json)覆盖最终网格的手臂骨骼权重和创建待机；当前版本恢复材质 0 内手臂的正常蒙皮，创建页面实机复测待用户完成。')
  p.write_text(text,encoding='utf8')
  acceptance=root/'reports/game_acceptance.json';old=json.loads(acceptance.read_text())
  if ident=='ShorekeeperRace':
   old.update(version='v0.1.1',status='pending_user_creation_arm_retest',previous_version_feedback={'version':'v0.1.0','feedback':'基本没问题；创建页面守岸人 A pose，其余角色手臂自然下垂','scope':'User overall feedback; does not certify every action or LOD'})
  else:old.update(status='user_basic_feedback_received',feedback='用户表示基本没问题，创建页面手臂自然下垂；未逐动作或 LOD 验收',tested_version='v0.1.0')
  old['collection_loading_retest']='pending';acceptance.write_text(json.dumps(old,ensure_ascii=False,indent=2),encoding='utf8')
 p=S/'README.md';text=p.read_text(encoding='utf8').replace('版本 `v0.1.0`','版本 `v0.1.1`').replace('_v0.1.0_Mod.zip','_v0.1.1_Mod.zip').replace('_v0.1.0_Source.zip','_v0.1.1_Source.zip')
 text=text.replace('每个角色有独立工程、独立模块、源文件、参数与交付目录；合集仅用于统一管理 ZIP，不新增合并游戏模块。','每个角色保留独立源工程、源文件、参数和构建资源；游戏内统一为一个 `WutheringWavesRaceCollection` 模块，启动器英文名为 `Wuthering Waves Race Collection`。')
 a=text.index('[模组合集 ZIP]');b=text.index('\n\n| 角色',a)
 text=text[:a]+'[模组合集 ZIP](dist/WutheringWavesRaceCollection_v0.1.1_Mod.zip) 顶层只有 `WutheringWavesRaceCollection/`，解压到游戏 `Modules/`，在启动器只启用 **Wuthering Waves Race Collection**。八个种族、测试兵种、TPAC 和界面组件由该模块统一加载。安装入口会完整备份原来的八个独立模块并移出游戏 `Modules/`，避免与合集重复注册；角色源工程继续保留。助手不启动游戏。'+text[b:]
 text=text.replace('| 启动器英文名 |','| 角色资源名称 |').replace('含这些种族的存档依赖对应模块。','含这些种族的存档依赖合集模块。原八模块存档迁移仍需实际读档确认。')
 text=text.replace('`module/<ModId>/` 是实际模块','`module/<ModId>/` 是角色独立构建资源；系列 `module/WutheringWavesRaceCollection/` 是唯一可安装模块')
 a=text.index('系列工具 `bootstrap.py`');b=text.index('\n\n## 检查',a)
 text=text[:a]+'''系列工具 `bootstrap.py` 保留原始输入，`configure.py` 保存八角色参数；已建立工程直接使用角色重建入口，不重复覆盖参数。`build_sources.py` 在后台 Blender 内执行，`build_resources.py` 构建独立 TPAC，`render.py` 从最终包生成各级预览。修改角色后先完成该角色的最终检查，再运行合集入口：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/WutheringWavesRaceCollection/tools/collection.py build
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/WutheringWavesRaceCollection/tools/collection.py install
```

`build` 合并 XML、检查 ID／GUID 和动作集、核对角色 TPAC／DLL 并运行各角色布料诊断；`install` 调用共用打包安装入口，核对 ZIP／工程／安装字节，备份并移出旧独立模块。保留旧版 ZIP 和标签。打包和安装需要 PowerShell 7，入口使用 `pwsh`。''' +text[b:]
 text=text.replace('游戏测试由用户完成，队伍／百科／物品栏预览、主要战场动作、握持、骑乘与远近布料效果仍待实机确认；助手未启动游戏。','用户对 v0.1.0 给出基本正常的反馈，并指出创建页面守岸人手臂展开。当前资源已通过手臂权重及整段创建待机离线检查，守岸人创建页面和单模块合集加载仍待用户复测；未逐项确认的战场动作、握持、骑乘和远近布料继续按各报告范围验收，助手未启动游戏。')
 p.write_text(text,encoding='utf8')
 (S/'reports/game_acceptance.json').write_text(json.dumps({'version':'v0.1.1','status':'pending_user_collection_and_shorekeeper_creation_retest','game_launched_by_assistant':False,'previous_feedback':{'version':'v0.1.0','layout':'8 independent modules','text':'基本没问题，只有守岸人在创建页面 A pose，其余手臂自然下垂','scope':'Basic overall feedback; no blanket certification of all actions/LODs'},'required_retests':['single_collection_module_loading','shorekeeper_character_creation_initial_and_rebuild','old_save_module_migration']},ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':main()
