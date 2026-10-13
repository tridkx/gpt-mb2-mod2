# BoRu Race

孟柏汝去脚版的独立骑砍2固定外观种族，版本 v0.1.1。模块 ID `BoRuRace`，内部种族 ID `boru_race`，模组管理器显示 `BoRu Race`。资源按本机 Native v1.4.8 制作。

## 使用

将 [Mod 包](dist/BoRuRace_Mod.zip) 解压到游戏 `Modules`，启动器启用 BoRu Race，放在 Native、SandBoxCore、Sandbox 之后。本机安装目录为 `D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/BoRuRace`。

新增独立女性测试兵种 `boru_race_test`（孟柏汝），没有替换原版招募或升级树。在开启作弊和开发者控制台的测试存档中执行：

```text
campaign.give_troops boru_race_test 10
```

[Race Troop Builder](../RaceTroopBuilder/README.md) 可扫描此模块，选择 `boru_race`、女性、固定脸参数；完整身体自带白衬衫、牛仔裤、帆布鞋、头发及眼镜，配置兵种时清除头部、身体、腿部、手套和披风防具，按需配置武器与坐骑。本包未声明种族固有护甲。

v0.1.1 已获用户实机验收通过，确认本次反馈的眼镜不透明、肩膀上顶和手臂拉长问题修复。范围见[用户验收记录](reports/user_acceptance.json)。队伍、百科、物品栏、各类重建操作及战场动作的其他行为仍按实际测试分别记录。使用本种族或测试兵种的存档依赖本模块，建议保留独立测试存档。

## 模型与材质

原始模型来自 `D:/dsh-nvguiqiao/repo/models/08_孟柏汝_BoRu_女_去脚/`，贴图来自相邻原版角色的 textures，工程保存只读副本与哈希。保留去脚切口和完整鞋壳；厘米统一换算为米并绕竖轴转向，脸型、四肢、胸腰和鞋身不作局部拉伸或收窄。

原 80 骨蒙皮映射到角色专用 28 骨骨架，关节位置匹配源模型，手臂绑定方向匹配源姿势；沿用当前游戏原生动作。裤裆与袜口采用皮肤/服装共用的连续权重场。固定脸与原手型保留，双手包含在完整身体 MetaMesh 中。

四级 LOD 为 32743 / 26851 / 23883 / 21508 个三角面。LOD0 保留全部原始三角形和网格坐标；远景移除衣裤内不可见的皮肤面，保持衣服和可见皮肤细节，减面主要用于头发、口腔等部位，保护共享边界及眼睛、睫毛和眼镜。换算后的静态总高约 1.655 米。身体、服装、头发使用源颜色与法线贴图，身体 ORM 转为金属度/光泽度/AO。眼球 UV 单独投影到源虹膜贴图，其他 UV 保留；缺失的衣服控制图和饰品参数使用保守值，详见 [材质恢复说明](reports/material_recovery.json)。

## 当前限制

固定外观，不提供捏脸形变、面部表情或手指握持形变。角色创建界面适配只保证使用本种族的动作集和绑定骨架，不制作脸型定制；身体滑杆触发重建时仍保留引擎原有缩放。短发、衬衫和牛仔裤采用蒙皮，没有游戏布料物理。普通防具可能叠加或遮盖身体，混搭不在本版验收范围。

离线检查可验证资源结构、权重、源比例和原生动作中的明显拉裂，不能证明游戏加载、IK、武器握持、马匹碰撞、镜片着色或全部穿模正确。种族最终身高还受运行时缩放影响，需要在游戏中确认。

## 工程与重建

`input/` 保存 PSK、OBJ、原说明、原工具及贴图；[Blend](source/BoRuRace_Rigged.blend) 与 [FBX](source/BoRuRace_Rigged.fbx) 位于 `source/`，配套贴图位于相邻 `tex/`；`module/BoRuRace/` 为可安装模块，`tools/` 为专用脚本和参数，`build/` 为缓存，`reports/` 为检查与预览。

依赖 Blender 5.2、Anaconda Python（NumPy、SciPy、Pillow）、.NET 9/10、.NET Framework 4.7.2 引用程序集、当前游戏资源、mbtool 和工作区 `tools/asset_helpers/`。从工作区根重建：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/BoRuRace/tools/rebuild.py
```

重建只生成并检查工程；打包和安装使用根 `tools/package_delivery.py`、`tools/install_release.ps1`。源 ZIP 保持 `source/` 与 `tex/` 相邻，共用助手存于 `workspace_tools/`，独立恢复时将其放回工作区根 `tools/` 并调整外部工具路径。

预览运行组件仅处理本种族的 CharacterTableau、BasicCharacterTableau 和 BodyGeneratorView，保存位置、缩放及两条动作通道进度；角色创建入口直接读取当前阶段的 BodyGeneratorView 以及当前/待切换人物。镜片使用排序后的透明通道，不写入不透明深度或投射阴影。运行日志位于文档目录 `Mount and Blade II Bannerlord/BoRuRace/ui_runtime_v0.1.1.jsonl`。

[最终资源检查](reports/release_validation.json)、[源比例检查](reports/preservation_validation.json)、[预览组件回归](reports/ui_scope_validation.json)、[本次返修与旧版对比](reports/feedback_fix_validation.json)、[更新日志](CHANGELOG.md)。
