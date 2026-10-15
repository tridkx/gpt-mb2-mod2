using TaleWorlds.Core;
using TaleWorlds.MountAndBlade;

namespace CavalryCombatTuning
{
    public static class StatModifier
    {
        // Called once after the original model has rebuilt the properties for this update.
        public static void Apply(AgentDrivenProperties properties, Settings settings,
            bool isMount, bool isHuman, bool hasMount, bool isAI, WeaponClass weaponClass)
        {
            if (isMount)
                properties.MountChargeDamage *= settings.ChargeDamageMultiplier;

            if (isHuman && hasMount && (!settings.MountedAccuracyAIOnly || isAI)
                && (weaponClass == WeaponClass.Bow || weaponClass == WeaponClass.Crossbow))
            {
                // The engine scales this penalty with movement. Leave base inaccuracy,
                // hold-time instability, rotation, and AI lead calculations unchanged.
                properties.WeaponMaxMovementAccuracyPenalty *= settings.MountedMovementPenaltyMultiplier;
            }
        }
    }
}
