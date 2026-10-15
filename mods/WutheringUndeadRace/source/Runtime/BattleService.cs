using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using TaleWorlds.CampaignSystem;
using TaleWorlds.CampaignSystem.Actions;
using TaleWorlds.CampaignSystem.MapEvents;
using TaleWorlds.CampaignSystem.Party;
using TaleWorlds.CampaignSystem.Roster;
using TaleWorlds.Core;
using TaleWorlds.Library;

namespace WutheringUndeadRace
{
 public static class BattleService
 {
  private static ConditionalWeakTable<MapEvent,object> done=new ConditionalWeakTable<MapEvent,object>();
  public static void Reset(){done=new ConditionalWeakTable<MapEvent,object>();}
  public static void Resolve(MapEvent battle,Patches.CaptureState state)
  {
   if(done.TryGetValue(battle,out _))return;
   done.Add(battle,new object());
   var winners=battle.Winner.Parties.ToArray();
   var losers=battle.GetMapEventSide(battle.DefeatedSide).Parties.ToArray();
   bool zombieWin=winners.Any(p=>Catalog.Zombie(p.Party));
   if(zombieWin)
   {
    var pool=new Dictionary<CharacterObject,int>();
    if(Settings.Current.ConvertDead)
     foreach(var p in losers.Where(p=>!Catalog.Zombie(p.Party)))
      foreach(var e in p.DiedInBattle.GetTroopRoster())if(!e.Character.IsHero)Add(pool,e.Character,e.Number);
    // Snapshot is taken after pre-existing prisoner loot, immediately before new captures.
    foreach(var p in winners.Where(p=>Catalog.Zombie(p.Party)))
    {
     var r=p.RosterToReceiveLootPrisoners;
     if(r==null || !state.Before.TryGetValue(r,out var old))continue;
     foreach(var e in r.GetTroopRoster().ToArray())
     {
      if(e.Character.IsHero)continue;
      old.TryGetValue(e.Character,out int previous);int captured=Math.Max(0,e.Number-previous);
      if(captured>0 && Settings.Current.ConvertCaptured)Add(pool,e.Character,captured);
      // Corpses never retain a human prisoner economy, regardless of conversion settings.
      if(captured>0)r.AddToCounts(e.Character,-captured,woundedCount:-Math.Min(captured,e.WoundedNumber));
     }
    }
    var targets=winners.Select(p=>p.Party.MobileParty).Where(p=>Catalog.Zombie(p) && p.IsActive).ToArray();
    int total=UndeadBehavior.TotalTroops();
    foreach(var item in pool)
    {
     int add=Rules.Count(item.Value*Settings.Current.Conversion/100.0,MBRandom.RandomFloat);
     for(int i=0;i<add;i++)
     {
      var party=targets.OrderBy(p=>p.MemberRoster.TotalRegulars).FirstOrDefault(p=>Rules.Room(p.MemberRoster.TotalRegulars,total,Settings.Current.PartyCap,Settings.Current.MaxTroops)>0 && (p.Army==null || p.Army.Parties.Sum(m=>m.MemberRoster.TotalRegulars)<Settings.Current.ArmyCap));
      if(party==null)break;
      party.MemberRoster.AddToCounts(Catalog.Convert(item.Key).Character,1);total++;
     }
    }
   }
   else
   {
    var killed=new Dictionary<CharacterObject,int>();
    foreach(var p in losers.Where(p=>Catalog.Zombie(p.Party)))
     foreach(var e in p.DiedInBattle.GetTroopRoster())
      if(!e.Character.IsHero && Catalog.For(e.Character)!=null)Add(killed,e.Character,e.Number);
    var recipients=winners.Where(p=>!Catalog.Zombie(p.Party) && p.Party.LeaderHero!=null && p.Party.LeaderHero.IsAlive).ToArray();
    if(recipients.Length==0)return;
    var weights=recipients.Select(p=>Math.Max(1,p.ContributionToBattle)).ToArray();
    int points=killed.Sum(k=>k.Value*Math.Max(1,k.Key.Tier));
    var gold=Rules.Allocate(points*Settings.Current.GoldPerTier,weights);
    long weightSum=weights.Sum(w=>(long)w);var troopRewards=new int[recipients.Length];
    for(int i=0;i<recipients.Length;i++)
    {
     var hero=recipients[i].Party.LeaderHero;
     int amount=Math.Min(gold[i],int.MaxValue-Math.Max(0,hero.Gold));if(amount>0)hero.ChangeHeroGold(amount);
     if(hero.Clan!=null)ChangeClanInfluenceAction.Apply(hero.Clan,(float)(points*Settings.Current.InfluencePerTier*weights[i]/weightSum));
    }
    foreach(var k in killed)
    {
     int reward=Rules.Count(k.Value*Settings.Current.RewardPercent/100.0,MBRandom.RandomFloat);
     var counts=Rules.Allocate(reward,weights);
     for(int i=0;i<recipients.Length;i++)
     {
      if(counts[i]>0)recipients[i].RosterToReceiveLootMembers.AddToCounts(k.Key,counts[i]);
      troopRewards[i]+=counts[i];
     }
    }
    for(int i=0;i<recipients.Length;i++)if(recipients[i].Party==PartyBase.MainParty)
     InformationManager.DisplayMessage(new InformationMessage($"清剿感染者：金币 +{gold[i]}，影响力 +{points*Settings.Current.InfluencePerTier*weights[i]/weightSum:0.00}，感染兵 +{troopRewards[i]}"));
   }
  }
  private static void Add(Dictionary<CharacterObject,int> d,CharacterObject c,int n){d.TryGetValue(c,out int old);d[c]=old+n;}
 }
}
