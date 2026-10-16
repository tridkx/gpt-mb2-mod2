# Shengxiu Collection v1.1.7（明玉长发布料）

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

后发基础造型按衣服背面平滑收拢，主体参考间距约 24mm，保留发束的前后层次；后颈隆起局部收回最多 45mm，在 z=1.32–1.59m 内平滑淡入淡出，固定头皮和下段主体不受此局部调整影响。下段蒙皮参考按高度平滑跟随对应躯干部位。布料的蒙皮位置仅作为活动范围中心，实际长发可在重力、约束和碰撞下离开该位置。后发活动距离从固定头皮逐渐增加，发尾最大 200mm；前侧发束保留原活动距离，原头皮零距离固定点不变。弯曲刚度为 0.18，重力为 7，拉伸与锚点刚度保持 1，阻尼保持 0.48。LOD0 按新几何、权重和 Alpha 重新编译长发布料，LOD1–3 仍为蒙皮。

头部引用自有 sx_mingyu_back_collision：28 个重叠胶囊覆盖后腰到上背，端点按模型对应高度的躯干权重随动；靠近上端逐渐缩小半径，避免挤压前侧发束和发根。碰撞表面按衣服背面拟合，轻微局部交叉以不影响整体观感为准，不以继续外移整片头发作为消除穿模的手段。

身体 MetaMesh 引用已获裙子修复反馈的 sx_mingyu_leg_collision，四个腿部胶囊、身体引用和衣裙袖纱布料保持原设置。白凤、素问资源包保持 v1.1.0 字节，在 LOD0/1 包含自有布料预处理数据，LOD2/3 使用蒙皮。

白凤、素问按各自坐标轴、材质槽和解剖标记适配原生 28 骨；肩口保留手臂权重，垂带使用自身躯干锚点，白凤肩羽跟随上臂。头部随动采用颈骨 70%／头骨 30%，脸、眼、头发与头饰同步；权重渐变限于颈环。套装具体配置见上表工程链接。

共用布料编译器使用三角网格约束网络，固定根部和额外固定点见各工程 tools/cloth_policy.json 与 reports/cooked_cloth_validation.json。

## 验证状态与限制

当前版本检查见 [back_hair_validation.json](reports/back_hair_validation.json)，源文件检查见 [source_validation.json](reports/source_validation.json)。最终 TPAC 回读覆盖全部四级 LOD、完整待机/跑步/持弓/骑乘周期中的后发蒙皮参考间距，以及长发布料位置、量化权重、映射、固定点和并行约束。其余 52 个网格的元数据与几何、衣裙袖纱三段布料及编辑器数据保持 v1.1.6 字节；头颈、脸、眼、饰物、原生骨架和动画不变，裙子腿部碰撞体不变。

[free_hair_diagnostic.json](reports/free_hair_diagnostic.json) 另记录七个静态原生姿态的近似 CPU 重力与胶囊约束诊断：每个姿态以 120Hz 松弛 3 秒，核对发根不漂移、活动距离与碰撞的冲突、后发下落和局部穿模。它没有运行游戏求解器或连续动画惯性，不能代替游戏测试。模型参考前后侧面见 [原后发](reports/back_hair_before_idle_side.png)、[新参考造型](reports/back_hair_after_idle_side.png)；近似重力诊断图见 [侧面](reports/back_hair_gravity_idle_side.png)、[背面](reports/back_hair_gravity_idle_back.png)。

用户已确认 v1.1.7 的头发整体效果可接受，此前裙子修复也已确认；整体观感和自然下垂优先，允许轻微局部穿模。这些反馈不涵盖全部动作、不同体型、武器、IK、远距离布料和其它套装。助手未启动游戏。战斗结束后物品界面的崩溃检查见 [2026-10-10 检查报告](reports/inventory_crash_20261010.md)，两份转储均直接指向 TroopDesigner 搜索功能的空引用异常。

## 重建与交付

白凤、素问在工作区根运行：

```powershell
python -X utf8 mods/ShengxiuCollection/tools/build_new_sets.py
# 可用 --set 02_Baifeng 或 --set 03_Suwen 选择一套
# prepare_collection_release.py 为 v1.1.0 基线组装入口，会要求旧明玉哈希。
```

当前 v1.1.7 从保留的 v1.1.6 源文件和包增量生成，在工作区根依次运行：

```powershell
& 'D:/Blender Foundation/Blender 5.2/blender.exe' --background --python-exit-code 1 --python mods/ShengxiuCollection/tools/fit_back_hair_source.py
python -X utf8 mods/ShengxiuCollection/tools/fit_free_hair_collision.py
& 'D:/Blender Foundation/Blender 5.2/blender.exe' --background --python-exit-code 1 --python mods/ShengxiuCollection/tools/export_geometry.py
& 'D:/Blender Foundation/Blender 5.2/blender.exe' --background --python-exit-code 1 --python mods/ShengxiuCollection/tools/verify_source.py
dotnet build mods/ShengxiuCollection/tools/BackHairGeometry.csproj -o mods/ShengxiuCollection/build/back_hair_geometry
python -X utf8 mods/ShengxiuCollection/tools/prepare_back_hair.py
python -X utf8 mods/ShengxiuCollection/tools/verify_back_hair.py
python -X utf8 mods/ShengxiuCollection/tools/diagnose_free_hair.py
& 'D:/Blender Foundation/Blender 5.2/blender.exe' --background --python-exit-code 1 --python mods/ShengxiuCollection/tools/render_back_hair.py
python -X utf8 mods/ShengxiuCollection/tools/finalize_back_hair.py
./tools/install_release.ps1 -Mod ShengxiuCollection -Version v1.1.7 -PreviousVersion v1.1.6
```

增量基线缓存为 build/back_hair_baseline_v1.1.6/，包括 TPAC、Blend/FBX、rig_arrays.npz、rig_manifest.json 和 cloth_bodies.xml；后发布位分类读取 v1.1.4 原始坐标缓存，衣服拟合读取 v1.1.6 最终回读几何。这些是当前增量流程实际读取的必要输入，不能作为普通缓存删除。当前没有已验证的 input/model.fbx 到 v1.1.7 完整冷启动入口，也不能用当前最新版源文件重新初始化旧版基线。构建需要既有 build/spec.json、模板及 cloth_probe、cloth_patch；入口复用 prepare_hair_shape.py、verify_hair_shape.py、render_hair_fit.py，并覆盖版本、输出目录和检查范围。预览需要已解码的贴图缓存。 当前明玉 build/ 保留完整；其中部分必要输入被 Git 忽略，普通推送不会备份它们，详细边界见[重建输入与构建缓存](../../docs/rebuild-and-cleanup.md)。

仅移植长发四级流，并修改 LOD0 长发弯曲参数和自有背部碰撞 XML。实际安装需退出游戏与启动器，旧交付包自动保留。依赖本机 Blender、Python、mbtool、原生资源和工作区 asset_helpers；源 ZIP 保持 source/、tex/ 相邻，并附带 workspace_tools/cloth_compiler/。

## 注意事项

- 每套材质槽与坐标方向从真实面片和源模型读取，不能按首个材质槽或预览方向猜测。
- 脸部权重渐变只覆盖颈环，不能延伸到下颌；最终检查须覆盖脸部与眼球各级量化权重。
- 活动 Alpha、模拟标记和材料参数存在，不代表布料数据完整或游戏求解生效；检查方法见 [共用编译器](../../tools/cloth_compiler/README.md)。

历史版本与调查见 [更新日志](CHANGELOG.md)。

## 常见问题

### 后发被顶起、远离身体或后颈外折

先比较源造型、原生待机蒙皮参考和近似重力结果。活动 Alpha 是相对蒙皮位置的移动上限，范围过小会限制下垂；碰撞体则应贴合外层衣服，检查覆盖、端帽和上端半径。当前模型的后颈平滑处理见 [源造型脚本](tools/fit_back_hair_source.py)，背部胶囊拟合见 [碰撞脚本](tools/fit_free_hair_collision.py)。上述数值只适用于明玉；返修须保留已确认的裙子配置，以自然观感为准接受轻微交叉。修改源几何、权重或 Alpha 后需重新编译受影响布料，而非只修改碰撞 XML。

### 战斗结束后进入物品界面崩溃

先核对同次日志、进程和转储，确认崩溃发生阶段。当前两份转储指向 TroopDesigner 搜索功能的空引用，详细证据与修复建议见 [检查报告](reports/inventory_crash_20261010.md)。该外部 Mod 尚未修改或验证修复，不以回退明玉布料代替处理实际异常。
