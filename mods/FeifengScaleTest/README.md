# Feifeng Skeleton Scale Test v0.1.0

飞凤苗银（女）的全身装备骨架缩放原型。原始输入来自 `D:/dsh-tiandao/飞凤苗银(女)`，源模型按当前尺寸等比例乘以 **1.5**，连头饰总高约 **2.542 米**。独立模块 `FeifengScaleTest`，仅单机任务场景启用缩放。

## 测试方法

1. 在启动器启用 **Feifeng Skeleton Scale Test**，位于 Native、SandBoxCore、Sandbox 之后。
2. 用已有作弊物品列表查找“飞凤苗银测试A”或“飞凤苗银测试B”，穿上同一字母的头部、衣裙与手部、腿部与鞋三件。手套、披肩槽留空。
3. **先测 A，再测 B**，每次换好全套后进入村庄、城镇或战斗场景。场景内显示 `Feifeng scale probe A/B applied`，约半秒后应用。
4. 看整体大小、脚是否落地、头颈是否连贯；然后跑步、屈肘、双手武器、拉弓、骑乘。最好与普通角色同框比较。
5. 换回普通装备后重新进入场景，检查恢复。不要混穿 A/B，缩放配置由身体装备决定，其他部件不会自动替换。

背包及角色预览界面不应用运行时补偿，可能显得大小或比例异常；**先以进入场景后的表现判断**。本原型不自动开启作弊、不赠送物品、不修改存档英雄的 BodyProperties。

| 组别 | 装备触发的实验配置 | 目的 |
| --- | --- | --- |
| A | 根骨统一 1.5，其他骨保持 1 | 判断根骨缩放是否向子骨及蒙皮传递 |
| B | 根骨 1.5，加按源解剖标记拟合的逐骨三轴比例 | 判断能否用骨架调整减少源比例改动 |

两组各自有导出补偿网格，在**假定的局部缩放层级模型**中恢复相同的源比例轮廓。动作姿态适配采用骨段旋转，没有把源肢体沿长度强行拉成原生比例；过渡区仍有蒙皮混合。原始尺寸 ×1.5 的独立源文件没有这些补偿变形。

## 验证范围与当前限制

最终 TPAC 已回读检查四级 LOD、材质引用、骨骼索引、权重和、几何及跑步/拉弓预测蒙皮；运行 DLL 对本机游戏程序集编译。四级 LOD 暂用相同的约 1.48 万三角形模型，便于隔离缩放问题。原型不启用物理布料。

**引擎的逐骨缩放传递方式尚未确认，不能据离线预览认定游戏中恢复了 1.5 倍或源比例。**运行时调用 `MBAgentVisuals.ApplySkeletonScale`，不改变 AgentScale；脚落地、碰撞、武器 IK 和骑乘可能与外观缩放不同步，正是此次测试需要确认的项目。游戏测试由你完成，未启动游戏。

预测动作中仍可见袖口、肩部和裙片变形，边长变化指标也偏高；这版通过的是结构检查，**尚未通过外观质量验证**。确认引擎缩放约定后再继续精修绑骨，不能用当前预览证明没有穿模或源比例完全还原。

运行诊断日志：Windows“文档”目录下 `Mount and Blade II Bannerlord/FeifengScaleTest/scale_probe.log`。记录每次应用前后的骨骼名称、rest/current 位置及 AgentScale。判断不符时结合截图、A/B 组别、动作与该日志继续修正。

预测预览保存在 `reports/predicted_A_rest.png`、`predicted_B_rest.png`、`predicted_B_run.png`，由最终 TPAC 计算；它们不是游戏截图。完整结果见 [离线检查](reports/release_validation.json)、[源文件检查](reports/source_validation.json)、[缩放参数与假定](reports/scale_plan.json)。

## 文件与重建

- `input/`：保留原始模型及其修复配置；`tex/`：原始贴图。
- `source/Feifeng_Source_150.blend` 和 `.fbx`：真正等比例放大 1.5 倍的源模型。
- `source/Feifeng_Test_Rigged.blend` 和 `.fbx`：两组运行补偿网格及原生绑定骨架，直接查看不代表游戏缩放后的外观。
- `tools/`：本模组的模型、构建、检查、渲染及运行代码；`module/FeifengScaleTest/`：安装模块；`dist/`：Mod 和源文件 ZIP。

依赖：本机 Bannerlord、Blender 5.2、Anaconda Python（NumPy/Pillow/SciPy）、.NET SDK 及 .NET Framework 4.7.2 参考程序集、`D:/mb-tools` 的 mbtool、工作区 `tools/asset_helpers/` 和 `tools/AssetTool/`。源包保留 source/ 与 tex/ 相邻；共用依赖在原工作区读取，源包中附 `workspace_tools/` 供迁移参考。

按序执行，某一步失败即停止：

```powershell
$taskMod = 'D:/gpt-mb2-mod2/mods/FeifengScaleTest'
$taskBlender = 'D:/Blender Foundation/Blender 5.2/blender.exe'
$taskPython = 'C:/ProgramData/anaconda3/python.exe'
& $taskBlender --background --python-exit-code 1 --python "$taskMod/tools/rig_model.py"
& $taskBlender --background --python-exit-code 1 --python "$taskMod/tools/export_geometry.py"
& $taskPython -B -X utf8 "$taskMod/tools/configure_module.py"
dotnet build "$taskMod/tools/Runtime/FeifengScaleTest.csproj" -o "$taskMod/module/FeifengScaleTest/bin/Win64_Shipping_Client"
& $taskPython -B -X utf8 "$taskMod/tools/build_package.py"
& $taskPython -B -X utf8 "$taskMod/tools/verify_release.py"
& $taskBlender --background --python-exit-code 1 --python "$taskMod/tools/verify_source.py"
& $taskBlender --background --python-exit-code 1 --python "$taskMod/tools/render_review.py"
```

动作 JSON 从当前游戏导出：骨架在 `Native/EmAssetPackages/human/human.tpac`，跑步在 `Native/EmAssetPackages/pack_anim_run/pack_anim_run.tpac`，拉弓在 `Native/EmAssetPackages/pack_anim_1/pack_anim_1.tpac`；命令分别为 mbtool `skeljson` 与 `anim`。使用工作区 `tools/package_delivery.py --mod FeifengScaleTest --version v0.1.0` 打包，首次安装执行本模组 `tools/install_test.ps1`（可先加 `-CheckOnly`）。安装脚本只接受不存在的目标模块并校验 TPAC/DLL，不覆盖旧安装；后续版本使用工作区共用发布安装器，保留上版包并更新版本。

变更记录见 [CHANGELOG](CHANGELOG.md)。本地 Git，不上传远程。
