# Feifeng Skeleton Scale Test v0.1.3

飞凤苗银（女）的全身装备骨架缩放原型。原始输入来自 `D:/dsh-tiandao/飞凤苗银(女)`，源模型按当前尺寸等比例乘以 **1.5**，连头饰总高约 **2.542 米**。独立模块 `FeifengScaleTest`，仅单机任务场景启用缩放。

## 单骨诊断测试方法

本版用 **E、F** 两组隔离头骨缩放。两组的头、身体和腿都引用同一套 A 网格，因此外观差异不再来自导出几何。旧 A/B/C/D 装备保留，但本版不触发它们的旧缩放方案。

1. 启用 **Feifeng Skeleton Scale Test**，位于 Native、SandBoxCore、Sandbox 之后。
2. 查找“飞凤苗银矩阵E一次”，穿上头、衣裙与手部、腿部与鞋三件；手套、披肩槽留空。
3. 进入村庄或战斗，下马，用能看到头部的镜头观察。只处理玩家角色，不处理士兵或坐骑。
4. 场景自动运行：正常 **6 秒** → 头骨 2 倍 **12 秒** → 恢复 **6 秒** → 再次头骨 2 倍 **12 秒** → 恢复并结束。每个阶段有英文提示。保持场景正常运行，不要打开菜单或暂停。最好录制这一段，或在正常与 `HEAD x2` 阶段各截一张同角度近景。
5. 换穿“飞凤苗银矩阵F持续”全套，重新进入场景，重复观察。每次重进场景重新计时。

| 组别 | 调用方式 | 用途 |
| --- | --- | --- |
| E | 每个放大阶段仅调用一次，头骨索引 13，三轴均为 2 | 检查单次调用及其持续性 |
| F | 放大阶段每次显示更新前调用相同参数 | 检查持续重施能否维持效果 |

两组直接写入头骨局部矩阵，然后调用 `UpdateEntitialFramesFromLocalFrames`，不调用旧的 `ApplySkeletonScale` 或 `ForceUpdateBoneFrames`。依据当前动画的颈骨与头骨矩阵计算局部姿态，保留头骨局部原点，将三个轴设为静止参考长度的 2 倍；每次均设为绝对长度，避免倍率累积。正常阶段、装备切换及场景结束时尝试恢复参考轴长度，并保留当前头部朝向与局部原点。若有累积放大、闪烁或头颈异常，记录阶段与组别；这些均是诊断结果，不能直接作为成品效果。

背包界面不运行该测试。头骨索引和名称在运行时检查；只有 E/F 身体装备触发，头部也必须穿同组，否则原生头部或其他模组头部会混入观察。仅单机使用，不修改存档英雄的 BodyProperties 或 AgentScale。

原始源文件仍是当前源尺寸 ×1.5；这一版的 **头骨 ×2 仅用于诊断接口**，不代表最终模型倍率。

## 验证范围与当前限制

最终 TPAC 已回读检查四级 LOD、材质引用、骨骼索引、权重和、几何及跑步/拉弓预测蒙皮；运行 DLL 对本机游戏程序集编译。四级 LOD 暂用相同的约 1.48 万三角形模型，便于隔离缩放问题。原型不启用物理布料。

**引擎的逐骨缩放传递方式尚未确认，不能据离线预览认定游戏中恢复了 1.5 倍或源比例。**当前只诊断头骨局部矩阵对蒙皮的影响，不改变 AgentScale。直接矩阵更新可能被动画覆盖，也可能被蒙皮计算忽略；重建骨架帧是否影响其他骨骼同样需要检查，尚未验证全身缩放、碰撞、武器 IK 或骑乘。本版游戏测试由你完成，未启动游戏。

预测动作中仍可见袖口、肩部和裙片变形，边长变化指标也偏高；这版通过的是结构检查，**尚未通过外观质量验证**。确认引擎缩放约定后再继续精修绑骨，不能用当前预览证明没有穿模或源比例完全还原。

运行诊断日志：Windows“文档”目录下 `Mount and Blade II Bannerlord/FeifengScaleTest/local_frame_probe_v0.1.3.log`。记录版本、阶段、调用次数、骨索引映射、完整静止/当前骨骼矩阵、AgentScale，以及显示前和后续场景更新的采样。关节原点不变并不等于蒙皮没有缩放；应同时检查矩阵轴和实际头部外观。

本版直接矩阵算法已对编译后 DLL 检查：旋转父骨下的局部转换、头骨原点保留、三轴 2 倍、连续 1000 次无累积及恢复 1 倍。详见 [局部矩阵检查](reports/local_frame_validation.json)。这些是离线矩阵计算，不证明引擎接受了写入或蒙皮实际变化。

历史测试结果见 [v0.1.2 游戏反馈](reports/game_v0.1.2_result.json)：用户未看到 C 头部变大，C/D 外观与 A 相近；完整日志显示 C 调用 2 次、D 调用 2278 次，头骨轴长度始终约 1，未观测到预期效果。

`reports/predicted_A_rest.png`、`predicted_B_rest.png`、`predicted_B_run.png` 仍是旧 A/B 假定缩放模型的离线预测，不是 E/F 的游戏结果。结构结果见 [离线检查](reports/release_validation.json)、[源文件检查](reports/source_validation.json)；旧方案见 [缩放参数与假定](reports/scale_plan.json)，历史可见性返修见 [检查记录](reports/visibility_repair.json)。

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
& $taskPython -B -X utf8 "$taskMod/tools/verify_single_bone.py"
```

单骨检查会比较 `dist/FeifengScaleTest_v0.1.2_Mod.zip` 的 TPAC 字节，需要保留该基线包。它同时执行编译后 DLL 的阶段边界与参数检查，但不会调用原生游戏接口。

动作 JSON 从当前游戏导出：骨架在 `Native/EmAssetPackages/human/human.tpac`，跑步在 `Native/EmAssetPackages/pack_anim_run/pack_anim_run.tpac`，拉弓在 `Native/EmAssetPackages/pack_anim_1/pack_anim_1.tpac`；命令分别为 mbtool `skeljson` 与 `anim`。使用工作区 `tools/package_delivery.py --mod FeifengScaleTest --version v0.1.3` 打包，首次安装执行本模组 `tools/install_test.ps1`（可先加 `-CheckOnly`）。安装脚本只接受不存在的目标模块并校验 TPAC/DLL，不覆盖旧安装；已有 v0.1.2 时使用工作区 `tools/install_release.ps1 -Mod FeifengScaleTest -Version v0.1.3 -PreviousVersion v0.1.2`，保留上版包并更新安装。

变更记录见 [CHANGELOG](CHANGELOG.md)。本地 Git，不上传远程。
