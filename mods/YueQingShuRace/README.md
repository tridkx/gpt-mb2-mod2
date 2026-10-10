# Yue Qingshu Race

月清疏默认时装基础种族模组，版本 v0.2.1，适用本机 Native v1.4.8。仅替换帝国贵族新兵 `imperial_vigla_recruit`（T2，等级 11），游戏内名称为“月清疏贵族新兵”。普通帝国新兵及其他兵种不变，升级后进入原版帝国骑手（imperial_equite）路线。

## 当前功能与限制

脸、头发、衣服、身体和双手组成完整身体，使用独立的 28 骨 `yqs_skeleton`，沿用原生动作。LOD0 网格仅做整体转向，不拉长脸、胸部或四肢；关节位置依据源模型骨架生成，含头饰源网格总高约 1.676 米，skin 缩放下限为 1.0，未套用五毒体型参数，也未额外放大。实际 AgentScale 由游戏引擎计算，尚无运行时测量证据；源网格尺寸校验不能替代游戏角色尺寸测量。保留原兵种等级、技能、武器和升级路线，移除防具以避免衣服叠加，不增加固有护甲。提供四级 LOD，见[统计](reports/lod_stats.json)。

不做表情、动态手势、捏脸和换装，手指保持源姿态。裙摆、悬垂袖片、长发、发带和流苏已配置游戏布料，LOD0–3 分别生成自己的预处理数据，共 18 个模拟网格；发根、腰部连接带、袖口和非悬垂部分固定。使用按源模型比例生成的 17 个自有碰撞胶囊，覆盖腰背、臀胯、颈头、双腿和双臂。UE 眼周遮挡和泪线层省略，眼球、脸与睫毛保留；骑砍材质不能完全复现原游戏光照。

v0.1.1 外形已由用户确认可用；本版臀胯碰撞和暗处材质尚待游戏验收。四级网格、UV、蒙皮、骨架与该基线一致；原始贴图不变，生成的材质控制贴图采用非金属、低光泽、完整 AO 亮度，避免额外压暗环境光，见[外形保留报告](reports/preservation_validation.json)。布料数据与碰撞活动范围见[反馈返修检查](reports/feedback_fix_validation.json)与[布料检查](reports/cloth_validation.json)，源网格对比与其他检查见[资源报告](reports/release_validation.json)、[源文件报告](reports/source_validation.json)和[注册报告](reports/registration_validation.json)。布料结构回读和离线胶囊检查不等于引擎求解验证。现有站立、动作图片仅展示最终包的蒙皮参考造型，没有运行游戏布料求解器；实际摆动、碰撞、远处 LOD、骑乘及多人战斗性能待用户实测。

## 安装与测试

`dist/YueQingShuRace_Mod.zip` 顶层目录可解压到游戏 `Modules/`；本机交付流程自动安装自己的模块，不启动游戏。

1. 启动器勾选 **Yue Qingshu Race**，排在 Native、SandBoxCore、Sandbox 后，避免其他模组同时替换帝国贵族新兵。
2. 百科查看“月清疏贵族新兵”，检查朝向、脸、头发、衣服、双手和高度。
3. 招募贵族新兵进入战斗，检查站立、走跑、挥刀时裙摆、袖片、长发和流苏是否摆动，靠近与拉远都检查；本版仍没有握持手势。
4. 升级后恢复原版帝国骑手（imperial_equite）外观。测试存档使用自定义种族后应保留本模块。

## 工程与重建

原始输入完整保存在 `input/default/`，来自 `D:/dsh-xianjian7/output/月清疏_YueQingShu/01_默认套装_MAJ02_01/`。制作使用 Blend 基线；GLB 几何不同，保留原文件。`source/` 保存打包贴图的 Blend 与 FBX，相邻 `tex/` 保存原贴图及派生材质；`tools/` 保存模型专用脚本和参数；`module/` 是运行模块；`reports/` 保存检查和预览；`build/`、`dist/` 为缓存和交付目录。

`source/` 的 `ClothDistance` 顶点色 Alpha 保存活动距离（米，网格倍率为 1）；0 表示固定，材质禁用顶点 Alpha 透明度以免固定部分消失。模型策略保存在 `tools/cloth_policy.json`，`reports/cloth_paint.json` 记录部件，`reports/cloth_travel_calibration.json` 记录局部余量修正。

依赖 Blender 5.2、Anaconda Python（NumPy、SciPy、Pillow、lxml）、.NET 10、mbtool、AssetTool、游戏资源和工作区 `tools/asset_helpers/`、`tools/cloth_compiler/`。报告中的原生骨架和动作 JSON 是本机 v1.4.8 快照，升级游戏后重新提取核对；骨架快照已与当前游戏资源逐项比较。`reports/final_skeleton.json` 为最终 TPAC 回读的自定义骨架；`reports/history/` 为历史版本记录，不作当前操作依据。

从工作区根运行：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/YueQingShuRace/tools/rebuild.py
./tools/install_release.ps1 -Mod YueQingShuRace -Version v0.2.1 -CheckOnly
```

源包保持 `source/` 与 `tex/` 相邻；`workspace_tools/` 恢复到工作区根 `tools/`。打包和安装使用共用入口，替换已有交付包时指定旧版本以保留回退包。仅使用本地 Git。变更见[更新日志](CHANGELOG.md)。
