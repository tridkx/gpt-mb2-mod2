using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Xml.Linq;
using TaleWorlds.CampaignSystem;
using TaleWorlds.CampaignSystem.Party;
using TaleWorlds.CampaignSystem.Roster;
using TaleWorlds.Core;

namespace BanditPopulationTuning
{
    public sealed class EnhancementBehavior : CampaignBehaviorBase
    {
        private readonly Dictionary<string,float> grainCarry=new Dictionary<string,float>(StringComparer.Ordinal);
        public override void RegisterEvents()
        {
            CampaignEvents.DailyTickEvent.AddNonSerializedListener(this,Daily);
            CampaignEvents.WeeklyTickEvent.AddNonSerializedListener(this,Weekly);
        }
        public override void SyncData(IDataStore dataStore)
        {
            string state="";
            if(dataStore.IsSaving)
                state=ExportCarry();
            dataStore.SyncData("bpt_grain_remainders_v1",ref state);
            if(dataStore.IsLoading) LoadCarry(state);
        }
        public string ExportCarry() => new XElement("Grain",grainCarry.OrderBy(x=>x.Key).Select(x=>new XElement("Party",
            new XAttribute("id",x.Key),new XAttribute("remainder",x.Value.ToString("R",CultureInfo.InvariantCulture))))).ToString(SaveOptions.DisableFormatting);
        public void LoadCarry(string state)
        {
            grainCarry.Clear();
            if(string.IsNullOrWhiteSpace(state)) return;
            try
            {
                foreach(var e in XElement.Parse(state).Elements("Party"))
                {
                    string id=(string)e.Attribute("id");
                    if(!string.IsNullOrEmpty(id) && float.TryParse((string)e.Attribute("remainder"),NumberStyles.Float,CultureInfo.InvariantCulture,out float f)
                        && !float.IsNaN(f) && !float.IsInfinity(f) && f>0 && f<1) grainCarry[id]=f;
                }
            }
            catch(System.Xml.XmlException e){SubModule.Log("Grain remainder state invalid; reset only carry. "+e.Message);}
        }
        private void Daily()
        {
            if(!EnhancementPatches.Ready) return;
            var s=Settings.Current;
            if(s.AIDailyExperiencePerSoldier==0 && s.AIDailyBasicTroops==0 && s.AIDailyEliteTroops==0 && s.AIDailyGrainPerSeven==0)
            {grainCarry.Clear();return;}
            var live=new HashSet<string>(StringComparer.Ordinal);
            foreach(var party in MobileParty.AllLordParties.ToArray())
            {
                if(!EnhancementRules.AIParty(party)) continue;
                live.Add(party.StringId);
                // Skip all daily assistance during active map battles, without catching up later.
                if(party.MapEvent!=null) continue;
                try
                {
                    // Train pre-existing troops before adding today's recruits.
                    Train(party.MemberRoster,s.AIDailyExperiencePerSoldier);
                    var culture=party.LeaderHero.Culture;
                    if(culture!=null && (s.AIDailyBasicTroops>0 || s.AIDailyEliteTroops>0))
                    {
                        int[] counts=EnhancementRules.Recruitment(party.MemberRoster.TotalManCount,party.Party.PartySizeLimit,
                            s.AIDailyBasicTroops,s.AIDailyEliteTroops,culture.BasicTroop!=null,culture.EliteBasicTroop!=null);
                        if(counts[0]>0) party.MemberRoster.AddToCounts(culture.BasicTroop,counts[0]);
                        if(counts[1]>0) party.MemberRoster.AddToCounts(culture.EliteBasicTroop,counts[1]);
                        if(counts.Sum()>0) party.Party.SetVisualAsDirty();
                    }
                    if(s.AIDailyGrainPerSeven>0)
                    {
                        grainCarry.TryGetValue(party.StringId,out float previous);
                        int add=EnhancementRules.Grain(party.MemberRoster.TotalManCount,s.AIDailyGrainPerSeven,previous,
                            party.Food,Math.Max(0,-party.FoodChange),s.GrainStockDays,out float next);
                        if(next>0) grainCarry[party.StringId]=next; else grainCarry.Remove(party.StringId);
                        if(add>0) party.ItemRoster.AddToCounts(DefaultItems.Grain,add);
                    }
                    else grainCarry.Remove(party.StringId);
                }
                catch(Exception error){SubModule.Log("Daily assistance failed for "+party.StringId+": "+error);}
            }
            foreach(string key in grainCarry.Keys.Where(x=>!live.Contains(x)).ToArray()) grainCarry.Remove(key);
        }
        public static int Train(TroopRoster roster,int perSoldier)
        {
            if(perSoldier<=0) return 0;
            int groups=0;
            foreach(var entry in roster.GetTroopRoster().ToArray())
            {
                if(entry.Character.IsHero) continue;
                int xp=EnhancementRules.Experience(entry.Number,perSoldier,entry.Xp,entry.Character.UpgradeTargets?.Length>0);
                if(xp>0){roster.AddXpToTroop(entry.Character,xp);groups++;}
            }
            return groups;
        }
        private void Weekly()
        {
            if(!EnhancementPatches.Ready) return;
            var s=Settings.Current;
            if(s.AILordWeeklyGold==0 && s.AILordWeeklySkillXp==0) return;
            var player=EnhancementRules.ReadyPlayerCharacter;
            if(player==null) return;
            SkillObject[] skills={DefaultSkills.OneHanded,DefaultSkills.TwoHanded,DefaultSkills.Polearm,DefaultSkills.Bow,
                DefaultSkills.Crossbow,DefaultSkills.Throwing,DefaultSkills.Riding,DefaultSkills.Athletics,DefaultSkills.Crafting,
                DefaultSkills.Scouting,DefaultSkills.Tactics,DefaultSkills.Roguery,DefaultSkills.Charm,DefaultSkills.Leadership,
                DefaultSkills.Trade,DefaultSkills.Steward,DefaultSkills.Medicine,DefaultSkills.Engineering};
            foreach(var hero in Hero.AllAliveHeroes.ToArray())
            {
                if(!hero.IsLord || !hero.IsAlive || hero.IsPrisoner || !EnhancementRules.AIClan(hero.Clan) || hero==player.HeroObject) continue;
                try
                {
                    int gold=(int)Math.Max(0,Math.Min((long)EnhancementRules.SafeInt(s.AILordWeeklyGold,100000), (long)int.MaxValue-hero.Gold));
                    if(gold>0) hero.ChangeHeroGold(gold);
                    int xp=EnhancementRules.SafeInt(s.AILordWeeklySkillXp,10000);
                    if(xp>0) foreach(var skill in skills) hero.AddSkillXp(skill,xp);
                }
                catch(Exception error){SubModule.Log("Weekly assistance failed for "+hero.StringId+": "+error);}
            }
        }
    }
}
