# Wudu Canglan Race Test

v0.2.6 使用 `01苍蓝流苏` 完整角色模型、自定义种族 `wdr_canglan` 和 28 骨骨架，只替换帝国普通新兵 `imperial_recruit`，游戏内名称为“五毒苍蓝新兵”。适用本机 Native v1.4.8。贵族新兵和 2 号模型尚未制作。

## 当前功能与限制

含头饰网格总高 1.45 米，正面朝游戏前方，保持原始头身和四肢比例，种族最小缩放为 1.1。本版沿用已由用户实测到原版成人胸口的尺寸参数；基础模型全部顶点位置与已验收版本一致。

双手包含在完整身体网格中；独立 hands_mesh 使用隐藏占位，关闭皮肤拼接。保留手腕支点、前臂到手掌渐变权重和手部平滑法线。用户已确认 v0.2.4 双手可见，手腕比此前好看。当前运行时不启用手指形变，手指保持原模型姿态；26 个实验形变仅保留在可编辑源文件中。资源与源文件离线检查通过，其他动作与握持效果尚未完整验收。

裙摆、袖片、袖口和头发具有游戏布料活动范围、固定根部、材料及预处理数据；近处 LOD0/1 共 10 组布料，远处 LOD2/3 使用简化蒙皮网格。贴头发片固定到头部，悬垂发梢保留活动；12 个随骨骼移动的布料碰撞胶囊按模型尺寸配置。布料动态与穿模程度尚待游戏验证，远处布料不求解。当前固定脸；握持、骑乘 IK、命中和大规模战斗性能尚未验收。

**当前未解决问题：背包预览和自定义角色页面的双手仍处于背手状态。** 用户已实测确认 v0.2.6 两个页面均存在该问题，待机姿势未通过游戏验收，当前暂停处理。动作集注册与离线姿态检查通过不能证明游戏显示正确，根因尚未确定。此前用户反馈持武器时正常；本次反馈未重新验收持武器动作。详细证据和未解决事项集中记录在[预览待机问题记录](reports/preview_stance_v0.2.6.md)，离线数据见[动作抽样](reports/inventory_validation.json)。

眼周睫毛部件使用经过 V 坐标修正的 UV 和半透明渐变，脸部、眼球 UV 保持原始数据，头部模型尺寸不变。眼周显示及头发动态需游戏复测。见[头发与眼周检查说明](reports/hair_inventory_face_v0.2.5.md)、[头部近景](reports/head_closeup.png)和[眼周 UV 检查](reports/face_uv_validation.json)。

衣服、头发、脸、身体和双手组成完整种族身体网格。防具栏为空，没有添加固有护甲。原兵种等级 6（T1）、技能、武器和升级路线保留，升级后进入原版兵种。

最终 TPAC、权重、四级 LOD、原始形状对照、XML 合并及 Blend/FBX 重开检查通过。检查确认四级双手都在身体中，运行时手部形变数为 0；源文件仍保留实验形变。原生跑步全周期和站立、持弓、骑乘、挥刀抽样完成蒙皮与布料活动范围检查。这些检查不运行游戏布料求解器。见[资源检查](reports/release_validation.json)、[布料检查](reports/cloth_validation.json)、[手部检查](reports/hand_validation.json)和[显示回归处理](reports/hand_display_regression_v0.2.4.md)。

## 游戏测试

1. 启动器勾选 **Wudu Canglan Race Test**，排在 Native、SandBoxCore、Sandbox 之后，避免其他兵种修改模组覆盖该兵种。
2. 背包和自定义角色页目前有已确认的背手问题，暂未修复。后续恢复排查时再记录初次显示、性别/身材切换前后的差异；近距离眼周黑块与透明妆面仍需单独验收。
3. 检查转头、跑步和停止时左侧头发是否穿入头部，以及袖口、裙摆与远近 LOD 切换。
4. 复查左右手可见、持剑挥刀和左手持盾时手腕表现；条件允许时检查持弓、骑乘。本版手指不会动态弯曲。
5. 诊断日志位于系统“文档”下 `Mount and Blade II Bannerlord/WuduRaceTest/probe_v0.2.6.log`，游戏初始化后记录男女战士/编辑动作集有效性、身体中手部网格实际面数、颜色及包围盒；任务生成后记录皮肤可见掩码及合批网格面数。合批网格名不能直接识别原始部件；包围盒可能包含武器，DLL 仅诊断。

退出测试后取消勾选本模块即可；保留旧版包以便回退。测试存档应保留本模块。

## 自动战斗

核对本机游戏 DLL 后，普通兵基础战力按兵种阶级计算，不直接读取护甲值或武器伤害数值。该 T1 新兵自动获得原版基础战力 0.66。装备可能通过坐骑和远程身份影响类别，地形、领队、战术和士气等继续参与模拟。本版未修改自动战斗。详见[机制核对记录](reports/autoresolve_analysis.md)。

## 注意事项

固定头发也必须保留原版 `hair_meshes/group_id` 容器及第 0 个无发型 `hair_mesh`，胡须同样保留零号占位条目。删容器会在启动加载时崩溃，清空列表会在角色或招募预览生成时崩溃。这些占位条目不引用额外网格，原模型头发仍在种族身体中。

布料顶点活动距离和碰撞体需匹配模型尺度；LOD 简化可能移除细小根部。重建对 LOD1 的两组头发显式补固定根部，并检查连通块、锚点、约束及最终包内容。游戏布料流程依据[官方布料文档](https://moddocs.bannerlord.com/editor/resource-editors/cloth_simulation/)。

原版手指握持主要使用手势形变，不能只给 `finger0` 增加权重代替。本机 `hands_female_a` 有 26 个通道；[官方动画说明](https://moddocs.bannerlord.com/asset-management/asset-types/animations/)也说明了左右手姿态属性调用手部形变。本工程的独立手部形变路径尚未验证成功，当前交付只用完整身体蒙皮显示。源文件中的实验形变不代表已经在游戏启用。

## 工程与重建

- `input/`：原始模型副本；`source/`：可编辑 Blend、FBX；相邻 `tex/`：原始贴图。
- `module/WuduRaceTest/`：游戏模块；`tools/`：本模型参数、制作、诊断和验证源码。
- `reports/`：检查结果与离线预览；`build/`：缓存；`dist/`：模块和源文件 ZIP。

依赖本机 Blender 5.2、Anaconda Python（NumPy、SciPy、Pillow、lxml）、.NET SDK、net472 引用程序集、mbtool、AssetTool、本机游戏资源和工作区 `tools/asset_helpers`、`tools/cloth_compiler`。路径为本机路径，迁移后需调整。源 ZIP 的 `workspace_tools/` 保存使用的共享源码，恢复时放到工作区根 `tools/`，本项目放到 `mods/WuduRaceTest/`。不附带工具二进制或第三方模型的再分发授权。

从工作区根目录重建：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/WuduRaceTest/tools/rebuild.py --preserve-input
```

`--preserve-input` 保留模组内输入副本并重新生成模块配置；不带它会重新复制原始目录。原始目录后续另有修复时，保留模式不自动吸收新输入；检查报告记录与输入副本的差异，同时验证副本自身哈希。模型参数集中在 `tools/model_config.json`。流程生成模型、四级 LOD、布料预处理、DLL，随后检查最终资源和源文件、生成离线预览。检查通过后只打包安装本模块，不启动游戏。

版本记录见 [CHANGELOG](CHANGELOG.md)。
