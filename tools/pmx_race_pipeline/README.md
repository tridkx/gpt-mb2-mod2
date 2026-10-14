# PMX 固定外观种族资源流程

供原神系列多个独立角色工程复用。模型专用路径、ID、比例、材质选择、头发布料和诊断参数保存在各模组 `tools/model_config.json`，本目录保存共用实现；已验收的艾梅莉埃继续使用自己的制作工具，本流程不修改其资源。

## 工程边界

角色工程位于 `mods/GenshinRaceCollection/<ModId>/`，每个角色有独立原始输入、源文件、构建模块与缓存。系列根目录的 `module/GenshinRaceCollection/` 是可安装的单一合集，`collection.py build` 检查各角色最终资源、调用各角色布料诊断、合并 XML 并保持 TPAC/DLL 字节不变；`collection.py install` 打包、安装并备份迁移重复的独立模块。归档提取会核对目标路径位于当前角色的 `input/original/`，保留完整源 ZIP 和解包内容；只读取配置选中的人物 PMX，不导入独立武器与杂物。

`prepare.py` 处理默认可见材质并排除重叠 MMD 渲染层；`templates/` 保存通用骨架、几何、材质、注册、回读与预览流程。`context.execute` 依据角色配置生成当前角色的资源命名和路径，不能直接执行模板。28 骨语义／层级来自当前 Native，关节位置、绑定方向和蒙皮按每个源模型校准；不拉伸角色形体。

`cloth.py` 使用角色自身的头发几何建立共同代理，并生成每个渲染 LOD 的映射。小型断开末端只映射到主表面，独立发束的固定位置和活动范围按角色配置。`collisions.py` 从当前角色的胸腰截面、脸宽及肢段长度测碰撞体；这些近似胶囊不等于真实身体或马匹碰撞。

人物预览运行组件按种族过滤，并以应用域注册表协调多个同系列模块的界面扫描；每个模块仍可独立加载，任务范围外的战场、地图实体和角色数据不改动。

## 使用与依赖

常规重建优先运行各角色 `tools/rebuild.py`。批量的初始模型索引保存在系列 `batch_inventory.json`，只包含本次新增角色，跳过艾梅莉埃。`source_batch.py` 在单个后台 Blender 进程中逐角色处理，`resource_batch.py` 最多并行构建两个角色的独立资源包。

依赖本机 Blender 5.2、Python（NumPy、SciPy、Pillow）、.NET 10／.NET Framework 4.7.2 引用程序集、Native v1.4.8、`D:/mb-tools`、已安装 MMD Tools 的 PMX 读取器与 `tools/asset_helpers/`、`tools/cloth_compiler/`、`tools/cloth_simulator/`。外部路径在脚本／配置中明示，当前 Native 版本改变后必须重新抽取和核对引用，不能继续使用旧动作目录。

`references.py` 为当前角色保存独立的 Native 骨架／动作副本和 SHA256 来源记录。初始 Native v1.4.8 引用读取工作区已核对的艾梅莉埃提取报告，只读其文件；源包中已经包含当前角色所需引用。

独立源包保持 `source/` 与 `tex/` 相邻，并附带 `workspace_tools/`。展开后将 `workspace_tools/` 恢复到工作区根 `tools/`，调整游戏、Blender、Python、mbtool 和 PMX 读取器路径，再运行角色入口。

## 检查边界

最终 TPAC 回读骨架、所有 LOD、材料、UV、量化权重和布料字节。源 Blend/FBX 重开后对照原始坐标与 UV；完整片段扫描跑步、持弓、挥击、骑乘，界面站姿使用抽样检查。结构通过不证明游戏 IK、握持、全部穿模或完整捏脸支持。

长发布料代理使用自有全透明裁切材质，所有贴图 mip 的 Alpha 均为零，材质忽略布料顶点 Alpha。可见头发与模拟代理的材料独立。预览纳入代理，只有确认最终解码贴图所有像素低于实际裁切阈值时才模拟全丢弃；不得仅凭物体名称或“物理代理”标签跳过。`hair_artifact_preview.py` 用于纳入代理的回归预览。材质返修通过逐字节比对全部 LOD 几何、代理流、旧贴图和布料段证明模拟输入不变后，可由 `reuse_proxy_diagnostics.py` 保留原轨迹及其生成时间，附明等价性证据；任一骨架、碰撞、动作或求解输入改变都禁止复用。

映射布料的 CPU 诊断保留 `incomplete`，直接代理另作近似动作诊断。报告模式允许保留 `needs_review` 或不完整提示交付，但提取、解码与求解错误会拦截。离线近似结果、资源结构和用户游戏验收分别记录，不启动游戏，不上传远程。
