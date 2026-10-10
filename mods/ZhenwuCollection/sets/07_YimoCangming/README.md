# 真武 · 弈墨苍冥 — ZhenwuCollection v1.3.0

## 使用与工程

游戏中搜索「弈墨苍冥」，穿戴发容、衣裙与手饰、腿部与长靴三件；手套和披肩槽留空。安装与共通说明见 [合集 README](../../README.md)，当前验收状态见 [STATUS](STATUS.md)。

原始输入来自 D:\dsh-tiandao\真武少女校服8套\07弈墨苍冥，原文件与源贴图保留。input/、source/、tex/、tools/、build/、reports/ 分别保存原始输入、编辑源、贴图、专用脚本、缓存和检查记录。

## 模型与参数

本套独立映射 14 个源网格，资源前缀 zw_yimo。人体标记经实测后适配当前原生 28 骨，保持骨序和绑定矩阵。头饰高度不用于缩放身体。只翻转配置列出的睫毛 V 坐标，其余源 UV、PNG 保留；四级 LOD 的皮肤接缝位置、权重、法线一致，鞋底简化边界受保护。

悬垂袖片、衣摆与长发按自身结构配置；邻近袖尾小饰片使用相应主袖片锚点。本套挂饰与衣摆按自身解剖标记和连通片配置。具体参数与网格映射以 tools/model_config.json 为准。

## 布料与验证范围

本套包含 6 个布料预处理数据段，LOD0、LOD1 分别使用各自拓扑、Alpha、锚点、约束和映射；LOD2、LOD3 使用蒙皮。显式固定点见 tools/cloth_policy.json 和 reports/cooked_cloth_validation.json。双面重合衣料只在求解输入中去除重复面、处理相反法线抵消，运行时几何、UV、Alpha、权重与材质保持不变。

最终 TPAC 回读检查四级 LOD、资源引用、骨索引、四权重量化和 255、接缝、法线、材质及完整贴图 mip。原生跑步 25 帧、持弓 150 帧、骑乘 20 帧、站立 16 帧离线检查通过。预览使用最终包几何与解码贴图，未使用游戏求解器或武器 IK，裙腿代理接触不能证明游戏无穿模。游戏内动态布料、骑乘与体型表现待用户验收。

source/ZhenwuYimo_Rigged.blend 已打包贴图并重新打开检查；对应 FBX 重导入通过，source/ 与 tex/ 在源包内保持相邻。

## 重建

在工作区根执行：

```powershell
python mods/ZhenwuCollection/tools/build_remaining.py build --sets 07_YimoCangming
python mods/ZhenwuCollection/tools/build_remaining.py render --sets 07_YimoCangming
```

布料编译输入必须是新构建的未编译 TPAC。共用编译器在工作区 tools/cloth_compiler，源 ZIP 附带 workspace_tools/cloth_compiler。后台 Blender 使用 --factory-startup、--python-exit-code 1。交付与安装从合集根进行。

## 注意事项

贴臂袖段不能按总高度误判为下垂布片；挂饰锚点按真实连接部位选择。双面布料和 UV 接缝处理方法见 [共用编译器](../../../../tools/cloth_compiler/README.md#注意事项)。版本变化见 [合集更新日志](../../CHANGELOG.md)。

## 源网格映射

- mesh_00_122067 → head / rigid_head / eye
- mesh_01_140465 → head / skin / face
- mesh_02_300678 → legs / legs / pants
- mesh_03_362443 → body / arms / cuff
- mesh_04_443376 → head / rigid_head / lash
- mesh_05_465525 → legs / legs / skin
- mesh_06_496506 → body / arms / skin
- mesh_07_502495 → body / upper_clothes / cloth
- mesh_08_577318 → head / long_hair / hair
- mesh_09_671079 → head / rigid_head / hair
- mesh_10_718836 → head / rigid_head / ornament
- mesh_11_724523 → head / rigid_head / ornament
- mesh_12_741038 → body / mixed_coat / cloth
- mesh_13_871847 → body / arms / skin
