# Beauty Banners v1.2.0

九款玩家可选彩色旗徽：保留 OL、旗袍、素雅汉服的三个透明横版，恢复三个原始竖版，并新增赛博朋克、日漫、唐制汉服三个带场景背景的横版。保留玩家可选纯白背景色。所有已确认输入和源图完整保留，图案目录与哈希见 `input/approved_artwork.json`；游戏贴图在相邻的 `tex/`。

## 使用

1. 启动器勾选英文显示名 **Beauty Banners**，加载在 Native、SandBoxCore、Sandbox 之后。
2. 进入战役大地图，按 **B** 打开旗帜编辑器，在 **美女旗帜** 分类中选择九款图案之一（英文语言下分类为 Beauty Banners）。依次为三个透明横版、三个原始竖版、三个场景横版。
3. 将**背景颜色和旗徽颜色都选择为白色**，尽量保留人物原色。新增的白色色块 ID 为 71001，开放为背景色和旗徽色；原版旗徽白色 172 也可使用。切换其他旗徽色仍会给人物染色。
4. 按需要调整图案大小和位置后保存，再查看大地图旗帜、战场旗帜和可显示家族旗徽的盾牌。

新图的城市、樱花河岸和庭院是图片内部背景，随图案一起缩放；没有增加独立的原版背景图层或整旗渲染插件。横版图片完整保留在方形图集格内，周围的透明留白仍显示所选旗底色。

这是旗帜编辑器图案包，不新增旗杆、装备属性或兵种。纯资源/XML 模组，不依赖 Harmony、BannerPaste 或其他旗帜编辑器。原版仍控制图案大小及不同旗面上的映射；盾牌和地图图标的裁切可能与战场旗面不同。阵营规则锁定背景颜色时，本模组不解除该限制。第三方模组压缩包未修改、未安装。

## 交付与验证

- 当前本机目标：Bannerlord **v1.4.8**。
- 旗徽分类 ID：71；7101–7103 保留现有透明横版，7104–7106 是恢复的竖版，7107–7109 为三个场景横版；图集位置依次为 0–8。既有存档的 7101–7103 不变。
- 材质：`bb_portrait_icons`，引用本机原生 `simple_shader`；保留完整 RGB 与柔和透明边缘。游戏实际染色、亮度和显示位置以用户测试为准。
- 主图集 4096×4096，4×4 分格；九张图按比例放入前九格，余下七格透明。无损 RGBA 资源约占 64 MiB，缩略图资源约占 0.5 MiB；不增加主图集显存。
- 九个 100×100 缩略图放入独立的 `ui_beautybanners` 分类，1024×128 图集，启用 AlwaysLoad。
- 从最终 TPAC 重新导出并逐字节比对 RGBA，检查资源校验和与元数据往返、编号/GUID 冲突、XML 注册、缩略图坐标和原图保留。
- 九款图案预览：`reports/final_banner_preview.png`。从最终 TPAC 解码的方形图集格生成，不模拟游戏着色器、裁切、旗面映射和光照。
- 检查报告：`reports/release_validation.json`。**游戏测试由用户完成**；未启动游戏或 Modding Kit。

Mod ZIP 的顶层是 `BeautyBanners/`，解压到游戏 `Modules/` 即可。源包保留 `input/`、`source/`、`tex/` 和制作脚本层级。卸载本模组前，建议把存档中的家族旗徽改回原版图案，避免存档引用不存在的图案编号。

## 本地重建

在已配置工具的工作区使用：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/BeautyBanners/tools/build_package.py
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/BeautyBanners/tools/verify_release.py
./tools/install_release.ps1 -Mod BeautyBanners -Version v1.2.0 -CheckOnly
```

本版更新使用工作区公共入口 `./tools/install_release.ps1 -Mod BeautyBanners -Version v1.2.0 -PreviousVersion v1.1.0`。旧交付包按版本保存在 `dist/BeautyBanners_v*_Mod.zip` 与 `dist/BeautyBanners_v*_Source.zip`。专用 `tools/install_mod.py` 仍仅适用于目标目录不存在的首次安装。请先退出游戏和启动器。

依赖 Python（Pillow、NumPy）、.NET 9 SDK/运行时和本机修补版 mbtool，以及目标版本原生 UI 纹理、旗徽材质和着色器模板。源包解压后的根目录也可直接运行 `tools/build_package.py`。工具路径可通过 `BANNERLORD_GAME_ROOT`、`BANNERLORD_MBTOOL` 环境变量覆盖；C# 项目的 mbtool 引用路径需与实际工具匹配。

## 资料

- [官方旗徽资源教程](https://moddocs.bannerlord.com/asset-management/creating_custom_banner_icons/)
- [官方 UI Sprite Sheet 教程](https://moddocs.bannerlord.com/asset-management/generating_and_loading_ui_sprite_sheets/)

本机 v1.4.8 的 BannerManager 明确使用 `BannerIcons` 注册的合并 XML；本模组按此注册。UI 加载器按 SpriteData 中的分类和图集名查找已加载纹理，无需运行时 DLL。原生游戏资产仅用作本机构建模板，不作为原版完整资源包分发。
