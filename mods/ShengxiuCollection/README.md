# Shengxiu Collection v1.0.4

v1.0.4 是离线逆向生成布料预处理数据的测试版本，全程未使用 Computer Use、未启动游戏或官方编辑器。原生红缨和披风共七个样本的 b97e0f10 数据段均完整解析并逐字节重写一致；约束长度与原始位置核对误差低于 2e-7 米，压缩位置误差低于 0.18 毫米。格式记录在 tools/cloth_payload.py 与 reports/cloth_format_research.json。

新增自己的三角网格布料编译器 tools/cook_cloth.py，为长发、裙摆、袖纱 LOD0/LOD1 分别生成 326368、167232、126312、83564 字节的预处理数据，并补全四个布料网格的编辑器蒙皮数据。按网格边生成抗拉约束、按相邻三角形的对角点生成弯曲约束；生成互不争写活动顶点的并行分组、法线/碰撞三角分组、顶点映射、位置和法线压缩、骨骼权重、测地距离锚点。此算法采用三角网格网络，没有复刻原生的重构网格或经纬分类算法；剪切分组为空，由三角形边长约束维持形状。

六片长袖纱的已有固定边保持不变。编译器检查连通片：20 个无根部的小袖饰固定随蒙皮；没有固定根部的独立发束和裙饰按最高处 1 厘米范围固定上缘，至少固定两个点。这些是求解数据中的显式根部覆盖，不修改渲染顶点的 Alpha。全部 56 个网格的几何、索引、运行时颜色与蒙皮数据不变，贴图和材质不变，头颈鞋子修复与 Blend/FBX 完全保留。根部覆盖位置在 reports/cooked_cloth_validation.json 中逐项记录。

最终 TPAC 已重新读出：四段新增数据与编译输出 SHA256 一致，约束长度、索引、映射、权重和分组通过检查，锚点不跨独立连通片。相同输入重复编译可得到相同的整个 TPAC。尚未运行 Bannerlord 求解器，不能把这些检查当作游戏中的回落效果确认；若仍无效果，继续核查引擎接收路径和剩余元数据字段。此版本为可回退的游戏测试候选。

重建时先编译 tools/PackagePatch/PackagePatch.csproj、tools/NativeClothProbe.csproj、tools/ClothPatch.csproj，分别输出到 build/package_patch、build/cloth_probe、build/cloth_patch；沿用已有几何导出与贴图流程，然后执行 tools/build_package.py，它会调用 build_cooked_cloth.py 生成自有数据。仅补数据可执行 `python tools/build_cooked_cloth.py build/cloth_baseline_v1.0.3/sx_mingyu.tpac build/cloth_candidate_v1.0.4.tpac`。执行 verify_release.py、verify_cloth_activation.py（包含 verify_cooked_cloth.py）、verify_cloth.py、verify_proportions.py、verify_veil_travel.py、verify_native_provenance.py，再执行 reuse_static_previews.py 和 prepare_delivery.py。静态预览复用已确认不变的外观，不能显示新增布料动态。

增量基线保存在 build/cloth_baseline_v1.0.3/。缓存缺失时从本地 ShengxiuCollection/v1.0.3 标签或保留的 v1.0.3 源包恢复，原生样本通过 NativeClothProbe --dump-segments 从当前安装的 crafting.tpac 和 armor666.tpac 只读提取。不要将任何原生约束数据复制到明玉。

以下为 v1.0.3 及此前版本的历史调查和参数说明；当时提出的官方编辑器路径现由上述离线编译路径替代。

2026-10-09 追加反馈「没变化」：当前布料返修未完成，不发布新版本。扩展 TPAC 检查发现，原生红缨 spear_banner_16/17 和披风的蒙皮模拟代理 clo_battania_shoulder_strap_cloak 都有类型 b97e0f10-df49-4666-8f1d-ada6630d4b4e 的额外网格数据段，分别为 120484 和 35772 字节；刚性刀头没有。明玉四个已标记为布料的子网格全部缺少这一段。原生代理的编辑器骨骼数据也完整，而明玉此数据为空。现有 builder 没有生成这些数据。此前的标记、参数、活动范围检查无法证明布料求解已经启动。

这是缺少布料预处理数据的强线索，尚未通过引擎确认其为唯一原因。原生段初步解析可读出 4986 个正的约束长度和对应顶点索引，其索引均落在原生 2295 个编辑器位置内，不能移植到明玉。官方文档说明布料预处理保存约束索引、长度等数据。当前未找到独立布料编译器或托管 API 的布料生成接口，Windows 编辑器 UI 也不在本会话可控制范围；未启动游戏或编辑器。

工具 NativeClothProbe 支持只读数据段检查；编译后执行 `python tools/audit_cloth_payload.py`。本版预期返回 1，报告为 reports/cloth_payload_diagnosis.json。prepare_delivery.py 已加入该检查，缺项时阻止再次发布仅修改参数的布料返修。检查通过也仅代表数据段存在，仍需核验约束与游戏动态。

后续实际修复路径：在官方编辑器中重新导入已保留比例和顶点颜色的 source/ShengxiuCollection_Rigged.fbx，确认蒙皮编辑数据，打开 Cloth Editor，以 native human 骨架和 human_body 碰撞体设置长发、裙摆、袖纱，保存网格设置并生成预处理资源；回读最终 TPAC 检查自有网格对应的数据段、约束索引与几何一致性，再验证造型、材质、骨骼、LOD 和三处接缝，最后打包安装新版本。官方操作参考 https://moddocs.bannerlord.com/editor/resource-editors/cloth_simulation/ 。不要复制原生红缨的数据段，也不要把原生武器碰撞体用于衣服。

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

安装本版：从工作区运行 tools/install_release.ps1 -Mod ShengxiuCollection -Version v1.0.4 -PreviousVersion v1.0.3。Mod ZIP 顶层为 ShengxiuCollection，源 ZIP 保持 source/ 与 tex/ 相邻。保留旧版包，仅更新本模组，用本地 Git 提交及 ShengxiuCollection/v1.0.4 标签，不上传远程。

启用验证需编译 tools/NativeClothProbe.csproj -o build/cloth_probe，执行 tools/verify_cloth_activation.py。静态预览可在验证全部几何和材质不变后执行 reuse_static_previews.py 复用，清楚记录实际渲染版本；这些预览无法显示本次启用字段的动态效果。
