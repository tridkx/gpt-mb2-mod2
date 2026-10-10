# Yue Qingshu Race

月清疏默认时装基础种族模组，版本 v0.1.1，适用本机 Native v1.4.8。仅替换帝国贵族新兵 `imperial_vigla_recruit`（T2，等级 11），游戏内名称为“月清疏贵族新兵”。普通帝国新兵及其他兵种不变，升级后进入原版帝国骑手（imperial_equite）路线。

## 当前功能与限制

脸、头发、衣服、身体和双手组成完整身体，使用独立的 28 骨 `yqs_skeleton`，沿用原生动作。LOD0 网格仅做整体转向，不拉长脸、胸部或四肢；关节位置依据源模型骨架生成，含头饰源网格总高约 1.676 米，运行时高度仍受角色缩放影响。保留原兵种等级、技能、武器和升级路线，移除防具以避免衣服叠加，不增加固有护甲。提供四级 LOD，见[统计](reports/lod_stats.json)。

不做表情、动态手势、捏脸和换装，手指保持源姿态。布料模拟后续再补：长发、裙摆、袖片与流苏暂用蒙皮随动，离线跑步预览可见抬腿穿出裙面，本版暂不处理布料碰撞。UE 眼周遮挡和泪线层省略，眼球、脸与睫毛保留；骑砍材质不能完全复现原游戏光照。

源网格与保留的原始 Blend 按材质逐项对比，仅有整体转向，检查见[资源报告](reports/release_validation.json)、[源文件报告](reports/source_validation.json)和[注册报告](reports/registration_validation.json)。离线预览不等于游戏验证，招募、百科、战斗显示及缩放、握持、骑乘和穿模程度待用户实测。

## 安装与测试

`dist/YueQingShuRace_Mod.zip` 顶层目录可解压到游戏 `Modules/`；本机交付流程自动安装自己的模块，不启动游戏。

1. 启动器勾选 **Yue Qingshu Race**，排在 Native、SandBoxCore、Sandbox 后，避免其他模组同时替换帝国贵族新兵。
2. 百科查看“月清疏贵族新兵”，检查朝向、脸、头发、衣服、双手和高度。
3. 招募贵族新兵进入战斗，检查站立、走跑、挥刀。本版没有物理布料或握持手势。
4. 升级后恢复原版帝国骑手（imperial_equite）外观。测试存档使用自定义种族后应保留本模块。

## 工程与重建

原始输入完整保存在 `input/default/`，来自 `D:/dsh-xianjian7/output/月清疏_YueQingShu/01_默认套装_MAJ02_01/`。制作使用 Blend 基线；GLB 几何不同，保留原文件。`source/` 保存打包贴图的 Blend 与 FBX，相邻 `tex/` 保存原贴图及派生材质；`tools/` 保存模型专用脚本和参数；`module/` 是运行模块；`reports/` 保存检查和预览；`build/`、`dist/` 为缓存和交付目录。

依赖 Blender 5.2、Anaconda Python（NumPy、SciPy、Pillow、lxml）、.NET 10、mbtool、AssetTool、游戏资源和工作区 `tools/asset_helpers/`。报告中的原生骨架和动作 JSON 是本机 v1.4.8 快照，升级游戏后重新提取核对；骨架快照已与当前游戏资源逐项比较。`reports/final_skeleton.json` 为最终 TPAC 回读的自定义骨架；`reports/history/` 为历史版本记录，不作当前操作依据。

从工作区根运行：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/YueQingShuRace/tools/rebuild.py
./tools/install_release.ps1 -Mod YueQingShuRace -Version v0.1.1 -CheckOnly
```

源包保持 `source/` 与 `tex/` 相邻；`workspace_tools/` 恢复到工作区根 `tools/`。打包和安装使用共用入口，替换已有交付包时指定旧版本以保留回退包。仅使用本地 Git。变更见[更新日志](CHANGELOG.md)。
