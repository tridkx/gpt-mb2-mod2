# 真武 · 玄虚清镜 — 第二套

本套加入 ZhenwuCollection v1.1.0，合集同时保留已验收的云海蹑踪。游戏内搜索「玄虚清镜」，穿戴发容、衣裙与手饰、腿部与长靴三件；手套与披肩槽留空。管理器英文名 Zhenwu Collection。保留固定源脸型，不提供原生表情和捏脸。

原始输入复制自 D:/dsh-tiandao/真武少女校服8套/02玄虚清镜，input/ 和 tex/ 保留原始文件。独立检查 12 网格、9,408 顶点、13,358 三角面：主衣裙 mesh_09_632392 包括身体、领部、裙片和腰饰；mesh_11_762679 包括袖片、肩饰与背饰。分别按位置分区适配 28 骨原生骨架。鞋底初始高度 -0.0476 源单位，映射后保持水平；各级 LOD 保护鞋底边界，避免简化移入地面。

脸、眼、睫毛实测几何和 UV 与已验收第一套完全一致，相应贴图原字节相同。只对本套睫毛 mesh_04_358718 做 V→1−V 修正，其余 11 网格 UV 未改动。输入文件和 PNG 均保留原字节。所有资源使用 zw_xuanxu 命名空间和独立 GUID；包 GUID 与第一套不同。

皮肤与袖片采用连续臂轴权重，保留原肩部开口；手部包含肘部露肤，按区域处理。16 处跨网格皮肤切口的量化权重、位置、法线在四级 LOD 保持一致。长衣摆增加大腿、小腿随动与余量，衣摆、袖边、长发仅在 LOD0 配置有限布料活动距离。贴图渐变 Alpha 与布料活动 Alpha 分开处理。

最终包回读验证四级 LOD、9 材质、11 贴图完整 mip、XML/引用、骨索引、权重和 255、鞋底、接缝及法线。原生跑步检查 25 帧、拉弓 150 帧、骑乘 20 帧，站立抽查 16 帧，所有 LOD 均做动作和接缝检查。source/ZhenwuXuanxu_Rigged.blend 内打包贴图，source/ZhenwuXuanxu_Rigged.fbx 重新导入通过。源 ZIP 中 source/ 与 tex/ 保持相邻。

final_*.png 和 final_motion_review.jpg 是最终包几何、解码贴图及量化权重的离线蒙皮预览。未运行游戏布料求解器，未生成官方编辑器 tcc/tcm 缓存；衣摆与腿的胶囊代理仍有接触，不把此指标当作游戏布料通过。游戏衣裙/袖片碰撞、握持、骑乘、透明排序及角色体型表现由用户验收。

重建顺序：Python tools/verify_native_provenance.py；后台 Blender tools/measure_source.py、rig_model.py、export_geometry.py（--python-exit-code 1）；dotnet build tools/PackagePatch/PackagePatch.csproj -o build/package_patch -p:BaseIntermediateOutputPath=<本套绝对路径>/build/patch_obj/；Python tools/build_package.py、verify_release.py、verify_details.py；后台 Blender tools/verify_source.py、render_review.py -- final face；检查预览后生成审阅记录，再由合集 tools/prepare_delivery.py 汇总。构建需要本机当前 Native、Blender、Anaconda Python、mbtool、.NET 和根 tools/asset_helpers。

仅本地 Git，不上传远程，不启动游戏，不修改 Native。完成本套安装及交付后暂停，等用户验收再制作第三套。
