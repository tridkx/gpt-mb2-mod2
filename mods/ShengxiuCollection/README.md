# Shengxiu Collection v1.1.6（明玉头颈随动与后发间距测试候选）

圣绣明玉、白凤（女）、素问三套装备，统一运行于 ShengxiuCollection，管理器显示 Shengxiu Collection。每套三件：发容、衣裙与手饰、腿部与绣鞋。

## 安装与穿戴

Mod ZIP 的 ShengxiuCollection/ 放入游戏 Modules，启用合集后搜索相应中文套装名。同套三件一起穿戴，手套和披肩槽留空。依赖 Native、SandBoxCore、Sandbox。

## 工程结构

| 套装 | 工程 | 资源包 |
| --- | --- | --- |
| 明玉 | 本工程 input/source/tex/tools | sx_mingyu.tpac |
| [白凤（女）](sets/02_Baifeng/README.md) | sets/02_Baifeng/ | sx_baifeng.tpac |
| [素问](sets/03_Suwen/README.md) | sets/03_Suwen/ | sx_suwen.tpac |

每套保留原始输入和贴图，source/ 与 tex/ 相邻；build/ 保存独立缓存，reports/ 保存最终回读和预览。资源名、GUID、骨骼参数及材料按套装独立配置。

## 当前模型与布料

明玉 LOD0 包含长发、裙摆和袖纱布料，LOD1 仅袖纱，LOD2/3 使用蒙皮。脸、眼、头饰与发根采用颈骨 85%／头骨 15% 的统一随动，减小本套模型在原生待机中的过度前倾；颈部皮肤在静态 z=1.425–1.515m 之间由上胸骨平滑过渡到相同头部变换，颈口共享顶点的量化权重一致。脸、下颌和眼睛保持相同变换，静态脸形不变。

后发下段相对 v1.1.5 向身体收回 25–45mm：最低发梢留有待机摆动余量，主体收回最多 45mm，收回量在 z=1.26–1.48m 间淡出，避开头颈新随动影响较大的上端；保留原后发下段逐渐随 spine2 的设置。后发活动距离上限为 8mm（量化后约 7.8mm），前发沿用原 Alpha，仍保留布料模拟。更新后的可编辑 Blend/FBX 生成头部和颈部皮肤四级 LOD，并按新几何、权重重新编译长发布料。

身体 MetaMesh 引用已获裙子修复反馈的 sx_mingyu_leg_collision，四个腿部胶囊及身体引用保持 v1.1.2 设置。头部引用 sx_mingyu_back_collision，含三个竖向背部胶囊，端点分别随 spine、spine2 运动；边界位于拟合背面外侧 2mm，上端中心降至 z=1.27m，避开发根、领口和胸前，不恢复原生全身碰撞体。袖纱与衣裙共享腿部碰撞引用。白凤、素问资源包保持 v1.1.0 字节，在 LOD0/1 包含自有布料预处理数据，LOD2/3 使用蒙皮。

白凤、素问按各自坐标轴、材质槽和解剖标记适配原生 28 骨；肩口保留手臂权重，垂带使用自身躯干锚点，白凤肩羽跟随上臂。头部随动采用颈骨 70%／头骨 30%，脸、眼、头发与头饰同步；权重渐变限于颈环。套装具体配置见上表工程链接。

共用布料编译器使用三角网格约束网络，固定根部和额外固定点见各工程 tools/cloth_policy.json 与 reports/cooked_cloth_validation.json。

## 验证状态与限制

当前候选检查见 [head_neck_validation.json](reports/head_neck_validation.json)，源文件检查见 [source_validation.json](reports/source_validation.json)。从最终 TPAC 回读全部四级 LOD，检查脸、眼、饰物的统一变换、颈口位置与量化权重、长发布料的位置/骨骼/映射/约束，以及完整待机、跑步、持弓和骑乘周期的后发三角面间距。后发检查的范围与取样方法继承 v1.1.5，具体最小间距和帧数见当前报告。

其余 28 个网格元数据与几何、衣裙袖纱三段布料与编辑器数据、自有碰撞 XML、白凤素问包均保持 v1.1.5 字节。此版改变的是头部与颈部皮肤随动、后发间距；原生骨架和动画不变。相同待机姿态的前后近景见 [原颈部](reports/head_neck_before_idle_neck.png)、[新颈部](reports/head_neck_after_idle_neck.png)、[新后发侧面](reports/head_neck_after_idle_side.png)。这些预览没有运行游戏布料求解器。

用户已确认此前自然下垂与裙子穿腿修复，随后反馈 v1.1.5 后发间距过大、头部前倾和颈部折叠。v1.1.6 尚待游戏确认头颈外观、后发贴背程度与站立/跑步穿模；不同体型、武器、IK、远距离布料和其它套装仍不属于本次离线检查的游戏验收范围。

## 重建与交付

白凤、素问在工作区根运行：

```powershell
python -X utf8 mods/ShengxiuCollection/tools/build_new_sets.py
# 可用 --set 02_Baifeng 或 --set 03_Suwen 选择一套
# prepare_collection_release.py 为 v1.1.0 基线组装入口，会要求旧明玉哈希。
```

当前 v1.1.6 候选从保留的 v1.1.5 源文件和包增量生成，在工作区根依次运行：

```powershell
& 'D:/Blender Foundation/Blender 5.2/blender.exe' --background --python-exit-code 1 --python mods/ShengxiuCollection/tools/fit_head_neck_source.py
& 'D:/Blender Foundation/Blender 5.2/blender.exe' --background --python-exit-code 1 --python mods/ShengxiuCollection/tools/export_geometry.py
& 'D:/Blender Foundation/Blender 5.2/blender.exe' --background --python-exit-code 1 --python mods/ShengxiuCollection/tools/verify_source.py
dotnet build mods/ShengxiuCollection/tools/HeadNeckGeometry.csproj -o mods/ShengxiuCollection/build/head_neck_geometry
python -X utf8 mods/ShengxiuCollection/tools/prepare_head_neck.py
python -X utf8 mods/ShengxiuCollection/tools/verify_head_neck.py
& 'D:/Blender Foundation/Blender 5.2/blender.exe' --background --python-exit-code 1 --python mods/ShengxiuCollection/tools/render_head_neck.py
python -X utf8 mods/ShengxiuCollection/tools/finalize_head_neck.py
./tools/install_release.ps1 -Mod ShengxiuCollection -Version v1.1.6 -PreviousVersion v1.1.5
```

增量基线缓存为 build/head_neck_baseline_v1.1.5/，包括 TPAC、Blend/FBX、rig_arrays.npz 与 rig_manifest.json；后发的原始部位分类还读取 v1.1.4 缓存。首次重建需从保留的回退包和历史模型流程恢复这些基线。当前构建、验证与渲染入口复用 tools/prepare_hair_shape.py、verify_hair_shape.py、render_hair_fit.py 的流程，并明确覆盖版本、输出目录与本次头颈范围。构建需要既有 build/spec.json、模板和 cloth_probe、cloth_patch；渲染需要 v1.1.5 回读与已解码贴图缓存。

仅移植头部和颈部皮肤的四级流，衣裙与材料不采用完整重建包的数据。实际安装需退出游戏与启动器，旧交付包自动保留。依赖本机 Blender、Python、mbtool、原生资源和工作区 asset_helpers；源 ZIP 保持 source/、tex/ 相邻，并附带 workspace_tools/cloth_compiler/。

## 注意事项

- 每套材质槽与坐标方向从真实面片和源模型读取，不能按首个材质槽或预览方向猜测。
- 脸部权重渐变只覆盖颈环，不能延伸到下颌；最终检查须覆盖脸部与眼球各级量化权重。
- 活动 Alpha、模拟标记和材料参数存在，不代表布料数据完整或游戏求解生效；检查方法见 [共用编译器](../../tools/cloth_compiler/README.md)。

历史版本与调查见 [更新日志](CHANGELOG.md)。
