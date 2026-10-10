# 真武 · 澹云未雨 — ZhenwuCollection v1.3.0

## 使用与工程

游戏中搜索「澹云未雨」，穿戴发容、衣裙与手饰、腿部与长靴三件；手套和披肩槽留空。安装与共通说明见 [合集 README](../../README.md)，当前验收状态见 [STATUS](STATUS.md)。

原始输入来自 D:\dsh-tiandao\真武少女校服8套\04澹云未雨，原文件与源贴图保留。input/、source/、tex/、tools/、build/、reports/ 分别保存原始输入、编辑源、贴图、专用脚本、缓存和检查记录。

## 模型与参数

本套独立映射 13 个源网格，资源前缀 zw_danyun。人体标记经实测后适配当前原生 28 骨，保持骨序和绑定矩阵。头饰高度不用于缩放身体。只翻转配置列出的睫毛 V 坐标，其余源 UV、PNG 保留；四级 LOD 的皮肤接缝位置、权重、法线一致，鞋底简化边界受保护。

悬垂袖片、衣摆与长发按自身结构配置；邻近袖尾小饰片使用相应主袖片锚点。后裙片腿部随动系数为 0.55。具体参数与网格映射以 tools/model_config.json 为准。

## 布料与验证范围

本套配置活动 Alpha、布料材料和模拟标记，未包含独立编译的布料预处理段。

最终 TPAC 回读检查四级 LOD、资源引用、骨索引、四权重量化和 255、接缝、法线、材质及完整贴图 mip。原生跑步 25 帧、持弓 150 帧、骑乘 20 帧、站立 16 帧离线检查通过。预览使用最终包几何与解码贴图，未使用游戏求解器或武器 IK，裙腿代理接触不能证明游戏无穿模。游戏内动态布料、骑乘与体型表现待用户验收。

source/ZhenwuDanyun_Rigged.blend 已打包贴图并重新打开检查；对应 FBX 重导入通过，source/ 与 tex/ 在源包内保持相邻。

## 重建

在工作区根执行：

```powershell
python mods/ZhenwuCollection/tools/build_remaining.py build --sets 04_DanyunWeiyu
python mods/ZhenwuCollection/tools/build_remaining.py render --sets 04_DanyunWeiyu
```

布料编译输入必须是新构建的未编译 TPAC。共用编译器在工作区 tools/cloth_compiler，源 ZIP 附带 workspace_tools/cloth_compiler。后台 Blender 使用 --factory-startup、--python-exit-code 1。交付与安装从合集根进行。

## 注意事项

贴臂袖段不能按总高度误判为下垂布片；挂饰锚点按真实连接部位选择。双面布料和 UV 接缝处理方法见 [共用编译器](../../../../tools/cloth_compiler/README.md#注意事项)。版本变化见 [合集更新日志](../../CHANGELOG.md)。

## 源网格映射

- mesh_00_122075 → head / rigid_head / eye
- mesh_01_140473 → head / skin / face
- mesh_02_300686 → legs / legs / pants
- mesh_03_387075 → body / arms / cuff
- mesh_04_424248 → head / rigid_head / lash
- mesh_05_446300 → body / hands / skin
- mesh_06_510969 → legs / legs / skin
- mesh_07_522246 → head / rigid_head / ornament
- mesh_08_549357 → head / long_hair / hair
- mesh_09_697654 → head / rigid_head / hair
- mesh_10_762923 → body / mixed_coat / cloth
- mesh_11_868411 → body / arms / skin
- mesh_12_900442 → body / upper_clothes / cloth
