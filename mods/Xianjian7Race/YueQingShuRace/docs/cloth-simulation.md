# 多层裙摆与视觉验收

本方案已获得用户反馈“效果很不错，提交更新”，作为 v0.3.4 正式资源发布。游戏、工作区和正式 Mod ZIP 使用同一已测 TPAC，启动器显示 `Yue Qingshu Race`、v0.3.4；原始输入、旧包和历史标签保留。助手未启动游戏。当前验收范围见[游戏验收记录](../reports/game_acceptance.json)。

用户接受外层承担主要飘动、内层同步跟随，允许轻微穿模。验收重点是减少明显的层间交叉并保持观感，不要求零穿模，也不把离线结果当作游戏验收。

## 当前实现

裙摆使用一张平滑的环向/高度代理网格，共 640 顶点、1,216 三角面。主裙面与重叠三组裙片共用连续坐标映射，在相同身体侧面和高度寻找对应区域，避免分别选择折叠主裙面的不同三角形。所有裙层共享该代理的运动，内层没有自己的求解顶点；原始裙层形状与相对偏移保留在渲染映射中。

代理活动范围上限约 5.5 cm，上方约 6 cm 固定，以控制过大的局部折弯。四级 LOD 都采用对应规则；减面后靠近前部裙根的少量顶点用实际几何区域补充分类，后部及头部饰片保留自身分区。原始渲染位置、UV、法线、切线、索引、骨架、权重、材质和贴图保持；仅原直接编译器的两个 LOD3 额外固定点取消映射。

头发、袖片及其他悬垂附件保留独立连接片，没有与裙摆增加跨部件约束。完整代理共 9,601 顶点；640 只表示裙摆分区。保留资源与非裙摆映射不等于这些部件的游戏动态已证明完全相同。

## 检查结果和边界

- [资源结构检查](../reports/experiments/outer_driven_layers_2026-10-14/resource_structure_validation.json)：最终 TPAC 回读、布料/映射字节往返、引用归属、四级可见几何和材质保留通过；静态重建最大误差约 0.18 mm。
- [源文件检查](../reports/experiments/outer_driven_layers_2026-10-14/source_validation.json)：重新打开 Blend 和 FBX；可见 Blend 几何与正式源文件一致，贴图已打包，代理可编辑。
- [层序采样](../reports/experiments/outer_driven_layers_2026-10-14/layer_order_validation.json)：875 对具有源间距的重叠点，在待机片段、跑步和骑乘轨迹中没有出现超过 2 mm 的层序反转。采样点不能代替三角面检查。
- [三角面交叉对比](../reports/experiments/outer_driven_layers_2026-10-14/layer_crossing_comparison.json)：实际四组裙片使用 BVH 候选筛选及精确边/三角形交叉测试，忽略约 1 mm 以下浅接触。下表是 CPU 动作中每帧平均交叉三角面对数，不是穿模面积或游戏改善百分比。

| CPU 动作范围 | 旧 964 顶点候选 | 当前资源 | 平均交叉对数减少 |
| --- | ---: | ---: | ---: |
| 女性待机源帧 1–60 | 954.95 | 103.38 | 约 89% |
| 完整跑步有效源帧 | 1027.96 | 310.92 | 约 70% |
| 完整骑乘有效源帧 | 654.95 | 376.15 | 约 43% |

层间交叉仍有残余，骑乘改善较小。[动作报告](../reports/experiments/outer_driven_layers_2026-10-14/motion_validation.json)仍提示身体胶囊穿透及约束拉伸，不能称作“轻微穿模已通过”。用户已接受当前整体布料观感与轻微穿模取舍；这些 CPU 提示保留，不扩展为其他动作或距离的游戏验收。

CPU 动作使用假定 60 fps、30 帧预热，未校准游戏播放时长、动作混合、材质系数和真实身体碰撞。三角面检查覆盖保存的源帧，不是连续碰撞检测。未添加引擎自碰撞，不承诺所有动作始终保持层距。

正式工程 `mod.json.cloth_diagnostics` 已接入共用 `tools/cloth_simulator/pipeline.py` 的报告模式，打包与安装自动调用。试验时的隔离候选配置与报告保留为历史证据。共用诊断仍明确报告[不完整](../reports/cloth_diagnostics.json)，因为不支持映射布料；专用层序与三角面检查没有将它改记为通过。正式打包与安装入口自动调用，工具错误会阻止交付。

## 预览和交付

`final_reference_*.png` 是原始蒙皮参考；`final_motion_*` 是当前资源在 CPU 碰撞最差帧的最终渲染网格重建，其他部件保持蒙皮参考。它们是离线预览，不是游戏截图。逐帧数值、最差帧图和代理回放在 `motions/`。

正式可编辑文件为 `source/YueQingShuRace_Rigged.blend` 与同名 FBX；原 `OuterDrivenLayers_Test` 文件作为试验源保留，`source/`、`tex/` 相邻。旧实验及正式源文件保留。测试包为 `dist/YueQingShuRace_OuterDrivenLayers_Test_Mod.zip` 和 `dist/YueQingShuRace_OuterDrivenLayers_Test_Source.zip`。Mod ZIP 顶层是 `YueQingShuRace/`；Source ZIP 保存本轮源文件、相邻贴图、参数、脚本、候选数据和报告，复现仍依赖当前工作区共用工具与正常重建缓存。正式 `YueQingShuRace_Mod.zip` 与 `YueQingShuRace_Source.zip` 已更新为 v0.3.4，旧 v0.3.3 和独立试验包保留。

## 重建与回退

常规重建和检查入口见[工程 README](../README.md#工程与重建)。重建先生成直接拓扑作为映射输入，再生成共同代理、连续对应与最终映射资源；直接输入不是交付模式。资源构建、最终回读、源文件、原生蒙皮扫描和共用诊断分别保存状态。新资源与验收包哈希不同时，不能沿用旧的游戏验收结论。

发布前使用工作区共用 `tools/install_release.ps1` 和 `tools/package_delivery.py`，报告模式的映射 `incomplete` 保留提示，工具错误仍阻止交付。保留历史 ZIP；仅更新自己的游戏模块，不启动游戏。源包中的 `workspace_tools/` 恢复到工作区根 `tools/`，源文件与 `tex/` 保持相邻。

需要回到 v0.3.3 时，退出游戏与启动器，用保留的 `dist/YueQingShuRace_v0.3.3_Mod.zip` 替换本模块。早期测试安装与备份记录在[试验报告](../reports/experiments/outer_driven_layers_2026-10-14/README.md)，历史测试回退脚本不能直接用于当前正式发布。
