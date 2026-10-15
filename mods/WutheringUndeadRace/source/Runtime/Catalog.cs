using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Xml.Linq;
using TaleWorlds.CampaignSystem;
using TaleWorlds.CampaignSystem.Party;
using TaleWorlds.Core;
using TaleWorlds.ObjectSystem;

namespace WutheringUndeadRace
{
 public sealed class Entry
 {
  public string Id,Key,Race,Role; public int Tier; public bool Lord;
  public float Weight; public int[] Armor; public CharacterObject Character;
 }
 public static class Catalog
 {
  public const string Prefix="wur_";
  public static readonly Dictionary<string,Entry> Entries=new Dictionary<string,Entry>();
  public static string[] Keys;
  public static void Load(string file)
  {
   Entries.Clear();
   foreach(var n in XDocument.Load(file).Root.Elements("Troop"))
   {
    var e=new Entry {Id=(string)n.Attribute("id"),Key=(string)n.Attribute("key"),Race=(string)n.Attribute("race"),Role=(string)n.Attribute("role"),
     Tier=(int)n.Attribute("tier"),Lord=(bool)n.Attribute("lord"),Weight=(float)n.Attribute("weight"),
     Armor=new[]{(int)n.Attribute("head"),(int)n.Attribute("body"),(int)n.Attribute("arms"),(int)n.Attribute("legs")}};
    if(e.Weight<0 || e.Armor.Any(v=>v<0 || v>500))throw new InvalidDataException("Invalid troop stats: "+e.Id);
    Entries.Add(e.Id,e);
   }
   Keys=Entries.Values.Select(e=>e.Key).Distinct().ToArray();
   if(Entries.Count!=48 || Keys.Length!=8)throw new InvalidDataException("Expected 40 troops and 8 lord templates");
  }
  public static void Bind()
  {
   foreach(var e in Entries.Values)
   {
    e.Character=MBObjectManager.Instance.GetObject<CharacterObject>(e.Id) ?? throw new InvalidDataException("Missing "+e.Id);
    var races=FaceGen.GetRaceNames();
    if(e.Character.Race<0 || e.Character.Race>=races.Length || races[e.Character.Race]!=e.Race)throw new InvalidDataException("Race mismatch: "+e.Id);
   }
  }
  public static Entry For(BasicCharacterObject c)
  {
   if(c==null)return null;
   if(Entries.TryGetValue(c.StringId,out var e))return e;
   var hero=(c as CharacterObject)?.HeroObject;
   return hero?.Template!=null && Entries.TryGetValue(hero.Template.StringId,out e)?e:null;
  }
  public static Entry Troop(string key,int tier)=>Entries["wur_"+key+"_t"+Math.Max(1,Math.Min(5,tier))];
  public static bool Zombie(MobileParty p)=>p!=null && p.ActualClan?.StringId=="wur_infected_clan";
  public static bool Zombie(PartyBase p)=>p!=null && p.IsMobile && Zombie(p.MobileParty);
  public static bool Lord(Hero h)=>h!=null && For(h.CharacterObject)?.Lord==true;
  public static bool Faction(IFaction f)=>f?.StringId=="wur_infected_kingdom" || f?.StringId=="wur_infected_clan";
  public static Entry Convert(CharacterObject c)
  {
   string role=c.IsMounted?(c.IsRanged?"HorseArcher":"Cavalry"):(c.IsRanged?"Ranged":"Infantry");
   var pool=Entries.Values.Where(e=>!e.Lord && e.Role==role && e.Tier==Math.Max(1,Math.Min(5,c.Tier))).ToArray();
   return pool[MBRandom.RandomInt(pool.Length)];
  }
 }
 public static class Rules
 {
  public static int Count(double expected,double random)=>Math.Max(0,(int)Math.Floor(expected)+(random<expected-Math.Floor(expected)?1:0));
  public static int Room(int party,int global,int partyCap,int globalCap)=>Math.Max(0,Math.Min(partyCap-party,globalCap-global));
  public static int[] Allocate(int total,int[] weights)
  {
   if(total<0 || weights.Length==0 || weights.Any(w=>w<0) || weights.Sum()==0)throw new ArgumentException();
   long sum=weights.Sum(w=>(long)w);var result=weights.Select(w=>(int)((long)total*w/sum)).ToArray();
   foreach(int i in Enumerable.Range(0,weights.Length).OrderByDescending(i=>(long)total*weights[i]%sum).Take(total-result.Sum()))result[i]++;
   return result;
  }
 }
}
