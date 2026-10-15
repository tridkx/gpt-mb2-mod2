using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;
using CavalryCombatTuning;
using HarmonyLib;
using TaleWorlds.Core;
using TaleWorlds.MountAndBlade;
using MCM.Abstractions.Base;
using MCM.Abstractions.Attributes;
using MCM.Abstractions.Attributes.v2;

internal static class Program
{
    private static int _checks;

    private static int Main(string[] args)
    {
        string gameRoot = args[0];
        AppDomain.CurrentDomain.AssemblyResolve += (sender, request) =>
        {
            string name = new AssemblyName(request.Name).Name + ".dll";
            string[] roots = { "bin/Win64_Shipping_Client", "Modules/Sandbox/bin/Win64_Shipping_Client",
                "Modules/SandBoxCore/bin/Win64_Shipping_Client", "Modules/Native/bin/Win64_Shipping_Client" };
            foreach (string root in roots)
            {
                string path = Path.Combine(gameRoot, root, name);
                if (File.Exists(path)) return Assembly.LoadFrom(path);
            }
            string[] moduleRoots = { Path.Combine(gameRoot, "Modules"), args.Length > 2 ? args[2] : "" };
            foreach (string moduleRoot in moduleRoots)
                foreach (string module in Directory.Exists(moduleRoot) ? Directory.GetDirectories(moduleRoot) : new string[0])
                {
                    string path = Path.Combine(module, "bin", "Win64_Shipping_Client", name);
                    if (File.Exists(path)) return Assembly.LoadFrom(path);
                }
            return null;
        };
        try { Run(args[1]); Console.WriteLine("PASS " + _checks + " checks"); return 0; }
        catch (Exception error) { Console.Error.WriteLine(error); return 1; }
    }

    [MethodImpl(MethodImplOptions.NoInlining)]
    private static void Run(string configPath)
    {
        Settings settings = Settings.Load(configPath);
        Near(settings.ChargeDamageMultiplier, 2.5f, "default charge");
        Near(settings.MountedMovementPenaltyMultiplier, 0.7f, "default accuracy");
        foreach (WeaponClass weapon in new[] { WeaponClass.Bow, WeaponClass.Crossbow })
        {
            foreach (bool ai in new[] { false, true })
            {
                var properties = Baseline();
                StatModifier.Apply(properties, settings, false, true, true, ai, weapon);
                Near(properties.WeaponMaxMovementAccuracyPenalty, 0.14f, "mounted bow/crossbow player/AI");
                Near(properties.WeaponInaccuracy, 0.04f, "base scatter unchanged");
                Near(properties.WeaponMaxUnsteadyAccuracyPenalty, 0.3f, "hold instability unchanged");
                Near(properties.AiShooterError, 0.008f, "AI aiming unchanged");
                Near(properties.WeaponRotationalAccuracyPenaltyInRadians, 0.1f, "rotation unchanged");
            }
            var foot = Baseline();
            StatModifier.Apply(foot, settings, false, true, false, true, weapon);
            Near(foot.WeaponMaxMovementAccuracyPenalty, 0.2f, "foot archer unchanged");
        }
        foreach (WeaponClass weapon in new[] { WeaponClass.Javelin, WeaponClass.OneHandedSword, WeaponClass.Undefined })
        {
            var properties = Baseline();
            StatModifier.Apply(properties, settings, false, true, true, true, weapon);
            Near(properties.WeaponMaxMovementAccuracyPenalty, 0.2f, "throwing/melee/unarmed unchanged");
        }
        var mount = Baseline();
        for (int update = 0; update < 100; update++)
        {
            // Mirrors the original models resetting charge and movement properties every update.
            mount.MountChargeDamage = 0.12f;
            StatModifier.Apply(mount, settings, true, false, false, true, WeaponClass.Undefined);
            Near(mount.MountChargeDamage, 0.3f, "mount update is 2.5x");
        }
        settings.MountedAccuracyAIOnly = true;
        var player = Baseline();
        StatModifier.Apply(player, settings, false, true, true, false, WeaponClass.Bow);
        Near(player.WeaponMaxMovementAccuracyPenalty, 0.2f, "AI-only excludes player");
        var aiOnly = Baseline();
        StatModifier.Apply(aiOnly, settings, false, true, true, true, WeaponClass.Crossbow);
        Near(aiOnly.WeaponMaxMovementAccuracyPenalty, 0.14f, "AI-only includes AI crossbow");
        settings.ChargeDamageMultiplier = 1f;
        settings.MountedMovementPenaltyMultiplier = 1f;
        var vanilla = Baseline();
        StatModifier.Apply(vanilla, settings, true, false, false, true, WeaponClass.Undefined);
        Near(vanilla.MountChargeDamage, 0.12f, "charge 1 restores vanilla");
        StatModifier.Apply(vanilla, settings, false, true, true, true, WeaponClass.Bow);
        Near(vanilla.WeaponMaxMovementAccuracyPenalty, 0.2f, "accuracy 1 restores vanilla");
        foreach (float invalid in new[] { -1f, 11f, float.NaN, float.PositiveInfinity })
        {
            settings.ChargeDamageMultiplier = invalid;
            Reject(settings.Validate, "invalid charge rejected");
        }
        settings.ChargeDamageMultiplier = 2.5f;
        settings.MountedMovementPenaltyMultiplier = 3.1f;
        Reject(settings.Validate, "invalid accuracy rejected");
        string temp = Path.GetTempFileName();
        try
        {
            File.WriteAllText(temp, "<CavalryCombatTuning><ChargeDamageMultiplier>oops</ChargeDamageMultiplier></CavalryCombatTuning>");
            Reject(() => Settings.Load(temp), "malformed number rejected");
            File.WriteAllText(temp, "<CavalryCombatTuning><ChargeDamageMultipler>3</ChargeDamageMultipler></CavalryCombatTuning>");
            Reject(() => Settings.Load(temp), "misspelled setting rejected");
        }
        finally { File.Delete(temp); }

        var mcm = new McmSettings(new Settings
        {
            ChargeDamageMultiplier = 3.5f, MountedMovementPenaltyMultiplier = 0.6f, MountedAccuracyAIOnly = true
        });
        Check(mcm.FormatType == "json2", "MCM persists global settings");
        Check(mcm.Id == "CavalryCombatTuning_v1", "stable MCM identity");
        Check(mcm.UIVersion == 2, "MCM v2 attributes");
        foreach (string property in new[] { nameof(mcm.ChargeDamageMultiplier), nameof(mcm.MountedMovementPenaltyMultiplier), nameof(mcm.MountedAccuracyAIOnly) })
        {
            var attribute = (BaseSettingPropertyAttribute)Attribute.GetCustomAttribute(typeof(McmSettings).GetProperty(property), typeof(BaseSettingPropertyAttribute));
            Check(attribute != null && !attribute.RequireRestart, "MCM control and no-restart: " + property);
        }
        McmBridge.Connect(mcm);
        Near(RuntimePatches.CurrentSettings.ChargeDamageMultiplier, 3.5f, "legacy charge seed");
        Near(RuntimePatches.CurrentSettings.MountedMovementPenaltyMultiplier, 0.6f, "legacy accuracy seed");
        Check(RuntimePatches.CurrentSettings.MountedAccuracyAIOnly, "legacy AI-only seed");
        mcm.ChargeDamageMultiplier = 4f;
        mcm.MountedMovementPenaltyMultiplier = 0.5f;
        mcm.MountedAccuracyAIOnly = false;
        mcm.OnPropertyChanged(nameof(mcm.ChargeDamageMultiplier));
        Near(RuntimePatches.CurrentSettings.ChargeDamageMultiplier, 3.5f, "unsaved menu edit not applied");
        mcm.OnPropertyChanged(BaseSettings.SaveTriggered);
        Near(RuntimePatches.CurrentSettings.ChargeDamageMultiplier, 4f, "saved menu charge applied without restart");
        Near(RuntimePatches.CurrentSettings.MountedMovementPenaltyMultiplier, 0.5f, "saved menu accuracy applied");
        Check(!RuntimePatches.CurrentSettings.MountedAccuracyAIOnly, "saved menu AI-only applied");
        var liveMount = Baseline();
        StatModifier.Apply(liveMount, RuntimePatches.CurrentSettings, true, false, false, true, WeaponClass.Undefined);
        Near(liveMount.MountChargeDamage, 0.48f, "live saved charge used by combat modifier");
        var liveArcher = Baseline();
        StatModifier.Apply(liveArcher, RuntimePatches.CurrentSettings, false, true, true, false, WeaponClass.Crossbow);
        Near(liveArcher.WeaponMaxMovementAccuracyPenalty, 0.1f, "live saved accuracy used by combat modifier");
        McmBridge.Disconnect();
        mcm.ChargeDamageMultiplier = 5f;
        mcm.OnPropertyChanged(BaseSettings.SaveTriggered);
        Near(RuntimePatches.CurrentSettings.ChargeDamageMultiplier, 4f, "MCM event detached on unload");
        McmBridge.Connect(mcm);
        mcm.ChargeDamageMultiplier = 2.5f;
        mcm.OnPropertyChanged(BaseSettings.LoadingComplete);
        Near(RuntimePatches.CurrentSettings.ChargeDamageMultiplier, 2.5f, "reloaded MCM values applied");
        McmBridge.Disconnect();
        mcm.ChargeDamageMultiplier = float.NaN;
        Reject(() => mcm.ToRuntimeSettings(), "MCM invalid value rejected");

        // Actually install Harmony patches against both installed game methods; do not launch a mission.
        RuntimePatches.Install();
        try
        {
            foreach (MethodInfo method in RuntimePatches.ResolveTargets())
            {
                var patches = Harmony.GetPatchInfo(method);
                Check(patches != null && patches.Postfixes.Count(p => p.owner == RuntimePatches.OwnerId) == 1,
                    "one postfix: " + method.DeclaringType.FullName);
                Console.WriteLine("PATCH OK " + method.DeclaringType.FullName + "." + method.Name);
            }
        }
        finally { RuntimePatches.Uninstall(); }
        foreach (MethodInfo method in RuntimePatches.ResolveTargets())
            Check(Harmony.GetPatchInfo(method)?.Postfixes.All(p => p.owner != RuntimePatches.OwnerId) ?? true,
                "owned patch removed");
    }

    private static AgentDrivenProperties Baseline() => new AgentDrivenProperties
    {
        MountChargeDamage = 0.12f,
        WeaponInaccuracy = 0.04f,
        WeaponMaxMovementAccuracyPenalty = 0.2f,
        WeaponMaxUnsteadyAccuracyPenalty = 0.3f,
        WeaponRotationalAccuracyPenaltyInRadians = 0.1f,
        AiShooterError = 0.008f
    };
    private static void Near(float actual, float expected, string name) => Check(Math.Abs(actual - expected) < 0.000001f, name);
    private static void Check(bool result, string name)
    {
        if (!result) throw new Exception("FAIL: " + name);
        _checks++;
    }
    private static void Reject(Action action, string name)
    {
        bool rejected = false;
        try { action(); } catch (InvalidOperationException) { rejected = true; } catch (InvalidDataException) { rejected = true; }
        Check(rejected, name);
    }
}
