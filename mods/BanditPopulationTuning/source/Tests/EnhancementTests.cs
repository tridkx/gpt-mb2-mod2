using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.Serialization;
using System.Web.Script.Serialization;
using BanditPopulationTuning;
using HarmonyLib;
using TaleWorlds.CampaignSystem;
using TaleWorlds.CampaignSystem.GameComponents;
using TaleWorlds.CampaignSystem.Party;
using TaleWorlds.CampaignSystem.Roster;
using TaleWorlds.Localization;

internal static class EnhancementTests
{
    private static int checks;
    public static int Run(string game)
    {
        var s=new Settings();
        string[] zero={"AIPartySizeBonus","AIClanPartyBonus","AIDailyExperiencePerSoldier","AIDailyBasicTroops","AIDailyEliteTroops",
            "AIDailyGrainPerSeven","AILordWeeklyGold","AILordWeeklySkillXp","SettlementLoyaltyBonus","SettlementFoodBonus",
            "SettlementMilitiaBonus","SettlementProsperityBonus","SettlementSecurityBonus","SettlementTaxBonus",
            "OtherHeroHealthBonus","PlayerHealthBonus","OtherHeroDamagePercent","PlayerDamagePercent"};
        foreach(string name in zero) Check(Convert.ToDouble(typeof(Settings).GetProperty(name).GetValue(s))==0,"new feature neutral by default: "+name);
        Near(s.AIPartySizeMultiplier,1,"capacity multiplier neutral");
        Check(!typeof(Settings).GetProperties().Any(x=>x.Name.EndsWith("Age",StringComparison.OrdinalIgnoreCase)
            || x.Name.IndexOf("Specialization",StringComparison.OrdinalIgnoreCase)>=0),"no age or specialization settings");
        var old=new JavaScriptSerializer().Deserialize<Settings>("{\"PartyCountMultiplier\":3.5,\"PartySizeMultiplier\":1.5,\"ReplenishmentMultiplier\":0.5}");
        Near(old.PartyCountMultiplier,3.5f,"existing per-save setting kept");
        Near(old.AIPartySizeMultiplier,1,"missing new multiplier defaults to one");
        Check(old.AIPartySizeBonus==0 && old.AIDailyExperiencePerSoldier==0,"old settings default new additions to zero");
        Near(EnhancementRules.PartyCapacity(120,1.5f,20),200,"final original result x multiplier plus flat");
        Near(EnhancementRules.PartyCapacity(80,1.5f,20),140,"original lord differences retained");
        Near(EnhancementRules.PartyCapacity(100,1,25),125,"addition only");
        Near(EnhancementRules.PartyCapacity(101,1.25f,0),126,"capacity floors once");
        Check(EnhancementRules.ClanCapacity(2,3)==5 && EnhancementRules.ClanCapacity(4,3)==7,"clan original differences retained");
        Check(EnhancementRules.EligibleClan(true,false,false,false),"AI clan included");
        Check(!EnhancementRules.EligibleClan(true,true,false,false),"player clan excluded");
        Check(!EnhancementRules.EligibleClan(true,false,true,false),"bandit clan excluded");
        Check(!EnhancementRules.EligibleClan(true,false,false,true),"eliminated clan excluded");
        Check(EnhancementRules.EligibleParty(true,true,true,false,true,false,false),"normal AI lord party included");
        foreach(int flag in Enumerable.Range(0,7))
        {
            bool[] v={true,true,true,false,true,false,false};v[flag]=!v[flag];
            Check(!EnhancementRules.EligibleParty(v[0],v[1],v[2],v[3],v[4],v[5],v[6]),"party exclusion flag "+flag);
        }
        Check(!EnhancementRules.Settlement(false,false,false),"village excluded from town militia");
        Check(!EnhancementRules.Settlement(true,true,true),"AI-only excludes player settlement");
        Check(EnhancementRules.Settlement(true,true,false),"explicit player settlement scope");
        var number=new ExplainedNumber(100,true,new TextObject("原基础"));
        number.Add(20,new TextObject("原加值"));number.AddFactor(.5f,new TextObject("原特长"));
        Near(number.ResultNumber,180,"native factor baseline");
        float desired=EnhancementRules.PartyCapacity(number.ResultNumber,1.5f,10);
        EnhancementRules.AddFinal(ref number,desired-number.ResultNumber,"新增带兵");
        Near(number.ResultNumber,280,"no double application of native factors");
        Near(number.GetLines().Sum(x=>x.number),280,"tooltip lines sum to result");
        Check(number.GetLines().Any(x=>x.name=="原特长") && number.GetLines().Any(x=>x.name=="新增带兵"),"native explanations retained");
        var neutral=new ExplainedNumber(100,false);neutral.AddFactor(.2f);
        EnhancementRules.AddFinal(ref neutral,0,"none");
        Near(neutral.BaseNumber,100,"neutral keeps original structure");Near(neutral.SumOfFactors,.2f,"neutral keeps factors");
        var clamped=new ExplainedNumber(100,false);clamped.LimitMax(80);
        EnhancementRules.AddFinal(ref clamped,10,"extra");Near(clamped.ResultNumber,90,"addition after native clamp");
        Near(EnhancementRules.HeroDamage(50,true,false,s),50,"default damage untouched");
        s.OtherHeroDamagePercent=20;s.PlayerDamagePercent=50;
        Near(EnhancementRules.HeroDamage(50,true,false,s),60,"other hero damage");
        Near(EnhancementRules.HeroDamage(50,true,true,s),75,"player independently configured");
        Near(EnhancementRules.HeroDamage(50,false,false,s),50,"ordinary soldiers untouched");
        Check(EnhancementRules.Experience(10,100,0,true)==1000 && EnhancementRules.Experience(30,100,0,true)==3000,"per-soldier rather than per-stack XP");
        Check(EnhancementRules.Experience(10,100,0,false)==0,"terminal troops skipped");
        Check(EnhancementRules.Experience(1000,10000,int.MaxValue-8,true)==8,"XP overflow bounded");
        var roster=TroopRoster.CreateDummyTroopRoster();
        CharacterObject recruit=Dummy("recruit"),infantry=Dummy("infantry"),terminal=Dummy("terminal");
        AccessTools.PropertySetter(typeof(CharacterObject),"UpgradeTargets").Invoke(recruit,new object[]{new[]{infantry}});
        AccessTools.PropertySetter(typeof(CharacterObject),"UpgradeTargets").Invoke(infantry,new object[]{new[]{terminal}});
        roster.AddToCounts(recruit,10,woundedCount:3);roster.AddToCounts(infantry,30);roster.AddToCounts(terminal,5);
        Check(EnhancementBehavior.Train(roster,100)==2,"daily training touches two eligible groups once");
        Check(roster.GetElementXp(recruit)==1000 && roster.GetElementXp(infantry)==3000 && roster.GetElementXp(terminal)==0,"real roster XP amounts");
        Check(roster.TotalManCount==45 && roster.TotalWounded==3,"training preserves men and wounded");
        foreach(var v in new[]{new[]{98,100,10,10,1,1},new[]{120,100,10,10,1,1},new[]{0,3,10,10,1,1},new[]{0,10,5,5,0,1}})
        {
            var plan=EnhancementRules.Recruitment(v[0],v[1],v[2],v[3],v[4]!=0,v[5]!=0);
            Check(plan.Sum()<=Math.Max(0,v[1]-v[0]),"recruitment never exceeds capacity");
            if(v[4]==0) Check(plan[0]==0,"missing culture entry skipped");
        }
        Check(EnhancementRules.Recruitment(98,100,10,10,true,true).SequenceEqual(new[]{1,1}),"both lines share scarce slots");
        float carry=0;int total=0;
        for(int day=0;day<7;day++) total+=EnhancementRules.Grain(1,1,carry,0,1,10,out carry);
        Check(total==1,"fractional grain accumulates across seven days");
        Check(EnhancementRules.Grain(70,1,0,0,10,10,out carry)==10,"grain uses actual men");
        Check(EnhancementRules.Grain(70,1,0,98,10,10,out carry)==2 && carry==0,"stock capped by all food, no backlog");
        Check(EnhancementRules.Grain(70,1,.8f,100,10,10,out carry)==0 && carry==0,"full stock clears deferred grain");
        Check(EnhancementRules.Grain(70,0,0,0,10,10,out carry)==0,"grain default off");
        var behavior=new EnhancementBehavior();
        behavior.LoadCarry("<Grain><Party id=\"lord &amp; a\" remainder=\"0.25\"/><Party id=\"invalid\" remainder=\"NaN\"/></Grain>");
        string state=behavior.ExportCarry();var reloaded=new EnhancementBehavior();reloaded.LoadCarry(state);
        Check(state==reloaded.ExportCarry() && state.Contains("0.25") && !state.Contains("invalid"),"fraction save roundtrip uses ordinary escaped string");
        Assembly.LoadFrom(Path.Combine(game,"Modules/SandBox/bin/Win64_Shipping_Client/SandBox.dll"));
        EnhancementPatches.Install();
        try
        {
            Check(EnhancementPatches.Targets.Count==10 && EnhancementPatches.Ready,"all ten new real methods patched");
            foreach(var method in EnhancementPatches.Targets)
            {
                Check(Harmony.GetPatchInfo(method).Postfixes.Count(p=>p.owner==EnhancementPatches.Owner)==1,"one new patch per native method");
                Console.WriteLine("PATCH OK "+method.DeclaringType.FullName+"."+method.Name);
            }
            // New neutral postfixes must tolerate absence of a campaign in model-only checks.
            var party=new ExplainedNumber(123,false);
            object[] arguments={null,party};
            AccessTools.Method(typeof(EnhancementPatches),"PartySize").Invoke(null,arguments);
            Near(((ExplainedNumber)arguments[1]).ResultNumber,123,"default model postfix exact no-op");
        }
        finally{EnhancementPatches.Uninstall();}
        Check(!EnhancementPatches.Ready && !Harmony.GetAllPatchedMethods().Any(m=>Harmony.GetPatchInfo(m).Owners.Contains(EnhancementPatches.Owner)),"new hooks completely uninstalled");
        CheckMixingOrder(game);
        return checks;
    }
    private static void CheckMixingOrder(string game)
    {
        string dll=Path.Combine(game,"Modules/GenshinBanditRace/bin/Win64_Shipping_Client/GenshinBanditRace.dll");
        if(!File.Exists(dll)){Console.WriteLine("COMBINED SKIP Genshin module not installed");return;}
        var type=Assembly.LoadFrom(dll).GetType("GenshinBanditRace.Patches");
        BanditPopulationTuning.Patches.Install();type.GetMethod("Install").Invoke(null,null);
        try
        {
            var method=AccessTools.DeclaredMethod(typeof(TaleWorlds.CampaignSystem.CampaignBehaviors.BanditSpawnCampaignBehavior),"InitializeBanditParty");
            var sorted=PatchProcessor.GetSortedPatchMethods(method,Harmony.GetPatchInfo(method).Postfixes.ToArray()).ToArray();
            Check(Array.FindIndex(sorted,m=>m.DeclaringType==typeof(BanditPopulationTuning.Patches))<Array.FindIndex(sorted,m=>m.DeclaringType==type),"population still runs before Genshin mixing");
        }
        finally{type.GetMethod("Uninstall").Invoke(null,null);BanditPopulationTuning.Patches.Uninstall();}
    }
    private static CharacterObject Dummy(string id){var c=(CharacterObject)FormatterServices.GetUninitializedObject(typeof(CharacterObject));c.StringId=id;return c;}
    private static void Check(bool value,string message){checks++;if(!value)throw new Exception(message);}
    private static void Near(float a,float b,string message)=>Check(Math.Abs(a-b)<.001f,message);
}
