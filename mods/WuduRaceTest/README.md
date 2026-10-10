# Wudu Canglan Race Test

v0.1.2 是针对本机《骑马与砍杀 2：霸主》Native v1.4.8 的最小种族验证版。使用 `01苍蓝流苏` 完整角色模型，自定义种族 `wdr_canglan` 和 28 骨绑定骨架，只替换帝国普通新兵 `imperial_recruit`。游戏内名称为“五毒苍蓝新兵（种族验证）”。贵族新兵和 2 号模型尚未制作。

## 当前行为与限制

模型只进行统一厘米到米换算和朝向旋转，没有重新塑形或改变头身、四肢比例，含头饰总高约 1.369 米。衣服、头发、脸和身体一起作为种族网格，防具栏为空；没有添加固有护甲。保留原兵种等级 6（T1）、技能、武器和升级路线，升级后进入原版兵种。

已通过最终 TPAC 回读、骨架和权重检查、原始顶点对照、XML 合并检查及 Blend/FBX 重开检查。[离线报告](reports/release_validation.json)的通过范围仅为文件和结构；游戏加载、百科显示、动作重定向、IK、实际比例及命中表现尚未实测。当前使用固定脸，粗略绑骨，无布料、穿模修复或 LOD 简化，适合少量士兵验证。

## 游戏测试

1. 启动器勾选 **Wudu Canglan Race Test**，排在 Native、SandBoxCore、Sandbox 之后。第一轮建议临时沙盒新档，避免已有兵种修改模组覆盖测试兵种。
2. 百科打开帝国普通兵种树，查看“五毒苍蓝新兵（种族验证）”。确认完整模型、贴图和原始头身比例是否出现。
3. 在帝国地区招募少量普通新兵，进入战斗或场景，与原版成人并排查看。重点检查整体高度、头身比例及站立/行走/持武器时是否被拉伸；本轮不以裙摆穿模或布料表现作为通过条件。
4. 若加载失败、模型缺失或被拉伸，保留报错及诊断日志。日志写入系统“文档”下的 `Mount and Blade II Bannerlord/WuduRaceTest/probe_v0.1.2.log`，记录种族加载、兵种等级、场景骨架和防具栏。DLL 只采集诊断，不修改比例或战斗公式。

退出测试后取消勾选本模块即可。测试存档应保留本模块，正式档建议等实机验证通过后再使用。

## 自动战斗

已经核对本机游戏 DLL：普通兵基础战力按兵种阶级计算，不直接读取护甲值或武器伤害数值。该 T1 新兵自动得到原版基础战力 0.66，无需额外设置；装备可能通过坐骑和远程身份影响类别判定。地形、攻守、领队特长、战术特长和士气会继续参与模拟。本版未修改自动战斗；未来若添加固有 30 身甲，它不会自动提高这个基础战力。详细依据见[机制核对记录](reports/autoresolve_analysis.md)。

## 注意事项

固定头发模型也必须保留原版 hair_meshes/group_id 容器及第 0 个无发型 hair_mesh，beard_meshes 也保留第 0 个无胡须 beard_mesh。删容器会在启动加载时崩溃；把容器清成零条目会在角色/招募预览生成时崩溃。这些占位条目不引用额外网格，原模型头发仍在种族身体里。重建检查同时验证节点、属性和零号条目。

## 工程与重建

- `input/`：原始模型副本；`source/`：可编辑 Blend、FBX；相邻 `tex/`：原始贴图。
- `module/WuduRaceTest/`：游戏模块；`tools/`：本模型的制作、打包、回读和诊断源码。
- `reports/`：检查结果与离线预览；`build/`：缓存；`dist/`：模块和源文件 ZIP。

依赖本机 Blender 5.2、Anaconda Python（NumPy、SciPy、Pillow、lxml）、.NET SDK、net472 引用程序集、mbtool、AssetTool、本机游戏资源及工作区 `tools/asset_helpers`。脚本中的工具路径为本机路径，迁移后需调整。源 ZIP 附带所用共享 Python 文件于 `workspace_tools/`；恢复到多模组工作区时，将它们对应放到根 `tools/`，本项目放到 `mods/WuduRaceTest/`。

从 `D:\gpt-mb2-mod2` 重建：

```powershell
& 'C:\ProgramData\anaconda3\python.exe' -B -X utf8 mods/WuduRaceTest/tools/rebuild.py --preserve-input
```

`--preserve-input` 使用现有输入与模块配置；不带它会从原始输入目录重新复制并生成配置。检查通过后按工作区安装流程打包、安装本模块，不启动游戏。源 ZIP 不附带游戏原版资源、工具二进制或第三方模型的再分发授权。

版本记录见 [CHANGELOG](CHANGELOG.md)。
