using System;
using System.ComponentModel;
using System.IO;
using MCM.Abstractions.Attributes;
using MCM.Abstractions.Attributes.v2;
using MCM.Abstractions.Base;
using MCM.Abstractions.Base.Global;

namespace CavalryCombatTuning
{
    public sealed class McmSettings : AttributeGlobalSettings<McmSettings>
    {
        public override string Id => "CavalryCombatTuning_v1";
        public override string DisplayName => "Cavalry Combat Tuning（骑兵战斗调整）";
        public override string FolderName => "CavalryCombatTuning";
        public override string FormatType => "json2";
        public override int UIVersion => 2;

        // MCM overlays its persisted values after construction. On first use, seed from v1.0 XML.
        public McmSettings() : this(ReadLegacySeed()) { }

        public McmSettings(Settings seed)
        {
            ChargeDamageMultiplier = seed.ChargeDamageMultiplier;
            MountedMovementPenaltyMultiplier = seed.MountedMovementPenaltyMultiplier;
            MountedAccuracyAIOnly = seed.MountedAccuracyAIOnly;
            VillageMilitiaRecruitmentMultiplier = seed.VillageMilitiaRecruitmentMultiplier;
            VillageMilitiaDailyBonus = seed.VillageMilitiaDailyBonus;
            VillageMilitiaPlayerClanOnly = seed.VillageMilitiaPlayerClanOnly;
        }

        [SettingPropertyFloatingInteger("冲撞基础伤害倍率", 0f, 10f, "0.00",
            Order = 0, RequireRestart = false,
            HintText = "默认2.5；1为原版。影响玩家与双方AI的坐骑冲撞，不影响骑枪。最终扣血还受技能和护甲影响。")]
        [SettingPropertyGroup("冲撞", GroupOrder = 0)]
        public float ChargeDamageMultiplier { get; set; }

        [SettingPropertyFloatingInteger("骑乘弓弩移动惩罚倍率", 0f, 3f, "0.00",
            Order = 0, RequireRestart = false,
            HintText = "默认0.7，移动精度惩罚降低30%；1为原版，越小越准。0只消除移动惩罚，不代表必中。步射和投掷不受影响。")]
        [SettingPropertyGroup("骑射", GroupOrder = 1)]
        public float MountedMovementPenaltyMultiplier { get; set; }

        [SettingPropertyBool("骑射精度仅影响AI", Order = 1, RequireRestart = false,
            HintText = "关闭：玩家与双方AI都生效。开启：己方和敌方AI生效，排除玩家操控角色。此项不限制冲撞伤害。")]
        [SettingPropertyGroup("骑射", GroupOrder = 1)]
        public bool MountedAccuracyAIOnly { get; set; }

        [SettingPropertyFloatingInteger("村庄民兵正向补充倍率", 0f, 10f, "0.00",
            Order = 0, RequireRestart = false,
            HintText = "默认2。仅倍率调整正常村庄的基础补充和炉灶补充，不乘退休项。1为原版；保存后影响后续每日增长，不立即翻倍现有人数。")]
        [SettingPropertyGroup("村庄民兵", GroupOrder = 2)]
        public float VillageMilitiaRecruitmentMultiplier { get; set; }

        [SettingPropertyFloatingInteger("村庄民兵每日额外人数", 0f, 100f, "0.00",
            Order = 1, RequireRestart = false,
            HintText = "默认0。独立加在倍率计算后，不参与倍率；支持小数累计。仅正常村庄生效，城镇、城堡和退休率不变。")]
        [SettingPropertyGroup("村庄民兵", GroupOrder = 2)]
        public float VillageMilitiaDailyBonus { get; set; }

        [SettingPropertyBool("民兵调整仅限玩家家族村庄", Order = 2, RequireRestart = false,
            HintText = "默认关闭：全部正常村庄生效。开启：只对当前属于玩家家族的村庄生效，不包括同王国其他家族；易主后按当前归属判断。")]
        [SettingPropertyGroup("村庄民兵", GroupOrder = 2)]
        public bool VillageMilitiaPlayerClanOnly { get; set; }

        public Settings ToRuntimeSettings()
        {
            var settings = new Settings
            {
                ChargeDamageMultiplier = ChargeDamageMultiplier,
                MountedMovementPenaltyMultiplier = MountedMovementPenaltyMultiplier,
                MountedAccuracyAIOnly = MountedAccuracyAIOnly,
                VillageMilitiaRecruitmentMultiplier = VillageMilitiaRecruitmentMultiplier,
                VillageMilitiaDailyBonus = VillageMilitiaDailyBonus,
                VillageMilitiaPlayerClanOnly = VillageMilitiaPlayerClanOnly
            };
            settings.Validate();
            return settings;
        }

        private static Settings ReadLegacySeed()
        {
            string root = Path.GetFullPath(Path.Combine(Path.GetDirectoryName(typeof(McmSettings).Assembly.Location), "..", ".."));
            try { return Settings.Load(Path.Combine(root, "ModuleData", "settings.xml")); }
            catch (IOException) { return new Settings(); }
            catch (InvalidOperationException) { return new Settings(); }
            catch (UnauthorizedAccessException) { return new Settings(); }
            catch (System.Xml.XmlException) { return new Settings(); }
        }
    }

    public static class McmBridge
    {
        private static McmSettings _bound;

        public static void Connect(McmSettings settings)
        {
            if (settings == null) throw new InvalidOperationException("MCM settings are unavailable.");
            Disconnect();
            RuntimePatches.CurrentSettings = settings.ToRuntimeSettings();
            _bound = settings;
            _bound.PropertyChanged += OnChanged;
        }

        private static void OnChanged(object sender, PropertyChangedEventArgs args)
        {
            if (args.PropertyName == BaseSettings.SaveTriggered || args.PropertyName == BaseSettings.LoadingComplete)
                RuntimePatches.CurrentSettings = _bound.ToRuntimeSettings();
        }

        public static void Disconnect()
        {
            if (_bound != null) _bound.PropertyChanged -= OnChanged;
            _bound = null;
        }
    }
}
