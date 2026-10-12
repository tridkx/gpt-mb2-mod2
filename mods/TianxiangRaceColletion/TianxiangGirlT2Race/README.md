# Tianxiang Girl T2 Mu Feng Race

第二套“沐风为裳”完整人物种族 Mod，版本 v0.1.3，适用本机 Native v1.4.8。模块 ID `TianxiangGirlT2Race`，种族 `txgirl2`，骨架 `txgirl2_skeleton`。可与第一套分别启用，保留源固定脸、衣服、头发、双手和修正过的眼周 UV。

## 当前功能

源网格统一换算成米，含头发总高约 1.335 米，没有拉伸脸、身体或四肢。14 个源网格使用独立测量的 28 骨绑定；肩、肘、腕位置和上臂、前臂方向按本模型确定，武器挂点位于掌心附近。四级 LOD 面数为 18986、14848、11615、9125。薄上衣与裙片保留原始几何精度，避免减面后落入皮肤内侧；其余部件随距离减面。实际游戏身高、握持和命中范围仍需游戏验收。

物品栏、队伍与百科预览使用本种族骨架和动作集，包含第一套已验收的物品栏入口修复。辅助遍历排除值类型，按引用判重，地图入口跳过；男女 warrior 物品栏待机均映射自然垂手片段，保留所选性别。当前版本待用户游戏验收。

裙子在全部四级 LOD 使用纯骨骼蒙皮，保留源网格、UV、腰臀连续随动和各裙片的原始位置。游戏布料标记、原生布料求解数据及腿部布料碰撞引用已关闭，裙片按参考造型随角色骨骼移动，保持正面包裹的位置。源 Blend/FBX 中的布料活动距离为 0。

新增女性测试兵种“天香沐风少女”（`txgirl2_test`），等级 6，沿用帝国新兵技能与四种武器组合，无防具、固有护甲和升级分支。它不覆盖原版兵种，不加入原版招募池。后续可用 [Race Troop Builder](../../RaceTroopBuilder/README.md) 拼装。

## 安装与游戏验收

在启动器启用 **Tianxiang Girl T2 Mu Feng Race**，排在 Native、SandBoxCore、Sandbox 后。使用测试存档，百科搜索“天香沐风少女”；已启用作弊的战役可执行：

```text
campaign.add_troops txgirl2_test | 5
```

重点检查创建角色和物品栏中手臂位置、待机垂手、左右手与单手／双手武器的间距，站立时正面裙片包裹位置、腰臀贴合，以及跑步、抬腿和骑乘时的裙片变形及安全裤遮盖。再检查脸、睫毛、肩袖、手腕接缝及远近 LOD 切换。日志位于系统文档目录 `Mount and Blade II Bannerlord/TianxiangGirlT2Race/ui_runtime_v0.1.3.jsonl`。依赖本模块的存档不能在停用模块后继续使用。

## 当前限制

固定脸，没有捏脸形变、表情或手指动态握持。裙子、袖片、头发均随骨骼移动；裙子没有独立飘动和腿部布料碰撞，较大抬腿或骑乘动作可能与裙片交叉。离线检查证明源比例、资源结构、绑定和采样动作没有严重拉裂，实际游戏造型与动作仍需用户验收。

## 工程与重建

`input/original/` 保留第二套原始目录与历史输入；`input/` 是构建输入，`source/` 保存 Blend/FBX，与 `tex/` 相邻。模型专用脚本和参数位于 `tools/`，游戏模块位于 `module/TianxiangGirlT2Race/`，检查与预览位于 `reports/`，缓存与交付包分别位于 `build/` 和 `dist/`。

依赖 Blender 5.2、Anaconda Python（NumPy、SciPy、Pillow、lxml）、.NET SDK、net472 引用程序集、mbtool、AssetTool、本机 Native 与工作区共用资源工具。源包中的 `workspace_tools/` 恢复到工作区根 `tools/`，外部二进制另行准备。

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/TianxiangRaceColletion/TianxiangGirlT2Race/tools/rebuild.py
./tools/install_release.ps1 -Mod TianxiangGirlT2Race -Version v0.1.3 -CheckOnly
```

首次安装去掉 `-CheckOnly`。已有交付包升级须提供真实旧版本 `-PreviousVersion`，不覆盖同版本历史交付。

证据见[最终资源](reports/release_validation.json)、[源文件](reports/source_validation.json)、[纯蒙皮裙片检查](reports/skeletal_skirt_validation.json)、[绑定与挂点](reports/binding_validation.json)、[预览入口](reports/ui_scope_validation.json)、[待机映射](reports/preview_idle_validation.json)、[注册](reports/registration_validation.json)、[返修范围](reports/cloth_fit_revision_validation.json)和[正面预览](reports/final_rest_front.png)。旧布料方案的记录保留在 `reports/history/`，不作为当前版本使用依据。版本记录见 [CHANGELOG](CHANGELOG.md)。
