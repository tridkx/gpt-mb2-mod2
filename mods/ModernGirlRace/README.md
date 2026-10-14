# Modern Girl Race

将现代少女脸发整理 v6 的完整人物制作成独立骑砍2固定外观种族。模块 ID 为 `ModernGirlRace`，内部种族为 `modern_girl`；模组管理器显示 `Modern Girl Race`。使用本机 Native v1.4.8 资源构建。

## 使用

将 [Mod 包](dist/ModernGirlRace_Mod.zip) 解压到游戏 `Modules`，启用 Modern Girl Race，放在 Native、SandBoxCore、Sandbox 之后。工作区安装目标为 `D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/ModernGirlRace`。

本包新增测试兵种 `modern_girl_test`（现代少女），不替换原版兵种，不改变原版招募或升级树。可在启用作弊模式和开发者控制台的测试存档中使用：

```text
campaign.give_troops modern_girl_test 10
```

独立种族也可由兵种拼装器使用：种族 ID `modern_girl`、女性、移除头部/身体/腿部/手套/披风防具，保留所需武器与坐骑。人物自带 T 恤、牛仔裤和鞋，普通防具可能叠加或遮盖身体。

游戏测试由用户完成。检查队伍、百科和物品栏预览，创建角色页面初次显示及切换参数后的姿态，以及战场待机、跑步、挥击、射箭和骑乘；离线预览不能证明游戏中的 IK、握持、碰撞与加载兼容性。测试存档使用本种族或兵种后依赖此模块，建议单独保留测试存档。

## 外观与范围

- 保留原六部位的固定脸、发髻、衣服、身体比例、UV 和颜色贴图；源归一化模型统一旋转和缩放，含发髻静态总高约 1.649 米。
- 当前模型专用 28 骨绑定骨架，沿用原生动作语义与层级；上臂、前臂及中间扭转骨的绑定方向按本模型骨段对齐。双手包含在身体 MetaMesh 中，保持源手型，未制作手指握持形变。
- 四级 LOD，保护跨部位共享切口与相同权重。LOD0 排除源头部两片零面积三角形，其他部位不作形体拉伸。
- 人物预览运行 DLL 处理本种族的 CharacterTableau、BasicCharacterTableau 和创建角色页面 BodyGeneratorView 的初次显示与人物重建；保留位置、缩放及两条动画通道进度。日志保存在文档目录 `Mount and Blade II Bannerlord/ModernGirlRace`。

## 当前限制

固定外观，不提供捏脸形变定制或面部表情动画。创建页面使用本种族的男女 `_facegen` 动作集；切换性别、年龄、衣着或身体参数后，组件会恢复匹配的动作集和绑定骨架。此适配不增加外观定制功能，滑杆对固定模型的形变效果不属于验收范围。创建页面初次显示和切换参数后的姿态仍需用户游戏复测。

源资产仅提供 BaseColor，游戏材质使用平坦法线和保守的控制贴图。头发与衣服采用骨骼蒙皮，没有布料物理。原模型的局部眼睑棱角、小 UV 岛与开放解剖切口保留；动作中仍需检查穿模、武器握持与骑乘效果。

## 工程与重建

`input/model.fbx` 是未改动原始输入；[可编辑 Blend](source/ModernGirlRace_Rigged.blend) 和 [FBX](source/ModernGirlRace_Rigged.fbx) 在 `source/`，六张颜色贴图在相邻 `tex/`。运行模块在 `module/ModernGirlRace/`，参数及专用脚本在 `tools/`，中间缓存在 `build/`，离线报告和预览在 `reports/`。

依赖当前游戏资源、Blender 5.2、本机 Anaconda Python（NumPy、SciPy、Pillow）、.NET 9/10 与 .NET Framework 4.7.2 引用程序集、mbtool，以及工作区 `tools/asset_helpers/`。工具路径在脚本中明确指定，重建入口：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/ModernGirlRace/tools/rebuild.py
```

重建只生成并检查本模块；打包与安装使用工作区入口。源 ZIP 保持 `source/` 与 `tex/` 相邻，附带共用助手；脱离工作区后应将 `workspace_tools/` 恢复为工作区根的 `tools/`，并调整本机外部依赖路径。

[离线检查报告](reports/release_validation.json)、[源比例与 UV 检查](reports/preservation_validation.json)、[手臂绑定与保留数据检查](reports/arm_binding_validation.json)、[预览组件范围检查](reports/ui_scope_validation.json)、[v0.1.1 创建页面适配历史检查](reports/ui_creation_fix_validation.json)、[更新日志](CHANGELOG.md)。
