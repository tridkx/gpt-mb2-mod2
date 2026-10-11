using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Reflection.Emit;
using HarmonyLib;
using TaleWorlds.Core;
using TaleWorlds.MountAndBlade;
using TaleWorlds.ModuleManager;
using RaceTroopBuilder.Armor;

namespace RaceTroopBuilder.ArmorRuntime
{
    public sealed class SubModule : MBSubModuleBase
    {
        private static bool patched;
        public override void OnGameInitializationFinished(Game game)
        {
            if (GameNetwork.IsMultiplayer) return;
            // Rebuild for each campaign, including reloads. Only enabled modules supply defaults.
            ArmorRegistry.Load(TaleWorlds.Engine.Utilities.GetModulesNames()
                .Where(x => !string.IsNullOrWhiteSpace(x)).Select(ModuleHelper.GetModuleFullPath));
            if (patched || !ArmorRegistry.HasValues) return;
            var type = AccessTools.TypeByName("SandBox.GameComponents.SandboxAgentStatCalculateModel");
            var target = AccessTools.Method(type, "UpdateHumanStats");
            if (target == null) throw new InvalidOperationException("RaceTroopBuilder armor: unsupported game stat model.");
            // Fail explicitly on changed IL; never silently claim armor is active.
            ArmorPatch.Transform(PatchProcessor.GetOriginalInstructions(target)).ToList();
            new Harmony("RaceTroopBuilder.Armor.v1").Patch(target,
                transpiler: new HarmonyMethod(typeof(ArmorPatch), nameof(ArmorPatch.Transpiler)));
            patched = true;
        }
    }

    public static class ArmorRegistry
    {
        private static Dictionary<string, ArmorValues> races = new Dictionary<string, ArmorValues>(StringComparer.Ordinal);
        private static Dictionary<string, Tuple<string, ArmorValues>> troops = new Dictionary<string, Tuple<string, ArmorValues>>(StringComparer.Ordinal);
        private static string[] raceNames = new string[0];
        public static bool HasValues { get { return races.Count != 0 || troops.Count != 0; } }
        public static void Load(IEnumerable<string> modules)
        {
            Load(modules, TaleWorlds.Core.FaceGen.GetRaceNames());
        }
        public static void Load(IEnumerable<string> modules, string[] names)
        {
            var defaults = new Dictionary<string, ArmorValues>(StringComparer.Ordinal);
            var overrides = new Dictionary<string, Tuple<string, ArmorValues>>(StringComparer.Ordinal);
            foreach (var module in modules.Distinct(StringComparer.OrdinalIgnoreCase))
            {
                foreach (var entry in ArmorProtocol.ReadRaces(Path.Combine(module, "ModuleData", ArmorProtocol.RaceFile)))
                {
                    if (defaults.ContainsKey(entry.Key)) throw new InvalidDataException("Duplicate race armor: " + entry.Key);
                    defaults.Add(entry.Key, entry.Value);
                }
                var file = Path.Combine(module, "ModuleData", ArmorProtocol.TroopFile);
                if (!File.Exists(file)) continue;
                foreach (var entry in ArmorProtocol.ReadRoot(file, "TroopArmor").Elements())
                {
                    var id = (string)entry.Attribute("id"); var race = (string)entry.Attribute("race");
                    if (entry.Name != "Troop" || string.IsNullOrWhiteSpace(id) || string.IsNullOrWhiteSpace(race) || overrides.ContainsKey(id))
                        throw new InvalidDataException("Invalid or duplicate troop armor: " + file);
                    overrides.Add(id, Tuple.Create(race, ArmorProtocol.ReadValues(entry)));
                }
            }
            raceNames = names;
            if (defaults.Keys.Concat(overrides.Values.Select(x => x.Item1)).Any(x => !raceNames.Contains(x)))
                throw new InvalidDataException("Armor configuration refers to an unregistered race.");
            races = defaults; troops = overrides;
        }
        // One authority: a troop override replaces the racial intrinsic value, never stacks with it.
        public static float Resolve(float equipmentArmor, string troop, string race, int part)
        {
            Tuple<string, ArmorValues> selected;
            ArmorValues value;
            if (troops.TryGetValue(troop, out selected) && selected.Item1 == race) value = selected.Item2;
            else races.TryGetValue(race, out value);
            return equipmentArmor + (value == null ? 0 : value.Get(part));
        }
        public static float Apply(float equipmentArmor, Agent agent, int part)
        {
            if (agent == null || !agent.IsHuman || agent.Character == null) return equipmentArmor;
            var index = agent.Character.Race;
            if (index < 0 || index >= raceNames.Length) return equipmentArmor;
            return Resolve(equipmentArmor, agent.Character.StringId, raceNames[index], part);
        }
    }

    public static class ArmorPatch
    {
        private static readonly string[] sums = { "GetHeadArmorSum", "GetHumanBodyArmorSum", "GetArmArmorSum", "GetLegArmorSum" };
        public static IEnumerable<CodeInstruction> Transpiler(IEnumerable<CodeInstruction> instructions) { return Transform(instructions); }
        public static List<CodeInstruction> Transform(IEnumerable<CodeInstruction> instructions)
        {
            var result = new List<CodeInstruction>(); var counts = new int[4];
            foreach (var instruction in instructions)
            {
                result.Add(instruction);
                var method = instruction.operand as MethodInfo;
                var part = method == null || (instruction.opcode != OpCodes.Call && instruction.opcode != OpCodes.Callvirt)
                    ? -1 : Array.IndexOf(sums, method.Name);
                if (part < 0) continue;
                if (method.DeclaringType != typeof(Equipment) || method.ReturnType != typeof(float) || method.GetParameters().Length != 0)
                    throw new InvalidOperationException("Unsupported armor calculation signature.");
                counts[part]++;
                result.Add(new CodeInstruction(OpCodes.Ldarg_1));
                result.Add(new CodeInstruction(OpCodes.Ldc_I4, part));
                result.Add(new CodeInstruction(OpCodes.Call, AccessTools.Method(typeof(ArmorRegistry), nameof(ArmorRegistry.Apply))));
            }
            if (counts.Any(x => x != 1)) throw new InvalidOperationException("Expected exactly four native armor calculation calls.");
            return result;
        }
    }
}
