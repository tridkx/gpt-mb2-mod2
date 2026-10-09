# Shengxiu Collection v1.0.3

圣绣系列独立模组工程，当前收录「圣绣 · 明玉」。模块 ID 为 ShengxiuCollection，管理器显示英文 Shengxiu Collection。三件装备分别为发容、衣裙与手饰、腿部与绣鞋；装备三件获得完整人物。依赖 Native、SandBoxCore、Sandbox，可在作弊物品列表按「圣绣 · 明玉」查找。

v1.0.3 根据用户反馈「外观很好，但完全看不出布料模拟」核查原生偃月刀。单人原版 khuzait_polearm_1_t4 的缨是 Guard 零件 spear_banner_16；spear_banner_17 是同形的红色马尾缨。它们独立于刀头，采用直接布料模拟，无专用动画骨链。LOD0 的 Alpha 范围 0–255：1295 个固定顶点、1227 个活动顶点。资源来自当前安装的 Native/EmAssetPackages/crafting/crafting.tpac。

相较 v1.0.2，原生缨还包含 force_enable_cloth，并且第三方 reader 的 UnknownBool3=true。此次仅将四个已有布料子网格（长发、裙摆、袖纱 LOD0 和袖纱 LOD1）的这两个字段对齐原生样本，其他材质参数、倍率、Alpha、骨骼和全部 56 个 LOD 网格数据完全保留。布料开关配置只读检查为 enable_cloth_simulation=1。UnknownBool3 的编辑器意义未确认，不把相关性当作已证实因果；游戏中的求解是否启动需用户复测。

检测报告为 reports/native_glaive_cloth.json、cloth_activation_validation.json，用户反馈另存 user_feedback_v1.0.2.json。为隔离启用问题，本次没有套用红缨较强的重力或风参数，也没有复制武器碰撞体到衣服。以下 v1.0.2 参数说明是此版本沿用的活动范围方案。


v1.0.2 针对「长袖薄纱挥舞武器时悬空、不回落」调整布料。六片悬垂薄纱各有 5–6 个袖口固定顶点，其余顶点按距固定边的实际网格路径长度绘制 Alpha，取 2.08 倍路径长度作为目标活动预算。薄纱路径长度约 0.59–0.96 米，旧版末端最多只有 0.16 米活动范围。袖口仍随前臂，悬垂部分不能绑到腿部。模型位置和全部骨骼权重与 v1.0.1 完全一致。

袖纱使用独立材料 sx_mingyu_sleeve_silk：弯曲刚度 0.04、剪切刚度 0.85、抗拉和锚定为 1、速度保留系数 Damping 0.90、Gravity 9.81、惯性 0.30、空气阻力 0.06、风力系数 0.03。按照官方文档，Damping 表示传到下一帧的速度比例，不能将较低值直接理解为阻尼更低。保留运动惯性，减少过强弯曲约束，并允许重力使薄纱回落。袖纱 LOD0、LOD1 启用布料，LOD1 保护固定边，LOD2–3 仍仅蒙皮。裙摆和长发的 Alpha、布料参数保留原版。

活动距离需要超过顶点 Alpha 的 0–1 范围。第三方 reader 的 UnknownFloat1 设为 3，作为候选距离倍率；其位置和用途支持这一推断，但尚未在当前游戏版本的编辑器确认字段对应关系。包中已回读确认此字段和全部 Alpha。挥砍 75 帧、拉弓 150 帧的活动空间检查在「该字段确为倍率」的前提下通过，最长约 1.84 米的回落位移可进入活动范围；这只是几何可达性分析，不是布料求解结果。详见 reports/veil_travel_validation.json、cloth_validation.json。若游戏中仍完全悬空，需继续确认引擎是否实际启用了模拟及倍率解释，不能把参数回读通过当作动态效果验证。

保留 v1.0.1 的比例修复：头部上段放大 10%，上颈后收 18 毫米，脚部回转 10.34°，鞋底长度约 23.51 厘米，原始平面鞋底顶点落在 z=0 上方 1 毫米。当前报告 proportion_validation.json 验证这次布料调整没有改变这些位置或权重。历史版本和报告可通过本地发布标签及旧交付包恢复。

原始输入来自 D:/dsh-tiandao/圣秀_明玉，原始模型及记录保存在 input/，PNG 原样保存在 tex/。14 个网格适配当前原生 28 骨骨架，保留 UV、贴图 Alpha。源 Blend 已打包贴图，FBX 重导入检查通过。固定脸型，不提供原版面部表情。

最终 TPAC 回读检查所有 LOD、XML、引用、几何、骨骼、量化权重、19 个皮肤接缝和贴图 mip。站立、跑步、拉弓、骑乘使用本机原生动作。离线蒙皮渲染在 reports/final_*.png，未模拟游戏布料。腿部代理仍有接触，游戏中的衣料碰撞、透明排序、武器握持、体型和性能需要用户测试。未启动游戏，未修改 Native。

未交付官方编辑器生成的 tcc/tcm 预处理缓存；离线路线携带模拟配置，不能声称完成编辑器烘焙或游戏求解验证。官方布料文档：https://moddocs.bannerlord.com/editor/resource-editors/cloth_simulation/

重建：后台 Blender 依次执行 tools/rig_model.py、export_geometry.py（加 --python-exit-code 1）。dotnet build tools/PackagePatch/PackagePatch.csproj -o build/package_patch，然后 Python 执行 build_package.py、verify_release.py、verify_cloth.py、verify_proportions.py、verify_veil_travel.py、verify_native_provenance.py；后台 Blender 执行 verify_source.py、render_review.py -- final face。最后复核预览，执行 prepare_delivery.py。依赖工作区 tools/asset_helpers、本机 Blender、Anaconda Python、mbtool 和已安装游戏资源。

启用回归基线在 build/cloth_baseline_v1.0.2/；活动空间分析仍使用 build/cloth_baseline_v1.0.1/。缓存缺失时从保留的 v1.0.2 源 ZIP 或本地 ShengxiuCollection/v1.0.2 标签恢复旧工程并重建，不把新版本当旧基线。动作 weapon_slash.json 来自原生双手右劈资源；另一个名为 downswing 的资源未包含关键帧，已排除动作验证。

安装：从工作区运行 tools/install_release.ps1 -Mod ShengxiuCollection -Version v1.0.3 -PreviousVersion v1.0.2。Mod ZIP 顶层为 ShengxiuCollection，源 ZIP 保持 source/ 与 tex/ 相邻。保留旧版包，仅更新本模组，用本地 Git 提交及 ShengxiuCollection/v1.0.3 标签，不上传远程。

启用验证需编译 tools/NativeClothProbe.csproj -o build/cloth_probe，执行 tools/verify_cloth_activation.py。静态预览可在验证全部几何和材质不变后执行 reuse_static_previews.py 复用，清楚记录实际渲染版本；这些预览无法显示本次启用字段的动态效果。
