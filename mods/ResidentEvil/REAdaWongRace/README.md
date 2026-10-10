# Resident Evil - Ada Wong Race

v0.1.2 为本机 Native v1.4.8 制作固定外观的艾达王种族 `reada_wong`。只替换帝国普通新兵 `imperial_recruit`，游戏内名称为“艾达王新兵”；保留原兵种等级、技能、武器与升级目标，升级后进入原版兵种。贵族新兵及其他兵种不在修改范围内。

## 外观与行为

默认红色针织衫、短裙、手套、过膝长靴、脸和头发组成完整种族身体。枪套、枪械、钩枪、携行绑带及相关金属挂件已移除。靴子本身的结构保留。防具栏为空，衣服为种族身体外观，不提供装备护甲数值。

从原始 cha200 OBJ 制作，所有保留部件的顶点只做 Y-up → Z-up 的坐标轴转换，不做人体拉伸、RBF 变形、手脚位置拟合或鞋底抬升。源模型的头身比、肩宽、臂长、腿长、衣服与脸部轮廓保留。最高精度 LOD0 保留原始顶点位置，清除退化三角形；去除头部模型附带、永久藏在高领衫内部的下颈部扩展面，避免动作中穿出衣服，外露颈部与腕部保留。远景 LOD 另做简化。

自定义绑定骨架 `adar_skeleton` 保留骑砍原生 28 骨语义、顺序和层级，关节位置按艾达原始骨架测量建立；躯干及四肢骨段按原模型绑定方向建立，脚骨保留原生动作的中立方向，维持原始高跟鞋的足部倾角。骨架适配模型，网格不适配原生成人体型。沿用原生动作轨道，离线检查采用最终绑定骨架计算；游戏的动作合成、重定向与 IK 仍需验收。基础模型含头发高约 1.729 米，skin 的 min_scale 为 1.10，通过运行时统一缩放放大整体身体与骨架；基础模型和绑定数据保持原始比例。实际游戏身高与站姿由用户验收。

双手始终在身体网格中。左右手分别刚性绑定到原生手骨，手指保持固定张开姿态，腕部与前臂使用渐变过渡；本版不启用手势形变。短裙、头发与衣服采用蒙皮随动，没有游戏布料模拟。近景至远景四级 LOD 为 154,473 / 39,498 / 24,077 / 21,200 三角面，不含内部四面占位网格。

鞋底与细跟在各级 LOD 中刚性跟随对应脚骨，不受脚趾弯曲影响；靴面下部保持鞋形，靴筒在踝部平滑过渡。鞋形、踝部关节位置和其他身体部位的数据保持原始形状。专项检查及同镜头前后预览见 [heel_validation.json](reports/heel_validation.json)、[修正前](reports/heel_before.png)与[修正后](reports/heel_after.png)。

## 安装与游戏验收

模块 ZIP 顶层为 `REAdaWongRace/`，安装到游戏的 `Modules/`。启动器勾选英文名 **Resident Evil - Ada Wong Race**，排在 Native、SandBoxCore、Sandbox 之后。

1. 使用测试存档，查看帝国普通新兵的招募、队伍、百科和物品预览，检查完整外观、朝向、站姿与双手。
2. 战斗检查站立、跑步、挥砍、持盾；有条件时检查持弓、骑乘和死亡倒地。
3. 检查短裙、肩袖、手腕、靴筒及头发，观察远近 LOD 切换、身高与脚底位置。
4. 确认升级后进入原版兵种，贵族新兵与其他兵种保持原版。

退出游戏后取消勾选可停止覆盖。含此种族角色的测试存档应保留模块；不要以唯一正式存档测试。

## 当前限制

- 最高精度约 15.4 万面，第一版优先保留原始外形；大规模同屏性能尚未验收。
- 固定脸和手型，没有捏脸、面部表情、眨眼、动态手指握持或玩家创建页种族选择功能。
- 缺失原始头发、眉毛和睫毛透明遮罩，使用不透明材质；部分 PBR 贴图使用平法线和保守参数。材质可用性与原作 shader 还原程度不同，见 [材质检查](reports/material_recovery.json)。
- 原始上衣贴图包含部分携行挂件的烘焙阴影；挂件几何已移除，首版仍保留这些贴图痕迹。
- 自带衣服为完整身体的一部分，自由换装和体型滑块不在本版兼容范围内。
- 离线原生蒙皮检查不能验证游戏 IK、实际握持、马匹碰撞、所有穿模或大规模战斗性能。游戏验收尚未完成，由用户测试。

## 工程与重建

`input/` 保存 cha200 模型与 cha800 权重参考副本；`source/` 保存 Blend/FBX；相邻 `tex/` 保存纹理。`tools/` 为本模型制作脚本和参数；`module/REAdaWongRace/` 为运行模块；`reports/` 为检查报告与最终资源离线预览；`build/`、`dist/` 分别为缓存和交付包。

依赖 Blender 5.2、Anaconda Python（NumPy、SciPy、Pillow、lxml）、.NET 10、mbtool、AssetTool、工作区 `tools/asset_helpers/`、当前游戏及 `D:/dsh-mod/re4-remake/tools/RE-Mesh-Editor-main` 解析库。原始提取工程只读，不修改 Native 或旧装备模块。

从工作区根运行：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/ResidentEvil/REAdaWongRace/tools/rebuild.py
```

主流程：注册 → 模型与纹理 → 可编辑源文件 → LOD → TPAC → 最终包回读及动作检查 → 源文件重开 → 四级预览。原始外形对照见 [geometry_fidelity.json](reports/geometry_fidelity.json)。发布检查入口为 [release_validation.json](reports/release_validation.json)，兵种替换验证为 [registration_validation.json](reports/registration_validation.json)。整体放大检查见 [scale_validation.json](reports/scale_validation.json)；现有离线预览展示基础模型与动作蒙皮，不包含游戏运行时的 skin 缩放。保留 v0.1.0 模块 ZIP 时，将其放在 `dist/REAdaWongRace_v0.1.0_Mod.zip`，重建流程会自动补做高跟鞋基线回归与近景对比；原始数据缓存缺失时会从该包恢复基线。

源 ZIP 保持 `source/`、`tex/` 相邻，并在 `workspace_tools/` 保存所用共享助手。恢复时将共享源码放回工作区 `tools/`，本工程放在 `mods/ResidentEvil/REAdaWongRace/`。工具二进制与第三方模型再分发授权不随源包提供。

### 注意事项

本模块与 WuduRaceTest 都替换帝国普通新兵；同时启用时后加载的兵种覆盖可能生效。测试艾达时取消勾选五毒测试模块及其他覆盖该新兵的模块。已有艾达装备模组使用独立资源名；给本种族额外穿整套艾达装备可能重复显示或遮盖身体。

固定外观仍需保留原生发型/胡须容器属性及零号占位条目，缺少这些结构可能在启动或角色预览时失败。运行骨架使用艾达自身的绑定参数，UI 动作继承原生男女动作集；不采用五毒的尺寸、关节坐标或 facegen 动作覆盖。结构与离线检查不证明游戏预览姿势已验收。

版本记录见 [CHANGELOG](CHANGELOG.md)。
