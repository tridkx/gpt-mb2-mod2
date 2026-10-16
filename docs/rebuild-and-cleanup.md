# 重建输入与构建缓存

## 当前可复现范围

游戏运行只读取各工程的 `module/`。继续制作还需要原始输入、最终可编辑模型、贴图、脚本、参数和原生参考数据。生成源模型、构建最终 TPAC、通过离线检查、通过游戏验收是不同结论。

| 范围 | 当前能力 | 必须保留的输入 |
| --- | --- | --- |
| 使用 `tools/pmx_race_pipeline/` 的 29 个原神／鸣潮角色 | `tools/rebuild.py` 从原始 PMX 生成源模型并进入资源构建；源模型生成及 Blend／FBX 重开已逐角色隔离验证。此次没有完整重建最终 TPAC | `input/`、`tex/`、角色配置、共用工具、原生骨架／动作参考和外部依赖 |
| 天香 T5 当前外观返修 | 从本地 `TianxiangT5/v1.4.0` 标签恢复固定 TPAC、Blend、FBX，再执行当前参数变换；不等于只靠原始模型重建最新版 | Git 历史与该标签、外观配置、贴图及参考数据 |
| 圣绣明玉 v1.1.7 | 现有流程是固定旧版基线上的增量制作；没有已验证的原始 FBX 到最新版完整冷启动入口 | 下方必要构建输入、最终源文件、脚本、贴图与参考数据 |
| 其他自定义种族和装备工程 | 有独立重建入口或分步生成脚本；此次只检查入口与依赖，未逐工程冷启动执行 | 原始输入、最终源文件、脚本、配置及仍被读取的基线 |

逐工程分类、29 个角色的比较指标和保留基线清单见 [重建能力检查报告](reports/2026-10-16-rebuild-capability-audit.json)。报告中的源模型比较覆盖顶点、UV、面循环索引、权重、布料 Alpha 和骨架静止矩阵；不覆盖全部材质、法线、修改器或最终 TPAC 字节。

## 常规重建入口

在工作区根目录运行角色自己的 `tools/rebuild.py`，例如：

```powershell
python -B -X utf8 mods/GenshinRaceCollection/GanyuRace/tools/rebuild.py
python -B -X utf8 mods/WutheringWavesRaceCollection/ShorekeeperRace/tools/rebuild.py
```

共用入口会建立缺少的 `build/`、`source/`、`tex/` 和 `reports/` 目录。默认流程重新处理源模型和贴图，不需要旧导出目录；`--reuse-textures` 是另一个显式复用编码缓存的路径，清理缓存后不能直接依赖该选项。Blender、Python 库、.NET、当前 Native、mbtool 和 PMX 读取器等外部依赖见 [共用流程说明](../tools/pmx_race_pipeline/README.md)。角色有历史修改不代表每个历史步骤都要重新执行，应按当前入口和配置处理。

天香 T5 使用 [外观构建入口](../mods/TianxiangCollection/sets/TianxiangT5/tools/build_appearance.ps1)。它向上查找工作区，恢复 Git 标签基线后重建输出。不能删除 Git 历史，或用当前源文件冒充旧版基线。

## 圣绣明玉的必要构建输入

当前入口实际读取以下内容，目录名虽然是 `build/`，其中部分数据目前仍承担源输入的作用：

- `mods/ShengxiuCollection/build/back_hair_baseline_v1.1.6/`：固定旧版 TPAC、Blend／FBX、权重数组、清单和碰撞 XML。
- `mods/ShengxiuCollection/build/hair_shape_baseline_v1.1.4/rig_arrays.npz`：旧版坐标用于区分后发区域。
- `mods/ShengxiuCollection/build/head_neck_final_export/geo/`：已接受身体的回读几何，用于后发贴合和碰撞拟合。
- `mods/ShengxiuCollection/build/rig_arrays.npz`、`rig_manifest.json`、`spec.json`、编码贴图及相关工具：增量构建和导出的配套输入。

本工作区保留明玉当前 `build/`。直接运行初始 `rig_model.py` 不能证明会恢复全部后续返修效果；缺少固定基线时让脚本从当前源文件新建“旧版基线”也不可靠。当前命令与验收范围见 [圣绣说明](../mods/ShengxiuCollection/README.md#重建与交付)。

这些输入及部分其他工程基线被现有 Git 忽略规则排除，普通推送不包含它们。只克隆当前 Git 仓库不足以保证所有历史增量工程都能重建。若要实现完全独立于缓存的远程备份，需要另行把必要输入归档为受管理的源依赖，或补齐从原始模型生成固定基线的流程；本次未伪称完成该改造。

## 清理边界

- 保留原始输入、当前最终 Blend／FBX、工作贴图、运行模块、配置、生成脚本、必要参考和 Git 历史／标签。
- 重复的 `*_Source.zip` 可以删除；需要交付时由对应打包入口从展开工程生成。Source ZIP 不是完整冷启动备份，未必包含被忽略的必要基线。
- 已确认生成链的导出网格、贴图编码结果、中间 TPAC 和布料诊断输出可以清理。诊断 Probe 及配置列出的输入仍保留；诊断输出缺失时共用入口会重新计算。
- 不对所有工程执行无差别的 `git clean -fdX` 或整目录 `build/` 删除。旧基线必须逐工程确认生成来源后再处理。

清理文件清单分别见 [首轮清理报告](reports/2026-10-16-workspace-cleanup.json)、[构建产物清理报告](reports/2026-10-16-generated-cleanup.json) 和 [源包内容核对](reports/2026-10-16-source-archive-audit.json)。
