# 圣绣合集更新日志

以下为原文档中的历史记录，按原有版本保留。记录中的“当前”“本版”、路径和命令均指当时状态，不作为当前操作依据。当前用法见同目录 README。

## v1.1.6 — 2026-10-09 明玉头颈随动与后发间距候选

用户反馈 v1.1.5 后发离身体过远，头部前倾明显、颈部折叠。回读原生待机确认本套头骨姿态随动与颈口权重差异，调整头部全部部件为颈骨 85%／头骨 15%，脸与下颌统一变换；颈部皮肤平滑连接上胸骨与相同头部变换，各级颈口共享权重一致，静态脸形不变。

后发下段相对 v1.1.5 向身体收回最多 45mm，上端保留间距以配合新的颈骨随动，后发活动距离限制 8mm，布料保留。重新生成头部与颈部皮肤四级 LOD 和长发布料，其余 28 个网格、衣裙袖纱布料、碰撞 XML 和另外两套包不变。报告见 reports/head_neck_validation.json，同姿态头颈近景及侧后方预览见 reports/head_neck_preview.json。

完整原生周期和最终包离线检查通过，实际头颈外观、头发贴背与动态穿模仍待用户游戏测试。保留 v1.1.5 回退包，仅安装本合集，助手不启动游戏。

## v1.1.5 — 2026-10-09 明玉后发造型与绑骨候选

用户补充：整片后发在待机站立时进入衣服，并提供库存侧后方截图。旧包的原生待机蒙皮预览复现穿背；原造型后发下段已有静态交叉，所有长发仅绑定头骨，头颈姿态进一步将后发带入躯干。此前仅改变碰撞与活动距离未解决反馈。

沿后颈至下段重新调整后发前后位置，上端保留发根；下段平滑增加 spine2 权重至 98%，后发活动距离限制 12mm，保留布料。更新 Blend/FBX、四级长发 LOD，并按新几何/权重重新编译 LOD0 长发布料。最终包回读确认其余 52 个网格、衣裙袖纱布料与编辑器数据、自有碰撞 XML、白凤素问包均不变。报告见 reports/hair_shape_validation.json；相同待机姿态的侧后方前后预览见 reports/hair_shape_preview.json。

四级 LOD 检查待机、跑步、持弓、骑乘完整原生周期中的后发顶点、面片中心和边中点。通过的是离线蒙皮与躯干三角面间距检查；游戏布料、体型与武器行为尚待用户测试。自动安装本合集、保留 v1.1.4 回退包，助手未运行游戏。

## v1.1.4 — 2026-10-09 明玉长发活动距离测试候选

用户确认 v1.1.3 站立自然下垂，但仍穿模。保持裙子腿部碰撞、所有几何、蒙皮、渲染 Alpha、编辑器数据和布料约束不变，仅扩大长发活动点的求解距离：至少原值三倍，且覆盖站立/完整跑步胶囊投影所需距离加 5mm，当前最大约 7.1cm；零距离固定点完全保留。原预算最多有 285 个活动点在单帧不能让到碰撞体外，新预算在所查 26 帧中均覆盖投影需求。覆盖参数与逻辑见 tools/hair_clearance_policy.json、prepare_hair_clearance.py，可编辑 Blend/FBX 的原始 Alpha 绘制未修改。

后续用户反馈 v1.1.4「还是没修好」，见 reports/user_feedback_v1.1.4.json。工程与安装的明玉包、碰撞 XML 哈希一致。距离预算调整未解决实际穿模，不能将此前投影诊断当成已确定的根因或修复。此轮只记录反馈并核对安装，不继续改动运行包，待当前背面/侧面跑动证据定位发束与真实碰撞方向。

背部碰撞边界由衣服表面内侧 8mm 调至外侧 2mm，上端中心降至 1.27m，离线站立最大上推约 2.6mm。报告见 reports/hair_clearance_fit.json、hair_clearance_validation.json。投影可达性不代表完整求解通过，实际长发穿后背、自然下垂和摆动范围尚待用户游戏确认。保留 v1.1.3 回退包，白凤、素问不变，助手未启动游戏。

## v1.1.3 — 2026-10-09 明玉长发背部碰撞测试候选

用户确认 v1.1.2「裙子修好了」，同时报告长发跑动时穿后背，见 reports/user_feedback_v1.1.2.json。保留已确认的四个腿部胶囊和身体碰撞引用，仅将头部引用设置为自有 sx_mingyu_back_collision。新增三个竖向背部胶囊，按模型背面拟合，端点分别随 spine、spine2；避开发根、领口与胸前。全部几何、蒙皮、材料、四段布料预处理和参数保持不变，白凤、素问及 Native 不变。

站立与完整 25 帧跑步作胶囊投影诊断，站立最大上推约 4.4mm；该诊断不运行游戏求解器，部分发点的推开超过既有 25mm 活动距离。候选尚待确认跑动背部穿模和自然下垂，不能扩大 v1.1.2 裙子反馈为 v1.1.3 头发验收。报告见 reports/back_collision_fit.json 与 reports/back_collision_validation.json。保留 v1.1.2 回退包，助手未启动游戏。

## v1.1.2 — 2026-10-09 明玉腿部碰撞测试候选

用户确认 v1.1.1 恢复自然下垂，但裙子在站立或跑步时穿腿，见 reports/user_feedback_v1.1.1.json。新增自有 ModuleData/cloth_bodies.xml 的 sx_mingyu_leg_collision，仅含四个腿部胶囊。按明玉腿部皮肤重新拟合中心线和半径，而非直接缩小原生胶囊；大腿半径约 8.65cm，小腿约 6.66cm，小腿轴线向模型实际位置偏移。头发保留无人体碰撞设置，身体（含袖纱）引用自有腿部碰撞体，不修改 Native。

相对 v1.1.1 全部几何、蒙皮、材料、布料参数与四段预处理数据不变。回读、材质与 Alpha 检查通过，白凤、素问哈希不变。站立与完整 25 帧跑步做胶囊投影诊断；站立最大上推约 6.6mm，部分跑步帧需要的推开超过裙摆原有活动距离，因此仍需确认游戏加载自有碰撞体、站立/跑步穿模与自然下垂。报告见 reports/leg_collision_fit.json 和 reports/leg_collision_validation.json。此版是游戏测试候选，助手未启动游戏，保留 v1.1.1 回退包。

## v1.1.1 — 2026-10-09 碰撞隔离测试候选

用户反馈引入布料后明玉裙片与头发像被提起。CPU 站立姿态诊断中，原生 human_body 推开可使活动发点上移约 10.8cm，明显超过发束约 2.5cm 的活动距离；无碰撞的约束隔离复现只有约 1–3mm 上移。此证据支持碰撞冲突疑点，尚不能代替游戏验证。

候选仅清空 sx_mingyu_head、sx_mingyu_body 的 human_body 引用；四段布料、所有材料参数、56 个网格及数据段保持不变。白凤、素问保持原包。头发、裙片和袖纱仍模拟，但暂不碰撞人体，可能增加穿模。用户已选择保留布料并准备游戏测试候选。待同一背包姿态、跑步与骑乘反馈后再适配最终碰撞方案。验证与基线哈希见 reports/collision_candidate_validation.json，截图反馈见 reports/user_feedback_lift_2026-10-09.json。保留 v1.1.0 回退包；助手未启动游戏。

## v1.1.0

加入白凤与素问，明玉 TPAC 保留 v1.0.4 字节。白凤与素问补充头颈随动、下颌颈环权重修正；素问补充睫毛透明通道和虹膜。

### v1.1.0 制作与检查原记录

下颌补修：已将胸椎到头部的权重渐变从下巴收回颈环；四级 LOD 验证完整脸部与眼睛同步，避免下巴被胸椎拉歪。

白凤与素问已补充动作头颈随动修正（静态造型不变）；素问恢复睫毛 Alpha 并补齐虹膜。专项报告位于各套装 reports/head_follow_validation.json 与素问 reports/eye_material_repair.json。

### 当时的合集说明

本版加入「圣绣 · 白凤（女）」和「圣绣 · 素问」，与已有明玉放在同一个 `ShengxiuCollection` 模块。管理器显示英文 Shengxiu Collection；游戏内按「圣绣 · 白凤」「圣绣 · 素问」查找装备。每套三件：发容（头盔）、衣裙与手饰（身体）、腿部与绣鞋（靴子）。同套三件一起装备，手套、披肩槽留空。

| 套装 | 工程 | 资源包 |
| --- | --- | --- |
| 明玉 | 现有根 input/source/tex/tools | sx_mingyu.tpac |
| 白凤（女） | sets/02_Baifeng/ | sx_baifeng.tpac |
| 素问 | sets/03_Suwen/ | sx_suwen.tpac |

明玉运行时 TPAC 与 v1.0.4 逐字节一致。两套新增装备分别测量尺度、朝向、材质槽与解剖标记，使用独立资源名和 GUID；不覆盖输入目录。素问原模型导入后 Y 轴向上，预览错拍成头顶；本版将它旋转到 Z 轴向上，重新生成正常正面、侧面、背面、面部和原生动作预览。白凤实际面片使用的材质槽不是第一个槽，已正确读取并用贴图透明裁切，避免衣服整体半透明或羽饰变黑。

新两套长袖/垂带、裙摆、长发在 LOD0、LOD1 都生成自己的布料预处理数据，LOD2/3 仅蒙皮。肩口保留手臂权重，垂带避免跟随腿部；腰部挂饰另按所属部件绑定，白凤肩羽固定跟随上臂。UV 切分点按位置恢复布料拓扑，活动范围与固定根部逐顶点检查；实际根部修补在每套 reports/cooked_cloth_validation.json 中记录。共用编译器是三角网格约束网络，未复刻原生重构网格算法。

最终 TPAC 已回读检查所有四级 LOD、28 骨索引与权重、皮肤接缝、全部贴图 mip、布料映射/骨骼/约束/锚点及并行分组。站立抽查 16 帧，跑步完整 25 帧、拉弓 150 帧、骑乘 20 帧。活动布料的离线蒙皮拉伸仅记录为诊断，因为预览未运行游戏布料求解器；固定皮肤和连接处另做拉伸检查。原生腿部胶囊接触只是诊断，不代表已消除所有裙摆穿模。鞋底用各套原始鞋子单独拟合，低处鞋长约 24.5cm、最低鞋底为 z=1mm。

交付包含 Mod ZIP 与 Source ZIP。源码包保留每套相邻的 source/、tex/，Blend 内打包贴图，FBX 可重新导入；旧包和 Git 标签保留。只安装此合集模块，不启动游戏。**新两套尚未由用户游戏验证；自然回落、挥砍、骑乘碰撞和远处 LOD 求解仍需游戏测试。**

新两套重建：在本工作区执行 `python -X utf8 mods/ShengxiuCollection/tools/build_new_sets.py`，可用 `--set 02_Baifeng` 或 `--set 03_Suwen` 指定一套。它直接运行各套已提交的模型参数和脚本，不重新套用明玉参数。检查最终预览后执行 tools/prepare_collection_release.py，再用工作区 tools/install_release.ps1 -Mod ShengxiuCollection -Version v1.1.0 -PreviousVersion v1.0.4 打包安装。Blender、mbtool、原生游戏包和 asset_helpers 为本机外部依赖；布料共用源码随 Source ZIP 放在 workspace_tools/cloth_compiler/。

## 明玉 v1.0.4 历史记录

2026-10-09 用户反馈「可以生效，但是只有很近的时候才生效」，确认 v1.0.4 安装期间的近距离布料效果；用户未明确指定测试版本，不扩展为所有 LOD/距离/动作已通过。助手未启动游戏。当前是包内 LOD0 三类布料、LOD1 仅袖纱、LOD2/3 无布料。最高画质的[官方默认网格切换点](https://moddocs.bannerlord.com/asset-management/asset-types/meshes/)为 15、22.5、30 米；对应参考区间 LOD0 约 0–15m、LOD1 约 15–22.5m、LOD2 约 22.5–30m、本模组最后的 LOD3 约 30m 以后直到剔除。画质设置可缩短距离，这不是本机实测布料截止值；LOD1 的求解效果和引擎是否独立限距仍待确认。

编译器现集中在工作区根 [tools/cloth_compiler](../../tools/cloth_compiler/README.md)，本模组 tools/cloth_policy.json 保留明玉固定策略，Python 入口和 C# 链接工程引用共用实现。原生格式验证与重建后 TPAC SHA256 均与迁移前一致。迁移不改版本、游戏文件或发布标签；源包可将所需共用文件收录到 workspace_tools/cloth_compiler，旧源包保留。

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
