# 简化裙摆代理试验 — 2026-10-14

适用范围：YueQingShuRace v0.3.3 / Native v1.4.8，以现有直接模拟资源为基线。试验没有修改运行模块、正式源文件或已安装模块，没有启动游戏，也没有发布新版本。

## 结果与边界

已生成原生映射模拟候选，四级 LOD 共 18 个渲染网格映射到一个独立模拟资源。原始可见网格的位置、UV、法线、切线、骨权重、索引、材质、贴图和骨架保持；仅原编译器额外固定的两个 LOD3 顶点取消映射。非裙摆部件作为独立连接片保留在代理中，未与裙摆建立跨部件约束；这不等于其游戏动态已经证明与直接模拟相同。

**候选未通过外观与映射检查，未安装。** 包格式与静态重建通过不能作为可交付结论。正式重建仍使用直接模拟，正式参数、版本和游戏验收状态保持原样。

| 候选 | 裙摆代理 | 检查结果 |
| --- | --- | --- |
| 第一轮：规则环形网格 | 768 顶点、1,472 三角面 | 映射偏移最大约 11.2 cm；CPU 下垂后裙片出现明显起皱。碰撞残留小不代表外观通过。 |
| 第二轮：贴近主裙面、限制活动范围 | 768 顶点、1,472 三角面 | CPU 下垂后起皱减少，但出现身体穿模；存在约 -1.34 cm 的内侧映射偏移。探针曾使用放宽的偏移范围作敏感性试验，不能当作发布验收。 |
| 第三轮：简化原始主裙面 | 964 顶点、1,848 三角面 | 主表面由 2,110 个去重顶点简化而来。原生格式、四级可见几何保留及实验源文件检查通过；部分裙片映射到代理内侧，最小偏移约 -6.57 cm，超出检查边界。 |

第三轮整个代理包含其他悬垂部件，共 9,925 个渲染顶点、9,788 个求解位置。964 只表示裙摆分区的顶点数，不能当作完整角色的模拟规模。

## 证据与预览

- [第三轮资源结构检查](iteration3/mapped_structure_validation.json)：最终候选 TPAC 回读、布料/映射字节往返、引用归属、四级原始 GPU 数据对比。
- [第三轮下垂检查](iteration3/mapped_settling_validation.json)：内侧映射偏移检查失败；失败原因和资源哈希保留。
- [实验源文件检查](source_validation.json)：重开 Blend 和 FBX；可见 Blend 几何与正式源文件一致，纹理已打包，代理可编辑。
- [第三轮动作报告](iteration3/motion_validation.json)：待机片段、跑步、骑乘的 CPU 近似诊断。面内部穿透残留最大约 1.54、5.50、3.09 cm，均需进一步处理。各动作的详细报告、最差帧和离线代理回放在 `iteration3/motions/`。
- 前两轮数据及预览分别在 `iteration1/`、`iteration2/`，不得作为第三轮结果使用。
- 本目录 `final_reference_*.png` 是原蒙皮参考；`final_settled_*.png` 是第三轮 CPU 探针重建结果。后者在失败后仍保存供排查，**不是通过证明或游戏截图**。

动作诊断只覆盖裙摆代理；女性待机限定源帧 1–60，跑步和骑乘覆盖现有片段的全部有效源帧，均先预热 30 帧。诊断使用现有骨架、胶囊和动作数据，假定 60 fps，未校准到游戏动作播放时长。CPU 弯曲/锚点系数为敏感性参数，不代表引擎材质系数。代理层间自碰撞、游戏求解器、动作混合及远距离行为未验证；不得把代理轨迹当作最终渲染网格整体通过。

## 复现与可编辑文件

在已有正常重建缓存的工作区根执行：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/Xianjian7Race/YueQingShuRace/tools/try_skirt_proxy.py
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 tools/cloth_compiler/verify_mapped.py mods/Xianjian7Race/YueQingShuRace
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/Xianjian7Race/YueQingShuRace/tools/probe_skirt_proxy.py mods/Xianjian7Race/YueQingShuRace
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/Xianjian7Race/YueQingShuRace/tools/diagnose_skirt_proxy.py
```

第三条命令对本候选应返回失败。脚本输出位于本模组的 `build/`，不会写游戏模块。实验参数仅在 `tools/skirt_proxy_config.json` 维护；构建包装器临时提供共用映射器所需配置，并在结束或报错后恢复正式 `model_config.json`。不能与其他正在修改该配置的构建并行执行。

实验源文件为 `source/YueQingShuRace_SkirtProxy_Experimental.blend` 与同名 FBX，包含不可见的 `yqs_cloth_proxy`，保持 `source/`、`tex/` 相邻。正式 `YueQingShuRace_Rigged.*` 未被替换。候选 TPAC 缓存在 `build/mapped_candidate.tpac`，保留副本在独立实验归档；不纳入正式 Mod ZIP，也不改变正式安装入口。

独立归档为 `dist/YueQingShuRace_SkirtProxy_Experiment_2026-10-14.zip`，保存候选资源、实验 Blend/FBX、相邻贴图、参数、脚本及检查记录。它是未验收的工程试验快照，不能直接作为游戏模块安装；复现仍依赖本工作区的正常重建缓存和共用工具。

## 下一步判断

简化规模已经实现，仍需解决代理覆盖与映射方向。继续尝试时，应按主裙、内层裙和独立悬垂饰片的实际表面关系拆分映射区域，限制法线偏移与三角形外推，并检查动态重建的可见裙片与身体。缩小模拟顶点数或增加身体胶囊不能代替这些检查。
