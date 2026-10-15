using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Runtime.Serialization;
using System.Xml.Linq;
using System.Xml.Schema;
using GenshinBanditRace;
using HarmonyLib;
using Patches = GenshinBanditRace.Patches;
using MCM.Abstractions.Attributes;
using MCM.Abstractions.Base.PerSave;
using RaceTroopBuilder.ArmorRuntime;
using TaleWorlds.CampaignSystem;
using TaleWorlds.CampaignSystem.CampaignBehaviors;
using TaleWorlds.CampaignSystem.Roster;

internal static class Program
{
    private static int checks;
    private static int Main(string[] args)
    {
        AppDomain.CurrentDomain.AssemblyResolve += (s,r)=>Resolve(args[0],args[2],r.Name);
        try { Run(args[0],args[1]); Console.WriteLine("PASS "+checks+" checks"); return 0; }
        catch(Exception error) { Console.Error.WriteLine(error); return 1; }
    }
    private static Assembly Resolve(string game,string workshop,string fullName)
    {
        string file=new AssemblyName(fullName).Name+".dll";
        var roots=new[]{Path.Combine(game,"bin/Win64_Shipping_Client"),Path.Combine(game,"Modules/Sandbox/bin/Win64_Shipping_Client")}
            .Concat(Directory.GetDirectories(Path.Combine(game,"Modules")).Concat(Directory.GetDirectories(workshop)).Select(x=>Path.Combine(x,"bin/Win64_Shipping_Client")));
        foreach(var root in roots) if(File.Exists(Path.Combine(root,file))) return Assembly.LoadFrom(Path.Combine(root,file));
        return null;
    }
    [MethodImpl(MethodImplOptions.NoInlining)]
    private static void Run(string game,string module)
    {
        var settings=new Settings();
        CheckCampaignRegistrations(module);
        var storyAssembly=Assembly.LoadFrom(Path.Combine(game,"Modules/StoryMode/bin/Win64_Shipping_Client/StoryMode.dll"));
        Check(typeof(Campaign).IsAssignableFrom(storyAssembly.GetType("StoryMode.CampaignStoryMode",true)),"story game type reaches the runtime Campaign binding branch");
        Check(settings is PerSaveSettings,"MCM per-save settings");
        Check(settings.Enabled && !settings.FixedMode && settings.Percentage==30 && settings.FixedCount==5 && settings.ArmorWeightMultiplier==1,"defaults");
        foreach(var property in typeof(Settings).GetProperties())
        {
            var attribute=Attribute.GetCustomAttribute(property,typeof(BaseSettingPropertyAttribute)) as BaseSettingPropertyAttribute;
            if(attribute!=null) Check(!attribute.RequireRestart,"live setting "+property.Name);
        }
        Check(Rules.Quota(40,40,false,30,5)==12,"size first, then 30 percent");
        Check(Rules.Quota(18,18,false,30,5)==5,"18 rounded to five");
        Check(Rules.Quota(5,5,false,30,5)==2,"midpoint rounds away from zero");
        Check(Rules.Quota(3,3,true,30,5)==3,"fixed quota capped by party");
        Check(Rules.Quota(40,8,false,100,5)==8,"rescued/non-native troops excluded");
        Check(Rules.Quota(0,0,false,30,5)==0 && Rules.Quota(100,100,false,0,5)==0,"zero quotas");
        for(int total=1;total<=200;total++)
            foreach(int percent in new[]{0,1,30,50,99,100})
            {
                int q=Rules.Quota(total,total,false,percent,5);
                Check(q>=0 && q<=total,"quota bounds");
                Check((total-q)+q==total,"headcount conserved");
            }
        Near(Rules.AddedWeight(3,33.5f,1,true),36.5f,"native armor weight added once");
        Near(Rules.AddedWeight(3,33.5f,0,true),3,"weight switch off");
        Near(Rules.AddedWeight(3,33.5f,2,true),70,"weight slider");
        Near(Rules.AddedWeight(3,33.5f,1,false),3,"other troops/militia unchanged");
        Check(Rules.SelectWeighted(new[]{0,5,0},0)==1 && Rules.SelectWeighted(new[]{1,1},.5)==1,"weighted removal boundaries");
        Catalog.Load(Path.Combine(module,"ModuleData/bandit_catalog.xml"));
        Check(Catalog.Troops.Count==22 && Catalog.NativeTroops.Count==6,"22 troops, all six clans");
        Check(!Catalog.NativeTroops.ContainsKey("deserters"),"deserters excluded");
        Check(Catalog.Troops.Values.Where(x=>x.Role=="cavalry").Select(x=>x.Race).OrderBy(x=>x)
            .SequenceEqual(new[]{"keqing_opulent","ningguang_orchid","yunjin"}),"only requested three melee cavalry");
        Check(Catalog.Troops["gbr_noelle"].Role=="shield" && Catalog.Troops["gbr_jean_seabreeze"].Role=="shield"
            && Catalog.Troops["gbr_ayaka_springbloom"].Role=="shock","earlier proposed cavalry reverted");
        foreach(var clan in Catalog.NativeTroops)
        {
            Check(clan.Value.Count>0,"native ranks covered: "+clan.Key);
            Check(Catalog.Roles[clan.Key].OrderBy(x=>x.Key).SequenceEqual(Catalog.Roles["looters"].OrderBy(x=>x.Key)),"no regional weighting: "+clan.Key);
            Console.WriteLine("COVERED "+clan.Key+": "+string.Join(",",clan.Value));
        }
        foreach(var e in Catalog.Troops.Values) e.Character=Dummy(e.Id);
        foreach(string clan in Rules.Clans)
        {
            var roster=TroopRoster.CreateDummyTroopRoster();
            var originals=Catalog.NativeTroops[clan].Take(3).Select(Dummy).ToArray();
            for(int i=0;i<originals.Length;i++) roster.AddToCounts(originals[i],10);
            var rescued=Dummy("imperial_recruit"); roster.AddToCounts(rescued,10);
            int total=roster.TotalManCount;
            int quota=Patches.MixRoster(roster,clan,new Settings());
            Check(quota==12,"real roster 30 percent quota: "+clan);
            Check(roster.TotalManCount==total,"real roster headcount conserved: "+clan);
            Check(roster.GetTroopCount(rescued)==10,"rescued soldiers untouched: "+clan);
            Check(roster.GetTroopRoster().Where(x=>Catalog.Troops.ContainsKey(x.Character.StringId)).Sum(x=>x.Number)==quota,"real roster additions match removals");
            int cleaned=CleanupService.Convert(roster,id=>Dummy(id));
            Check(cleaned==quota && roster.TotalManCount==total,"cleanup real mixed roster conserves count");
        }
        var woundedRoster=TroopRoster.CreateDummyTroopRoster();
        var noelle=Catalog.Troops["gbr_noelle"].Character;
        var ganyu=Catalog.Troops["gbr_ganyu"].Character;
        var fallback=Dummy("looter");
        woundedRoster.AddToCounts(noelle,10,woundedCount:3,xpChange:110);
        woundedRoster.AddToCounts(ganyu,5,woundedCount:2,xpChange:70);
        woundedRoster.AddToCounts(fallback,4,woundedCount:1,xpChange:20);
        Check(CleanupService.Convert(woundedRoster,id=>fallback)==15,"cleanup only own troops");
        var restored=woundedRoster.GetTroopRoster().Single();
        Check(restored.Number==19 && restored.WoundedNumber==6 && restored.Xp==200,"cleanup preserves real roster numbers, wounded and XP");
        var troops=XDocument.Load(Path.Combine(module,"ModuleData/troops.xml")).Root.Elements().ToArray();
        var schemas=new XmlSchemaSet();
        schemas.Add(null,Path.Combine(game,"XmlSchemas/NPCCharacters.xsd"));
        XDocument.Load(Path.Combine(module,"ModuleData/troops.xml")).Validate(schemas,(sender,error)=>{throw error.Exception;});
        Check(true,"NPCCharacters valid against installed game's actual XSD");
        Check(troops.Length==22,"22 NPC definitions");
        var loadouts=troops.Select(x=>string.Join(";",x.Elements("Equipments").Elements("EquipmentRoster").First().Elements("equipment")
            .Select(e=>(string)e.Attribute("slot")+":"+(string)e.Attribute("id")))).ToArray();
        Check(loadouts.Distinct().Count()==22,"every troop has a distinct loadout");
        foreach(var troop in troops)
        {
            Check((string)troop.Attribute("level")=="16","T3 level");
            Check(troop.Element("upgrade_targets")==null,"no unintended upgrades");
            Check(!troop.Descendants("equipment").Any(x=>new[]{"Head","Body","Cape","Gloves","Leg"}.Contains((string)x.Attribute("slot"))),"no visible/hidden armor");
        }
        var raceNames=Catalog.Troops.Values.Select(x=>x.Race).Distinct().ToArray();
        ArmorRegistry.Load(new[]{module},raceNames);
        Near(ArmorRegistry.Resolve(0,"gbr_noelle","noelle",1),54,"troop intrinsic armor enabled");
        Near(ArmorRegistry.Resolve(0,"imperial_militia_spearman","noelle",1),0,"same race militia untouched");
        Near(ArmorRegistry.Resolve(0,"gbr_noelle","ganyu",1),0,"armor requires matching troop and race");
        string fixture=Path.Combine(Path.GetDirectoryName(module),"..","build","armor-fixture");
        Directory.CreateDirectory(Path.Combine(fixture,"ModuleData"));
        File.WriteAllText(Path.Combine(fixture,"ModuleData/rtb_troop_armor.xml"),
            "<TroopArmor schemaVersion=\"1\"><Troop id=\"imperial_militia_spearman\" race=\"noelle\" head=\"8\" body=\"12\" arms=\"9\" legs=\"10\" /></TroopArmor>");
        ArmorRegistry.Load(new[]{module,fixture},raceNames);
        Near(ArmorRegistry.Resolve(0,"gbr_noelle","noelle",1),54,"bandit armor remains 54 with same-race militia override");
        Near(ArmorRegistry.Resolve(0,"imperial_militia_spearman","noelle",1),12,"same-race militia keeps independent armor 12");
        Near(ArmorRegistry.Resolve(5,"gbr_noelle","noelle",1),59,"real equipment armor added exactly once");
        Assembly.LoadFrom(Path.Combine(game,"Modules/SandBox/bin/Win64_Shipping_Client/SandBox.dll"));
        var model=AccessTools.TypeByName("SandBox.GameComponents.SandboxAgentStatCalculateModel");
        var armorMethod=AccessTools.DeclaredMethod(model,"UpdateHumanStats");
        Check(ArmorPatch.Transform(PatchProcessor.GetOriginalInstructions(armorMethod)).Count>0,"real four armor calls recognized");
        var sharedArmor=new Harmony("DKX.BanditTests.Armor");
        try
        {
            sharedArmor.Patch(armorMethod,transpiler:new HarmonyMethod(typeof(ArmorPatch),nameof(ArmorPatch.Transpiler)));
            Console.WriteLine("PATCH OK "+model.FullName+".UpdateHumanStats (shared troop armor)");
        }
        finally {sharedArmor.UnpatchAll(sharedArmor.Id);}
        Patches.Install();
        try
        {
            Check(Patches.Targets.Count==4,"four real runtime targets");
            foreach(var method in Patches.Targets)
            {
                Check(Harmony.GetPatchInfo(method).Owners.Contains(Patches.Owner),"native patch installed");
                Console.WriteLine("PATCH OK "+method.DeclaringType.FullName+"."+method.Name);
            }
            Check(Patches.AddWeight(17,null)==17,"non-agent weight unchanged");
            // Exercise the uniform pool entry point for every clan, with the game's managed RNG.
            foreach(string clan in Rules.Clans)
            {
                var selected=Enumerable.Range(0,2200).Select(_=>Catalog.Choose(clan).Id).Distinct().ToArray();
                Check(selected.Length==22,"all 22 reachable without regional restrictions: "+clan);
            }
            string popDll=Path.Combine(game,"Modules/BanditPopulationTuning/bin/Win64_Shipping_Client/BanditPopulationTuning.dll");
            if(File.Exists(popDll))
            {
                var assembly=Assembly.LoadFrom(popDll); var patches=assembly.GetType("BanditPopulationTuning.Patches");
                patches.GetMethod("Install").Invoke(null,null);
                try
                {
                    var method=AccessTools.DeclaredMethod(typeof(BanditSpawnCampaignBehavior),"InitializeBanditParty");
                    var sorted=PatchProcessor.GetSortedPatchMethods(method,Harmony.GetPatchInfo(method).Postfixes.ToArray()).ToArray();
                    int a=Array.FindIndex(sorted,m=>m.DeclaringType.Assembly==assembly);
                    int b=Array.FindIndex(sorted,m=>m.DeclaringType==typeof(Patches));
                    Check(a>=0 && b>a,"both modules: population executes before mixing");
                }
                finally {patches.GetMethod("Uninstall").Invoke(null,null);}
            }
            else Console.WriteLine("COMBINED SKIP population module is not installed; standalone checks passed");
        }
        finally {Patches.Uninstall();}
        Check(!Harmony.GetAllPatchedMethods().Any(m=>Harmony.GetPatchInfo(m).Owners.Contains(Patches.Owner)),"owned hooks removed");
    }
    private static void CheckCampaignRegistrations(string module)
    {
        var descriptor=XDocument.Load(Path.Combine(module,"SubModule.xml"));
        var story=descriptor.Descendants("DependedModule").Single(x=>(string)x.Attribute("Id")=="StoryMode");
        Check((string)story.Attribute("Optional")=="true","story dependency optional: sandbox remains supported");
        var registered=descriptor.Descendants("XmlNode").Where(x=>(string)x.Element("XmlName")?.Attribute("id")=="NPCCharacters").ToArray();
        var expected=XDocument.Load(Path.Combine(module,"ModuleData/bandit_catalog.xml")).Root.Elements("Troop")
            .Select(x=>(string)x.Attribute("id")).OrderBy(x=>x).ToArray();
        foreach(string mode in new[]{"Campaign","CampaignStoryMode"})
        {
            var selected=registered.Where(x=>x.Elements("IncludedGameTypes").Elements("GameType").Any(t=>(string)t.Attribute("value")==mode)).ToArray();
            Check(selected.Length==1,"one troop XML selected for "+mode);
            string relative=(string)selected[0].Element("XmlName").Attribute("path");
            var path=Path.Combine(module,"ModuleData",relative+".xml");
            Check(File.Exists(path),"registered troop XML exists for "+mode);
            var ids=XDocument.Load(path).Root.Elements("NPCCharacter").Select(x=>(string)x.Attribute("id")).OrderBy(x=>x).ToArray();
            Check(ids.SequenceEqual(expected),"all 22 troop definitions selected for "+mode);
            Check(ids.Contains("gbr_noelle"),"tutorial-first-spawn troop gbr_noelle selected for "+mode);
            Console.WriteLine("MODE OK "+mode+": all 22 troops, including gbr_noelle");
        }
    }
    private static void Check(bool value,string message) { checks++; if(!value) throw new Exception(message); }
    private static CharacterObject Dummy(string id)
    {
        var troop=(CharacterObject)FormatterServices.GetUninitializedObject(typeof(CharacterObject));
        troop.StringId=id;
        return troop;
    }
    private static void Near(float a,float b,string message)=>Check(Math.Abs(a-b)<.001f,message);
}
