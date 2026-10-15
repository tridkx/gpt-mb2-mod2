# PMX 固定外观种族资源流程

供原神系列多个独立角色工程复用。模型专用路径、ID、比例、材质选择、头发布料和诊断参数保存在各模组 `tools/model_config.json`，本目录保存共用实现；已验收的艾梅莉埃继续使用自己的制作工具，本流程不修改其资源。

## 工程边界

角色工程位于 `mods/GenshinRaceCollection/<ModId>/`，每个角色有独立原始输入、源文件、构建模块与缓存。系列根目录的 `module/GenshinRaceCollection/` 是可安装的单一合集，`collection.py build` 检查各角色最终资源、调用各角色布料诊断、合并 XML 并保持 TPAC/DLL 字节不变；`collection.py install` 打包、安装并备份迁移重复的独立模块。归档提取会核对目标路径位于当前角色的 `input/original/`，保留完整源 ZIP 和解包内容；只读取配置选中的人物 PMX，不导入独立武器与杂物。

`prepare.py` 处理默认可见材质并排除重叠 MMD 渲染层；`templates/` 保存通用骨架、几何、材质、注册、回读与预览流程。`context.execute` 依据角色配置生成当前角色的资源命名和路径，不能直接执行模板。28 骨语义／层级来自当前 Native，关节位置、绑定方向和蒙皮按每个源模型校准；不拉伸角色形体。

`direct_hair.py` 为配置 `cloth_mode=direct` 的角色逐可见发束、逐 LOD 编译直接布料；保留可见几何、UV、材质和权重，删除旧模拟代理与映射。固定带按角色设置并限制到当前发束高度的 15%，避免细小发饰全部固定。`cloth.py` 保留供历史映射工程重建。`collisions.py` 按当前角色测量碰撞胶囊，近似碰撞不等于真实身体或马匹。

人物预览运行组件按种族过滤，并以应用域注册表协调多个同系列模块的界面扫描；每个模块仍可独立加载，任务范围外的战场、地图实体和角色数据不改动。

## 使用与依赖

常规重建优先运行各角色 `tools/rebuild.py`。批量的初始模型索引保存在系列 `batch_inventory.json`，只包含本次新增角色，跳过艾梅莉埃。`source_batch.py` 在单个后台 Blender 进程中逐角色处理，`resource_batch.py` 最多并行构建两个角色的独立资源包。

依赖本机 Blender 5.2、Python（NumPy、SciPy、Pillow）、.NET 10／.NET Framework 4.7.2 引用程序集、Native v1.4.8、`D:/mb-tools`、已安装 MMD Tools 的 PMX 读取器与 `tools/asset_helpers/`、`tools/cloth_compiler/`、`tools/cloth_simulator/`。外部路径在脚本／配置中明示，当前 Native 版本改变后必须重新抽取和核对引用，不能继续使用旧动作目录。

`references.py` 为当前角色保存独立的 Native 骨架／动作副本和 SHA256 来源记录。初始 Native v1.4.8 引用读取工作区已核对的艾梅莉埃提取报告，只读其文件；源包中已经包含当前角色所需引用。

独立源包保持 `source/` 与 `tex/` 相邻，并附带 `workspace_tools/`。展开后将 `workspace_tools/` 恢复到工作区根 `tools/`，调整游戏、Blender、Python、mbtool 和 PMX 读取器路径，再运行角色入口。

## 检查边界

最终 TPAC 回读骨架、所有 LOD、材料、UV、量化权重和布料字节。源 Blend/FBX 重开后对照原始坐标与 UV；完整片段扫描跑步、持弓、挥击、骑乘，界面站姿使用抽样检查。结构通过不证明游戏 IK、握持、全部穿模或完整捏脸支持。

当前 13 个长发角色使用可见头发直接模拟，包内不保留代理资产或 `ClothMetamesh` 引用；每级直接预处理段必须回读校验，原几何、UV、权重逐字节比较。`direct_hair_trial.py` 保存旧资源并验证转换，`source_direct_hair.py` 清理可编辑 Blend 中的旧代理，`finish_direct_hair.py` 校验 LOD 数值等价性并设置代表级诊断。正常重建由 `build_one.py` 依据配置选择直接或映射路线。

`HairRuntimeProbe.cs.tpl` 只读记录创建页面实际网格、布料状态、材质与漫反射纹理名称，日志位于用户 Documents 下对应角色目录的 `ui_runtime.jsonl`。它不修改渲染属性，日志只能说明运行时选用的资源。旧代理透明材质及 Native 映射角色实验记录保存在报告历史目录，不作为当前直接模拟验收。

BC 纹理的顶层宽高必须为 4 的倍数；编码前对不合规源图按完整 UV 范围重采样到下一档 2 的幂次尺寸，保留原 PNG。回读全部 mip 后检查尺寸和编码数据。本机 D3D11 WARP 资源创建对照可使用 `RuntimeResourcePatch check-bc-texture`，不启动游戏；驱动或游戏的实际加载仍由用户复测。

直接布料按最终可见网格作近似动作诊断；若各级预处理数据一致，可用代表级检查。历史映射工程的不支持映射仍须保留 `incomplete`。报告模式允许保留 `needs_review` 或不完整提示交付，但提取、解码与求解错误会拦截。离线近似结果、资源结构和用户游戏验收分别记录，不启动游戏，不上传远程。
