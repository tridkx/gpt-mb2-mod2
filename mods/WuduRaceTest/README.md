# Wudu Canglan Race Test

v0.2.1 使用 `01苍蓝流苏` 完整角色模型、自定义种族 `wdr_canglan` 和 28 骨骨架，只替换帝国普通新兵 `imperial_recruit`，游戏内名称为“五毒苍蓝新兵”。适用本机 Native v1.4.8。贵族新兵和 2 号模型尚未制作。

## 当前功能与限制

含头饰网格总高 1.45 米，正面朝游戏前方，保持原始头身和四肢比例，种族最小缩放为 1.1。本版沿用已由用户实测到原版成人胸口的尺寸参数；基础模型全部顶点位置与已验收版本一致。

手部通过独立 `hands_mesh` 接入原版手势形变，四级 LOD 各有 26 个通道。手腕重新对齐支点，使用前臂扭转骨到手掌的渐变权重，手部法线平滑处理。游戏中的手势选择、武器接触和腕部效果尚待本版复测。

裙摆、袖片、袖口和头发具有游戏布料活动范围、固定根部、材料及预处理数据；近处 LOD0/1 共 10 组布料，远处 LOD2/3 使用简化蒙皮网格。配置了 12 个随骨骼移动的布料碰撞胶囊。布料运行和穿模程度尚待游戏验证，远处布料不求解。当前固定脸；握持、骑乘 IK、命中和大规模战斗性能尚未验收。

衣服、头发、脸和身体组成种族身体网格，手部单独注册以支持握持形变。防具栏为空，没有添加固有护甲。原兵种等级 6（T1）、技能、武器和升级路线保留，升级后进入原版兵种。

最终 TPAC、权重、四级 LOD、原始形状对照、XML 合并及 Blend/FBX 重开检查通过，源文件保留全部手部形变。原生跑步全周期和站立、持弓、骑乘、挥刀抽样完成蒙皮与布料活动范围检查。这些检查不运行游戏布料求解器。见[资源检查](reports/release_validation.json)、[布料检查](reports/cloth_validation.json)、[手部检查](reports/hand_validation.json)和[手部优化说明](reports/hand_optimization_v0.2.1.md)。

## 游戏测试

1. 启动器勾选 **Wudu Canglan Race Test**，排在 Native、SandBoxCore、Sandbox 之后，避免其他兵种修改模组覆盖该兵种。
2. 招募帝国普通新兵，近距离查看持剑和挥刀时手指是否握住剑柄，手腕扭转是否较平顺；同时观察左手持盾。
3. 条件允许时检查持弓、骑乘等不同手势。重点记录武器类型、左右手以及发生问题的动作。
4. 检查跑步、停止时袖口和裙摆是否正常，并检查远近切换中的手部表现。
5. 诊断日志位于系统“文档”下 `Mount and Blade II Bannerlord/WuduRaceTest/probe_v0.2.1.log`，包含种族、缩放、骨骼姿态和包围盒。包围盒可能包含武器，DLL 仅诊断。

退出测试后取消勾选本模块即可；保留旧版包以便回退。测试存档应保留本模块。

## 自动战斗

核对本机游戏 DLL 后，普通兵基础战力按兵种阶级计算，不直接读取护甲值或武器伤害数值。该 T1 新兵自动获得原版基础战力 0.66。装备可能通过坐骑和远程身份影响类别，地形、领队、战术和士气等继续参与模拟。本版未修改自动战斗。详见[机制核对记录](reports/autoresolve_analysis.md)。

## 注意事项

固定头发也必须保留原版 `hair_meshes/group_id` 容器及第 0 个无发型 `hair_mesh`，胡须同样保留零号占位条目。删容器会在启动加载时崩溃，清空列表会在角色或招募预览生成时崩溃。这些占位条目不引用额外网格，原模型头发仍在种族身体中。

布料顶点活动距离和碰撞体需匹配模型尺度；LOD 简化可能移除细小根部。重建对 LOD1 的两组头发显式补固定根部，并检查连通块、锚点、约束及最终包内容。游戏布料流程依据[官方布料文档](https://moddocs.bannerlord.com/editor/resource-editors/cloth_simulation/)。

原版手指握持主要使用手势形变，不能只给 `finger0` 增加权重代替。手部需注册到 `hands_mesh` 并保留正确的形变通道和浮点帧编号。本机 `hands_female_a` 有 26 个通道，其顶点权重不使用 finger0；[官方动画说明](https://moddocs.bannerlord.com/asset-management/asset-types/animations/)也说明了左右手姿态属性调用手部形变。

## 工程与重建

- `input/`：原始模型副本；`source/`：可编辑 Blend、FBX；相邻 `tex/`：原始贴图。
- `module/WuduRaceTest/`：游戏模块；`tools/`：本模型参数、制作、诊断和验证源码。
- `reports/`：检查结果与离线预览；`build/`：缓存；`dist/`：模块和源文件 ZIP。

依赖本机 Blender 5.2、Anaconda Python（NumPy、SciPy、Pillow、lxml）、.NET SDK、net472 引用程序集、mbtool、AssetTool、本机游戏资源和工作区 `tools/asset_helpers`、`tools/cloth_compiler`。路径为本机路径，迁移后需调整。源 ZIP 的 `workspace_tools/` 保存使用的共享源码，恢复时放到工作区根 `tools/`，本项目放到 `mods/WuduRaceTest/`。不附带工具二进制或第三方模型的再分发授权。

从工作区根目录重建：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/WuduRaceTest/tools/rebuild.py --preserve-input
```

`--preserve-input` 使用现有输入；不带它会重新复制原始输入并生成模块配置。模型参数集中在 `tools/model_config.json`。流程生成模型、四级 LOD、布料预处理、DLL，随后检查最终资源和源文件、生成离线预览。检查通过后只打包安装本模块，不启动游戏。

版本记录见 [CHANGELOG](CHANGELOG.md)。
