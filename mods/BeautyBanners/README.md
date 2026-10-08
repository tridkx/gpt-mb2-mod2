# Beauty Banners v1.0.0

新增三款玩家可选彩色人物旗徽：OL 制服、红色缎面旗袍、白蓝素雅汉服。三张图均来自用户已确认的生成插画；原始 PNG 保存在 `input/`，未经改画的编辑源保存在 `source/`，游戏贴图在相邻的 `tex/`。

## 使用

1. 启动器勾选英文显示名 **Beauty Banners**，加载在 Native、SandBoxCore、Sandbox 之后。
2. 进入战役大地图，按 **B** 打开旗帜编辑器，在 **美女旗帜** 分类中选择三款人物之一（英文语言下分类为 Beauty Banners）。
3. 将**旗徽颜色选择为白色**，尽量保留人物原色；背景颜色可自由选择。原版可选白色的颜色 ID 为 172。切换为其他旗徽色会给彩色人物染色。
4. 按需要调整图案大小和位置后保存，再查看大地图旗帜、战场旗帜和可显示家族旗徽的盾牌。

这是旗帜编辑器图案包，不新增旗杆、装备属性或兵种。纯资源/XML 模组，不依赖 Harmony、BannerPaste 或其他旗帜编辑器。与第三方编辑器的兼容性未实测。

## 交付与验证

- 当前本机目标：Bannerlord **v1.4.8**。
- 旗徽分类 ID：71；图案 ID：7101、7102、7103；图集位置依次为 0、1、2。
- 材质：`bb_portrait_icons`，引用本机原生 `simple_shader`；保留完整 RGB 与柔和透明边缘。游戏实际染色、亮度和显示位置以用户测试为准。
- 主图集 4096×4096，4×4 分格；三个人物按比例放入前三格，余下十三格透明。保留原图中的柔和光晕。无损 RGBA 资源约占 64 MiB，缩略图资源约占 0.25 MiB。
- 三个 100×100 缩略图放入独立的 `ui_beautybanners` 分类，启用 AlwaysLoad。
- 从最终 TPAC 重新导出并逐字节比对 RGBA，检查资源校验和与元数据往返、编号/GUID 冲突、XML 注册、缩略图坐标和原图保留。
- 离线布局预览：`reports/final_banner_preview.png`。它不是游戏截图，也不模拟游戏着色器和光照。
- 检查报告：`reports/release_validation.json`。**游戏测试由用户完成**；未启动游戏或 Modding Kit。

Mod ZIP 的顶层是 `BeautyBanners/`，解压到游戏 `Modules/` 即可。源包保留 `input/`、`source/`、`tex/` 和制作脚本层级。卸载本模组前，建议把存档中的家族旗徽改回原版图案，避免存档引用不存在的图案编号。

## 本地重建

在已配置工具的工作区使用：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/BeautyBanners/tools/build_package.py
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/BeautyBanners/tools/verify_release.py
./tools/install_release.ps1 -Mod BeautyBanners -Version v1.0.0 -CheckOnly
```

首次安装也可先运行工作区 `tools/package_delivery.py --mod BeautyBanners --version v1.0.0`，再运行本工程 `tools/install_mod.py`。专用安装脚本逐项核对检查报告与 ZIP 字节，仅允许安装到尚不存在的 `Modules/BeautyBanners/`；已存在时会停止，保留旧目录。请先退出游戏和启动器。后续版本可走工作区公共安装入口并指定上一版本，以保留旧交付包。

依赖 Python（Pillow、NumPy）、.NET 9 SDK/运行时和本机修补版 mbtool，以及目标版本原生 UI 纹理、旗徽材质和着色器模板。源包解压后的根目录也可直接运行 `tools/build_package.py`。工具路径可通过 `BANNERLORD_GAME_ROOT`、`BANNERLORD_MBTOOL` 环境变量覆盖；C# 项目的 mbtool 引用路径需与实际工具匹配。

## 资料

- [官方旗徽资源教程](https://moddocs.bannerlord.com/asset-management/creating_custom_banner_icons/)
- [官方 UI Sprite Sheet 教程](https://moddocs.bannerlord.com/asset-management/generating_and_loading_ui_sprite_sheets/)

本机 v1.4.8 的 BannerManager 明确使用 `BannerIcons` 注册的合并 XML；本模组按此注册。UI 加载器按 SpriteData 中的分类和图集名查找已加载纹理，无需运行时 DLL。原生游戏资产仅用作本机构建模板，不作为原版完整资源包分发。
