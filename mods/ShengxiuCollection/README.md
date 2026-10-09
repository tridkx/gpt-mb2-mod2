# Shengxiu Collection v1.0.1

圣绣系列独立模组工程；当前收录「圣绣 · 明玉」。游戏模块 ID 为 `ShengxiuCollection`，管理器显示英文 `Shengxiu Collection`。后续同系列装备继续放本项目，使用各自资源前缀和源文件，明玉资源前缀为 `sx_mingyu_`。

v1.0.1 根据用户对 v1.0.0 的外观反馈修正：头部上段放大 10%，颈部上端向后收 18 毫米，头颈与领口采用连续过渡；脚部回转 10.34°，鞋底前后长度从 26.95 厘米减至 23.51 厘米，原始鞋底平面顶点落在 z=0 上方 1 毫米。脚踝渐变过渡，皮肤与鞋使用一致变形。原生骨架、绑骨权重、布料 Alpha、全部运行时布料元数据和裙摆几何保持不变。布料问题按用户要求暂不处理。报告 reports/proportion_validation.json，固定镜头对比为 reports/proportion_*_before/after.png。这是离线几何与动作验证，游戏中的比例和落地表现由用户复测。

配套装备三件：圣绣 · 明玉 · 发容（头盔），圣绣 · 明玉 · 衣裙与手饰（身体），圣绣 · 明玉 · 腿部与绣鞋（靴子）。手套和披肩槽留空。可在作弊物品列表按名称找到，装备三件获得完整人物；商店生成需要等待游戏刷新。依赖 Native、SandBoxCore、Sandbox。

原始输入来自 `D:/dsh-tiandao/圣秀_明玉`，原始模型与修复记录保存在 input/，PNG 原样保存在 tex/。14 个无骨网格独立测量后适配当前原生 28 骨骨架，面向转换一次，保留 UV 和贴图 Alpha。固定脸型，不提供原版面部表情。源 Blend 内打包贴图，FBX 重新导入验证。

## 布料

最终 TPAC 的 LOD0 启用原生直接布料模拟。腰与肩袖连接处固定，裙摆渐变活动距离最高约 9 厘米；分离长袖薄纱顶部跟随袖口，尖端最高约 16 厘米；长发尖端约 2.5 厘米。贴肤袖片采用邻近皮肤权重，悬垂薄纱单独锚定，避免错误跟随腿部。薄纱在静态适配时保持悬垂形状，减少因手臂姿态转换造成的外张。采用较低弯曲刚度、高抗拉与锚定、适度阻尼和较低风力。远处 LOD1–3 仅蒙皮。参数在 tools/model_config.json、tools/PackagePatch/Program.cs。

已回读确认顶点活动距离、uses_cloth_simulation 标记、human_body 引用、布料材料和元数据往返。未运行游戏布料求解器，未生成编辑器预处理 tcc/tcm 文件；引擎字段 UnknownFloat1 等保留工具原字段名，不声称其与编辑器选项一一对应。无需 Blender Cloth 修改器即可在游戏资源中携带布料设置。官方参考：https://moddocs.bannerlord.com/editor/resource-editors/cloth_simulation/

## 检查与边界

最终 TPAC 回读检查 XML、独立资源名/GUID、所有引用、有限几何、四骨 byte 权重和为 255、四级 LOD、UV/颜色与构建数据一致、19 个跨网格皮肤接缝、所有贴图 mip 解码。原生站立采样 16 帧，跑步 25 帧，拉弓 150 帧，骑乘 20 帧；动作文件重新从当前已安装游戏读取核对。报告与预览在 reports/。

预览是最终 TPAC 的离线蒙皮渲染，衣料以低阈值裁切加原贴图透明度近似，其余材质采用阈值裁切；不是引擎半透明或布料模拟画面。衣料 AlphaTest 为 0.025，避免大量薄纱被裁掉。腿部代理检测仍有接触：跑步/拉弓/骑乘最大约 7.5 厘米，不能据此声称没有穿模。游戏中的布料摆动、腿部与马匹碰撞、薄纱透明排序、武器握持、角色体型滑块和性能由用户测试。未启动游戏，未修改 Native。

## 重建

后台 Blender 执行 tools/rig_model.py，再执行 tools/export_geometry.py，均加 `--python-exit-code 1` 并检查退出码。用 dotnet build tools/PackagePatch/PackagePatch.csproj -o build/package_patch 编译独立补丁器；Python 执行 tools/build_package.py、tools/verify_release.py、tools/verify_native_provenance.py。后台 Blender 执行 tools/verify_source.py 和 tools/render_review.py -- final face。依赖工作区共用 tools/asset_helpers、本机 Blender、Anaconda Python、D:/mb-tools 和已安装游戏资源。

本次返修重建需额外执行 tools/verify_proportions.py、tools/verify_cloth.py 和 tools/render_proportion_compare.py。比例回归基线在 build/proportion_baseline_v1.0.0/，缓存缺失时从保留的 v1.0.0 源 ZIP 或本地 ShengxiuCollection/v1.0.0 标签恢复旧工程并重建，不将新版本当旧基线。

通过检查并人工复核预览后执行 tools/prepare_delivery.py，再从工作区运行 tools/install_release.ps1 -Mod ShengxiuCollection -Version v1.0.1 -PreviousVersion v1.0.0。交付 Mod ZIP 顶层为 ShengxiuCollection，可解压至游戏 Modules；源 ZIP 保持 source/ 与 tex/ 相邻。只安装自己的模块，本地 Git 管理，不上传远程。更新发布时保留上一版交付包。
