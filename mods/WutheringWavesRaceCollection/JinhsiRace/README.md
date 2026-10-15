# Jinhsi Race

今汐完整人物固定外观种族，保留独立源工程，运行资源由上级合集统一加载。角色资源版本 `v0.1.0`，Native v1.4.8；模块 ID `JinhsiRace`，内部种族 `ww_jinhsi`。

## 使用

随[鸣潮合集](../README.md)安装，在启动器只启用 `Wuthering Waves Race Collection`。`module/JinhsiRace/` 为独立构建资源，不与合集同时启用，避免重复注册。角色带完整头、脸、衣服、双手，普通防具可能叠加或遮盖外观。仅新增女性测试兵种 `ww_jinhsi_test`，不替换原版招募或兵种树。测试存档开启作弊和开发者控制台后可使用：

```text
campaign.give_troops ww_jinhsi_test 10
```

Race Troop Builder 可选择 `ww_jinhsi`、女性，去除头、身体、腿、手套、披风装备，再配置需要的武器和坐骑。使用本种族的存档依赖合集模块。

## 外观与布料

保留源 PMX 固定脸、比例与 UV，统一单位换算为 0.08 米／源单位，自有 28 骨骨架按源关节与绑定方向校准，沿用原生动作。四级 LOD 保护脸部轮廓。默认不启用布料，仅配置明确的长发、长饰品；**裙子和袖子不使用布料**。当前启用的材质及挂点、固定高度、活动距离见[模型配置](tools/model_config.json)的 `cloth_parts` 和 `cloth_policy`。腰部饰品挂 pelvis，发束与头部饰品挂 head。可见表面直接模拟，包内没有透明模拟代理。

源文件 `input/original/鸣潮_今汐1.023请标明辫子软化版本.pmx`。原 ZIP、完整解包内容、作者说明保存在 `input/`；仅导入人物，未上传远程。多余眼部高光／表情层及确认为重叠的 MMD sphere 层按[准备报告](reports/preparation.json)排除；虹膜保留源颜色贴图中的高光。

## 验证与限制

[最终 TPAC 检查](reports/release_validation.json)回读骨架、全部交付 LOD、UV、材质引用、量化权重、布料标记和直接预处理数据，并扫描跑步、持弓、挥击、骑乘原生片段；UI 待机采用抽样姿态检查。[源文件检查](reports/source_validation.json)包含重新打开 Blend/FBX 后的比例与 UV 对照。人物预览组件仅适配此种族 UI，随模块独立交付；完整场景动作集按当前 Native 生成。

[布料诊断](reports/cloth_diagnostics.json)读取最终 TPAC，以 CPU 近似模拟检查动作；初次接入采用报告模式，提示不代表游戏物理通过或失败。诊断采用每秒 60 个源帧，尚未对齐所有游戏片段实际播放时长；LOD 布料数据相同时检查代表级 0。

固定外观，无捏脸形变、面部表情或手指握持形变。MMD toon 与游戏 PBR 不同；普通蒙皮裙子在骑乘、蹲姿与大幅动作中可能折叠或穿模。游戏测试由用户完成，队伍、百科、物品栏、主要战场动作和远近 LOD 均待实机验收；助手未启动游戏。状态见[游戏验收记录](reports/game_acceptance.json)。

## 工程与重建

`input/` 原始输入，`source/` 可编辑 Blend/FBX，`tex/` 相邻贴图，`tools/` 角色参数和入口，`module/JinhsiRace/` 独立构建资源，`build/` 缓存，`reports/` 检查与预览，`dist/` 独立构建包。最终管理使用上级合集 ZIP。

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/WutheringWavesRaceCollection/JinhsiRace/tools/rebuild.py
```

依赖 Blender 5.2、Python NumPy/SciPy/Pillow、.NET 10／net472 引用、Native v1.4.8、mbtool、MMD Tools PMX 读取器及[共用资源流程](../../../tools/pmx_race_pipeline/README.md)。合集源包保持每个角色 `source/` 与 `tex/` 相邻；将 `workspace_tools/` 恢复到工作区 `tools/`，按本机情况调整外部路径。

[更新日志](CHANGELOG.md) · [合集入口](../README.md)
