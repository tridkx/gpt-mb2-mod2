using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Reflection.Emit;
using HarmonyLib;
using TaleWorlds.CampaignSystem;
using TaleWorlds.CampaignSystem.Actions;
using TaleWorlds.CampaignSystem.CampaignBehaviors;
using TaleWorlds.CampaignSystem.GameComponents;
using TaleWorlds.CampaignSystem.Encounters;
using TaleWorlds.CampaignSystem.GameMenus;
using TaleWorlds.CampaignSystem.MapEvents;
using TaleWorlds.CampaignSystem.Party;
using TaleWorlds.CampaignSystem.Roster;
using TaleWorlds.Core;
using TaleWorlds.Localization;
using TaleWorlds.MountAndBlade;

namespace WutheringUndeadRace
{
 public static class Patches
 {
  public const string Owner="DKX.WutheringUndeadRace.v1";
  public static readonly List<MethodBase> Targets=new List<MethodBase>();
  public static void Install()
  {
   var h=new Harmony(Owner);Targets.Clear();
   try
   {
    Patch(h,typeof(DefaultPartySpeedCalculatingModel),"CalculateFinalSpeed",post:nameof(Speed));
    Patch(h,typeof(DefaultMobilePartyFoodConsumptionModel),"DoesPartyConsumeFood",pre:nameof(Food));
    Patch(h,typeof(DefaultMobilePartyFoodConsumptionModel),"CalculateDailyFoodConsumptionf",pre:nameof(Consumption));
    Patch(h,typeof(DefaultPartyWageModel),"GetTotalWage",pre:nameof(Wage));
    Patch(h,typeof(DefaultPartyMoraleModel),"GetEffectivePartyMorale",pre:nameof(Morale));
    Patch(h,typeof(DefaultPartySizeLimitModel),"GetPartyMemberSizeLimit",pre:nameof(Size));
    Patch(h,typeof(DefaultArmyManagementCalculationModel),"CalculatePartyInfluenceCost",pre:nameof(ArmyCost));
    Patch(h,typeof(PartyUpgraderCampaignBehavior),"UpgradeReadyTroops",pre:nameof(Upgrade));
    Patch(h,typeof(DefaultPartyTroopUpgradeModel),"GetGoldCostForUpgrade",pre:nameof(UpgradeGold));
    Patch(h,typeof(DefaultPartyTroopUpgradeModel),"DoesPartyHaveRequiredItemsForUpgrade",pre:nameof(UpgradeItems));
    Patch(h,typeof(DefaultMilitaryPowerModel),"GetTroopPower",post:nameof(Power));
    Patch(h,typeof(DefaultPartyHealingModel),"GetSurvivalChance",post:nameof(Survival));
    Patch(h,typeof(DefaultHeroDeathProbabilityCalculationModel),"CalculateHeroDeathProbability",post:nameof(AgeDeath));
    Patch(h,typeof(Hero),"CanDie",post:nameof(CanDie));
    Patch(h,typeof(Hero),"CanBecomePrisoner",post:nameof(CanCapture));
    Patch(h,typeof(HeroSpawnCampaignBehavior),"TrySpawnHeroesAndParties",pre:nameof(NativeSpawn));
    Patch(h,typeof(HeroSpawnCampaignBehavior),"OnHeroDailyTick",pre:nameof(NativeHeroTick));
    Patch(h,typeof(EncounterGameMenuBehavior),"game_menu_encounter_meeting_on_init",pre:nameof(Encounter));
    Patch(h,typeof(DestroyKingdomAction),"ApplyInternal",pre:nameof(DestroyKingdom));
    Patch(h,typeof(ChangeKingdomAction),"ApplyInternal",pre:nameof(ChangeKingdom));
    Patch(h,typeof(MakePeaceAction),"ApplyInternal",pre:nameof(Peace));
    Patch(h,typeof(DefaultDiplomacyModel),"IsAtConstantWar",pre:nameof(ConstantWar));
    Patch(h,typeof(Army),"HourlyTick",pre:nameof(ArmyTick));
    Patch(h,typeof(Army),"Tick",pre:nameof(ArmyTick));
    Patch(h,typeof(Army),"GetNotificationText",pre:nameof(ArmyNotification));
    Patch(h,typeof(MapEvent),"CaptureDefeatedPartyMembers",pre:nameof(BeforeCapture),post:nameof(AfterCapture));
    var model=AccessTools.TypeByName("SandBox.GameComponents.SandboxAgentStatCalculateModel") ?? throw new TypeLoadException("Sandbox stats model");
    Patch(h,model,"UpdateHumanStats",trans:nameof(ArmorTransform));
    Patch(h,model,"GetEffectiveArmorEncumbrance",trans:nameof(WeightTransform));
   }
   catch {h.UnpatchAll(Owner);Targets.Clear();throw;}
  }
  private static void Patch(Harmony h,Type type,string name,string pre=null,string post=null,string trans=null)
  {
   var m=AccessTools.DeclaredMethod(type,name) ?? throw new MissingMethodException(type.FullName,name);
   h.Patch(m,pre==null?null:new HarmonyMethod(typeof(Patches),pre),post==null?null:new HarmonyMethod(typeof(Patches),post),
    trans==null?null:new HarmonyMethod(typeof(Patches),trans));Targets.Add(m);
  }
  public static void Speed(MobileParty mobileParty,ref ExplainedNumber __result)
  {
   if(!Catalog.Zombie(mobileParty))return;
   // The native final speed is computed once for the moving leader including attached parties.
   float v=__result.ResultNumber;float n=v*Settings.Current.Speed;
   if(Settings.Current.SpeedCap>0)n=Math.Min(n,Settings.Current.SpeedCap);
   __result.Add(n-v,new TextObject("感染者行军"));
  }
  public static bool Food(MobileParty mobileParty,ref bool __result)
  {if(!Catalog.Zombie(mobileParty))return true;__result=false;return false;}
  public static bool Consumption(MobileParty party,ref ExplainedNumber __result)
  {if(!Catalog.Zombie(party))return true;__result=new ExplainedNumber(0);return false;}
  public static bool Wage(MobileParty mobileParty,ref ExplainedNumber __result)
  {if(!Catalog.Zombie(mobileParty))return true;__result=new ExplainedNumber(0);return false;}
  public static bool Morale(MobileParty mobileParty,ref ExplainedNumber __result)
  {if(!Catalog.Zombie(mobileParty))return true;__result=new ExplainedNumber(100);return false;}
  public static bool Size(PartyBase party,ref ExplainedNumber __result)
  {if(!Catalog.Zombie(party))return true;__result=new ExplainedNumber(Math.Max(party.MemberRoster.TotalManCount,Settings.Current.PartyCap+1));return false;}
  public static bool ArmyCost(MobileParty armyLeaderParty,MobileParty party,ref int __result)
  {if(!Catalog.Zombie(armyLeaderParty) || !Catalog.Zombie(party))return true;__result=0;return false;}
  public static bool Upgrade(PartyBase party)
  {if(!Catalog.Zombie(party))return true;UndeadBehavior.Upgrade(party);return false;}
  public static bool UpgradeGold(PartyBase party,ref ExplainedNumber __result)
  {if(!Catalog.Zombie(party))return true;__result=new ExplainedNumber(0);return false;}
  public static bool UpgradeItems(PartyBase party,ref bool __result)
  {if(!Catalog.Zombie(party))return true;__result=true;return false;}
  public static void Power(CharacterObject troop,ref float __result)
  {if(Catalog.For(troop)!=null)__result*=Settings.Current.SimulationPower;}
  public static void Survival(CharacterObject character,PartyBase party,PartyBase enemyParty,ref float __result)
  {if(Catalog.Lord(character.HeroObject) || (character.IsHero && Catalog.Zombie(enemyParty)))__result=1f;}
  public static void AgeDeath(Hero hero,ref float __result){if(Catalog.Lord(hero))__result=0f;}
  public static void CanDie(Hero __instance,ref bool __result){if(Catalog.Lord(__instance))__result=false;}
  public static void CanCapture(Hero __instance,ref bool __result)
  {
   var battle=__instance.PartyBelongedTo?.MapEvent;
   if(Catalog.Lord(__instance) || (battle?.HasWinner==true && battle.Winner.Parties.Any(p=>Catalog.Zombie(p.Party))))__result=false;
  }
  public static bool NativeSpawn(Clan clan)=>!Catalog.Faction(clan);
  public static bool NativeHeroTick(Hero hero)=>!Catalog.Lord(hero);
  public static bool Encounter()
  {
   if(!Catalog.Zombie(PlayerEncounter.EncounteredParty))return true;
   if(PlayerEncounter.Battle==null)PlayerEncounter.StartBattle();
   GameMenu.SwitchToMenu("encounter");return false;
  }
  public static bool DestroyKingdom(Kingdom destroyedKingdom)=>!Catalog.Faction(destroyedKingdom);
  public static bool ChangeKingdom(Clan clan,Kingdom newKingdom)=>Catalog.Faction(clan)?Catalog.Faction(newKingdom):!Catalog.Faction(newKingdom);
  public static bool Peace(IFaction faction1,IFaction faction2)=>!Catalog.Faction(faction1) && !Catalog.Faction(faction2);
  public static bool ConstantWar(IFaction faction1,IFaction faction2,ref bool __result)
  {
   if(!Catalog.Faction(faction1) && !Catalog.Faction(faction2))return true;
   __result=Catalog.Faction(faction1)!=Catalog.Faction(faction2) && faction1!=null && faction2!=null && faction1.StringId!="neutral" && faction2.StringId!="neutral";
   return false;
  }
  public static bool ArmyTick(Army __instance)=>!Catalog.Zombie(__instance.LeaderParty);
  public static bool ArmyNotification(Army __instance,ref TextObject __result)
  {if(!Catalog.Zombie(__instance.LeaderParty))return true;__result=new TextObject("感染者正在集结尸潮军团");return false;}
  public sealed class CaptureState
  {
   public readonly Dictionary<TroopRoster,Dictionary<CharacterObject,int>> Before=new Dictionary<TroopRoster,Dictionary<CharacterObject,int>>();
   public bool Relevant;
  }
  public static void BeforeCapture(MapEvent __instance,ref CaptureState __state)
  {
   __state=new CaptureState();
   if(!__instance.IsFieldBattle || __instance.IsNavalMapEvent || !__instance.HasWinner)return;
   __state.Relevant=__instance.InvolvedParties.Any(Catalog.Zombie);
   if(!__state.Relevant)return;
   foreach(var p in __instance.GetMapEventSide(__instance.DefeatedSide).Parties.Where(p=>Catalog.Zombie(p.Party)))
    foreach(var e in p.Party.MemberRoster.GetTroopRoster().Where(e=>e.Character.IsHero))UndeadBehavior.Current?.Schedule(e.Character.HeroObject);
   foreach(var p in __instance.Winner.Parties)
   {
    var r=p.RosterToReceiveLootPrisoners;
    if(r!=null && !__state.Before.ContainsKey(r))__state.Before.Add(r,r.GetTroopRoster().ToDictionary(e=>e.Character,e=>e.Number));
   }
  }
  public static void AfterCapture(MapEvent __instance,CaptureState __state)
  {
   if(__state?.Relevant!=true)return;
   try{BattleService.Resolve(__instance,__state);}catch(Exception e){SubModule.Log("Battle settlement failed: "+e);}
  }
  private static readonly string[] Sums={"GetHeadArmorSum","GetHumanBodyArmorSum","GetArmArmorSum","GetLegArmorSum"};
  public static IEnumerable<CodeInstruction> ArmorTransform(IEnumerable<CodeInstruction> source)
  {
   var result=new List<CodeInstruction>();var counts=new int[4];
   foreach(var i in source)
   {
    result.Add(i);var m=i.operand as MethodInfo;int p=m==null?-1:Array.IndexOf(Sums,m.Name);
    if(p<0 || m.DeclaringType!=typeof(Equipment))continue;
    counts[p]++;result.Add(new CodeInstruction(OpCodes.Ldarg_1));result.Add(new CodeInstruction(OpCodes.Ldc_I4,p));
    result.Add(new CodeInstruction(OpCodes.Call,AccessTools.Method(typeof(Patches),nameof(Armor))));
   }
   if(counts.Any(c=>c!=1))throw new InvalidOperationException("Expected four armour sums");return result;
  }
  public static float Armor(float baseline,Agent agent,int part)=>baseline+(Catalog.For(agent?.Character)?.Armor[part]??0);
  public static IEnumerable<CodeInstruction> WeightTransform(IEnumerable<CodeInstruction> source)
  {
   var result=new List<CodeInstruction>();int count=0;
   foreach(var i in source)
   {
    result.Add(i);
    if(i.operand is MethodInfo m && m.DeclaringType==typeof(Equipment) && m.Name=="GetTotalWeightOfArmor")
    {count++;result.Add(new CodeInstruction(OpCodes.Ldarg_1));result.Add(new CodeInstruction(OpCodes.Call,AccessTools.Method(typeof(Patches),nameof(Weight))));}
   }
   if(count!=1)throw new InvalidOperationException("Expected one armour weight sum");return result;
  }
  public static float Weight(float baseline,Agent agent)=>baseline+(Catalog.For(agent?.Character)?.Weight??0);
 }
}
