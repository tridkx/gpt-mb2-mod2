using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Runtime.Serialization;
using BanditPopulationTuning;
using HarmonyLib;
using Patches = BanditPopulationTuning.Patches;
using MCM.Abstractions.Attributes;
using MCM.Abstractions.Base.PerSave;
using TaleWorlds.CampaignSystem;
using TaleWorlds.CampaignSystem.CampaignBehaviors;

internal static class Program
{
    private static int checks;
    private static int simulatedNative;
    private static float observedRatio;
    private static int Main(string[] args)
    {
        AppDomain.CurrentDomain.AssemblyResolve += (s,r) => Resolve(args[0],args[2],r.Name);
        try { Run(); Console.WriteLine("PASS " + checks + " checks"); return 0; }
        catch (Exception e) { Console.Error.WriteLine(e); return 1; }
    }
    private static Assembly Resolve(string game,string workshop,string fullName)
    {
        string file = new AssemblyName(fullName).Name + ".dll";
        var roots = new[] { Path.Combine(game,"bin/Win64_Shipping_Client"), Path.Combine(game,"Modules/Sandbox/bin/Win64_Shipping_Client") }
            .Concat(Directory.GetDirectories(Path.Combine(game,"Modules")).Concat(Directory.GetDirectories(workshop))
                .Select(x => Path.Combine(x,"bin/Win64_Shipping_Client")));
        foreach (var root in roots) if (File.Exists(Path.Combine(root,file))) return Assembly.LoadFrom(Path.Combine(root,file));
        return null;
    }
    [MethodImpl(MethodImplOptions.NoInlining)]
    private static void Run()
    {
        var settings=new Settings();
        Check(settings is PerSaveSettings,"settings stored by MCM per save, no custom save types");
        Check(settings.PartyCountMultiplier==2 && settings.PartySizeMultiplier==2 && settings.ReplenishmentMultiplier==2,"all defaults 2x");
        foreach (var property in typeof(Settings).GetProperties())
        {
            var attribute=Attribute.GetCustomAttribute(property,typeof(BaseSettingPropertyAttribute)) as BaseSettingPropertyAttribute;
            if (attribute!=null) Check(!attribute.RequireRestart,"live MCM: "+property.Name);
        }
        foreach (var clan in Rules.Clans) Check(Rules.Includes(clan),"covered clan "+clan);
        foreach (var clan in new[] { "deserters","imperial","pirates",null }) Check(!Rules.Includes(clan),"excluded "+clan);
        Near(Rules.ScaleRatio(.07f,2,true),.14f,"looters replenishment 2x");
        Near(Rules.ScaleRatio(.1f,2,true),.2f,"other replenishment 2x");
        Near(Rules.ScaleRatio(.65f,2,false),.65f,"new game initialization not speed-multiplied");
        Near(Rules.ScaleRatio(.1f,0,true),0,"pause replenishment");
        foreach (int[] original in new[] { new[]{20},new[]{2,1,1},new[]{5,3,2},new[]{1,0,4},new int[0] })
            foreach(float multiplier in new[]{.25f,.5f,1f,2f,5f})
            {
                int[] counts=Rules.ScaleCounts(original,multiplier);
                int target=original.Sum()==0 ? 0 : Math.Max(1,Rules.ScaleLimit(original.Sum(),multiplier));
                Check(counts.Sum()==target,"exact rounded total for "+multiplier);
                Check(counts.All(x=>x>=0),"nonnegative counts");
                Check(counts.Where((x,i)=>original[i]==0).All(x=>x==0),"absent troops not introduced");
            }
        Check(Rules.ScaleCounts(new[]{12,5,3},2).SequenceEqual(new[]{24,10,6}),"all native ranks scaled");
        Check(Rules.ScaleLimit(6,2)==12 && Rules.ScaleLimit(49,2)==98,"both cap types doubled once");
        var testHarmony=new Harmony("DKX.BanditTests");
        Patches.Install();
        try
        {
            Check(Patches.Targets.Count==8,"all eight native hooks installed");
            foreach(var target in Patches.Targets)
            {
                var info=Harmony.GetPatchInfo(target);
                Check(info.Owners.Contains(Patches.Owner),"real game method patched");
                Console.WriteLine("PATCH OK "+target.DeclaringType.FullName+"."+target.Name);
            }
            var instance=FormatterServices.GetUninitializedObject(typeof(BanditSpawnCampaignBehavior));
            var looters=(Clan)FormatterServices.GetUninitializedObject(typeof(Clan)); looters.StringId="looters";
            var deserters=(Clan)FormatterServices.GetUninitializedObject(typeof(Clan)); deserters.StringId="deserters";
            var limit=AccessTools.DeclaredMethod(typeof(BanditSpawnCampaignBehavior),"GetCurrentLimitForLooters");
            testHarmony.Patch(limit,prefix:new HarmonyMethod(typeof(Program),nameof(NativeLimit)));
            simulatedNative=49;
            Check((int)limit.Invoke(instance,new object[]{looters})==98,"actual looter postfix doubles the final min-cap");
            Check((int)limit.Invoke(instance,new object[]{deserters})==49,"actual deserter cap untouched");
            var hideout=AccessTools.DeclaredMethod(typeof(BanditSpawnCampaignBehavior),"get__numberOfMaxBanditCountPerClanHideout");
            testHarmony.Patch(hideout,prefix:new HarmonyMethod(typeof(Program),nameof(NativeLimit)));
            simulatedNative=6;
            Check((int)hideout.Invoke(instance,null)==12,"actual bandit cap postfix doubles once");
            var spawn=AccessTools.DeclaredMethod(typeof(BanditSpawnCampaignBehavior),"SpawnLooters");
            testHarmony.Patch(spawn,prefix:new HarmonyMethod(typeof(Program),nameof(ObserveRatio)){priority=Priority.Last});
            spawn.Invoke(instance,new object[]{looters,.65f,true});
            Near(observedRatio,.65f,"real initial spawn ratio untouched");
            AccessTools.Method(typeof(Patches),"BeginNight").Invoke(null,null);
            try { spawn.Invoke(instance,new object[]{looters,.07f,false}); Near(observedRatio,.14f,"real nightly ratio doubled"); }
            finally { AccessTools.Method(typeof(Patches),"EndNight").Invoke(null,new object[]{null}); }
            Check((int)AccessTools.Field(typeof(Patches),"nightly").GetValue(null)==0,"night scope cleared");
            var natural=AccessTools.DeclaredMethod(typeof(BanditSpawnCampaignBehavior),"SpawnBanditParty");
            testHarmony.Patch(natural,prefix:new HarmonyMethod(typeof(Program),nameof(AbortSpawn)){priority=Priority.Last});
            try { natural.Invoke(instance,new object[]{looters}); } catch(TargetInvocationException) { }
            Check((int)AccessTools.Field(typeof(Patches),"spawning").GetValue(null)==0,"creation scope clears even after exception");
        }
        finally { testHarmony.UnpatchAll(testHarmony.Id); Patches.Uninstall(); }
        Check(!Harmony.GetAllPatchedMethods().Any(m=>Harmony.GetPatchInfo(m).Owners.Contains(Patches.Owner)),"all owned patches removed");
    }
    private static bool NativeLimit(ref int __result) { __result=simulatedNative; return false; }
    private static bool ObserveRatio(float __1) { observedRatio=__1; return false; }
    private static bool AbortSpawn() { throw new InvalidOperationException("offline scope test"); }
    private static void Check(bool value,string message) { checks++; if(!value) throw new Exception(message); }
    private static void Near(float a,float b,string message) => Check(Math.Abs(a-b)<.0001f,message);
}
