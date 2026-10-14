# Bishui Qingluan Female Race

碧水青鸾女性完整角色种族，模块 ID `BishuiQingluanFemaleRace`，首版 `v0.1.0`。源模型来自 `D:/dsh-tiandao/碧水青鸾-女`，保留原脸、身体比例、衣裙、头发和贴图。

提供内部种族 `bql_qingluan`、28 骨自定义绑定骨架 `bql_skeleton`、完整身体 `bql_body`、四级 LOD，以及独立女性测试兵种 `bql_test`（“碧水青鸾”）。原版招募线与升级树不变，可通过控制台或兵种工具使用测试兵种。

## 安装与使用

`dist/BishuiQingluanFemaleRace_Mod.zip` 顶层是模块目录，解压至游戏 `Modules/`。本机目标为 `D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/BishuiQingluanFemaleRace`。启动器启用 **Bishui Qingluan Female Race**，放在 Native、SandBoxCore、Sandbox 后。

按本机 Native `v1.4.8` 构建。固定外观包含衣服与双手，使用此种族时保留空防具槽，武器、盾和坐骑可另外配置。[RaceTroopBuilder](../../RaceTroopBuilder/README.md) 可用于后续兵种编排；本模块未替换原版兵种。

## 布料与动作

裙摆使用共同环向／高度驱动面，重叠裙层共用对应关系，保留原始层间偏移。代理按裙层内侧采样，可见网格不因代理简化而改变。左右袖片、长发、飘带及长头饰保持各自连接区域。腰部、肩口、袖口和发根作为固定／蒙皮区域，悬垂部分使用游戏布料。下部裙摆的蒙皮参考有限跟随左右大腿，不受小腿和脚部直接牵引。

LOD0、LOD1 带原生布料映射和匹配预处理数据，LOD2、LOD3 使用简化蒙皮。模型原姿势与尺寸保留，关节和手臂绑定方向适配本角色。按当前 Native 动作目录补齐种族场景动作集，提供固定女性待机和本种族物品栏骨架适配组件。未制作捏脸形变、面部表情、主角切换或固有护甲逻辑。

## 工程与重建

`input/` 保留原始 FBX、OBJ、贴图和原配置；`source/` 保存可编辑 Blend、FBX，`tex/` 与其相邻。专用脚本和参数在 `tools/`，游戏模块在 `module/BishuiQingluanFemaleRace/`，检查与预览在 `reports/`，缓存在 `build/`，交付包在 `dist/`。

依赖 Blender 5.2、Python（NumPy、SciPy、Pillow、Matplotlib）、.NET 10、`D:/mb-tools` 和游戏资源。共用工具位于工作区根 `tools/asset_helpers/`、`tools/cloth_compiler/`、`tools/cloth_simulator/`；源包保存为 `workspace_tools/`，恢复到工作区根 `tools/` 后可重建。

从工作区根运行：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/TiandaoRaceCollection/BishuiQingluanFemaleRace/tools/rebuild.py
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 tools/package_delivery.py --mod BishuiQingluanFemaleRace --version v0.1.0 --check-only
./tools/install_release.ps1 -Mod BishuiQingluanFemaleRace -Version v0.1.0 -CheckOnly
```

后两条仅检查，安装去掉 `-CheckOnly`；已有交付包时提供旧版版本号，保留历史包。

## 检查范围与注意事项

- 最终结构、贴图回读、源比例、权重、动作与注册检查：[release_validation.json](reports/release_validation.json)。源文件重开：[source_validation.json](reports/source_validation.json)。映射与几何保留：[mapped_structure_validation.json](reports/mapped_structure_validation.json)。
- [cloth_diagnostics.json](reports/cloth_diagnostics.json) 分别记录不支持的渲染映射检查与支持的代理近似模拟；`incomplete`、`needs_review` 均不表示游戏通过。采样率由当前 Native AnimationClip 时长推导，见 [animation_rates.json](reports/animation_rates.json)。
- `final_rest_*` 是最终包静态预览，`final_*_worst` 是纯蒙皮风险图，`final_cpu_*` 是近似代理模拟加原生映射检查图，均不是游戏截图。
- 多层共同驱动没有引擎自碰撞保证。长袖抬臂、跑步腿部避让、骑乘、武器握持、界面人物预览和近远 LOD 均需实机复测。近似胶囊检查不能替代游戏观感和性能验收。
- 当前离线动作与代理预览仍提示腿部穿裙、袖片折叠和局部拉伸风险。首版用于游戏复测，布料视觉验收尚未通过；用户反馈后按对应动作继续返修。

游戏由用户测试，状态见 [game_acceptance.json](reports/game_acceptance.json)，版本记录见 [CHANGELOG.md](CHANGELOG.md)。
