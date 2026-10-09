# Shengxiu Collection v1.1.5（明玉后发造型与绑骨测试候选）

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

明玉 LOD0 包含长发、裙摆和袖纱布料，LOD1 仅袖纱，LOD2/3 使用蒙皮。后发按本套衣服背面重新留出间距，变形只沿后颈到下段平滑展开；头顶发根、脸、眼睛、头饰与正前方发束保持原样。后发下段的上身权重逐渐增加至 spine2 98%，上端仍随头部，避免整片长发随头骨前倾而切入后背。后发活动距离上限为 12mm（量化后约 11.8mm），保留布料；前发沿用原 Alpha。四级长发 LOD 与 LOD0 预处理数据均由更新后的可编辑 Blend/FBX 生成。

身体 MetaMesh 引用已获裙子修复反馈的 sx_mingyu_leg_collision，四个腿部胶囊及身体引用保持 v1.1.2 设置。头部引用 sx_mingyu_back_collision，含三个竖向背部胶囊，端点分别随 spine、spine2 运动；边界位于拟合背面外侧 2mm，上端中心降至 z=1.27m，避开发根、领口和胸前，不恢复原生全身碰撞体。袖纱与衣裙共享腿部碰撞引用。白凤、素问资源包保持 v1.1.0 字节，在 LOD0/1 包含自有布料预处理数据，LOD2/3 使用蒙皮。

白凤、素问按各自坐标轴、材质槽和解剖标记适配原生 28 骨；肩口保留手臂权重，垂带使用自身躯干锚点，白凤肩羽跟随上臂。头部随动采用颈骨 70%／头骨 30%，脸、眼、头发与头饰同步；权重渐变限于颈环。套装具体配置见上表工程链接。

共用布料编译器使用三角网格约束网络，固定根部和额外固定点见各工程 tools/cloth_policy.json 与 reports/cooked_cloth_validation.json。

## 验证状态与限制

当前候选检查见 [hair_shape_validation.json](reports/hair_shape_validation.json)，造型参数和源文件检查见 [hair_source_fit.json](reports/hair_source_fit.json)、[source_validation.json](reports/source_validation.json)。从最终 TPAC 回读全部四级 LOD，核对长发布料的位置、骨骼、映射、约束和并行分组；其余 52 个网格元数据与几何、衣裙袖纱的预处理和编辑器数据、碰撞 XML 保持 v1.1.4 字节。白凤、素问包哈希不变。v1.1.0 的完整基线检查另见 [collection_release_validation.json](reports/collection_release_validation.json)，不作为当前包哈希依据。

对原生待机、跑步、持弓与骑乘从第 1 帧起的完整周期，检查后发顶点、面片中心和边中点与实际躯干三角面。检查限定原始后发 Y<-25mm、Z<1.50m；在上胸骨动画局部坐标沿前后方向投射，排除袖纱外侧与低处裙摆。各级 LOD 的具体最小间距和帧数见候选报告。这项检查证明所查蒙皮姿态与躯干的间距，不能代替游戏布料求解、不同体型、武器碰撞或 IK。源包中保留旧版原生姿态报告作为历史参考。

用户确认自然下垂和裙子穿腿问题已修复，但 v1.1.4 整片后发在待机站立时仍穿衣。相同姿态的最终包预览复现了旧版后发进入背部，新候选后发位于衣服外侧，见 [修复前侧面](reports/hair_before_idle_side.png)、[修复后侧面](reports/hair_after_idle_side.png)、[修复后背面](reports/hair_after_idle_back.png)。预览未运行游戏布料求解器。v1.1.5 尚待用户确认站立、跑步的后发位置与自然摆动；白凤、素问和明玉远距离布料仍待游戏验收。

## 重建与交付

白凤、素问在工作区根运行：

```powershell
python -X utf8 mods/ShengxiuCollection/tools/build_new_sets.py
# 可用 --set 02_Baifeng 或 --set 03_Suwen 选择一套
# prepare_collection_release.py 为 v1.1.0 基线组装入口，会要求旧明玉哈希。
```

当前 v1.1.5 候选从保留的 v1.1.4 源文件和包增量生成，在工作区根依次运行：

```powershell
& 'D:/Blender Foundation/Blender 5.2/blender.exe' --background --python-exit-code 1 --python mods/ShengxiuCollection/tools/fit_hair_source.py
& 'D:/Blender Foundation/Blender 5.2/blender.exe' --background --python-exit-code 1 --python mods/ShengxiuCollection/tools/export_geometry.py
& 'D:/Blender Foundation/Blender 5.2/blender.exe' --background --python-exit-code 1 --python mods/ShengxiuCollection/tools/verify_source.py
dotnet build mods/ShengxiuCollection/tools/HairGeometry.csproj -o mods/ShengxiuCollection/build/hair_geometry
python -X utf8 mods/ShengxiuCollection/tools/prepare_hair_shape.py
python -X utf8 mods/ShengxiuCollection/tools/verify_hair_shape.py
& 'D:/Blender Foundation/Blender 5.2/blender.exe' --background --python-exit-code 1 --python mods/ShengxiuCollection/tools/render_hair_fit.py
python -X utf8 mods/ShengxiuCollection/tools/finalize_hair_shape.py
./tools/install_release.ps1 -Mod ShengxiuCollection -Version v1.1.5 -PreviousVersion v1.1.4
```

增量基线缓存为 build/hair_shape_baseline_v1.1.4/，包括 TPAC、Blend/FBX、rig_arrays.npz 和 rig_manifest.json；脚本核对旧包哈希。首次重建需从 v1.1.4 Mod/Source 回退包和旧版模型流程恢复这些基线。prepare_hair_shape.py 使用既有 build/spec.json、本机模板和编译好的 cloth_probe、cloth_patch；完整基线流程见历史更新日志。候选只移植重新生成的四个长发流并编译长发，不采用完整重建包的衣裙或材料数据。render_hair_fit.py 使用保留的旧版 final_export/geo、贴图解码缓存和新候选回读数据做相同视角对比。

实际安装需退出游戏与启动器，旧交付包自动保留。依赖本机 Blender、Python、mbtool、原生资源和工作区 asset_helpers；源 ZIP 保持 source/、tex/ 相邻，并附带 workspace_tools/cloth_compiler/。

## 注意事项

- 每套材质槽与坐标方向从真实面片和源模型读取，不能按首个材质槽或预览方向猜测。
- 脸部权重渐变只覆盖颈环，不能延伸到下颌；最终检查须覆盖脸部与眼球各级量化权重。
- 活动 Alpha、模拟标记和材料参数存在，不代表布料数据完整或游戏求解生效；检查方法见 [共用编译器](../../tools/cloth_compiler/README.md)。

历史版本与调查见 [更新日志](CHANGELOG.md)。
