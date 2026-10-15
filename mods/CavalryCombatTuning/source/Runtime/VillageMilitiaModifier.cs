using System;
using TaleWorlds.CampaignSystem;
using TaleWorlds.Localization;

namespace CavalryCombatTuning
{
    public static class VillageMilitiaModifier
    {
        private static readonly TextObject BonusText = new TextObject("骑兵战斗调整：村庄民兵补充");

        public static float CalculateAdjustment(Settings settings, float hearths,
            bool isVillage, bool isNormal, bool belongsToPlayerClan)
        {
            if (!isVillage || !isNormal || (settings.VillageMilitiaPlayerClanOnly && !belongsToPlayerClan))
                return 0f;
            // Vanilla v1.4.8 village recruitment consists of base + hearths.
            // Add only their delta to the original model, retaining retirement and other effects.
            float positiveRecruitment = Math.Max(0f, 0.5f + hearths / 400f);
            return positiveRecruitment * (settings.VillageMilitiaRecruitmentMultiplier - 1f)
                + settings.VillageMilitiaDailyBonus;
        }

        public static void Apply(ref ExplainedNumber result, Settings settings, float hearths,
            bool isVillage, bool isNormal, bool belongsToPlayerClan)
        {
            float adjustment = CalculateAdjustment(settings, hearths, isVillage, isNormal, belongsToPlayerClan);
            if (adjustment != 0f) result.Add(adjustment, BonusText);
        }
    }
}
