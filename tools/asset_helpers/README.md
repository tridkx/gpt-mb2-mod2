# 共用装备资源助手

2026-10-08 从 `D:/gpt-mb2-mod` 复制当前两个模组实际使用的依赖及其导入依赖，原目录保持不变。`migration_manifest.json` 记录原路径、目标路径和复制时的 SHA256。复制的九个文件未改动内容。

| 路径 | 用途 |
| --- | --- |
| `pipeline/build_assets.py` | 模组脚本导入 `vertex_tangents` |
| `pipeline/convert_textures.py` | 模组脚本导入 `encode_mips` |
| `pipeline/paths.py` | 查找游戏、mbtool 及其 Python 库 |
| `config/spec.py` | 前两项导入时需要的旧工程规格 |
| `tools/georead.py` | GDMB 几何读取 |
| `previewer/baker/skeleton.py`、`animation.py` | 骨架、原生动画与离线蒙皮 |
| `previewer/baker/__init__.py`、`config.py` | baker 包初始化依赖 |

这里是共用函数的依赖集合，不是旧工程的完整制作流程或完整网页预览器。`spec.py` 和两个 pipeline 文件仍含旧工程的专用规格与命令行构建逻辑；当前模组只导入所需函数，不直接运行这些文件制作新模组。制作、检查、预览继续使用 `mods/<ModId>/tools/` 中的入口。旧模型、产物、缓存和历史资料未复制。

## 依赖与预检

仍需本机游戏资源、Blender、Python（NumPy、Pillow；示例检查还需 SciPy）、Git、.NET，以及 `D:/mb-tools` 中的 mbtool 和 `py/bcencode.py`。AssetTool 保持在工作区 `tools/AssetTool/`。本次仅合并旧工程助手，不合并游戏或 mbtool。

在工作区运行：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 tools/preflight.py --require-example-pipeline --check-blender-python
# 其他模组指定自己的工程：
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 tools/preflight.py --example-workspace mods/HanfuBlueRed --require-example-pipeline --check-blender-python
```

此入口调用唯一已安装技能的预检脚本，只指定当前工作区。已安装技能的原预检脚本现默认从选定工作区根的 `tools/asset_helpers/` 读取助手；从 `mods/<ModId>/` 运行时也会识别工作区根。直接运行原脚本无需传入 `--helpers`，仅在使用其他助手目录时才覆盖它。技能内工具与动画说明已同步，不再需要旧工程目录。预检只核对工具与导入，不生成模型或启动游戏。
