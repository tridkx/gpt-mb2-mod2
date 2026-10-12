# Tianxiang Girl T1 Ren Qiu Race

第一套“纫秋为佩”完整人物种族 Mod，版本 v0.1.1，适用本机 Native v1.4.8。模块 ID 为 `TianxiangGirlT1Race`，种族 ID 为 `txgirl1`，独立骨架为 `txgirl1_skeleton`。

## 当前功能

保留原始固定脸、头发、衣服和双手，源模型仅统一换算为米，没有拉伸头身或四肢。含头发的源网格总高约 1.332 米，skin 最小缩放参数为 1.0；实际游戏身高仍需实测校准。四级 LOD 面数为 15516、10850、7030、4096，使用当前 Native 的 28 骨语义和原生动作。

双手包含在完整身体中，其他自动生成身体槽使用内部隐藏占位。保留输入文件已有的眼周 UV 修正；源纹理打包到 Blend。UI 运行组件仅处理明确属于 CharacterTableau、BasicCharacterTableau 或 BodyGeneratorView 的本种族预览骨架，跳过地图人物；重建时保留位置、缩放、装备和动作进度。游戏内效果尚未验收。

裙摆 LOD0/1 有直接布料模拟配置和各自拓扑的预处理数据，腰部约 30 毫米固定带，下摆最大活动距离 0.32 米。双腿各有上大腿、下大腿和小腿胶囊，共六个碰撞体，按本模型腿部表面和骨架拟合；拟合范围避开紧贴身体的固定腰部。远处 LOD2/3 使用蒙皮。最终预处理数据、骨骼映射、固定点、约束和随动胶囊活动范围检查通过，游戏实际求解尚未验证。

新增一个女性测试兵种“天香纫秋少女”（`txgirl1_test`），等级 6，沿用帝国新兵技能和四种武器组合，没有防具、固有护甲或升级分支。战斗与平民装备均移除原版衣物。它不进入原版招募池，不覆盖原版兵种；后续可使用 [Race Troop Builder](../../RaceTroopBuilder/README.md) 拼装兵种树。

## 游戏验收

在启动器启用 **Tianxiang Girl T1 Ren Qiu Race**，排在 Native、SandBoxCore、Sandbox 后。用独立测试存档检查百科中的“天香纫秋少女”。在已启用作弊的战役存档中，打开控制台执行以下命令，添加 5 名测试兵；命令及竖线参数格式已对照本机 v1.4.8 `CampaignCheats.AddTroopsToParty` 核对。

```text
campaign.add_troops txgirl1_test | 5
```

加入队伍后检查队伍预览与战场显示。使用本种族创建的角色可另外检查物品栏预览。种族资源和测试兵种的具体 ID 见上文。

先复测创建角色后进入地图、打开物品栏再返回地图是否稳定；本版的预览范围修复尚待游戏确认。然后检查脸和睫毛、整体身高、头颈连接、肩袖、左右手腕、待机及跑步。近处观察裙摆是否真正摆动、抬腿是否推开布料、静止时是否异常顶起；再检查持弓、挥刀、骑乘和远近 LOD 切换。诊断日志位于系统文档目录 `Mount and Blade II Bannerlord/TianxiangGirlT1Race/ui_runtime_v0.1.1.jsonl`。测试存档依赖本模块；关闭模块后不要继续使用依赖它的存档。

## 当前限制

- 裙摆布料仅在 LOD0/1 配置，游戏求解和碰撞效果待验收；远处裙摆、袖片和头发随骨骼移动。大幅抬腿、骑乘及转头可能穿模，动作扫描不证明不存在穿模。
- 固定脸，不提供捏脸形变、表情动画或手指动态握持。捏脸页面适配未纳入本次验收。
- 实际身高、武器握持、IK、命中胶囊、人物预览与性能尚待游戏验收。Monster 尺寸暂沿用当前 Native，不能以源网格高度推断命中范围。

## 工程与重建

`input/original/` 完整保留用户输入，`input/` 根层是构建输入副本；`source/` 保存可编辑 Blend/FBX，相邻 `tex/` 保存贴图。`tools/` 是本模型参数和脚本，`module/TianxiangGirlT1Race/` 是可安装模块，`reports/` 保存离线检查与最终资源预览，`build/` 为缓存，`dist/` 为交付包。

依赖本机 Blender 5.2、Anaconda Python（NumPy、SciPy、Pillow、lxml）、.NET SDK、net472 引用程序集、mbtool、AssetTool、当前游戏 Native 资源与工作区 `tools/asset_helpers/`、`tools/cloth_compiler/`。源包中的 `workspace_tools/` 恢复到工作区根 `tools/`；外部工具二进制需单独准备。

从工作区根重建：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/TianxiangRaceColletion/TianxiangGirlT1Race/tools/rebuild.py
./tools/install_release.ps1 -Mod TianxiangGirlT1Race -Version v0.1.1 -CheckOnly
```

首次安装去掉 `-CheckOnly`；已有交付包的升级安装需指定实际旧版本 `-PreviousVersion`。不要用首版命令覆盖已交付同版本包。流程不启动游戏。

离线证据见[最终资源检查](reports/release_validation.json)、[布料检查](reports/cloth_validation.json)、[腿部碰撞体](reports/cloth_collision.json)、[源文件检查](reports/source_validation.json)、[注册检查](reports/registration_validation.json)、[最终包正面预览](reports/final_rest_front.png)及[待机预览](reports/final_idle_worst.png)。动作预览只展示蒙皮参考姿态，没有运行游戏布料求解器。版本记录见 [CHANGELOG](CHANGELOG.md)。
