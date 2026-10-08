# Tianxiang Xuezhi v1.0.1

v1.0.1 返修肩口分离与手臂穿袖：肩口恢复与皮肤一致的解剖权重，长袖在上臂到前臂间作连续过渡，袖端前臂权重至少 86.5%。保留各级袖子几何，减少远处袖口简化造成的缝隙。原始坐标、皮肤、脸部、耳饰、腿部、中央衣裙与裙摆数据保持一致；只调整肩口与袖子。离线动作和最终预览检查通过，游戏效果待用户实测。v1.0.0 包与本地标签保留。

“雪芷丹华”完整角色装备，独立模组 ID `TianxiangXuezhi`，资源前缀 `xz7_`。管理器英文显示，装备名称中文。

三件配套：雪芷丹华 · 发容（头盔）、雪芷丹华 · 衣裙与手饰（身体）、雪芷丹华 · 腿部与绣鞋（靴子）。手套和披肩槽留空。依赖 Native、SandBoxCore、Sandbox。Mod ZIP 顶层可解压至 Modules。

原始输入保存在 input/，原始贴图在 tex/。每套独立测量的物体计划、解剖标记、UV 修正和布料参数在 tools/model_config.json，测量证据在 reports/source_inspection.json。不是物理身高的源坐标按 0.013 比例适配原生 28 骨 human skeleton。固定脸型，不提供原版表情变形。

本套检查到 13 个无骨网格、8 张贴图。共用衣裙网格按实际连通结构分别处理 1892 个上身顶点与 1629 个裙摆顶点：上身布料固定，裙摆平滑跟随小腿，中央衣裙不受前臂和手牵动，肩口跟随上臂；衣裙、袖子及腿部保持四级 LOD 的完整几何。耳侧垂饰固定跟随头部，避免转头及拉弓时被皮肤权重拉长。睫毛单独修正 V 方向。独立检查脚本验证这些约束，最终静态前侧后视、脸部及最差动作帧已人工查看。

腿部胶囊代理的最深重叠约为跑步 49 毫米、骑乘 51 毫米，作为离线诊断保留在报告中；此代理并非实际皮肤表面，预览没有运行游戏布料求解器，不能据此承诺游戏中完全无穿模。

最终 TPAC 回读验证四级 LOD、量化权重、跨网格皮肤接缝、原生站立/跑步/拉弓/骑乘；贴图所有 mip 从最终包解码。Blend 打包贴图，FBX 重新导入，原始 FBX 和 PNG 哈希不变。预览来自最终 TPAC，透明按阈值裁切。LOD0 有有限布料距离，远处仅蒙皮；未运行游戏布料求解器。腿部代理接触只是诊断，游戏中裙摆、武器握持、体型滑块和骑乘碰撞仍需实测。游戏测试由你完成。

重建：Python 执行 tools/configure_mixed_tunic.py、tools/configure_arm_repair.py；后台 Blender 执行 tools/rig_model.py、tools/export_geometry.py；编译 tools/PackagePatch 到 build/package_patch；Python 执行 tools/build_package.py、tools/verify_release.py；后台 Blender 执行 tools/verify_source.py、tools/render_review.py -- final face；Python 执行 tools/prepare_delivery.py。工作区 tools/install_release.ps1 -Mod TianxiangXuezhi -Version v1.0.1 -PreviousVersion v1.0.0 打包并安装自己的模块。源码包保持 source/ 与 tex/ 相邻；外部工具和原生游戏资源不随源包交付。本地 Git，不上传远程。

