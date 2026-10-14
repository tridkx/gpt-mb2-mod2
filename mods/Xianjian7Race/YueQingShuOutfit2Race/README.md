# Yue Qing Shu Outfit 2 Race

仙剑7固定完整角色的独立种族资源模块，版本 **v0.1.3**。属于[仙剑7系列](../README.md)。模块 ID：`YueQingShuOutfit2Race`；种族 ID：`yqs2_outfit2`。按本机 Native v1.4.8 制作。

## 当前功能与验证

保留原模型脸、身体比例、头发、时装、双手、28 骨自定义骨架、四级 LOD 和材质。**全部动态布料已关闭**，裙子、头发和饰带仅随骨骼运动；运行包无布料求解标记、预处理数据或碰撞体引用，源 Blend/FBX 的布料活动距离为 0。

最终包回读、原生动作扫描、源文件重开与 FBX 重导入通过。GPU 网格、权重、UV、材质、贴图和骨架与保留的外观基线完全一致，检查见[静态版专项报告](reports/static_cloth_validation.json)、[发布检查](reports/release_validation.json)和[源文件检查](reports/source_validation.json)。[预览图索引](reports/final_preview_manifest.json)为骨骼蒙皮结果。游戏效果尚待用户确认。

保留限定本种族的队伍、百科、物品栏人物预览组件。本模块不提供兵种树、原版人物替换或招募入口；使用方自行配置成人女性人物的 `race="yqs2_outfit2"`、生成方式与装备。

场景动作集按当前 Native 目录覆盖地图、举旗、野外对话、领主、酒馆及条件 NPC；完整名称与 Monster ID 匹配，保留六个旧短名和人物预览待机，共 95 项。名称、继承及资源保留证据见[动作集检查](reports/action_sets_validation.json)和[修复保留检查](reports/action_set_fix_validation.json)，生成与检查方法见[系列说明](../README.md#动作集注册与检查)。新增场景姿态与地图明暗频闪仍待游戏验证。

## 安装与使用

将 `dist/YueQingShuOutfit2Race_Mod.zip` 的顶层模块目录解压到游戏 `Modules/`。启动器勾选 **Yue Qing Shu Outfit 2 Race**，排在 Native、SandBoxCore、Sandbox 后。固定服装身体不适合叠穿原版防具；含此种族的存档需要保留模块。

## 工程与重建

`input/original/` 保留输入；`source/` 为可编辑 Blend/FBX，`tex/` 与其相邻；`tools/` 保存专用脚本；`module/YueQingShuOutfit2Race/` 为运行模块；`reports/` 保存当前证据，`reports/history/` 保存旧版记录；`build/` 为缓存，`dist/` 为当前与保留交付包。

依赖 Blender 5.2、Anaconda Python（NumPy、SciPy、Pillow）、.NET、mbtool、当前游戏资源及工作区 `tools/asset_helpers/`。重建稳定版使用：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -X utf8 mods/Xianjian7Race/YueQingShuOutfit2Race/tools/rebuild.py
./tools/install_release.ps1 -Mod YueQingShuOutfit2Race -Version v0.1.3 -CheckOnly
```

重建从 `dist/YueQingShuOutfit2Race_v0.1.0_Mod.zip` 恢复外观基线，必须保留此旧包；源包不重复包含历史交付 ZIP。源包的 `workspace_tools/` 恢复到工作区根 `tools/`。发布前运行 `tools/finalize_release.py`。变更见[更新日志](CHANGELOG.md)。

## 当前限制

关闭动态布料后，没有独立裙摆、发尾和饰带摆动。骨骼运动仍可能造成跑动、战斗、骑乘时的衣片、内衬、腿部或头发交叉；本版不声称消除了所有蒙皮穿模。

固定脸和手指，不提供捏脸、表情、动态手势或换装；源 UE 着色近似转换。游戏测试由用户完成。官方布料编辑器研究与当前稳定版分开，不自动重新启用布料。
