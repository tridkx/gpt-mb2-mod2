using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Reflection.Emit;
using System.Xml.Linq;
using HarmonyLib;
using TaleWorlds.CampaignSystem;
using TaleWorlds.CampaignSystem.CampaignBehaviors;
using TaleWorlds.CampaignSystem.Party;
using TaleWorlds.CampaignSystem.Roster;
using TaleWorlds.CampaignSystem.Settlements;
using TaleWorlds.Core;
using TaleWorlds.Library;
using TaleWorlds.MountAndBlade;
using TaleWorlds.ObjectSystem;

namespace GenshinBanditRace
{
    public sealed class Entry
    {
        public string Id, Race, Role, Fallback;
        public float Weight;
        public CharacterObject Character;
    }
    public static class Rules
    {
        public static readonly string[] Clans = { "looters", "sea_raiders", "mountain_bandits", "forest_bandits", "steppe_bandits", "desert_bandits" };
        public static bool Includes(string clan) => Array.IndexOf(Clans, clan) >= 0;
        public static int Quota(int total, int eligible, bool fixedMode, int percent, int fixedCount)
        {
            if (total < 0 || eligible < 0) throw new ArgumentOutOfRangeException();
            int desired = fixedMode ? Math.Max(0, Math.Min(500, fixedCount)) :
                (int)Math.Round(total * Math.Max(0, Math.Min(100, percent)) / 100.0, MidpointRounding.AwayFromZero);
            return Math.Min(Math.Min(total, eligible), desired);
        }
        public static float AddedWeight(float equipmentWeight, float referenceWeight, float multiplier, bool matches)
        {
            if (!matches) return equipmentWeight;
            if (float.IsNaN(multiplier) || float.IsInfinity(multiplier)) multiplier = 1f;
            return equipmentWeight + Math.Max(0, referenceWeight) * Math.Max(0, Math.Min(2, multiplier));
        }
        public static int SelectWeighted(IList<int> weights, double unitRandom)
        {
            if (weights.Count == 0 || weights.Any(x => x < 0) || weights.Sum() <= 0) throw new ArgumentException("Empty weights");
            if (unitRandom < 0 || unitRandom >= 1 || double.IsNaN(unitRandom)) throw new ArgumentOutOfRangeException(nameof(unitRandom));
            double position = unitRandom * weights.Sum();
            for (int i = 0; i < weights.Count; i++) { position -= weights[i]; if (position < 0) return i; }
            throw new InvalidOperationException("Invalid weighted selection");
        }
    }

    public static class Catalog
    {
        public static readonly Dictionary<string, Entry> Troops = new Dictionary<string, Entry>(StringComparer.Ordinal);
        public static readonly Dictionary<string, HashSet<string>> NativeTroops = new Dictionary<string, HashSet<string>>(StringComparer.Ordinal);
        public static readonly Dictionary<string, Dictionary<string, int>> Roles = new Dictionary<string, Dictionary<string, int>>(StringComparer.Ordinal);
        public static string[] Races = new string[0];
        public static bool Ready;
        public static void Load(string path)
        {
            Troops.Clear(); NativeTroops.Clear(); Roles.Clear(); Ready = false;
            var root = XDocument.Load(path).Root;
            foreach (var node in root.Elements("Troop"))
            {
                var e = new Entry { Id = (string)node.Attribute("id"), Race = (string)node.Attribute("race"),
                    Role = (string)node.Attribute("role"), Fallback = (string)node.Attribute("fallback"),
                    Weight = (float)node.Attribute("weight") };
                if (e.Weight < 0 || float.IsNaN(e.Weight) || float.IsInfinity(e.Weight)) throw new InvalidDataException("Invalid weight");
                Troops.Add(e.Id, e);
            }
            foreach (var node in root.Elements("Clan"))
            {
                string id = (string)node.Attribute("id");
                if (!Rules.Includes(id)) throw new InvalidDataException("Unsupported clan: " + id);
                NativeTroops.Add(id, new HashSet<string>(node.Elements("Native").Select(x => (string)x.Attribute("id")), StringComparer.Ordinal));
                Roles.Add(id, node.Elements("Role").ToDictionary(x => (string)x.Attribute("id"), x => (int)x.Attribute("weight")));
            }
            if (Troops.Count != 22 || !Rules.Clans.All(NativeTroops.ContainsKey)) throw new InvalidDataException("Incomplete coverage");
        }
        public static void Bind()
        {
            Ready = false;
            Races = TaleWorlds.Core.FaceGen.GetRaceNames();
            foreach (var entry in Troops.Values)
            {
                entry.Character = MBObjectManager.Instance.GetObject<CharacterObject>(entry.Id)
                    ?? throw new InvalidDataException("Troop missing: " + entry.Id);
                if (entry.Character.Race < 0 || entry.Character.Race >= Races.Length || Races[entry.Character.Race] != entry.Race)
                    throw new InvalidDataException("Troop race differs: " + entry.Id);
                if (MBObjectManager.Instance.GetObject<CharacterObject>(entry.Fallback) == null)
                    throw new InvalidDataException("Cleanup fallback missing: " + entry.Fallback);
            }
            Ready = true;
        }
        public static bool Matches(Agent agent, out Entry entry)
        {
            entry = null;
            return Ready && agent != null && agent.IsHuman && agent.Character != null
                && Troops.TryGetValue(agent.Character.StringId, out entry) && agent.Character.Race >= 0
                && agent.Character.Race < Races.Length && Races[agent.Character.Race] == entry.Race;
        }
        public static Entry Choose(string clan)
        {
            if (!Rules.Includes(clan)) throw new ArgumentException("Unsupported clan", nameof(clan));
            var pool = Troops.Values.ToArray();
            return pool[MBRandom.RandomInt(pool.Length)];
        }
    }

    public static class Patches
    {
        public const string Owner = "DKX.GenshinBanditRace.v1";
        [ThreadStatic] private static int spawning;
        public static readonly List<MethodBase> Targets = new List<MethodBase>();
        public static void Install()
        {
            var harmony = new Harmony(Owner);
            try
            {
                foreach (string name in new[] { "SpawnLooterParty", "SpawnBanditParty" })
                    Patch(harmony, AccessTools.DeclaredMethod(typeof(BanditSpawnCampaignBehavior), name),
                        new HarmonyMethod(typeof(Patches), nameof(BeginSpawn)), finalizer: new HarmonyMethod(typeof(Patches), nameof(EndSpawn)));
                Patch(harmony, AccessTools.DeclaredMethod(typeof(BanditSpawnCampaignBehavior), "InitializeBanditParty"),
                    postfix: new HarmonyMethod(typeof(Patches), nameof(Mix)) { priority = Priority.Last,
                        after = new[] { "DKX.BanditPopulationTuning.v1" } });
                var model = AccessTools.TypeByName("SandBox.GameComponents.SandboxAgentStatCalculateModel")
                    ?? throw new TypeLoadException("SandboxAgentStatCalculateModel");
                var method = AccessTools.DeclaredMethod(model, "GetEffectiveArmorEncumbrance")
                    ?? throw new MissingMethodException("GetEffectiveArmorEncumbrance");
                Transform(PatchProcessor.GetOriginalInstructions(method)).ToList();
                Patch(harmony, method, transpiler: new HarmonyMethod(typeof(Patches), nameof(Transform)));
            }
            catch { harmony.UnpatchAll(Owner); Targets.Clear(); throw; }
        }
        private static void Patch(Harmony h, MethodInfo method, HarmonyMethod prefix = null, HarmonyMethod postfix = null,
            HarmonyMethod finalizer = null, HarmonyMethod transpiler = null)
        {
            if (method == null) throw new MissingMethodException("Bandit creation hook");
            h.Patch(method, prefix: prefix, postfix: postfix, finalizer: finalizer, transpiler: transpiler);
            Targets.Add(method);
        }
        private static void BeginSpawn() { spawning++; }
        private static Exception EndSpawn(Exception __exception) { spawning = Math.Max(0, spawning - 1); return __exception; }
        private static void Mix(MobileParty __0, Clan __1)
        {
            if (spawning <= 0 || !Rules.Includes(__1?.StringId) || !Settings.Current.Enabled
                || __0?.BanditPartyComponent == null || __0.BanditPartyComponent.IsBossParty) return;
            // Initial new-game parties can be created before OnGameInitializationFinished.
            // At this point native party creation has already resolved all NPC definitions.
            if (!Catalog.Ready) Catalog.Bind();
            MixRoster(__0.MemberRoster, __1.StringId, Settings.Current);
            __0.Party.SetVisualAsDirty();
        }
        public static int MixRoster(TroopRoster roster, string clan, Settings settings)
        {
            if (!settings.Enabled || !Rules.Includes(clan)) return 0;
            var entries = roster.GetTroopRoster().Where(x => !x.Character.IsHero && x.WoundedNumber == 0
                && Catalog.NativeTroops[clan].Contains(x.Character.StringId)).ToArray();
            int quota = Rules.Quota(roster.TotalManCount, entries.Sum(x => x.Number), settings.FixedMode,
                settings.Percentage, settings.FixedCount);
            if (quota == 0) return 0;
            var remaining = entries.Select(x => x.Number).ToArray();
            var additions = new Dictionary<CharacterObject, int>();
            // Construct the complete transaction before changing the native roster.
            for (int i = 0; i < quota; i++)
            {
                int source = Rules.SelectWeighted(remaining, MBRandom.RandomFloat);
                remaining[source]--;
                var troop = Catalog.Choose(clan).Character ?? throw new InvalidDataException("Troop pool not bound");
                additions.TryGetValue(troop, out int count);
                additions[troop] = count + 1;
            }
            for (int i = 0; i < entries.Length; i++)
                if (remaining[i] != entries[i].Number) roster.AddToCounts(entries[i].Character, remaining[i] - entries[i].Number);
            foreach (var pair in additions) roster.AddToCounts(pair.Key, pair.Value);
            return quota;
        }
        // Insert before the native perk multiplier, rather than overriding final movement speed.
        public static IEnumerable<CodeInstruction> Transform(IEnumerable<CodeInstruction> instructions)
        {
            var result = new List<CodeInstruction>(); int matches = 0;
            foreach (var instruction in instructions)
            {
                result.Add(instruction);
                if (instruction.operand is MethodInfo called && called.DeclaringType == typeof(Equipment)
                    && called.Name == "GetTotalWeightOfArmor" && called.ReturnType == typeof(float))
                {
                    matches++;
                    result.Add(new CodeInstruction(OpCodes.Ldarg_1));
                    result.Add(new CodeInstruction(OpCodes.Call, AccessTools.Method(typeof(Patches), nameof(AddWeight))));
                }
            }
            if (matches != 1) throw new InvalidOperationException("Expected one armor-weight calculation, found " + matches);
            return result;
        }
        public static float AddWeight(float baseline, Agent agent) => Catalog.Matches(agent, out Entry e)
            ? Rules.AddedWeight(baseline, e.Weight, Settings.Current.ArmorWeightMultiplier, true) : baseline;
        public static void Uninstall() { new Harmony(Owner).UnpatchAll(Owner); Targets.Clear(); Catalog.Ready = false; }
    }

    public static class CleanupService
    {
        public static void Request()
        {
            if (!CanClean())
            {
                InformationManager.DisplayMessage(new InformationMessage("请返回战役大地图，并在没有进行中战斗时清理。"));
                return;
            }
            InformationManager.ShowInquiry(new InquiryData("原神土匪混编：清理准备",
                "请先备份存档。确认后停止混编，将本Mod兵种转换为原版土匪；人数和伤员保留。请另存新档并重载验证，清理不保证完整卸载安全。",
                true, true, "转换", "取消", Execute, null));
        }
        private static void Execute()
        {
            if (!CanClean())
            {
                InformationManager.DisplayMessage(new InformationMessage("清理条件已变化，请返回大地图并等待含本Mod兵种的战斗结束。"));
                return;
            }
            Settings.Current.Enabled = false;
            // MCM persists the changed per-save setting through the same provider as its Save button.
            MCM.Abstractions.BaseSettingsProvider.Instance?.SaveSettings(Settings.Current);
            var parties = new HashSet<PartyBase>(MobileParty.All.Select(x => x.Party));
            foreach (var settlement in Settlement.All) parties.Add(settlement.Party);
            int count = 0;
            foreach (var party in parties)
            {
                count += Convert(party.MemberRoster, id => MBObjectManager.Instance.GetObject<CharacterObject>(id));
                count += Convert(party.PrisonRoster, id => MBObjectManager.Instance.GetObject<CharacterObject>(id));
                party.SetVisualAsDirty();
            }
            InformationManager.DisplayMessage(new InformationMessage("已转换 " + count + " 名本Mod兵种并关闭混编。请另存新档、重载后验证；勿直接覆盖唯一存档。"));
        }
        private static bool CanClean() => Campaign.Current != null && Catalog.Ready && Mission.Current == null
            && !MobileParty.All.Any(x => x.MapEvent != null &&
                (x.MemberRoster.GetTroopRoster().Any(t => Catalog.Troops.ContainsKey(t.Character.StringId)) ||
                 x.PrisonRoster.GetTroopRoster().Any(t => Catalog.Troops.ContainsKey(t.Character.StringId))));
        public static int Convert(TroopRoster roster, Func<string, CharacterObject> resolve)
        {
            if (roster == null) return 0;
            int count = 0;
            var plan = roster.GetTroopRoster().Where(x => !x.Character.IsHero && Catalog.Troops.ContainsKey(x.Character.StringId))
                .Select(x => new { Item = x, Target = resolve(Catalog.Troops[x.Character.StringId].Fallback)
                    ?? throw new InvalidDataException("Cleanup fallback missing: " + x.Character.StringId) }).ToArray();
            foreach (var conversion in plan)
            {
                var item = conversion.Item;
                roster.AddToCounts(item.Character, -item.Number, woundedCount: -item.WoundedNumber, xpChange: -item.Xp);
                roster.AddToCounts(conversion.Target, item.Number, woundedCount: item.WoundedNumber, xpChange: item.Xp);
                count += item.Number;
            }
            return count;
        }
    }

    public sealed class SubModule : MBSubModuleBase
    {
        private string warning;
        public static readonly string Root = Path.GetFullPath(Path.Combine(Path.GetDirectoryName(typeof(SubModule).Assembly.Location), "..", ".."));
        protected override void OnSubModuleLoad()
        {
            base.OnSubModuleLoad();
            try { Catalog.Load(Path.Combine(Root, "ModuleData", "bandit_catalog.xml")); Patches.Install(); }
            catch (Exception error) { Fail(error); }
        }
        public override void OnGameInitializationFinished(Game game)
        {
            base.OnGameInitializationFinished(game);
            if (!(game.GameType is Campaign)) return;
            try { Catalog.Bind(); }
            catch (Exception error) { Fail(error); }
            ShowWarning();
        }
        protected override void OnBeforeInitialModuleScreenSetAsRoot() { base.OnBeforeInitialModuleScreenSetAsRoot(); ShowWarning(); }
        private void Fail(Exception error)
        {
            Catalog.Ready = false;
            warning = "原神土匪混编：初始化失败，混编未启用；请查看本模块 ModuleData/runtime.log。";
            try { File.AppendAllText(Path.Combine(Root, "ModuleData", "runtime.log"), error + Environment.NewLine); }
            catch (IOException) { } catch (UnauthorizedAccessException) { }
        }
        private void ShowWarning() { if (warning != null) { InformationManager.DisplayMessage(new InformationMessage(warning)); warning = null; } }
        protected override void OnSubModuleUnloaded() { Patches.Uninstall(); base.OnSubModuleUnloaded(); }
    }
}
