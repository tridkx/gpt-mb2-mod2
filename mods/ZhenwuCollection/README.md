# Zhenwu Collection v1.3.0 — 真武少女八套合集

八套统一管理在本工程 sets/ 下，运行时为一个 ZhenwuCollection 模块，共 24 件头、身、腿装备。管理器英文名 Zhenwu Collection；游戏内使用中文套装名。神机韬略只包含用户指定的 PVP 版。源输入、上游贴图及历史交付包保留；前三套已验收资源、装备定义、可编辑模型和贴图保持原字节。

## 安装和穿戴

模块自动安装到 D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/ZhenwuCollection。启动器勾选 Zhenwu Collection，游戏作弊物品列表搜索相应套装名，穿戴发容、衣裙与手饰、腿部与长靴三件；手套和披肩槽留空。只依赖 Native、SandBoxCore、Sandbox。保留源固定脸型，未实现原生表情和捏脸。

最新交付在 dist/ZhenwuCollection_Mod.zip、dist/ZhenwuCollection_Source.zip，Mod ZIP 顶层为 ZhenwuCollection，可解压到 Modules。dist/ 保留 v1.0.0、v1.1.0、v1.2.0 旧包。源 ZIP 中每套 source/ 与 tex/ 相邻，Blend 内打包贴图，FBX 能重导入。各套独立 input/、source/、tex/、tools/、build/、reports/；通用依赖在根 tools/asset_helpers。集合 source_files 排除缓存、日志、ZIP、备份 Blend 和重复运行时 TPAC。

| 顺序 | 套装 | 子目录 | 验收状态 |
| --- | --- | --- | --- |
| 01 | 云海蹑踪 | [sets/01_YunhaiNiezong](sets/01_YunhaiNiezong/README.md) | 用户已验收，资源保持原字节 |
| 02 | 玄虚清镜 | [sets/02_XuanxuQingjing](sets/02_XuanxuQingjing/README.md) | 用户已验收，资源保持原字节 |
| 03 | 画水微明 | [sets/03_HuashuiWeiming](sets/03_HuashuiWeiming/README.md) | 用户已验收，资源保持原字节 |
| 04 | 澹云未雨 | [sets/04_DanyunWeiyu](sets/04_DanyunWeiyu/README.md) | v1.3.0 离线完成，游戏待验收 |
| 05 | 拂雨冲云 | [sets/05_FuyuChongyun](sets/05_FuyuChongyun/README.md) | v1.3.0 离线完成，游戏待验收 |
| 06 | 玄机空濛 | [sets/06_XuanjiKongmeng](sets/06_XuanjiKongmeng/README.md) | v1.3.0 离线完成，游戏待验收 |
| 07 | 弈墨苍冥 | [sets/07_YimoCangming](sets/07_YimoCangming/README.md) | v1.3.0 离线完成，游戏待验收 |
| 08 | 神机韬略 PVP | [sets/08_ShenjiTaolue](sets/08_ShenjiTaolue/README.md) | v1.3.0 离线完成，游戏待验收 |

## 制作与验证

每套按实际 FBX、UV、材质和连通块独立映射，使用自身资源名、包 GUID 和断言。当前原生 human 骨架 28 骨，保持骨序及绑定矩阵；头饰高度不用于缩放身体。所有套装脸/眼/睫毛实测几何、UV、贴图与已验收第一套相同，因此只对本套睫毛做 V→1−V 修正，其余 UV 和原 PNG 保留。皮肤共享切口的位置、权重与法线在各级 LOD 一致；薄鞋底保护简化边界。

悬垂袖片和披挂按连通块上沿测量肩臂或躯干锚点，避免下垂部分因位置较低被绑到腿上。固定端平滑过渡到活动区，配置有限活动距离、布料材料与模拟标记。澹云未雨远离身体的后裙片降低腿部随动，减少双腿交替造成的拉伸。护腕和手套使用连续前臂至手骨过渡。长发和长头饰按自身高度配置活动区。

每套从最终 TPAC 回读四级 LOD，检查 XML/引用、有限坐标、骨索引、最多四权重且字节和 255、法线/切线、接缝、鞋底、材质 Alpha 与布料字段，完整解码所有贴图 mip。跑步检查 25 有效帧、持弓 150 帧、骑乘 20 帧，站立抽查 16 帧，全部 LOD 检查动态接缝；渲染最差拉伸和腿部代理接触帧，再审阅正侧背面和面部近景。重新打开 Blend 核对打包贴图、原生骨矩阵与权重，FBX 重导入检查通过。合集回读所有八包，确保 24 件装备及所有资源名/GUID 不冲突。

前四套使用活动 Alpha、材料和模拟标记，未包含独立编译的布料预处理段。第五至第八套在 LOD0、LOD1 分别生成原生类型的直接布料预处理段：各级使用自己的拓扑、活动距离、固定根部和约束；LOD2、LOD3 保留蒙皮。最终包回读验证约束长度、无写冲突分组、映射、骨权重、锚点与压缩误差，布料 blob 与生成字节一致。双面重合衣料只在求解输入中合并重复三角面并处理相反法线抵消，运行时几何、材质、UV、Alpha 和蒙皮保留原字节。各套 tools/cloth_policy.json 与 reports/cooked_cloth_validation.json 记录额外固定点及拓扑适配。

最终预览是原生骨骼的离线蒙皮结果，未使用游戏布料求解器、官方编辑器 tcc/tcm 缓存、武器 IK 或真实马体碰撞。部分裙摆/悬垂部件与腿的代理仍有接触，不能将离线通过称为游戏穿模全部解决。后五套的衣摆、袖口、握持、骑乘、透明排序和体型表现由用户游戏验收。

## 报告和重建

合集当前检查记录见 [release_validation.json](reports/release_validation.json)。

各套 reports/ 保存 source_measurement、native_provenance、rig_fit、source_validation、release_validation、detail_validation、package_audit、eye_uv_validation 和 final_preview_manifest；final_*.png / final_motion_review.jpg 使用最终包几何、量化权重和解码贴图。合集 reports/ 保存八套源调研、前三套用户验收记录、最终资产清单、发布及安装一致性检查。源调研只表示静态输入可导入，与已生成的游戏资源检查是不同阶段。

在工作区根运行 `python mods/ZhenwuCollection/tools/build_remaining.py build`，按依赖顺序构建并验证第四至第八套，失败即停止；render 阶段最多并发两个后台 Blender 进程。全部后台 Blender 使用 --factory-startup，避免加载用户插件，使用 --python-exit-code 1；该脚本不安装或启动游戏。build 阶段对第五至第八套自动构建共用编译器、写入布料段并重新检查最终包；随后执行 `python mods/ZhenwuCollection/tools/build_remaining.py render`。单独使用 tools/compile_cloth.py 时必须紧随未编译的新包构建，之后重新运行各套 verify_release.py 与 verify_details.py。源包通过 shared_source_files 包含 workspace_tools/cloth_compiler 共用编译器。各套 README 记录专用参数与重建顺序。第四至第八套文档由 tools/finalize_documents.py 的主题模板生成；修改相关结构时同步维护模板。审阅最终图后 tools/prepare_delivery.py 校验报告、保留基线并合并模块；根 tools/install_release.ps1 打包和安装自身模块；tools/verify_installation.py 核对所有包内与安装字节。

本地 Git 保存源输入、编辑源、脚本、模块和报告；发布标签为 ZhenwuCollection/v<版本>。旧版本标签保留，不上传远程。

## 注意事项

每套仅使用自身的模型参数和网格映射；共通检查和安装步骤以本文件为准。双面布料、UV 接缝、透明 Alpha 及固定根部处理见 [共用编译器](../../tools/cloth_compiler/README.md#注意事项)。

验收状态以各套 STATUS.md 为主，合集表格为汇总；资源哈希以对应检查报告为准。

## 历史记录

版本变化见 [更新日志](CHANGELOG.md)。
