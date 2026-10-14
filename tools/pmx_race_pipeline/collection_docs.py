"""Maintain the current collection entry from the character configuration."""
import json
from context import SERIES,config
def write():
    rows=json.loads((SERIES/'batch_inventory.json').read_text(encoding='utf8'))['characters']
    table=['| 角色工程 | 种族 ID | 布料范围 |','| --- | --- | --- |','| [艾梅莉埃](EmilieRace/README.md) | `emilie` | 帽后长饰、背后飘带；已验收资源保留 |']
    for row in rows:
        c=config(row['root']);table.append(f"| [{c['display_name']}]({c['id']}/README.md) | `{c['race']}` | {'后部长发' if c['cloth_enabled'] else '普通蒙皮'} |")
    text='''# Genshin Race Collection

22 个原神完整人物固定外观种族的单一可安装合集。模块 ID `GenshinRaceCollection`，启动器英文名 `Genshin Race Collection`。包含已验收的艾梅莉埃与新增 21 个角色；角色源文件、配置和检查仍分别维护。

## 安装与使用

[Mod 包](dist/GenshinRaceCollection_Mod.zip) 解压到游戏 `Modules`，在 Native、SandBoxCore、Sandbox 后启用 **Genshin Race Collection**。启动器只显示一个合集。本机安装在 `D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/GenshinRaceCollection`。

不要同时加载旧独立角色模块；它们与合集注册同样的种族和资源。自动安装先核对合集包与安装文件，随后完整备份并移出旧独立安装，备份在 `build/previous_installed_modules/`。旧交付包、标签、源工程保留。旧存档可能记录 `EmilieRace` 等模块依赖；先备份存档，迁移后的加载兼容性尚待用户验证。

各角色内部种族 ID 不变，测试兵种为 `<资源前缀>_test`，例如 `ganyu_test`、`furina_test`、`emilie_test`。在启用作弊和开发者控制台的测试存档中可执行 `campaign.give_troops ganyu_test 10`。没有替换原版招募或兵种树；兵种拼装器可以选择表中种族及女性，移除头、身体、腿、手套、披风防具，保留武器和坐骑。

## 角色与布料

芙宁娜随机选择 **荒配色**。独立武器和杂物不进入运行资源，原始档案完整保留。13 个新增角色启用有限长发布料，其余 8 个新增角色头发采用普通蒙皮。所有新角色衣裙均为普通蒙皮；艾梅莉埃保留已验收的帽后长饰和背后飘带布料。

'''+ '\n'.join(table)+'''

逐角色选择依据、源 PMX 和忽略项见 [模型方案](hair_decisions.json)。各角色使用自己的资源名、GUID、骨架、碰撞体和布料参数，模型与骨架只做统一单位换算及整体朝向调整，保留源比例、固定脸和 UV。

## 工程与交付

`<Character>Race/` 保存角色原始输入、`source/`、相邻 `tex/`、参数、构建模块和报告。根目录 `module/GenshinRaceCollection/` 保存合并后的运行模块，`build/` 为合集缓存，`dist/` 保存合集 Mod 包和 [完整源文件包](dist/GenshinRaceCollection_Source.zip)。源包包含所有角色与共用 `workspace_tools/`，不包含缓存和旧交付 ZIP；个人本地适配，不上传远程。

在工作区根目录执行：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 tools/pmx_race_pipeline/collection.py build
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 tools/pmx_race_pipeline/collection.py install
```

先完成各角色重建和离线检查，再构建合集。合集构建自动调用逐角色配置的布料诊断，核对资源哈希，合并 skins、action_sets、Monsters、测试兵种和碰撞 XML，检查重复 ID 与组件等价性；TPAC 和界面 DLL 原样复制。依赖与单角色重建见 [共用流程](../../tools/pmx_race_pipeline/README.md)。

## 检查与当前限制

长发布料代理使用独立全透明裁切材质，与可见头发分开。v0.1.1 的[材质修复检查](reports/hair_proxy_visibility_fix.json)核对全部 LOD、原贴图、骨架、布料和映射字节不变，修复前后预览见各角色报告中的 `hair_proxy_before_*`／`hair_proxy_after_*`。v0.1.0 已收到整体良好的反馈；v0.1.1 的头发实机效果待复测。

[合集检查](reports/collection_validation.json)与 [安装一致性](reports/collection_installation.json)分别记录。各新角色已检查最终 TPAC 所有交付 LOD、纹理、UV、权重、原生动作，以及重开的 Blend/FBX；[正面预览](reports/final_front_1.png)、[第二页](reports/final_front_2.png)、[背面预览](reports/final_back_1.png)、[第二页](reports/final_back_2.png)来自最终资源。

映射布料的 CPU 渲染诊断不支持当前代理映射，保留 `incomplete`；直接代理另作近似轨迹检查。[合集诊断索引](reports/collection_cloth_diagnostics.json)链接到各角色的独立报告。近似碰撞、拉伸提示不当作游戏验收。艾梅莉埃保留其原验收记录；新增角色和合集的队伍、百科、物品栏、战场动作、布料与 LOD 尚待用户游戏测试，助手不启动游戏。

固定外观，无捏脸形变、表情动画或手指握持形变。普通蒙皮衣裙在骑乘和大幅动作中可能折叠、穿模，MMD toon 与游戏材质表现不同。使用种族的存档依赖合集模块。

[更新日志](CHANGELOG.md) · [工作区入口](../../README.md)
'''
    (SERIES/'README.md').write_text(text,encoding='utf8')
if __name__=='__main__':write()
