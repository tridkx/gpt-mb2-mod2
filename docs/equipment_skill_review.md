# 骑砍装备技能只读审查

审查时间：2026-10-06。范围：`C:/Users/DKX/.codex/skills/bannerlord-equipment-mod/` 的 SKILL.md、三个 references 文档、两个 Python 助手和 agents/openai.yaml。未修改技能；迁移前后对全部技能文件做 SHA256 比较。

结论：核心流程完整，可以继续用于本机制作与返修。它明确要求原始输入保护、最终 TPAC 回读、动作检查、源贴图打包、发布字节一致性，并正确区分离线预览与游戏实测。没有要求默认修改 Native，也没有把天香参数规定为新模型通用值。

## 发现

1. **迁移后示例路径失效，需要后续维护。** `references/local-toolchain.md` 的包审查、Blender 命令和生成流程仍指向根目录的 `tools/`、`module/`；`references/asset-workflow.md`、`troubleshooting.md` 也引用旧的专用脚本位置。`scripts/preflight.py` 默认 `--example-workspace` 为工作区根目录，开启 `--require-example-pipeline` 后会找不到已迁移的三个示例脚本。当前使用显式覆盖参数，映射见根 README。本次按只读要求未更改这些文件。
2. **预检覆盖不足，ready 不能视为全流程可运行。** `scripts/preflight.py` 仅用 find_spec 检测 NumPy/Pillow，并检查外部源码路径存在。实际天香回归脚本还使用 SciPy；它也没有检测 Blender 内 Python 依赖能否导入，或执行源码助手的导入。建议后续增加按流程选择的实际导入检查，并继续保留“仅工具清单”的范围说明。
3. **技能依赖工作区和外部工程，不是独立安装即用的工具包。** AssetTool 来自本工作区，几何、贴图及动画助手来自 `D:/gpt-mb2-mod`，TPAC 库来自 `D:/mb-tools`。此依赖已经在文档中声明，属于可移植性限制。迁移机器时仅安装技能不足以完成构建；应同步工具源码、版本及配置。本次保持共用 AssetTool 原路径。
4. **运行时描述与项目构建目标不同。** 技能记载 AssetTool 当前部署运行时为 .NET 10，与现有 runtimeconfig 一致，但 AssetTool.csproj 的 TargetFramework 是 net9.0。部署来自手工编译，重新构建不能默认等同当前 DLL。建议后续统一构建方式及版本记录；本次不重编译该工具。

## 助手检查结果与边界

- `preflight.py` 和 `audit_package.py` 都只读；错误或缺失检查会输出 incomplete。材质审查允许提供外部材质 JSON，并保留未覆盖引用的说明。
- 包审查只覆盖元数据、材料引用及标准 shader 的顶点 Alpha 风险，未覆盖纹理解码、权重、接缝或布料动态。SKILL.md 已明确要求其他检查，因此这不是“完整验证”工具。
- 所有示例模型生成、安装和返修脚本均为工程依赖，不能仅凭技能助手通过就认为新模型完成。新模组需独立适配。
- 本次预检显式指定新示例工程路径后返回 ready；检查结果不代表游戏兼容性实测。

技能保持原样。后续如需更新上述内容，应只修改 Codex 技能目录中的这一份。

本次迁移后对天香最终包执行技能自带 audit_package.py，结果 pass：23 个资产校验及元数据往返一致，9 个材质、56 个子网格引用完整，覆盖 LOD0–LOD3。此结果仍只代表该助手声明的检查范围。
