using MCM.Abstractions.Attributes;
using MCM.Abstractions.Attributes.v2;
using MCM.Abstractions.Base.PerSave;

namespace BanditPopulationTuning
{
    public sealed partial class Settings : AttributePerSaveSettings<Settings>
    {
        public override string Id => "BanditPopulationTuning_v1";
        public override string DisplayName => "土匪与AI强化 / Bandit Population Tuning";
        public override string FolderName => "BanditPopulationTuning";
        public override int UIVersion => 2;

        [SettingPropertyFloatingInteger("地图队伍数量倍率", 0.25f, 5f, "0.00", Order = 0, RequireRestart = false,
            HintText = "默认2。调整六类自然生成土匪的目标数量上限；现有队伍自然消亡，不立即删除。逃兵、首领和任务队不变。")]
        [SettingPropertyGroup("自然生成", GroupOrder = 0)]
        public float PartyCountMultiplier { get; set; } = 2f;

        [SettingPropertyFloatingInteger("每队生成人数倍率", 0.25f, 5f, "0.00", Order = 1, RequireRestart = false,
            HintText = "默认2。仅新生成的普通地图土匪队伍生效；与混编Mod同时使用时先调人数、再混编。旧队不重复扩编。")]
        [SettingPropertyGroup("自然生成", GroupOrder = 0)]
        public float PartySizeMultiplier { get; set; } = 2f;

        [SettingPropertyFloatingInteger("生成与补充速度倍率", 0f, 5f, "0.00", Order = 2, RequireRestart = false,
            HintText = "默认2。倍率调整原版夜间按缺额补队的系数；0暂停后续自然补队。保留原版昼夜规则，不加倍新开局的初始填充比例。")]
        [SettingPropertyGroup("自然生成", GroupOrder = 0)]
        public float ReplenishmentMultiplier { get; set; } = 2f;

        public static Settings Current => Instance ?? Defaults;
        private static readonly Settings Defaults = new Settings();
    }
}
