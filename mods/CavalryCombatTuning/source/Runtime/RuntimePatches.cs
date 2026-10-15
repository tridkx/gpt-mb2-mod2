using System;
using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using TaleWorlds.Core;
using TaleWorlds.MountAndBlade;

namespace CavalryCombatTuning
{
    public static class RuntimePatches
    {
        public const string OwnerId = "dkx.CavalryCombatTuning";
        public static Settings CurrentSettings { get; set; } = new Settings();

        public static MethodInfo[] ResolveTargets()
        {
            // No compile-time Sandbox dependency: it is loaded explicitly for campaign support.
            Type sandbox = Assembly.Load("SandBox").GetType("SandBox.GameComponents.SandboxAgentStatCalculateModel", true);
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
            return result.ToArray();
        }

        public static void Install()
        {
            MethodInfo[] targets = ResolveTargets();
            var harmony = new Harmony(OwnerId);
            var postfix = new HarmonyMethod(typeof(RuntimePatches), nameof(AfterUpdate)) { priority = Priority.Last };
            try
            {
                foreach (MethodInfo target in targets)
                    harmony.Patch(target, postfix: postfix);
            }
            catch
            {
                harmony.UnpatchAll(OwnerId);
                throw;
            }
        }

        public static void Uninstall() => new Harmony(OwnerId).UnpatchAll(OwnerId);

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
