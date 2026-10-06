# HanfuBlueRed

汉服少女蓝红配色的新模组工程，尚未制作游戏装备或发布。

原始输入复制自 `D:/dsh-tripo/汉服少女蓝红配色`，完整保留在 `input/`。
供 Tripo 自动拆分的无骨骼模型：`source/HanfuBlueRed_NoRig.fbx`，已嵌入基础颜色贴图。
已移除骨架、蒙皮权重与动画；重新导入核对顶点/三角面数量、位置、UV、材质及贴图。
检查记录位于 `reports/remove_rig.json`，复现脚本为 `tools/remove_rig.py`。

原始模型放 input/，可编辑工程放 source/，贴图放 tex/，专用脚本放 tools/。
完成制作后创建 SubModule.xml 和 items.xml，使用自己的资源名及 GUID，并将 mod.json 的 source_files、package、validation_report 更新为实际交付文件。
