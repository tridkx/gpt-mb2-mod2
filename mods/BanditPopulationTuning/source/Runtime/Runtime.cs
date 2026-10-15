using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using HarmonyLib;
using TaleWorlds.CampaignSystem;
using TaleWorlds.CampaignSystem.CampaignBehaviors;
using TaleWorlds.CampaignSystem.Party;
using TaleWorlds.CampaignSystem.Party.PartyComponents;
using TaleWorlds.Library;
using TaleWorlds.MountAndBlade;

namespace BanditPopulationTuning
{
    public static class Rules
    {
        public static readonly string[] Clans = { "looters", "sea_raiders", "mountain_bandits", "forest_bandits", "steppe_bandits", "desert_bandits" };
        public static bool Includes(string clan) => Array.IndexOf(Clans, clan) >= 0;
        public static float Safe(float value, float min, float max, float fallback) =>
            float.IsNaN(value) || float.IsInfinity(value) ? fallback : Math.Max(min, Math.Min(max, value));
        public static int ScaleLimit(int baseline, float multiplier) => Math.Max(0,
            (int)Math.Round(baseline * Safe(multiplier, .25f, 5f, 2f), MidpointRounding.AwayFromZero));
        public static float ScaleRatio(float ratio, float speed, bool nightly) => nightly
            ? Math.Min(1f, ratio * Safe(speed, 0f, 5f, 2f)) : ratio;

        // Largest remainders preserve both total headcount and the native distribution.
        public static int[] ScaleCounts(int[] counts, float multiplier)
        {
            if (counts.Any(x => x < 0)) throw new ArgumentOutOfRangeException(nameof(counts));
            int total = counts.Sum();
            if (total == 0) return new int[counts.Length];
            int target = Math.Max(1, ScaleLimit(total, multiplier));
            var exact = counts.Select(x => (double)x * target / total).ToArray();
            var result = exact.Select(x => (int)Math.Floor(x)).ToArray();
            foreach (int i in Enumerable.Range(0, counts.Length).OrderByDescending(i => exact[i] - result[i]).ThenBy(i => i)
                         .Take(target - result.Sum())) result[i]++;
            return result;
        }
    }

    public static class Patches
    {
        public const string Owner = "DKX.BanditPopulationTuning.v1";
        [ThreadStatic] private static int spawning;
        [ThreadStatic] private static int nightly;
        public static readonly List<MethodBase> Targets = new List<MethodBase>();

        public static void Install()
        {
            var harmony = new Harmony(Owner);
            try
            {
                // Patch small getters before callers can be JIT-compiled/inlined.
                Patch(harmony, "GetCurrentLimitForLooters", postfix: nameof(LooterLimit));
                Patch(harmony, "get__numberOfMaxBanditCountPerClanHideout", postfix: nameof(HideoutLimit));
                Patch(harmony, "SpawnLooterParty", nameof(BeginSpawn), finalizer: nameof(EndSpawn));
                Patch(harmony, "SpawnBanditParty", nameof(BeginSpawn), finalizer: nameof(EndSpawn));
                Patch(harmony, "HourlyTickClan", nameof(BeginNight), finalizer: nameof(EndNight));
                Patch(harmony, "SpawnLooters", nameof(AdjustRatio));
                Patch(harmony, "SpawnBanditsAroundHideout", nameof(AdjustRatio));
                Patch(harmony, "InitializeBanditParty", postfix: nameof(AdjustSize));
            }
            catch { harmony.UnpatchAll(Owner); Targets.Clear(); throw; }
        }
        private static void Patch(Harmony h, string target, string prefix = null, string postfix = null, string finalizer = null)
        {
            var method = AccessTools.DeclaredMethod(typeof(BanditSpawnCampaignBehavior), target)
                ?? throw new MissingMethodException(target);
            HarmonyMethod Hook(string name) => name == null ? null : new HarmonyMethod(typeof(Patches), name)
                { priority = Priority.First, before = new[] { "DKX.GenshinBanditRace.v1" } };
            h.Patch(method, prefix: Hook(prefix), postfix: Hook(postfix), finalizer: Hook(finalizer));
            Targets.Add(method);
        }
        private static void BeginSpawn() { spawning++; }
        private static Exception EndSpawn(Exception __exception) { spawning = Math.Max(0, spawning - 1); return __exception; }
        private static void BeginNight() { nightly++; }
        private static Exception EndNight(Exception __exception) { nightly = Math.Max(0, nightly - 1); return __exception; }
        private static void AdjustRatio(Clan __0, ref float __1)
        {
            if (Rules.Includes(__0?.StringId)) __1 = Rules.ScaleRatio(__1, Settings.Current.ReplenishmentMultiplier, nightly > 0);
        }
        private static void LooterLimit(Clan __0, ref int __result)
        {
            if (__0?.StringId == "looters") __result = Rules.ScaleLimit(__result, Settings.Current.PartyCountMultiplier);
        }
        private static void HideoutLimit(ref int __result) => __result = Rules.ScaleLimit(__result, Settings.Current.PartyCountMultiplier);
        private static void AdjustSize(MobileParty __0, Clan __1)
        {
            if (spawning <= 0 || !Rules.Includes(__1?.StringId) || __0?.BanditPartyComponent == null
                || __0.BanditPartyComponent.IsBossParty) return;
            var roster = __0.MemberRoster;
            var entries = roster.GetTroopRoster().ToArray();
            // This hook runs only at natural creation, before combat, capture or XP gain.
            if (entries.Any(x => x.Character.IsHero || x.WoundedNumber != 0)) return;
            int[] target = Rules.ScaleCounts(entries.Select(x => x.Number).ToArray(), Settings.Current.PartySizeMultiplier);
            for (int i = 0; i < entries.Length; i++)
                if (target[i] != entries[i].Number) roster.AddToCounts(entries[i].Character, target[i] - entries[i].Number);
            __0.Party.SetVisualAsDirty();
        }
        public static void Uninstall() { new Harmony(Owner).UnpatchAll(Owner); Targets.Clear(); }
    }

    public sealed class SubModule : MBSubModuleBase
    {
        private string warning;
        protected override void OnSubModuleLoad()
        {
            base.OnSubModuleLoad();
            try { Patches.Install(); }
            catch (Exception error)
            {
                warning = "土匪数量调节：补丁加载失败，未启用；请检查本模块 ModuleData/runtime.log。";
                var root = Path.GetFullPath(Path.Combine(Path.GetDirectoryName(GetType().Assembly.Location), "..", ".."));
                try { File.AppendAllText(Path.Combine(root, "ModuleData", "runtime.log"), error + Environment.NewLine); }
                catch (IOException) { } catch (UnauthorizedAccessException) { }
            }
        }
        protected override void OnBeforeInitialModuleScreenSetAsRoot()
        {
            base.OnBeforeInitialModuleScreenSetAsRoot();
            if (warning != null) { InformationManager.DisplayMessage(new InformationMessage(warning)); warning = null; }
        }
        protected override void OnSubModuleUnloaded() { Patches.Uninstall(); base.OnSubModuleUnloaded(); }
    }
}
