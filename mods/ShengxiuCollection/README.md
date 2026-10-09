# Shengxiu Collection v1.1.4（明玉长发活动距离测试候选）

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

明玉 LOD0 包含长发、裙摆和袖纱布料，LOD1 仅袖纱，LOD2/3 使用蒙皮。当前候选保留全部几何、蒙皮、渲染 Alpha、材料和布料约束，固定发根不变，仅调整长发求解数据的活动距离：活动点至少取原距离三倍，并覆盖站立、跑步胶囊投影所需距离加 5mm 余量，当前最大约 7.1cm。此覆盖保存在 tools/hair_clearance_policy.json 和生成脚本中，不改 Blend/FBX 的原始 Alpha 绘制。

身体 MetaMesh 引用已获裙子修复反馈的 sx_mingyu_leg_collision，四个腿部胶囊及身体引用保持 v1.1.2 设置。头部引用 sx_mingyu_back_collision，含三个竖向背部胶囊，端点分别随 spine、spine2 运动；边界位于拟合背面外侧 2mm，上端中心降至 z=1.27m，避开发根、领口和胸前，不恢复原生全身碰撞体。袖纱与衣裙共享腿部碰撞引用。白凤、素问资源包保持 v1.1.0 字节，在 LOD0/1 包含自有布料预处理数据，LOD2/3 使用蒙皮。

白凤、素问按各自坐标轴、材质槽和解剖标记适配原生 28 骨；肩口保留手臂权重，垂带使用自身躯干锚点，白凤肩羽跟随上臂。头部随动采用颈骨 70%／头骨 30%，脸、眼、头发与头饰同步；权重渐变限于颈环。套装具体配置见上表工程链接。

共用布料编译器使用三角网格约束网络，固定根部和额外固定点见各工程 tools/cloth_policy.json 与 reports/cooked_cloth_validation.json。

## 验证状态与限制

当前候选检查见 [hair_clearance_validation.json](reports/hair_clearance_validation.json)，背部拟合见 [hair_clearance_fit.json](reports/hair_clearance_fit.json)。腿部拟合记录见 [leg_collision_fit.json](reports/leg_collision_fit.json)。候选相对 v1.1.3 回读确认 56 个网格元数据、几何哈希、全部编辑器数据和其余三段布料不变；长发布料段仅 max_distances 数组改变。原腿部碰撞定义逐项不变。v1.1.0 的完整静态检查记录见 [collection_release_validation.json](reports/collection_release_validation.json)，其包哈希适用于历史基线。

最终 TPAC 已回读检查所有四级 LOD、28 骨索引与权重、皮肤接缝、全部贴图 mip、布料映射/骨骼/约束/锚点及并行分组。站立抽查 16 帧，跑步完整 25 帧、拉弓 150 帧、骑乘 20 帧。活动布料的离线蒙皮拉伸仅记录为诊断，因为预览未运行游戏布料求解器；固定皮肤和连接处另做拉伸检查。原生腿部胶囊接触只是诊断，不代表已消除所有裙摆穿模。鞋底用各套原始鞋子单独拟合，低处鞋长约 24.5cm、最低鞋底为 z=1mm。

用户确认 v1.1.1 恢复自然下垂，v1.1.2 修复所反馈的裙子穿腿问题；v1.1.3 站立自然下垂但长发仍穿模，v1.1.4 也未修复长发问题。当前已安装包与工程包、碰撞 XML 哈希一致。活动距离不足不能认定为实际根因，需结合当前跑动的背面/侧面画面继续检查受影响发束、完整求解约束与头盔槽资源的运行时碰撞行为。站立和完整 25 帧跑步的活动发点碰撞投影虽均在新距离预算内，但这仅是投影可达性检查，不是游戏布料求解通过。站立最大投影上推约 2.6mm。反馈不覆盖所有动作、距离和体型；明玉 LOD1、远距离和全部动作范围未确认。白凤、素问尚待游戏验收。离线预览不运行游戏布料求解器、武器 IK 或真实马体碰撞，代理接触仅为诊断。

## 重建与交付

白凤、素问在工作区根运行：

```powershell
python -X utf8 mods/ShengxiuCollection/tools/build_new_sets.py
# 可用 --set 02_Baifeng 或 --set 03_Suwen 选择一套
# prepare_collection_release.py 为 v1.1.0 基线组装入口，会要求旧明玉哈希。
```

当前 v1.1.4 候选从保留的 v1.1.3 明玉包增量生成，在工作区根运行：

```powershell
dotnet build mods/ShengxiuCollection/tools/ClothPatch.csproj -o mods/ShengxiuCollection/build/cloth_patch
python -X utf8 mods/ShengxiuCollection/tools/prepare_hair_clearance.py
./tools/install_release.ps1 -Mod ShengxiuCollection -Version v1.1.4 -PreviousVersion v1.1.3
```

增量基线缓存为 build/hair_clearance_baseline_v1.1.3/，保留明玉 TPAC 与 cloth_bodies.xml；缺失时可从保留的 v1.1.3 Mod ZIP 提取，脚本核对固定哈希。拟合读取 build/final_export/geo 的明玉静态几何（与已回读确认不变的运行包一致）。prepare_hair_clearance.py 调用背部拟合，再单独替换长发求解数据，不重新生成其它布料。实际安装需退出游戏与启动器，保留被替换交付包。依赖本机 Blender、Python、mbtool、原生资源和工作区 asset_helpers。源 ZIP 保持 source/、tex/ 相邻，并附带 workspace_tools/cloth_compiler/。

明玉完整几何与布料基线的重建流程、旧版验证断言见更新日志；原有 build_package.py 和 prepare_collection_release.py 生成 v1.1.0 基线设置。当前候选使用上面的增量入口，不将旧版碰撞体断言当成候选验收依据。

## 注意事项

- 每套材质槽与坐标方向从真实面片和源模型读取，不能按首个材质槽或预览方向猜测。
- 脸部权重渐变只覆盖颈环，不能延伸到下颌；最终检查须覆盖脸部与眼球各级量化权重。
- 活动 Alpha、模拟标记和材料参数存在，不代表布料数据完整或游戏求解生效；检查方法见 [共用编译器](../../tools/cloth_compiler/README.md)。

历史版本与调查见 [更新日志](CHANGELOG.md)。
