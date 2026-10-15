# Genshin Race Collection

22 个原神完整人物固定外观种族的单一可安装合集。模块 ID `GenshinRaceCollection`，启动器英文名 `Genshin Race Collection`。包含已验收的艾梅莉埃与新增 21 个角色；角色源文件、配置和检查仍分别维护。

## 安装与使用

[Mod 包](dist/GenshinRaceCollection_Mod.zip) 解压到游戏 `Modules`，在 Native、SandBoxCore、Sandbox 后启用 **Genshin Race Collection**。启动器只显示一个合集。本机安装在 `D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/GenshinRaceCollection`。

不要同时加载旧独立角色模块；它们与合集注册同样的种族和资源。自动安装先核对合集包与安装文件，随后完整备份并移出旧独立安装，备份在 `build/previous_installed_modules/`。旧交付包、标签、源工程保留。旧存档可能记录 `EmilieRace` 等模块依赖；先备份存档，迁移后的加载兼容性尚待用户验证。

各角色内部种族 ID 不变，测试兵种为 `<资源前缀>_test`，例如 `ganyu_test`、`furina_test`、`emilie_test`。在启用作弊和开发者控制台的测试存档中可执行 `campaign.give_troops ganyu_test 10`。没有替换原版招募或兵种树；兵种拼装器可以选择表中种族及女性，移除头、身体、腿、手套、披风防具，保留武器和坐骑。

## 角色与布料

芙宁娜随机选择 **荒配色**。独立武器和杂物不进入运行资源，原始档案完整保留。13 个新增角色启用有限长发布料，其余 8 个新增角色头发采用普通蒙皮。所有新角色衣裙均为普通蒙皮；艾梅莉埃保留已验收的帽后长饰和背后飘带布料。

| 角色工程 | 种族 ID | 布料范围 |
| --- | --- | --- |
| [艾梅莉埃](EmilieRace/README.md) | `emilie` | 帽后长饰、背后飘带；已验收资源保留 |
| [甘雨](GanyuRace/README.md) | `ganyu` | 后部长发 |
| [丽莎·叶隐芳名](LisaLeafShadeRace/README.md) | `lisa_leafshade` | 普通蒙皮 |
| [神里绫华·花时来信](AyakaSpringBloomRace/README.md) | `ayaka_springbloom` | 普通蒙皮 |
| [荧](LumineRace/README.md) | `lumine` | 普通蒙皮 |
| [凝光·纱中幽兰](NingguangOrchidRace/README.md) | `ningguang_orchid` | 后部长发 |
| [云堇](YunJinRace/README.md) | `yunjin` | 后部长发 |
| [砂糖](SucroseRace/README.md) | `sucrose` | 普通蒙皮 |
| [珊瑚宫心海](KokomiRace/README.md) | `kokomi` | 后部长发 |
| [芙宁娜](FurinaRace/README.md) | `furina` | 普通蒙皮 |
| [闲云](XianyunRace/README.md) | `xianyun` | 后部长发 |
| [丽莎](LisaRace/README.md) | `lisa` | 普通蒙皮 |
| [妮露](NilouRace/README.md) | `nilou` | 后部长发 |
| [安柏](AmberRace/README.md) | `amber` | 后部长发 |
| [刻晴·霓裾翩跹](KeqingOpulentRace/README.md) | `keqing_opulent` | 后部长发 |
| [八重神子](YaeMikoRace/README.md) | `yaemiko` | 后部长发 |
| [琴·时装](JeanSeaBreezeRace/README.md) | `jean_seabreeze` | 普通蒙皮 |
| [神里绫华](AyakaRace/README.md) | `ayaka` | 后部长发 |
| [胡桃·海灯节](HuTaoLanternRace/README.md) | `hutao_lantern` | 后部长发 |
| [胡桃](HuTaoRace/README.md) | `hutao` | 后部长发 |
| [薇斯纳](WeisinaRace/README.md) | `weisina` | 后部长发 |
| [诺艾尔](NoelleRace/README.md) | `noelle` | 普通蒙皮 |

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

当前版本 v0.1.3 的 13 个长发角色直接模拟可见头发，每级保留自身直接布料数据，最终资源没有头发模拟代理、代理引用或映射段。发型、UV、材质和蒙皮保持不变，详见 [直接布料检查](reports/direct_hair_cloth.json)。默认丽莎、安柏和诺艾尔的表情贴图使用合法 BC 尺寸，原 PNG 和 UV 保留；[D3D11 对照](reports/d3d11_bc_resource_test.json)记录资源创建结果。用户已确认默认丽莎、安柏可以加载；v0.1.3 的头发色块修复已获用户实测确认，详见 [游戏验收记录](reports/game_acceptance.json)。

[合集检查](reports/collection_validation.json)与 [安装一致性](reports/collection_installation.json)分别记录。各新角色已检查最终 TPAC 所有交付 LOD、纹理、UV、权重、原生动作，以及重开的 Blend/FBX；[正面预览](reports/final_front_1.png)、[第二页](reports/final_front_2.png)、[背面预览](reports/final_back_1.png)、[第二页](reports/final_back_2.png)对应保留不变的最终可见网格和贴图，属于静态／普通蒙皮预览，不展示本次直接布料形变。

直接布料由 CPU 近似求解器检查动作轨迹和碰撞；数值相同的四级 LOD 依据预处理数据等价性选取代表级。[合集诊断索引](reports/collection_cloth_diagnostics.json)链接到各角色的独立报告。近似碰撞、拉伸提示不当作游戏验收。艾梅莉埃保留其原验收记录；头发色块修复已通过用户实测；新增角色和合集的队伍、百科、物品栏、战场动作及完整布料／LOD 覆盖仍按各自验收记录核对，助手不启动游戏。

固定外观，无捏脸形变、表情动画或手指握持形变。普通蒙皮衣裙在骑乘和大幅动作中可能折叠、穿模，MMD toon 与游戏材质表现不同。使用种族的存档依赖合集模块。

[更新日志](CHANGELOG.md) · [工作区入口](../../README.md)
