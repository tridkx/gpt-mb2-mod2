using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Reflection.Emit;
using System.Runtime.CompilerServices;
using HarmonyLib;
using RaceTroopBuilder.ArmorRuntime;

internal static class Program
{
    private static string game;
    private static int failures;
    private static readonly List<string> results = new List<string>();
    private static void Assert(bool condition, string message) { if (!condition) throw new Exception(message); }
    private static void Test(string name, Action test)
    {
        try { test(); results.Add(name + ": pass"); }
        catch (Exception e) { failures++; results.Add(name + ": FAIL " + e); }
    }
    public static int Main(string[] args)
    {
        game = args[0];
        AppDomain.CurrentDomain.AssemblyResolve += (sender, e) =>
        {
            var name = new AssemblyName(e.Name).Name + ".dll";
            var paths = new[] { Path.Combine(game, "bin", "Win64_Shipping_Client", name), Path.Combine(game, "Modules", "SandBox", "bin", "Win64_Shipping_Client", name) };
            return paths.Where(File.Exists).Select(Assembly.LoadFrom).FirstOrDefault();
        };
        return Run(args[1]);
    }
    [MethodImpl(MethodImplOptions.NoInlining)]
    private static int Run(string output)
    {
        Directory.CreateDirectory(output);
        var a = Path.Combine(output, "default"); var b = Path.Combine(output, "override");
        Directory.CreateDirectory(Path.Combine(a, "ModuleData")); Directory.CreateDirectory(Path.Combine(b, "ModuleData"));
        File.WriteAllText(Path.Combine(a, "ModuleData/rtb_race_armor.xml"), "<RaceArmor schemaVersion='1'><Race id='custom' head='10' body='30' arms='20' legs='25'/></RaceArmor>");
        File.WriteAllText(Path.Combine(b, "ModuleData/rtb_troop_armor.xml"), "<TroopArmor schemaVersion='1'><Troop id='elite' race='custom' head='0' body='50' arms='40' legs='45'/></TroopArmor>");
        ArmorRegistry.Load(new[] { a, b }, new[] { "human", "custom" });
        Test("unarmed racial default", () => Assert(ArmorRegistry.Resolve(0, "recruit", "custom", 1) == 30, "default"));
        Test("troop override replaces default", () => Assert(ArmorRegistry.Resolve(0, "elite", "custom", 1) == 50, "stacked"));
        Test("zero override is honored", () => Assert(ArmorRegistry.Resolve(0, "elite", "custom", 0) == 0, "zero"));
        Test("equipment plus intrinsic armor", () => Assert(ArmorRegistry.Resolve(7, "elite", "custom", 1) == 57, "equipment"));
        Test("race mismatch does not affect native humans", () => Assert(ArmorRegistry.Resolve(7, "elite", "human", 1) == 7, "human"));
        Test("real v1.4.8 stat IL inserts exactly four scoped hooks", () =>
        {
            var type = Assembly.LoadFrom(Path.Combine(game, "Modules/SandBox/bin/Win64_Shipping_Client/SandBox.dll")).GetType("SandBox.GameComponents.SandboxAgentStatCalculateModel", true);
            var target = AccessTools.Method(type, "UpdateHumanStats");
            var source = PatchProcessor.GetOriginalInstructions(target);
            var patched = ArmorPatch.Transform(source);
            Assert(patched.Count == source.Count + 12, "instruction count");
            Assert(patched.Count(x => x.operand is MethodInfo m && m.DeclaringType == typeof(ArmorRegistry) && m.Name == "Apply") == 4, "hook count");
            // Compile Harmony's replacement method offline. No agent or native engine is initialized.
            var harmony = new Harmony("RaceTroopBuilder.OfflineCheck");
            try { harmony.Patch(target, transpiler: new HarmonyMethod(typeof(ArmorPatch), "Transpiler")); }
            finally { harmony.UnpatchAll(harmony.Id); }
        });
        Test("changed game IL fails explicitly", () =>
        {
            try { ArmorPatch.Transform(new[] { new CodeInstruction(OpCodes.Ret) }); }
            catch (InvalidOperationException) { return; }
            throw new Exception("missing hooks accepted");
        });
        Test("disabled provider is ignored and registry resets", () =>
        {
            ArmorRegistry.Load(new[] { b }, new[] { "human", "custom" });
            Assert(ArmorRegistry.Resolve(0, "recruit", "custom", 1) == 0, "stale defaults");
        });
        Test("duplicate troop overrides rejected", () =>
        {
            var c = Path.Combine(output, "conflict/ModuleData"); Directory.CreateDirectory(c);
            File.Copy(Path.Combine(b, "ModuleData/rtb_troop_armor.xml"), Path.Combine(c, "rtb_troop_armor.xml"), true);
            try { ArmorRegistry.Load(new[] { b, Path.GetDirectoryName(c) }, new[] { "human", "custom" }); }
            catch (InvalidDataException) { return; }
            throw new Exception("duplicate accepted");
        });
        File.WriteAllLines(Path.Combine(output, "runtime-tests.txt"), results);
        Console.WriteLine(string.Join(Environment.NewLine, results));
        return failures == 0 ? 0 : 1;
    }
}
