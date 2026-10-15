using System;
using MCM.Abstractions.Attributes;
using MCM.Abstractions.Attributes.v2;
using MCM.Abstractions.Base.PerSave;

namespace GenshinBanditRace
{
    public sealed class Settings : AttributePerSaveSettings<Settings>
    {
        public override string Id => "GenshinBanditRace_v1";
        public override string DisplayName => "原神土匪混编 / Genshin Bandit Race";
        public override string FolderName => "GenshinBanditRace";
        public override int UIVersion => 2;

        [SettingPropertyBool("启用新队伍混编", Order = 0, RequireRestart = false,
            HintText = "只作用于六类新生成的普通地图土匪；逃兵、任务队和藏身处首领排除。关闭不移除已有原神兵。")]
        [SettingPropertyGroup("混编", GroupOrder = 0)]
        public bool Enabled { get; set; } = true;

        [SettingPropertyBool("使用固定人数模式", Order = 1, RequireRestart = false,
            HintText = "关闭为比例模式，开启为固定人数模式。两种模式都替换队内原版土匪，不增加总人数。")]
        [SettingPropertyGroup("混编", GroupOrder = 0)]
        public bool FixedMode { get; set; }

        [SettingPropertyInteger("原神兵比例（%）", 0, 100, Order = 2, RequireRestart = false,
            HintText = "比例模式默认30%。以最终队伍总人数计算，四舍五入；最多替换可用的原版土匪人数。")]
        [SettingPropertyGroup("混编", GroupOrder = 0)]
        public int Percentage { get; set; } = 30;

        [SettingPropertyInteger("每队固定原神兵人数", 0, 500, Order = 3, RequireRestart = false,
            HintText = "固定模式默认5人；队伍不足时最多替换可用原版土匪。不影响俘虏和其他来源的兵。")]
        [SettingPropertyGroup("混编", GroupOrder = 0)]
        public int FixedCount { get; set; } = 5;

        [SettingPropertyFloatingInteger("等效防具负重倍率", 0f, 2f, "0.00", Order = 0, RequireRestart = false,
            HintText = "默认1，补齐参考五级兵防具重量；0关闭。武器、盾、弹药和马具照常计算。招募后的本Mod兵种也生效，其他兵种不变。")]
        [SettingPropertyGroup("战斗负重", GroupOrder = 1)]
        public float ArmorWeightMultiplier { get; set; } = 1f;

        [SettingPropertyButton("清理本Mod兵种", Content = "转换为原版土匪", Order = 0, RequireRestart = false,
            HintText = "需在战役大地图、无进行中战斗时执行。确认后关闭混编，将各队伍/驻军/俘虏中的本Mod兵转换为原版土匪，保留人数与伤员。请先备份，之后另存并重载验证；不保证完整卸载安全。")]
        [SettingPropertyGroup("卸载准备", GroupOrder = 2)]
        public Action Cleanup { get; set; } = CleanupService.Request;

        public static Settings Current => Instance ?? Defaults;
        private static readonly Settings Defaults = new Settings();
    }
}
