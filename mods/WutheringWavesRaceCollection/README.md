# Wuthering Waves Race Collection

鸣潮 8 个完整人物固定外观种族，版本 `v0.1.0`，适用于本机 Native v1.4.8。每个角色有独立工程、独立模块、源文件、参数与交付目录；合集仅用于统一管理 ZIP，不新增合并游戏模块。

## 安装与使用

[模组合集 ZIP](dist/WutheringWavesRaceCollection_v0.1.0_Mod.zip) 顶层是下表 8 个模块目录。选择需要的角色解压到游戏 `Modules/`，在启动器分别启用；可同时启用，彼此没有依赖。制作完成后安装到 `D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/<ModId>/`，助手不启动游戏。

| 角色／工程 | 启动器英文名 | 内部种族 | 测试兵种 |
| --- | --- | --- | --- |
| [今汐](JinhsiRace/README.md) | Jinhsi Race | `ww_jinhsi` | `ww_jinhsi_test` |
| [今汐·桃夭灼灼](JinhsiOutfitRace/README.md) | Jinhsi Outfit Race | `ww_jinhsi_outfit` | `ww_jinhsi_outfit_test` |
| [白芷](BaizhiRace/README.md) | Baizhi Race | `ww_baizhi` | `ww_baizhi_test` |
| [鉴心](JianxinRace/README.md) | Jianxin Race | `ww_jianxin` | `ww_jianxin_test` |
| [吟霖](YinlinRace/README.md) | Yinlin Race | `ww_yinlin` | `ww_yinlin_test` |
| [守岸人](ShorekeeperRace/README.md) | Shorekeeper Race | `ww_shorekeeper` | `ww_shorekeeper_test` |
| [长离](ChangliRace/README.md) | Changli Race | `ww_changli` | `ww_changli_test` |
| [折枝](ZhezhiRace/README.md) | Zhezhi Race | `ww_zhezhi` | `ww_zhezhi_test` |

仅新增女性测试兵种，不更改原版招募和兵种树。测试存档开启作弊和开发者控制台后可用 `campaign.give_troops ww_jinhsi_test 10`，其他角色替换对应兵种 ID。Race Troop Builder 可选择各自种族、女性，去掉头部、身体、腿、手套和披风防具，再选武器与坐骑。完整人物自带服装、双手和发型；普通防具可能叠加或遮盖外观。含这些种族的存档依赖对应模块。

## 模型和布料

保留源固定脸、服装比例与 UV，按源关节校准各自 28 骨绑定骨架，沿用原生动作；四级 LOD 保留关键脸部轮廓。默认不使用布料，仅对长发及明确的长饰品启用有限直接模拟，**裙子与袖子均为普通蒙皮**。

| 角色 | 布料范围 |
| --- | --- |
| 今汐 | 长辫、辫上饰品、独立长穗 |
| 今汐·桃夭灼灼 | 后部长发、独立前后长带；裙身和薄纱裙片普通蒙皮 |
| 白芷 | 后部长发；披肩普通蒙皮 |
| 鉴心 | 后部长发、随发长饰、独立前后飘带；前后裙摆普通蒙皮 |
| 吟霖 | 长马尾 |
| 守岸人 | 后发、头巾垂片、独立前长带；裙片和蝴蝶结普通蒙皮 |
| 长离 | 后部长发、独立流苏；裙片和袖子普通蒙皮 |
| 折枝 | 后部长发；镜片使用连续透明材质 |

各材质、挂点、固定区、活动距离与碰撞体按角色配置，不按通用材质名猜测。详见各工程 `tools/model_config.json`、`reports/cloth_paint.json` 与 `reports/cloth_collision.json`。布料直接作用于可见表面，不使用透明模拟代理。

## 工程、依赖与重建

`<ModId>/input/` 保留原 ZIP、完整 PMX 和贴图；`source/` 与 `tex/` 相邻，`tools/` 保存参数与独立重建入口，`module/<ModId>/` 是实际模块，`build/`、`reports/`、`dist/` 分别保存缓存、检查和独立交付。系列 `tools/` 只负责此次八角色的批次处理与合集打包。

[合集源包](dist/WutheringWavesRaceCollection_v0.1.0_Source.zip) 内每个角色仍保持独立目录，公共工具仅在 `workspace_tools/` 保存一份。恢复到新工作区时将其放回根 `tools/`，保持各工程 `source/` 与 `tex/` 相邻，并调整游戏、Blender、PMX 读取器和 mbtool 的外部路径。

依赖 Blender 5.2、Python（NumPy、SciPy、Pillow、Matplotlib）、.NET 10 与 .NET Framework 4.7.2 引用程序集、Native v1.4.8、`D:/mb-tools`、MMD Tools PMX 读取器和[共用 PMX 流程](../../tools/pmx_race_pipeline/README.md)。在工作区根运行，例如：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/WutheringWavesRaceCollection/JinhsiRace/tools/rebuild.py
```

系列工具 `bootstrap.py` 保留原始输入，`configure.py` 根据八个模型写入专用参数；首次制作后通常直接使用角色重建入口，不重复覆盖专用参数。`build_sources.py` 在后台 Blender 内执行，`build_resources.py` 构建独立 TPAC，`render.py` 从最终包生成各级预览，`finalize.py` 写入当前文档和诊断配置，`deliver.py` 运行诊断并调用共用安装入口，最后 `deliver.py --assemble` 汇总并逐文件核对合集。已有合集 ZIP 时需要改用新版本，入口拒绝覆盖历史包。

## 检查与当前限制

[交付检查](reports/collection_delivery.json)记录最终包、ZIP 与安装目录逐文件一致性。各角色报告包含最终 TPAC 回读、骨架、全部交付 LOD、UV、材质、量化权重、直接布料预处理段、完整动作片段检查及 Blend/FBX 重开验证。预览使用最终 TPAC 解码资源，见[角色总览](reports/collection_overview.jpg)。

布料诊断读取最终包，初次接入为报告模式；CPU 近似结果独立于游戏验收，`needs_review` 提示不会被写成实机通过。源帧采样暂按 60 fps，尚未校准所有片段实际播放时长；数据一致的 LOD 检查代表级 0。具体动作范围、最差帧和状态见各角色 `reports/cloth_diagnostics.json`。

固定外观，不提供捏脸形变、面部表情或手指握持形变。MMD toon 与游戏 PBR 不同。普通蒙皮裙子在骑乘、深蹲和大幅动作中可能折叠或穿模。游戏测试由用户完成，队伍／百科／物品栏预览、主要战场动作、握持、骑乘与远近布料效果仍待实机确认；助手未启动游戏。

[更新日志](CHANGELOG.md) · [工作区入口](../../README.md)
