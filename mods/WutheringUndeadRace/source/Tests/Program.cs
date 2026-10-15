using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Runtime.Serialization;
using System.Xml.Linq;
using System.Xml.Schema;
using HarmonyLib;
using TaleWorlds.CampaignSystem;
using TaleWorlds.CampaignSystem.Party;
using TaleWorlds.CampaignSystem.Roster;
using WutheringUndeadRace;
using Patches = WutheringUndeadRace.Patches;

internal static class Program
{
 static int checks;
 static int Main(string[] a)
 {
  AppDomain.CurrentDomain.AssemblyResolve+=(s,r)=>Resolve(a[0],a[2],r.Name);
  try{Run(a[0],a[1]);Console.WriteLine("PASS "+checks+" checks");return 0;}
  catch(Exception e){Console.Error.WriteLine(e);return 1;}
 }
 static Assembly Resolve(string game,string workshop,string name)
 {
  string file=new AssemblyName(name).Name+".dll";
  var roots=new[]{Path.Combine(game,"bin/Win64_Shipping_Client")}.Concat(Directory.GetDirectories(Path.Combine(game,"Modules")).Concat(Directory.GetDirectories(workshop)).Select(p=>Path.Combine(p,"bin/Win64_Shipping_Client")));
  foreach(string root in roots)if(File.Exists(Path.Combine(root,file)))return Assembly.LoadFrom(Path.Combine(root,file));return null;
 }
 [MethodImpl(MethodImplOptions.NoInlining)]
 static void Run(string game,string module)
 {
  var settings=new Settings();Check(settings.Speed==1.05f && settings.RespawnDays==3 && settings.RewardPercent==10,"agreed defaults");
  Check(Rules.Count(.5,.49)==1 && Rules.Count(.5,.5)==0,"fractional recruitment lottery");
  Check(Rules.Count(0,0)==0 && Rules.Count(10,.9)==10,"integer quotas exact");
  Check(Rules.Room(249,2999,250,3000)==1 && Rules.Room(250,2999,250,3000)==0 && Rules.Room(200,3100,250,3000)==0,"party and global caps");
  for(int n=0;n<=2000;n++)
  {
   var allocated=Rules.Allocate(n,new[]{1,3,7,29});Check(allocated.Sum()==n && allocated.All(x=>x>=0),"joint rewards conserved");
  }
  Check(Rules.Allocate(10,new[]{1,1}).SequenceEqual(new[]{5,5}),"no duplicate joint rewards");
  Catalog.Load(Path.Combine(module,"ModuleData/undead_catalog.xml"));
  Check(Catalog.Entries.Count==48 && Catalog.Entries.Values.Count(e=>!e.Lord)==40,"40 ranks, eight lords");
  foreach(var group in Catalog.Entries.Values.Where(e=>!e.Lord).GroupBy(e=>e.Key))
  {
   Check(group.Select(e=>e.Role).Distinct().Count()==1 && group.Select(e=>e.Tier).OrderBy(t=>t).SequenceEqual(new[]{1,2,3,4,5}),"one role per character, five ranks");
  }
  foreach(var role in Catalog.Entries.Values.Where(e=>!e.Lord && e.Tier==1).GroupBy(e=>e.Role))Check(role.Count()==2,"two characters per role");
  foreach(string filename in new[]{"NPCCharacters","Items","Monsters"})
  {
   string f=filename=="NPCCharacters"?"troops":filename.ToLowerInvariant();var schemas=new XmlSchemaSet();
   schemas.Add(null,Path.Combine(game,"XmlSchemas",filename+".xsd"));
   XDocument.Load(Path.Combine(module,"ModuleData",f+".xml")).Validate(schemas,(s,e)=>{throw e.Exception;});
   Check(true,"installed game schema: "+filename);
  }
  var troops=XDocument.Load(Path.Combine(module,"ModuleData/troops.xml")).Root.Elements().ToArray();
  var project=XDocument.Load(Path.Combine(module,"ModuleData/project.mbproj")).Root;
  Check((string)project.Attribute("type")=="solution","native engine project manifest exists");
  foreach(var resource in new[]{new[]{"skin","ModuleData/skins.xml"},new[]{"action_set","ModuleData/action_sets.xml"},new[]{"monster","ModuleData/monsters.xml"}})
   Check(project.Elements("file").Any(f=>(string)f.Attribute("type")==resource[0] && (string)f.Attribute("name")==resource[1]) && File.Exists(Path.Combine(module,resource[1])),"engine discovers "+resource[0]+" before NPC deserialization");
  var ownRaces=XDocument.Load(Path.Combine(module,"ModuleData/skins.xml")).Root.Elements().Select(r=>(string)r.Attribute("id")).ToArray();
  foreach(var t in troops.Where(t=>((string)t.Attribute("id")).EndsWith("_lord_template")))
   Check(ownRaces.Contains((string)t.Attribute("race")),"every lord has a race declared in the engine-registered skin file");
  foreach(var t in troops.Where(t=>((string)t.Attribute("id")).EndsWith("_lord_template")))
   Check((string)t.Attribute("is_template")=="true" && (string)t.Attribute("is_hero")!="true","dynamic lord template is not declared a static hero");
  foreach(var t in troops)
  {
   var r=t.Element("Equipments").Elements("EquipmentRoster").First();
   Check(!r.Elements().Any(e=>new[]{"Head","Body","Cape","Gloves","Leg"}.Contains((string)e.Attribute("slot"))),"five armour slots empty");
   foreach(var target in t.Elements("upgrade_targets").Elements())Check(troops.Any(x=>(string)x.Attribute("id")==((string)target.Attribute("id")).Substring(13)),"upgrade target resolves");
  }
  var shore=troops.Where(t=>((string)t.Attribute("id")).StartsWith("wur_shorekeeper_"));
  foreach(var t in shore)Check(t.Element("Equipments").Elements().First().Elements().Count()==6,"shorekeeper four weapon slots plus horse/harness");
  foreach(var e in Catalog.Entries.Values)e.Character=Dummy(e.Id);
  Check(Catalog.For(Catalog.Troop("jianxin",3).Character).Tier==3 && Catalog.For(Dummy("imperial_recruit"))==null,"own troop identity only");
  var normal=(MobileParty)FormatterServices.GetUninitializedObject(typeof(MobileParty));
  Check(!Catalog.Zombie(normal),"model/race or soldier presence does not identify a horde");
  var zombie=(MobileParty)FormatterServices.GetUninitializedObject(typeof(MobileParty));
  var infectedClan=(Clan)FormatterServices.GetUninitializedObject(typeof(Clan));infectedClan.StringId="wur_infected_clan";
  typeof(MobileParty).GetField("_actualClan",BindingFlags.Instance|BindingFlags.NonPublic).SetValue(zombie,infectedClan);
  Check(Catalog.Zombie(zombie),"only the infected clan receives horde mechanics");
  var speed=new ExplainedNumber(4.5f);Patches.Speed(zombie,ref speed);Check(Math.Abs(speed.ResultNumber-4.725f)<.0001,"default 1.05 speed multiplier");
  var normalSpeed=new ExplainedNumber(4.5f);Patches.Speed(normal,ref normalSpeed);Check(normalSpeed.ResultNumber==4.5f,"normal army/reward troops keep native speed");
  bool eats=true;Check(!Patches.Food(zombie,ref eats) && !eats,"hordes do not eat");
  int influence=20;Check(!Patches.ArmyCost(zombie,zombie,ref influence) && influence==0,"free horde army joining");
  Check(Patches.ArmyCost(normal,zombie,ref influence),"other armies retain native influence costs");
  Check(!Patches.ChangeKingdom(infectedClan,null),"infection faction cannot defect or dissolve through clan exit");
  var roster=TroopRoster.CreateDummyTroopRoster();var c=Catalog.Troop("shorekeeper",5).Character;
  roster.AddToCounts(c,10,woundedCount:3,xpChange:100);roster.AddToCounts(c,-2,woundedCount:-1);
  Check(roster.TotalManCount==8 && roster.TotalWounded==2,"real capture removal preserves remaining wounded");
  Check(Patches.Armor(7,null,0)==7 && Patches.Weight(9,null)==9,"normal agents unchanged");
  var stateA=new UndeadBehavior();var stateStore=new Store();
  typeof(UndeadBehavior).GetField("started",BindingFlags.Instance|BindingFlags.NonPublic).SetValue(stateA,123.25);
  var respawns=(System.Collections.Generic.Dictionary<string,double>)typeof(UndeadBehavior).GetField("respawn",BindingFlags.Instance|BindingFlags.NonPublic).GetValue(stateA);
  respawns["shorekeeper"]=126.25;stateA.SyncData(stateStore);
  var stateB=new UndeadBehavior();stateStore.IsLoading=true;stateB.SyncData(stateStore);
  Check((double)typeof(UndeadBehavior).GetField("started",BindingFlags.Instance|BindingFlags.NonPublic).GetValue(stateB)==123.25,"save/load campaign start preserved");
  var restored=(System.Collections.Generic.Dictionary<string,double>)typeof(UndeadBehavior).GetField("respawn",BindingFlags.Instance|BindingFlags.NonPublic).GetValue(stateB);
  Check(restored["shorekeeper"]==126.25,"save/load three-day cooldown preserved");
  Assembly.LoadFrom(Path.Combine(game,"Modules/SandBox/bin/Win64_Shipping_Client/SandBox.dll"));
  try
  {
   Patches.Install();Check(Patches.Targets.Count>=25,"actual engine method hooks installed");
   foreach(var method in Patches.Targets)
   {
    Check(Harmony.GetPatchInfo(method).Owners.Contains(Patches.Owner),"real hook ownership");
    Check(PatchProcessor.GetCurrentInstructions(method).Count>0,"patched method compiled");
    Console.WriteLine("PATCH OK "+method.DeclaringType.FullName+"."+method.Name);
   }
  }
  finally{new Harmony(Patches.Owner).UnpatchAll(Patches.Owner);}
 }
 static CharacterObject Dummy(string id){var c=(CharacterObject)FormatterServices.GetUninitializedObject(typeof(CharacterObject));c.StringId=id;return c;}
 sealed class Store:IDataStore
 {
  public bool IsLoading {get;set;}
  public bool IsSaving=>!IsLoading;
  private string value;
  public bool SyncData<T>(string key,ref T data){if(IsSaving)value=(string)(object)data;else data=(T)(object)value;return true;}
 }
 static void Check(bool b,string name){checks++;if(!b)throw new Exception(name);}
}
