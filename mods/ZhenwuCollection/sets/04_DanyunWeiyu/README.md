# 真武 · 澹云未雨 — ZhenwuCollection v1.3.0

游戏中搜索「澹云未雨」，穿戴发容、衣裙与手饰、腿部与长靴三件；手套和披肩槽留空。原始输入来自 D:\dsh-tiandao\真武少女校服8套\04澹云未雨，原文件与源贴图保留。神机韬略使用 PVP 版。

本套独立映射 13 个源网格，资源前缀 zw_danyun。人体标记经实测后适配当前原生 28 骨，保持骨序和绑定矩阵。头饰高度不用于缩放身体。只翻转配置列出的睫毛 V 坐标，其余源 UV、PNG 保留；四级 LOD 的皮肤接缝位置、权重、法线一致，鞋底简化边界受保护。

悬垂袖片、衣摆与长发按自身结构配置。贴臂袖段不按总高度误判为下垂布片；邻近袖尾独立小饰片继承主袖片锚点，避免因位置低被分配腿部权重。澹云未雨后裙片随动系数为 0.55；拂雨冲云的窄前垂饰固定到腰部。神机韬略的主裙片采用 0.45 基础腿部随动、0.20 侧片增量，缓和骑乘时前中裙片拉伸；袖片在连通检查中合并 UV 接缝共享位置。

本套在布料技能更新前已完成，按用户指示保留原有活动 Alpha、材料和模拟标记；未补编译布料段。

最终 TPAC 回读检查四级 LOD、资源引用、骨索引、四权重量化和 255、接缝、法线、材质及完整贴图 mip。原生跑步 25 帧、持弓 150 帧、骑乘 20 帧、站立 16 帧离线检查通过。预览使用最终包几何与解码贴图，未使用游戏求解器或武器 IK，裙腿代理接触不能证明游戏无穿模。游戏内动态布料、骑乘与体型表现待用户验收。

source/ZhenwuDanyun_Rigged.blend 已打包贴图并重新打开检查；对应 FBX 重导入通过，source/ 与 tex/ 在源包内保持相邻。

重建：合集 tools/build_remaining.py build --sets 04_DanyunWeiyu；随后 render --sets 04_DanyunWeiyu。build 对第五至第八套自动编译布料，并再次检查最终资源；布料编译输入必须是新构建的未编译 TPAC。共用编译器在工作区 tools/cloth_compiler，源 ZIP 附带 workspace_tools/cloth_compiler。后台 Blender 使用 --factory-startup、--python-exit-code 1。本地 Git 管理，不启动游戏、不改 Native、不上传远程。

源网格映射：

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
