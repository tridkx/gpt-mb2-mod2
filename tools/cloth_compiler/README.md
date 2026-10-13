# Bannerlord 离线布料编译器

从原生 `b97e0f10-df49-4666-8f1d-ada6630d4b4e` 数据段逆向得到的直接模拟工具。无需 Blender Cloth、官方编辑器或 Computer Use。格式已在七个原生样本上逐字节往返验证；明玉 v1.0.4 由用户确认近距离布料有效，远距离和 LOD1 的实际求解尚未确认。该案例不代表所有模型或引擎版本均可用。

| 文件 | 职责 |
| --- | --- |
| `cloth_payload.py` | 13 个计数数组的完整读写、编辑器几何读取、位置解码 |
| `cook_cloth.py` | 抗拉/弯曲约束、并行分组、三角分组、位置/法线压缩、骨骼与测地锚点 |
| `validation.py` | 数组长度、索引、分组覆盖、并行写冲突、锚点检查 |
| `NativeClothProbe.cs` | 只读 TPAC/网格回读，按指定资产名导出数据段和网格 JSON |
| `ClothPatch.cs` | 按显式 metamesh 范围插入自有约束、补全编辑器骨骼数据 |
| `research_cloth_topology.py` | 对原生约束和编辑器几何作长度/拓扑分析 |

共用实现不含明玉资源名、四网格数量或发束/裙饰默认固定方案。模型策略放各模组 `tools/cloth_policy.json`，布料 LOD、材料、倍率、源网格与 GUID 也由各模组负责。明玉目录保留兼容入口及 C# 链接工程，避免重复维护实现。

动态近似检查使用[离线布料诊断器](../cloth_simulator/README.md)，可读取最终包约束并输出动作轨迹、指标和回放；其通过结果不表示游戏求解已验证。

## 运行

依赖 Python（NumPy、SciPy）、.NET 10、TpacTool.Lib（当前由 `D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.dll` 提供）。在工作区根运行，构建缓存放目标模组的 build 中：

```powershell
dotnet build tools/cloth_compiler/NativeClothProbe.csproj -o mods/<ModId>/build/cloth_probe
dotnet build tools/cloth_compiler/ClothPatch.csproj -o mods/<ModId>/build/cloth_patch
dotnet mods/<ModId>/build/cloth_probe/NativeClothProbe.dll <输入.tpac> <metamesh名> --dump-segments mods/<ModId>/build/cloth_inputs
python tools/cloth_compiler/cook_cloth.py mods/<ModId>/build/cloth_inputs mods/<ModId>/build/cooked_cloth --policy mods/<ModId>/tools/cloth_policy.json
dotnet mods/<ModId>/build/cloth_patch/ClothPatch.dll <输入.tpac> mods/<ModId>/build/cooked_cloth/manifest.json <新输出.tpac> --allow-metameshes <metamesh名>
```

`--allow-metameshes` 支持多个精确名称，输出必须与输入路径不同。可用 `-p:MbToolPath=<mbtool.dll路径>` 覆盖共用项目引用。Probe 按已有 `uses_cloth_simulation` 标记选择网格；标记应由模组自己的资源流程设置。

JSON 网格输入包含 `name/guid/metamesh/lod`、`positions/normals`（每顶点 XYZ）、`indices`（三角索引）、`alpha`（0–255），以及 `weights/bones`（每顶点四个 byte 值、权重和 255）。非蒙皮输入的 weights/bones 均为空数组。Patch 要求编辑器顶点与运行时顶点顺序一致；共享编辑器位置的权重须一致，不适配任意外部导入器的顶点重排。

没有 `--policy` 时，缺少固定根部的连通片会报错。可按具体网格配置：

```json
{
  "default": {"unanchored": "error"},
  "meshes": {
    "your_cloth": {"unanchored": "pin_upper", "axis": 2, "band_m": 0.01, "min_vertices": 2},
    "your_decoration": {"unanchored": "freeze_small", "max_positions": 6, "max_alpha": 3}
  }
}
```

这些只是语法示例；固定位置要按实际连接点选择，不能把明玉策略当作所有衣服的默认值。`pin_upper` 对每个无根连通片选择指定轴的最高边；如果连接点不在最高处，应先在源网格画正确 Alpha。所有新固定点都记录在 manifest，覆盖仅写入求解数据，不改变运行时顶点 Alpha。

## 检查与限制

七个原生样本、具体网格与最终 TPAC 检查见明玉的 `reports/cloth_format_research.json`、`cooked_cloth_validation.json`。新模型使用自己的数量、骨骼、GUID 与回读断言。模型流程仍需检查最终 blob 与生成结果相同，约束长度符合原网格、压缩误差、映射、量化蒙皮和跨连通片锚点，再检查未请求改动的几何/材质/Alpha 与原包相同。

这是三角网络编译器，没有复刻原生网格重构或经纬分类。剪切组为空，三角边抗拉维持形状；不生成 `af41613e...` 映射数据，也不实现代理模拟。别复制其他网格的约束。每个启用 LOD 必须有自身 Alpha、固定点和匹配数据；LOD0 的数据不能直接挂到减面网格。

[官方 LOD 文档](https://moddocs.bannerlord.com/asset-management/asset-types/meshes/)给出的最高画质默认切换点为 15、22.5、30、50、70、130、210 米，角色/环境质量可缩短距离。它们是网格切换的默认值，不是布料引擎的实测截止距离；布料标记、包内数据与该级实际求解需要分别确认。

源包可用模组 `mod.json.shared_source_files` 明确列入这些共用文件，`tools/package_delivery.py` 将其放到 `workspace_tools/cloth_compiler/`。明玉兼容入口会自动识别工作区和这种源包布局。source/tex 仍保持相邻，不把技能副本放入工程或源包。

## 注意事项

TpacTool 的外部加载器可能只持有弱引用；修改编辑器数据后调用 `MarkLongLive()` 保持到保存结束。最终重新回读，否则可能只有最后一个网格的骨骼改动被写入。当前 mbtool 保存器会计算解压数据的 XXH64。

透明裁切材料须区分贴图 Alpha 和布料活动 Alpha。固定顶点的活动 Alpha 为零时，若材质同时乘算顶点 Alpha，会使衣物消失；使用对应材质标志并从最终包核对。

模拟标记和活动距离不是布料预处理数据的替代品；字段回读、约束验证和游戏求解应分别记录。直接模拟与代理映射有不同资源需求，不能把另一网格的约束或 LOD 数据移植到本模型。

共享位置应检查 UV 接缝、连通片和骨权重；下垂部件的固定根部按真实连接点配置，不能仅按空间高度分配到腿部。

历史布料试验及用户反馈见 [天香 T5 更新记录](../../mods/TianxiangCollection/sets/TianxiangT5/CHANGELOG.md) 和 [圣绣更新日志](../../mods/ShengxiuCollection/CHANGELOG.md)。
