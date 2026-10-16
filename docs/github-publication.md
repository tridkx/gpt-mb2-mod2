# GitHub 公共发布

公共仓库：[tridkx/gpt-mb2-mod2](https://github.com/tridkx/gpt-mb2-mod2)。各模组当前发布包见[Release 索引](release-index.md)。普通仓库包含受 Git 管理的源工程、运行模块与历史；安装用户优先下载对应 Release 的 Mod ZIP。

## 本地工程与发布副本

- 原始制作工作区：`D:/gpt-mb2-mod2`，保持原有提交、分支与历史标签；其中 `github` remote 指向公共仓库，用于查阅。
- GitHub 发布副本：`D:/gpt-mb2-mod2-github`，`source` remote 指向原始工作区，`origin` 指向 GitHub。公共默认分支 `main` 对应最新制作快照。
- 两份超过普通 Git 单文件限制的艾达王源模型在发布副本中迁入 Git LFS。迁移会改变相关历史提交的哈希，版本标签名称和文件内容保留，原始制作工作区不执行迁移。发布副本的 `history/local-main` 保留原本地 main 分支的位置。

从 GitHub 克隆制作源工程需安装 Git LFS，并运行 `git lfs pull` 取得大模型文件。没有 LFS 内容时，文件可能只是指针，不能直接交给 Blender。工作区内被忽略的必要增量基线没有因此自动上传，完整重建边界见[重建输入与构建缓存](rebuild-and-cleanup.md)。

## 后续同步

先在原始工作区完成本地提交，再在发布副本同步和执行相同的 LFS 转换。不要把原始分支强制覆盖到 GitHub 上已转换的分支。下列命令只用于无未提交修改的独立发布副本，不能对制作工作区执行 reset：

```powershell
$publication = 'D:/gpt-mb2-mod2-github'
git -C $publication status --short
git -C $publication fetch source --tags --force
git -C $publication switch main
git -C $publication reset --hard source/codex/bishui-qingluan-race
git -C $publication lfs migrate import --everything --skip-fetch --yes --include='**/REAdaWongDefault_Rigged.blend,**/REAdaWongDefault_Rigged.fbx'
git -C $publication push origin main
git -C $publication push origin --tags
```

制作分支改变时，先核对实际分支再替换上面的 source ref。首次大历史导入按对象大小分批推送，后续只传输新增对象。远程写入仍需当次明确授权。

## 发布包与版本选择

每个当前可安装模块发布一个 `<ModId>/<版本>` Release，包含以 Mod ID 为顶层的安装 ZIP 和 `SHA256SUMS.txt`。RaceTroopBuilder 发布既有带运行时的 Windows x64 工具包。Release 索引列出每个包、版本与说明位置。

版本按当前有效交付选择，而不是机械选取数值最高的标签：天香 T5 使用无布料外观版 v1.4.2，五毒使用已回退的 v0.2.6；已撤回版本只保留历史标签。碧水青鸾不在当前工作树中，从最后保留的 v0.1.2 标签恢复模块打包。

本次发布核对 ZIP、包内文件与 SHA-256，不重新制作模型、不安装模块、不启动游戏；既有游戏验收和限制以各工程说明为准。Source ZIP 可按需从展开源工程重新打包，不重复上传为每个 Release 的资产。公开发布不额外改变仓库中模型或其他第三方内容既有的许可条件。
