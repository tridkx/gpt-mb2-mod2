# 共用装备资源助手

几何、贴图、骨架和动画函数的共用依赖集合，供模组 tools/ 中的制作和检查入口导入。

| 路径 | 用途 |
| --- | --- |
| `pipeline/build_assets.py` | 模组脚本导入 `vertex_tangents` |
| `pipeline/convert_textures.py` | 模组脚本导入 `encode_mips` |
| `pipeline/paths.py` | 查找游戏、mbtool 及其 Python 库 |
| `config/spec.py` | 前两项导入时需要的旧工程规格 |
| `tools/georead.py` | GDMB 几何读取 |
| `previewer/baker/skeleton.py`、`animation.py` | 骨架、原生动画与离线蒙皮 |
| `previewer/baker/__init__.py`、`config.py` | baker 包初始化依赖 |

制作、检查和预览使用对应模组 tools/ 中的入口，本目录提供被导入的共用函数。

## 依赖与预检

仍需本机游戏资源、Blender、Python（NumPy、Pillow；示例检查还需 SciPy）、Git、.NET，以及 `D:/mb-tools` 中的 mbtool 和 `py/bcencode.py`。AssetTool 保持在工作区 `tools/AssetTool/`。

在工作区运行：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 tools/preflight.py --require-example-pipeline --check-blender-python
# 其他模组指定自己的工程：
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 tools/preflight.py --example-workspace mods/HanfuBlueRed --require-example-pipeline --check-blender-python
```

此入口调用唯一已安装技能的预检脚本，只指定当前工作区。已安装技能的原预检脚本现默认从选定工作区根的 `tools/asset_helpers/` 读取助手；从 `mods/<ModId>/` 运行时也会识别工作区根。直接运行原脚本无需传入 `--helpers`，仅在使用其他助手目录时才覆盖它。预检只核对工具与导入，不生成模型或启动游戏。

## 注意事项

spec.py 和 pipeline 文件包含来源工程专用规格，不能作为新模组通用构建器直接运行；仅导入所需函数。依赖来源、原路径和复制时 SHA256 保存在 migration_manifest.json；历史更新见 [工作区日志](../../docs/CHANGELOG.md)。
