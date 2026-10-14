# 外层驱动、内层跟随 — 2026-10-14

当前候选已安装到游戏 `Modules/YueQingShuRace/AssetPackages/yqs.tpac`，等待用户实测。启动器仍显示 `Yue Qingshu Race`、v0.3.3；正式工作区模块、正式交付 ZIP 和原始模型保持不变。本次是测试资源替换，没有启动游戏或创建发布标签。

用户接受外层承担主要飘动、内层同步跟随，允许轻微穿模。验收重点是减少明显的层间交叉并保持观感，不要求零穿模，也不把离线结果当作游戏验收。

## 当前实现

裙摆使用一张平滑的环向/高度代理网格，共 640 顶点、1,216 三角面。主裙面与重叠三组裙片共用连续坐标映射，在相同身体侧面和高度寻找对应区域，避免分别选择折叠主裙面的不同三角形。所有裙层共享该代理的运动，内层没有自己的求解顶点；原始裙层形状与相对偏移保留在渲染映射中。

代理活动范围上限约 5.5 cm，上方约 6 cm 固定，以控制过大的局部折弯。四级 LOD 都采用对应规则；减面后靠近前部裙根的少量顶点用实际几何区域补充分类，后部及头部饰片保留自身分区。原始渲染位置、UV、法线、切线、索引、骨架、权重、材质和贴图保持；仅原直接编译器的两个 LOD3 额外固定点取消映射。

头发、袖片及其他悬垂附件保留独立连接片，没有与裙摆增加跨部件约束。完整代理共 9,601 顶点；640 只表示裙摆分区。保留资源与非裙摆映射不等于这些部件的游戏动态已证明完全相同。

## 检查结果和边界

- [资源结构检查](resource_structure_validation.json)：最终 TPAC 回读、布料/映射字节往返、引用归属、四级可见几何和材质保留通过；静态重建最大误差约 0.18 mm。
- [源文件检查](source_validation.json)：重新打开 Blend 和 FBX；可见 Blend 几何与正式源文件一致，贴图已打包，代理可编辑。
- [层序采样](layer_order_validation.json)：875 对具有源间距的重叠点，在待机片段、跑步和骑乘轨迹中没有出现超过 2 mm 的层序反转。采样点不能代替三角面检查。
- [三角面交叉对比](layer_crossing_comparison.json)：实际四组裙片使用 BVH 候选筛选及精确边/三角形交叉测试，忽略约 1 mm 以下浅接触。下表是 CPU 动作中每帧平均交叉三角面对数，不是穿模面积或游戏改善百分比。

| CPU 动作范围 | 旧 964 顶点候选 | 当前候选 | 平均交叉对数减少 |
| --- | ---: | ---: | ---: |
| 女性待机源帧 1–60 | 954.95 | 103.38 | 约 89% |
| 完整跑步有效源帧 | 1027.96 | 310.92 | 约 70% |
| 完整骑乘有效源帧 | 654.95 | 376.15 | 约 43% |

层间交叉仍有残余，骑乘改善较小。[动作报告](motion_validation.json)仍提示身体胶囊穿透及约束拉伸，不能称作“轻微穿模已通过”。本轮按用户授权安装查看实际表现，尚无本候选的游戏验收反馈。

CPU 动作使用假定 60 fps、30 帧预热，未校准游戏播放时长、动作混合、材质系数和真实身体碰撞。三角面检查覆盖保存的源帧，不是连续碰撞检测。未添加引擎自碰撞，不承诺所有动作始终保持层距。

共用 `tools/cloth_simulator/pipeline.py` 已以报告模式检查最终候选。隔离候选工程在本模组 `build/outer_driver_diagnostics/`，其 `mod.json.cloth_diagnostics` 由 `tools/outer_driver_mod.json` 维护，正式模块与配置不被覆盖。共用诊断仍明确报告[不完整](cloth_diagnostics.json)，因为不支持映射布料；专用层序与三角面检查没有将它改记为通过。测试安装入口自动调用，工具错误会阻止安装。

## 预览和交付

`final_reference_*.png` 是原始蒙皮参考；`final_motion_*` 是当前候选在 CPU 碰撞最差帧的最终渲染网格重建，其他部件保持蒙皮参考。它们是离线预览，不是游戏截图。逐帧数值、最差帧图和代理回放在 `motions/`。

可编辑文件为 `source/YueQingShuRace_OuterDrivenLayers_Test.blend` 与同名 FBX，`source/`、`tex/` 相邻。旧实验及正式源文件保留。测试包为 `dist/YueQingShuRace_OuterDrivenLayers_Test_Mod.zip` 和 `dist/YueQingShuRace_OuterDrivenLayers_Test_Source.zip`。Mod ZIP 顶层是 `YueQingShuRace/`；Source ZIP 保存本轮源文件、相邻贴图、参数、脚本、候选数据和报告，复现仍依赖当前工作区共用工具与正常重建缓存。正式 Mod/Source ZIP 保留原样。

## 复现与回退

从工作区根运行，要求已有正常重建缓存：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/Xianjian7Race/YueQingShuRace/tools/build_outer_driver.py
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 tools/cloth_compiler/verify_mapped.py mods/Xianjian7Race/YueQingShuRace
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/Xianjian7Race/YueQingShuRace/tools/diagnose_skirt_proxy.py
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/Xianjian7Race/YueQingShuRace/tools/verify_outer_layers.py
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/Xianjian7Race/YueQingShuRace/tools/run_outer_driver_diagnostics.py
```

构建包装器临时提供映射器配置，在结束或报错后恢复正式 `model_config.json`；不能与其他修改该配置的构建并行。新候选需重新归档资源与层序检查、源文件检查和预览，不能使用旧哈希报告安装。

安装与备份哈希见[安装记录](test_installation.json)。退出游戏和启动器后，以下命令二选一：

```powershell
# 回到上一版 964 顶点测试候选
& mods/Xianjian7Race/YueQingShuRace/tools/install_outer_driver_test.ps1 -Restore
# 或直接恢复原 v0.3.3 直接模拟资源
& mods/Xianjian7Race/YueQingShuRace/tools/install_outer_driver_test.ps1 -RestoreOriginal
```

回退先验证当前候选和备份，不结束游戏进程、不改其他模块。常规正式安装入口会覆盖测试资源。
