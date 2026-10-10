# 真武 · 画水微明

## 使用与当前状态

合集模块 ZhenwuCollection。游戏内搜索「画水微明」，穿戴发容、衣裙与手饰、腿部与长靴三件；手套与披肩槽留空。保留固定源脸型，管理器英文名 Zhenwu Collection。

本套已获用户验收，具体动作测试范围未单独报告；见 [当前状态](STATUS.md)。安装与共通使用方法见 [合集 README](../../README.md)。

## 模型与参数

原始输入来自 D:/dsh-tiandao/真武少女校服8套/03画水微明，input/、tex/ 保留原文件。13 个网格、11,522 源顶点、15,597 三角面，独立测量并分配部件。主衣裙 mesh_10_722401 包含领部、身体、裙片和饰物；袖片 mesh_12_879872 按臂轴绑定，手部 mesh_06_471503 包含肘部露肤。长靴为 mesh_02_302444，高头饰达到源 z143.45，仅跟随头骨，不用总高度缩放身体。资源名和包 GUID 使用独立 zw_huashui 命名空间。

脸、眼、睫毛实测几何、UV 和贴图与已验收第一套完全一致，因此只对睫毛 mesh_04_434086 做 V→1−V 修正，其余 12 网格 UV 和全部源 PNG 保留。21 处跨网格皮肤切口的权重、位置和法线在四级 LOD 一致。源鞋底保持水平并保护远景简化边界。

衣摆增加大腿、小腿随动和余量；LOD0 衣摆、袖边与长发配置有限布料活动 Alpha、材料和模拟标记，远景 LOD 使用蒙皮。贴图透明 Alpha 与布料活动距离分开处理。未生成官方编辑器 tcc/tcm 缓存，未运行游戏布料求解器；衣摆胶囊代理仍有接触，具体游戏动作覆盖范围以 STATUS.md 及原验收记录为准。

## 检查与限制

最终 TPAC 回读全部四级 LOD、9 材质和 11 贴图完整 mip，检查 XML/引用、有限坐标、28 骨索引、最多四权重和 255、接缝/法线、鞋底与布料字段。各 LOD 检查原生跑步 25 帧、持弓 150 帧、骑乘 20 帧，站立抽查 16 帧。source/ZhenwuHuashui_Rigged.blend 内打包贴图，source/ZhenwuHuashui_Rigged.fbx 重导入检查通过；源 ZIP 保持 source/ 与 tex/ 相邻。final_*.png 为最终包量化几何、解码贴图的离线蒙皮预览。

## 重建

重建顺序：Python tools/verify_native_provenance.py；后台 Blender tools/measure_source.py、rig_model.py、export_geometry.py（--python-exit-code 1）；dotnet build tools/PackagePatch/PackagePatch.csproj -o build/package_patch -p:BaseIntermediateOutputPath=<本套绝对路径>/build/patch_obj/；Python tools/build_package.py、verify_release.py、verify_details.py；后台 Blender tools/verify_source.py、render_review.py -- final face。最后审阅预览、生成 make_review_sheet.py 和审阅记录，由合集 tools/prepare_delivery.py 汇总。依赖本机 Native、Blender、Anaconda Python、mbtool、.NET 及根 tools/asset_helpers。

上述本套脚本以本套工程目录为运行目录，交付从合集根进行。

## 历史记录

版本变化见 [合集更新日志](../../CHANGELOG.md)。
