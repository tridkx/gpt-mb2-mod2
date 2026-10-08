# Tianxiang Fangzi v1.0.0

“芳姿盈袖”完整角色装备，独立模组 ID `TianxiangFangzi`，资源前缀 `fz5_`。管理器英文显示，装备名称中文。

三件配套：芳姿盈袖 · 发容（头盔）、芳姿盈袖 · 衣裙与手饰（身体）、芳姿盈袖 · 腿部与绣鞋（靴子）。手套和披肩槽留空。依赖 Native、SandBoxCore、Sandbox。Mod ZIP 顶层可解压至 Modules。

原始输入保存在 input/，原始贴图在 tex/。每套独立测量的物体计划、解剖标记、UV 修正和布料参数在 tools/model_config.json，测量证据在 reports/source_inspection.json。不是物理身高的源坐标按 0.013 比例适配原生 28 骨 human skeleton。固定脸型，不提供原版表情变形。

最终 TPAC 回读验证四级 LOD、量化权重、跨网格皮肤接缝、原生站立/跑步/拉弓/骑乘；贴图所有 mip 从最终包解码。Blend 打包贴图，FBX 重新导入，原始 FBX 和 PNG 哈希不变。预览来自最终 TPAC，透明按阈值裁切。LOD0 有有限布料距离，远处仅蒙皮；未运行游戏布料求解器。腿部代理接触只是诊断，游戏中裙摆、武器握持、体型滑块和骑乘碰撞仍需实测。游戏测试由你完成。

本套合并上衣与裙片的网格按实际连通部件分区：1934 个上衣顶点随躯干且布料距离为零，1637 个裙片与装饰顶点采用平滑腿部随动；中心小腿影响渐变归零，最多四骨。中央上衣不继承手、前臂权重。长袖独立按肩臂锚点及有限前臂随动处理，裙摆和腿部轮廓保留到四级 LOD。眼睛、睫毛和绣鞋已放大检查，未扩大后裙摆或隐藏腿部。

完整检查包括 25 帧跑步、150 帧拉弓、20 帧骑乘及 16 个待机采样。无物理蒙皮仍有腿部代理接触，不能将检查通过理解为游戏中完全无穿模；本套最大代理接触深度跑步约 0.047 m、骑乘约 0.024 m，布料最大活动距离为 0.05 m。游戏效果由用户确认。

重建：后台 Blender 执行 tools/rig_model.py、tools/export_geometry.py；编译 tools/PackagePatch 到 build/package_patch；Python 执行 tools/build_package.py、tools/verify_release.py；后台 Blender 执行 tools/verify_source.py、tools/render_review.py -- final face；Python 执行 tools/prepare_delivery.py。工作区 tools/install_release.ps1 -Mod TianxiangFangzi -Version v1.0.0 打包并安装自己的模块。源码包保持 source/ 与 tex/ 相邻；外部工具和原生游戏资源不随源包交付。本地 Git，不上传远程。
