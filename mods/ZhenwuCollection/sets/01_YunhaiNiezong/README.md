# 真武 · 云海蹑踪 — 第一套

合集模块 ZhenwuCollection，首次交付 v1.0.0。本套保留源脸型、发型、服装贴图与 UV，制作头部、身体、腿靴三件装备。装备三件后手套与披肩槽留空。固定脸型，不提供原生表情和捏脸。

原始输入复制自 D:/dsh-tiandao/真武少女校服8套/01云海蹑踪，input/ 保留源 FBX、OBJ、材质映射和原始预览；tex/ 保留原 PNG。源模型面向 +Y、未旋转；14 个静态网格、12,543 顶点、16,144 三角面独立适配当前原生 28 骨骨架。睫毛与眼影网格 mesh_04_399558 的 UV 单独做 V→1−V 修正：原映射让眼影变成眼下块状阴影，翻转后睫毛位于眼睑边缘；原贴图、其他网格 UV 均保留。所有新资源使用 zw_yunhai 命名空间及独立 GUID。脚底保持源鞋底水平，脚掌跟随脚骨、踝部平滑过渡；源脸下颈使用过渡权重，嘴、眼与脸部跟随头骨。

手部网格还含四块肘部皮肤，已分区处理。皮肤和袖子使用同一套连续臂轴投影权重，保留原露肤开口；衣裙为混合网格，上半身与裙摆分别分配权重，侧裙增加大腿和小腿随动及少量余量。头颈与肘部共有皮肤切口在各级 LOD 保持位置、量化权重、法线一致。贴图 Alpha 保留渐变透明，材质禁用布料顶点 Alpha 对透明度的乘算。

LOD0 衣裙、袖边、后发配置有限活动距离；其他 LOD 使用蒙皮。最终文件检查模拟标记、活动 Alpha 与材质配置回读；未运行游戏布料求解器、未生成官方编辑器 tcc/tcm 缓存。蒙皮预览仍可能出现腿、衣裙或袖片接触，最终布料、握持、骑乘和角色体型表现由用户游戏验收。

source/ZhenwuYunhai_Rigged.blend 内打包贴图，source/ZhenwuYunhai_Rigged.fbx 可以重导入。源 ZIP 中 source/ 与 tex/ 保持相邻，单套工程在 sets/01_YunhaiNiezong 下。reports/release_validation.json 检查最终 TPAC 元数据、几何、UV、权重、材质、完整 mip 和原生动作；detail_validation.json 补充全部 LOD 的动作接缝、法线、鞋底和布料字段核对。final_*.png 直接使用最终包导出的几何、量化权重、解码贴图与原生姿态，属于离线预览。

重建需要本机 Blender、Anaconda Python、.NET、mbtool、当前游戏资源和工作区 tools/asset_helpers。首先 tools/verify_native_provenance.py 确认本机资源，再后台 Blender 依次运行 tools/rig_model.py、export_geometry.py（--python-exit-code 1）；dotnet build tools/PackagePatch/PackagePatch.csproj -o build/package_patch -p:BaseIntermediateOutputPath=<本套绝对路径>/build/patch_obj/；Python 运行 build_package.py、verify_release.py、verify_details.py；后台 Blender 运行 verify_source.py、render_review.py -- final face。各阶段失败即停止。合集顶层 tools/prepare_delivery.py 校验本套报告与预览后汇总模块和源包清单。

不修改其他模组；本地 Git，不上传远程。完成安装后暂停，由用户验收本套后再继续第二套。
