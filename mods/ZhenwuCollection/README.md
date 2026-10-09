# Zhenwu Collection v1.0.0 — 真武少女八套

当前交付仅包含第一套「云海蹑踪」，其余七套等待逐套制作与验收。2026-10-09 完成源模型调研，随后制作第一套。神机韬略按用户后续指示仅用 PVP 版。

用户要求：八套统一管理；按原编号制作，每完成一套、离线检查通过并安装后暂停汇报，由用户游戏验收；收到验收通过及继续指示后再处理下一套。返修仍属于当前套，不越过验收关口。游戏由用户测试，助手不启动游戏、不修改 Native、不上传远程。

合集 ID 为 `ZhenwuCollection`，管理器英文名 `Zhenwu Collection`，游戏内使用中文套装名。运行模块位于 `module/ZhenwuCollection/`。逐套增加资源，保持已验收装备 ID、资源名和 GUID 稳定，保留旧版交付包。

八套工程统一位于本目录 `sets/`；每套使用 input/、source/、tex/、tools/、build/、reports/，source/ 与 tex/ 相邻。合集顶层 tools/ 保存合集调研、构建及检查入口，dist/ 保存累计交付与旧版包。第一套已复制原始输入与贴图进入工程，其余套仍在用户提供目录中；用户原文件全部保留。

## 第一套交付与验收

在启动器勾选 **Zhenwu Collection**。通过作弊物品列表搜索「云海蹑踪」，穿戴发容、衣裙与手饰、腿部与长靴三件；手套与披肩槽留空。本合集只依赖 Native、SandBoxCore、Sandbox。

Mod 包在 dist/ZhenwuCollection_Mod.zip，源包在 dist/ZhenwuCollection_Source.zip。安装到 D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/ZhenwuCollection。第一套专用说明与重建步骤见 sets/01_YunhaiNiezong/README.md。

最终 TPAC 已检查四级 LOD、XML、引用、四骨量化权重、头颈/肘部共享切口、法线、鞋底、布料配置与全部贴图 mip；跑步、拉弓、骑乘检查完整有效帧区间，站立动作抽查 16 帧，全部 LOD 检查动态接缝。可编辑 Blend 贴图打包与 FBX 重导入通过。最终预览为离线蒙皮，不是游戏布料求解效果；仍需用户确认衣裙/袖口碰撞、握持、骑乘、体型和透明排序。未运行游戏、未修改 Native。

每次完成一套即暂停。本次等待第一套验收，不制作第二套。

| 顺序 | 套装 | 子目录 | 网格数 | 源顶点 | 三角面 | 当前状态 |
| --- | --- | --- | ---: | ---: | ---: | --- |
| 01 | 云海蹑踪 | sets/01_YunhaiNiezong | 14 | 12,543 | 16,144 | v1.0.0，等待用户游戏验收 |
| 02 | 玄虚清镜 | sets/02_XuanxuQingjing | 12 | 9,408 | 13,358 | 已调研，待前套验收 |
| 03 | 画水微明 | sets/03_HuashuiWeiming | 13 | 11,522 | 15,597 | 已调研，待前套验收 |
| 04 | 澹云未雨 | sets/04_DanyunWeiyu | 13 | 14,641 | 18,332 | 已调研，待前套验收 |
| 05 | 拂雨冲云 | sets/05_FuyuChongyun | 14 | 16,082 | 21,081 | 已调研，待前套验收 |
| 06 | 玄机空濛 | sets/06_XuanjiKongmeng | 13 | 13,763 | 18,331 | 已调研，待前套验收 |
| 07 | 弈墨苍冥 | sets/07_YimoCangming | 14 | 11,013 | 14,764 | 已调研，待前套验收 |
| 08 | 神机韬略 | sets/08_ShenjiTaolue | 14 | 19,132 | 23,265 | 已调研，待前套验收 |

## 本次检查结论

- Blender 5.2.0 LTS 实际导入八套及第八套的 PVP/PVE，共十份 FBX；全部为静态模型，armature、顶点组及带权顶点均为零。所有网格坐标有限、存在 UV 层；没有检查或生成游戏资源。
- 前七套各 9 张 PNG，第八套 13 张；全部能实际解码，尺寸最大 1024×1024。FBX 导入图像均能在本套 tex/ 找到对应文件。贴图仅为 D 色图，没有提供法线/粗糙度/金属度图；后续采用保守材质，不能称作恢复原作完整 PBR。
- 每套 prior repair_report.json 的 unresolved 都是空数组，仅代表上游修复记录。不能由此推断骑砍绑骨、动作、碰撞或布料已通过。
- 模型导入高度范围约 136–145 源坐标单位（含头饰），不能直接当米使用。适配时根据脚底、骨盆、肩肘腕、颈部与头顶实测标记确定尺度，保留每套头饰差异，不按总包围盒机械拉伸。
- 第八套 model.fbx 与 model_PVP.fbx SHA256 相同；PVE 文件不同。三个版本导入后的几何、面索引及 UV SHA256 完全一致。用户已选择仅制作 PVP；PVE 原文件仍保留，不加入交付。
- 已核对本机 Native/SubModule.xml 为 v1.4.8。技能工具预检指定迁移后的 TianxiangT5 示例路径后 ready，依赖导入通过；这只证明工具就绪，不能证明本合集与游戏兼容。

## 制作路线与风险

先做 01 云海蹑踪，建立真武专用的物体映射、解剖标记、稳定命名和 GUID。按头部（脸、眼、发、头饰）、身体（衣服、手臂、手饰）、腿靴三个装备槽制作完整角色，后续可按实测部件调整。使用固定源脸型，不默认实现原生表情或捏脸。

每套分别测量，不能使用天香物体编号和绑骨参数。从本机原生资源重新读取骨架与有效动画；各级 LOD 保持颈缝位置、权重和法线一致。长袖按肩口、包臂区、袖口和悬垂片分区；多部位共用材质时结合连通块与位置判断。裙摆与长发先完善蒙皮，再根据实际拓扑配置游戏布料。04–08 的袖片、披挂与饰物更繁复；08 网格最多，优先控制布料模拟面数与远景 LOD。

透明贴图裁切与布料顶点 Alpha 分开处理，避免使用活动距离后衣服/头发消失。官方说明顶点 Alpha 用于控制布料活动距离，游戏布料需专门配置；离线蒙皮不能验证引擎求解器。依据：[TaleWorlds 布料说明](https://moddocs.bannerlord.com/editor/resource-editors/cloth_simulation/)。模块布局依据：[官方模块快速入门](https://moddocs.bannerlord.com/asset-management/quickguide_create_a_mod/)。

每套完成后从最终 TPAC 回读全部交付 LOD，检查几何、骨索引、四骨权重和为 255、材质引用、透明裁切、XML、接缝与原生站立/跑步/持弓/骑乘等动作。生成预览、可编辑 Blend/FBX、Mod ZIP 与源 ZIP，核对包/工程/安装文件字节一致后只安装本合集，再暂停等待用户验收。离线动作检查不替代游戏布料、握持、骑乘碰撞及角色体型测试。

## 调研证据与复现

- reports/source_survey.json：每份输入 SHA256、对象/连通块、坐标、UV、权重、图像引用、贴图 Alpha、全量原始文件清单。
- reports/source_overview.jpg：拼接用户目录已有正面预览，不是骑砍效果图。
- reports/toolchain_preflight.json：指定真实示例路径后的工具依赖预检。
- tools/survey_sources.py：后台 Blender 只读导入检查，不保存或修改源模型。
- tools/summarize_survey.py：Python/Pillow 贴图解码、源文件清单及概览。

复现：先用本机 Blender --background --python-exit-code 1 --python tools/survey_sources.py，再用 Anaconda Python -B -X utf8 tools/summarize_survey.py。两个脚本按自身路径定位本合集，输入目录固定为本次用户指定路径。
