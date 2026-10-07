# 长水袖改用映射模拟：准备结果与未完成项

2026-10-07。用户反馈：v1.4.0 和 v1.4.1 的长水袖仍随手臂抬起，没有下垂。因此已有离线参数检查不能作为修复成功的证据。

## 官方资料核对

- [官方布料教程（中文）](https://moddocs.bannerlord.com/zh_cn/editor/resource-editors/cloth_simulation/)：直接模拟适合简单、少顶点网格；映射模拟通过独立网格驱动外观网格。代理 Alpha 决定活动距离，外观 Alpha 仅决定映射或蒙皮。必须在编辑器按 **Save mesh settings** 保存。
- [官方资产目录说明](https://moddocs.bannerlord.com/asset-management/asset-types/overriding_assets/)：`Assets` 保存可编辑资产，`AssetSources` 保存输入，`AssetPackages` 是客户端只读包；资源缓存可自动重新生成。整个 MetaMesh 才能覆盖，不能只覆盖其单个子网格。
- 当前天香运行时资源没有映射代理引用。直接模拟本来就不需要该引用，不能据此断言布料未启用；缺少 `.tcc/.tcm` 文件也不能单独证明原因。这次切换路线是为了建立可观察的官方求解与映射流程，并非已经确认直接模拟失败的唯一原因。
- 原生 `battania_dress_c` 有独立模拟资源引用（本机报告 `native_cloth.json`）。当前 TPAC 库的 `ClothMappingData` 只读取原始数据，并没有可用于生成映射的实现；不能靠写入代理 GUID 冒充完成映射。

## 已准备

`source/TianxiangT5_MappedSleeves.blend` 是独立候选源，不覆盖已交付源。

- `source/TianxiangT5_SleeveSimulation.fbx`：原生骨架和 `tx5_sleeve_simulation`。两条水袖各 142 顶点、240 三角面，各 8 个固定根点。只焊接导出产生的重合接缝，保留长袖轮廓；没有进一步简化导致贴合误差。
- `source/TianxiangT5_MappedSleeves_Render.fbx`：完整外观源的 14 个网格，几何与绑骨沿用当前源。长袖自由顶点 Alpha=1，根点与其他上衣部分 Alpha=0。此次候选只映射长袖，原先上衣边缘的小幅直接模拟暂时固定，以免错误映射到远处水袖；裙摆和头发在独立网格中保留。
- 模拟代理沿用 v1.4.1 的距离渐变，距离乘数 2。具体参数只是编辑器起点，需要按实际预览调整。
- 两个 FBX 均重新导入检查：网格数量、骨架、代理顶点与面数、颜色 Alpha、有限坐标和骨架修改器通过。代理无退化面、重复三角面或超过两面共享的边。
- 构建入口：Blender 后台运行 `tools/prepare_mapped_sleeves.py`。需要已有 `build/sleeve_mask.npz` 与基线网格 JSON；可先运行现有 `tools/build_sleeves.ps1` 生成，后者会重新构建现有直接模拟版本，不应当作路线 2 发布入口。
- 机器检查结果与文件摘要见 `mapped_sleeves_preparation.json`。

## 继续制作的必要步骤

1. 在自己的模块建立可编辑资产环境并保留客户端 TPAC 的完整备份。导入两个候选 FBX 后，核对官方命名规则得到的 MetaMesh 与子网格名；不要仅凭文件名认定引用已正确。保留原有材质、贴图、其他身体部件与 LOD，防止整 MetaMesh 覆盖丢失资源。
2. 打开布料编辑器：Preview mesh 选择身体外观资源，Simulation mesh 选择 `tx5_sleeve_simulation`；骨架选择当前原生 human 骨架，碰撞体使用 `human_body`。只勾选需要映射的上衣/长水袖子网格。代理距离乘数设 2，代理材质从 `tx5_water_sleeve` 参数起步；代理设置会覆盖渲染网格布料设置。
3. 先关闭动画观察重力是否使末端下落，再播放当前游戏的抬臂、持弓、格挡动作。确认袖根跟臂、袖尾下落；若整段仍跟臂，应检查模拟是否更新、Alpha 是否实际导入、映射和子网格选择是否保存，而不是继续盲调软硬度。
4. 按 Save mesh settings，重新加载资源后复查映射、碰撞体和参数。处理 LOD1 的映射并检查远近切换；不能把目前只有原始导出网格的候选称为完整 LOD 交付。
5. 用官方发布流程生成客户端资源包，检查真实代理引用和预处理数据、贴图/材质/其他 54 个子网格，再离线核对与安装自己的模块。游戏测试由用户完成。

## 当前阻碍

本次尝试通过已安装 Windows computer-use 技能操作官方编辑器。其 Node 工具在执行前退出，诊断为 `windows sandbox failed: helper_unknown_error: setup refresh had errors`，无法读取或操作编辑器窗口。普通受限终端也遇到相同初始化错误，但经自动审核的文件操作可执行；这不是用户拒绝授权，也不是自动审批拒绝。

因此本次没有完成官方映射保存、官方求解器预览或发布安装。游戏仍为 v1.4.1；没有新发布版本或标签。候选仅供继续制作，不是可安装修复包。桌面操作通道恢复后可从上述候选继续，不需要重做已准备的网格。
