# Bai Mo Qing Outfit 2 No Hat Race

白茉晴第二套时装（无帽）的独立种族资源模块，版本 v0.1.0，按本机 Native v1.4.8 制作。属于[仙剑7系列工程](../README.md)。模块 ID 为 `BaiMoQingOutfit2Race`，种族 ID 为 `bmq2_outfit2`。

## 功能与验证范围

原始脸、头发、时装、身体和双手组成固定完整身体，使用独立 28 骨 `bmq2_skeleton`，沿用原生动作。LOD0 保留源比例，仅整体转向；含头饰总高约 1.576 米。四级 LOD 的三角面数为 102712, 67112, 36610, 16275。裙摆、发束和饰带按本套模型的材料、连通片与实测范围画布料，四级合计 12 个布料网格；固定衣片和手指由骨架带动。

最终 TPAC 已回读并验证几何、量化权重、骨架、材质、全部贴图 mip、布料约束和锚点。源 Blend 已重开、FBX 已重导入，源网格比例检查与原生动作扫描见[发布检查](reports/release_validation.json)、[源文件检查](reports/source_validation.json)、[布料检查](reports/cloth_validation.json)及[预览图索引](reports/final_preview_manifest.json)。图片来自最终 TPAC 和离线蒙皮，不使用游戏布料求解器。

自有 UI Runtime 为本种族的队伍、百科及物品栏人物预览选择自有骨架，并在必要时重建人物预览，保留人物数据、缩放及动画进度。物品栏使用经原生 clip GUID 核对的女性垂手待机候选。检查见[UI 范围回归](reports/ui_scope_validation.json)、[待机映射检查](reports/preview_idle_validation.json)。实际游戏显示尚待用户验收。

## 安装与集成

将 `dist/BaiMoQingOutfit2Race_Mod.zip` 顶层模块目录解压到游戏 `Modules/`，启动器勾选 **Bai Mo Qing Outfit 2 No Hat Race**，排在 Native、SandBoxCore、Sandbox 后。可与其他仙剑7角色种族模块一起启用。

本模块提供种族资源，不包含兵种树、NPCCharacters、原版人物替换或招募入口，单独启用不会自动生成角色。使用方模块依赖 `BaiMoQingOutfit2Race`，给成人女性人物配置 `race="bmq2_outfit2"`，自行设置生成方式、数值、武器、坐骑和升级路线。固定服装身体不适合叠穿原版防具；防具槽应避免遮盖或叠加身体。含本种族角色的存档需要保留此模块。

## 源文件与重建

原始输入保存在 `input/original/`，来源为 `D:\dsh-xianjian7\output\白茉晴_BaiMoQing\03_第二套装_无帽_MAJ03_02`，文件哈希见[输入记录](reports/input_hashes.json)。`source/` 为打包贴图的 Blend 与 FBX，`tex/` 与其相邻；`tools/` 保存本模型实现和参数，`module/` 为运行模块，`reports/` 为检查与预览，`build/`、`dist/` 为缓存与交付包。

依赖 Blender 5.2、Anaconda Python（NumPy、SciPy、Pillow、lxml）、.NET 10、.NET Framework 4.7.2 引用程序集、mbtool、当前游戏 DLL/XML 和工作区 `tools/asset_helpers/`、`tools/cloth_compiler/`。从工作区根运行：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/Xianjian7Race/BaiMoQingOutfit2Race/tools/rebuild.py
./tools/install_release.ps1 -Mod BaiMoQingOutfit2Race -Version v0.1.0 -CheckOnly
```

重建会生成离线检查与预览图；复核图像并更新 `reports/visual_review.json` 后，运行本模组的 `tools/finalize_release.py` 更新交付清单。源包保持 `source/`、`tex/` 相邻，将 `workspace_tools/` 恢复至工作区根 `tools/`。只在本地 Git 提交，发布标签为 `BaiMoQingOutfit2Race/v0.1.0`。变更见[更新日志](CHANGELOG.md)。

## 当前限制与注意事项

固定脸和手指，不提供捏脸、表情、动态手势或换装。省略 UE 眼周遮挡和泪线层，骑砍材质对源着色作近似转换。

布料 `ClothDistance` 顶点色 Alpha 保存米制活动距离，0 为固定，网格倍率为 1；材质关闭顶点 Alpha 透明度。减面后缺失的上缘固定点会显式记录在布料编译清单。碰撞以源关节和可见皮肤拟合；衣服遮盖的躯干使用按本角色尺寸生成的胶囊代理，不能视为完整身体表面覆盖证明。

游戏测试由用户完成，需检查站立、跑动、持弓、挥砍、骑乘，以及队伍／百科／物品栏预览和穿脱装备后的恢复。离线通过不代表游戏布料、握持、IK、全部穿模或多人性能已通过。

无帽版保留毛边层的原始几何与源预览底色；UE 程序毛绒着色未移植，毛边观感以游戏验收为准。
