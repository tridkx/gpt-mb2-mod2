# Shengxiu Collection v1.1.1（明玉碰撞隔离测试候选）

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

明玉 LOD0 包含长发、裙摆和袖纱布料，LOD1 仅袖纱，LOD2/3 使用蒙皮。当前候选保留全部几何、蒙皮、布料预处理和材料参数，仅将明玉头部、身体 MetaMesh 的人体碰撞体引用清空，以验证头发、裙摆上提是否来自原生 human_body 的碰撞推开。此设置也会影响袖纱的人体碰撞，可能增加穿模；确认原因后再决定适配碰撞体的最终方案。白凤、素问资源包保持 v1.1.0 字节，在 LOD0/1 包含自有布料预处理数据，LOD2/3 使用蒙皮。

白凤、素问按各自坐标轴、材质槽和解剖标记适配原生 28 骨；肩口保留手臂权重，垂带使用自身躯干锚点，白凤肩羽跟随上臂。头部随动采用颈骨 70%／头骨 30%，脸、眼、头发与头饰同步；权重渐变限于颈环。套装具体配置见上表工程链接。

共用布料编译器使用三角网格约束网络，固定根部和额外固定点见各工程 tools/cloth_policy.json 与 reports/cooked_cloth_validation.json。

## 验证状态与限制

当前候选检查见 [collision_candidate_validation.json](reports/collision_candidate_validation.json)。v1.1.0 的完整静态检查记录见 [collection_release_validation.json](reports/collection_release_validation.json)，其明玉包哈希适用于历史基线；候选逐项回读确认 56 个网格元数据、几何哈希、全部 MetaMesh 数据段校验和及四套布料/编辑器数据 SHA256 保持一致，只有两个碰撞体引用改变。

最终 TPAC 已回读检查所有四级 LOD、28 骨索引与权重、皮肤接缝、全部贴图 mip、布料映射/骨骼/约束/锚点及并行分组。站立抽查 16 帧，跑步完整 25 帧、拉弓 150 帧、骑乘 20 帧。活动布料的离线蒙皮拉伸仅记录为诊断，因为预览未运行游戏布料求解器；固定皮肤和连接处另做拉伸检查。原生腿部胶囊接触只是诊断，不代表已消除所有裙摆穿模。鞋底用各套原始鞋子单独拟合，低处鞋长约 24.5cm、最低鞋底为 z=1mm。

用户已反馈明玉引入布料后头发和裙摆上提；当前候选尚待游戏测试，不能认定问题已修复。请先在同一背包站立姿态检查是否自然垂下，再检查跑步和骑乘的穿模。明玉 LOD1、远距离和全部动作范围未确认。白凤、素问尚待游戏验收。离线预览不运行游戏布料求解器、武器 IK 或真实马体碰撞，代理接触仅为诊断。

## 重建与交付

白凤、素问在工作区根运行：

```powershell
python -X utf8 mods/ShengxiuCollection/tools/build_new_sets.py
# 可用 --set 02_Baifeng 或 --set 03_Suwen 选择一套
# prepare_collection_release.py 为 v1.1.0 基线组装入口，会要求旧明玉哈希。
```

当前 v1.1.1 候选从保留的 v1.1.0 明玉包增量生成，在工作区根运行：

```powershell
dotnet build mods/ShengxiuCollection/tools/CollisionIsolation.csproj -o mods/ShengxiuCollection/build/collision_isolation
python -X utf8 mods/ShengxiuCollection/tools/diagnose_cloth_lift.py
python -X utf8 mods/ShengxiuCollection/tools/prepare_collision_candidate.py
./tools/install_release.ps1 -Mod ShengxiuCollection -Version v1.1.1 -PreviousVersion v1.1.0
```

增量基线缓存为 build/collision_baseline_v1.1.0/sx_mingyu.tpac；缺失时可从保留的 v1.1.0 Mod ZIP 提取，脚本核对固定哈希。实际安装需退出游戏与启动器，保留被替换交付包。依赖本机 Blender、Python、mbtool、原生资源和工作区 asset_helpers。源 ZIP 保持 source/、tex/ 相邻，并附带 workspace_tools/cloth_compiler/。

明玉完整几何与布料基线的重建流程、旧版验证断言见更新日志；原有 build_package.py 和 prepare_collection_release.py 生成 v1.1.0 基线设置。当前候选使用上面的增量入口，不将旧版碰撞体断言当成候选验收依据。

## 注意事项

- 每套材质槽与坐标方向从真实面片和源模型读取，不能按首个材质槽或预览方向猜测。
- 脸部权重渐变只覆盖颈环，不能延伸到下颌；最终检查须覆盖脸部与眼球各级量化权重。
- 活动 Alpha、模拟标记和材料参数存在，不代表布料数据完整或游戏求解生效；检查方法见 [共用编译器](../../tools/cloth_compiler/README.md)。

历史版本与调查见 [更新日志](CHANGELOG.md)。
