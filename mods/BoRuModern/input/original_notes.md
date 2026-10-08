# 孟柏汝 BoRu —— 已完成（原版网格）

* `SK_BR.psk` / `SK_BR.obj` —— **游戏原版骨骼网格**（骨架 `SKEL_BR`，80 骨骼，含 LOD）
* 贴图：`T_RoRu_Body_D/N/ORM/opacity`（身体/脸）、`T_RoRu_2012Cloth_D`（白衬衫+牛仔裤+帆布鞋）、
  `T_Common_Eyes_01_D`（共用眼球）、`T_BoRu_Hair_D.png`（用共用发丝图 `T_Hair_D` 按她发色着色）
* 眼镜、手表/编织手绳**是网格自带的材质槽**，不是重建的

槽位 → 贴图（渲染用）：
`0=T_RoRu_Body, 1=T_RoRu_Body, 2/3=T_Common_Eyes_01, 4=眼镜/饰品(灰), 5=T_RoRu_2012Cloth, 6=头发`

预览：`output/preview/card_08_孟柏汝_BoRu_女.png`

## 这个网格是怎么找到的

提取器原来用「名字表里第一条 `/Game/...` 字符串」当包名，这是**启发式**，会撞名：
pak 里 `/Game` 包条目 **12,073 条，却只有 7,209 个不同名字** → 约 4,800 个包写盘时
**被同名文件覆盖**。按名字做的完整性审计查不出这种事（名字都在，只是内容被换了），
所以本角色的网格一度没进解包树。

正确的做法：UE4 包头的 `FPackageFileSummary` **本来就带 PackageName 字段**，按固定偏移解出来即可。
本次用 `tools/mesh_roster_from_paks.py` 直接对 **pak 条目**（而不是解包树）逐条解压点名，
再按 `(pak, entry_off)` 精确重取（`tools/recover_meshes.py`），一次找回：

| 网格 | 所在 pak | 说明 |
|---|---|---|
| **SK_BR** | pakchunk201 | **孟柏汝本人网格**（80 骨骼，含眼镜、手表/手绳） |
| **SK_LN** | pakchunk203 | **郑琳恩常态网格**（9 槽：身体/嘴/眼/衣/裙/长发…） |
| SK_GG1 / SK_GGEX | pakchunk306 | 女鬼两个网格 |
| SK_TM / SK_WY / SK_DC | 205/206/202 | 男角色（之前"缺 .ubulk"导不出来的那三个） |
| SK_Corpse_01 / SK_BS | 104/308 | 尸体/干尸相关 |

对照图集逐槽验证：SK_BR 的衣服槽 UV 正好落在 `T_RoRu_2012Cloth_D`（白衬衫+牛仔裤+帆布鞋）上，
烘出来与官方画册 P11 完全一致。
