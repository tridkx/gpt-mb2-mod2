# Tianxiang Mufeng v1.0.3

“沐风为裳”完整角色装备，独立模组 ID `TianxiangMufeng`，资源前缀 `mf2_`。管理器英文显示，装备名称中文。

三件配套：沐风为裳 · 发容（头盔）、沐风为裳 · 衣裙与手饰（身体）、沐风为裳 · 腿部与绣鞋（靴子）。手套和披肩槽留空。依赖 Native、SandBoxCore、Sandbox。Mod ZIP 顶层可解压至 Modules。

原始输入保存在 input/，原始贴图在 tex/。每套独立测量的物体计划、解剖标记、UV 修正和布料参数在 tools/model_config.json，测量证据在 reports/source_inspection.json。不是物理身高的源坐标按 0.013 比例适配原生 28 骨 human skeleton。固定脸型，不提供原版表情变形。

最终 TPAC 回读验证四级 LOD、量化权重、跨网格皮肤接缝、原生站立/跑步/拉弓/骑乘；贴图所有 mip 从最终包解码。Blend 打包贴图，FBX 重新导入，原始 FBX 和 PNG 哈希不变。预览来自最终 TPAC，透明按阈值裁切。LOD0 有有限布料距离，远处仅蒙皮；未运行游戏布料求解器。腿部代理接触只是诊断，游戏中裙摆、武器握持、体型滑块和骑乘碰撞仍需实测。游戏测试由你完成。

重建：后台 Blender 执行 tools/rig_model.py、tools/export_geometry.py；编译 tools/PackagePatch 到 build/package_patch；Python 执行 tools/build_package.py、tools/verify_release.py；后台 Blender 执行 tools/verify_source.py、tools/render_review.py -- final face；Python 执行 tools/prepare_delivery.py。工作区 tools/install_release.ps1 -Mod TianxiangMufeng -Version v1.0.3 打包并安装自己的模块。源码包保持 source/ 与 tex/ 相邻；外部工具和原生游戏资源不随源包交付。本地 Git，不上传远程。


## v1.0.3 裙摆随动返修

参考用户认可的第一套裙摆随动逻辑，按本套原始裙片与解剖标记独立校准，选择 pelvis_0.9_0.45。下裙摆恢复平滑同侧小腿影响，中心交界的小腿影响平滑归零，避免四骨截断切换。保留原版全部静态坐标、UV、拓扑、其他部件权重和布料 Alpha；四级 LOD 保留裙摆/腿部轮廓。未扩大后摆，未隐藏腿部。source/SkirtClearanceFit.npz 保存可重建的裙摆权重。

完整跑步、拉弓、骑乘及 16 个待机采样检查最终 TPAC。离线腿部接触与变形指标见 reference_skirt_validation.json；游戏布料未验证，不能声称全部穿模已消除。游戏测试由用户完成。历史版本和交付包保留。
