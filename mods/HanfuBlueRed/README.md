# 汉服少女 · 蓝红衣装 v1.0.2

独立的骑马与砍杀2装备模块。保留原模型的少女脸、长发、发饰、蓝花上衣、宽袖、红花宽裤和绣鞋。
游戏测试由用户完成。

## 装备与使用

| 装备 | ID | 槽位 |
| --- | --- | --- |
| 汉服少女 · 发容与头饰 | hbr_head | 头部 |
| 汉服少女 · 蓝花上衣与宽袖 | hbr_body | 身体 |
| 汉服少女 · 红花宽裤与绣鞋 | hbr_legs | 腿部 |

建议首次测试整套穿戴并卸下其他手套，以观察自带的手部模型。发容装备包含原模型脸部，覆盖游戏头部、头发与胡须。
物品已注册为商品，并可用于平民装备。不同体型、男性角色、与其他模组装备混搭尚未在游戏中测试。

安装包为 `dist/HanfuBlueRed_Mod.zip`，顶层是 `HanfuBlueRed/`。
需要安装时将这个文件夹放进游戏 `Modules`，在启动器勾选本模块，排在 Native、SandBoxCore、Sandbox 后面。
本机安装位置为 `D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/HanfuBlueRed`。工作区运行时模块位于 `module/HanfuBlueRed/`。

## 当前模型与检查

- 原始 FBX 和 Tripo 的23部件拆分结果分别保存在 `input/`，原目录没有改动。
- 原生骨架从当前游戏 `Native/EmAssetPackages/human/human.tpac` 读取，使用28骨原生顺序和绑定矩阵。
- 为肩臂、手腕、裤腿和鞋重新分配权重；脸/颈与身体及其他真实接缝统一位置和权重。
- 分开原模型里头发与衣服粘连的地方，补上头发移开后露出的衣服缺面。新补面采用匹配蓝色，原输入没有这些位置的完整衣服花纹。
- 分开垂饰与裤腿粘连的区域，垂饰下段从骨盆固定，避免被小腿动作拉扯。
- 恢复原版4096×4096颜色图：471354个原三角面中，86个因拆分后轻微位置变化采用近表面UV投影，其余使用对应原三角面的UV。
- 生成四级LOD；每顶点最多四骨，byte权重和为255。远景接缝保留原位置和权重。
- 长发、宽袖、衣摆和垂饰仅在LOD0设置有限活动距离；裤腿和鞋以蒙皮为主。材质忽略布料距离Alpha对透明度的影响。
- 使用保守的平法线和低高光参数；输入仅有颜色图，没有原作完整PBR材质。
- 最终TPAC重新导出四级模型，核对静态结构、UV、材质引用、权重、接缝和原生动作。
- `reports/release_validation.json` 记录最终包SHA256、面数、动作范围与检查边界；`reports/package_audit.json` 记录包元数据和引用检查。
- `reports/final_*.png` 来自最终TPAC回读后的几何、贴图和量化权重。`reports/*_preview.png` 是源模型离线预览。

离线动作使用本机原生站立、跑步、持弓和骑乘数据。没有运行游戏布料求解器、武器IK或骑乘碰撞；不能据此保证游戏里没有穿模。
首次游戏测试重点观察头颈接缝、长发与肩/袖交叠、宽袖握持、骑乘衣摆/裤腿，以及装备显示和远景切换。

## 可编辑源包与复现

`dist/HanfuBlueRed_Source.zip` 包含可编辑Blend、FBX、相邻的tex目录、原始输入、专用脚本与关键检查记录。
Blend已打包其使用的4K贴图；FBX使用相邻tex目录，解压时保持目录层级。
源文件已重新打开检查骨架、贴图和网格。

专用脚本位于本工程 tools/，以下步骤以本工程目录为运行目录。制作顺序：`rig_model.py` → `export_geometry.py` → 编译 `tools/PackagePatch` → `build_package.py` → `verify_release.py` → `verify_back.py` → `verify_shoes.py` → `verify_source.py` → `render_final.py` → `render_shoes.py`。背面修复逻辑位于 `repair_hair_contacts.py`，鞋底修复位于 `level_shoes.py`；`verify_back.py` 检查各LOD背面补洞及头部、上衣的保留情况；`verify_shoes.py` 检查最终资源鞋底高度、鞋裤接缝和权重保留情况。
骨架和动作JSON均保存于reports；几何、压缩贴图和临时导出位于build，可重新生成。
制作脚本使用本机Blender、Python、mbtool和外部几何/贴图助手，绝对路径写在脚本中；这是本机可复现工程，非独立的软件安装包。

历史无骨骼Tripo输入仍保留为 `source/HanfuBlueRed_NoRig.fbx`，其检查记录为 `reports/remove_rig.json`。
历史版本变化见 [更新日志](CHANGELOG.md)。

## 注意事项

衣背补面使用匹配蓝色，输入缺失位置没有原始花纹；各级 LOD 保留补面和贴图接缝。鞋底按原生站立参考拟合，离线接地不能替代游戏脚部 IK。

依赖工作区 tools/asset_helpers；在工作区根执行 tools/preflight.py 时使用 --example-workspace mods/HanfuBlueRed。
