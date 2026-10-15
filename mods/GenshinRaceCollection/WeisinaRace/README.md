# Weisina Race

薇斯纳完整人物固定外观种族。模块 ID `WeisinaRace`，内部种族 ID `weisina`，启动器英文名 `Weisina Race`。针对本机 Native v1.4.8 制作。

## 使用

本角色随 [Genshin Race Collection 合集](../README.md) 安装，启动器只需启用一个合集模块。内部种族 ID 和测试兵种保持独立。`module/WeisinaRace/` 是角色构建中间模块；不要与合集同时安装，以免资源和种族重复注册。

新增独立女性测试兵种 `weisina_test`，不替换原版招募与兵种树。在启用作弊模式和开发者控制台的测试存档中使用：

```text
campaign.give_troops weisina_test 10
```

兵种拼装器可选择种族 `weisina`、女性，移除头部、身体、腿部、手套和披风防具，保留需要的原版武器与坐骑。角色自带服装、头发和双手；普通防具可能叠加或遮盖外观。使用本种族的存档依赖此模块。

## 外观与布料

保留所选 PMX 的固定脸、服装、身体比例和 UV。模型与骨架统一换算为每源单位 0.08 米，静态整体高度约 1.641 米。采用自有 28 骨绑定骨架，按源关节位置校准，沿用骑砍原生动作；源权重映射后补平滑肩部、腰部与胯部过渡。四级 LOD 保留关键切口及脸部轮廓。

启用后部长发的有限布料摆动，刘海、帽子和衣裙保持普通蒙皮。 **裙子不启用布料模拟**。头发方案：后部卷曲长发启用较小摆动范围，前发与翅膀固定。含布料时各级渲染 LOD 使用自身映射段，代理、固定区、碰撞尺寸与活动范围属于当前角色，参数见 [模型配置](tools/model_config.json)。

选用 `input/original/薇斯纳.pmx`。忽略的附属／备用模型：武器.pmx、法杖.pmx、魔法剑1.pmx、魔法剑2.pmx。原始压缩包和完整解包内容保留在 `input/`，这些附属模型不进入运行资源。重复的 MMD 高光／sphere 网格只排除经检查重叠的渲染层；具体几何范围见 [准备报告](reports/preparation.json)。

## 检查与当前限制

当前版本的[运行资源检查](reports/runtime_resource_fix.json)覆盖 BC 纹理尺寸和原生驱动角色：BC 顶层尺寸满足 4 像素对齐；含长发布料时代理仅由可见网格引用，清除代理的直接渲染布料标记、身体绑定和三个附加开关，与 Native 模拟网格相同。独立透明材质仅作防护，不作为代理未显示的实机证据。模型、UV、骨架、权重与布料数据保留，创建页面加载和头发实机表现仍待复测。

[最终资源报告](reports/release_validation.json)覆盖 TPAC 回读、骨架、材质、UV、量化权重、所有交付 LOD 与原生动作。跑步、持弓、挥击和骑乘扫描完整提取片段；界面／捏脸基础站姿仅作抽样姿态检查，不提供外观定制功能。[源文件检查](reports/source_validation.json)确认重新打开 Blend/FBX 后仍保留源比例和 UV。

映射布料的 CPU 渲染诊断仍为 `incomplete`；另检查直接模拟代理的动作轨迹。代理报告中的碰撞、拉伸提示属于近似诊断，不当作游戏通过或失败。初次接入使用报告模式。 诊断采样暂按 60 fps，尚未对齐所有游戏动作播放速度。离线报告与 [游戏验收](reports/game_acceptance.json)独立记录。

固定外观，无捏脸形变、面部表情或手指握持形变。源颜色贴图配合平坦法线和保守材质控制，MMD toon／高光显示与游戏 PBR 不完全相同。普通蒙皮衣裙在骑乘、深蹲和大幅动作中可能折叠或穿模。游戏测试由用户完成，检查队伍、百科、物品栏、战场主要动作及远近 LOD；助手不启动游戏。

人物预览组件只处理本种族的 CharacterTableau、BasicCharacterTableau 和 BodyGeneratorView；合集中的新角色共用一次界面发现，再按种族调用各自修正函数。

## 工程与重建

工程位于 `mods/GenshinRaceCollection/WeisinaRace/`。`source/` 保存可编辑 Blend/FBX，贴图在相邻 `tex/`；参数和独立入口在 `tools/`，角色构建模块在 `module/WeisinaRace/`，缓存和检查分别位于 `build/`、`reports/`。可安装模块和合集交付位于上级的 `module/GenshinRaceCollection/` 与 `dist/`。

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/GenshinRaceCollection/WeisinaRace/tools/rebuild.py
```

依赖 Blender 5.2、本机 Python（NumPy、SciPy、Pillow）、.NET 10／.NET Framework 4.7.2 引用程序集、Native v1.4.8、mbtool、已安装 MMD Tools PMX 读取器与工作区共用工具。共用实现及源包恢复方法见 [PMX 流程说明](../../../tools/pmx_race_pipeline/README.md)。原始模型的作者规则在 `input/original/`，当前工程与包用于个人本地适配，不上传远程。

[合集源文件包](../dist/GenshinRaceCollection_Source.zip)、[更新日志](CHANGELOG.md)、[合集入口](../README.md)。
