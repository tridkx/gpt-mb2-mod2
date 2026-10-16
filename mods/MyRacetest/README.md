# My Race Test

原版帝国五个高级兵种的种族替换模块，依赖月清疏、白茉晴和天香种族资源。完整依赖与加载入口见 [SubModule.xml](module/MyRacetest/SubModule.xml)。

## 使用与结构

- `module/MyRacetest/`：可安装模块，复制至游戏 `Modules/MyRacetest/`，在启动器中排在依赖种族之后。
- `dist/`：本机保留的修改前备份和交付包，不纳入 Git。
- `reports/`：注明日期的离线检查记录，不代表游戏内验收。

运行需要 Bannerlord 单人战役、SubModule 中声明的种族依赖，以及模块自带的 `RaceTroopBuilder.ArmorRuntime.dll` 和 Harmony。运行组件来源为 [RaceTroopBuilder](../RaceTroopBuilder/README.md)。

五个兵种的人物防具槽为空，由 `ModuleData/rtb_troop_armor.xml` 按兵种 ID 和种族 ID 提供固有护甲。精英具装骑兵为头52／身64／臂48／腿40；其余数值见该配置文件。数值来自本机原版各自兵种战斗装备的四部位汇总，多套等权平均后四舍五入；排除平民装备、马具、品质和特长加成。

## 当前限制

此工程保存已安装模块的维护副本，不含用户原始 GUI 工程 JSON；再次从原 GUI 工程导出时，应先给精英具装骑兵设置相同四项固有护甲覆盖，避免覆盖此配置。模型资源由依赖模块提供。

护甲适配原版 Sandbox 战役场景属性计算，不额外提高自动战斗战力。离线检查通过仍需由用户验证战场减伤；安装后重新启动游戏并载入战役，使护甲数据重新读取。

检查记录见 [2026-10-16 检查报告](reports/2026-10-16-armor-audit.md)，变更见 [CHANGELOG](CHANGELOG.md)。
