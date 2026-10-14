# 外层驱动裙摆试验报告 — 2026-10-14

适用 YueQingShuRace 当时的 v0.3.3 测试安装 / Native v1.4.8。共同代理资源 SHA256 为 `b35a392e834ba90105403d8e759c066f527cba230d1d14b86a1437bcc6cab7db`。用户后来反馈“效果很不错，提交更新”，相同资源作为 v0.3.4 发布，验收范围见[游戏验收记录](../../game_acceptance.json)。助手未启动游戏。

当前制作方法、视觉取舍、正常重建和回退只维护在[多层裙摆说明](../../../docs/cloth-simulation.md)。本目录保留生成时的数据，安装记录、候选配置、当时的诊断状态不作为当前安装依据。

## 检查证据

- [资源结构](resource_structure_validation.json)与[可编辑源文件](source_validation.json)：最终回读及外观保留检查通过。
- [层序采样](layer_order_validation.json)：875 对源间距点，在所选 CPU 动作中没有超过 2 mm 的层序反转；不是三角面零交叉证明。
- [三角面交叉对比](layer_crossing_comparison.json)：每帧平均交叉对数，旧 964 顶点候选 → 共同驱动：待机片段 954.95 → 103.38，跑步 1027.96 → 310.92，骑乘 654.95 → 376.15。不是游戏改善百分比。
- [动作报告](motion_validation.json)仍提示身体穿透和拉伸；[共用诊断](cloth_diagnostics.json)为不完整，因为不支持映射布料。这些状态保留，不与后续用户视觉验收混为一谈。
- [测试安装](test_installation.json)、[测试包检查](delivery_validation.json)、[当时结论](conclusion.json)保留原生成范围和时间，正式状态以当前工程为准。

动作范围为女性待机源帧 1–60、完整跑步和骑乘有效源帧；假定 60 fps，先预热 30 帧，未校准游戏播放时长或混合。三角面交叉忽略约 1 mm 以下浅接触，覆盖保存的源帧，不是连续碰撞或引擎自碰撞。

## 预览与试验源

`final_reference_*.png` 是原蒙皮参考，`final_motion_*` 是当时 CPU 最差碰撞帧的映射重建，其他部件保持蒙皮参考；均非游戏截图。逐帧报告、图和代理回放在 `motions/`。

当时源文件为 `source/YueQingShuRace_OuterDrivenLayers_Test.blend` 及同名 FBX；正式源文件已另行更新，原试验文件、旧 964 顶点文件及测试 Mod/Source ZIP 保留。
