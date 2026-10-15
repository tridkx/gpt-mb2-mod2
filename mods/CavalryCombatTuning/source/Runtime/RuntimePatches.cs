using System;
using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using TaleWorlds.Core;
using TaleWorlds.MountAndBlade;
using TaleWorlds.CampaignSystem;
using TaleWorlds.CampaignSystem.GameComponents;
using TaleWorlds.CampaignSystem.Settlements;

namespace CavalryCombatTuning
{
    public static class RuntimePatches
    {
        public const string OwnerId = "dkx.CavalryCombatTuning";
        public static Settings CurrentSettings { get; set; } = new Settings();

        public static MethodInfo[] ResolveTargets()
        {
            // The game loads module assemblies in its own context. Short-name Assembly.Load
            // does not reliably bind that context; never force a second Sandbox assembly load.
            Type sandbox = null;
            foreach (Assembly assembly in AppDomain.CurrentDomain.GetAssemblies())
            {
                sandbox = assembly.GetType("SandBox.GameComponents.SandboxAgentStatCalculateModel", false);
                if (sandbox != null) break;
            }
            if (sandbox == null)
                throw new InvalidOperationException("Sandbox agent model is not loaded yet. Initialize patches after module loading completes.");
            Type[] types = { sandbox, typeof(CustomBattleAgentStatCalculateModel) };
            var result = new List<MethodInfo>();
            foreach (Type type in types)
            {
                MethodInfo method = type.GetMethod("UpdateAgentStats", BindingFlags.Public | BindingFlags.Instance
                    | BindingFlags.DeclaredOnly, null, new[] { typeof(Agent), typeof(AgentDrivenProperties) }, null);
                if (method == null || method.IsAbstract)
                    throw new MissingMethodException(type.FullName, "UpdateAgentStats(Agent, AgentDrivenProperties)");
                result.Add(method);
            }
            MethodInfo militia = typeof(DefaultSettlementMilitiaModel).GetMethod("CalculateMilitiaChange",
                new[] { typeof(Settlement), typeof(bool) });
            if (militia == null) throw new MissingMethodException("DefaultSettlementMilitiaModel.CalculateMilitiaChange");
            result.Add(militia);
            return result.ToArray();
        }

        public static void Install()
        {
            MethodInfo[] targets = ResolveTargets();
            var harmony = new Harmony(OwnerId);
            var postfix = new HarmonyMethod(typeof(RuntimePatches), nameof(AfterUpdate)) { priority = Priority.Last };
            var militiaPostfix = new HarmonyMethod(typeof(RuntimePatches), nameof(AfterMilitiaChange)) { priority = Priority.Last };
            try
            {
                foreach (MethodInfo target in targets)
                    harmony.Patch(target, postfix: target.DeclaringType == typeof(DefaultSettlementMilitiaModel) ? militiaPostfix : postfix);
            }
            catch
            {
                harmony.UnpatchAll(OwnerId);
                throw;
            }
        }

        public static void Uninstall() => new Harmony(OwnerId).UnpatchAll(OwnerId);

        private static void AfterMilitiaChange(Settlement __0, ref ExplainedNumber __result)
        {
            if (__0 == null || !__0.IsVillage || __0.Village == null
                || __0.Village.VillageState != Village.VillageStates.Normal) return;
            Settings settings = CurrentSettings;
            bool playerOwned = settings.VillageMilitiaPlayerClanOnly && Clan.PlayerClan != null
                && __0.OwnerClan == Clan.PlayerClan;
            VillageMilitiaModifier.Apply(ref __result, settings, __0.Village.Hearth, true, true, playerOwned);
        }

        private static void AfterUpdate(Agent __0, AgentDrivenProperties __1)
        {
            if (__0 == null || __1 == null) return;
            WeaponComponentData weapon = null;
            if (__0.IsHuman)
            {
                EquipmentIndex index = __0.GetPrimaryWieldedItemIndex();
                if (index != EquipmentIndex.None)
                    weapon = __0.Equipment[index].CurrentUsageItem;
            }
            StatModifier.Apply(__1, CurrentSettings, __0.IsMount, __0.IsHuman,
                __0.HasMount, __0.IsAIControlled, weapon?.WeaponClass ?? WeaponClass.Undefined);
        }
    }
}
