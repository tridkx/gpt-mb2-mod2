using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Xml.Linq;
using Helpers;
using TaleWorlds.CampaignSystem;
using TaleWorlds.CampaignSystem.Actions;
using TaleWorlds.CampaignSystem.Extensions;
using TaleWorlds.CampaignSystem.MapEvents;
using TaleWorlds.CampaignSystem.Party;
using TaleWorlds.CampaignSystem.Party.PartyComponents;
using TaleWorlds.CampaignSystem.Roster;
using TaleWorlds.CampaignSystem.Settlements;
using TaleWorlds.Core;
using TaleWorlds.Library;
using TaleWorlds.Localization;
using TaleWorlds.ObjectSystem;

namespace WutheringUndeadRace
{
 public sealed class UndeadBehavior : CampaignBehaviorBase
 {
  public static UndeadBehavior Current;
  private Clan clan;private Kingdom kingdom;
  private double started=-1,nextSpawn,nextArmy;
  private readonly Dictionary<string,double> respawn=new Dictionary<string,double>();
  private readonly Dictionary<string,double> armyStarted=new Dictionary<string,double>();
  private readonly HashSet<Hero> escape=new HashSet<Hero>();
  public override void RegisterEvents()
  {
   Current=this;
   CampaignEvents.OnSessionLaunchedEvent.AddNonSerializedListener(this,Session);
   CampaignEvents.HourlyTickEvent.AddNonSerializedListener(this,Hourly);
   CampaignEvents.QuarterHourlyTickEvent.AddNonSerializedListener(this,Quarterly);
   CampaignEvents.DailyTickEvent.AddNonSerializedListener(this,PopulationLog);
   CampaignEvents.MobilePartyDestroyed.AddNonSerializedListener(this,Destroyed);
   CampaignEvents.HeroPrisonerTaken.AddNonSerializedListener(this,Prisoner);
   CampaignEvents.CanKingdomBeDiscontinuedEvent.AddNonSerializedListener(this,ProtectKingdom);
  }
  private void ProtectKingdom(Kingdom k,ref bool result){if(Catalog.Faction(k))result=false;}
  public override void SyncData(IDataStore store)
  {
   string xml="";
   if(store.IsSaving)xml=new XElement("State",new XAttribute("version",1),new XAttribute("started",F(started)),new XAttribute("spawn",F(nextSpawn)),new XAttribute("army",F(nextArmy)),
    respawn.Select(p=>new XElement("Respawn",new XAttribute("key",p.Key),new XAttribute("time",F(p.Value)))),
    armyStarted.Select(p=>new XElement("Army",new XAttribute("key",p.Key),new XAttribute("time",F(p.Value))))).ToString(SaveOptions.DisableFormatting);
   store.SyncData("wur_state_v1",ref xml);
   if(store.IsLoading)
   {
    respawn.Clear();armyStarted.Clear();escape.Clear();clan=null;kingdom=null;
    if(string.IsNullOrWhiteSpace(xml)){started=-1;nextSpawn=nextArmy=0;return;}
    var root=XElement.Parse(xml);started=(double)root.Attribute("started");nextSpawn=(double)root.Attribute("spawn");nextArmy=(double)root.Attribute("army");
    foreach(var n in root.Elements("Respawn"))respawn.Add((string)n.Attribute("key"),(double)n.Attribute("time"));
    foreach(var n in root.Elements("Army"))armyStarted.Add((string)n.Attribute("key"),(double)n.Attribute("time"));
   }
  }
  private static string F(double n)=>n.ToString("R",CultureInfo.InvariantCulture);
  public static int TotalTroops()=>MobileParty.All.Where(Catalog.Zombie).Sum(p=>p.MemberRoster.TotalRegulars);
  private void Session(CampaignGameStarter starter)
  {
   try
   {
    Catalog.Bind();BattleService.Reset();if(started<0)started=CampaignTime.Now.ToDays;
    clan=Clan.All.FirstOrDefault(Catalog.Faction);kingdom=Kingdom.All.FirstOrDefault(Catalog.Faction);
    foreach(var hero in Hero.AllAliveHeroes)if(hero.IsPrisoner && (Catalog.Lord(hero) || Catalog.Zombie(hero.PartyBelongedToAsPrisoner)))escape.Add(hero);
    SubModule.Log("Campaign ready; lord respawn="+Settings.Current.RespawnDays+" days, speed="+Settings.Current.Speed);
    PopulationLog();
   }
   catch(Exception e){SubModule.Fail(e);}
  }
  private void PopulationLog()
  {
   if(!SubModule.Ready)return;
   var parties=MobileParty.All.Where(Catalog.Zombie).ToArray();
   SubModule.Log("Population day="+F(CampaignTime.Now.ToDays)+" parties="+parties.Length+" lord_parties="+parties.Count(p=>p.LeaderHero!=null)
    +" wanderers="+parties.Count(p=>p.LeaderHero==null)+" regulars="+parties.Sum(p=>p.MemberRoster.TotalRegulars)
    +" armies="+parties.Where(p=>p.Army!=null && p.Army.LeaderParty==p).Count()+" spawning="+Settings.Current.Spawning);
  }
  private void EnsureFaction()
  {
   var home=Settlement.All.First(s=>s.IsTown);
   var culture=MBObjectManager.Instance.GetObject<CultureObject>("empire");
   if(clan==null)
   {
    clan=Clan.CreateClan("wur_infected_clan");clan.ChangeClanName(new TextObject("感染者"),new TextObject("感染者"));
    clan.Culture=culture;clan.IsNoble=true;clan.Banner=Banner.CreateRandomClanBanner(85219);clan.SetInitialHomeSettlement(home);clan.AddRenown(6000,false);
   }
   // Create all eight living hero identities once; party spawning obeys grace/cooldown/caps.
   foreach(string key in Catalog.Keys)
   {
    var hero=FindLord(key);
    if(hero==null)
    {
     var template=Catalog.Entries["wur_"+key+"_lord_template"].Character;
     hero=HeroCreator.CreateSpecialHero(template,home,clan,age:30);hero.SetName(template.Name,template.Name);
     hero.Level=36;
     foreach(var skill in Skills.All)hero.SetSkillValue(skill,template.GetSkillValue(skill));
     hero.ChangeState(Hero.CharacterStates.Fugitive);respawn[key]=CampaignTime.Now.ToDays;
    }
   }
   if(clan.Leader==null || !clan.Leader.IsAlive)clan.SetLeader(FindLord(Catalog.Keys[0]));
   if(kingdom==null)
   {
    kingdom=Kingdom.CreateKingdom("wur_infected_kingdom");
    var name=new TextObject("感染潮");kingdom.InitializeKingdom(name,name,culture,clan.Banner,0xff362047,0xffbfdc75,home,new TextObject("失去理智的感染者，只在野外猎杀与扩散。"),name,new TextObject("感染统领"));
    ChangeKingdomAction.ApplyByCreateKingdom(clan,kingdom,false);
   }
   foreach(IFaction f in Kingdom.All.Where(k=>!k.IsEliminated).Cast<IFaction>().Concat(Clan.All.Where(c=>!c.IsEliminated && c.Kingdom==null)))
    if(!Catalog.Faction(f) && !f.IsMinorFaction && f.StringId!="neutral" && !kingdom.IsAtWarWith(f))DeclareWarAction.ApplyByDefault(kingdom,f);
   // Minor and bandit clans are enemies too, including those outside kingdom diplomacy.
   foreach(var c in Clan.All.Where(c=>!c.IsEliminated && c.Kingdom==null && c.StringId!="neutral" && !Catalog.Faction(c)))
    if(!kingdom.IsAtWarWith(c))DeclareWarAction.ApplyByDefault(kingdom,c);
  }
  private static Hero FindLord(string key)=>Hero.AllAliveHeroes.FirstOrDefault(h=>Catalog.For(h.CharacterObject)?.Id=="wur_"+key+"_lord_template");
  private void Hourly()
  {
   if(!SubModule.Ready)return;
   try
   {
    if(started<0)started=CampaignTime.Now.ToDays;
    if(CampaignTime.Now.ToDays<started+Settings.Current.GraceDays)return;
    if(clan==null && !Settings.Current.Spawning)return;
    EnsureFaction();ReleaseHeroes();
    foreach(var p in MobileParty.All.Where(Catalog.Zombie).ToArray())
    {
     if(p.MapEvent!=null)continue;
     if(p.CurrentSettlement!=null)LeaveSettlementAction.ApplyForParty(p);
     foreach(var e in p.PrisonRoster.GetTroopRoster().Where(e=>!e.Character.IsHero).ToArray())p.PrisonRoster.AddToCounts(e.Character,-e.Number,woundedCount:-e.WoundedNumber);
     Upgrade(p.Party);p.ItemRoster.Clear();
    }
    double now=CampaignTime.Now.ToDays;
    if(Settings.Current.Spawning)
    {
     foreach(string key in Catalog.Keys)
     {
      var h=FindLord(key);
      if(h?.PartyBelongedTo!=null || h==null || h.IsPrisoner)continue;
      if(!respawn.TryGetValue(key,out double when)){respawn[key]=now+Settings.Current.RespawnDays;continue;}
      if(when<0){respawn[key]=now+Settings.Current.RespawnDays;continue;}
      if(now>=when && CanSpawn())Spawn(h,key);
     }
     if(now>=nextSpawn && CanSpawn()){Spawn(null,null);nextSpawn=now+Settings.Current.SpawnHours/24.0;}
    }
    ManageArmies(now);
    foreach(var p in MobileParty.All.Where(Catalog.Zombie).ToArray())Think(p);
   }
   catch(Exception e){SubModule.Log("Hourly: "+e);}
  }
  private bool CanSpawn()=>MobileParty.All.Count(Catalog.Zombie)<Settings.Current.MaxParties && TotalTroops()<Settings.Current.MaxTroops;
  private void Spawn(Hero hero,string key)
  {
   var towns=Settlement.All.Where(s=>s.IsTown).ToArray();var home=towns[MBRandom.RandomInt(towns.Length)];
   var pos=NavigationHelper.FindPointAroundPosition(home.GatePosition,MobileParty.NavigationType.Default,25f,8f,true,true);
   if(!pos.IsOnLand || !pos.IsValid())return;
   // Keep initial spawns away from the player's immediate vicinity.
   if(MobileParty.MainParty!=null && pos.DistanceSquared(MobileParty.MainParty.Position)<36f)return;
   int count=Math.Min(Math.Min(Settings.Current.PartyCap,Settings.Current.MaxTroops-TotalTroops()),MBRandom.RandomInt(Math.Min(Settings.Current.SpawnMin,Settings.Current.SpawnMax),Math.Max(Settings.Current.SpawnMin,Settings.Current.SpawnMax)+1));
   if(count<=0)return;
   MobileParty party;
   if(hero!=null)
   {
    if(hero.CurrentSettlement!=null)LeaveSettlementAction.ApplyForCharacterOnly(hero);
    hero.ChangeState(Hero.CharacterStates.Active);hero.HitPoints=hero.MaxHitPoints;
    party=LordPartyComponent.CreateLordParty(hero.CharacterObject.StringId,hero,pos,0,null,hero);
    foreach(var e in party.MemberRoster.GetTroopRoster().Where(e=>!e.Character.IsHero).ToArray())party.MemberRoster.AddToCounts(e.Character,-e.Number,woundedCount:-e.WoundedNumber);
    respawn[key]=-1;
   }
   else party=BanditPartyComponent.CreateLooterParty("wur_horde_"+Guid.NewGuid().ToString("N"),clan,home,false,null,pos);
   for(int i=0;i<count;i++)
   {
    string k=key??Catalog.Keys[MBRandom.RandomInt(Catalog.Keys.Length)];int tier=MBRandom.RandomInt(1,Settings.Current.SpawnTier+1);
    party.MemberRoster.AddToCounts(Catalog.Troop(k,tier).Character,1);
   }
   party.ItemRoster.Clear();party.Aggressiveness=1f;party.Party.SetCustomName(new TextObject(hero==null?"游荡感染尸群":hero.Name+"的尸群"));
   party.Ai.SetDoNotMakeNewDecisions(true);party.SetMovePatrolAroundPoint(pos,MobileParty.NavigationType.Default);party.Party.SetVisualAsDirty();
   SubModule.Log("Spawn "+party.StringId+" ordinary="+count+" day="+F(CampaignTime.Now.ToDays)+" near="+home.Name+" name="+party.Name);
  }
  private void Quarterly()
  {
   if(!SubModule.Ready || clan==null)return;
   try{ReleaseHeroes();foreach(var p in MobileParty.All.Where(Catalog.Zombie).ToArray())Think(p);}
   catch(Exception e){SubModule.Log("Quarter hour: "+e);}
  }
  private void Think(MobileParty party)
  {
   if(!party.IsActive || party.MapEvent!=null || party.CurrentSettlement!=null)return;
   party.Ai.SetDoNotMakeNewDecisions(true);
   party.Ai.SetInitiative(1f,0f,2f);
   if(party.Army!=null && party.Army.LeaderParty!=party)
   {
    var leader=party.Army.LeaderParty;
    if(party.AttachedTo!=leader)
    {
     if(party.Position.DistanceSquared(leader.Position)<2.25f)party.AttachedTo=leader;
     else party.SetMoveEscortParty(leader,MobileParty.NavigationType.Default,false);
    }
    return;
   }
   var target=MobileParty.All.Where(p=>p!=party && p.IsActive && !Catalog.Zombie(p) && p.Position.IsOnLand && p.CurrentSettlement==null && !p.IsCurrentlyUsedByAQuest && !p.IsGarrison && !p.IsMilitia && p.MemberRoster.TotalManCount>0 && p.MapFaction!=null && party.MapFaction.IsAtWarWith(p.MapFaction) && (p.Army==null || p.Army.LeaderParty==p))
    .Select(p=>new {Party=p,Distance=party.Position.DistanceSquared(p.Position)})
    .Where(x=>x.Distance<=Settings.Current.ChaseRadius*Settings.Current.ChaseRadius && (x.Party.MapEvent==null || x.Party.MapEvent.InvolvedParties.Any(Catalog.Zombie)))
    .OrderBy(x=>x.Distance).FirstOrDefault()?.Party;
   if(target!=null)party.SetMoveEngageParty(target,MobileParty.NavigationType.Default);
   else if(party.DefaultBehavior!=AiBehavior.PatrolAroundPoint)party.SetMovePatrolAroundPoint(party.Position,MobileParty.NavigationType.Default);
  }
  private void ManageArmies(double now)
  {
   foreach(var a in kingdom.Armies.ToArray())
   {
    if(!Catalog.Zombie(a.LeaderParty) || a.LeaderParty.MapEvent!=null)continue;
    string id=a.LeaderParty.StringId;
    if(!armyStarted.TryGetValue(id,out double when)){when=now;armyStarted[id]=when;}
    if(!Settings.Current.Armies || now-when>=Settings.Current.ArmyHours/24.0 || a.Parties.Count<2 || a.Parties.Count>Settings.Current.ArmyParties || a.Parties.Sum(p=>p.MemberRoster.TotalRegulars)>Settings.Current.ArmyCap)
    {DisbandArmyAction.ApplyByObjectiveFinished(a);armyStarted.Remove(id);nextArmy=Math.Max(nextArmy,now+Settings.Current.ArmyCooldown/24.0);}
    else a.Cohesion=100;
   }
   if(!Settings.Current.Armies || now<nextArmy)return;
   foreach(var leader in MobileParty.All.Where(p=>Catalog.Zombie(p) && p.LeaderHero!=null && p.Army==null && p.MapEvent==null && p.CurrentSettlement==null).ToArray())
   {
    var members=MobileParty.All.Where(p=>p!=leader && Catalog.Zombie(p) && p.LeaderHero!=null && p.Army==null && p.MapEvent==null && p.CurrentSettlement==null && p.Position.DistanceSquared(leader.Position)<=Settings.Current.GatherRadius*Settings.Current.GatherRadius)
     .OrderBy(p=>p.Position.DistanceSquared(leader.Position)).ToArray();
    var chosen=new List<MobileParty>();int total=leader.MemberRoster.TotalRegulars;
    foreach(var p in members)
     if(chosen.Count<Settings.Current.ArmyParties-1 && total+p.MemberRoster.TotalRegulars<=Settings.Current.ArmyCap){chosen.Add(p);total+=p.MemberRoster.TotalRegulars;}
    if(chosen.Count==0)continue;
    var army=new Army(kingdom,leader,Army.ArmyTypes.Patrolling);
    foreach(var p in chosen)p.Army=army;
    CampaignEventDispatcher.Instance.OnArmyCreated(army);
    armyStarted[leader.StringId]=now;nextArmy=now+Settings.Current.ArmyCooldown/24.0;
    SubModule.Log("Army formed with "+army.Parties.Count+" parties, regulars="+total);break;
   }
  }
  private void Destroyed(MobileParty party,PartyBase destroyer)
  {
   if(!Catalog.Zombie(party))return;
   foreach(var e in party.MemberRoster.GetTroopRoster().Where(e=>e.Character.IsHero).ToArray())Schedule(e.Character.HeroObject);
   // The leader can already have been removed by capture resolution.
   foreach(var h in Hero.AllAliveHeroes.Where(h=>Catalog.Lord(h) && (h.PartyBelongedTo==party || h==party.LeaderHero)).ToArray())Schedule(h);
  }
  public void Schedule(Hero hero)
  {
   var e=Catalog.For(hero?.CharacterObject);if(e?.Lord!=true)return;
   respawn[e.Key]=CampaignTime.Now.ToDays+Settings.Current.RespawnDays;
   escape.Add(hero);
  }
  private void Prisoner(PartyBase capturer,Hero prisoner)
  {
   if(Catalog.Lord(prisoner))Schedule(prisoner);
   else if(Catalog.Zombie(capturer))escape.Add(prisoner);
  }
  private void ReleaseHeroes()
  {
   foreach(var h in escape.ToArray())
   {
    if(h.PartyBelongedTo?.MapEvent!=null || h.PartyBelongedToAsPrisoner?.MapEvent!=null)continue;
    if(h.IsPrisoner)EndCaptivityAction.ApplyByEscape(h,showNotification:false);
    if(Catalog.Lord(h) && h.PartyBelongedTo==null && h.IsAlive)h.ChangeState(Hero.CharacterStates.Fugitive);
    escape.Remove(h);
   }
  }
  public static void Upgrade(PartyBase party)
  {
   if(!Settings.Current.Upgrade)return;
   foreach(var e in party.MemberRoster.GetTroopRoster().ToArray())
   {
    var c=Catalog.For(e.Character);if(c==null || c.Lord || c.Tier>=5)continue;
    var next=Catalog.Troop(c.Key,c.Tier+1).Character;
    int cost=Math.Max(1,(int)Math.Ceiling(Campaign.Current.Models.PartyTroopUpgradeModel.GetXpCostForUpgrade(party,e.Character,next)*Settings.Current.UpgradeXp));
    int n=Math.Min(e.Number-e.WoundedNumber,e.Xp/cost);if(n<=0)continue;
    party.MemberRoster.AddToCounts(e.Character,-n,xpChange:-n*cost);party.MemberRoster.AddToCounts(next,n);
   }
  }
 }
}
