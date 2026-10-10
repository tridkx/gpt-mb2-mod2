# 圣绣 · 白凤 — Shengxiu Collection v1.1.0

## 使用与工程

此目录是合集内部套装工程，不要把内部 module/ 当作完整合集单独覆盖游戏。运行时已汇入 ../../module/ShengxiuCollection/，资源前缀 sx_baifeng。装备分发容、衣裙与手饰、腿部与绣鞋三件，手套和披肩槽留空。

## 模型配置

input/ 保留原始输入、修复配置与原预览；tex/ 保存原始 PNG，source/ 保存原生 28 骨绑定后的 Blend 和 FBX，两者必须保持相邻。实际尺度、坐标旋转、面片材质槽、独立解剖标记、鞋底拟合与布料/LOD 参数在 tools/model_config.json。预览均从最终 TPAC 解码后生成。

头部随动权重为颈骨 70%／头骨 30%，让旋转支点更接近本模型颈根，降低原生高支点造成的侧偏；头饰、眼睛、头发与脸部同步。head_follow_validation.json 记录原生四组完整动作中相对颈骨的头部中心侧移，并另行检查最终包的量化权重与各级颈缝。

权重渐变限于原模型 z=1.532–1.548m 的颈环，z≥1.548m 的下颌、脸颊和额头使用同一组随动权重。最终四级 LOD 同时检查脸部与眼球的量化权重一致性，以及头部中心侧移。

## 检查与限制

build/ 是可清理的独立缓存，reports/ 是最终回读与动作检查报告。布料在 LOD0/1 生成自有约束，LOD2/3 仅蒙皮。预览只运行原生骨骼动画，不运行游戏布料，不能显示自然回落。原生腿部代理报告只是诊断；游戏动态、穿模和体型滑块需要用户测试。

## 重建

在工作区根运行：

```powershell
python -X utf8 mods/ShengxiuCollection/tools/build_new_sets.py --set 02_Baifeng
```

检查本套 reports/final_*.png 后，从合集根准备交付。依赖本机 Blender 5.2、mbtool、Native 资源及工作区 tools/asset_helpers；共用 cloth_compiler 可从工作区或源包 workspace_tools/ 加载。

安装、交付及版本变化见 [合集说明](../../README.md) 和 [合集更新日志](../../CHANGELOG.md)。
