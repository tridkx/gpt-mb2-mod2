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

        public Settings ToRuntimeSettings()
        {
            var settings = new Settings
            {
                ChargeDamageMultiplier = ChargeDamageMultiplier,
                MountedMovementPenaltyMultiplier = MountedMovementPenaltyMultiplier,
                MountedAccuracyAIOnly = MountedAccuracyAIOnly
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
