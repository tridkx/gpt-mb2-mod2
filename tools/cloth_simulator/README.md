# 骑砍 2 离线布料诊断器

读取最终 TPAC 的直接布料预处理数据，用 CPU PBD 近似求解，输出整段动作指标、数值轨迹、最差帧和可双击打开的离线 HTML 回放。用于助手自动筛查和比较候选参数，减少游戏调参次数。当前是诊断原型，未校准到游戏结果，不代替游戏验收。

## 实现与依赖

- `run.py`：只读提取最终包、原生动画/骨架驱动、检查和输出。
- `solver.py`：重力、速度保留、分组长度约束、测地锚点、活动球、胶囊投影、四个面内部辅助碰撞采样。固定点保持蒙皮参考位置。
- `viewer.html`：本地 Canvas 回放，无 CDN、网络依赖或服务器需求；支持正侧背面、拖动旋转、蒙皮参考和碰撞体显示。
- `demo.py`：无需游戏文件的程序布片示例。
- `test_solver.py`：重力、移动固定点、确定性、刚度、轴线上碰撞、不可满足碰撞和三角形内部接触检查。

Python 需要 NumPy、SciPy（示例和现有编译器）、Matplotlib。本机使用 `C:/ProgramData/anaconda3/python.exe`。提取 TPAC 使用现有[布料编译工具](../cloth_compiler/README.md)的 `NativeClothProbe.dll`、.NET 10 和 `mbtool.dll`；模拟本身无需 Blender、编辑器或游戏进程。源代码放共用工具，模型参数留在对应模组 `tools/`，正式模组检查输出留在该模组 `build/` 或 `reports/`。

## 快速开始

从工作区根运行（完整路径与本机命令示例）：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -X utf8 tools/cloth_simulator/test_solver.py
& 'C:/ProgramData/anaconda3/python.exe' -X utf8 tools/cloth_simulator/demo.py --output build/cloth_simulator/demo
```

双击 `build/cloth_simulator/demo/result/replay.html`。重复运行需选择新的输出目录，以保留上次结果。

## 检查最终游戏资源

1. 用现有 `NativeClothProbe` 提取最终 TPAC；不得把编译前的网格当作最终包检查。可以使用目标模组已构建的 Probe DLL，也可按编译器说明将新构建输出放该模组 `build/`。
2. 根据提取的 `*.mesh.json` 中 `name` 选择子网格，配对同名 `.bin`。每个子网格与 LOD 分别运行。
3. 使用对应角色骨架、原生动作和碰撞体 XML。显式提供动画采样率与最终网格距离倍率。提取的 `package.json` 会记录原包哈希、网格元数据、材质和导出文件哈希；模拟时验证提取文件及倍率。

月清疏的命令示例（只读该模组，工具试跑输出在工作区根缓存）：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -X utf8 tools/cloth_simulator/run.py extract --tpac mods/Xianjian7Race/YueQingShuRace/module/YueQingShuRace/AssetPackages/yqs.tpac --metamesh yqs_body --probe mods/Xianjian7Race/YueQingShuRace/build/cloth_probe/NativeClothProbe.dll --output build/cloth_simulator/yqs_final

& 'C:/ProgramData/anaconda3/python.exe' -X utf8 tools/cloth_simulator/run.py simulate --payload build/cloth_simulator/yqs_final/yqs_body_1386cdce-ee2a-62b7-d17c-00cc0e15cd4d.bin --mesh build/cloth_simulator/yqs_final/yqs_body_1386cdce-ee2a-62b7-d17c-00cc0e15cd4d.mesh.json --skeleton mods/Xianjian7Race/YueQingShuRace/reports/final_skeleton.json --animation mods/Xianjian7Race/YueQingShuRace/reports/run.json --capsules mods/Xianjian7Race/YueQingShuRace/module/YueQingShuRace/ModuleData/cloth_bodies.xml --body yqs_collision --fps 60 --multiplier 1 --output build/cloth_simulator/yqs_run
```

该 GUID 只用于此网格示例；新模型从自己的导出列表选择。`60 fps` 是本次诊断假定的采样速度，尚未对齐游戏动作播放时长，不能作为游戏的通用帧率。`--start`/`--end` 是原生源帧区间，结束帧不包含；自动跳过已有动画读取器识别的绑定姿势帧。默认保持首姿势预热 30 帧，再播放一次动作。未循环拼接、插值成更多源动作帧或包含游戏动作混合。

`--capsules` 当前读取本工作区自制碰撞体的 frame 约定：行主序，第一行的 XYZ 为长度方向，第四行的 XYZ 为首端点；端点在绑定空间通过自身骨骼权重随动。未知骨名或无效权重报错。此约定未验证所有原生 body 资源。变半径胶囊使用沿轴线线性插值半径的近似，未严格复现游戏 cone 投影。

其他动画系统可以提供 `--motion <文件.npz>`：`anchors` 为 `[帧数,模拟顶点数,3]`，可选 `capsules` 为 `[帧数,胶囊数,2,4]`，每端点是 `x,y,z,radius`。坐标统一为米、Z 向上，同一局部空间；顶点顺序必须对应布料 blob 中的模拟顶点顺序，不能直接使用渲染网格顺序。NPZ 模式不同时使用骨架/动画/XML 参数。未提供碰撞体时状态为 `incomplete`。

## 输出与判读

| 输出 | 用途 |
| --- | --- |
| `report.json` | 输入 SHA256、参数、检查范围、逐帧指标、最大值、原生最差帧编号 |
| `frames.npz` | 全部帧的模拟位置、蒙皮参考、胶囊、模拟三角形和顶点穿透深度 |
| `replay.html` | 离线回放；大网格抽样回放，保留穿透/拉伸最差帧；数值报告始终检查所有源帧 |
| `worst_frame.png` | 顶点/面内部采样穿透最差帧的正侧面 |
| `worst_stretch.png` | 最大相对拉伸偏差帧的正侧面 |

退出码 `0` / `within_thresholds`：当前代理检查在指定阈值内。退出码 `1` / `needs_review`：模拟顶点或面内部采样穿透超过默认 2 mm，或抗拉约束相对长度偏差超过默认 25%。退出码 `2`：输入错误、工具失败或缺少碰撞体。报告固定保存 `game_solver_used=false`、`game_verified=false`。

同时查看相对误差、绝对长度误差和最差帧。极短约束的相对误差会放大位置量化影响，不能只按百分比判断可见破坏。`fixed_penetration_m` 是信息指标：固定区域可能有意在碰撞体内部，不参与通过阈值。橙色点只显示模拟顶点接触残留；面内部采样风险另看指标。胶囊图只画轴线和端点球，不代表完整三维轮廓。

## 与游戏求解器的差异

本机 `Shaders/Sources/gpucloth_solver.rs` 提供了积分、活动距离、锚点、分组约束和碰撞的求解顺序，可作为对齐参考。本实现并非该源码的完整移植，也不复制分发游戏文件。公式与输入语义参照[官方布料说明](https://moddocs.bannerlord.com/editor/resource-editors/cloth_simulation/)。

当前明确差异：

- CPU float64 中间计算，保存 float32 轨迹；未复现 GPU 位置压缩、并行执行和完整拼接约束第二遍处理。
- 硬固定点不参与约束移动，每次迭代最后收紧活动球；游戏着色器在约束/碰撞之前限制活动距离，边界点处理也不同。
- `--stretch`、`--shear`、`--bend`、`--anchor`、`--damping` 是诊断参数。报告记录原游戏材质，但尚未确认 CPU 端系数转换，不能直接认定两者一一对应。
- 当前动作采用现有离线关键帧采样与子步间线性位置插值，未对齐游戏动画混合、变体、体型、移动惯性、风、瞬移/LOD 重置。
- 只支持直接模拟及完整模拟顶点映射；没有代理映射布料、马匹/真实身体三角面碰撞、连续碰撞和自碰撞。
- 四点面内部采样会漏掉其他位置的接触，胶囊也不能覆盖真实人体全部形状。通过结果只覆盖当前输入代理和阈值。

要进一步对齐，需要核对游戏 CPU 准备的时间步/材质/惯性参数、严格复现碰撞和压缩分支，并使用同一资源、动作、播放速度的游戏参考轨迹衡量误差。截图可比较外观，但不足以证明逐顶点或逐帧一致。当前离线效果自然或指标通过，都不能证明游戏引擎已经启动布料求解或在远距离仍然求解。

## 当前验证范围

实现验证及带日期的原包试跑记录见[2026-10-13 检查报告](reports/2026-10-13-validation.json)。这些是工具检查，不更改任何模组的游戏验收状态。此工具不生成或安装新的模组包。
